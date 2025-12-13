const Chat = {
    currentChatUser: null,
    conversations: [],
    messages: [],
    replyingTo: null,
    selectedImage: null,
    isViewOnce: false,
    typingTimeout: null,
    pollInterval: null,
    emojiCategories: {
        'smileys': ['😀', '😃', '😄', '😁', '😅', '😂', '🤣', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙', '🥲', '😋', '😛', '😜', '🤪', '😝', '🤑', '🤗', '🤭', '🤫', '🤔', '🤐', '🤨', '😐', '😑', '😶', '😏', '😒', '🙄', '😬', '🤥'],
        'gestures': ['👍', '👎', '👌', '🤌', '🤏', '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👆', '👇', '☝️', '👋', '🤚', '🖐️', '✋', '🖖', '👏', '🙌', '👐', '🤲', '🤝', '🙏', '💪', '🦾'],
        'hearts': ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '♥️'],
        'objects': ['🔥', '✨', '🌟', '💫', '⭐', '🌈', '☀️', '🌙', '💰', '💎', '🎁', '🎉', '🎊', '🏆', '🥇', '📸', '🎵', '🎶', '💡', '📱', '💻', '🔒', '🔑', '💣']
    },
    quickReactions: ['❤️', '😂', '😮', '😢', '😠', '👍'],

    async init() {
        this.bindEvents();
        await this.loadConversations();
        this.startPolling();
        this.updateUnreadBadge();
    },

    bindEvents() {
        document.getElementById('chat-search-input')?.addEventListener('input', (e) => {
            this.filterConversations(e.target.value);
        });

        document.getElementById('chat-textarea')?.addEventListener('input', (e) => {
            this.autoResizeTextarea(e.target);
            this.sendTypingIndicator();
        });

        document.getElementById('chat-textarea')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        document.getElementById('chat-image-input')?.addEventListener('change', (e) => {
            this.handleImageSelect(e);
        });
    },

    async loadConversations() {
        try {
            const response = await App.apiRequest('/api/messages/conversations');
            if (response.success) {
                this.conversations = response.conversations || [];
                this.renderConversations();
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
        }
    },

    renderConversations() {
        const container = document.getElementById('conversations-list');
        if (!container) return;

        if (this.conversations.length === 0) {
            container.innerHTML = `
                <div class="sidebar-empty">
                    <div class="sidebar-empty-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"></path>
                        </svg>
                    </div>
                    <h3>Sin mensajes</h3>
                    <p>Inicia una conversacion</p>
                </div>
            `;
            return;
        }

        const currentUserId = this.currentChatUser?.id;
        container.innerHTML = this.conversations.map(conv => `
            <button class="conversation-item ${conv.unread_count > 0 ? 'unread' : ''} ${String(conv.other_user_id) === String(currentUserId) ? 'active' : ''}" 
                    onclick="Chat.openChat('${conv.other_user_id}', '${this.escapeHtml(conv.username || '')}', '${conv.avatar_url || ''}')">
                <div class="conversation-avatar">
                    ${conv.avatar_url 
                        ? `<img src="${this.escapeHtml(conv.avatar_url)}" class="conversation-avatar-img" alt="${this.escapeHtml(conv.username)}">`
                        : `<div class="conversation-avatar-initial">${(conv.username || 'U')[0].toUpperCase()}</div>`
                    }
                </div>
                <div class="conversation-content">
                    <div class="conversation-header">
                        <span class="conversation-name">${this.escapeHtml(conv.username || 'Usuario')}</span>
                        <span class="conversation-time">${this.formatTime(conv.last_message_at)}</span>
                    </div>
                    <div class="conversation-preview">
                        <span class="conversation-last-msg">${this.escapeHtml(this.truncateMessage(conv.last_message))}</span>
                        ${conv.unread_count > 0 ? `<span class="conversation-unread-badge">${conv.unread_count}</span>` : ''}
                    </div>
                </div>
            </button>
        `).join('');
    },

    filterConversations(query) {
        const items = document.querySelectorAll('.conversation-item');
        const q = query.toLowerCase();
        items.forEach(item => {
            const name = item.querySelector('.conversation-name')?.textContent.toLowerCase() || '';
            item.style.display = name.includes(q) ? '' : 'none';
        });
    },

    async openChat(userId, username, avatarUrl) {
        this.currentChatUser = { id: userId, username, avatarUrl };
        this.messages = [];
        this.replyingTo = null;
        this.selectedImage = null;

        const chatPanel = document.getElementById('chat-panel');
        const chatPlaceholder = document.getElementById('chat-placeholder');
        const chatSidebar = document.getElementById('chat-sidebar');
        
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        const activeConv = document.querySelector(`.conversation-item[onclick*="'${userId}'"]`);
        if (activeConv) activeConv.classList.add('active');
        
        if (chatPlaceholder) chatPlaceholder.style.display = 'none';
        if (chatPanel) {
            chatPanel.classList.add('active');
            this.renderChatHeader();
            await this.loadMessages();
            this.scrollToBottom();
            document.getElementById('chat-textarea')?.focus();
        }
        
        if (window.innerWidth <= 768 && chatSidebar) {
            chatSidebar.classList.add('hidden');
        }
    },

    closeChat() {
        const chatPanel = document.getElementById('chat-panel');
        const chatPlaceholder = document.getElementById('chat-placeholder');
        const chatSidebar = document.getElementById('chat-sidebar');
        
        if (chatPanel) chatPanel.classList.remove('active');
        if (chatPlaceholder) chatPlaceholder.style.display = 'flex';
        if (chatSidebar) chatSidebar.classList.remove('hidden');
        
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        
        this.currentChatUser = null;
        this.loadConversations();
    },

    renderChatHeader() {
        const user = this.currentChatUser;
        if (!user) return;

        const headerInfo = document.getElementById('chat-user-info');
        if (headerInfo) {
            headerInfo.innerHTML = `
                ${user.avatarUrl 
                    ? `<img src="${this.escapeHtml(user.avatarUrl)}" class="chat-user-avatar" alt="${this.escapeHtml(user.username)}">`
                    : `<div class="chat-user-avatar-initial">${(user.username || 'U')[0].toUpperCase()}</div>`
                }
                <div class="chat-user-details">
                    <div class="chat-user-name">${this.escapeHtml(user.username || 'Usuario')}</div>
                    <div class="chat-user-status" id="chat-user-status"></div>
                </div>
            `;
        }
    },

    async loadMessages() {
        if (!this.currentChatUser) return;

        try {
            const response = await App.apiRequest(`/api/messages/${this.currentChatUser.id}`);
            if (response.success) {
                this.messages = response.messages || [];
                this.renderMessages();
            }
        } catch (error) {
            console.error('Error loading messages:', error);
        }
    },

    renderMessages() {
        const container = document.getElementById('chat-messages');
        if (!container) return;

        if (this.messages.length === 0) {
            container.innerHTML = `
                <div class="messages-empty" style="height: 100%;">
                    <div class="messages-empty-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                        </svg>
                    </div>
                    <h3>Inicia la conversación</h3>
                    <p>Envía un mensaje para comenzar</p>
                </div>
            `;
            return;
        }

        const myUserId = String(App.user?.id || App.demoUserId || '0');
        let html = '';
        let lastDate = '';

        this.messages.forEach((msg, index) => {
            const msgDate = new Date(msg.created_at).toLocaleDateString();
            if (msgDate !== lastDate) {
                lastDate = msgDate;
                html += `
                    <div class="chat-date-separator">
                        <span>${this.formatDateSeparator(msg.created_at)}</span>
                    </div>
                `;
            }

            const isMine = String(msg.sender_id) === myUserId;
            const isDeleted = isMine ? msg.deleted_for_sender : msg.deleted_for_receiver;
            
            if (isDeleted) return;

            html += this.renderMessageBubble(msg, isMine);
        });

        container.innerHTML = html;
    },

    renderMessageBubble(msg, isMine) {
        const replyHtml = msg.reply_to_id ? this.renderReplyPreview(msg.reply_to_id) : '';
        const reactionsHtml = this.renderReactions(msg.reactions || []);
        
        let contentHtml = '';
        if (msg.image_url) {
            if (msg.is_view_once && !msg.viewed_at && !isMine) {
                contentHtml = `
                    <div class="message-image-container" onclick="Chat.viewOnceImage(${msg.id}, '${msg.image_url}')">
                        <div class="message-image-viewonce-overlay">
                            <div class="message-image-viewonce-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <polygon points="10 8 16 12 10 16 10 8"></polygon>
                                </svg>
                            </div>
                            <span>Foto · Toca para ver</span>
                        </div>
                    </div>
                `;
            } else if (msg.is_view_once && msg.viewed_at) {
                contentHtml = `<div class="message-text" style="opacity: 0.5; font-style: italic;">📷 Foto vista</div>`;
            } else {
                contentHtml = `
                    <div class="message-image-container">
                        <img src="${msg.image_url}" class="message-image" alt="Imagen" onclick="Chat.viewImage('${msg.image_url}')">
                    </div>
                `;
            }
        }
        
        if (msg.content) {
            contentHtml += `<div class="message-text">${this.escapeHtml(msg.content)}</div>`;
        }

        const statusIcon = isMine ? this.getStatusIcon(msg) : '';

        return `
            <div class="message-wrapper ${isMine ? 'mine' : 'other'}" data-msg-id="${msg.id}"
                 oncontextmenu="Chat.showMessageOptions(event, ${msg.id})"
                 onclick="Chat.handleMessageTap(event, ${msg.id})">
                <div class="message-bubble">
                    ${replyHtml}
                    ${contentHtml}
                </div>
                <div class="message-meta">
                    <span class="message-time">${this.formatMessageTime(msg.created_at)}</span>
                    ${statusIcon}
                </div>
                ${reactionsHtml}
            </div>
        `;
    },

    renderReplyPreview(replyToId) {
        const originalMsg = this.messages.find(m => m.id === replyToId);
        if (!originalMsg) return '';

        const myUserId = String(App.user?.id || App.demoUserId || '0');
        const senderName = String(originalMsg.sender_id) === myUserId ? 'Tú' : (this.currentChatUser?.username || 'Usuario');

        return `
            <div class="message-reply-preview">
                <div class="message-reply-name">${this.escapeHtml(senderName)}</div>
                <div class="message-reply-text">${this.escapeHtml(this.truncateMessage(originalMsg.content || '📷 Foto', 50))}</div>
            </div>
        `;
    },

    renderReactions(reactions) {
        if (!reactions || reactions.length === 0) return '';

        const grouped = {};
        reactions.forEach(r => {
            if (!grouped[r.emoji]) grouped[r.emoji] = [];
            grouped[r.emoji].push(r.user_id);
        });

        const myUserId = String(App.user?.id || App.demoUserId || '0');
        let html = '<div class="message-reactions">';
        for (const [emoji, users] of Object.entries(grouped)) {
            const isMine = users.includes(myUserId);
            html += `<span class="message-reaction ${isMine ? 'mine' : ''}" onclick="Chat.toggleReaction(event)">${emoji}${users.length > 1 ? ` ${users.length}` : ''}</span>`;
        }
        html += '</div>';
        return html;
    },

    getStatusIcon(msg) {
        if (msg.is_read) {
            return `<span class="message-status read"><svg viewBox="0 0 16 15" fill="currentColor"><path d="M15.01 3.316l-.478-.372a.365.365 0 0 0-.51.063L8.666 9.879a.32.32 0 0 1-.484.033l-.358-.325a.319.319 0 0 0-.484.032l-.378.483a.418.418 0 0 0 .036.541l1.32 1.266c.143.14.361.125.484-.033l6.272-8.048a.366.366 0 0 0-.064-.512zm-4.1 0l-.478-.372a.365.365 0 0 0-.51.063L4.566 9.879a.32.32 0 0 1-.484.033L1.891 7.769a.366.366 0 0 0-.515.006l-.423.433a.364.364 0 0 0 .006.514l3.258 3.185c.143.14.361.125.484-.033l6.272-8.048a.365.365 0 0 0-.063-.51z"/></svg></span>`;
        }
        return `<span class="message-status sent"><svg viewBox="0 0 12 11" fill="currentColor"><path d="M11.155.668a.457.457 0 0 0-.637-.083L4.094 5.682a.39.39 0 0 1-.607-.041L1.87 3.321a.457.457 0 0 0-.64-.094l-.527.407a.456.456 0 0 0-.084.637l2.795 3.63a.443.443 0 0 0 .606.075l7.27-5.676a.455.455 0 0 0 .083-.637l-.218-.995z"/></svg></span>`;
    },

    async sendMessage() {
        const textarea = document.getElementById('chat-textarea');
        const content = textarea?.value.trim() || '';
        
        if (!content && !this.selectedImage) return;
        if (!this.currentChatUser) return;

        const messageData = {
            receiver_id: this.currentChatUser.id,
            content: content,
            reply_to_id: this.replyingTo?.id || null,
            image_url: this.selectedImage,
            is_view_once: this.isViewOnce
        };

        if (textarea) textarea.value = '';
        this.autoResizeTextarea(textarea);
        this.clearReply();
        this.clearImagePreview();

        try {
            const response = await App.apiRequest('/api/messages', {
                method: 'POST',
                body: JSON.stringify(messageData)
            });

            if (response.success && response.message) {
                this.messages.push(response.message);
                this.renderMessages();
                this.scrollToBottom();
            }
        } catch (error) {
            console.error('Error sending message:', error);
            App.showToast('Error al enviar mensaje', 'error');
        }
    },

    setReply(msgId) {
        const msg = this.messages.find(m => m.id === msgId);
        if (!msg) return;

        this.replyingTo = msg;
        const myUserId = String(App.user?.id || App.demoUserId || '0');
        const senderName = String(msg.sender_id) === myUserId ? 'Tú' : (this.currentChatUser?.username || 'Usuario');

        const container = document.getElementById('chat-reply-preview');
        if (container) {
            container.classList.remove('hidden');
            container.innerHTML = `
                <div class="chat-reply-content">
                    <div class="chat-reply-name">${this.escapeHtml(senderName)}</div>
                    <div class="chat-reply-text">${this.escapeHtml(this.truncateMessage(msg.content || '📷 Foto', 50))}</div>
                </div>
                <button class="chat-reply-close" onclick="Chat.clearReply()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            `;
        }
        document.getElementById('chat-textarea')?.focus();
    },

    clearReply() {
        this.replyingTo = null;
        const container = document.getElementById('chat-reply-preview');
        if (container) {
            container.classList.add('hidden');
            container.innerHTML = '';
        }
    },

    handleImageSelect(event) {
        const file = event.target.files?.[0];
        if (!file) return;

        if (file.size > 5 * 1024 * 1024) {
            App.showToast('La imagen no puede superar 5MB', 'error');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            this.selectedImage = e.target.result;
            this.showImagePreview();
        };
        reader.readAsDataURL(file);
    },

    showImagePreview() {
        const container = document.getElementById('chat-image-preview');
        if (!container) return;

        container.classList.remove('hidden');
        container.innerHTML = `
            <img src="${this.selectedImage}" class="chat-image-preview-img" alt="Preview">
            <button class="chat-image-preview-remove" onclick="Chat.clearImagePreview()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
            <div class="chat-image-preview-viewonce">
                <input type="checkbox" id="viewonce-checkbox" ${this.isViewOnce ? 'checked' : ''} onchange="Chat.toggleViewOnce()">
                <label for="viewonce-checkbox">
                    <span class="checkbox-custom">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" width="12" height="12">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </span>
                    Ver una vez
                </label>
            </div>
        `;
    },

    clearImagePreview() {
        this.selectedImage = null;
        this.isViewOnce = false;
        const container = document.getElementById('chat-image-preview');
        if (container) {
            container.classList.add('hidden');
            container.innerHTML = '';
        }
        const input = document.getElementById('chat-image-input');
        if (input) input.value = '';
    },

    toggleViewOnce() {
        this.isViewOnce = !this.isViewOnce;
    },

    async viewOnceImage(msgId, imageUrl) {
        const viewer = document.createElement('div');
        viewer.className = 'viewonce-viewer';
        viewer.innerHTML = `
            <div class="viewonce-viewer-header">
                <button class="viewonce-viewer-close" onclick="this.closest('.viewonce-viewer').remove()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
                <div class="viewonce-viewer-timer" id="viewonce-timer">5s</div>
            </div>
            <img src="${imageUrl}" class="viewonce-viewer-img" alt="View Once">
            <div class="viewonce-viewer-footer">Esta foto desaparecerá después de verla</div>
        `;
        document.body.appendChild(viewer);

        try {
            await App.apiRequest(`/api/messages/${msgId}/view-once`, { method: 'POST' });
        } catch (e) {}

        let seconds = 5;
        const timer = viewer.querySelector('#viewonce-timer');
        const interval = setInterval(() => {
            seconds--;
            if (timer) timer.textContent = `${seconds}s`;
            if (seconds <= 0) {
                clearInterval(interval);
                viewer.remove();
                this.loadMessages();
            }
        }, 1000);
    },

    viewImage(imageUrl) {
        const viewer = document.createElement('div');
        viewer.className = 'viewonce-viewer';
        viewer.style.cursor = 'pointer';
        viewer.onclick = () => viewer.remove();
        viewer.innerHTML = `
            <div class="viewonce-viewer-header">
                <button class="viewonce-viewer-close" onclick="event.stopPropagation(); this.closest('.viewonce-viewer').remove()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <img src="${imageUrl}" class="viewonce-viewer-img" alt="Image">
        `;
        document.body.appendChild(viewer);
    },

    showEmojiPicker() {
        const existing = document.querySelector('.emoji-picker-overlay');
        if (existing) {
            existing.remove();
            return;
        }

        const overlay = document.createElement('div');
        overlay.className = 'emoji-picker-overlay';
        overlay.onclick = (e) => {
            if (e.target === overlay) overlay.remove();
        };

        const categories = Object.keys(this.emojiCategories);
        const firstCategory = categories[0];
        
        overlay.innerHTML = `
            <div class="emoji-picker">
                <div class="emoji-picker-tabs">
                    ${categories.map((cat, i) => `
                        <button class="emoji-picker-tab ${i === 0 ? 'active' : ''}" data-category="${cat}">
                            ${this.emojiCategories[cat][0]}
                        </button>
                    `).join('')}
                </div>
                <div class="emoji-picker-grid" id="emoji-grid">
                    ${this.emojiCategories[firstCategory].map(emoji => `
                        <button class="emoji-item" onclick="Chat.insertEmoji('${emoji}')">${emoji}</button>
                    `).join('')}
                </div>
            </div>
        `;

        overlay.querySelectorAll('.emoji-picker-tab').forEach(tab => {
            tab.onclick = () => {
                overlay.querySelectorAll('.emoji-picker-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                const cat = tab.dataset.category;
                const grid = overlay.querySelector('#emoji-grid');
                if (grid) {
                    grid.innerHTML = this.emojiCategories[cat].map(emoji => `
                        <button class="emoji-item" onclick="Chat.insertEmoji('${emoji}')">${emoji}</button>
                    `).join('');
                }
            };
        });

        document.body.appendChild(overlay);
    },

    insertEmoji(emoji) {
        const textarea = document.getElementById('chat-textarea');
        if (textarea) {
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const text = textarea.value;
            textarea.value = text.substring(0, start) + emoji + text.substring(end);
            textarea.selectionStart = textarea.selectionEnd = start + emoji.length;
            textarea.focus();
        }
        document.querySelector('.emoji-picker-overlay')?.remove();
    },

    handleMessageTap(event, msgId) {
        if (event.detail === 2) {
            this.showQuickReaction(event, msgId);
        }
    },

    showMessageOptions(event, msgId) {
        event.preventDefault();
        const msg = this.messages.find(m => m.id === msgId);
        if (!msg) return;

        const myUserId = String(App.user?.id || App.demoUserId || '0');
        const isMine = String(msg.sender_id) === myUserId;

        const overlay = document.createElement('div');
        overlay.className = 'message-options-overlay';
        overlay.onclick = (e) => {
            if (e.target === overlay) overlay.remove();
        };

        overlay.innerHTML = `
            <div class="message-options-menu">
                <div class="message-options-header">
                    <div class="message-options-preview">${this.escapeHtml(msg.content || '📷 Foto')}</div>
                </div>
                <button class="message-option-item" onclick="Chat.setReply(${msgId}); this.closest('.message-options-overlay').remove()">
                    <svg class="message-option-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="9 17 4 12 9 7"></polyline>
                        <path d="M20 18v-2a4 4 0 0 0-4-4H4"></path>
                    </svg>
                    Responder
                </button>
                <button class="message-option-item" onclick="Chat.showReactionPicker(${msgId}); this.closest('.message-options-overlay').remove()">
                    <svg class="message-option-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M8 14s1.5 2 4 2 4-2 4-2"></path>
                        <line x1="9" y1="9" x2="9.01" y2="9"></line>
                        <line x1="15" y1="9" x2="15.01" y2="9"></line>
                    </svg>
                    Reaccionar
                </button>
                <button class="message-option-item" onclick="Chat.copyMessage(${msgId}); this.closest('.message-options-overlay').remove()">
                    <svg class="message-option-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                    Copiar
                </button>
                ${isMine ? `
                <button class="message-option-item danger" onclick="Chat.showDeleteOptions(${msgId}); this.closest('.message-options-overlay').remove()">
                    <svg class="message-option-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                    Eliminar
                </button>
                ` : ''}
            </div>
        `;

        document.body.appendChild(overlay);
    },

    showQuickReaction(event, msgId) {
        const existing = document.querySelector('.reaction-picker');
        if (existing) existing.remove();

        const picker = document.createElement('div');
        picker.className = 'reaction-picker';
        picker.style.left = `${Math.min(event.clientX - 100, window.innerWidth - 220)}px`;
        picker.style.top = `${event.clientY - 50}px`;

        picker.innerHTML = this.quickReactions.map(emoji => `
            <button class="reaction-option" onclick="Chat.addReaction(${msgId}, '${emoji}')">${emoji}</button>
        `).join('');

        document.body.appendChild(picker);
        
        setTimeout(() => {
            document.addEventListener('click', function handler(e) {
                if (!picker.contains(e.target)) {
                    picker.remove();
                    document.removeEventListener('click', handler);
                }
            });
        }, 100);
    },

    showReactionPicker(msgId) {
        this.showQuickReaction({ clientX: window.innerWidth / 2, clientY: window.innerHeight / 2 }, msgId);
    },

    async addReaction(msgId, emoji) {
        document.querySelector('.reaction-picker')?.remove();
        
        try {
            await App.apiRequest(`/api/messages/${msgId}/reaction`, {
                method: 'POST',
                body: JSON.stringify({ emoji })
            });
            await this.loadMessages();
        } catch (error) {
            console.error('Error adding reaction:', error);
        }
    },

    copyMessage(msgId) {
        const msg = this.messages.find(m => m.id === msgId);
        if (msg?.content) {
            navigator.clipboard.writeText(msg.content);
            App.showToast('Mensaje copiado', 'success');
        }
    },

    showDeleteOptions(msgId) {
        const modal = document.createElement('div');
        modal.className = 'delete-message-modal';
        modal.innerHTML = `
            <div class="delete-message-content">
                <h3>¿Eliminar mensaje?</h3>
                <div class="delete-message-options">
                    <button class="delete-option-btn primary" onclick="Chat.deleteMessage(${msgId}, 'both'); this.closest('.delete-message-modal').remove()">
                        Eliminar para todos
                    </button>
                    <button class="delete-option-btn secondary" onclick="Chat.deleteMessage(${msgId}, 'me'); this.closest('.delete-message-modal').remove()">
                        Eliminar para mí
                    </button>
                    <button class="delete-option-btn secondary" onclick="this.closest('.delete-message-modal').remove()">
                        Cancelar
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    },

    async deleteMessage(msgId, deleteFor) {
        try {
            await App.apiRequest(`/api/messages/${msgId}`, {
                method: 'DELETE',
                body: JSON.stringify({ delete_for: deleteFor })
            });
            await this.loadMessages();
            App.showToast('Mensaje eliminado', 'success');
        } catch (error) {
            console.error('Error deleting message:', error);
            App.showToast('Error al eliminar', 'error');
        }
    },

    sendTypingIndicator() {
        if (this.typingTimeout) clearTimeout(this.typingTimeout);
        
        if (this.currentChatUser) {
            App.apiRequest(`/api/messages/typing/${this.currentChatUser.id}`, {
                method: 'POST'
            }).catch(() => {});
        }

        this.typingTimeout = setTimeout(() => {
            this.typingTimeout = null;
        }, 3000);
    },

    async checkTypingStatus() {
        if (!this.currentChatUser) return;

        try {
            const response = await App.apiRequest(`/api/messages/typing/${this.currentChatUser.id}/status`);
            const statusEl = document.getElementById('chat-user-status');
            if (statusEl) {
                if (response.is_typing) {
                    statusEl.textContent = 'escribiendo...';
                    statusEl.classList.add('typing');
                } else {
                    statusEl.textContent = '';
                    statusEl.classList.remove('typing');
                }
            }
        } catch (e) {}
    },

    startPolling() {
        if (this.pollInterval) clearInterval(this.pollInterval);
        
        this.pollInterval = setInterval(() => {
            if (this.currentChatUser) {
                this.loadMessages();
                this.checkTypingStatus();
            }
            this.updateUnreadBadge();
        }, 3000);
    },

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    },

    async updateUnreadBadge() {
        try {
            const response = await App.apiRequest('/api/messages/unread-count');
            if (response.success) {
                const badge = document.getElementById('messages-unread-badge');
                const count = response.unread_count || 0;
                if (badge) {
                    if (count > 0) {
                        badge.textContent = count > 99 ? '99+' : count;
                        badge.classList.remove('hidden');
                    } else {
                        badge.classList.add('hidden');
                    }
                }
            }
        } catch (e) {}
    },

    autoResizeTextarea(textarea) {
        if (!textarea) return;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    },

    scrollToBottom() {
        const container = document.getElementById('chat-messages');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    },

    formatTime(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return 'ahora';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m`;
        if (diff < 86400000) return date.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });
        if (diff < 604800000) return date.toLocaleDateString('es', { weekday: 'short' });
        return date.toLocaleDateString('es', { day: 'numeric', month: 'short' });
    },

    formatMessageTime(dateStr) {
        if (!dateStr) return '';
        return new Date(dateStr).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });
    },

    formatDateSeparator(dateStr) {
        const date = new Date(dateStr);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        if (date.toDateString() === today.toDateString()) return 'Hoy';
        if (date.toDateString() === yesterday.toDateString()) return 'Ayer';
        return date.toLocaleDateString('es', { weekday: 'long', day: 'numeric', month: 'long' });
    },

    truncateMessage(text, maxLength = 40) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    async openChatFromProfile(userId, username, avatarUrl) {
        await App.showSection('messages');
        setTimeout(() => {
            this.openChat(userId, username, avatarUrl);
        }, 100);
    },

    cleanup() {
        this.stopPolling();
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
            this.typingTimeout = null;
        }
    }
};

window.Chat = Chat;
