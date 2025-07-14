# 🛍️ Vibe Shopping - AI-Powered Fashion Recommendation System

A sophisticated conversational AI system that helps users find perfect fashion items through natural language interactions, powered by a two-stage recommendation engine with LLM-based intelligent ranking.

## 📱 How to Use the UI

### Getting Started
1. **Access the Application**: Open http://44.200.192.40:3000/  in your browser
2. **Welcome Screen**: You'll see a welcome message with example queries

### Starting a Conversation
Type your request in the chat box at the bottom. The system understands natural language!

**Good Starting Examples:**
- "I need a red dress for a party"
- "casual top under $50"
- "flowy dress for vacation"
- "professional outfit for work"
- "something comfortable for weekend"

### How the Conversation Works
1. **You ask** → Assistant analyzes your request using AI
2. **Assistant may ask clarifying questions** like:
   - "What size should I look for?"
   - "What's your budget range?"
   - "Any specific color preferences?"
3. **Answer naturally** → Assistant finds recommendations using two-stage AI system
4. **Get results** → See product cards with AI-generated explanations

### Understanding Product Cards
Each recommendation shows:
- **Product Name** and **Price**
- **Category, Fit, Color** details
- **Available Sizes**
- **💡 AI Reasoning** - why this item was chosen specifically for you

### UI Controls
- **🔄 New Search**: Start over with a fresh conversation
- **📊 Show/Hide Logs**: Toggle technical details to see how the AI works
- **Send Button**: Submit your message (or press Enter)

### Tips for Better Results
- **Be specific**: "red cocktail dress size M" vs just "dress"
- **Mention occasion**: "for work", "for party", "casual"
- **Include preferences**: "under $100", "flowy fit", "bright colors"
- **Ask follow-ups**: "show me something cheaper" or "more formal options"

### Debug Logs (Optional)
- Click **📊 Show Logs** to see the AI system working
- Watch the two-stage recommendation process
- See attribute extraction and LLM reasoning
- Understand why certain products were chosen

## 🚀 Setup Instructions

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **OpenAI API Key** (for AI features)

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd vibe_shopping

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Backend Setup

```bash
# Start FastAPI backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or use the startup script
python start_app.py
```

**Backend will be available at:**
- 🌐 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 🧪 **Health Check**: http://localhost:8000/health

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start React development server
npm start
```

**Frontend will be available at:**
- 🎨 **Application**: http://localhost:3000

### 4. Quick Test

```bash
# Test the API directly
curl -X POST http://localhost:8000/api/chat/start \
  -H 'Content-Type: application/json' \
  -d '{"initial_query": "red dress for party"}'
```

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React + TypeScript)                │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │  Chat Interface │ │ Product Cards   │ │ Debug Panel     │   │
│  │  - Real-time    │ │ - AI Reasoning  │ │ - System Logs   │   │
│  │  - Auto-scroll  │ │ - Rich Details  │ │ - Filter Info   │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP API
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Chat Endpoints  │ │ Session Manager │ │ Debug Logging   │   │
│  │ - Start/Message │ │ - UUID Sessions │ │ - Real-time     │   │
│  │ - CORS Enabled  │ │ - In-memory     │ │ - Per Session   │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Conversation Flow Engine                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ LLM Decisions   │ │ Attribute       │ │ State Manager   │   │
│  │ - Dynamic       │ │ Extraction      │ │ - Phase Track   │   │
│  │ - Context-aware │ │ - Confidence    │ │ - History       │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              Vibe Attribute Engine                              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ LLM Extraction  │ │ Rule Enhancement│ │ Fuzzy Matching  │   │
│  │ - Structured    │ │ - Domain Rules  │ │ - Typo Tolerance│   │
│  │ - Pydantic      │ │ - Confidence    │ │ - Abbreviations │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│            Enhanced Recommendation Engine                       │
│                                                                 │
│  🎯 STAGE 1: Progressive Filtering (15 Candidates)             │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Confidence      │ │ Progressive     │ │ Diverse Pool    │   │
│  │ Thresholds      │ │ Relaxation      │ │ Generation      │   │
│  │ - Filter Prep   │ │ - Smart Removal │ │ - 15 Products   │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
│                                                                 │
│  🧠 STAGE 2: LLM Intelligent Ranking (Top 5)                  │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Context Analysis│ │ Multi-Criteria  │ │ Reasoned        │   │
│  │ - User Intent   │ │ - Relevance 40% │ │ - Explanations  │   │
│  │ - Conversation  │ │ - Style 25%     │ │ - Top 5 Final   │   │
│  │ - History       │ │ - Value 20%     │ │ - Ranked        │   │
│  │                 │ │ - Variety 15%   │ │                 │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Product Catalog                              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Excel Data      │ │ 70+ Products    │ │ Rich Attributes │   │
│  │ - Apparels      │ │ - Dresses       │ │ - Fit, Fabric   │   │
│  │ - Structured    │ │ - Tops          │ │ - Color, Price  │   │
│  │ - Validated     │ │ - Accessories   │ │ - Sizes, Occasion│   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Module Explanations

### 1. Frontend (React + TypeScript)
**Location**: `frontend/`

**Purpose**: User interface for chat-based shopping experience

**Key Components**:
- **Chat Interface**: Real-time messaging with typing indicators
- **Product Cards**: Display recommendations with AI reasoning
- **Debug Panel**: Shows system internals and AI decision process
- **Responsive Design**: Works on mobile and desktop

**Technologies**: React 18, TypeScript, CSS3, Fetch API

### 2. Backend (FastAPI)
**Location**: `main.py`

**Purpose**: RESTful API server with session management

**Key Features**:
- **Chat Endpoints**: `/api/chat/start`, `/api/chat/message`
- **Session Management**: UUID-based conversation tracking
- **Debug Logging**: Real-time system logs per session
- **CORS Configuration**: Frontend integration support

**API Endpoints**:
```bash
POST /api/chat/start          # Start new conversation
POST /api/chat/message        # Send message to existing conversation
DELETE /api/chat/{session_id} # Clear conversation
GET /api/debug/logs/{session_id} # Get system logs
GET /api/sessions             # List active sessions
GET /health                   # Health check
```

### 3. Conversation Flow Engine
**Location**: `conversation_flow/`

**Purpose**: Manages conversation state and LLM-driven decisions

**Core Components**:
- **ConversationManager**: Orchestrates conversation flow
- **ConversationState**: Tracks user attributes and history
- **LLM Decision Making**: Dynamic conversation flow without hardcoded rules

**Key Features**:
- Context-aware response generation
- Phase tracking (gathering_info → recommendations → changes)
- Conversation history management
- Dynamic question generation

**Example Usage**:
```python
from conversation_flow import SimplifiedConversationManager

manager = SimplifiedConversationManager()
response = manager.process_message("red dress for party", session_id)
```

### 4. Vibe Attribute Engine
**Location**: `vibe_attribute_engine/`

**Purpose**: Extracts structured attributes from natural language using AI

**Two-Stage Hybrid System**:

#### Stage 1: LLM Extraction
- **OpenAI Structured Output**: Uses GPT-4 with Pydantic models
- **Guaranteed Valid JSON**: No parsing errors
- **Per-Value Confidence**: Individual confidence scores
- **Product & Price Extraction**: Identifies specific items and budgets

#### Stage 2: Rule Enhancement
- **Fuzzy Matching**: Handles typos and abbreviations
- **Domain Rules**: Fashion-specific knowledge
- **Confidence Boosting**: Enhances LLM results with rules

**Attribute Schema** (10 attributes, 400+ values):
- **category**: top, dress, skirt, pants
- **fit**: Relaxed, Body hugging, Tailored, Flowy
- **fabric**: Linen, Silk, Cotton, Velvet
- **color_or_print**: Pastel pink, Floral print, Ruby red
- **occasion**: Party, Vacation, Everyday, Work
- **sleeve_length**: Short sleeves, Sleeveless, Spaghetti straps
- **neckline**: V neck, Sweetheart, Collar
- **length**: Mini, Short, Midi, Maxi
- **pant_type**: Wide-legged, Ankle length, Flared

**Example Usage**:
```python
from vibe_attribute_engine import VibeToAttributeMapper

mapper = VibeToAttributeMapper()
result = mapper.map_vibe_to_attributes("something cute for brunch")
print(result.final_attributes)  # Structured attributes with confidence
```

### 5. Enhanced Recommendation Engine
**Location**: `recommendation_engine/`

**Purpose**: Two-stage intelligent product recommendation system

#### Stage 1: Progressive Filtering (15 Candidates)
- **Confidence-Based Filtering**: Uses attribute confidence scores
- **Progressive Relaxation**: Gradually removes constraints
- **Diverse Candidate Pool**: Ensures variety in results

**Algorithm**:
1. Start with high-confidence filters (≥0.8)
2. Apply filters in confidence order
3. If insufficient results, progressively relax lowest confidence filters
4. Generate 15 diverse candidates

#### Stage 2: LLM Intelligent Ranking (Top 5)
- **Context-Aware Analysis**: Uses full conversation context
- **Multi-Criteria Evaluation**:
  - **Relevance (40%)**: Match to stated preferences
  - **Style Coherence (25%)**: Fit with overall vibe/occasion
  - **Value (20%)**: Price appropriateness
  - **Variety (15%)**: Diversity in final recommendations
- **Detailed Reasoning**: AI-generated explanations for each choice

**Core Classes**:
- **ProductCatalog**: Manages 70+ products from Excel data
- **ProgressiveMatcher**: Implements confidence-based filtering
- **LLMRanker**: AI-powered intelligent ranking
- **EnhancedProgressiveMatcher**: Orchestrates two-stage system

**Example Usage**:
```python
from recommendation_engine import EnhancedProgressiveMatcher, ProductCatalog

catalog = ProductCatalog()
matcher = EnhancedProgressiveMatcher(catalog)
recommendations = matcher.find_recommendations(attributes)
```

### 6. Product Catalog
**Location**: `recommendation_engine/catalog.py`, `Apparels_shared.xlsx`

**Purpose**: Product data management and filtering

**Data Source**: Excel file with 70+ real fashion products

**Product Attributes**:
- Basic info: name, price, category
- Style details: fit, fabric, color_or_print
- Specifications: available_sizes, occasion
- Additional: sleeve_length, neckline, length, pant_type

**Features**:
- Efficient filtering by any attribute combination
- Size availability checking
- Price range filtering
- Category-based organization

## 🧪 Testing

### Run All Tests
```bash
# Test individual components
python -m recommendation_engine.test_recommendations
python -m conversation_flow.test_conversation
python -m vibe_attribute_engine.test_engine

# Test full integration
python test_full_integration.py
python test_enhanced_recommendations.py
```

### Test Coverage
- ✅ Product catalog loading and filtering
- ✅ Vibe-to-attribute mapping with confidence scores
- ✅ Progressive matching with various confidence levels
- ✅ LLM ranking with different user contexts
- ✅ Full conversation system integration
- ✅ API endpoints and error handling

### Example Test Cases
```bash
# Test vibe mapping
"something cute for brunch with friends"
"professional outfit for client presentation"
"edgy look for date night"

# Test recommendations
"red dress for party"
"casual top under $50"
"flowy dress for vacation"
```

## 🎯 Key Technical Features

### AI-Powered Natural Language Understanding
- **OpenAI GPT-4 Integration**: Structured output with Pydantic validation
- **Context Awareness**: Maintains conversation history and user preferences
- **Confidence Scoring**: Per-attribute confidence for intelligent filtering

### Two-Stage Recommendation Algorithm
- **Stage 1**: Progressive confidence-based filtering (15 candidates)
- **Stage 2**: LLM multi-criteria ranking (top 5 with reasoning)
- **Fallback Strategies**: Graceful degradation when exact matches unavailable

### Robust Error Handling
- **API Failures**: Fallback to rule-based extraction
- **Network Issues**: Graceful degradation with user feedback
- **Invalid Inputs**: Validation and correction mechanisms

### Real-Time Debugging
- **System Logs**: View AI decision process in real-time
- **Filter Details**: See progressive filtering steps
- **LLM Reasoning**: Understand product selection rationale

## 📁 Project Structure

```
vibe_shopping/
├── 📄 README.md                    # This documentation
├── 📄 requirements.txt             # Python dependencies
├── 📄 main.py                      # FastAPI backend server
├── 📄 start_app.py                 # Startup script
├── 📄 .env.example                 # Environment template
├── 📄 Apparels_shared.xlsx         # Product catalog data
│
├── 📁 frontend/                    # React frontend
│   ├── 📄 package.json             # Node.js dependencies
│   ├── 📁 public/                  # Static assets
│   └── 📁 src/                     # React source code
│       ├── 📄 App.tsx              # Main React component
│       ├── 📄 index.tsx            # React entry point
│       └── 📄 index.css            # Styling
│
├── 📁 conversation_flow/           # Conversation management
│   ├── 📄 conversation_manager.py  # LLM-driven conversation logic
│   ├── 📄 models.py                # Conversation state models
│   └── 📄 test_conversation.py     # Conversation tests
│
├── 📁 vibe_attribute_engine/       # AI attribute extraction
│   ├── 📄 vibe_mapper.py           # Two-stage hybrid system
│   ├── 📄 models.py                # Pydantic data models
│   └── 📄 test_engine.py           # Engine tests
│
├── 📁 recommendation_engine/       # Two-stage recommendation system
│   ├── 📄 enhanced_matcher.py      # Main two-stage system
│   ├── 📄 progressive_matcher.py   # Progressive filtering (Stage 1)
│   ├── 📄 llm_ranker.py           # LLM ranking (Stage 2)
│   ├── 📄 catalog.py              # Product catalog management
│   ├── 📄 models.py               # Product and filter models
│   └── 📄 test_recommendations.py # Recommendation tests
│
├── 📁 data/                       # Configuration and rules
│   ├── 📄 config.json             # System configuration
│   ├── 📄 attribute_schema.json   # Product attribute schema
│   └── 📄 vibe_rules.json         # Fashion domain rules
│
└── 📁 tests/                      # Integration tests
    ├── 📄 test_full_integration.py
    └── 📄 test_enhanced_recommendations.py
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Required for AI features
OPENAI_API_KEY=your_openai_api_key_here

# Optional
ENVIRONMENT=development
```

### System Configuration (data/config.json)
```json
{
  "openai": {
    "model": "gpt-4",
    "temperature": 0.3,
    "timeout_seconds": 30
  },
  "recommendation": {
    "candidate_count": 15,
    "final_count": 5,
    "confidence_threshold": 0.6
  }
}
```

## 🎨 Example User Experience Flow

### 1. Initial Query
```
User: "I need a red dress for a party"
System: Analyzes query → Extracts attributes → Asks clarifying questions
```

### 2. Information Gathering
```
Assistant: "What size should I look for?"
User: "Medium"
System: Updates attributes → Determines if ready for recommendations
```

### 3. Two-Stage Recommendation Process
```
🎯 Stage 1: Progressive Filtering
- Applies filters: category=dress, color=red, size=M
- Finds 15 diverse candidates through progressive relaxation

🧠 Stage 2: LLM Ranking
- Analyzes candidates with conversation context
- Ranks based on relevance, style, value, variety
- Selects top 5 with detailed reasoning
```

### 4. Results Display
```
🏆 Your Perfect Matches:
1. Storm Skyline Slip - $160
   💡 "Bodycon fit perfect for party, though storm grey instead of red"
2. Midnight Mosaic Midi - $185
   💡 "Body hugging with vibrant multicolor, great party option"
...
```

## 🚧 Future Enhancements

### Planned Features
- [ ] **User Profiles**: Persistent preferences and history
- [ ] **Image Integration**: Product images and visual search
- [ ] **Voice Interface**: Speech-to-text conversation support
- [ ] **Real-time Inventory**: Live inventory integration
- [ ] **Multi-language**: Support for multiple languages

### Technical Improvements
- [ ] **Database Integration**: PostgreSQL for persistent storage
- [ ] **Caching Layer**: Redis for improved performance
- [ ] **Authentication**: User accounts and secure sessions
- [ ] **Analytics**: User behavior tracking and insights
- [ ] **A/B Testing**: Recommendation strategy optimization


