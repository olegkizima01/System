#!/usr/bin/env python3

"""
Copilot MCP Client - Alternative to Anthropic MCP for AI analysis
Uses the CopilotLLM provider instead of Anthropic API
"""

import json
import logging
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage

# Import CopilotLLM
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from providers.copilot import CopilotLLM
except ImportError:
    raise ImportError("Could not import CopilotLLM. Make sure providers/copilot.py is available")

logger = logging.getLogger(__name__)


class CopilotMCPClient:
    """
    MCP Client that uses Copilot LLM for AI analysis tasks
    Compatible with Anthropic MCP interface
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timeout = config.get('timeout', 60000)
        self.retry_attempts = config.get('retryAttempts', 3)
        
        # Initialize Copilot LLM
        try:
            self.llm = CopilotLLM()
            logger.info("CopilotMCP initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CopilotLLM: {e}")
            raise
    
    def connect(self) -> bool:
        """Test connection by making a simple call"""
        try:
            test_message = [HumanMessage(content="Test connection. Reply with 'OK'.")]
            response = self.llm.invoke(test_message)
            logger.info("CopilotMCP connection test successful")
            return True
        except Exception as e:
            logger.error(f"CopilotMCP connection test failed: {e}")
            return False
    
    def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute AI command using Copilot
        
        Supported commands:
        - ai_analyze: Analyze data for a specific purpose
        - ai_summarize: Summarize content
        - ai_generate: Generate content about a topic
        - ai_translate: Translate text to another language
        - ai_extract: Extract entities from text
        - ai_classify: Classify content into categories
        - ai_compare: Compare two items
        - ai_evaluate: Evaluate content against criteria
        - ai_predict: Predict outcomes based on data
        - ai_recommend: Recommend items based on preferences
        - ai_explain: Explain a concept
        - ai_rewrite: Rewrite text in a specific style
        - ai_code_review: Review code
        - ai_debug: Debug errors
        - ai_optimize: Optimize content for a goal
        - ai_validate: Validate data against schema
        - ai_convert: Convert data between formats
        - ai_sentiment: Analyze sentiment
        - ai_keywords: Extract keywords
        - ai_answer: Answer questions
        """
        try:
            # Map command to appropriate prompt
            prompt = self._build_prompt(command, **kwargs)
            
            # Create messages
            messages = [
                SystemMessage(content="You are a helpful AI assistant powered by GitHub Copilot. Provide clear, accurate, and concise responses."),
                HumanMessage(content=prompt)
            ]
            
            # Invoke LLM
            response = self.llm.invoke(messages)
            
            # Extract content
            content = response.content if hasattr(response, 'content') else str(response)
            
            return {
                "success": True,
                "command": command,
                "data": content,
                "raw_output": content,
                "provider": "copilot"
            }
            
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "provider": "copilot"
            }
    
    def _build_prompt(self, command: str, **kwargs) -> str:
        """Build appropriate prompt based on command and arguments"""
        
        # AI Analysis commands
        if command == "ai_analyze":
            data = kwargs.get("data", "")
            purpose = kwargs.get("purpose", "general analysis")
            return f"Analyze the following data for {purpose}:\n\n{data}"
        
        elif command == "ai_summarize":
            content = kwargs.get("content", "")
            return f"Summarize the following content:\n\n{content}"
        
        elif command == "ai_generate":
            content_type = kwargs.get("content_type", "text")
            topic = kwargs.get("topic", "")
            return f"Generate {content_type} about {topic}"
        
        elif command == "ai_translate":
            text = kwargs.get("text", "")
            language = kwargs.get("language", "English")
            return f"Translate the following text to {language}:\n\n{text}"
        
        elif command == "ai_extract":
            entities = kwargs.get("entities", "entities")
            text = kwargs.get("text", "")
            return f"Extract {entities} from the following text:\n\n{text}"
        
        elif command == "ai_classify":
            content = kwargs.get("content", "")
            categories = kwargs.get("categories", "")
            return f"Classify the following content into these categories: {categories}\n\nContent:\n{content}"
        
        elif command == "ai_compare":
            item1 = kwargs.get("item1", "")
            item2 = kwargs.get("item2", "")
            return f"Compare the following:\n\nItem 1: {item1}\n\nItem 2: {item2}"
        
        elif command == "ai_evaluate":
            content = kwargs.get("content", "")
            criteria = kwargs.get("criteria", "")
            return f"Evaluate the following content against these criteria: {criteria}\n\nContent:\n{content}"
        
        elif command == "ai_predict":
            outcome = kwargs.get("outcome", "")
            data = kwargs.get("data", "")
            return f"Predict {outcome} based on the following data:\n\n{data}"
        
        elif command == "ai_recommend":
            items = kwargs.get("items", "")
            preferences = kwargs.get("preferences", "")
            return f"Recommend {items} based on these preferences: {preferences}"
        
        elif command == "ai_explain":
            concept = kwargs.get("concept", "")
            style = kwargs.get("style", "simple")
            return f"Explain the following concept in {style} style:\n\n{concept}"
        
        elif command == "ai_rewrite":
            text = kwargs.get("text", "")
            style = kwargs.get("style", "")
            return f"Rewrite the following text in {style} style:\n\n{text}"
        
        elif command == "ai_code_review":
            code = kwargs.get("code", "")
            return f"Review the following code:\n\n```\n{code}\n```"
        
        elif command == "ai_debug":
            error = kwargs.get("error", "")
            context = kwargs.get("context", "")
            return f"Debug the following error:\n\nError: {error}\n\nContext: {context}"
        
        elif command == "ai_optimize":
            content = kwargs.get("content", "")
            goal = kwargs.get("goal", "")
            return f"Optimize the following content for {goal}:\n\n{content}"
        
        elif command == "ai_validate":
            data = kwargs.get("data", "")
            schema = kwargs.get("schema", "")
            return f"Validate the following data against this schema:\n\nSchema: {schema}\n\nData: {data}"
        
        elif command == "ai_convert":
            data = kwargs.get("data", "")
            format1 = kwargs.get("format1", "")
            format2 = kwargs.get("format2", "")
            return f"Convert the following data from {format1} to {format2}:\n\n{data}"
        
        elif command == "ai_sentiment":
            text = kwargs.get("text", "")
            return f"Analyze the sentiment of the following text:\n\n{text}"
        
        elif command == "ai_keywords":
            text = kwargs.get("text", "")
            return f"Extract keywords from the following text:\n\n{text}"
        
        elif command == "ai_answer":
            question = kwargs.get("question", "")
            return f"Answer the following question:\n\n{question}"
        
        else:
            # Generic command
            prompt_parts = [f"Command: {command}"]
            for key, value in kwargs.items():
                prompt_parts.append(f"{key}: {value}")
            return "\n".join(prompt_parts)
    
    def get_status(self) -> Dict[str, Any]:
        """Get client status"""
        return {
            "server": "copilot_mcp",
            "status": "connected",
            "provider": "GitHub Copilot",
            "model": self.llm.model_name if hasattr(self, 'llm') else "unknown"
        }
