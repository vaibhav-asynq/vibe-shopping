"""
Minimalistic FastAPI backend for Vibe Shopping Chat Interface
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import os
from datetime import datetime

# Clear any existing OPENAI_API_KEY from environment before loading .env
if 'OPENAI_API_KEY' in os.environ:
    del os.environ['OPENAI_API_KEY']

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(override=True)

from conversation_flow import SimplifiedConversationManager, ConversationState
from recommendation_engine import EnhancedProgressiveMatcher, ProductCatalog

app = FastAPI(title="Vibe Shopping API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (simple approach)
sessions: Dict[str, ConversationState] = {}
session_logs: Dict[str, List[str]] = {}

# Initialize conversation manager
conversation_manager = SimplifiedConversationManager()

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    recommendations: List[Dict[str, Any]] = []
    action: str
    phase: str

class NewSessionRequest(BaseModel):
    initial_query: str

class SessionLogs(BaseModel):
    session_id: str
    logs: List[str]

def format_product_for_api(product) -> Dict[str, Any]:
    """Format product object for API response"""
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "category": product.category,
        "fit": product.fit,
        "fabric": product.fabric,
        "color_or_print": product.color_or_print,
        "occasion": product.occasion,
        "available_sizes": product.available_sizes,
        "ranking_score": getattr(product, 'ranking_score', None),
        "ranking_reasoning": getattr(product, 'ranking_reasoning', None)
    }

def capture_logs(session_id: str, message: str, log_type: str = "info"):
    """Capture logs for debugging with categorization"""
    if session_id not in session_logs:
        session_logs[session_id] = []
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Add log type prefix for better categorization
    type_prefix = {
        "info": "ℹ️",
        "success": "✅", 
        "warning": "⚠️",
        "error": "❌",
        "debug": "🔍",
        "llm": "🧠",
        "filter": "🎯",
        "extract": "📊"
    }.get(log_type, "ℹ️")
    
    session_logs[session_id].append(f"[{timestamp}] {type_prefix} {message}")

def capture_detailed_logs(session_id: str, component: str, details: dict):
    """Capture detailed structured logs from components"""
    if session_id not in session_logs:
        session_logs[session_id] = []
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if component == "attribute_extraction":
        if details.get('attributes'):
            for attr, values in details['attributes'].items():
                confidences = details.get('confidence_scores', {}).get(attr, [])
                for i, value in enumerate(values):
                    conf = confidences[i] if i < len(confidences) else 0.0
                    capture_logs(session_id, f"Extracted {attr}: '{value}' (confidence: {conf:.2f})", "extract")
        
        if details.get('extraction_quality'):
            capture_logs(session_id, f"Overall extraction quality: {details['extraction_quality']:.2f}", "extract")
    
    elif component == "llm_decision":
        if details.get('reasoning'):
            capture_logs(session_id, f"LLM Reasoning: {details['reasoning']}", "llm")
        if details.get('action'):
            capture_logs(session_id, f"LLM Decision: {details['action']}", "llm")
    
    elif component == "recommendation_stage1":
        if details.get('filters_applied'):
            capture_logs(session_id, f"Applied {len(details['filters_applied'])} filters", "filter")
        if details.get('candidates_found'):
            capture_logs(session_id, f"Stage 1: Found {details['candidates_found']} candidates", "filter")
        if details.get('relaxation_steps'):
            for step in details['relaxation_steps']:
                capture_logs(session_id, f"Relaxed filter: {step}", "filter")
    
    elif component == "recommendation_stage2":
        if details.get('llm_ranking'):
            capture_logs(session_id, "🧠 Stage 2: LLM ranking candidates...", "llm")
        if details.get('final_count'):
            capture_logs(session_id, f"✅ Selected top {details['final_count']} recommendations", "success")

# Set up logging callback for detailed logs
conversation_manager.log_callback = capture_detailed_logs

@app.get("/")
async def root():
    return {"message": "🛍️ Vibe Shopping API is running!", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "vibe-shopping-api"}

@app.post("/api/chat/start", response_model=ChatResponse)
async def start_conversation(request: NewSessionRequest):
    """Start a new conversation session"""
    try:
        # Create new session
        session_id = str(uuid.uuid4())
        state = ConversationState(original_query=request.initial_query)
        state.session_id = session_id  # Add session_id to state for logging
        sessions[session_id] = state
        session_logs[session_id] = []
        
        capture_logs(session_id, f"🚀 Started new session with query: '{request.initial_query}'")
        
        # Process initial query
        turn = conversation_manager.process_conversation("", state)
        
        capture_logs(session_id, f"📝 Action: {turn.action}, Phase: {turn.phase.value}")
        
        # Format recommendations if any
        recommendations = []
        if turn.recommendations:
            recommendations = [format_product_for_api(product) for product in turn.recommendations]
            capture_logs(session_id, f"🏆 Generated {len(recommendations)} recommendations")
        
        return ChatResponse(
            response=turn.response_message,
            session_id=session_id,
            recommendations=recommendations,
            action=turn.action,
            phase=turn.phase.value
        )
        
    except Exception as e:
        capture_logs(session_id if 'session_id' in locals() else "unknown", f"❌ Error starting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting conversation: {str(e)}")

@app.post("/api/chat/message", response_model=ChatResponse)
async def send_message(message: ChatMessage):
    """Send a message in an existing conversation"""
    try:
        session_id = message.session_id
        if not session_id or session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        state = sessions[session_id]
        capture_logs(session_id, f"💬 User message: '{message.message}'")
        
        # Process the message
        turn = conversation_manager.process_conversation(message.message, state)
        
        capture_logs(session_id, f"📝 Action: {turn.action}, Phase: {turn.phase.value}")
        
        # Format recommendations if any
        recommendations = []
        if turn.recommendations:
            recommendations = [format_product_for_api(product) for product in turn.recommendations]
            capture_logs(session_id, f"🏆 Generated {len(recommendations)} recommendations")
        
        return ChatResponse(
            response=turn.response_message,
            session_id=session_id,
            recommendations=recommendations,
            action=turn.action,
            phase=turn.phase.value
        )
        
    except HTTPException:
        raise
    except Exception as e:
        capture_logs(session_id if session_id else "unknown", f"❌ Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.delete("/api/chat/{session_id}")
async def clear_conversation(session_id: str):
    """Clear a conversation session"""
    try:
        if session_id in sessions:
            del sessions[session_id]
        if session_id in session_logs:
            del session_logs[session_id]
        
        return {"message": "Session cleared successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")

@app.get("/api/debug/logs/{session_id}", response_model=SessionLogs)
async def get_session_logs(session_id: str):
    """Get debug logs for a session"""
    try:
        if session_id not in session_logs:
            return SessionLogs(session_id=session_id, logs=[])
        
        return SessionLogs(
            session_id=session_id,
            logs=session_logs[session_id]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")

@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions (for debugging)"""
    return {
        "active_sessions": len(sessions),
        "session_ids": list(sessions.keys())
    }

# Serve static files for React frontend (if built)
if os.path.exists("frontend/build"):
    app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("🛍️ Starting Vibe Shopping API...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
