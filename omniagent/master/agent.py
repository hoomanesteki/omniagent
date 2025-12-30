"""
Master Agent - Orchestrates specialized agents to answer user queries.

Uses Groq API for LLM inference with proper:
- Tool calling and execution
- Conversation history management
- Error handling and rate limit recovery
- User-friendly response formatting
"""

import json
import os
import re
from typing import Any, Generator

from dotenv import load_dotenv

from omniagent.config.logging import get_logger
from omniagent.mcp.client import MCPClient
from omniagent.mcp.protocol import ToolCallMessage
from omniagent.models.dataset import DatasetProfile
from omniagent.models.messages import Conversation, MessageRole

logger = get_logger(__name__)

load_dotenv()


SYSTEM_PROMPT = """You are OmniAgent, a friendly AI data analyst assistant. You help users explore and understand their data through conversation.

## Your Role
- Be helpful, clear, and concise
- Actually USE tools to get real data - don't make up results
- Present findings in a user-friendly way
- Suggest next steps and follow-up questions

## Available Tools

You have these tools - USE THEM to answer questions:

**Data Info:**
- schema_agent.get_columns() - List all columns
- schema_agent.get_row_count() - Get row count  
- schema_agent.get_sample(n) - Get n sample rows
- schema_agent.get_column_info(column) - Details about one column

**Analysis:**
- eda_agent.profile() - Complete dataset overview
- eda_agent.missing_report() - Find missing values
- eda_agent.outlier_detect(column, method) - Find outliers
- eda_agent.value_counts(column, top_n) - Value frequencies
- stats_agent.describe(columns) - Statistics for columns
- stats_agent.correlate(columns) - Correlation analysis
- stats_agent.groupby(group_column, agg_column, agg_func, top_n) - Group analysis

**Visualization:**
- plot_agent.histogram(column, bins, title) - Distribution plot
- plot_agent.scatter(x_column, y_column, color_column, title) - Scatter plot
- plot_agent.boxplot(column, group_by, title) - Box plot
- plot_agent.bar(x_column, y_column, aggregation, top_n, title) - Bar chart
- plot_agent.heatmap(columns, title) - Correlation heatmap

**SQL:**
- sql_agent.query(sql, limit) - Run SELECT query

## IMPORTANT RULES

1. **ALWAYS call tools** to get real data. Never make up numbers.
2. **For visualizations**: Call plot_agent tools - they return base64 images.
3. **Be concise**: Don't repeat the same information.
4. **Be helpful**: Suggest what to explore next.
5. **Never show raw function syntax** to users - just describe what you found.

## Current Dataset

{dataset_context}
"""


class MasterAgent:
    """
    Master Agent that orchestrates specialized agents.
    
    Uses Groq API to understand user intent and coordinate
    tool calls across specialized agents.
    """
    
    def __init__(
        self,
        mcp_client: MCPClient,
        dataset_profile: DatasetProfile | None = None,
    ):
        """
        Initialize the Master Agent.
        
        Args:
            mcp_client: MCP client with registered agents
            dataset_profile: Profile of the current dataset
        """
        self.client = mcp_client
        self.dataset_profile = dataset_profile
        self.conversation = Conversation(
            conversation_id="default",
            dataset_id=dataset_profile.metadata.dataset_id if dataset_profile else None,
        )
        self._groq_client: Any = None
        self._max_history = 10  # Keep last N exchanges to avoid context overflow
    
    @property
    def groq_client(self) -> Any:
        """Lazy initialization of Groq client."""
        if self._groq_client is None:
            try:
                from groq import Groq
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise ValueError("GROQ_API_KEY not found in environment")
                self._groq_client = Groq(api_key=api_key)
            except ImportError:
                raise ImportError("groq package not installed. Run: pip install groq")
        return self._groq_client
    
    def set_dataset(self, profile: DatasetProfile) -> None:
        """Set or update the current dataset."""
        self.dataset_profile = profile
        self.conversation.dataset_id = profile.metadata.dataset_id
    
    def _get_system_prompt(self) -> str:
        """Generate system prompt with dataset context."""
        if self.dataset_profile:
            context = self._get_compact_context()
        else:
            context = "No dataset loaded. Ask the user to upload a CSV file."
        
        return SYSTEM_PROMPT.format(dataset_context=context)
    
    def _get_compact_context(self) -> str:
        """Get a compact dataset context to save tokens."""
        if not self.dataset_profile:
            return "No dataset loaded."
        
        meta = self.dataset_profile.metadata
        columns_info = []
        for col in meta.columns[:15]:
            columns_info.append(f"  - {col.name} ({col.dtype.value})")
        
        if len(meta.columns) > 15:
            columns_info.append(f"  ... and {len(meta.columns) - 15} more columns")
        
        return f"""Dataset: {meta.filename}
Rows: {meta.row_count:,}
Columns: {meta.column_count}
Table: {meta.table_name}

Columns:
{chr(10).join(columns_info)}"""
    
    def _get_tools(self) -> list[dict[str, Any]]:
        """Get tool schemas for Groq (OpenAI format)."""
        anthropic_tools = self.client.get_available_tools()
        
        openai_tools = []
        for tool in anthropic_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                }
            })
        
        return openai_tools
    
    def _execute_tool_call(self, tool_call: Any) -> str:
        """Execute a tool call and return the result."""
        # Parse arguments - handle None, empty string, or 'null'
        args_str = tool_call.function.arguments
        if args_str and args_str != 'null' and args_str.strip():
            try:
                arguments = json.loads(args_str)
                if arguments is None:
                    arguments = {}
            except json.JSONDecodeError:
                arguments = {}
        else:
            arguments = {}
        
        tc = ToolCallMessage(
            id=tool_call.id,
            name=tool_call.function.name,
            arguments=arguments,
        )
        
        logger.info(f"Executing tool: {tc.name}", arguments=tc.arguments)
        
        result = self.client.call_tool_from_llm(tc)
        
        if result.is_error:
            logger.warning(f"Tool error: {tc.name}", error=result.content)
            return f"Error: {result.content}"
        
        # Truncate very long results to avoid context overflow
        content = result.content
        if len(content) > 3000:
            content = content[:3000] + "\n... (truncated for brevity)"
        
        return content
    
    def _clean_response(self, text: str) -> str:
        """Clean up response to remove any raw function syntax."""
        # Remove <function=...>...</function> patterns
        text = re.sub(r'<function=[^>]+>.*?</function>', '', text, flags=re.DOTALL)
        text = re.sub(r'<function=[^>]+>\{[^}]*\}</function>', '', text, flags=re.DOTALL)
        text = re.sub(r'<function=[^>]+>[^<]*', '', text)
        text = text.replace('{$}', '')
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def chat(self, user_message: str) -> str:
        """
        Process a user message and return a response.
        
        Args:
            user_message: The user's message
            
        Returns:
            The assistant's response
        """
        # Add user message to conversation
        self.conversation.add_user_message(user_message)
        
        # Prepare messages for Groq
        messages = [
            {"role": "system", "content": self._get_system_prompt()}
        ]
        
        # Add conversation history (limited)
        for msg in self.conversation.messages[-(self._max_history * 2):]:
            if msg.role == MessageRole.USER:
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == MessageRole.ASSISTANT:
                content = msg.content
                if len(content) > 1500:
                    content = content[:1500] + "..."
                messages.append({"role": "assistant", "content": content})
        
        tools = self._get_tools()
        model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
        
        logger.info("Calling Groq", model=model)
        
        try:
            response = self.groq_client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=2048,
                temperature=0.1,
            )
        except Exception as e:
            error_str = str(e)
            if "rate_limit" in error_str.lower() or "429" in error_str:
                return "⚠️ Rate limit reached. Please wait a moment and try again."
            elif "context_length" in error_str.lower() or "413" in error_str:
                self.conversation.messages = self.conversation.messages[-4:]
                return "⚠️ Conversation too long. I've cleared some history. Please try again."
            raise
        
        message = response.choices[0].message
        images = []
        
        # Process tool calls (limit iterations to prevent infinite loops)
        max_iterations = 5
        iteration = 0
        
        while message.tool_calls and iteration < max_iterations:
            iteration += 1
            
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in message.tool_calls
                ]
            })
            
            for tool_call in message.tool_calls:
                result = self._execute_tool_call(tool_call)
                
                # Extract images from results
                if "image_base64" in result:
                    try:
                        result_dict = json.loads(result) if isinstance(result, str) else result
                        if isinstance(result_dict, dict) and "image_base64" in result_dict:
                            images.append(result_dict["image_base64"])
                            result_dict["image_base64"] = "[IMAGE GENERATED]"
                            result = json.dumps(result_dict)
                    except:
                        pass
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
            
            try:
                response = self.groq_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=2048,
                    temperature=0.1,
                )
                message = response.choices[0].message
            except Exception as e:
                if "rate_limit" in str(e).lower():
                    break
                raise
        
        final_text = message.content or "I couldn't generate a response."
        final_text = self._clean_response(final_text)
        
        if images:
            final_text += f"\n\n📊 *Generated {len(images)} visualization(s)*"
        
        self.conversation.add_assistant_message(final_text)
        
        return final_text
    
    def chat_stream(self, user_message: str) -> Generator[str, None, None]:
        """Process a user message with streaming response."""
        response = self.chat(user_message)
        yield response
    
    def chat_with_images(self, user_message: str) -> tuple[str, list[str]]:
        """
        Process a user message and return response with images.
        
        Args:
            user_message: The user's message
            
        Returns:
            Tuple of (response_text, list_of_base64_images)
        """
        # Add user message to conversation
        self.conversation.add_user_message(user_message)
        
        # Prepare messages for Groq
        messages = [
            {"role": "system", "content": self._get_system_prompt()}
        ]
        
        # Add conversation history (limited)
        for msg in self.conversation.messages[-(self._max_history * 2):]:
            if msg.role == MessageRole.USER:
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == MessageRole.ASSISTANT:
                content = msg.content
                if len(content) > 1500:
                    content = content[:1500] + "..."
                messages.append({"role": "assistant", "content": content})
        
        tools = self._get_tools()
        model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
        
        logger.info("Calling Groq", model=model)
        
        try:
            response = self.groq_client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=2048,
                temperature=0.1,
            )
        except Exception as e:
            error_str = str(e)
            if "rate_limit" in error_str.lower() or "429" in error_str:
                return "⚠️ Rate limit reached. Please wait a moment and try again.", []
            elif "context_length" in error_str.lower() or "413" in error_str:
                self.conversation.messages = self.conversation.messages[-4:]
                return "⚠️ Conversation too long. I've cleared some history. Please try again.", []
            raise
        
        message = response.choices[0].message
        images = []
        
        # Process tool calls
        max_iterations = 5
        iteration = 0
        
        while message.tool_calls and iteration < max_iterations:
            iteration += 1
            
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in message.tool_calls
                ]
            })
            
            for tool_call in message.tool_calls:
                result = self._execute_tool_call(tool_call)
                
                # Extract images
                if "image_base64" in result:
                    try:
                        result_dict = json.loads(result) if isinstance(result, str) else result
                        if isinstance(result_dict, dict) and "image_base64" in result_dict:
                            images.append(result_dict["image_base64"])
                            result_dict["image_base64"] = "[IMAGE GENERATED - showing to user]"
                            result = json.dumps(result_dict)
                    except:
                        pass
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
            
            try:
                response = self.groq_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=2048,
                    temperature=0.1,
                )
                message = response.choices[0].message
            except Exception as e:
                if "rate_limit" in str(e).lower():
                    break
                raise
        
        final_text = message.content or "I couldn't generate a response."
        final_text = self._clean_response(final_text)
        
        self.conversation.add_assistant_message(final_text)
        
        return final_text, images
    
    def reset_conversation(self) -> None:
        """Clear the conversation history."""
        self.conversation = Conversation(
            conversation_id="default",
            dataset_id=self.dataset_profile.metadata.dataset_id if self.dataset_profile else None,
        )
