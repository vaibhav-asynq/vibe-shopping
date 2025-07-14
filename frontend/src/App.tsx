import React, { useState, useEffect, useRef } from 'react';
import './index.css';

interface Product {
  id: string;
  name: string;
  price: number;
  category: string;
  fit: string;
  fabric: string;
  color_or_print: string;
  occasion: string;
  available_sizes: string[];
  ranking_score?: number;
  ranking_reasoning?: string;
}

interface LogGroup {
  id: string;
  title: string;
  type: string;
  timestamp: string;
  logs: string[];
  isExpanded: boolean;
}

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  recommendations?: Product[];
}

interface ChatResponse {
  response: string;
  session_id: string;
  recommendations: Product[];
  action: string;
  phase: string;
}

const API_BASE = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showLogs, setShowLogs] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [logGroups, setLogGroups] = useState<LogGroup[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const groupLogs = (logs: string[]): LogGroup[] => {
    const groups: LogGroup[] = [];
    let currentGroup: LogGroup | null = null;
    
    logs.forEach((log, index) => {
      const timestamp = log.match(/\[(\d{2}:\d{2}:\d{2})\]/)?.[1] || '';
      
      // Determine if this log starts a new group
      if (log.includes('🚀 Started new session') || 
          log.includes('💬 User message:') ||
          log.includes('📊 Extracted') ||
          log.includes('🧠 LLM') ||
          log.includes('🎯') ||
          log.includes('🏆 Generated')) {
        
        // Save previous group if exists
        if (currentGroup) {
          groups.push(currentGroup);
        }
        
        // Create new group
        let title = '';
        let type = '';
        
        if (log.includes('🚀 Started new session')) {
          title = '🚀 Session Started';
          type = 'session';
        } else if (log.includes('💬 User message:')) {
          const message = log.split("'")[1] || 'User Input';
          title = `💬 User: "${message.substring(0, 30)}${message.length > 30 ? '...' : ''}"`;
          type = 'user';
        } else if (log.includes('📊 Extracted')) {
          title = '📊 Attribute Extraction';
          type = 'extract';
        } else if (log.includes('🧠 LLM')) {
          title = '🧠 LLM Decision Process';
          type = 'llm';
        } else if (log.includes('🎯')) {
          title = '🎯 Recommendation Engine';
          type = 'filter';
        } else if (log.includes('🏆 Generated')) {
          title = '🏆 Final Recommendations';
          type = 'success';
        }
        
        currentGroup = {
          id: `group-${index}`,
          title,
          type,
          timestamp,
          logs: [log],
          isExpanded: type === 'extract' || type === 'llm' || type === 'filter' // Auto-expand important groups
        };
      } else if (currentGroup) {
        // Add to current group
        currentGroup.logs.push(log);
      } else {
        // Create a misc group for orphaned logs
        currentGroup = {
          id: `group-${index}`,
          title: 'ℹ️ System Info',
          type: 'info',
          timestamp,
          logs: [log],
          isExpanded: false
        };
      }
    });
    
    // Add final group
    if (currentGroup) {
      groups.push(currentGroup);
    }
    
    return groups;
  };

  const fetchLogs = async (sessionId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/debug/logs/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        const rawLogs = data.logs || [];
        setLogs(rawLogs);
        setLogGroups(groupLogs(rawLogs));
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  const toggleLogGroup = (groupId: string) => {
    setLogGroups(prev => prev.map(group => 
      group.id === groupId 
        ? { ...group, isExpanded: !group.isExpanded }
        : group
    ));
  };

  const startNewConversation = async (query: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/chat/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ initial_query: query }),
      });

      if (response.ok) {
        const data: ChatResponse = await response.json();
        setSessionId(data.session_id);
        
        // Add the user's initial message first
        const userMessage: Message = {
          id: Date.now().toString(),
          type: 'user',
          content: query,
        };
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: data.response,
          recommendations: data.recommendations,
        };

        setMessages([userMessage, assistantMessage]);
        await fetchLogs(data.session_id);
      } else {
        throw new Error('Failed to start conversation');
      }
    } catch (error) {
      console.error('Error starting conversation:', error);
      setMessages([{
        id: Date.now().toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (message: string) => {
    if (!message.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: message,
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      if (!sessionId) {
        // Start new conversation
        await startNewConversation(message);
        return;
      }

      const response = await fetch(`${API_BASE}/api/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          session_id: sessionId,
        }),
      });

      if (response.ok) {
        const data: ChatResponse = await response.json();
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: data.response,
          recommendations: data.recommendations,
        };

        setMessages(prev => [...prev, assistantMessage]);
        await fetchLogs(sessionId);
      } else {
        throw new Error('Failed to send message');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewSearch = async () => {
    if (sessionId) {
      try {
        await fetch(`${API_BASE}/api/chat/${sessionId}`, {
          method: 'DELETE',
        });
      } catch (error) {
        console.error('Error clearing session:', error);
      }
    }
    
    setMessages([]);
    setSessionId(null);
    setLogs([]);
    setLogGroups([]);
    setInput('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const ProductCard: React.FC<{ product: Product }> = ({ product }) => (
    <div className="product-card">
      <div className="product-id">ID: {product.id}</div>
      <div className="product-name">{product.name}</div>
      <div className="product-price">${product.price}</div>
      <div className="product-details">
        {product.category} | {product.fit} | {product.color_or_print}
        {product.fabric && ` | ${product.fabric}`}
      </div>
      {product.available_sizes && product.available_sizes.length > 0 && (
        <div className="product-details">
          Sizes: {product.available_sizes.join(', ')}
        </div>
      )}
      {product.ranking_reasoning && (
        <div className="product-reasoning">
          💡 {product.ranking_reasoning}
        </div>
      )}
    </div>
  );

  const TypingIndicator = () => (
    <div className="typing-indicator">
      <span>Assistant is thinking</span>
      <div className="typing-dots">
        <div className="typing-dot"></div>
        <div className="typing-dot"></div>
        <div className="typing-dot"></div>
      </div>
    </div>
  );

  return (
    <div className="app">
      <header className="header">
        <h1>🛍️ Vibe Shopping Assistant</h1>
        <div className="header-controls">
          <button className="btn btn-primary" onClick={handleNewSearch}>
            🔄 New Search
          </button>
          <button 
            className="btn btn-primary" 
            onClick={() => setShowLogs(!showLogs)}
          >
            📊 {showLogs ? 'Hide' : 'Show'} Logs
          </button>
        </div>
      </header>

      <div className="main-content">
        <div className="chat-section">
          <div className="chat-messages">
            {messages.length === 0 ? (
              <div className="empty-state">
                <h2>Welcome to Vibe Shopping! 👋</h2>
                <p>
                  I'm your AI fashion assistant. Tell me what you're looking for and I'll help you find the perfect items!
                </p>
                <p>
                  Try something like: "I need a red dress for a party" or "casual top under $50"
                </p>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div key={message.id}>
                    <div className={`message ${message.type}`}>
                      {message.content}
                    </div>
                    {message.recommendations && message.recommendations.length > 0 && (
                      <div className="recommendations">
                        {message.recommendations.map((product, index) => (
                          <ProductCard key={`${product.id}-${index}`} product={product} />
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {isLoading && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          <form onSubmit={handleSubmit} className="chat-input-container">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message here..."
              className="chat-input"
              disabled={isLoading}
            />
            <button 
              type="submit" 
              className="send-btn"
              disabled={isLoading || !input.trim()}
            >
              Send
            </button>
          </form>
        </div>

        {showLogs && (
          <div className="logs-section">
            <div className="logs-header">
              🔍 System Logs
              <button 
                className="btn btn-small" 
                onClick={() => sessionId && fetchLogs(sessionId)}
                style={{ marginLeft: '10px', fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}
              >
                🔄 Refresh
              </button>
            </div>
            <div className="logs-content">
              {logGroups.length === 0 ? (
                <div className="log-entry info">No logs available - start a conversation to see system details</div>
              ) : (
                logGroups.map((group) => (
                  <div key={group.id} className={`log-group ${group.type}`}>
                    <div 
                      className="log-group-header"
                      onClick={() => toggleLogGroup(group.id)}
                    >
                      <span className="log-group-toggle">
                        {group.isExpanded ? '▼' : '▶'}
                      </span>
                      <span className="log-group-title">{group.title}</span>
                      <span className="log-group-timestamp">{group.timestamp}</span>
                      <span className="log-group-count">({group.logs.length})</span>
                    </div>
                    {group.isExpanded && (
                      <div className="log-group-content">
                        {group.logs.map((log, index) => {
                          // Determine log type from emoji prefix
                          let logClass = "log-entry";
                          if (log.includes("📊")) logClass += " extract";
                          else if (log.includes("🧠")) logClass += " llm";
                          else if (log.includes("🎯")) logClass += " filter";
                          else if (log.includes("✅")) logClass += " success";
                          else if (log.includes("❌")) logClass += " error";
                          else if (log.includes("⚠️")) logClass += " warning";
                          else if (log.includes("🔍")) logClass += " debug";
                          else logClass += " info";

                          return (
                            <div key={index} className={logClass}>
                              {log}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
