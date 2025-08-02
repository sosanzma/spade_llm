# LLMBehaviour: Funcionamiento e Integración



spade_llm/
├── agent/
│   └── llm_agent.py     # Implementación principal del Agente LLM
├── behaviour/
│   └── llm_behaviour.py # Comportamiento especializado para LLM
├── context/
│   └── context_manager.py # Gestión de conversaciones y contexto
├── mcp/                 # MCP
├── providers/           # Abstracción para distintos proveedores LLM
├── tools/               # Definición e implementación de herramientas


## 1. Ciclo de Ejecución Principal

```
┌─────────────────────────────────────────────────────────────┐
│                    CICLO DE EJECUCIÓN                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ ┌───────────┐     ┌─────────────┐     ┌───────────────────┐ │
│ │ Recepción │     │ Preparación │     │ Verificación de   │ │
│ │ de mensaje│────▶│ y validación│────▶│ estado de         │ │
│ │           │     │             │     │ conversación      │ │
│ └───────────┘     └─────────────┘     └───────────────────┘ │
│         ▲                                        │          │
│         │                                        ▼          │
│ ┌───────────────┐                      ┌───────────────────┐│
│ │    Envío      │                      │   Actualización   ││
│ │  de respuesta │                      │    de contexto    ││
│ └───────────────┘                      └───────────────────┘│
│         ▲                                        │          │
│         │                                        ▼          │
│ ┌───────────────┐                      ┌───────────────────┐│
│ │  Verificación │                      │  Procesamiento    ││
│ │ de terminación│◀─────────────────────│   con LLM         ││
│ └───────────────┘                      └───────────────────┘│
│                                                 ▲           │
│                      ┌───────────────┐          │           │
│                      │  Ejecución    │          │           │
│                      │ de herramientas◀─────────┘           │
│                      │  (si aplica)  │                      │
│                      └───────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

## 2. Integración con ContextManager

```
┌───────────────────┐      ┌───────────────────────────────┐
│                   │      │         ContextManager        │
│                   │      │                               │
│                   │      │  ┌─────────────────────────┐  │
│                   │      │  │Conversation 1           │  │
│                   │      │  │  [msg1, msg2, ...]      │  │
│                   │      │  └─────────────────────────┘  │
│                   │      │                               │
│  LLMBehaviour     │      │  ┌─────────────────────────┐  │
│                   │──────┼─▶│Conversation 2           │  │
│ .add_message()    │      │  │  [msg1, tool_result1]   │  │
│ .add_tool_result()│      │  └─────────────────────────┘  │
│ .get_prompt()     │◀─────┼──│                         │  │
│                   │      │  │  System Prompt          │  │
│                   │      │  └─────────────────────────┘  │
└───────────────────┘      └───────────────────────────────┘
```




## 3. Flujo de Datos Completo

```
┌─────────────┐     ┌───────────────┐     ┌───────────────┐     ┌─────────────┐
│ SPADE       │     │ LLMBehaviour  │     │ Context       │     │ LLMProvider │
│ Framework   │     │               │     │ Manager       │     │             │
└─────────────┘     └───────────────┘     └───────────────┘     └─────────────┘
      │                     │                     │                     │
      │                     │                     │                     │
      │   1. Mensaje        │                     │                     │
      │─────────────────────>                     │                     │
      │                     │                     │                     │
      │                     │  2. Añadir mensaje  │                     │
      │                     │────────────────────>│                     │
      │                     │                     │                     │
      │                     │  3. Obtener prompt  │                     │
      │                     │<────────────────────│                     │
      │                     │                     │                     │
      │                     │         4. Solicitar herramientas         │
      │                     │────────────────────────────────────────────>
      │                     │                     │                     │
      │                     │        5. Especificaciones de herramientas│
      │                     │<────────────────────────────────────────────
      │                     │                     │                     │
      │                     │                     │                     │
      │                     │           ┌──────────────────┐            │
      │                     │───────────│6. Ejecutar       │            │
      │                     │           │   herramientas   │            │
      │                     │<──────────│   (si aplica)    │            │
      │                     │           └──────────────────┘            │
      │                     │                     │                     │
      │                     │  7. Añadir resultados                     │
      │                     │────────────────────>│                     │
      │                     │                     │                     │
      │                     │  8. Obtener prompt  │                     │
      │                     │<────────────────────│                     │
      │                     │                     │                     │
      │                     │        9. Solicitar respuesta final       │
      │                     │────────────────────────────────────────────>
      │                     │                     │                     │
      │                     │        10. Respuesta final                │
      │                     │<────────────────────────────────────────────
      │                     │                     │                     │
      │  11. Respuesta      │                     │                     │
      │<─────────────────────                     │                     │
      │                     │                     │                     │
```


