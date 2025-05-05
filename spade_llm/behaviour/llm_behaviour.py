"""LLM Behaviour implementation for SPADE agents."""

import asyncio
import logging
import time
import json
from typing import Optional, Any, Dict, List, Callable, Set

from spade.behaviour import CyclicBehaviour
from spade.message import Message

from ..context import ContextManager
from ..providers.base_provider import LLMProvider
from ..tools import LLMTool

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
                on_conversation_end: Optional[Callable[[str, str], None]] = None,
                tools: Optional[List[LLMTool]] = None):
        """
        Initialize the LLM behaviour.
        
        Args:
            llm_provider: Provider for LLM integration (OpenAI, Gemini, etc.)
            context_manager: Manager for conversation context (optional, will create new if None)
            termination_markers: List of strings that indicate conversation completion when present in LLM responses
            max_interactions_per_conversation: Maximum number of back-and-forth exchanges in a conversation
            on_conversation_end: Callback function when a conversation ends (receives conversation_id and reason)
            tools: Optional list of tools that can be used by the LLM
        """
        super().__init__()
        self.provider = llm_provider
        self.context = context_manager or ContextManager()
        
        # Conversation lifecycle management
        self.termination_markers = termination_markers or ["<TASK_COMPLETE>", "<END>", "<DONE>"]
        self.max_interactions_per_conversation = max_interactions_per_conversation
        self.on_conversation_end = on_conversation_end
        
        # Register tools with the provider
        if tools:
            for tool in tools:
                self.provider.register_tool(tool)
        
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
        self.context.add_message(msg,conversation_id)
        
        # Process the conversation with the LLM
        try:
            await self._process_message_with_llm(msg, conversation_id)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._end_conversation(conversation_id, ConversationState.ERROR)
            
            # Send error message
            reply = msg.make_reply()
            reply.body = f"Error processing your message: {str(e)}"
            await self.send(reply)
    
    async def _process_message_with_llm(self, msg: Message, conversation_id: str):
        """
        Process a message with the LLM, handling any tool calls.
        
        Args:
            msg: The message to process
            conversation_id: The ID of the conversation
        """
        response = None
        handled_tool_calls = False
        
        try:
            # First get tool calls from the LLM
            tool_calls = await self.provider.get_tool_calls(self.context)
            
            # If there are tool calls, process them
            if tool_calls:
                handled_tool_calls = True
                logger.info(f"LLM requested {len(tool_calls)} tool calls")
                
                for tool_call in tool_calls:
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("arguments", {})
                    
                    logger.info(f"Processing tool call: {tool_name} with args: {tool_args}")
                    
                    # Find the tool by name
                    tool = next((t for t in self.provider.tools if t.name == tool_name), None)
                    
                    if tool:
                        try:
                            # Execute the tool
                            result = await tool.execute(**tool_args)
                            
                            # Add the result to the context
                            self.context.add_tool_result(tool_name, result, conversation_id)
                            
                            logger.info(f"Tool {tool_name} executed successfully")
                        except Exception as e:
                            error_msg = f"Error executing tool {tool_name}: {str(e)}"
                            logger.error(error_msg)
                            self.context.add_tool_result(tool_name, {"error": error_msg}, conversation_id)
                    else:
                        error_msg = f"Tool {tool_name} not found"
                        logger.error(error_msg)
                        self.context.add_tool_result(tool_name, {"error": error_msg}, conversation_id)
                
                # Get a final response from the LLM with the tool results
                try:
                    response = await self.provider.get_response(self.context)
                    logger.info(f"Got response from LLM after tool execution: {response[:100]}...")
                except Exception as e:
                    logger.error(f"Error getting response after tool execution: {e}")
                    response = f"Error getting response after using {', '.join([tc.get('name') for tc in tool_calls])}: {str(e)}"
            else:
                # If no tool calls, just get a regular response
                response = await self.provider.get_response(self.context)
        except Exception as e:
            logger.error(f"Error in tool processing: {e}")
            response = f"Error processing your request: {str(e)}"
        
        # CRITICAL: Even if response is empty, send a default message for tool calls
        if not response and handled_tool_calls:
            logger.warning("Got empty response after tool execution, using default message")
            response = "I've processed your request using the available tools, but couldn't generate a proper response. Please try again or rephrase your question."
            
        # Skip sending only if response is still empty and we didn't handle any tools    
        if not response and not handled_tool_calls:
            logger.warning("Empty response and no tools were handled, skipping reply")
            return
        
        # Check for termination markers in the response
        if response and any(marker in response for marker in self.termination_markers):
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
        
        # Log antes de enviar
        logger.info(f"Sending response to {reply.to} with thread: {reply.thread}")
        
        try:
            await self.send(reply)
            logger.info(f"Response sent successfully to {reply.to}")
        except Exception as e:
            logger.error(f"Error sending response: {e}")
            # Intentar nuevamente con un mensaje directo si falla
            direct_msg = Message(to=str(msg.sender))
            direct_msg.body = response
            direct_msg.thread = conversation_id
            try:
                await self.send(direct_msg)
                logger.info(f"Sent fallback direct message to {direct_msg.to}")
            except Exception as e2:
                logger.error(f"Also failed to send direct message: {e2}")
    
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
        
    def register_tool(self, tool: LLMTool) -> None:
        """
        Register a tool with the LLM provider.
        
        Args:
            tool: The tool to register
        """
        self.provider.register_tool(tool)
