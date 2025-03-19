"""
Core assistant module for Jarvis.
This module handles the interaction with the OpenAI API.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
import time

import openai
from openai import OpenAI

from jarvis.config import settings
from jarvis.core.commands import command_executor
from jarvis.memory.memory_manager import memory_manager

logger = logging.getLogger(__name__)

# System prompt template for the assistant
SYSTEM_PROMPT_TEMPLATE = """
You are {assistant_name}, a helpful AI assistant. You can help with various tasks on the user's computer.

You have the following capabilities:
1. Open applications and websites
2. Create, read, and delete files
3. Search the web for information
4. Take screenshots
5. Get system information

When the user asks you to perform an action, analyze the request and determine which command to execute.
Always be helpful, concise, and respectful. If you can't do something, explain why.

Current date and time: {current_datetime}
Current operating system: {os_type}

{memory_context}
"""

class JarvisAssistant:
    """Core assistant class for Jarvis."""
    
    def __init__(self):
        """Initialize the assistant."""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.conversation_history = []
        self.memory = memory_manager
        
        # Initialize the system prompt (without memory context yet)
        from datetime import datetime
        import platform
        
        self.system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            assistant_name=settings.ASSISTANT_NAME,
            current_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            os_type=platform.system(),
            memory_context=""  # Empty initially, will be populated per request
        )
        
        # Add the system message to the conversation history
        self.conversation_history.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        # Load recent conversations from memory if available
        self._load_recent_conversations()
        
        logger.info(f"Jarvis Assistant initialized with model: {self.model}")
    
    def _load_recent_conversations(self, n: int = 5):
        """Load recent conversations from memory storage."""
        if not settings.MEMORY_ENABLED:
            return
        
        recent_conversations = self.memory.get_recent_conversations(n)
        
        # Add to conversation history
        for conv in recent_conversations:
            self.add_to_history("user", conv["user_input"])
            self.add_to_history("assistant", conv["assistant_response"])
    
    def add_to_history(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
        
        # Manage history size to avoid token limits
        # For simplicity, we'll keep the last 20 messages plus the system message
        if len(self.conversation_history) > 21:  # 1 system + 20 conversation
            # Keep the system message and trim the oldest conversation messages
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-20:]
    
    def _get_system_prompt_with_memory(self, query: str) -> str:
        """Get the system prompt with relevant memory context for the current query."""
        from datetime import datetime
        import platform
        
        # Get context from vector memory if enabled
        memory_context = ""
        if settings.VECTOR_MEMORY_ENABLED:
            memory_context = self.memory.get_context_for_query(query)
        
        # Generate the complete system prompt
        return SYSTEM_PROMPT_TEMPLATE.format(
            assistant_name=settings.ASSISTANT_NAME,
            current_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            os_type=platform.system(),
            memory_context=memory_context
        )
    
    def process_command(self, user_input: str) -> str:
        """
        Process a command from the user.
        
        Args:
            user_input: The user's input message
            
        Returns:
            The assistant's response
        """
        try:
            # Define tool (function) descriptions for OpenAI API
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "execute_command",
                        "description": "Execute a command on the user's computer",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "command_name": {
                                    "type": "string",
                                    "enum": list(command_executor.commands.keys()),
                                    "description": "The name of the command to execute"
                                },
                                "kwargs": {
                                    "type": "object",
                                    "description": "Arguments for the command",
                                    "properties": {
                                        "content": {
                                            "type": "string",
                                            "description": "Content for file operations"
                                        },
                                        "file_path": {
                                            "type": "string",
                                            "description": "Path for file operations"
                                        },
                                        "url": {
                                            "type": "string",
                                            "description": "URL for web operations"
                                        },
                                        "query": {
                                            "type": "string",
                                            "description": "Query string for search operations"
                                        },
                                        "directory_path": {
                                            "type": "string",
                                            "description": "Path for directory operations"
                                        },
                                        "output_path": {
                                            "type": "string",
                                            "description": "Output path for saving files"
                                        }
                                    }
                                }
                            },
                            "required": ["command_name"]
                        }
                    }
                }
            ]
            
            # Create a system message with memory context for this specific query
            system_message_with_context = {
                "role": "system",
                "content": self._get_system_prompt_with_memory(user_input)
            }
            
            # Reset conversation history for this request (use the new system message)
            temp_conversation_history = [system_message_with_context]
            
            # Add previous few messages for context if available
            if len(self.conversation_history) > 1:
                # Add up to the 10 most recent messages
                start_idx = max(1, len(self.conversation_history) - 10)
                temp_conversation_history.extend(self.conversation_history[start_idx:])
            
            # Add the current user message
            temp_conversation_history.append({
                "role": "user", 
                "content": user_input
            })
            
            # We need to handle streaming differently - for now, let's disable it to fix the error
            # Later we can implement proper streaming support
            response = self.client.chat.completions.create(
                model=self.model,
                messages=temp_conversation_history,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
                tools=tools,
                tool_choice="auto"
            )
            
            # Extract the response message
            assistant_message = response.choices[0].message
            
            # Step 2: Check if the assistant wants to use a tool
            if assistant_message.tool_calls:
                # Add the assistant's response with tool calls to our history
                self.add_to_history("user", user_input)
                
                # We need to include the assistant's message with tool calls
                messages_for_second_call = temp_conversation_history.copy()
                messages_for_second_call.append(assistant_message)
                
                # Keep track of command context for memory
                command_context = {}
                
                # Handle each tool call
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Function call: {function_name} with args: {function_args}")
                    
                    if function_name == "execute_command":
                        command_name = function_args.get("command_name")
                        kwargs = function_args.get("kwargs", {})
                        
                        # Track command for context
                        command_context = {
                            "command_name": command_name,
                            "args": kwargs
                        }
                        
                        # Execute the command
                        result = command_executor.execute_command(command_name, **kwargs)
                        
                        # Store the command in memory
                        self.memory.add_command(command_name, kwargs, result)
                        
                        # Add the result to messages for the second call
                        messages_for_second_call.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                
                # Step 3: Get the final response after tool execution
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages_for_second_call,
                    max_tokens=settings.OPENAI_MAX_TOKENS,
                    temperature=settings.OPENAI_TEMPERATURE
                )
                
                # Get the final response content
                final_content = final_response.choices[0].message.content
                
                # Add the final response to our conversation history
                self.add_to_history("assistant", final_content)
                
                # Store the conversation in memory with context
                self.memory.add_conversation(
                    user_input, 
                    final_content,
                    context_info={
                        "command_executed": command_context,
                        "has_tool_calls": True
                    }
                )
                
                return final_content
                
            else:
                # No tool calls needed, just return the content
                content = assistant_message.content
                
                # Add both messages to conversation history
                self.add_to_history("user", user_input)
                self.add_to_history("assistant", content)
                
                # Store the conversation in memory with context
                self.memory.add_conversation(
                    user_input, 
                    content,
                    context_info={
                        "has_tool_calls": False
                    }
                )
                
                return content
                
        except Exception as e:
            logger.error(f"Error in processing command: {str(e)}")
            error_message = f"I apologize, but I encountered an error: {str(e)}"
            
            # Add messages to history even in case of error
            self.add_to_history("user", user_input)
            self.add_to_history("assistant", error_message)
            
            return error_message

# Create a singleton instance of the assistant
jarvis = JarvisAssistant()
