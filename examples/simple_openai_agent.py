"""
Demostración simple de dos agentes SPADE comunicándose, utilizando
un LLM real de OpenAI en lugar de respuestas simuladas.
"""

import asyncio
import getpass
import logging
import os
import spade
from spade.agent import Agent
from spade.template import Template
from spade.message import Message
from spade.behaviour import CyclicBehaviour

from spade_llm.agent import LLMAgent
from spade_llm.providers.open_ai_provider import OpenAILLMProvider
from spade_llm.utils import load_env_vars

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("example")


class HumanAgent(Agent):
    """Agente que actúa como un usuario humano que chatea con el LLM."""

    class SendBehaviour(CyclicBehaviour):
        """Comportamiento para enviar mensajes pendientes al agente inteligente."""

        async def run(self):
            message_to_send = self.get("message_to_send")
            if message_to_send:
                smart_jid = self.get("smart_agent_jid")
                msg = Message(to=smart_jid)
                msg.body = message_to_send
                msg.set_metadata("performative", "request")  # Metadata para el enrutamiento
                print(f"Humano enviando: '{message_to_send}' a {smart_jid}")
                await self.send(msg)
                # Limpiar el mensaje para evitar reenvío
                self.set("message_to_send", None)
            await asyncio.sleep(0.1)

    class ReceiveBehaviour(CyclicBehaviour):
        """Comportamiento para recibir y mostrar mensajes del agente inteligente."""

        async def run(self):
            response = await self.receive(timeout=0.1)
            if response:
                print(f"\nRespuesta del agente inteligente: '{response.body}'")
            await asyncio.sleep(0.1)


async def async_input(prompt: str = "") -> str:
    """
    Ejecuta input() en un hilo separado para no bloquear el bucle de eventos.
    """
    return await asyncio.to_thread(input, prompt)


async def main():
    # Cargar variables de entorno desde el archivo .env
    env_vars = load_env_vars()
    
    # Obtener la API key de OpenAI de las variables de entorno o pedir al usuario
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        openai_api_key = await async_input("Ingresa tu API key de OpenAI: ")
        os.environ["OPENAI_API_KEY"] = openai_api_key

    # Creación del agente inteligente
    smart_jid = await async_input("Ingresa el JID del Agente Inteligente: ")
    smart_password = getpass.getpass("Ingresa la contraseña del Agente Inteligente: ")

    # Crear el proveedor OpenAI
    openai_provider = OpenAILLMProvider(
        api_key=openai_api_key,
        model="gpt-4o-mini"  # O el modelo que prefieras
    )

    # Crear el agente LLM con toda la configuración en un solo paso
    smart_agent = LLMAgent(
        jid=smart_jid, 
        password=smart_password,
        provider=openai_provider,
        system_prompt="Eres un asistente útil y amigable. Responde de manera concisa y clara.",
        termination_markers=["<TASK_COMPLETE>", "<END>", "<DONE>"],
        max_interactions_per_conversation=10,
        on_conversation_end=lambda conv_id, reason: print(f"Conversación {conv_id} terminada: {reason}")
    )

    # Iniciar el SmartAgent
    await smart_agent.start()
    print(f"Agente inteligente {smart_jid} está en ejecución.")

    # Configuración y arranque del HumanAgent (agente que simula usuario humano)
    human_jid = await async_input("Ingresa el JID del Agente Humano: ")
    human_password = getpass.getpass("Ingresa la contraseña del Agente Humano: ")

    human_agent = HumanAgent(human_jid, human_password)
    human_agent.set("smart_agent_jid", smart_jid)
    human_agent.set("message_to_send", None)

    # Añadir comportamientos para enviar y recibir mensajes
    send_behaviour = HumanAgent.SendBehaviour()
    receive_behaviour = HumanAgent.ReceiveBehaviour()
    human_agent.add_behaviour(send_behaviour)
    human_agent.add_behaviour(receive_behaviour)

    await human_agent.start()
    print(f"Agente humano {human_jid} está en ejecución.")

    print("\nAhora puedes chatear con el agente inteligente. Escribe 'exit' para salir.\n")

    # Bucle principal de interacción para leer entrada del usuario de forma asíncrona
    while True:
        user_input = await async_input("> ")
        if user_input.lower() == "exit":
            break
        human_agent.set("message_to_send", user_input)
        await asyncio.sleep(0.2)

    await human_agent.stop()
    await smart_agent.stop()
    print("Agentes detenidos. ¡Adiós!")


if __name__ == "__main__":
    spade.run(main())
