# SPADE_LLM Context Management Guide

## Visión General

La gestión de contexto en SPADE_LLM controla cómo se mantiene y filtra el historial conversacional entre los agentes y los LLMs. Esta guía documenta las tres estrategias implementadas: `NoContextManagement`, `WindowSizeContext`, y la nueva `SmartWindowSizeContext`.

## Arquitectura del Sistema de Context Management

### Clase Base: `ContextManagement`

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class ContextManagement(ABC):
    @abstractmethod
    def apply_context_strategy(self, 
                              messages: List[ContextMessage], 
                              system_prompt: Optional[str] = None) -> List[ContextMessage]:
        """Aplica la estrategia de gestión de contexto a los mensajes"""
        pass
    
    @abstractmethod
    def get_stats(self, total_messages: int) -> Dict[str, Any]:
        """Obtiene estadísticas sobre la gestión de contexto"""
        pass
```

## Estrategias Implementadas

### 1. NoContextManagement (Predeterminada)

**Comportamiento:** Mantiene todos los mensajes sin aplicar ningún filtro o limitación.

```python
from spade_llm.context import NoContextManagement

context_mgmt = NoContextManagement()
```

**Características:**
- ✅ Preserva toda la información conversacional
- ✅ Sin pérdida de contexto
- ❌ Crecimiento ilimitado de memoria
- ❌ Posibles desbordamientos de contexto del LLM

**Casos de uso:**
- Conversaciones cortas (< 10 intercambios)
- Sesiones de depuración donde se necesita historial completo
- Análisis post-conversación

### 2. WindowSizeContext (Básica)

**Comportamiento:** Implementa una ventana deslizante que mantiene solo los últimos N mensajes.

```python
from spade_llm.context import WindowSizeContext

# Mantener últimos 20 mensajes
context_mgmt = WindowSizeContext(max_messages=20)
```

**Características:**
- ✅ Control de memoria predecible
- ✅ Previene desbordamiento de contexto
- ❌ Pérdida de contexto inicial importante
- ❌ No diferencia entre tipos de mensajes

**Casos de uso:**
- Conversaciones largas con memoria limitada
- Chatbots con recursos limitados
- Sesiones de monitoreo continuo

### 3. SmartWindowSizeContext (Avanzada) 🆕

**Comportamiento:** Gestión inteligente que combina ventana deslizante con retención selectiva de mensajes críticos.

#### Configuración Básica

```python
from spade_llm.context import SmartWindowSizeContext

# Comportamiento estándar (equivale a WindowSizeContext)
basic_context = SmartWindowSizeContext(max_messages=20)

# Con preservación de mensajes iniciales
initial_preserve = SmartWindowSizeContext(
    max_messages=20,
    preserve_initial=3
)

# Con priorización de herramientas
tool_priority = SmartWindowSizeContext(
    max_messages=20,
    prioritize_tools=True
)

# Configuración completa
smart_context = SmartWindowSizeContext(
    max_messages=20,
    preserve_initial=3,
    prioritize_tools=True
)
```

#### Parámetros de Configuración

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `max_messages` | `int` | 20 | Número máximo de mensajes en contexto |
| `preserve_initial` | `int` | 0 | Número de mensajes iniciales a preservar siempre |
| `prioritize_tools` | `bool` | False | Si priorizar resultados de herramientas |

#### Algoritmo de Retención Inteligente

```
1. Si total_messages ≤ max_messages → Retornar todos
2. Si preserve_initial = 0 y prioritize_tools = False → Comportamiento básico
3. Si preserve_initial > 0 → Preservar iniciales + completar con recientes
4. Si prioritize_tools = True → Priorizar tool results + completar espacio
5. Si ambos activos → Combinar preservación + priorización
```

#### Comportamientos Detallados

##### Preservación de Mensajes Iniciales

```python
# Ejemplo: 30 mensajes total, ventana=10, preserve_initial=3
# Resultado: [msg1, msg2, msg3] + [msg24, msg25, ..., msg30]

context = SmartWindowSizeContext(max_messages=10, preserve_initial=3)
```

**Ventaja:** Preserva el objetivo original y contexto fundamental de la conversación.

##### Priorización de Herramientas

```python
# Ejemplo: Prioriza todos los mensajes con role="tool"
context = SmartWindowSizeContext(max_messages=15, prioritize_tools=True)
```

**Algoritmo:**
1. Extraer todos los mensajes con `role="tool"`
2. Si tool_messages ≥ max_messages → Tomar últimos tool_messages
3. Sino → tool_messages + mensajes recientes hasta llenar ventana
4. Reordenar cronológicamente

##### Combinación Avanzada

```python
# Preservar contexto inicial + priorizar herramientas
context = SmartWindowSizeContext(
    max_messages=20, 
    preserve_initial=3, 
    prioritize_tools=True
)
```

**Algoritmo:**
1. Reservar espacio para mensajes iniciales
2. Aplicar priorización de herramientas al resto
3. Completar espacio disponible con mensajes recientes

## Casos de Uso Prácticos

### Planificación de Viajes

```python
# Preserva destino/fechas + resultados de APIs de hoteles/vuelos
trip_context = SmartWindowSizeContext(
    max_messages=25,
    preserve_initial=4,      # "Viaje a Valencia, 3 días, 800€, 2 personas"
    prioritize_tools=True    # Resultados de Airbnb, TicketMaster, etc.
)
```

### Revisión de Código

```python
# Mantiene requisitos + análisis de herramientas
code_context = SmartWindowSizeContext(
    max_messages=30,
    preserve_initial=2,      # Requisitos y especificaciones
    prioritize_tools=True    # Resultados de linters, tests, análisis
)
```

### Monitoreo de Sistemas

```python
# Configuración inicial + estados críticos recientes
monitor_context = SmartWindowSizeContext(
    max_messages=15,
    preserve_initial=1,      # Configuración de monitoreo
    prioritize_tools=True    # Estados de servicios, métricas críticas
)
```

### Investigación y Análisis

```python
# Pregunta inicial + datos de herramientas de búsqueda
research_context = SmartWindowSizeContext(
    max_messages=40,
    preserve_initial=2,      # Pregunta de investigación + contexto
    prioritize_tools=True    # Resultados de Wikipedia, DuckDuckGo, APIs
)
```

## Integración con LLMAgent

### Configuración en Constructor

```python
from spade_llm.agent import LLMAgent
from spade_llm.context import SmartWindowSizeContext

# Crear estrategia de contexto
smart_context = SmartWindowSizeContext(
    max_messages=20,
    preserve_initial=3,
    prioritize_tools=True
)

# Integrar en agente
agent = LLMAgent(
    jid="agent@example.com",
    password="password",
    provider=llm_provider,
    context_management=smart_context,  # ← Configuración aquí
    system_prompt="Eres un asistente con contexto inteligente..."
)
```

### Actualización Dinámica

```python
# Cambiar estrategia durante ejecución
new_context = SmartWindowSizeContext(max_messages=30, preserve_initial=5)
agent.update_context_management(new_context)

# Obtener estadísticas
stats = agent.get_context_stats()
print(f"Mensajes en contexto: {stats['messages_in_context']}")
```

## Estadísticas y Monitoreo

### Obtención de Estadísticas

```python
context = SmartWindowSizeContext(
    max_messages=20, 
    preserve_initial=3, 
    prioritize_tools=True
)

# Obtener stats para 50 mensajes totales
stats = context.get_stats(total_messages=50)
```

### Formato de Estadísticas

```python
{
    "strategy": "smart_window_size",
    "max_messages": 20,
    "preserve_initial": 3,
    "prioritize_tools": True,
    "total_messages": 50,
    "messages_in_context": 20,
    "messages_dropped": 30
}
```

## Comparación de Estrategias

| Característica | NoContext | WindowSize | SmartWindowSize |
|---------------|-----------|------------|-----------------|
| **Control de memoria** | ❌ | ✅ | ✅ |
| **Preserva contexto inicial** | ✅ | ❌ | ✅ (opcional) |
| **Prioriza herramientas** | ✅ | ❌ | ✅ (opcional) |
| **Complejidad configuración** | Ninguna | Baja | Media |
| **Rendimiento** | O(1) | O(1) | O(n log n) |
| **Uso de memoria** | Ilimitado | Limitado | Limitado |

## Mejores Prácticas

### Configuración Recomendada por Escenario

**Conversaciones cortas (< 15 mensajes):**
```python
context = NoContextManagement()
```

**Conversaciones largas simples:**
```python
context = WindowSizeContext(max_messages=25)
```

**Workflows complejos con herramientas:**
```python
context = SmartWindowSizeContext(
    max_messages=30,
    preserve_initial=2,
    prioritize_tools=True
)
```

**Sesiones de análisis profundo:**
```python
context = SmartWindowSizeContext(
    max_messages=50,
    preserve_initial=3,
    prioritize_tools=True
)
```

### Configuración de preserve_initial

- **preserve_initial=1-2:** Para objetivos simples
- **preserve_initial=3-4:** Para contextos complejos con múltiples requisitos
- **preserve_initial=5+:** Para especificaciones muy detalladas

### Configuración de max_messages

- **10-15:** Para memoria limitada o modelos pequeños
- **20-30:** Configuración estándar recomendada
- **40-60:** Para análisis complejos con muchas herramientas
- **60+:** Solo para casos especiales con modelos grandes

## Ejemplos de Código Completo

### Ejemplo Básico

```python
import asyncio
from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.context import SmartWindowSizeContext
from spade_llm.providers import LLMProvider

async def main():
    # Configurar contexto inteligente
    smart_context = SmartWindowSizeContext(
        max_messages=20,
        preserve_initial=3,
        prioritize_tools=True
    )
    
    # Crear proveedor
    provider = LLMProvider.create_ollama(
        model="gemma2:2b",
        base_url="http://ollama.gti-ia.upv.es/v1"
    )
    
    # Crear agente con contexto inteligente
    agent = LLMAgent(
        jid="smart_agent@example.com",
        password="password",
        provider=provider,
        context_management=smart_context,
        system_prompt="Asistente con gestión inteligente de contexto"
    )
    
    await agent.start()
    # ... uso del agente
    await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Ejemplo con Monitoreo

```python
async def context_monitoring_example():
    context = SmartWindowSizeContext(
        max_messages=15,
        preserve_initial=2,
        prioritize_tools=True
    )
    
    agent = LLMAgent(
        jid="monitor_agent@example.com",
        password="password",
        provider=provider,
        context_management=context
    )
    
    await agent.start()
    
    # Simular conversación larga
    for i in range(25):
        # ... interacciones del agente
        
        # Obtener estadísticas periódicamente
        if i % 5 == 0:
            stats = agent.get_context_stats()
            print(f"Iteración {i}: {stats['messages_in_context']} mensajes en contexto")
    
    await agent.stop()
```

## Futuras Mejoras

### Roadmap de Desarrollo

1. **Context Management basado en tokens** - Gestión por tokens en lugar de conteo de mensajes
2. **Estrategias semánticas** - Retención basada en relevancia semántica
3. **Context compression** - Compresión inteligente de mensajes largos
4. **Adaptive windows** - Ventanas que se ajustan dinámicamente
5. **Cross-conversation learning** - Aprendizaje de patrones entre conversaciones

### API Futura Propuesta

```python
# API futura (conceptual)
context = AdaptiveSmartContext(
    token_limit=4000,
    semantic_similarity_threshold=0.8,
    compression_enabled=True,
    adaptive_window=True
)
```

## Conclusión

La implementación de `SmartWindowSizeContext` proporciona un balance óptimo entre control de memoria y preservación de información crítica. Su diseño modular permite adaptarse a diferentes escenarios de uso manteniendo la simplicidad de configuración y la eficiencia en el rendimiento.

La estrategia es especialmente valiosa en workflows complejos con múltiples herramientas donde tanto el contexto inicial como los resultados de herramientas son fundamentales para la continuidad de la conversación.