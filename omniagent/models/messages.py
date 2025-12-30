"""
Chat message data models.

These models represent the conversation between
the user and the agents.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of the message sender."""
    
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """A single message in the conversation."""
    
    role: MessageRole = Field(description="Who sent this message")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Optional: for tool messages
    tool_name: str | None = Field(default=None, description="Tool that generated this")
    tool_call_id: str | None = Field(default=None, description="ID of the tool call")
    
    # Optional: for assistant messages with tool calls
    tool_calls: list[dict[str, Any]] | None = Field(
        default=None,
        description="Tool calls made by assistant",
    )
    
    # Optional: attachments (plots, tables)
    attachments: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Attached content (plots, tables)",
    )


class Conversation(BaseModel):
    """A full conversation with context."""
    
    conversation_id: str = Field(description="Unique conversation ID")
    dataset_id: str | None = Field(
        default=None,
        description="Associated dataset ID",
    )
    messages: list[ChatMessage] = Field(
        default_factory=list,
        description="Conversation messages",
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def add_user_message(self, content: str) -> ChatMessage:
        """Convenience method to add a user message."""
        message = ChatMessage(role=MessageRole.USER, content=content)
        self.add_message(message)
        return message
    
    def add_assistant_message(
        self,
        content: str,
        tool_calls: list[dict[str, Any]] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> ChatMessage:
        """Convenience method to add an assistant message."""
        message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=content,
            tool_calls=tool_calls,
            attachments=attachments or [],
        )
        self.add_message(message)
        return message
    
    def get_messages_for_llm(self) -> list[dict[str, Any]]:
        """
        Format messages for sending to the LLM API.
        
        Converts our message format to the format expected by
        Claude/OpenAI APIs.
        """
        llm_messages = []
        
        for msg in self.messages:
            if msg.role == MessageRole.SYSTEM:
                llm_messages.append({
                    "role": "system",
                    "content": msg.content,
                })
            elif msg.role == MessageRole.USER:
                llm_messages.append({
                    "role": "user",
                    "content": msg.content,
                })
            elif msg.role == MessageRole.ASSISTANT:
                message_dict: dict[str, Any] = {
                    "role": "assistant",
                    "content": msg.content,
                }
                if msg.tool_calls:
                    message_dict["tool_calls"] = msg.tool_calls
                llm_messages.append(message_dict)
            elif msg.role == MessageRole.TOOL:
                llm_messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content,
                })
        
        return llm_messages
