"""Context management for LLM conversations."""

import logging
from typing import Dict, List, Any, Optional, Set
from spade.message import Message

logger = logging.getLogger("spade_llm.context")


class ContextManager:
    """
    Manages the conversation context for LLM interactions.
    
    Features:
    - Stores conversation history
    - Manages token limits
    - Maintains system prompts and user objectives
    - Handles persistent storage between behaviour activations
    - Supports conversation-specific contexts
    """
    
    def __init__(self, 
                max_tokens: int = 4096, 
                system_prompt: Optional[str] = None):
        """
        Initialize the context manager.
        
        Args:
            max_tokens: Maximum number of tokens to maintain in context
            system_prompt: Optional system instructions for the LLM
        """
        self.max_tokens = max_tokens
        self._system_prompt = system_prompt
        self._values = {}
        
        # Store messages by conversation ID
        self._conversations: Dict[str, List[Dict[str, Any]]] = {}
        # Set to track which conversation IDs are currently active
        self._active_conversations: Set[str] = set()
        # Current conversation ID (used when not explicitly specified)
        self._current_conversation_id: Optional[str] = None
        
    def add_message(self, message: Message, conversation_id: str) -> None:
        """
        Add a message to the context.
        
        Args:
            message: The SPADE message to add to the context
            conversation_id: ID of the conversation
        """


        self._current_conversation_id = conversation_id
            
        # Mark conversation as active
        self._active_conversations.add(conversation_id)
        
        # Initialize conversation if needed
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        
        # Convert SPADE message to a format suitable for LLM context
        context_entry = {
            "role": "user" if message.sender else "assistant",
            "content": message.body,
            "sender": str(message.sender),
            "receiver": str(message.to),
            "thread": message.thread
        }
        
        # Add message to the conversation
        self._conversations[conversation_id].append(context_entry)
        
        # TODO : Token counting and context windowing will be implemented later
        
    def get_prompt(self, conversation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get the current prompt including history formatted for LLM providers.
        
        Args:
            conversation_id: Optional ID of the conversation. If not provided, 
                          uses the current conversation.
        
        Returns:
            A list of message dictionaries formatted for LLM API consumption
        """
        # Determine which conversation to use
        conv_id = conversation_id or self._current_conversation_id
        
        # If no conversation is specified or found, return just the system prompt
        if not conv_id or conv_id not in self._conversations:
            if self._system_prompt:
                return [{"role": "system", "content": self._system_prompt}]
            return []
            
        prompt = []
        
        # Add system prompt if available
        if self._system_prompt:
            prompt.append({"role": "system", "content": self._system_prompt})
            
        # Add conversation history
        for msg in self._conversations[conv_id]:
            message_entry = {
                "role": msg["role"],
                "content": msg["content"]
            }
            
            # Include name parameter for function messages as required by OpenAI
            if msg["role"] == "function" and "name" in msg:
                message_entry["name"] = msg["name"]
                
            prompt.append(message_entry)
            
        return prompt
        
    def add_tool_result(self, tool_name: str, result: Any, conversation_id: Optional[str] = None) -> None:
        """
        Add a tool execution result to the context.
        
        Args:
            tool_name: The name of the tool that was executed
            result: The result returned by the tool
            conversation_id: Optional ID of the conversation to add the result to
        """
        # Determine which conversation to use
        conv_id = conversation_id or self._current_conversation_id
        
        # If no conversation is found, log a warning and return
        if not conv_id or conv_id not in self._conversations:
            logger.warning(f"No active conversation found to add tool result for: {tool_name}")
            return
        
        # This will be expanded in the tools implementation
        self._conversations[conv_id].append({
            "role": "function",
            "name": tool_name,
            "content": str(result)
        })
        
    def clear(self, conversation_id: Optional[str] = None) -> None:
        """
        Clear messages from the context but retain system prompt.
        
        Args:
            conversation_id: Optional ID of the conversation to clear.
                          If None, clears the current conversation.
                          If 'all', clears all conversations.
        """
        if conversation_id == 'all':
            self._conversations = {}
            self._active_conversations = set()
            self._current_conversation_id = None
        else:
            conv_id = conversation_id or self._current_conversation_id
            if conv_id in self._conversations:
                self._conversations[conv_id] = []
                if conv_id in self._active_conversations:
                    self._active_conversations.remove(conv_id)
                
                # Reset current conversation if it was cleared
                if self._current_conversation_id == conv_id:
                    self._current_conversation_id = None
                    
    def get_active_conversations(self) -> List[str]:
        """
        Get a list of all active conversation IDs.
        
        Returns:
            List of conversation IDs
        """
        return list(self._active_conversations)
    
    def set_current_conversation(self, conversation_id: str) -> bool:
        """
        Set the current conversation context.
        
        Args:
            conversation_id: The ID of the conversation to set as current
            
        Returns:
            bool: True if successful, False if conversation doesn't exist
        """
        if conversation_id in self._conversations:
            self._current_conversation_id = conversation_id
            return True
        return False
