import React, { useState, useEffect, useRef } from 'react';

const API_BASE = `http://${window.location.hostname}:8000`;

function ChatInterface({ initialMessage, onContextUsed }) {
    const [messages, setMessages] = useState([
        { id: 1, sender: 'bot', text: 'Hello! I am Hugo, your procurement assistant. How can I help you today?' },
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const processedRef = useRef(false);

    // Function to send message to backend
    const sendMessage = async (text) => {
        if (!text.trim()) return;

        setLoading(true);
        // Add user message to UI (if not already added by useEffect for initial)
        // Actually, let's keep it simple: caller handles the UI update?
        // No, local function handles UI.

        try {
            const response = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: text }),
            });

            if (response.ok) {
                const data = await response.json();
                setMessages(prev => [...prev, {
                    id: Date.now(),
                    sender: 'bot',
                    text: data.reply
                }]);
            } else {
                throw new Error('API Error');
            }
        } catch (error) {
            console.error("Chat error:", error);
            setMessages(prev => [...prev, {
                id: Date.now(),
                sender: 'bot',
                text: "Sorry, I'm having trouble connecting to the Hugo Knowledge Base. Please ensure the backend is running."
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleSendClick = () => {
        if (!input.trim()) return;
        const text = input;
        // Add user message immediately
        setMessages(prev => [...prev, { id: Date.now(), sender: 'user', text: text }]);
        setInput('');
        sendMessage(text);
    };

    // Handle initial context message (auto-send)
    useEffect(() => {
        if (initialMessage && !processedRef.current) {
            processedRef.current = true;
            // Show user message
            setMessages(prev => [...prev, { id: Date.now(), sender: 'user', text: initialMessage }]);
            // Call API
            sendMessage(initialMessage);

            if (onContextUsed) onContextUsed();
        }
    }, [initialMessage, onContextUsed]);

    return (
        <div className="chat-interface">
            <div className="chat-header">
                <div className="chat-title">
                    <h1>💬 Ask Hugo</h1>
                    <p>AI-powered procurement insights (Connected to Cloud Data)</p>
                </div>
            </div>

            <div className="chat-messages">
                {messages.map((msg, idx) => (
                    <div key={msg.id || idx} className={`message ${msg.sender}`}>
                        <div className="bubble">
                            {msg.text}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="message bot">
                        <div className="bubble">
                            <span className="typing-dot">.</span>
                            <span className="typing-dot">.</span>
                            <span className="typing-dot">.</span>
                        </div>
                    </div>
                )}
            </div>

            <div className="chat-input-area">
                <input
                    type="text"
                    placeholder={loading ? "Hugo is thinking..." : "Type your message..."}
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyPress={e => e.key === 'Enter' && !loading && handleSendClick()}
                    disabled={loading}
                />
                <button
                    className="btn btn-primary"
                    onClick={handleSendClick}
                    disabled={loading}
                >
                    Send
                </button>
            </div>
        </div>
    );
}

export default ChatInterface;
