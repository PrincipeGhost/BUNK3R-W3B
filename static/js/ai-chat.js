const AIChat = {
    isOpen: false,
    messages: [],
    isLoading: false,
    
    init() {
        this.createChatWidget();
        this.bindEvents();
        this.loadHistory();
    },
    
    createChatWidget() {
        const widget = document.createElement('div');
        widget.id = 'ai-chat-widget';
        widget.innerHTML = `
            <button class="ai-chat-toggle" id="ai-chat-toggle" aria-label="Abrir chat de IA">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <span class="ai-badge">AI</span>
            </button>
            <div class="ai-chat-container hidden" id="ai-chat-container">
                <div class="ai-chat-header">
                    <div class="ai-chat-title">
                        <span class="ai-icon">🤖</span>
                        <span>BUNK3R AI</span>
                    </div>
                    <div class="ai-chat-actions">
                        <button class="ai-action-btn" id="ai-clear-btn" title="Limpiar chat">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            </svg>
                        </button>
                        <button class="ai-action-btn" id="ai-close-btn" title="Cerrar">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="ai-chat-messages" id="ai-chat-messages">
                    <div class="ai-welcome-message">
                        <div class="ai-avatar">🤖</div>
                        <div class="ai-bubble">
                            <p>Hola! Soy <strong>BUNK3R AI</strong>, tu asistente inteligente.</p>
                            <p>Puedo ayudarte con:</p>
                            <ul>
                                <li>Rastreo de paquetes</li>
                                <li>Criptomonedas y blockchain</li>
                                <li>Preguntas sobre la plataforma</li>
                                <li>Programacion y tecnologia</li>
                            </ul>
                            <p>Escribe tu pregunta!</p>
                        </div>
                    </div>
                </div>
                <div class="ai-chat-input-area">
                    <div class="ai-provider-indicator" id="ai-provider-indicator"></div>
                    <div class="ai-input-wrapper">
                        <textarea id="ai-chat-input" placeholder="Escribe tu mensaje..." rows="1"></textarea>
                        <button class="ai-send-btn" id="ai-send-btn" disabled>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                                <line x1="22" y1="2" x2="11" y2="13"></line>
                                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(widget);
    },
    
    bindEvents() {
        const toggle = document.getElementById('ai-chat-toggle');
        const close = document.getElementById('ai-close-btn');
        const clear = document.getElementById('ai-clear-btn');
        const input = document.getElementById('ai-chat-input');
        const send = document.getElementById('ai-send-btn');
        
        toggle.addEventListener('click', () => this.toggle());
        close.addEventListener('click', () => this.close());
        clear.addEventListener('click', () => this.clearChat());
        
        input.addEventListener('input', () => {
            send.disabled = !input.value.trim();
            this.autoResize(input);
        });
        
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        send.addEventListener('click', () => this.sendMessage());
    },
    
    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    },
    
    toggle() {
        this.isOpen = !this.isOpen;
        const container = document.getElementById('ai-chat-container');
        const toggle = document.getElementById('ai-chat-toggle');
        
        if (this.isOpen) {
            container.classList.remove('hidden');
            toggle.classList.add('active');
            document.getElementById('ai-chat-input').focus();
        } else {
            container.classList.add('hidden');
            toggle.classList.remove('active');
        }
    },
    
    close() {
        this.isOpen = false;
        document.getElementById('ai-chat-container').classList.add('hidden');
        document.getElementById('ai-chat-toggle').classList.remove('active');
    },
    
    async loadHistory() {
        try {
            const response = await fetch('/api/ai/history');
            const data = await response.json();
            
            if (data.success && data.history && data.history.length > 0) {
                this.messages = data.history;
                this.renderMessages();
            }
            
            if (data.providers && data.providers.length > 0) {
                const indicator = document.getElementById('ai-provider-indicator');
                indicator.textContent = `Powered by: ${data.providers.join(', ')}`;
            }
        } catch (error) {
            console.error('Error loading AI history:', error);
        }
    },
    
    renderMessages() {
        const container = document.getElementById('ai-chat-messages');
        const welcomeMsg = container.querySelector('.ai-welcome-message');
        
        if (this.messages.length > 0 && welcomeMsg) {
            welcomeMsg.style.display = 'none';
        }
        
        this.messages.forEach(msg => {
            if (!document.querySelector(`[data-msg-id="${msg.id || msg.content.substring(0, 20)}"]`)) {
                this.appendMessage(msg.role, msg.content, false);
            }
        });
    },
    
    appendMessage(role, content, save = true) {
        const container = document.getElementById('ai-chat-messages');
        const welcomeMsg = container.querySelector('.ai-welcome-message');
        if (welcomeMsg) welcomeMsg.style.display = 'none';
        
        const msgDiv = document.createElement('div');
        msgDiv.className = `ai-message ai-message-${role}`;
        msgDiv.setAttribute('data-msg-id', content.substring(0, 20));
        
        if (role === 'assistant') {
            msgDiv.innerHTML = `
                <div class="ai-avatar">🤖</div>
                <div class="ai-bubble">${this.formatMessage(content)}</div>
            `;
        } else {
            msgDiv.innerHTML = `
                <div class="ai-bubble">${this.escapeHtml(content)}</div>
            `;
        }
        
        container.appendChild(msgDiv);
        container.scrollTop = container.scrollHeight;
        
        if (save) {
            this.messages.push({ role, content });
        }
    },
    
    formatMessage(text) {
        let formatted = this.escapeHtml(text);
        formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        formatted = formatted.replace(/\n/g, '<br>');
        return formatted;
    },
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    showTyping() {
        const container = document.getElementById('ai-chat-messages');
        const typing = document.createElement('div');
        typing.className = 'ai-message ai-message-assistant ai-typing';
        typing.id = 'ai-typing-indicator';
        typing.innerHTML = `
            <div class="ai-avatar">🤖</div>
            <div class="ai-bubble">
                <div class="ai-typing-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        container.appendChild(typing);
        container.scrollTop = container.scrollHeight;
    },
    
    hideTyping() {
        const typing = document.getElementById('ai-typing-indicator');
        if (typing) typing.remove();
    },
    
    async sendMessage() {
        const input = document.getElementById('ai-chat-input');
        const message = input.value.trim();
        
        if (!message || this.isLoading) return;
        
        this.isLoading = true;
        input.value = '';
        input.style.height = 'auto';
        document.getElementById('ai-send-btn').disabled = true;
        
        this.appendMessage('user', message);
        this.showTyping();
        
        try {
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            this.hideTyping();
            
            if (data.success) {
                this.appendMessage('assistant', data.response);
                
                if (data.provider) {
                    const indicator = document.getElementById('ai-provider-indicator');
                    indicator.textContent = `Respondido por: ${data.provider}`;
                }
            } else {
                this.appendMessage('assistant', data.error || 'Error al procesar tu mensaje. Intenta de nuevo.');
            }
        } catch (error) {
            this.hideTyping();
            this.appendMessage('assistant', 'Error de conexion. Verifica tu internet e intenta de nuevo.');
            console.error('AI Chat error:', error);
        }
        
        this.isLoading = false;
    },
    
    async clearChat() {
        if (!confirm('Limpiar todo el historial del chat?')) return;
        
        try {
            await fetch('/api/ai/clear', { method: 'POST' });
            this.messages = [];
            
            const container = document.getElementById('ai-chat-messages');
            container.innerHTML = `
                <div class="ai-welcome-message">
                    <div class="ai-avatar">🤖</div>
                    <div class="ai-bubble">
                        <p>Chat limpiado. Como puedo ayudarte?</p>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error clearing chat:', error);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => AIChat.init(), 1000);
});
