# Arquitectura de Comunicación XMPP-WebSocket

## Arquitectura Real (Simplificada)

```
┌─────────────────┐    XMPP     ┌──────────────────┐    XMPP     ┌─────────────────┐
│  Agente SPADE   │◄──────────► │ Servidor XMPP    │◄──────────► │   Navegador     │
│                 │   (TCP)     │ (ej: Openfire)   │ (WebSocket) │                 │
│ Python/aioxmpp  │             │                  │             │ JavaScript      │
│                 │             │ Puerto 5222      │             │ XMPP.js         │
└─────────────────┘             │ Puerto 7070 (WS) │             └─────────────────┘
                                └──────────────────┘
                                
                                        ▲
                                        │ HTTP
                                        │ (solo archivos)
                                        ▼
                                ┌──────────────────┐
                                │  Web Server      │
                                │  Python          │
                                │  Puerto 8080     │
                                │ (solo HTML/CSS)  │
                                └──────────────────┘
```

## Los Dos Servidores Separados

### 1. **Servidor Web Python (Puerto 8080)**
- **Función**: Solo sirve archivos HTML, CSS, JavaScript
- **Es como Apache o Nginx**: solo archivos estáticos
- **NO maneja XMPP**: no traduce mensajes ni hace de gateway

```python
# spade_llm/human_interface/web_server.py
# Es solo un servidor HTTP básico
def run_server(port=8080, directory=None):
    handler = partial(CORSRequestHandler, directory=directory)
    httpd = HTTPServer(('localhost', port), handler)
    httpd.serve_forever()  # Solo sirve archivos
```

### 2. **Servidor XMPP (Puerto 7070)**
- **Función**: Servidor XMPP real (Openfire, ejabberd, etc.)
- **Maneja**: Autenticación, routing de mensajes, WebSocket
- **Puerto 5222**: Para clientes XMPP normales (agentes SPADE)
- **Puerto 7070**: Para clientes WebSocket (navegadores)

## Flujo Real de Mensajes

### Paso 1: Agente pregunta al humano
```python
# En el agente SPADE
msg = Message(to="experto@servidor.com")
msg.body = "¿Cuál es el estado del proyecto?"
await self.send(msg)  # Envía via XMPP normal al servidor XMPP
```

### Paso 2: Servidor XMPP entrega mensaje
El servidor XMPP ve que `experto@servidor.com` está conectado via WebSocket desde el navegador, así que le envía el mensaje por WebSocket.

### Paso 3: Navegador recibe mensaje
```javascript
// El navegador está conectado directamente al servidor XMPP
xmppClient.on('stanza', (stanza) => {
    if (stanza.is('message')) {
        // Muestra el mensaje en la interfaz web
        displayMessage(stanza.getChild('body').text());
    }
});
```

### Paso 4: Humano responde
```javascript
// El navegador envía respuesta directamente al servidor XMPP
const response = xml('message', {
    to: 'agente@servidor.com',
    type: 'chat'
}, xml('body', {}, 'El proyecto está completado'));

await xmppClient.send(response);  // Directo al servidor XMPP
```

### Paso 5: Agente recibe respuesta
```python
# El agente recibe la respuesta via XMPP normal
response_msg = await self.receive(timeout=300)
print(response_msg.body)  # "El proyecto está completado"
```

## Lo Clave: NO HAY TRADUCCIÓN

**No hay traducción de protocolos** porque:
1. El navegador habla XMPP (usando XMPP.js)
2. El agente habla XMPP (usando aioxmpp)
3. Ambos se conectan al mismo servidor XMPP
4. El servidor XMPP maneja ambos tipos de conexión:
   - TCP/XMPP para agentes
   - WebSocket/XMPP para navegadores

## La Configuración de Conexión

En el navegador:
```javascript
// Se conecta DIRECTAMENTE al servidor XMPP, no al web server Python
service: "ws://sosanzma:7070/ws/"  // Puerto 7070 = WebSocket del servidor XMPP
```

En el agente SPADE:
```python
# Se conecta DIRECTAMENTE al servidor XMPP
agent = LLMAgent("agente@sosanzma", "password")  # Puerto 5222 implícito
```

## Uso de la Librería XMPP.js

### Carga de la Librería
La librería XMPP.js se carga desde CDN en el navegador:

```html
<!-- Carga desde CDN con fallback -->
<script src="https://unpkg.com/@xmpp/client@0.13.0/dist/xmpp.min.js" 
        crossorigin 
        onerror="loadXMPPFallback()"></script>
<script>
    function loadXMPPFallback() {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/@xmpp/client@0.13.0/dist/xmpp.min.js';
        document.head.appendChild(script);
    }
</script>
```

### Inicialización del Cliente XMPP

```javascript
// Verificar que la librería se cargó correctamente
if (!window.XMPP) {
    console.error('XMPP library not loaded!');
    return;
}

const { client, xml } = window.XMPP;

// Crear cliente XMPP con configuración
const clientConfig = {
    service: 'ws://sosanzma:7070/ws/',  // WebSocket del servidor XMPP
    domain: 'sosanzma',                 // Dominio XMPP
    username: 'experto',                // Usuario
    password: 'password123'             // Contraseña
};

xmppClient = client(clientConfig);
```

### Manejo de Eventos del Cliente

```javascript
// Evento: Conexión exitosa
xmppClient.on('online', async (address) => {
    console.log(`Conectado como: ${address.toString()}`);
    
    // Enviar presencia inicial (disponible)
    await xmppClient.send(xml('presence'));
    
    // Mostrar interfaz principal
    showMainInterface();
});

// Evento: Error de conexión
xmppClient.on('error', (err) => {
    console.error(`Error XMPP: ${err.message}`);
    showError('Error de conexión XMPP');
});

// Evento: Desconexión
xmppClient.on('offline', () => {
    console.log('Desconectado del servidor XMPP');
    showLoginForm();
});

// Evento: Recepción de stanzas XMPP
xmppClient.on('stanza', (stanza) => {
    console.log(`Stanza recibida: ${stanza.toString()}`);
    
    if (stanza.is('message') && stanza.attrs.type === 'chat') {
        handleIncomingMessage(stanza);
    }
});
```

### Envío de Mensajes

```javascript
// Enviar mensaje de respuesta
async function sendResponse(query, responseText) {
    if (!xmppClient) {
        console.error('Cliente XMPP no disponible');
        return;
    }
    
    try {
        // Crear mensaje XMPP usando xml()
        const message = xml(
            'message',
            {
                to: query.from,        // Destinatario
                type: 'chat',          // Tipo de mensaje
                thread: query.id       // ID del hilo para correlación
            },
            xml('body', {}, responseText)  // Cuerpo del mensaje
        );
        
        // Enviar mensaje
        await xmppClient.send(message);
        console.log('Mensaje enviado correctamente');
        
    } catch (error) {
        console.error(`Error enviando mensaje: ${error.message}`);
    }
}
```

### Procesamiento de Mensajes Entrantes

```javascript
function handleIncomingMessage(stanza) {
    // Extraer información del mensaje
    const from = stanza.attrs.from;
    const thread = stanza.attrs.thread;
    const body = stanza.getChildText('body');
    
    if (!body) {
        console.warn('Mensaje sin contenido recibido');
        return;
    }
    
    // Parsear información de la consulta
    const queryMatch = body.match(/\[Query ([^\]]+)\]/);
    const queryId = queryMatch ? queryMatch[1] : thread || 'unknown';
    
    // Crear objeto de consulta
    const query = {
        id: thread || queryId,
        shortId: queryId,
        from: from,
        body: body,
        timestamp: new Date()
    };
    
    // Mostrar en la interfaz
    displayQuery(query);
    
    // Notificación opcional
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Nueva Consulta', {
            body: `${queryId}: ${body.substring(0, 50)}...`
        });
    }
}
```

### Manejo de Presencia

```javascript
// Enviar presencia personalizada
async function setPresence(show, status) {
    const presence = xml(
        'presence',
        {},
        xml('show', {}, show),        // 'chat', 'away', 'xa', 'dnd'
        xml('status', {}, status)     // Mensaje de estado personalizado
    );
    
    await xmppClient.send(presence);
}

// Ejemplos de uso
await setPresence('chat', 'Disponible para consultas');
await setPresence('away', 'Temporalmente ausente');
await setPresence('dnd', 'No molestar - ocupado');
```

### Gestión de Conexión

```javascript
// Conectar al servidor
async function connect() {
    try {
        await xmppClient.start();
        console.log('Conexión XMPP iniciada');
    } catch (error) {
        console.error(`Error de conexión: ${error.message}`);
        throw error;
    }
}

// Desconectar del servidor
async function disconnect() {
    if (xmppClient) {
        await xmppClient.stop();
        console.log('Desconectado del servidor XMPP');
    }
}

// Reconexión automática
xmppClient.on('offline', () => {
    console.log('Intentando reconexión...');
    setTimeout(async () => {
        try {
            await connect();
        } catch (error) {
            console.error('Reconexión fallida:', error);
        }
    }, 5000);
});
```

## Resumen Simple

1. **Web Server Python**: Solo sirve la página web (como abrir un archivo HTML)
2. **Navegador**: Se conecta directamente al servidor XMPP via WebSocket usando XMPP.js
3. **Agente**: Se conecta directamente al servidor XMPP via TCP usando aioxmpp
4. **Servidor XMPP**: Enruta mensajes entre navegador y agente

**No hay gateway ni traducciones** - es comunicación XMPP directa por ambos lados, solo que el navegador usa WebSocket en lugar de TCP.