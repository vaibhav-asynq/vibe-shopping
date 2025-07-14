"""
Simplified LLM-Driven Conversation Flow Manager for Fashion Chatbot

This module provides a conversation manager that uses LLM to make all
conversation decisions through dynamic prompts, avoiding hardcoded logic.
"""

from .conversation_manager import SimplifiedConversationManager, SimpleConversationManager
from .models import ConversationState, ConversationTurn, ConversationPhase

__all__ = ['SimplifiedConversationManager', 'SimpleConversationManager', 'ConversationState', 'ConversationTurn', 'ConversationPhase']
