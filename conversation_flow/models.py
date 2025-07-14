"""
Simplified data models for the Conversation Flow Manager
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class ConversationPhase(Enum):
    """Simple conversation phases"""
    GATHERING_INFO = "gathering_info"
    READY_FOR_RECOMMENDATIONS = "ready_for_recommendations"
    HANDLING_CHANGES = "handling_changes"


@dataclass
class ConversationState:
    """Minimal conversation state tracking"""
    original_query: str
    phase: ConversationPhase = ConversationPhase.GATHERING_INFO
    all_attributes: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[str] = field(default_factory=list)
    questions_asked: int = 0
    
    def add_to_history(self, message: str):
        """Add a message to conversation history"""
        self.conversation_history.append(message)
    
    def has_essential_attributes(self) -> bool:
        """Check if we have the essential attributes for recommendations"""
        has_size = 'size' in self.all_attributes and self.all_attributes['size']
        has_category = 'category' in self.all_attributes and self.all_attributes['category']
        return has_size and has_category


@dataclass
class ConversationTurn:
    """Result of processing one conversation turn"""
    action: str
    phase: ConversationPhase
    response_message: str
    reasoning: str = ""
    next_phase: Optional[ConversationPhase] = None
    recommendations: Optional[List[Any]] = None  # Will hold Product objects
    
    @classmethod
    def create(cls, action: str, phase: ConversationPhase, response_message: str, 
              reasoning: str = "", next_phase: Optional[ConversationPhase] = None,
              recommendations: Optional[List[Any]] = None) -> 'ConversationTurn':
        """Create a conversation turn"""
        return cls(
            action=action,
            phase=phase,
            response_message=response_message,
            reasoning=reasoning,
            next_phase=next_phase,
            recommendations=recommendations
        )


@dataclass
class AttributePriority:
    """Defines priority and requirements for an attribute"""
    priority: int
    required: bool
    examples: List[str] = field(default_factory=list)
    description: str = ""
