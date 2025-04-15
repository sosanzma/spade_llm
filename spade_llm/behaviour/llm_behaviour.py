"""LLM Behaviour implementation for SPADE agents."""

import asyncio
import logging
import time
from typing import Optional, Any, Dict, List, Callable, Set

from spade.behaviour import CyclicBehaviour
from spade.message import Message

from ..context import ContextManager
from ..providers.base_provider import LLMProvider

logger = logging.getLogger("spade_llm.behaviour")


class ConversationState:
    """Represents the state of a conversation or task."""
    
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"
    MAX_INTERACTIONS_REACHED = "max_interactions_reached"


class LLMBehaviour(CyclicBehaviour):
    """
    A specialized behaviour for SPADE agents that integrates Large Language Models.
    
    This behaviour extends the CyclicBehaviour to:
    - Receive XMPP messages
    - Process and update the conversation context
    - Send prompts to LLM providers
    - Handle tool invocation
    - Send responses back
    
    The behaviour remains active throughout the agent's lifecycle,
    but individual conversations can be terminated based on conditions.
    """
    
    def __init__(self, 
                llm_provider: LLMProvider,
                context_manager: Optional[ContextManager] = None,
                termination_markers: Optional[List[str]] = None,
                max_interactions_per_conversation: Optional[int] = None,
                on_conversation_end: Optional[Callable[[str, str], None]] = None):
        """
        Initialize the LLM behaviour.
        
        Args:
            llm_provider: Provider for LLM integration (OpenAI, Gemini, etc.)
            context_manager: Manager for conversation context (optional, will create new if None)
            termination_markers: List of strings that indicate conversation completion when present in LLM responses
            max_interactions_per_conversation: Maximum number of back-and-forth exchanges in a conversation
            on_conversation_end: Callback function when a conversation ends (receives conversation_id and reason)
        """
        super().__init__()
        self.provider = llm_provider
        self.context = context_manager or ContextManager()
        
        # Conversation lifecycle management
        self.termination_markers = termination_markers or ["<TASK_COMPLETE>", "<END>", "<DONE>"]
        self.max_interactions_per_conversation = max_interactions_per_conversation
        self.on_conversation_end = on_conversation_end
        
        # Track active conversations
        self._active_conversations: Dict[str, Dict[str, Any]] = {}
        self._processed_messages: Set[str] = set()
        
    async def run(self):
        """
        Main execution loop for the behaviour.
        Waits for messages, processes them with the LLM, and sends responses.
        The behaviour itself continues indefinitely, but individual conversations
        can be terminated based on configured conditions.
        """
        # Wait for incoming message
        msg = await self.receive(timeout=10)
        
        if not msg:
            return
        
        # Check if we've already processed this message
        if msg.id in self._processed_messages:
            logger.debug(f"Skipping already processed message {msg.id}")
            return
        
        # Mark message as processed
        self._processed_messages.add(msg.id)
        logger.debug(f"LLMBehaviour received message: {msg}")
        
        # Determine conversation ID (use thread if available, otherwise create from message properties)
        conversation_id = msg.thread or f"{msg.sender}_{msg.to}"

        
        # Initialize or retrieve conversation state
        if conversation_id not in self._active_conversations:
            self._active_conversations[conversation_id] = {
                "state": ConversationState.ACTIVE,
                "interaction_count": 0,
                "start_time": time.time(),
                "last_activity": time.time()
            }
        
        conversation = self._active_conversations[conversation_id]
        
        # Check if conversation should be active
        if conversation["state"] != ConversationState.ACTIVE:
            logger.info(f"Conversation {conversation_id} is already in state {conversation['state']}, not processing further")
            return
        
        # Update conversation tracking
        conversation["interaction_count"] += 1
        conversation["last_activity"] = time.time()
        
        # Check for max interactions
        if (self.max_interactions_per_conversation and 
            conversation["interaction_count"] > self.max_interactions_per_conversation):
            await self._end_conversation(
                conversation_id, 
                ConversationState.MAX_INTERACTIONS_REACHED
            )
            
            # Optional: Send a message indicating the conversation has reached its limit
            reply = msg.make_reply()
            reply.body = f"This conversation has reached the maximum limit of {self.max_interactions_per_conversation} interactions."
            await self.send(reply)
            return
        
        # Update context with new message
        self.context.add_message(msg)
        
        # Get response from LLM provider
        try:
            response = await self.provider.get_response(self.context)
        except Exception as e:
            logger.error(f"Error getting response from LLM provider: {e}")
            await self._end_conversation(conversation_id, ConversationState.ERROR)

            # Send error message
            reply = msg.make_reply()
            reply.body = f"Error processing your message: {str(e)}"
            await self.send(reply)

            return
        
        # Check for termination markers in the response
        if any(marker in response for marker in self.termination_markers):
            # Remove the termination marker from the response
            for marker in self.termination_markers:
                response = response.replace(marker, "")
            
            # End the conversation
            await self._end_conversation(conversation_id, ConversationState.COMPLETED)

            # Send response back
        reply = msg.make_reply()
        reply.body = response
        # Preserve the conversation thread
        reply.thread = conversation_id
        await self.send(reply)
    
    async def _end_conversation(self, conversation_id: str, reason: str) -> None:
        """
        End a conversation and perform cleanup.
        
        Args:
            conversation_id: The ID of the conversation to end
            reason: The reason for ending the conversation
        """
        if conversation_id in self._active_conversations:
            self._active_conversations[conversation_id]["state"] = reason
            
            # Call the callback if provided
            if self.on_conversation_end:
                self.on_conversation_end(conversation_id, reason)
            
            logger.info(f"Conversation {conversation_id} ended: {reason}")
    
    def reset_conversation(self, conversation_id: str) -> bool:
        """
        Reset a conversation to allow it to continue beyond its limits.
        
        Args:
            conversation_id: The ID of the conversation to reset
            
        Returns:
            bool: True if the conversation was reset, False if not found
        """
        if conversation_id in self._active_conversations:
            self._active_conversations[conversation_id] = {
                "state": ConversationState.ACTIVE,
                "interaction_count": 0,
                "start_time": time.time(),
                "last_activity": time.time()
            }
            return True
        return False
    
    def get_conversation_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            Dict or None: The conversation state if found, None otherwise
        """
        return self._active_conversations.get(conversation_id)
