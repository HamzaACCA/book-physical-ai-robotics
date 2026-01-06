/**
 * RAG Chatbot Widget
 * Embeddable chat interface with session management and history
 */

(function() {
    // Configuration
    const API_BASE_URL = 'http://localhost:8000/api/v1/chat';
    const STORAGE_KEY = 'rag_chat_session_id';

    // State
    let sessionId = localStorage.getItem(STORAGE_KEY);
    let isOpen = false;

    // Create widget HTML
    function createWidget() {
        const widgetHTML = `
            <!-- Chat Button -->
            <div id="chat-button" class="chat-button">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <span class="chat-badge" id="chat-badge" style="display: none;">1</span>
            </div>

            <!-- Chat Window -->
            <div id="chat-window" class="chat-window" style="display: none;">
                <div class="chat-header">
                    <div class="chat-title">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                        </svg>
                        <span>Ask about this book</span>
                    </div>
                    <button id="chat-close" class="chat-close">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>

                <div id="chat-messages" class="chat-messages">
                    <div class="chat-message bot-message">
                        <div class="message-content">
                            Hi! I'm an AI assistant for this book on Physical AI & Humanoid Robotics. Ask me anything about the content!
                        </div>
                    </div>
                </div>

                <div class="chat-input-container">
                    <input
                        type="text"
                        id="chat-input"
                        class="chat-input"
                        placeholder="Type your question..."
                        autocomplete="off"
                    />
                    <button id="chat-send" class="chat-send">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="22" y1="2" x2="11" y2="13"></line>
                            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', widgetHTML);
    }

    // Add styles
    function addStyles() {
        const styles = `
            .chat-button {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                transition: transform 0.2s, box-shadow 0.2s;
                z-index: 9998;
            }

            .chat-button:hover {
                transform: scale(1.05);
                box-shadow: 0 6px 16px rgba(0,0,0,0.2);
            }

            .chat-badge {
                position: absolute;
                top: -5px;
                right: -5px;
                background: #ef4444;
                color: white;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: bold;
            }

            .chat-window {
                position: fixed;
                bottom: 90px;
                right: 20px;
                width: 380px;
                height: 550px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.15);
                display: flex;
                flex-direction: column;
                z-index: 9999;
                overflow: hidden;
            }

            .chat-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .chat-title {
                display: flex;
                align-items: center;
                gap: 10px;
                font-weight: 600;
                font-size: 16px;
            }

            .chat-close {
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                padding: 4px;
                display: flex;
                align-items: center;
                opacity: 0.9;
            }

            .chat-close:hover {
                opacity: 1;
            }

            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                background: #f9fafb;
            }

            .chat-message {
                margin-bottom: 16px;
                animation: fadeIn 0.3s ease-in;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .message-content {
                padding: 12px 16px;
                border-radius: 12px;
                max-width: 85%;
                word-wrap: break-word;
                line-height: 1.5;
            }

            .user-message .message-content {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin-left: auto;
            }

            .bot-message .message-content {
                background: white;
                color: #1f2937;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }

            .message-sources {
                margin-top: 8px;
                padding: 8px 12px;
                background: #f3f4f6;
                border-radius: 8px;
                font-size: 12px;
                color: #6b7280;
            }

            .typing-indicator {
                display: flex;
                gap: 4px;
                padding: 12px 16px;
                background: white;
                border-radius: 12px;
                width: fit-content;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }

            .typing-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #9ca3af;
                animation: typing 1.4s infinite;
            }

            .typing-dot:nth-child(2) {
                animation-delay: 0.2s;
            }

            .typing-dot:nth-child(3) {
                animation-delay: 0.4s;
            }

            @keyframes typing {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-10px); }
            }

            .chat-input-container {
                display: flex;
                gap: 8px;
                padding: 16px 20px;
                border-top: 1px solid #e5e7eb;
                background: white;
            }

            .chat-input {
                flex: 1;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s;
            }

            .chat-input:focus {
                border-color: #667eea;
            }

            .chat-send {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                border-radius: 8px;
                color: white;
                padding: 10px 16px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: opacity 0.2s;
            }

            .chat-send:hover {
                opacity: 0.9;
            }

            .chat-send:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            @media (max-width: 480px) {
                .chat-window {
                    width: calc(100vw - 40px);
                    height: calc(100vh - 140px);
                    bottom: 90px;
                    right: 20px;
                }
            }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }

    // Load chat history
    async function loadHistory() {
        if (!sessionId) return;

        try {
            const response = await fetch(`${API_BASE_URL}/history/${sessionId}`);
            if (response.ok) {
                const data = await response.json();
                const messagesContainer = document.getElementById('chat-messages');

                // Clear existing messages except welcome
                const welcomeMsg = messagesContainer.querySelector('.bot-message');
                messagesContainer.innerHTML = '';
                if (data.messages.length === 0 && welcomeMsg) {
                    messagesContainer.appendChild(welcomeMsg);
                }

                // Add history messages
                data.messages.forEach(msg => {
                    addMessage(msg.content, msg.role === 'user' ? 'user' : 'bot', false);
                });
            }
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    // Add message to chat
    function addMessage(text, type, scroll = true) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}-message`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;

        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);

        if (scroll) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    // Show typing indicator
    function showTyping() {
        const messagesContainer = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message bot-message';
        typingDiv.id = 'typing-indicator';

        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';

        typingDiv.appendChild(indicator);
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Remove typing indicator
    function removeTyping() {
        const typing = document.getElementById('typing-indicator');
        if (typing) typing.remove();
    }

    // Send message
    async function sendMessage(message) {
        if (!message.trim()) return;

        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('chat-send');

        // Disable input
        input.disabled = true;
        sendBtn.disabled = true;

        // Add user message
        addMessage(message, 'user');

        // Show typing
        showTyping();

        try {
            const response = await fetch(`${API_BASE_URL}/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId
                })
            });

            const data = await response.json();

            // Save session ID
            if (data.session_id) {
                sessionId = data.session_id;
                localStorage.setItem(STORAGE_KEY, sessionId);
            }

            // Remove typing
            removeTyping();

            // Add bot response
            addMessage(data.answer, 'bot');

        } catch (error) {
            removeTyping();
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            console.error('Chat error:', error);
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            input.value = '';
            input.focus();
        }
    }

    // Toggle chat window
    function toggleChat() {
        const chatWindow = document.getElementById('chat-window');
        const chatBadge = document.getElementById('chat-badge');

        isOpen = !isOpen;
        chatWindow.style.display = isOpen ? 'flex' : 'none';

        if (isOpen) {
            chatBadge.style.display = 'none';
            document.getElementById('chat-input').focus();
            if (!sessionId || document.querySelectorAll('.chat-message').length === 1) {
                loadHistory();
            }
        }
    }

    // Initialize
    function init() {
        createWidget();
        addStyles();

        // Event listeners
        document.getElementById('chat-button').addEventListener('click', toggleChat);
        document.getElementById('chat-close').addEventListener('click', toggleChat);

        document.getElementById('chat-send').addEventListener('click', () => {
            const input = document.getElementById('chat-input');
            sendMessage(input.value);
        });

        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage(e.target.value);
            }
        });
    }

    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
