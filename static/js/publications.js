/**
 * Encrypted Publications System
 * Client-side AES-256-GCM encryption and media handling
 */

// Client-side encryption module using Web Crypto API
const CryptoModule = {
    async generateKey() {
        const key = await crypto.subtle.generateKey(
            { name: 'AES-GCM', length: 256 },
            true,
            ['encrypt', 'decrypt']
        );
        return key;
    },

    async exportKey(key) {
        const exported = await crypto.subtle.exportKey('raw', key);
        return this.arrayBufferToBase64(exported);
    },

    async importKey(keyBase64) {
        const keyBuffer = this.base64ToArrayBuffer(keyBase64);
        return await crypto.subtle.importKey(
            'raw',
            keyBuffer,
            { name: 'AES-GCM', length: 256 },
            true,
            ['encrypt', 'decrypt']
        );
    },

    generateIV() {
        return crypto.getRandomValues(new Uint8Array(12));
    },

    async encrypt(data, key) {
        const iv = this.generateIV();
        const encrypted = await crypto.subtle.encrypt(
            { name: 'AES-GCM', iv: iv, tagLength: 128 },
            key,
            data
        );
        return {
            ciphertext: encrypted,
            iv: this.arrayBufferToBase64(iv),
            tag: 'included'
        };
    },

    async decrypt(ciphertext, key, ivBase64) {
        const iv = this.base64ToArrayBuffer(ivBase64);
        const decrypted = await crypto.subtle.decrypt(
            { name: 'AES-GCM', iv: iv, tagLength: 128 },
            key,
            ciphertext
        );
        return decrypted;
    },

    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    },

    base64ToArrayBuffer(base64) {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    },

    async encryptFile(file) {
        const arrayBuffer = await file.arrayBuffer();
        const key = await this.generateKey();
        const encrypted = await this.encrypt(arrayBuffer, key);
        const exportedKey = await this.exportKey(key);
        
        return {
            encryptedData: new Blob([encrypted.ciphertext], { type: 'application/octet-stream' }),
            encryptionKey: exportedKey,
            iv: encrypted.iv,
            originalType: file.type,
            originalName: file.name,
            originalSize: file.size
        };
    },

    async decryptMedia(encryptedData, keyBase64, ivBase64, originalType) {
        try {
            const key = await this.importKey(keyBase64);
            const decrypted = await this.decrypt(encryptedData, key, ivBase64);
            return new Blob([decrypted], { type: originalType });
        } catch (error) {
            console.error('Decryption error:', error);
            return null;
        }
    }
};

const PublicationsManager = {
    currentUser: null,
    feedPosts: [],
    selectedFiles: [],
    currentPostIndex: 0,
    isUploading: false,
    contentType: 'media',
    
    REACTION_EMOJIS: ['❤️', '😂', '😮', '😢', '😡', '👏', '🔥', '💯'],
    
    DEFAULT_AVATAR: 'data:image/svg+xml;base64,' + btoa(`
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="50" fill="#1a2744"/>
            <circle cx="50" cy="35" r="18" fill="#3b82f6"/>
            <ellipse cx="50" cy="85" rx="30" ry="25" fill="#3b82f6"/>
        </svg>
    `.trim()),
    
    init() {
        this.setupEventListeners();
        this.loadFeed();
        this.loadStories();
    },
    
    setupEventListeners() {
        const createBtn = document.getElementById('floating-create-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.showCreateModal());
        }
        
        const fileInput = document.getElementById('publication-files');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }
        
        const uploadArea = document.getElementById('file-upload-area');
        if (uploadArea) {
            uploadArea.addEventListener('click', () => fileInput?.click());
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                this.handleFileDrop(e);
            });
        }
        
        const publishBtn = document.getElementById('publish-btn');
        if (publishBtn) {
            publishBtn.addEventListener('click', () => this.publishPost());
        }
        
        const captionInput = document.getElementById('caption-input');
        if (captionInput) {
            captionInput.addEventListener('input', () => this.updateCaptionCounter());
        }
        
        // Content type selector (Media vs Text only)
        const contentTypeBtns = document.querySelectorAll('.content-type-btn');
        contentTypeBtns.forEach(btn => {
            btn.addEventListener('click', () => this.switchContentType(btn.dataset.type));
        });
        
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('create-publication-modal')) {
                this.hideCreateModal();
            }
        });
    },
    
    switchContentType(type) {
        this.contentType = type;
        const fileUploadSection = document.getElementById('file-upload-section');
        const contentTypeBtns = document.querySelectorAll('.content-type-btn');
        
        contentTypeBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.type === type);
        });
        
        if (type === 'text') {
            fileUploadSection?.classList.add('hidden');
            this.selectedFiles = [];
            this.updateMediaPreview();
        } else {
            fileUploadSection?.classList.remove('hidden');
        }
    },
    
    async loadFeed() {
        try {
            console.log('Loading feed...');
            const response = await this.apiRequest('/api/publications/feed');
            console.log('Feed response:', response);
            if (response.success) {
                this.feedPosts = response.posts;
                console.log('Posts loaded:', this.feedPosts.length);
                this.renderFeed();
            } else {
                console.error('Feed load failed:', response.error);
            }
        } catch (error) {
            console.error('Error loading feed:', error);
        }
    },
    
    async loadStories() {
        try {
            const response = await this.apiRequest('/api/stories/feed');
            if (response.success) {
                this.renderStories(response.stories);
            }
        } catch (error) {
            console.error('Error loading stories:', error);
        }
    },
    
    renderFeed() {
        console.log('renderFeed called, posts:', this.feedPosts.length);
        const feedContainer = document.getElementById('publications-feed');
        console.log('Feed container found:', !!feedContainer);
        if (!feedContainer) return;
        
        if (this.feedPosts.length === 0) {
            feedContainer.innerHTML = `
                <div class="empty-gallery">
                    <div class="empty-gallery-icon">📷</div>
                    <h4>Sin publicaciones</h4>
                    <p>Sé el primero en compartir algo</p>
                </div>
            `;
            return;
        }
        
        const postsHtml = this.feedPosts.map(post => this.renderPost(post)).join('');
        console.log('Posts HTML length:', postsHtml.length);
        feedContainer.innerHTML = postsHtml;
        console.log('Feed container updated');
        this.setupPostInteractions();
    },
    
    renderPost(post) {
        const mediaHtml = this.renderPostMedia(post);
        const captionHtml = this.renderCaption(post.caption);
        const timeAgo = this.formatTimeAgo(post.created_at);
        const avatarUrl = post.avatar_url || this.DEFAULT_AVATAR;
        const likesText = post.reactions_count === 1 ? '1 me gusta' : `${post.reactions_count || 0} me gusta`;
        
        return `
            <article class="publication-card" data-post-id="${post.id}">
                <div class="publication-header">
                    <div class="publication-author">
                        <img src="${avatarUrl}" 
                             alt="${post.username}" class="publication-author-avatar"
                             onerror="this.src='${this.DEFAULT_AVATAR}'">
                        <div class="publication-author-info">
                            <span class="publication-author-name">${post.first_name || post.username}</span>
                            <span class="publication-time">${timeAgo}</span>
                        </div>
                    </div>
                    <button class="publication-menu-btn" onclick="PublicationsManager.showPostMenu(${post.id}, '${post.user_id}')" data-post-menu="${post.id}">
                        ⋯
                    </button>
                </div>
                
                ${mediaHtml}
                
                ${captionHtml}
                
                <div class="publication-actions">
                    <div class="publication-actions-left">
                        <button class="publication-action-btn ${post.user_reaction ? 'liked' : ''}" 
                                onclick="PublicationsManager.toggleReaction(${post.id})"
                                data-reaction-btn="${post.id}">
                            ${post.user_reaction ? '❤️' : '🤍'}
                        </button>
                        <button class="publication-action-btn" 
                                onclick="document.getElementById('inline-comment-${post.id}').focus()">
                            💬
                        </button>
                        <button class="publication-action-btn" 
                                onclick="PublicationsManager.sharePost(${post.id})">
                            ↗️
                        </button>
                    </div>
                    <button class="publication-action-btn ${post.user_saved ? 'saved' : ''}" 
                            onclick="PublicationsManager.toggleSave(${post.id})"
                            data-save-btn="${post.id}">
                        ${post.user_saved ? '🔖' : '📑'}
                    </button>
                </div>
                
                <div class="publication-stats">
                    <span class="likes-count" data-reactions-count="${post.id}">${likesText}</span>
                </div>
                
                <div class="inline-comments-section" id="comments-section-${post.id}">
                    ${post.comments_count > 0 ? `
                        <button class="view-comments-btn" onclick="PublicationsManager.loadInlineComments(${post.id})" data-view-comments="${post.id}">
                            Ver ${post.comments_count > 2 ? 'los ' + post.comments_count : ''} comentario${post.comments_count > 1 ? 's' : ''}
                        </button>
                    ` : ''}
                    <div class="inline-comments-list" id="comments-list-${post.id}"></div>
                </div>
                
                <div class="inline-comment-input">
                    <input type="text" 
                           id="inline-comment-${post.id}" 
                           class="comment-text-input" 
                           placeholder="Escribe un comentario..."
                           onkeypress="if(event.key==='Enter') PublicationsManager.sendInlineComment(${post.id})">
                    <button class="send-inline-btn" onclick="PublicationsManager.sendInlineComment(${post.id})">
                        Publicar
                    </button>
                </div>
                
                ${post.is_encrypted ? '<span class="encryption-badge">🔒</span>' : ''}
            </article>
        `;
    },
    
    renderPostMedia(post) {
        const media = post.media || [];
        if (media.length === 0) return '';
        
        if (media.length === 1) {
            const item = media[0];
            if (item.media_type === 'video') {
                return `
                    <div class="publication-media">
                        <video src="${item.media_url}" controls playsinline></video>
                    </div>
                `;
            }
            return `
                <div class="publication-media">
                    <img src="${item.media_url}" alt="Publication media" loading="lazy">
                </div>
            `;
        }
        
        return `
            <div class="publication-media">
                <div class="media-carousel" data-carousel="${post.id}">
                    <div class="carousel-track">
                        ${media.map((item, index) => `
                            <div class="carousel-slide">
                                ${item.media_type === 'video' 
                                    ? `<video src="${item.media_url}" controls playsinline></video>`
                                    : `<img src="${item.media_url}" alt="Media ${index + 1}" loading="lazy">`
                                }
                            </div>
                        `).join('')}
                    </div>
                    <button class="carousel-nav prev" onclick="PublicationsManager.prevSlide(${post.id})">‹</button>
                    <button class="carousel-nav next" onclick="PublicationsManager.nextSlide(${post.id})">›</button>
                    <div class="carousel-dots">
                        ${media.map((_, i) => `
                            <span class="carousel-dot ${i === 0 ? 'active' : ''}" data-index="${i}"></span>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    },
    
    renderCaption(caption) {
        if (!caption) return '';
        
        let processedCaption = caption
            .replace(/#(\w+)/g, '<span class="hashtag" onclick="PublicationsManager.goToHashtag(\'$1\')">#$1</span>')
            .replace(/@(\w+)/g, '<span class="mention" onclick="PublicationsManager.goToProfile(\'$1\')">@$1</span>');
        
        return `
            <div class="publication-caption">
                ${processedCaption}
            </div>
        `;
    },
    
    renderStories(stories) {
        const container = document.getElementById('stories-container');
        if (!container) return;
        
        const addStoryHtml = `
            <div class="story-item" onclick="PublicationsManager.createStory()">
                <div class="story-avatar-wrapper add-story">
                    <img src="${this.DEFAULT_AVATAR}" class="story-avatar" alt="Tu historia">
                    <span class="story-add-icon">+</span>
                </div>
                <span class="story-username">Tu historia</span>
            </div>
        `;
        
        const storiesHtml = stories.map(story => `
            <div class="story-item" onclick="PublicationsManager.viewStories('${story.user_id}')">
                <div class="story-avatar-wrapper ${story.has_viewed ? 'viewed' : ''}">
                    <img src="${story.avatar_url || this.DEFAULT_AVATAR}" 
                         class="story-avatar" alt="${story.username}"
                         onerror="this.src='${this.DEFAULT_AVATAR}'">
                </div>
                <span class="story-username">${story.username || story.first_name}</span>
            </div>
        `).join('');
        
        container.innerHTML = addStoryHtml + storiesHtml;
    },
    
    showCreateModal() {
        const modal = document.getElementById('create-publication-modal');
        if (modal) {
            modal.classList.remove('hidden');
            this.selectedFiles = [];
            this.contentType = 'media';
            this.switchContentType('media');
            this.updateMediaPreview();
            document.getElementById('caption-input').value = '';
            this.updateCaptionCounter();
        }
    },
    
    hideCreateModal() {
        const modal = document.getElementById('create-publication-modal');
        if (modal) {
            modal.classList.add('hidden');
            this.selectedFiles = [];
            this.contentType = 'media';
            this.updateMediaPreview();
            document.getElementById('caption-input').value = '';
            this.updateCaptionCounter();
        }
    },
    
    handleFileSelect(event) {
        const files = Array.from(event.target.files);
        this.addFiles(files);
    },
    
    handleFileDrop(event) {
        const files = Array.from(event.dataTransfer.files);
        this.addFiles(files);
    },
    
    addFiles(files) {
        const validFiles = files.filter(file => {
            const isImage = file.type.startsWith('image/');
            const isVideo = file.type.startsWith('video/');
            return isImage || isVideo;
        });
        
        if (this.selectedFiles.length + validFiles.length > 10) {
            this.showToast('Máximo 10 archivos permitidos', 'error');
            return;
        }
        
        this.selectedFiles = [...this.selectedFiles, ...validFiles];
        this.updateMediaPreview();
    },
    
    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.updateMediaPreview();
    },
    
    updateMediaPreview() {
        const previewGrid = document.getElementById('media-preview-grid');
        const uploadArea = document.getElementById('file-upload-area');
        
        if (!previewGrid) return;
        
        if (this.selectedFiles.length === 0) {
            previewGrid.innerHTML = '';
            previewGrid.classList.add('hidden');
            uploadArea?.classList.remove('hidden', 'has-files');
            return;
        }
        
        uploadArea?.classList.add('has-files');
        previewGrid.classList.remove('hidden');
        
        previewGrid.innerHTML = this.selectedFiles.map((file, index) => {
            const url = URL.createObjectURL(file);
            const isVideo = file.type.startsWith('video/');
            
            return `
                <div class="media-preview-item">
                    ${isVideo 
                        ? `<video src="${url}"></video>`
                        : `<img src="${url}" alt="Preview ${index + 1}">`
                    }
                    <button class="remove-media-btn" onclick="PublicationsManager.removeFile(${index})">×</button>
                </div>
            `;
        }).join('');
    },
    
    updateCaptionCounter() {
        const input = document.getElementById('caption-input');
        const counter = document.getElementById('caption-counter');
        if (input && counter) {
            counter.textContent = `${input.value.length} caracteres`;
        }
    },
    
    async publishPost() {
        if (this.isUploading) return;
        
        const caption = document.getElementById('caption-input')?.value || '';
        
        if (this.selectedFiles.length === 0 && !caption.trim()) {
            this.showToast('Añade contenido o una descripción', 'error');
            return;
        }
        
        this.isUploading = true;
        this.showUploadProgress(0);
        
        try {
            const encryptedFiles = [];
            const totalFiles = this.selectedFiles.length;
            
            for (let i = 0; i < this.selectedFiles.length; i++) {
                const file = this.selectedFiles[i];
                this.showUploadProgress(Math.floor((i / totalFiles) * 50));
                
                const encrypted = await CryptoModule.encryptFile(file);
                encryptedFiles.push({
                    data: encrypted.encryptedData,
                    key: encrypted.encryptionKey,
                    iv: encrypted.iv,
                    type: encrypted.originalType,
                    name: encrypted.originalName,
                    size: encrypted.originalSize
                });
            }
            
            this.showUploadProgress(60);
            
            const formData = new FormData();
            formData.append('caption', caption);
            formData.append('encryption_metadata', JSON.stringify(
                encryptedFiles.map(f => ({
                    key: f.key,
                    iv: f.iv,
                    type: f.type,
                    name: f.name,
                    size: f.size
                }))
            ));
            
            for (let i = 0; i < encryptedFiles.length; i++) {
                formData.append('files', encryptedFiles[i].data, `encrypted_${i}.bin`);
            }
            
            this.showUploadProgress(70);
            
            const response = await fetch('/api/publications/create', {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: formData
            });
            
            this.showUploadProgress(90);
            
            const result = await response.json();
            
            if (result.success) {
                this.showUploadProgress(100);
                this.showToast('Publicación creada con encriptación E2E', 'success');
                this.hideCreateModal();
                this.loadFeed();
            } else {
                this.showToast(result.error || 'Error al publicar', 'error');
            }
        } catch (error) {
            console.error('Publish error:', error);
            this.showToast('Error de conexión', 'error');
        } finally {
            this.isUploading = false;
            this.hideUploadProgress();
        }
    },
    
    showUploadProgress(percent) {
        const progress = document.getElementById('upload-progress');
        const fill = document.getElementById('progress-bar-fill');
        const text = document.getElementById('progress-text');
        
        if (progress) {
            progress.classList.remove('hidden');
            fill.style.width = `${percent}%`;
            text.textContent = percent < 100 ? 'Encriptando y subiendo...' : 'Procesando...';
        }
    },
    
    hideUploadProgress() {
        const progress = document.getElementById('upload-progress');
        if (progress) {
            progress.classList.add('hidden');
        }
    },
    
    pendingReactions: {},
    
    async toggleReaction(postId) {
        if (this.pendingReactions[postId]) return;
        this.pendingReactions[postId] = true;
        
        const btn = document.querySelector(`[data-reaction-btn="${postId}"]`);
        const countEl = document.querySelector(`[data-reactions-count="${postId}"]`);
        const isLiked = btn?.classList.contains('liked');
        
        try {
            const endpoint = isLiked 
                ? `/api/publications/${postId}/unreact`
                : `/api/publications/${postId}/react`;
            
            const response = await this.apiRequest(endpoint, {
                method: 'POST',
                body: JSON.stringify({ reaction: 'like' })
            });
            
            if (response.success) {
                btn?.classList.toggle('liked');
                btn.innerHTML = isLiked ? '🤍' : '❤️';
                
                const post = this.feedPosts.find(p => p.id === postId);
                if (post) {
                    const newCount = response.reactions_count !== undefined 
                        ? response.reactions_count 
                        : (post.reactions_count || 0) + (isLiked ? -1 : 1);
                    post.reactions_count = newCount;
                    post.user_reaction = isLiked ? null : 'like';
                    if (countEl) {
                        countEl.textContent = newCount === 1 ? '1 me gusta' : `${newCount} me gusta`;
                    }
                }
            }
        } catch (error) {
            console.error('Reaction error:', error);
        } finally {
            this.pendingReactions[postId] = false;
        }
    },
    
    async toggleSave(postId) {
        const btn = document.querySelector(`[data-save-btn="${postId}"]`);
        const isSaved = btn?.classList.contains('saved');
        
        try {
            const endpoint = isSaved 
                ? `/api/publications/${postId}/unsave`
                : `/api/publications/${postId}/save`;
            
            const response = await this.apiRequest(endpoint, { method: 'POST' });
            
            if (response.success) {
                btn?.classList.toggle('saved');
                btn.innerHTML = isSaved ? '📑' : '🔖';
                this.showToast(isSaved ? 'Eliminado de guardados' : 'Guardado', 'success');
            }
        } catch (error) {
            console.error('Save error:', error);
        }
    },
    
    async showComments(postId) {
        try {
            const [postResponse, commentsResponse] = await Promise.all([
                this.apiRequest(`/api/publications/${postId}`),
                this.apiRequest(`/api/publications/${postId}/comments`)
            ]);
            
            if (postResponse.success && commentsResponse.success) {
                this.renderPostDetail(postResponse.post, commentsResponse.comments);
            }
        } catch (error) {
            console.error('Error loading comments:', error);
        }
    },
    
    renderPostDetail(post, comments) {
        const modal = document.createElement('div');
        modal.className = 'post-detail-modal';
        modal.id = 'post-detail-modal';
        
        modal.innerHTML = `
            <div class="post-detail-header">
                <button class="back-btn" onclick="PublicationsManager.closePostDetail()">←</button>
                <span>Publicación</span>
                <button class="publication-menu-btn" onclick="PublicationsManager.showPostMenu(${post.id}, '${post.user_id}')">⋯</button>
            </div>
            <div class="post-detail-content">
                ${this.renderPost(post)}
                <div class="comments-section">
                    <div class="comments-list">
                        ${this.renderComments(comments)}
                    </div>
                </div>
            </div>
            <div class="comment-input-wrapper">
                <input type="text" class="comment-input" id="comment-input-${post.id}" 
                       placeholder="Añade un comentario...">
                <button class="send-comment-btn" onclick="PublicationsManager.sendComment(${post.id})">➤</button>
            </div>
        `;
        
        document.body.appendChild(modal);
    },
    
    renderComments(comments) {
        if (!comments || comments.length === 0) {
            return '<p style="color: var(--text-muted); text-align: center; padding: 20px;">Sin comentarios aún</p>';
        }
        
        return comments.map(comment => `
            <div class="comment-item" data-comment-id="${comment.id}">
                <img src="${comment.avatar_url || '/static/images/default-avatar.png'}" 
                     class="comment-avatar" alt="${comment.username}">
                <div class="comment-content">
                    <div class="comment-header">
                        <span class="comment-username">${comment.username}</span>
                        <span class="comment-time">${this.formatTimeAgo(comment.created_at)}</span>
                    </div>
                    <div class="comment-text">${comment.content}</div>
                    <div class="comment-actions">
                        <button class="comment-action-btn" onclick="PublicationsManager.likeComment(${comment.id})">
                            ❤️ ${comment.likes_count || 0}
                        </button>
                        <button class="comment-action-btn" onclick="PublicationsManager.replyToComment(${comment.id})">
                            Responder
                        </button>
                    </div>
                    ${comment.replies && comment.replies.length > 0 ? `
                        <div class="comment-replies">
                            ${this.renderComments(comment.replies)}
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
    },
    
    closePostDetail() {
        const modal = document.getElementById('post-detail-modal');
        if (modal) {
            modal.remove();
        }
    },
    
    async sendComment(postId) {
        const input = document.getElementById(`comment-input-${postId}`);
        const content = input?.value.trim();
        
        if (!content) return;
        
        try {
            const response = await this.apiRequest(`/api/publications/${postId}/comments`, {
                method: 'POST',
                body: JSON.stringify({ content })
            });
            
            if (response.success) {
                input.value = '';
                this.showComments(postId);
                this.showToast('Comentario añadido', 'success');
            }
        } catch (error) {
            console.error('Comment error:', error);
        }
    },
    
    async loadInlineComments(postId) {
        const container = document.getElementById(`comments-list-${postId}`);
        const viewBtn = document.querySelector(`[data-view-comments="${postId}"]`);
        
        if (!container) return;
        
        container.innerHTML = '<div class="loading-comments">Cargando...</div>';
        if (viewBtn) viewBtn.style.display = 'none';
        
        try {
            const response = await this.apiRequest(`/api/publications/${postId}/comments?limit=10`);
            
            if (response.success && response.comments) {
                container.innerHTML = this.renderInlineComments(response.comments, postId);
            } else {
                container.innerHTML = '<p class="no-comments">No hay comentarios</p>';
            }
        } catch (error) {
            console.error('Error loading comments:', error);
            container.innerHTML = '<p class="no-comments">Error al cargar comentarios</p>';
        }
    },
    
    renderInlineComments(comments, postId) {
        if (!comments || comments.length === 0) {
            return '<p class="no-comments">No hay comentarios aún</p>';
        }
        
        return comments.map(comment => {
            const avatarUrl = comment.avatar_url || this.DEFAULT_AVATAR;
            const username = comment.first_name || comment.username || 'Usuario';
            const timeAgo = this.formatTimeAgo(comment.created_at);
            
            return `
                <div class="inline-comment" data-comment-id="${comment.id}">
                    <img src="${avatarUrl}" class="inline-comment-avatar" alt="${username}" onerror="this.src='${this.DEFAULT_AVATAR}'">
                    <div class="inline-comment-body">
                        <div class="inline-comment-bubble">
                            <span class="inline-comment-name">${username}</span>
                            <span class="inline-comment-text">${comment.content}</span>
                        </div>
                        <div class="inline-comment-meta">
                            <span class="inline-comment-time">${timeAgo}</span>
                            <button class="inline-comment-like" onclick="PublicationsManager.likeComment(${comment.id})">
                                Me gusta ${comment.likes_count > 0 ? '(' + comment.likes_count + ')' : ''}
                            </button>
                            <button class="inline-comment-reply" onclick="PublicationsManager.focusReply(${postId}, '${username}')">
                                Responder
                            </button>
                        </div>
                        ${comment.replies && comment.replies.length > 0 ? `
                            <div class="inline-comment-replies">
                                ${comment.replies.map(reply => {
                                    const replyAvatar = reply.avatar_url || this.DEFAULT_AVATAR;
                                    const replyName = reply.first_name || reply.username || 'Usuario';
                                    return `
                                        <div class="inline-comment inline-reply">
                                            <img src="${replyAvatar}" class="inline-comment-avatar small" alt="${replyName}" onerror="this.src='${this.DEFAULT_AVATAR}'">
                                            <div class="inline-comment-body">
                                                <div class="inline-comment-bubble">
                                                    <span class="inline-comment-name">${replyName}</span>
                                                    <span class="inline-comment-text">${reply.content}</span>
                                                </div>
                                                <div class="inline-comment-meta">
                                                    <span class="inline-comment-time">${this.formatTimeAgo(reply.created_at)}</span>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
    },
    
    async sendInlineComment(postId) {
        const input = document.getElementById(`inline-comment-${postId}`);
        const content = input?.value.trim();
        
        if (!content) return;
        
        input.disabled = true;
        
        try {
            const response = await this.apiRequest(`/api/publications/${postId}/comments`, {
                method: 'POST',
                body: JSON.stringify({ content })
            });
            
            if (response.success) {
                input.value = '';
                
                const post = this.feedPosts.find(p => p.id === postId);
                if (post) {
                    post.comments_count = (post.comments_count || 0) + 1;
                }
                
                this.loadInlineComments(postId);
                this.showToast('Comentario publicado', 'success');
            }
        } catch (error) {
            console.error('Comment error:', error);
            this.showToast('Error al comentar', 'error');
        } finally {
            input.disabled = false;
        }
    },
    
    focusReply(postId, username) {
        const input = document.getElementById(`inline-comment-${postId}`);
        if (input) {
            input.value = `@${username} `;
            input.focus();
        }
    },
    
    async likeComment(commentId) {
        try {
            const response = await this.apiRequest(`/api/comments/${commentId}/like`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast('Like añadido', 'success');
            }
        } catch (error) {
            console.error('Like comment error:', error);
        }
    },
    
    sharePost(postId) {
        const shareUrl = `${window.location.origin}/post/${postId}`;
        
        const options = [
            { 
                label: 'Compartir en Telegram', 
                action: async () => {
                    if (window.Telegram?.WebApp) {
                        window.Telegram.WebApp.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent('Mira esta publicación en BUNK3R')}`);
                    } else {
                        window.open(`https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent('Mira esta publicación en BUNK3R')}`, '_blank');
                    }
                    await this.incrementShareCount(postId);
                }
            },
            { 
                label: 'Copiar enlace', 
                action: async () => {
                    try {
                        await navigator.clipboard.writeText(shareUrl);
                        this.showToast('Enlace copiado', 'success');
                        await this.incrementShareCount(postId);
                    } catch (e) {
                        this.showToast('No se pudo copiar', 'error');
                    }
                }
            },
            {
                label: 'Repostear en mi perfil',
                action: async () => {
                    try {
                        const response = await this.apiRequest(`/api/publications/${postId}/share`, {
                            method: 'POST',
                            body: JSON.stringify({ type: 'repost' })
                        });
                        if (response.success) {
                            this.showToast('Publicación reposteada', 'success');
                            this.loadFeed();
                        }
                    } catch (error) {
                        console.error('Repost error:', error);
                    }
                }
            }
        ];
        
        this.showActionSheet(options);
    },
    
    async incrementShareCount(postId) {
        try {
            await this.apiRequest(`/api/publications/${postId}/share-count`, {
                method: 'POST'
            });
        } catch (e) {
            console.error('Share count error:', e);
        }
    },
    
    showPostMenu(postId, postUserId) {
        const post = this.feedPosts.find(p => p.id === postId);
        const userId = postUserId || post?.user_id;
        const isOwner = post && userId === String(this.currentUser?.id || 0);
        
        const options = [
            { label: 'Copiar enlace', action: () => this.copyPostLink(postId) }
        ];
        
        if (isOwner) {
            options.unshift(
                { label: 'Editar', action: () => this.editPost(postId) },
                { label: 'Eliminar', action: () => this.deletePost(postId), danger: true }
            );
        } else {
            options.push(
                { label: 'Reportar publicacion', action: () => this.reportContent('post', postId) },
                { label: 'Bloquear usuario', action: () => this.blockUser(userId), danger: true }
            );
        }
        
        this.showActionSheet(options);
    },
    
    async blockUser(userId) {
        if (!confirm('¿Bloquear a este usuario? Ya no veras sus publicaciones.')) return;
        
        try {
            const response = await this.apiRequest(`/api/users/${userId}/block`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast('Usuario bloqueado', 'success');
                this.loadFeed();
            } else {
                this.showToast(response.error || 'Error al bloquear', 'error');
            }
        } catch (error) {
            console.error('Block user error:', error);
            this.showToast('Error al bloquear usuario', 'error');
        }
    },
    
    showActionSheet(options) {
        const existing = document.querySelector('.action-sheet-overlay');
        if (existing) existing.remove();
        
        const overlay = document.createElement('div');
        overlay.className = 'action-sheet-overlay';
        overlay.innerHTML = `
            <div class="action-sheet">
                ${options.map(opt => `
                    <button class="action-sheet-btn ${opt.danger ? 'danger' : ''}" 
                            onclick="PublicationsManager.executeAction('${opt.label}')">
                        ${opt.label}
                    </button>
                `).join('')}
                <button class="action-sheet-btn cancel" onclick="PublicationsManager.closeActionSheet()">
                    Cancelar
                </button>
            </div>
        `;
        
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) this.closeActionSheet();
        });
        
        this._actionOptions = options;
        document.body.appendChild(overlay);
    },
    
    executeAction(label) {
        const option = this._actionOptions?.find(o => o.label === label);
        if (option?.action) {
            option.action();
        }
        this.closeActionSheet();
    },
    
    closeActionSheet() {
        const overlay = document.querySelector('.action-sheet-overlay');
        if (overlay) overlay.remove();
    },
    
    async deletePost(postId) {
        if (!confirm('¿Eliminar esta publicación?')) return;
        
        try {
            const response = await this.apiRequest(`/api/publications/${postId}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                this.showToast('Publicación eliminada', 'success');
                this.loadFeed();
            }
        } catch (error) {
            console.error('Delete error:', error);
        }
    },
    
    copyPostLink(postId) {
        const url = `${window.location.origin}/post/${postId}`;
        navigator.clipboard.writeText(url).then(() => {
            this.showToast('Enlace copiado', 'success');
        });
    },
    
    async reportContent(type, id) {
        const reason = prompt('Motivo del reporte:');
        if (!reason) return;
        
        try {
            const response = await this.apiRequest('/api/report', {
                method: 'POST',
                body: JSON.stringify({
                    content_type: type,
                    content_id: id,
                    reason: reason
                })
            });
            
            if (response.success) {
                this.showToast('Reporte enviado', 'success');
            }
        } catch (error) {
            console.error('Report error:', error);
        }
    },
    
    prevSlide(postId) {
        const carousel = document.querySelector(`[data-carousel="${postId}"]`);
        if (!carousel) return;
        
        const track = carousel.querySelector('.carousel-track');
        const dots = carousel.querySelectorAll('.carousel-dot');
        const slideWidth = carousel.offsetWidth;
        
        let current = parseInt(carousel.dataset.current || '0');
        current = Math.max(0, current - 1);
        
        track.style.transform = `translateX(-${current * slideWidth}px)`;
        carousel.dataset.current = current;
        
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === current);
        });
    },
    
    nextSlide(postId) {
        const carousel = document.querySelector(`[data-carousel="${postId}"]`);
        if (!carousel) return;
        
        const track = carousel.querySelector('.carousel-track');
        const dots = carousel.querySelectorAll('.carousel-dot');
        const slideWidth = carousel.offsetWidth;
        const totalSlides = track.children.length;
        
        let current = parseInt(carousel.dataset.current || '0');
        current = Math.min(totalSlides - 1, current + 1);
        
        track.style.transform = `translateX(-${current * slideWidth}px)`;
        carousel.dataset.current = current;
        
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === current);
        });
    },
    
    async createStory() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*,video/*';
        
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/api/stories/create', {
                    method: 'POST',
                    headers: this.getAuthHeaders(),
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.showToast('Historia creada', 'success');
                    this.loadStories();
                } else {
                    this.showToast(result.error || 'Error al crear historia', 'error');
                }
            } catch (error) {
                console.error('Story creation error:', error);
            }
        };
        
        input.click();
    },
    
    async viewStories(userId) {
        try {
            const response = await this.apiRequest(`/api/stories/user/${userId}`);
            if (response.success && response.stories.length > 0) {
                this.showStoryViewer(response.stories, 0);
            }
        } catch (error) {
            console.error('Error loading stories:', error);
        }
    },
    
    showStoryViewer(stories, index) {
        const viewer = document.createElement('div');
        viewer.className = 'story-viewer';
        viewer.id = 'story-viewer';
        
        const story = stories[index];
        
        viewer.innerHTML = `
            <div class="story-progress-container">
                ${stories.map((_, i) => `
                    <div class="story-progress-bar">
                        <div class="story-progress-fill" style="width: ${i < index ? '100%' : '0%'}"></div>
                    </div>
                `).join('')}
            </div>
            <div class="story-viewer-header">
                <div class="story-user-info">
                    <img src="${story.avatar_url || '/static/images/default-avatar.png'}" 
                         class="story-viewer-avatar" alt="">
                    <div>
                        <div class="story-viewer-username">${story.username || 'Usuario'}</div>
                        <div class="story-viewer-time">${this.formatTimeAgo(story.created_at)}</div>
                    </div>
                </div>
                <button class="story-close-btn" onclick="PublicationsManager.closeStoryViewer()">×</button>
            </div>
            <div class="story-content">
                ${story.media_type === 'video' 
                    ? `<video src="${story.media_url}" autoplay playsinline></video>`
                    : `<img src="${story.media_url}" alt="Story">`
                }
            </div>
            <div class="story-nav-area prev" onclick="PublicationsManager.prevStory()"></div>
            <div class="story-nav-area next" onclick="PublicationsManager.nextStory()"></div>
        `;
        
        document.body.appendChild(viewer);
        
        this._currentStories = stories;
        this._currentStoryIndex = index;
        
        this.markStoryViewed(story.id);
        this.startStoryProgress(stories[index]);
    },
    
    async markStoryViewed(storyId) {
        try {
            await this.apiRequest(`/api/stories/${storyId}/view`, { method: 'POST' });
        } catch (error) {
            console.error('Error marking story viewed:', error);
        }
    },
    
    startStoryProgress(story) {
        const duration = story.duration_seconds || 5;
        const progressBars = document.querySelectorAll('.story-progress-fill');
        const currentBar = progressBars[this._currentStoryIndex];
        
        if (currentBar) {
            currentBar.style.transition = `width ${duration}s linear`;
            setTimeout(() => {
                currentBar.style.width = '100%';
            }, 50);
        }
        
        this._storyTimeout = setTimeout(() => {
            this.nextStory();
        }, duration * 1000);
    },
    
    prevStory() {
        if (this._storyTimeout) clearTimeout(this._storyTimeout);
        
        if (this._currentStoryIndex > 0) {
            this.closeStoryViewer();
            this.showStoryViewer(this._currentStories, this._currentStoryIndex - 1);
        } else {
            this.closeStoryViewer();
        }
    },
    
    nextStory() {
        if (this._storyTimeout) clearTimeout(this._storyTimeout);
        
        if (this._currentStoryIndex < this._currentStories.length - 1) {
            this.closeStoryViewer();
            this.showStoryViewer(this._currentStories, this._currentStoryIndex + 1);
        } else {
            this.closeStoryViewer();
        }
    },
    
    closeStoryViewer() {
        if (this._storyTimeout) clearTimeout(this._storyTimeout);
        const viewer = document.getElementById('story-viewer');
        if (viewer) viewer.remove();
    },
    
    goToHashtag(tag) {
        window.location.href = `/explore?hashtag=${tag}`;
    },
    
    goToProfile(username) {
        window.location.href = `/profile/${username}`;
    },
    
    setupPostInteractions() {
        document.querySelectorAll('.publication-action-btn').forEach(btn => {
            btn.addEventListener('touchstart', () => {
                btn.style.transform = 'scale(0.9)';
            });
            btn.addEventListener('touchend', () => {
                btn.style.transform = '';
            });
        });
    },
    
    formatTimeAgo(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);
        
        if (diff < 60) return 'ahora';
        if (diff < 3600) return `${Math.floor(diff / 60)}m`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
        if (diff < 604800) return `${Math.floor(diff / 86400)}d`;
        
        return date.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
    },
    
    async apiRequest(url, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...this.getAuthHeaders(),
            ...options.headers
        };
        
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        return response.json();
    },
    
    getAuthHeaders() {
        const headers = {};
        
        if (typeof App !== 'undefined') {
            if (App.isDemoMode) {
                headers['X-Demo-Mode'] = 'true';
            } else if (App.initData) {
                headers['X-Telegram-Init-Data'] = App.initData;
            }
        }
        
        return headers;
    },
    
    showToast(message, type = 'info') {
        const existing = document.querySelector('.toast-notification');
        if (existing) existing.remove();
        
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            padding: 12px 24px;
            background: ${type === 'error' ? 'var(--accent-danger)' : 'var(--accent-success)'};
            color: white;
            border-radius: 8px;
            z-index: 9999;
            animation: fadeIn 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('publications-feed')) {
        PublicationsManager.init();
    }
});

// Global alias for HTML onclick handlers
const Publications = {
    openCreateModal: () => PublicationsManager.showCreateModal(),
    closeCreateModal: () => PublicationsManager.hideCreateModal(),
    submitPost: () => PublicationsManager.publishPost(),
    closeViewModal: () => PublicationsManager.closeViewModal?.() || document.getElementById('view-post-modal')?.classList.add('hidden'),
    showPostOptions: () => PublicationsManager.showPostMenu?.(PublicationsManager._currentViewingPostId),
    submitComment: () => PublicationsManager.submitComment?.(),
    toggleEmojiPicker: () => {},
    closeStoryViewer: () => PublicationsManager.closeStoryViewer(),
    prevStory: () => PublicationsManager.prevStory(),
    nextStory: () => PublicationsManager.nextStory(),
    openStoryModal: () => PublicationsManager.createStory(),
    closeStoryModal: () => document.getElementById('create-story-modal')?.classList.add('hidden'),
    submitStory: () => PublicationsManager.createStory(),
    reportPost: () => PublicationsManager.reportContent?.('post', PublicationsManager._currentViewingPostId),
    sharePost: () => PublicationsManager.showActionSheet?.([{label: 'Compartir', action: () => {}}]),
    copyLink: () => PublicationsManager.copyPostLink?.(PublicationsManager._currentViewingPostId),
    editPost: () => PublicationsManager.editPost?.(PublicationsManager._currentViewingPostId),
    deletePost: () => PublicationsManager.deletePost?.(PublicationsManager._currentViewingPostId),
    closeOptionsModal: () => document.getElementById('post-options-modal')?.classList.add('hidden'),
    closeLikesModal: () => document.getElementById('likes-modal')?.classList.add('hidden'),
    closeReportModal: () => document.getElementById('report-modal')?.classList.add('hidden'),
    reactToStory: (emoji) => {}
};
