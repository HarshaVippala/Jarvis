"""
LangChain integration service for Jarvis.

This module provides integration with LangChain for tool calling,
function execution, and agent capabilities with local language models.
"""

import logging
import os
import sys
import json
from typing import List, Dict, Any, Optional, Union, Callable
from pathlib import Path

try:
    # Import LangChain components
    from langchain.llms.base import LLM
    from langchain.chat_models.base import BaseChatModel
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate
    from langchain.tools import Tool
    from langchain.agents import AgentType, initialize_agent
    from langchain.schema import SystemMessage, HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from jarvis.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class LangChainService:
    """Service for LangChain integration and tool calling capabilities."""
    
    def __init__(self):
        """Initialize the LangChain service."""
        self.active = False
        self.available = LANGCHAIN_AVAILABLE
        self.tools = {}
        self.language_model = None
        self.agent = None
        
        if not self.available:
            logger.warning("LangChain not available. Please install langchain and langchain-community packages.")
    
    def start(self) -> bool:
        """Start the LangChain service.
        
        Returns:
            bool: True if successfully started, False otherwise
        """
        if self.active:
            logger.info("LangChain service already running")
            return True
        
        if not self.available:
            logger.error("Cannot start LangChain service: required packages not installed")
            return False
        
        logger.info("Starting LangChain service")
        self.active = True
        return True
    
    def stop(self) -> None:
        """Stop the LangChain service."""
        if not self.active:
            return
        
        logger.info("Stopping LangChain service")
        self.active = False
    
    def set_language_model(self, model: Any) -> None:
        """Set the language model to use with LangChain.
        
        Args:
            model: The language model instance
        """
        if not self.active:
            logger.error("LangChain service not active")
            return
        
        # Store the model
        self.language_model = model
        logger.info(f"Language model set for LangChain service")
        
        # Recreate the agent if it exists
        if self.agent is not None and len(self.tools) > 0:
            self._create_agent()
    
    def register_tool(self, name: str, func: Callable, description: str) -> bool:
        """Register a new tool for the agent to use.
        
        Args:
            name: Name of the tool
            func: Function to call when tool is used
            description: Description of what the tool does
            
        Returns:
            bool: True if tool was registered successfully
        """
        if not self.active:
            logger.error("LangChain service not active")
            return False
        
        try:
            # Create a LangChain Tool
            tool = Tool(
                name=name,
                description=description,
                func=func
            )
            
            # Register the tool
            self.tools[name] = tool
            logger.info(f"Registered tool: {name}")
            
            # Recreate the agent if necessary
            if self.language_model is not None and self.agent is not None:
                self._create_agent()
                
            return True
            
        except Exception as e:
            logger.error(f"Error registering tool {name}: {str(e)}")
            return False
    
    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool.
        
        Args:
            name: Name of the tool to unregister
            
        Returns:
            bool: True if tool was unregistered
        """
        if not self.active or name not in self.tools:
            return False
        
        try:
            # Remove the tool
            del self.tools[name]
            logger.info(f"Unregistered tool: {name}")
            
            # Recreate the agent if necessary
            if self.language_model is not None and self.agent is not None:
                self._create_agent()
                
            return True
            
        except Exception as e:
            logger.error(f"Error unregistering tool {name}: {str(e)}")
            return False
    
    def _create_agent(self) -> None:
        """Create the LangChain agent with registered tools."""
        if not self.active or not self.language_model:
            logger.error("Cannot create agent: service inactive or no language model")
            return
        
        try:
            # Get the list of tools
            tool_list = list(self.tools.values())
            
            if not tool_list:
                logger.warning("No tools registered for agent")
                self.agent = None
                return
            
            # Create the agent
            self.agent = initialize_agent(
                tools=tool_list,
                llm=self.language_model,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                verbose=True,
                max_iterations=5
            )
            
            logger.info(f"Created agent with {len(tool_list)} tools")
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            self.agent = None
    
    def execute_with_tools(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Execute a query using the agent with tool capabilities.
        
        Args:
            query: The user query to process
            context: Optional context information
            
        Returns:
            dict: Result of the execution
        """
        if not self.active:
            return {"error": "LangChain service not active"}
        
        if not self.agent:
            if not self.language_model:
                return {"error": "No language model available"}
            
            if not self.tools:
                return {"error": "No tools registered"}
            
            self._create_agent()
            
            if not self.agent:
                return {"error": "Failed to create agent"}
        
        try:
            # Prepare input with context if provided
            if context:
                input_text = f"Context: {context}\n\nQuery: {query}"
            else:
                input_text = query
            
            # Execute the agent
            result = self.agent.run(input=input_text)
            
            return {
                "status": "success",
                "message": result
            }
            
        except Exception as e:
            logger.error(f"Error executing agent: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing your request: {str(e)}"
            }
    
    def run_prompt_template(self, 
                           template: str, 
                           variables: Dict[str, str]) -> Dict[str, Any]:
        """Run a prompt template with the language model.
        
        Args:
            template: The prompt template string
            variables: Dictionary of variables to insert into the template
            
        Returns:
            dict: Result of the execution
        """
        if not self.active:
            return {"error": "LangChain service not active"}
        
        if not self.language_model:
            return {"error": "No language model available"}
        
        try:
            # Create prompt template
            prompt = PromptTemplate(
                template=template,
                input_variables=list(variables.keys())
            )
            
            # Create chain
            chain = LLMChain(llm=self.language_model, prompt=prompt)
            
            # Run the chain
            result = chain.run(**variables)
            
            return {
                "status": "success",
                "message": result
            }
            
        except Exception as e:
            logger.error(f"Error running prompt template: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing your request: {str(e)}"
            }
    
    def get_registered_tools(self) -> List[Dict[str, str]]:
        """Get information about registered tools.
        
        Returns:
            list: List of dictionaries with tool information
        """
        result = []
        
        for name, tool in self.tools.items():
            result.append({
                "name": name,
                "description": tool.description
            })
        
        return result
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the service.
        
        Returns:
            dict: Information about the service state
        """
        return {
            "active": self.active,
            "available": self.available,
            "tools_count": len(self.tools),
            "has_model": self.language_model is not None,
            "has_agent": self.agent is not None,
            "registered_tools": [name for name in self.tools.keys()]
        }


# Create singleton instance
langchain_service = LangChainService() 