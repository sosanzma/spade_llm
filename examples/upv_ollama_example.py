"""
Ejemplo de uso del servidor Ollama UPV con SPADE_LLM

Este ejemplo muestra cómo configurar y usar el servidor Ollama interno 
de la UPV con agentes SPADE_LLM.

Requisitos:
- Estar conectado a la VPN UPV
- Tener credenciales XMPP válidas
"""

import asyncio
import getpass
import spade

from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.providers import LLMProvider

async def main():
    print("🏫 === SPADE_LLM con Servidor Ollama UPV === 🏫\n")
    
    # Configuración del servidor UPV (descubierta por diagnóstico)
    UPV_OLLAMA_BASE_URL = "http://ollama.gti-ia.upv.es/v1"
    
    print(f"🔗 Servidor: {UPV_OLLAMA_BASE_URL}")
    print("📋 Configuración para UPV:")
    print("   - Puerto: 80 (HTTP estándar)")
    print("   - Sin autenticación requerida")
    print("   - Requiere VPN UPV activa\n")
    
    # Credenciales XMPP
    print("🔐 Configuración XMPP:")
    smart_jid = input("Smart Agent JID: ")
    smart_password = getpass.getpass("Smart Agent password: ")
    
    human_jid = input("Human Agent JID: ")
    human_password = getpass.getpass("Human Agent password: ")
    
    # Lista de modelos disponibles comunes en UPV
    available_models = [
        "qwen2.5:latest",  # 4.4GB - Recomendado para uso general
        "meditron:7b",     # 3.6GB - Especializado en medicina
        "llama4:scout",    # 62.8GB - Muy grande, alto rendimiento
    ]
    
    print(f"\n🤖 Modelos disponibles detectados:")
    for i, model in enumerate(available_models, 1):
        print(f"   {i}. {model}")
    
    # Selección de modelo
    model_choice = input(f"\nSelecciona modelo (1-{len(available_models)}) [1]: ").strip()
    if not model_choice:
        model_choice = "1"
    
    try:
        selected_model = available_models[int(model_choice) - 1]
    except (ValueError, IndexError):
        selected_model = available_models[0]
    
    print(f"✅ Modelo seleccionado: {selected_model}")
    
    # Crear proveedor Ollama para UPV
    print(f"\n🔧 Configurando proveedor Ollama UPV...")
    
    provider = LLMProvider.create_ollama(
        model=selected_model,
        base_url=UPV_OLLAMA_BASE_URL,
        temperature=0.7,
        timeout=60.0  # Timeout generoso para modelos grandes
    )
    
    # Crear agente LLM
    print(f"🤖 Creando Smart Agent...")
    
    smart_agent = LLMAgent(
        jid=smart_jid,
        password=smart_password,
        provider=provider,
        system_prompt=f"""Eres un asistente inteligente ejecutándose en el servidor Ollama de la UPV.

Información del sistema:
- Modelo: {selected_model}
- Servidor: Universidad Politécnica de Valencia
- Tipo: Modelo open-source local

Responde de manera útil y concisa. Si te preguntan sobre tu configuración, 
menciona que estás ejecutándose en la infraestructura de la UPV."""
    )
    
    # Crear agente de chat humano
    print(f"👤 Creando Human Interface Agent...")
    
    chat_agent = ChatAgent(
        jid=human_jid,
        password=human_password,
        target_agent_jid=smart_jid
    )
    
    # Iniciar agentes
    try:
        print(f"\n🚀 Iniciando agentes...")
        await smart_agent.start()
        print(f"✅ Smart Agent iniciado: {smart_jid}")
        
        await chat_agent.start()
        print(f"✅ Chat Agent iniciado: {human_jid}")
        
        print(f"\n" + "="*60)
        print(f"🎓 CHAT CON SERVIDOR OLLAMA UPV ACTIVO")
        print(f"="*60)
        print(f"🤖 Modelo: {selected_model}")
        print(f"🔗 Servidor: ollama.gti-ia.upv.es:80")
        print(f"💬 Puedes empezar a chatear. Escribe 'exit' para salir.")
        print(f"🔬 Pregunta al modelo sobre ciencia, programación, medicina, etc.")
        print(f"-"*60)
        
        # Ejecutar chat interactivo
        await chat_agent.run_interactive(
            input_prompt="UPV-Ollama> ",
            exit_command="exit"
        )
        
    except Exception as e:
        print(f"❌ Error al iniciar agentes: {e}")
        print(f"💡 Asegúrate de:")
        print(f"   - Estar conectado a VPN UPV")
        print(f"   - Tener credenciales XMPP correctas") 
        print(f"   - El servidor Ollama esté disponible")
        
    finally:
        # Cleanup
        print(f"\n🔄 Deteniendo agentes...")
        try:
            await chat_agent.stop()
            await smart_agent.stop()
            print(f"✅ Agentes detenidos correctamente")
        except:
            pass

# Función para probar conectividad antes de ejecutar main
async def test_connectivity():
    """Prueba rápida de conectividad con el servidor UPV"""
    import requests
    
    print("🔍 Probando conectividad con servidor UPV...")
    
    try:
        response = requests.get("http://ollama.gti-ia.upv.es/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"✅ Servidor accesible: {len(models)} modelos disponibles")
            return True
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)[:100]}...")
        print(f"💡 Soluciones:")
        print(f"   - Verifica conexión VPN UPV")
        print(f"   - Ejecuta: python examples/diagnose_ollama_server.py")
        return False

if __name__ == "__main__":
    # Prueba conectividad primero
    if asyncio.run(test_connectivity()):
        # Si la conectividad es OK, ejecuta la aplicación principal
        spade.run(main())
    else:
        print(f"\n❌ No se puede conectar al servidor UPV. Revisa la configuración.")
