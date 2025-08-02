# Arquitectura y Funcionamiento de SPADE_LLM con MCP

## 1. Introducción a la Arquitectura General

El ejemplo `valencia_smart_mcp.py` demuestra la integración de tres tecnologías clave:

- **SPADE (Smart Python Agent Development Environment)**: Framework para sistemas multiagente
- **LLM (Large Language Models)**: Modelos de lenguaje como GPT-4o-mini
- **MCP (Model Context Protocol)**: Protocolo para integrar herramientas externas con LLMs

Visualmente, la arquitectura puede representarse así:

```
┌─────────────────────┐     ┌──────────────────────┐     ┌────────────────────┐
│                     │     │                      │     │                    │
│    Human Agent      │◄────┼─────►  LLM Agent     │◄────┼─────► MCP Server   │
│                     │     │                      │     │                    │
└─────────────────────┘     └──────────────────────┘     └────────────────────┘
        ▲                                                       ▲
        │                                                       │
        ▼                                                       ▼
┌─────────────────────┐                              ┌────────────────────┐
│                     │                              │                    │
│       Usuario       │                              │  APIs / Servicios  │
│                     │                              │  (ValenciaSmart)   │
└─────────────────────┘                              └────────────────────┘
```

## 2. Registro y Configuración de Servidores MCP

### 2.1 ¿Qué es MCP?

Model Context Protocol (MCP) es una especificación que permite que los LLMs interactúen con herramientas externas de manera estandarizada. Estas herramientas pueden ser desde APIs hasta servicios locales o remotos.

### 2.2 Configuración de un Servidor MCP

En nuestro ejemplo, configuramos un servidor MCP para ValenciaSmart:

```python
valencia_smart_mcp = StdioServerConfig(
    name="ValenciaSmart",
    command="C:/Users/manel/PycharmProjects/SmartCityMCP/.venv/Scripts/python.exe",
    args=["C:/Users/manel/PycharmProjects/SmartCityMCP/valencia_traffic_mcp.py"],
    cache_tools=True
)
```

Este código hace varias cosas importantes:

1. **Definir un nombre para el servidor** (`ValenciaSmart`): Este nombre se usa internamente para identificar el servidor.
2. **Especificar el comando y argumentos**: Indica qué script ejecutar para iniciar el servidor MCP.
3. **Activar caché de herramientas**: Optimiza el rendimiento almacenando en caché la información sobre las herramientas disponibles.

### 2.3 Protocolos de Transporte MCP

MCP soporta tres protocolos de transporte:

- **STDIO (Standard Input/Output)**: Comunicación a través de flujos de entrada/salida estándar
- **SSE (Server-Sent Events)**: Comunicación a través de eventos HTTP enviados por el servidor (⚠️ **Deprecado**)
- **Streamable HTTP**: Protocolo moderno que mejora SSE con mejor gestión de sesiones (**Recomendado** para servicios remotos)

!!! warning "SSE Deprecado"
    El transporte SSE está deprecado. Para nuevas implementaciones de servicios remotos, 
    se recomienda usar `StreamableHttpServerConfig` en lugar de `SseServerConfig`.

En nuestro ejemplo, usamos STDIO por varias razones:

1. **Simplicidad**: STDIO no requiere configuración de servidor HTTP.
2. **Rendimiento local**: Para herramientas locales, STDIO tiene menos sobrecarga.
3. **Integración sencilla**: Permite ejecutar scripts de Python directamente.

El código de configuración MCP mediante STDIO crea un subproceso que ejecuta el script especificado y establece una comunicación bidireccional con él:

```
┌─────────────────┐           ┌─────────────────┐
│                 │  stdin    │                 │
│   LLM Agent     │─────────►│  MCP Server     │
│                 │  stdout   │                 │
└─────────────────┘◄─────────┘─────────────────┘
```

Para servicios remotos, el transporte Streamable HTTP ofrece ventajas significativas:

```python
# Configuración moderna para servicios remotos
remote_mcp = StreamableHttpServerConfig(
    name="RemoteService",
    url="https://api.example.com/mcp",
    headers={"Authorization": "Bearer token"},
    timeout=30.0,
    sse_read_timeout=300.0,
    terminate_on_close=True,
    cache_tools=True
)
```

El transporte Streamable HTTP proporciona:
- Mayor estabilidad en conexiones de larga duración
- Mejor manejo de errores y reconexión
- Gestión mejorada de sesiones
- Compatibilidad total con la especificación MCP actual

## 3. Integración con el Agente LLM

### 3.1 Creación del Agente LLM

El agente LLM se configura pasando el servidor MCP:

```python
llm_agent = LLMAgent(
    jid=llm_jid,
    password=llm_password,
    provider=provider,
    system_prompt=(...),
    mcp_servers=[valencia_smart_mcp]
)
```

### 3.2 ¿Qué ocurre internamente en el LLMAgent?

Cuando se inicializa el `LLMAgent`, ocurre lo siguiente:

1. **Registro de servidores MCP**: Los servidores MCP se añaden a una sesión MCP interna.
2. **Descubrimiento de herramientas**: El agente consulta a cada servidor MCP para conocer las herramientas disponibles.
3. **Integración con el proveedor LLM**: Las herramientas descubiertas se formatean según el proveedor LLM (OpenAI en este caso).

Veamos cómo funciona este flujo internamente (basado en el código de la biblioteca `spade_llm`):

```python
# Versión simplificada del proceso interno
async def setup(self):
    # Inicializar sesión MCP
    self.mcp_session = MCPSession()
    
    # Registrar servidores MCP
    for server_config in self.mcp_servers:
        await self.mcp_session.register_server(server_config)
    
    # Descubrir herramientas
    tools = await self.mcp_session.list_all_tools()
    
    # Convertir herramientas al formato del proveedor LLM
    llm_tools = self.provider.format_tools(tools)
    
    # Configurar comportamiento LLM con herramientas
    self.llm_behaviour.set_tools(llm_tools)
```

## 4. Comunicación entre Agentes SPADE

### 4.1 Estructura de Comportamientos del Agente Humano

En SPADE, los agentes se comunican mediante comportamientos. En nuestro ejemplo, el agente humano tiene dos comportamientos clave:

```python
class SendBehaviour(CyclicBehaviour):
    # Envía mensajes al agente LLM
    
class ReceiveBehaviour(CyclicBehaviour):
    # Recibe mensajes del agente LLM
```

### 4.2 Flujo de Comunicación

El flujo de comunicación sigue este patrón:

```
┌─────────┐      ┌───────────────┐      ┌────────────────┐      ┌─────────────┐
│         │      │               │      │                │      │             │
│ Usuario │─────►│ SendBehaviour │─────►│ LLM Behaviour  │─────►│ MCP Server  │
│         │      │               │      │                │      │             │
└─────────┘      └───────────────┘      └────────────────┘      └─────────────┘
    ▲                                          │                       │
    │                                          ▼                       │
    │              ┌───────────────┐      ┌────────────┐               │
    │              │               │      │            │               │
    └──────────────┤ReceiveBehaviour◄─────┤  OpenAI    │◄──────────────┘
                   │               │      │            │
                   └───────────────┘      └────────────┘
```

### 4.3 Formato de Mensajes SPADE

Los mensajes SPADE incluyen varios componentes:

```python
msg = Message(to=smart_jid)
msg.body = message_to_send
msg.set_metadata("performative", "request")
```

- **to**: El destinatario del mensaje (JID del agente LLM)
- **body**: El contenido del mensaje (consulta del usuario)
- **metadata**: Información adicional sobre el mensaje (tipo de acción, etc.)

## 5. Procesamiento de Consultas y Herramientas

### 5.1 Decisión de Herramientas por el LLM

Cuando el LLM recibe una consulta, decide si necesita usar herramientas basándose en:

1. El contenido de la consulta
2. Las herramientas disponibles
3. El contexto de la conversación

Este proceso se ve así internamente:

```python
# Versión simplificada del procesamiento del LLM
async def process_message(self, message):
    # Preparar el contexto con todas las herramientas disponibles
    context = {
        "message": message.body,
        "tools": self.available_tools
    }
    
    # Enviar a OpenAI para procesamiento
    response = await self.provider.generate_response(context)
    
    # Si la respuesta incluye llamadas a herramientas
    if "tool_calls" in response:
        for tool_call in response["tool_calls"]:
            # Ejecutar la herramienta a través del MCP
            tool_result = await self.mcp_session.call_tool(
                tool_call.name, tool_call.arguments
            )
            
            # Enviar resultado de vuelta al LLM para finalizar la respuesta
            final_response = await self.provider.generate_response_with_tool_results(
                context, tool_result
            )
            
    # Enviar respuesta final al usuario
    response_msg = Message(to=message.sender.jid)
    response_msg.body = final_response
    await self.send(response_msg)
```

### 5.2 Formato de Herramientas MCP para OpenAI

Las herramientas MCP se transforman al formato esperado por OpenAI:

```python
# Ejemplo de formato de herramienta para OpenAI
{
    "type": "function",
    "function": {
        "name": "get_weather_forecast",
        "description": "Obtiene la previsión del tiempo para Valencia",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Fecha en formato YYYY-MM-DD"
                }
            },
            "required": ["date"]
        }
    }
}
```

Este formato permite que OpenAI entienda:
- Qué herramientas están disponibles
- Qué parámetros necesita cada una
- Cuándo y cómo usar cada herramienta

## 6. Ciclo Completo de una Consulta

Veamos el ciclo completo de una consulta, desde el usuario hasta la respuesta:

### 6.1 Diagrama de Secuencia

```
Usuario        HumanAgent      LLMAgent        MCPSession      OpenAI         ValenciaSmart
   |               |               |               |               |               |
   |---Consulta--->|               |               |               |               |
   |               |---Mensaje---->|               |               |               |
   |               |               |---Procesa---->|               |               |
   |               |               |               |---Consulta--->|               |
   |               |               |               |               |---¿Herramientas?--->|
   |               |               |               |               |<--Lista herramientas-|
   |               |               |               |               |--Decide usar-->|
   |               |               |               |               |   herramienta  |
   |               |               |               |<--Llamada a---|               |
   |               |               |               |  herramienta  |               |
   |               |               |               |---Ejecuta---->|               |
   |               |               |               |   herramienta |               |
   |               |               |               |<--Resultado---|               |
   |               |               |               |---Resultado-->|               |
   |               |               |<--Respuesta---|               |               |
   |               |<--Mensaje-----|               |               |               |
   |<--Respuesta---|               |               |               |               |
   |               |               |               |               |               |
```

### 6.2 Ejemplo Concreto

Tomemos una consulta específica: "¿Qué tiempo hará mañana en Valencia?"

1. **Usuario → HumanAgent**:
   - El usuario escribe la consulta
   - El `input_loop` recoge la entrada y la almacena en `message_to_send`

2. **HumanAgent → LLMAgent**:
   - `SendBehaviour` crea un mensaje SPADE con la consulta
   - El mensaje se envía al LLMAgent

3. **LLMAgent → OpenAI**:
   - El LLMAgent procesa el mensaje
   - Prepara un contexto con la consulta y las herramientas disponibles
   - Envía todo a OpenAI

4. **OpenAI → Decisión de Herramientas**:
   - OpenAI analiza la consulta sobre el tiempo
   - Decide que necesita la herramienta `get_weather_forecast`
   - Genera una llamada a la herramienta con los parámetros adecuados

5. **LLMAgent → MCP Server**:
   - El LLMAgent recibe la llamada a la herramienta
   - Traduce la llamada al formato MCP
   - Envía la solicitud al servidor MCP de ValenciaSmart

6. **MCP Server → Ejecución**:
   - El servidor MCP ejecuta la herramienta `get_weather_forecast`
   - Obtiene los datos meteorológicos
   - Devuelve los resultados

7. **LLMAgent → Finalización**:
   - El LLMAgent recibe los resultados de la herramienta
   - Envía estos resultados de vuelta a OpenAI
   - OpenAI genera una respuesta final en lenguaje natural

8. **LLMAgent → HumanAgent**:
   - El LLMAgent crea un mensaje SPADE con la respuesta
   - Envía el mensaje al HumanAgent

9. **HumanAgent → Usuario**:
   - `ReceiveBehaviour` recibe el mensaje
   - Muestra la respuesta al usuario
   - Prepara el sistema para la siguiente consulta
