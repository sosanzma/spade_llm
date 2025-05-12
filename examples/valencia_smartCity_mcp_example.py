"""
Valencia Smart City MCP Example

Este ejemplo demuestra cómo un agente SPADE puede utilizar el MCP de Valencia Smart City
para obtener información meteorológica y otros datos de la ciudad.

El ejemplo configura:
1. Un agente LLM con acceso al MCP "ValenciaSmart"
2. Un agente humano interactivo que enviará consultas del usuario y mostrará respuestas
3. Un sistema de comunicación mejorado entre ambos agentes
"""

import asyncio
import getpass
import os
import logging
import sys

import spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template
from dotenv import load_dotenv

from spade_llm.agent import LLMAgent
from spade_llm.mcp import StdioServerConfig
from spade_llm.providers.open_ai_provider import OpenAILLMProvider
from spade_llm.utils import load_env_vars

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("valencia_smart_mcp")


class HumanAgent(Agent):
    """Agente que simula a un usuario humano que interactúa con el agente LLM"""

    class SendBehaviour(CyclicBehaviour):
        """Comportamiento para enviar mensajes pendientes al agente LLM"""

        async def run(self):
            message_to_send = self.get("message_to_send")
            if message_to_send:
                smart_jid = self.get("smart_agent_jid")
                msg = Message(to=smart_jid)
                msg.body = message_to_send
                msg.set_metadata("performative", "request")

                logger.info(f"Enviando mensaje al agente LLM: '{message_to_send}'")
                await self.send(msg)

                # Limpiar el mensaje para evitar reenvíos
                self.set("message_to_send", None)
                # Indicar que estamos esperando respuesta
                self.set("waiting_response", True)
                print("\033[90m(Esperando respuesta...)\033[0m")

            await asyncio.sleep(0.1)

    class ReceiveBehaviour(CyclicBehaviour):
        """Comportamiento para recibir y mostrar mensajes del agente LLM"""

        async def on_start(self):
            logger.info("Comportamiento de recepción del agente humano iniciado")

        async def run(self):
            response = await self.receive(timeout=1.0)

            if response:
                print(f"\n\033[92m[Agente LLM]:\033[0m {response.body}\n")

                logger.debug(f"Mensaje recibido de {response.sender} con thread: {response.thread}")

                self.set("waiting_response", False)

                print("\033[93m[Tú]:\033[0m ", end="", flush=True)

            if self.get("should_exit"):
                self.kill()

            await asyncio.sleep(0.1)


async def async_input(prompt: str = "") -> str:
    """
    Ejecutar input() en un hilo separado para evitar bloquear el bucle de eventos.
    """
    return await asyncio.to_thread(input, prompt)


async def input_loop(human_agent):
    """Bucle para manejar la entrada del usuario y la comunicación con el agente LLM"""

    print("\n¡Bienvenido al agente MCP de Valencia Smart City!")
    print("Puedes hacer preguntas sobre Valencia (clima, tráfico, etc.)")
    print("Escribe 'salir' para terminar.\n")

    # Mostrar prompt inicial
    print("\033[93m[Tú]:\033[0m ", end="", flush=True)

    try:
        while not human_agent.get("should_exit"):
            if not human_agent.get("waiting_response"):
                user_input = await async_input()

                # Verificar si el usuario quiere salir
                if user_input.lower() in ("salir", "exit", "quit"):
                    human_agent.set("should_exit", True)
                    break

                if user_input.strip():
                    human_agent.set("message_to_send", user_input)

            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        human_agent.set("should_exit", True)

    print("\nSaliendo...")


async def main():
    """Función principal que configura y ejecuta los agentes"""
    load_dotenv()

    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        openai_api_key = getpass.getpass("Introduce tu API key de OpenAI: ")
        os.environ["OPENAI_API_KEY"] = openai_api_key

    print("\n--- Configuración del Agente LLM ---")
    llm_jid = input("JID del agente LLM: ")
    llm_password = getpass.getpass("Contraseña del agente LLM: ")

    print("\n--- Configuración del Agente Humano ---")
    human_jid = input("JID del agente humano: ")
    human_password = getpass.getpass("Contraseña del agente humano: ")

    # Configurar el servidor MCP de Valencia Smart City
    valencia_smart_mcp = StdioServerConfig(
        name="ValenciaSmart",
        command="uv",
        args= ["run", "valencia_traffic_mcp.py"],
        cache_tools=True
    )

    provider = OpenAILLMProvider(
        api_key=openai_api_key,
        model="gpt-4o-mini"
    )

    llm_agent = LLMAgent(
        jid=llm_jid,
        password=llm_password,
        provider=provider,
        system_prompt=(
            "Eres un asistente útil con acceso a herramientas de información sobre Valencia. "
            "Puedes proporcionar información sobre el clima, tráfico y otros datos de la ciudad. "
            "Usa las herramientas disponibles para dar respuestas precisas y detalladas. "
            "Cuando no tengas información suficiente, indícalo claramente."
        ),
        mcp_servers=[valencia_smart_mcp],
        termination_markers=["<FIN>", "<COMPLETADO>"],
        max_interactions_per_conversation=20,
        on_conversation_end=lambda conv_id, reason: logger.info(f"Conversación {conv_id} finalizada: {reason}")
    )

    human_agent = HumanAgent(
        jid=human_jid,
        password=human_password
    )

    human_agent.set("smart_agent_jid", llm_jid)
    human_agent.set("message_to_send", None)
    human_agent.set("waiting_response", False)
    human_agent.set("should_exit", False)

    send_behaviour = HumanAgent.SendBehaviour()
    receive_behaviour = HumanAgent.ReceiveBehaviour()
    receive_template = Template()
    receive_template.sender = llm_jid


    human_agent.add_behaviour(send_behaviour)
    human_agent.add_behaviour(receive_behaviour, receive_template)

    await llm_agent.start()
    print(f"Agente LLM {llm_jid} iniciado")

    await human_agent.start()
    print(f"Agente humano {human_jid} iniciado")


    input_task = asyncio.create_task(input_loop(human_agent))

    try:
        await input_task
    except asyncio.CancelledError:
        logger.info("Bucle de entrada cancelado")

    await human_agent.stop()
    await llm_agent.stop()
    print("Agentes detenidos")


if __name__ == "__main__":
    spade.run(main())
