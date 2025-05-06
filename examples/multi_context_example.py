"""
Demostración de manejo de múltiples contextos en SPADE_LLM.

Este ejemplo permite al usuario mantener dos conversaciones paralelas con un
mismo agente LLM a través de dos agentes humanos intermediarios distintos.
El sistema debería mantener el contexto de cada conversación separado.

Esta versión utiliza directamente la clase LLMAgent en lugar de crear
un comportamiento LLMBehaviour manualmente.
"""

import asyncio
import getpass
import logging
import os
import uuid
import spade
from spade.agent import Agent
from spade.template import Template
from spade.message import Message
from spade.behaviour import CyclicBehaviour

from spade_llm.agent import LLMAgent
from spade_llm.providers.open_ai_provider import OpenAILLMProvider
from spade_llm.utils import load_env_vars

# Configuración de logging
logger = logging.getLogger("multi_context_example")


class HumanAgent(Agent):
    """Agente intermediario que transmite mensajes entre el usuario real y el agente LLM."""

    class SendBehaviour(CyclicBehaviour):
        """Comportamiento para enviar mensajes al agente LLM."""

        async def run(self):
            message_to_send = self.get("message_to_send")
            if message_to_send:
                smart_jid = self.get("smart_agent_jid")
                msg = Message(to=smart_jid)
                msg.body = message_to_send
                msg.set_metadata("performative", "request")  # Metadata para el enrutamiento

                # Asegurar que el mensaje tenga un thread_id consistente
                if not self.agent.get("current_thread_id"):
                    thread_id = str(uuid.uuid4())
                    self.agent.set("current_thread_id", thread_id)

                msg.thread = self.agent.get("current_thread_id")

                print(f"[{self.agent.name}] Enviando: '{message_to_send}' a {smart_jid}")
                print(f"[{self.agent.name}] Thread ID: {msg.thread}")

                # Debug adicional
                logger.debug(f"Enviando mensaje desde {self.agent.name}")

                await self.send(msg)

                # Limpiar el mensaje para evitar reenvío
                self.set("message_to_send", None)

            await asyncio.sleep(0.1)

    class ReceiveBehaviour(CyclicBehaviour):
        """Comportamiento para recibir respuestas del agente LLM."""

        async def on_start(self):
            logger.debug(f"Iniciando comportamiento de recepción para {self.agent.name}")

        async def run(self):
            response = await self.receive(timeout=0.1)
            if response:
                # Verificar si esta respuesta corresponde al thread actual
                my_thread = self.agent.get("current_thread_id")
                if my_thread and response.thread and my_thread != response.thread:
                    logger.warning(f"THREAD MISMATCH: Recibido {response.thread}, esperaba {my_thread}")

                # Mantener consistente el thread_id (por seguridad)
                if response.thread and not self.agent.get("current_thread_id"):
                    self.agent.set("current_thread_id", response.thread)

                # Mostrar respuesta con información clara de thread
                print(f"\n[{self.agent.name}] Respuesta: '{response.body}'")
                print(f"[{self.agent.name}] Thread ID: {response.thread}")

                # Información adicional de depuración
                logger.debug(f"Recibida respuesta para {self.agent.name} con thread={response.thread}")

                # Señalizar que estamos listos para nueva entrada
                self.agent.set("waiting_for_input", True)

            await asyncio.sleep(0.1)


async def async_input(prompt: str = "") -> str:
    """
    Ejecuta input() en un hilo separado para no bloquear el bucle de eventos.
    """
    return await asyncio.to_thread(input, prompt)


async def main():
    # Cargar variables de entorno
    load_env_vars()

    # Log para validar que estamos usando la versión corregida
    logger.info("Iniciando ejemplo de múltiples contextos - VERSIÓN CON LLMAgent")

    # Obtener la API key de OpenAI
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        openai_api_key = await async_input("Ingresa tu API key de OpenAI: ")
        os.environ["OPENAI_API_KEY"] = openai_api_key

    # Configurar agente LLM
    llm_jid = await async_input("JID del Agente LLM: ")
    llm_password = getpass.getpass("Contraseña del Agente LLM: ")

    # Crear el proveedor de LLM
    openai_provider = OpenAILLMProvider(
        api_key=openai_api_key,
        model="gpt-3.5-turbo"  # Modelo más económico para pruebas
    )

    # Crear el agente LLM usando la clase LLMAgent directamente
    llm_agent = LLMAgent(
        jid=llm_jid,
        password=llm_password,
        provider=openai_provider,
        system_prompt="""Eres un asistente útil y amigable.
        Si te preguntan sobre física clásica, asegúrate de responder sobre física clásica.
        Si te preguntan sobre física cuántica, asegúrate de responder sobre física cuántica.
        """,
        # Configuración adicional para el comportamiento
        termination_markers=["<TASK_COMPLETE>", "<END>", "<DONE>"],
        max_interactions_per_conversation=10,
        on_conversation_end=lambda conv_id, reason: logger.info(f"Conversación {conv_id} finalizada: {reason}")
    )

    # Iniciar el agente LLM
    await llm_agent.start()
    print(f"Agente LLM iniciado: {llm_jid}")

    # Configurar los dos agentes humanos
    human1_jid = await async_input("JID del Agente Humano 1: ")
    human1_password = getpass.getpass("Contraseña del Agente Humano 1: ")
    human1 = HumanAgent(human1_jid, human1_password)

    human2_jid = await async_input("JID del Agente Humano 2: ")
    human2_password = getpass.getpass("Contraseña del Agente Humano 2: ")
    human2 = HumanAgent(human2_jid, human2_password)

    # Inicializar los agentes humanos
    for human in [human1, human2]:
        human.set("smart_agent_jid", llm_jid)
        human.set("message_to_send", None)
        human.set("waiting_for_input", True)
        human.set("current_thread_id", None)  # Se establecerá automáticamente mediante UUID

        # Añadir comportamientos
        send_behaviour = HumanAgent.SendBehaviour()
        receive_behaviour = HumanAgent.ReceiveBehaviour()
        human.add_behaviour(send_behaviour)
        human.add_behaviour(receive_behaviour)

    # Iniciar los agentes humanos
    await human1.start()
    await human2.start()
    print("Agentes humanos iniciados")

    print("\n===== PRUEBA DE MANEJO DE MÚLTIPLES CONTEXTOS =====")
    print("Puedes mantener dos conversaciones paralelas con el mismo agente LLM.")
    print("Cada agente humano mantendrá su propio contexto de conversación.")
    print()
    print("Comandos especiales:")
    print("  'agente1': Cambiar a conversación con Agente 1")
    print("  'agente2': Cambiar a conversación con Agente 2")
    print("  'salir': Terminar el programa")
    print()

    # Inicialmente interactuar con el primer agente
    current_agent = human1
    print(f"Conversando con {current_agent}. Escribe tu mensaje:")

    # Bucle principal de interacción
    while True:
        try:
            user_input = await async_input(f"[{current_agent.name}]> ")

            # Comandos para cambiar de agente o salir
            if user_input.lower() == "agente1":
                current_agent = human1
                print(f"Cambiado a {current_agent.name}")
                continue
            elif user_input.lower() == "agente2":
                current_agent = human2
                print(f"Cambiado a {current_agent.name}")
                continue
            elif user_input.lower() in ["salir", "exit"]:
                break

            # Enviar mensaje a través del agente actual
            current_agent.set("message_to_send", user_input)

            # Pequeña pausa para permitir el procesamiento
            await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            print("\nSaliendo del programa...")
            break
        except Exception as e:
            print(f"Error: {e}")

    # Detener todos los agentes
    await human1.stop()
    await human2.stop()
    await llm_agent.stop()
    print("Todos los agentes detenidos. Fin del programa.")


if __name__ == "__main__":
    spade.run(main())