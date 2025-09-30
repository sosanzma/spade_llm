"""
CoordinatorAgent: Specialized agent for multi-agent coordination

This module provides a CoordinatorAgent class that extends LLMAgent
to coordinate multiple subordinate agents.

Architecture:
- Coordinator uses CoordinationContextManager to see ALL coordination messages
- Subagents are regular LLMAgent instances that only see their individual tasks
- Coordinator routes work sequentially and waits for responses before proceeding
- All coordination happens in a shared session ID for the coordinator's visibility
"""

from typing import List, Optional, Dict, Set, Union, Any
import time
from spade.message import Message
from spade_llm.agent.llm_agent import LLMAgent
from spade_llm.context.context_manager import ContextManager
from spade_llm.routing.types import RoutingFunction, RoutingResponse
from spade_llm.tools.llm_tool import LLMTool
from spade_llm.context._types import _sanitize_jid_for_name
class CoordinationContextManager(ContextManager):
    """
    Context manager specialized for coordination scenarios.

    Forces all subagent conversations to use the same coordination session ID,
    enabling shared context across multiple agent interactions.
    """

    def __init__(
        self,
        coordination_session: str,
        subagent_ids: Set[str],
        **kwargs
    ):
        super().__init__(**kwargs)
        self.coordination_session = coordination_session
        self._sanitize_jid_for_name = _sanitize_jid_for_name
        self.subagent_ids = subagent_ids

    def _get_coordination_conversation_id(self, msg: Message) -> str:
        """
        Override conversation ID logic for coordination.

        For messages involving subagents, use coordination session ID.
        For external messages, use standard logic.
        """
        sender_str = str(msg.sender)
        to_str = str(msg.to) if hasattr(msg, 'to') else ""

        # Check if subagent
        if (sender_str in self.subagent_ids or
            to_str in self.subagent_ids or
            msg.thread == self.coordination_session):
            return self.coordination_session

        # External conversation
        return msg.thread or f"{msg.sender}_{msg.to}"

    def add_message(self, message: Message, conversation_id: Optional[str] = None) -> None:
        """Override to use coordination conversation ID logic"""
        if conversation_id is None:
            conversation_id = self._get_coordination_conversation_id(message)

        super().add_message(message, conversation_id)

    def add_coordination_command(
        self,
        target_agent: str,
        command: str,
        conversation_id: Optional[str] = None
    ) -> None:
        """Add a coordination command to the shared context"""
        if conversation_id is None:
            conversation_id = self.coordination_session

        user_msg_dict = {
            "role": "user",
            "content": f"[TO: {target_agent}] {command}",
            "name": self._sanitize_jid_for_name(target_agent)
        }

        self.add_message_dict(user_msg_dict, conversation_id)


class CoordinatorAgent(LLMAgent):
    """
    Agent specialized for coordinating multiple subordinate agents.

    Features:
    - Shared conversation context across all subagents
    - Automatic routing of subagent responses back to coordinator
    - Built-in coordination tools
    - Agent registry and status tracking
    """

    def __init__(
        self,
        jid: str,
        password: str,
        subagent_ids: List[str],
        coordination_session: str = "main_coordination",
        routing_function: Optional[RoutingFunction] = None,
        **kwargs
    ):
        # Validate inputs
        if not subagent_ids:
            raise ValueError("subagent_ids cannot be empty")

        self.subagent_ids = set(subagent_ids)
        self.coordination_session = coordination_session

        if routing_function is None:
            routing_function = self._create_coordination_routing()

        if 'system_prompt' not in kwargs:
            kwargs['system_prompt'] = self._default_coordination_prompt()

        coordination_context = CoordinationContextManager(
            coordination_session=coordination_session,
            subagent_ids=self.subagent_ids,
            system_prompt=kwargs.get('system_prompt'),
            context_management=kwargs.get('context_management', None)
        )

        kwargs['_context_override'] = coordination_context

        super().__init__(
            jid=jid,
            password=password,
            routing_function=routing_function,
            **kwargs
        )

        self.agent_status: Dict[str, str] = {
            agent_id: "unknown" for agent_id in self.subagent_ids
        }

        self._original_requester: Optional[str] = None

        self.termination_markers = ["<TASK_COMPLETE>", "<END>", "<DONE>"]

    def _default_coordination_prompt(self) -> str:
        """Default system prompt for coordination"""
        agent_list = ", ".join(self.subagent_ids)
        return f"""You are a coordinator agent managing the following subagents: {agent_list}

COORDINATION RULES:
1. Work SEQUENTIALLY - wait for each agent to respond before sending the next command
2. Review the full conversation context to see all agent responses
3. Only YOU can see the full coordination context - subagents only see their individual tasks
4. After receiving responses from all required agents, provide a final summary to the user
5. Use termination markers (<TASK_COMPLETE>, <END>, or <DONE>) ONLY when all work is finished

Available tools:
- send_to_agent: Send a command to a specific subagent
- list_subagents: See available agents and their current status

WORKFLOW:
1. Send command to first agent
2. WAIT for response (it will appear in your context)
3. Review response, then send to next agent
4. Repeat until all tasks complete
5. Provide final summary with termination marker

Coordination session: {self.coordination_session}
"""

    def _create_coordination_routing(self) -> RoutingFunction:
        """Create routing function for coordination responses"""
        def coordination_routing(
            msg: Message,
            response: str,
            context: Dict[str, Any]
        ) -> Union[str, RoutingResponse]:

            sender_str = str(msg.sender)

            if sender_str not in self.subagent_ids and self._original_requester is None:
                self._original_requester = sender_str

            is_completion = any(marker in response for marker in self.termination_markers)

            if is_completion and self._original_requester is not None:
                return self._original_requester

            if sender_str in self.subagent_ids:
                return str(self.jid)

            # External messages: route back to sender
            return str(msg.sender)

        return coordination_routing

    async def setup(self):
        """Override setup to add coordination tools"""
        await super().setup()

        coordination_tools = [
            self._create_send_to_agent_tool(),
            self._create_list_subagents_tool()
        ]

        for tool in coordination_tools:
            self.add_tool(tool)

    def _create_send_to_agent_tool(self) -> LLMTool:
        """Create tool for sending commands to subagents"""
        agent = self

        async def send_to_agent(agent_id: str, command: str) -> str:
            """Send a command to a specific subagent"""
            if agent_id not in agent.subagent_ids:
                return f"Error: {agent_id} is not a registered subagent"

            msg = Message(to=agent_id)
            msg.set_metadata("message_type", "llm")
            msg.set_metadata("coordination_session", agent.coordination_session)
            msg.thread = agent.coordination_session  # Force shared context
            msg.body = command

            await agent.llm_behaviour.send(msg)

            agent.agent_status[agent_id] = "sent_command"

            return f"Command sent to {agent_id}: {command}"

        return LLMTool(
            name="send_to_agent",
            description="Send a command to a specific subagent in the coordination session",
            parameters={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "The JID of the target subagent"
                    },
                    "command": {
                        "type": "string",
                        "description": "The command to send to the subagent"
                    }
                },
                "required": ["agent_id", "command"]
            },
            func=send_to_agent
        )

    def _create_list_subagents_tool(self) -> LLMTool:
        """Create tool for listing subagents and their status"""
        agent = self

        def list_subagents() -> str:
            """List all subagents and their current status"""
            agent_info = []
            for agent_id in agent.subagent_ids:
                status = agent.agent_status.get(agent_id, "unknown")
                agent_info.append(f"- {agent_id}: {status}")

            return f"Subagents in coordination session '{agent.coordination_session}':\n" + "\n".join(agent_info)

        return LLMTool(
            name="list_subagents",
            description="List all registered subagents and their current status",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            func=list_subagents
        )

    async def _handle_subagent_response(self, msg: Message) -> None:
        """Handle response from subagent - update status and context"""
        sender_str = str(msg.sender)

        if sender_str in self.subagent_ids:
            self.agent_status[sender_str] = "responded"

            # Response will be automatically added to context by LLMBehaviour
            # due to shared conversation ID from routing