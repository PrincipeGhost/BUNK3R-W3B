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
            if (typeof ErrorHandler !== 'undefined') {
                ErrorHandler.handle(error, 'Media decryption', false);
            }
            Logger?.warn('Decryption failed for media:', error.message);
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
    feedOffset: 0,
    feedLimit: 10,
    hasMorePosts: true,
    isLoadingFeed: false,
    feedObserver: null,
    
    feedPollingInterval: null,
    lastFeedCheck: null,
    newPostsCount: 0,
    POLLING_INTERVAL: 45000,
    POLLING_ACTIVE: false,
    _isPullRefreshing: false,
    _pullStartY: 0,
    
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
        this.initComposeBar();
        this.loadFeed();
        this.loadStories();
        this.loadTrendingHashtags();
        this.setupInfiniteScroll();
        this.startFeedPolling();
        this.setupPullToRefresh();
    },
    
    inlineFiles: [],
    
    initComposeBar() {
        const composeAvatar = document.getElementById('compose-avatar');
        const composeTextarea = document.getElementById('compose-textarea');
        const composeFileInput = document.getElementById('compose-file-input');
        const composeImageBtn = document.getElementById('compose-image-btn');
        const composeVideoBtn = document.getElementById('compose-video-btn');
        const composePublishBtn = document.getElementById('compose-publish-btn');
        
        const updateComposeBar = (user) => {
            if (composeAvatar && user) {
                if (user.profile_pic) {
                    composeAvatar.style.backgroundImage = `url(${user.profile_pic})`;
                    composeAvatar.textContent = '';
                } else {
                    const initial = (user.first_name || user.username || 'U')[0].toUpperCase();
                    composeAvatar.style.backgroundImage = 'none';
                    composeAvatar.textContent = initial;
                }
                
                if (composeTextarea) {
                    const name = user.first_name || user.username || 'amigo';
                    composeTextarea.placeholder = `¿Que estas pensando, ${name}?`;
                }
            }
        };
        
        if (composeTextarea) {
            composeTextarea.addEventListener('input', () => {
                composeTextarea.style.height = 'auto';
                composeTextarea.style.height = Math.min(composeTextarea.scrollHeight, 150) + 'px';
                this.updatePublishButton();
            });
        }
        
        if (composeImageBtn) {
            composeImageBtn.addEventListener('click', () => {
                if (composeFileInput) {
                    composeFileInput.accept = 'image/*';
                    composeFileInput.click();
                }
            });
        }
        
        if (composeVideoBtn) {
            composeVideoBtn.addEventListener('click', () => {
                if (composeFileInput) {
                    composeFileInput.accept = 'video/*';
                    composeFileInput.click();
                }
            });
        }
        
        if (composeFileInput) {
            composeFileInput.addEventListener('change', (e) => this.handleInlineFileSelect(e));
        }
        
        if (composePublishBtn) {
            composePublishBtn.addEventListener('click', () => this.publishInlinePost());
        }
        
        if (typeof App !== 'undefined' && App.user) {
            updateComposeBar(App.user);
        } else {
            setTimeout(() => {
                if (typeof App !== 'undefined' && App.user) {
                    updateComposeBar(App.user);
                }
            }, 1000);
        }
        
        window.updateComposeBarUser = updateComposeBar;
    },
    
    handleInlineFileSelect(e) {
        const files = Array.from(e.target.files || []);
        if (files.length === 0) return;
        
        const maxFiles = 10;
        if (this.inlineFiles.length + files.length > maxFiles) {
            if (typeof ToastManager !== 'undefined') {
                ToastManager.show(`Maximo ${maxFiles} archivos`, 'warning');
            }
            return;
        }
        
        files.forEach(file => {
            if (file.size > 100 * 1024 * 1024) {
                if (typeof ToastManager !== 'undefined') {
                    ToastManager.show('Archivo muy grande (max 100MB)', 'error');
                }
                return;
            }
            this.inlineFiles.push(file);
        });
        
        this.renderInlineMediaPreview();
        this.updatePublishButton();
        
        e.target.value = '';
    },
    
    renderInlineMediaPreview() {
        const preview = document.getElementById('compose-media-preview');
        if (!preview) return;
        
        if (this.inlineFiles.length === 0) {
            preview.classList.add('hidden');
            preview.innerHTML = '';
            return;
        }
        
        preview.classList.remove('hidden');
        preview.innerHTML = this.inlineFiles.map((file, index) => {
            const url = URL.createObjectURL(file);
            const isVideo = file.type.startsWith('video/');
            return `
                <div class="compose-media-item" data-index="${index}">
                    ${isVideo 
                        ? `<video src="${url}" muted></video><div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:white;font-size:20px;">▶</div>`
                        : `<img src="${url}" alt="Preview">`
                    }
                    <button class="compose-media-remove" onclick="PublicationsManager.removeInlineFile(${index})">&times;</button>
                </div>
            `;
        }).join('');
    },
    
    removeInlineFile(index) {
        this.inlineFiles.splice(index, 1);
        this.renderInlineMediaPreview();
        this.updatePublishButton();
    },
    
    updatePublishButton() {
        const textarea = document.getElementById('compose-textarea');
        const publishBtn = document.getElementById('compose-publish-btn');
        if (!publishBtn) return;
        
        const hasText = textarea && textarea.value.trim().length > 0;
        const hasFiles = this.inlineFiles.length > 0;
        
        if (hasText || hasFiles) {
            publishBtn.classList.remove('hidden');
        } else {
            publishBtn.classList.add('hidden');
        }
    },
    
    async publishInlinePost() {
        const textarea = document.getElementById('compose-textarea');
        const publishBtn = document.getElementById('compose-publish-btn');
        const caption = textarea ? textarea.value.trim() : '';
        
        if (!caption && this.inlineFiles.length === 0) {
            if (typeof ToastManager !== 'undefined') {
                ToastManager.show('Escribe algo o agrega media', 'warning');
            }
            return;
        }
        
        if (publishBtn) {
            publishBtn.disabled = true;
            publishBtn.textContent = 'Publicando...';
        }
        
        try {
            const formData = new FormData();
            formData.append('caption', caption);
            formData.append('content_type', this.inlineFiles.length > 0 ? 'media' : 'text');
            
            if (this.inlineFiles.length > 0) {
                for (let i = 0; i < this.inlineFiles.length; i++) {
                    const file = this.inlineFiles[i];
                    const encrypted = await CryptoModule.encryptFile(file);
                    formData.append('files', encrypted.encryptedData, `encrypted_${i}.bin`);
                    formData.append(`encryption_key_${i}`, encrypted.encryptionKey);
                    formData.append(`iv_${i}`, encrypted.iv);
                    formData.append(`original_type_${i}`, encrypted.originalType);
                    formData.append(`original_name_${i}`, encrypted.originalName);
                }
                formData.append('file_count', this.inlineFiles.length.toString());
            }
            
            const response = await fetch('/api/publications/create', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                if (typeof ToastManager !== 'undefined') {
                    ToastManager.show('Publicado!', 'success');
                }
                
                if (textarea) {
                    textarea.value = '';
                    textarea.style.height = 'auto';
                }
                this.inlineFiles = [];
                this.renderInlineMediaPreview();
                this.updatePublishButton();
                
                await this.loadFeed(true);
            } else {
                throw new Error(result.error || 'Error al publicar');
            }
        } catch (error) {
            console.error('Error publishing:', error);
            if (typeof ToastManager !== 'undefined') {
                ToastManager.show(error.message || 'Error al publicar', 'error');
            }
        } finally {
            if (publishBtn) {
                publishBtn.disabled = false;
                publishBtn.textContent = 'Publicar';
            }
        }
    },
    
    async loadTrendingHashtags() {
        try {
            const response = await this.apiRequest('/api/trending/hashtags?limit=10');
            if (response.success && response.hashtags && response.hashtags.length > 0) {
                const container = document.getElementById('trending-tags-list');
                const bar = document.getElementById('trending-hashtags-bar');
                if (container && bar) {
                    container.innerHTML = response.hashtags.map(tag => `
                        <button class="trending-tag" onclick="PublicationsManager.goToHashtag('${tag.tag}')">
                            #${tag.tag}
                            <span class="tag-count">${tag.posts_count}</span>
                        </button>
                    `).join('');
                    bar.classList.remove('hidden');
                }
            }
        } catch (error) {
            console.log('Trending hashtags not available:', error.message);
        }
    },
    
    setupPullToRefresh() {
        const feedContainer = document.getElementById('publications-feed');
        if (!feedContainer) return;
        
        let pullIndicator = document.getElementById('pull-refresh-indicator');
        if (!pullIndicator) {
            pullIndicator = document.createElement('div');
            pullIndicator.id = 'pull-refresh-indicator';
            pullIndicator.className = 'pull-refresh-indicator';
            pullIndicator.innerHTML = '<div class="pull-spinner"></div><span>Suelta para actualizar</span>';
            feedContainer.parentNode.insertBefore(pullIndicator, feedContainer);
        }
        
        feedContainer.addEventListener('touchstart', (e) => {
            if (window.scrollY <= 0) {
                this._pullStartY = e.touches[0].clientY;
            }
        }, { passive: true });
        
        feedContainer.addEventListener('touchmove', (e) => {
            if (this._isPullRefreshing || window.scrollY > 0) return;
            
            const pullDistance = e.touches[0].clientY - this._pullStartY;
            
            if (pullDistance > 0 && pullDistance < 150) {
                pullIndicator.style.transform = `translateY(${pullDistance - 60}px)`;
                pullIndicator.style.opacity = Math.min(pullDistance / 60, 1);
                
                if (pullDistance > 60) {
                    pullIndicator.classList.add('ready');
                } else {
                    pullIndicator.classList.remove('ready');
                }
            }
        }, { passive: true });
        
        feedContainer.addEventListener('touchend', async () => {
            const pullIndicator = document.getElementById('pull-refresh-indicator');
            if (!pullIndicator) return;
            
            if (pullIndicator.classList.contains('ready') && !this._isPullRefreshing) {
                this._isPullRefreshing = true;
                pullIndicator.classList.add('refreshing');
                pullIndicator.innerHTML = '<div class="pull-spinner spinning"></div><span>Actualizando...</span>';
                
                try {
                    await this.loadFeed(true);
                    if (typeof App !== 'undefined' && App.tg && App.tg.HapticFeedback) {
                        App.tg.HapticFeedback.impactOccurred('light');
                    }
                } finally {
                    setTimeout(() => {
                        pullIndicator.style.transform = '';
                        pullIndicator.style.opacity = '';
                        pullIndicator.classList.remove('ready', 'refreshing');
                        pullIndicator.innerHTML = '<div class="pull-spinner"></div><span>Suelta para actualizar</span>';
                        this._isPullRefreshing = false;
                    }, 300);
                }
            } else {
                pullIndicator.style.transform = '';
                pullIndicator.style.opacity = '';
                pullIndicator.classList.remove('ready');
            }
            
            this._pullStartY = 0;
        }, { passive: true });
    },

    cleanup() {
        this.stopFeedPolling();
        if (this.feedObserver) {
            this.feedObserver.disconnect();
            this.feedObserver = null;
        }
        if (this._storyTimeout) {
            clearTimeout(this._storyTimeout);
            this._storyTimeout = null;
        }
        if (this._boundVisibilityHandler) {
            document.removeEventListener('visibilitychange', this._boundVisibilityHandler);
            this._boundVisibilityHandler = null;
        }
        this.closeStoryViewer();
        const viewersModal = document.querySelector('.story-viewers-modal');
        if (viewersModal) viewersModal.remove();
    },
    
    setupInfiniteScroll() {
        const sentinel = document.createElement('div');
        sentinel.id = 'feed-sentinel';
        sentinel.className = 'feed-sentinel';
        const feedContainer = document.getElementById('publications-feed');
        if (feedContainer && feedContainer.parentNode) {
            feedContainer.parentNode.appendChild(sentinel);
        }
        
        this.feedObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && this.hasMorePosts && !this.isLoadingFeed) {
                    this.loadMorePosts();
                }
            });
        }, { rootMargin: '200px' });
        
        if (sentinel) {
            this.feedObserver.observe(sentinel);
        }
    },
    
    async loadMorePosts() {
        if (this.isLoadingFeed || !this.hasMorePosts) return;
        
        this.isLoadingFeed = true;
        const sentinel = document.getElementById('feed-sentinel');
        if (sentinel) {
            sentinel.innerHTML = '<div class="feed-loading-more"><div class="spinner"></div></div>';
        }
        
        try {
            const response = await this.apiRequest(`/api/publications/feed?offset=${this.feedOffset}&limit=${this.feedLimit}`);
            
            if (response.success) {
                const newPosts = response.posts || [];
                this.hasMorePosts = response.has_more;
                
                if (newPosts.length > 0) {
                    this.feedPosts = [...this.feedPosts, ...newPosts];
                    this.feedOffset += newPosts.length;
                    this.appendPostsToFeed(newPosts);
                }
            }
        } catch (error) {
            Logger?.error('Error loading more posts:', error);
        } finally {
            this.isLoadingFeed = false;
            if (sentinel) {
                sentinel.innerHTML = this.hasMorePosts ? '' : '<div class="feed-end">No hay mas publicaciones</div>';
            }
        }
    },
    
    appendPostsToFeed(posts) {
        const feedContainer = document.getElementById('publications-feed');
        if (!feedContainer) return;
        
        posts.forEach(post => {
            feedContainer.insertAdjacentHTML('beforeend', this.renderPost(post));
        });
        
        this.setupPostInteractions();
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
    
    async loadFeed(refresh = false) {
        const feedContainer = document.getElementById('publications-feed');
        
        if (typeof RequestManager !== 'undefined') {
            RequestManager.cancel('feed-load');
        }
        
        if (refresh) {
            this.feedOffset = 0;
            this.hasMorePosts = true;
            this.feedPosts = [];
        }
        
        try {
            if (typeof FallbackUI !== 'undefined' && feedContainer) {
                FallbackUI.showSkeleton('publications-feed', 2);
            }
            
            Logger?.debug('Loading feed...');
            const response = await this.apiRequest(`/api/publications/feed?offset=0&limit=${this.feedLimit}`, {}, 'feed-load');
            Logger?.debug('Feed response:', response);
            
            if (response.success) {
                this.feedPosts = response.posts || [];
                this.feedOffset = this.feedPosts.length;
                this.hasMorePosts = response.has_more !== false && this.feedPosts.length === this.feedLimit;
                Logger?.info('Posts loaded:', this.feedPosts.length, 'hasMore:', this.hasMorePosts);
                this.renderFeed();
                
                const sentinel = document.getElementById('feed-sentinel');
                if (sentinel) {
                    sentinel.innerHTML = this.hasMorePosts ? '' : '<div class="feed-end">No hay mas publicaciones</div>';
                }
            } else {
                Logger?.error('Feed load failed:', response.error);
                if (typeof FallbackUI !== 'undefined') {
                    FallbackUI.showLoadingError('publications-feed', 'PublicationsManager.loadFeed()', 'Error al cargar publicaciones');
                }
            }
        } catch (error) {
            if (typeof ErrorHandler !== 'undefined') {
                ErrorHandler.handle(error, 'Load feed');
            }
            if (typeof FallbackUI !== 'undefined') {
                FallbackUI.showLoadingError('publications-feed', 'PublicationsManager.loadFeed()', 'Error de conexión');
            }
        }
    },
    
    async loadStories() {
        try {
            Logger?.debug('Loading stories...');
            const response = await this.apiRequest('/api/stories/feed');
            if (response.success) {
                this.renderStories(response.stories);
                Logger?.info('Stories loaded:', response.stories?.length || 0);
            } else {
                Logger?.warn('Stories load failed:', response.error);
            }
        } catch (error) {
            if (typeof ErrorHandler !== 'undefined') {
                ErrorHandler.handle(error, 'Load stories', false);
            }
        }
    },

    startFeedPolling() {
        if (this.feedPollingInterval) {
            clearInterval(this.feedPollingInterval);
        }
        
        if (this._boundVisibilityHandler) {
            document.removeEventListener('visibilitychange', this._boundVisibilityHandler);
        }
        
        this.POLLING_ACTIVE = true;
        this.lastFeedCheck = Date.now();
        
        this.feedPollingInterval = setInterval(() => {
            if (this.POLLING_ACTIVE && document.visibilityState === 'visible') {
                this.checkForNewPosts();
            }
        }, this.POLLING_INTERVAL);
        
        this._boundVisibilityHandler = this.handleVisibilityChange.bind(this);
        document.addEventListener('visibilitychange', this._boundVisibilityHandler);
        
        Logger?.info('Feed polling started');
    },

    stopFeedPolling() {
        if (this.feedPollingInterval) {
            clearInterval(this.feedPollingInterval);
            this.feedPollingInterval = null;
        }
        if (this._boundVisibilityHandler) {
            document.removeEventListener('visibilitychange', this._boundVisibilityHandler);
            this._boundVisibilityHandler = null;
        }
        this.POLLING_ACTIVE = false;
        Logger?.info('Feed polling stopped');
    },

    handleVisibilityChange() {
        if (document.visibilityState === 'visible' && this.POLLING_ACTIVE) {
            const timeSinceLastCheck = Date.now() - (this.lastFeedCheck || 0);
            if (timeSinceLastCheck > this.POLLING_INTERVAL) {
                this.checkForNewPosts();
            }
        }
    },

    async checkForNewPosts() {
        if (this.isLoadingFeed) return;
        
        try {
            const latestPostId = this.feedPosts[0]?.id;
            if (!latestPostId) return;
            
            const response = await this.apiRequest(`/api/publications/check-new?since_id=${latestPostId}`);
            
            if (response.success && response.new_count > 0) {
                this.newPostsCount = response.new_count;
                this.showNewPostsBanner(response.new_count);
            }
            
            this.lastFeedCheck = Date.now();
        } catch (error) {
            Logger?.warn('Error checking for new posts:', error);
        }
    },

    showNewPostsBanner(count) {
        let banner = document.getElementById('new-posts-banner');
        
        if (!banner) {
            banner = document.createElement('div');
            banner.id = 'new-posts-banner';
            banner.className = 'new-posts-banner';
            banner.onclick = () => this.loadNewPosts();
            
            const feedContainer = document.getElementById('publications-feed');
            if (feedContainer && feedContainer.parentNode) {
                feedContainer.parentNode.insertBefore(banner, feedContainer);
            }
        }
        
        banner.innerHTML = `<span class="new-posts-arrow">↑</span> ${count} ${count === 1 ? 'nueva publicacion' : 'nuevas publicaciones'}`;
        banner.classList.add('visible');
        
        if (typeof App !== 'undefined' && App.tg && App.tg.HapticFeedback) {
            App.tg.HapticFeedback.impactOccurred('light');
        }
    },

    hideNewPostsBanner() {
        const banner = document.getElementById('new-posts-banner');
        if (banner) {
            banner.classList.remove('visible');
        }
        this.newPostsCount = 0;
    },

    async loadNewPosts() {
        this.hideNewPostsBanner();
        await this.loadFeed(true);
        
        const feedContainer = document.getElementById('publications-feed');
        if (feedContainer) {
            feedContainer.scrollTop = 0;
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    },
    
    renderFeed() {
        Logger?.debug('renderFeed called, posts:', this.feedPosts.length);
        const feedContainer = document.getElementById('publications-feed');
        if (!feedContainer) return;
        
        if (this.feedPosts.length === 0) {
            if (typeof FallbackUI !== 'undefined') {
                FallbackUI.showEmptyState('publications-feed', '📷', 'Sin publicaciones', 'Sé el primero en compartir algo');
            } else {
                feedContainer.innerHTML = `
                    <div class="empty-gallery">
                        <div class="empty-gallery-icon">📷</div>
                        <h4>Sin publicaciones</h4>
                        <p>Sé el primero en compartir algo</p>
                    </div>
                `;
            }
            return;
        }
        
        const postsHtml = this.feedPosts.map(post => this.renderPost(post)).join('');
        feedContainer.innerHTML = postsHtml;
        Logger?.debug('Feed container updated');
        this.setupPostInteractions();
    },
    
    renderPost(post) {
        const mediaHtml = this.renderPostMedia(post);
        const captionHtml = this.renderCaption(post.caption);
        const timeAgo = this.formatTimeAgo(post.created_at);
        const safeAvatarUrl = escapeAttribute(post.avatar_url || this.DEFAULT_AVATAR);
        const likesText = post.reactions_count === 1 ? '1 me gusta' : `${parseInt(post.reactions_count) || 0} me gusta`;
        const displayName = escapeHtml(post.first_name || post.username || 'Usuario');
        const username = escapeHtml(post.username || '');
        const safeUserId = sanitizeForJs(post.user_id);
        
        return `
            <article class="publication-card" data-post-id="${parseInt(post.id)}">
                <div class="publication-header">
                    <div class="publication-author">
                        <img src="${safeAvatarUrl}" 
                             alt="Avatar de ${displayName}" class="publication-author-avatar"
                             onerror="this.src='${this.DEFAULT_AVATAR}'">
                        <div class="publication-author-info">
                            <span class="publication-author-name">${displayName}</span>
                            <span class="publication-time">${timeAgo}</span>
                        </div>
                    </div>
                    <button class="publication-menu-btn" onclick="PublicationsManager.showPostMenu(${parseInt(post.id)}, '${safeUserId}')" data-post-menu="${parseInt(post.id)}" aria-label="Opciones de publicacion">
                        ⋯
                    </button>
                </div>
                
                ${mediaHtml}
                
                ${captionHtml}
                
                <div class="publication-actions">
                    <div class="publication-actions-left">
                        <button class="publication-action-btn ${post.user_reaction ? 'liked' : ''}" 
                                onclick="PublicationsManager.toggleReaction(${parseInt(post.id)})"
                                data-reaction-btn="${parseInt(post.id)}"
                                aria-label="${post.user_reaction ? 'Quitar me gusta' : 'Me gusta'}"
                                aria-pressed="${post.user_reaction ? 'true' : 'false'}">
                            <svg class="action-icon heart-icon" viewBox="0 0 24 24" fill="${post.user_reaction ? '#F6465D' : 'none'}" stroke="${post.user_reaction ? '#F6465D' : 'currentColor'}" stroke-width="2">
                                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                            </svg>
                        </button>
                        <button class="publication-action-btn" 
                                onclick="document.getElementById('inline-comment-${parseInt(post.id)}').focus()"
                                aria-label="Comentar">
                            <svg class="action-icon comment-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                            </svg>
                        </button>
                        <button class="publication-action-btn" 
                                onclick="PublicationsManager.sharePost(${parseInt(post.id)})"
                                aria-label="Compartir">
                            <svg class="action-icon share-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
                            </svg>
                        </button>
                    </div>
                    <button class="publication-action-btn ${post.user_saved ? 'saved' : ''}" 
                            onclick="PublicationsManager.toggleSave(${parseInt(post.id)})"
                            data-save-btn="${parseInt(post.id)}"
                            aria-label="${post.user_saved ? 'Quitar de guardados' : 'Guardar'}"
                            aria-pressed="${post.user_saved ? 'true' : 'false'}">
                        <svg class="action-icon bookmark-icon" viewBox="0 0 24 24" fill="${post.user_saved ? '#F0B90B' : 'none'}" stroke="${post.user_saved ? '#F0B90B' : 'currentColor'}" stroke-width="2">
                            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                        </svg>
                    </button>
                </div>
                
                <div class="publication-stats">
                    <span class="likes-count" data-reactions-count="${parseInt(post.id)}">${likesText}</span>
                </div>
                
                <div class="inline-comments-section" id="comments-section-${parseInt(post.id)}">
                    ${post.comments_count > 0 ? `
                        <button class="view-comments-btn" onclick="PublicationsManager.loadInlineComments(${parseInt(post.id)})" data-view-comments="${parseInt(post.id)}">
                            Ver ${parseInt(post.comments_count) > 2 ? 'los ' + parseInt(post.comments_count) : ''} comentario${parseInt(post.comments_count) > 1 ? 's' : ''}
                        </button>
                    ` : ''}
                    <div class="inline-comments-list" id="comments-list-${parseInt(post.id)}"></div>
                </div>
                
                <div class="inline-comment-input">
                    <input type="text" 
                           id="inline-comment-${parseInt(post.id)}" 
                           class="comment-text-input" 
                           placeholder="Escribe un comentario..."
                           onkeypress="if(event.key==='Enter') PublicationsManager.sendInlineComment(${parseInt(post.id)})">
                    <button class="send-inline-btn" onclick="PublicationsManager.sendInlineComment(${parseInt(post.id)})">
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
            const safeUrl = escapeAttribute(item.media_url || '');
            if (item.media_type === 'video') {
                return `
                    <div class="publication-media">
                        <video src="${safeUrl}" controls playsinline></video>
                    </div>
                `;
            }
            return `
                <div class="publication-media">
                    <img src="${safeUrl}" alt="Publication media" loading="lazy">
                </div>
            `;
        }
        
        return `
            <div class="publication-media">
                <div class="media-carousel" data-carousel="${parseInt(post.id)}">
                    <div class="carousel-track">
                        ${media.map((item, index) => {
                            const safeUrl = escapeAttribute(item.media_url || '');
                            return `
                            <div class="carousel-slide">
                                ${item.media_type === 'video' 
                                    ? `<video src="${safeUrl}" controls playsinline></video>`
                                    : `<img src="${safeUrl}" alt="Media ${parseInt(index) + 1}" loading="lazy">`
                                }
                            </div>
                        `;}).join('')}
                    </div>
                    <button class="carousel-nav prev" onclick="PublicationsManager.prevSlide(${parseInt(post.id)})">‹</button>
                    <button class="carousel-nav next" onclick="PublicationsManager.nextSlide(${parseInt(post.id)})">›</button>
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
        
        const safeCaption = escapeHtml(caption);
        let processedCaption = safeCaption
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
        
        const storiesHtml = stories.map(story => {
            const safeAvatarUrl = escapeAttribute(story.avatar_url || this.DEFAULT_AVATAR);
            const safeUserId = sanitizeForJs(story.user_id);
            const safeUsername = escapeHtml(story.username || story.first_name || 'Usuario');
            return `
            <div class="story-item" onclick="PublicationsManager.viewStories('${safeUserId}')">
                <div class="story-avatar-wrapper ${story.has_viewed ? 'viewed' : ''}">
                    <img src="${safeAvatarUrl}" 
                         class="story-avatar" alt="${safeUsername}"
                         onerror="this.src='${this.DEFAULT_AVATAR}'">
                </div>
                <span class="story-username">${safeUsername}</span>
            </div>
        `;}).join('');
        
        container.innerHTML = addStoryHtml + storiesHtml;
    },
    
    showCreateModal(initialType = null) {
        const modal = document.getElementById('create-publication-modal');
        if (modal) {
            modal.classList.remove('hidden');
            this.selectedFiles = [];
            this.contentType = 'media';
            this.switchContentType('media');
            this.updateMediaPreview();
            document.getElementById('caption-input').value = '';
            this.updateCaptionCounter();
            
            if (initialType === 'image' || initialType === 'video') {
                setTimeout(() => {
                    const fileInput = document.getElementById('publication-files');
                    if (fileInput) {
                        if (initialType === 'image') {
                            fileInput.accept = 'image/*';
                        } else if (initialType === 'video') {
                            fileInput.accept = 'video/*';
                        }
                        fileInput.click();
                        fileInput.accept = 'image/*,video/*';
                    }
                }, 100);
            }
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
    
    MAX_IMAGE_SIZE: 10 * 1024 * 1024,
    MAX_VIDEO_SIZE: 100 * 1024 * 1024,
    
    addFiles(files) {
        const validatedFiles = [];
        const errors = [];
        
        for (const file of files) {
            const isImage = file.type.startsWith('image/');
            const isVideo = file.type.startsWith('video/');
            
            if (!isImage && !isVideo) {
                errors.push(`${file.name}: tipo no soportado`);
                continue;
            }
            
            if (isImage && file.size > this.MAX_IMAGE_SIZE) {
                errors.push(`${file.name}: imagen muy grande (máx 10MB)`);
                continue;
            }
            
            if (isVideo && file.size > this.MAX_VIDEO_SIZE) {
                errors.push(`${file.name}: video muy grande (máx 100MB)`);
                continue;
            }
            
            validatedFiles.push(file);
        }
        
        if (errors.length > 0) {
            this.showToast(errors[0], 'error');
            Logger?.warn('File validation errors:', errors);
        }
        
        if (validatedFiles.length === 0) return;
        
        if (this.selectedFiles.length + validatedFiles.length > 10) {
            this.showToast('Máximo 10 archivos permitidos', 'error');
            return;
        }
        
        this.selectedFiles = [...this.selectedFiles, ...validatedFiles];
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
    
    showUploadProgress(percent, stage = '') {
        const progress = document.getElementById('upload-progress');
        const fill = document.getElementById('progress-bar-fill');
        const text = document.getElementById('progress-text');
        
        if (progress) {
            progress.classList.remove('hidden');
            fill.style.width = `${percent}%`;
            
            let message = '';
            if (stage) {
                message = stage;
            } else if (percent < 50) {
                message = 'Encriptando archivos...';
            } else if (percent < 70) {
                message = 'Preparando subida...';
            } else if (percent < 90) {
                message = 'Subiendo a servidor...';
            } else if (percent < 100) {
                message = 'Finalizando...';
            } else {
                message = 'Completado';
            }
            
            if (text) {
                text.textContent = `${percent}% - ${message}`;
            }
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
        
        if (btn) {
            btn.classList.add('liking');
            setTimeout(() => btn.classList.remove('liking'), 300);
        }
        
        try {
            const endpoint = isLiked 
                ? `/api/publications/${postId}/unreact`
                : `/api/publications/${postId}/react`;
            
            const response = await this.apiRequest(endpoint, {
                method: 'POST',
                body: JSON.stringify({ reaction: 'like' })
            });
            
            if (response.success) {
                if (!isLiked) {
                    this.showFloatingHeart(btn);
                }
                
                btn?.classList.toggle('liked');
                const heartFill = isLiked ? 'none' : '#F6465D';
                const heartStroke = isLiked ? 'currentColor' : '#F6465D';
                btn.innerHTML = `<svg class="action-icon heart-icon" viewBox="0 0 24 24" fill="${heartFill}" stroke="${heartStroke}" stroke-width="2">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>`;
                
                if (typeof App !== 'undefined' && App.tg && App.tg.HapticFeedback) {
                    App.tg.HapticFeedback.impactOccurred('light');
                }
                
                const post = this.feedPosts.find(p => p.id === postId);
                if (post) {
                    const newCount = response.reactions_count !== undefined 
                        ? response.reactions_count 
                        : (post.reactions_count || 0) + (isLiked ? -1 : 1);
                    post.reactions_count = newCount;
                    post.user_reaction = isLiked ? null : 'like';
                    if (countEl) {
                        countEl.textContent = newCount === 1 ? '1 me gusta' : `${newCount} me gusta`;
                        countEl.classList.add('count-updated');
                        setTimeout(() => countEl.classList.remove('count-updated'), 300);
                    }
                }
            }
        } catch (error) {
            console.error('Reaction error:', error);
        } finally {
            this.pendingReactions[postId] = false;
        }
    },
    
    showFloatingHeart(btn) {
        if (!btn) return;
        const heart = document.createElement('span');
        heart.className = 'floating-heart';
        heart.innerHTML = `<svg viewBox="0 0 24 24" fill="#F6465D" stroke="#F6465D" stroke-width="2" width="20" height="20">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>`;
        btn.appendChild(heart);
        setTimeout(() => heart.remove(), 1000);
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
                const bookmarkFill = isSaved ? 'none' : '#F0B90B';
                const bookmarkStroke = isSaved ? 'currentColor' : '#F0B90B';
                btn.innerHTML = `<svg class="action-icon bookmark-icon" viewBox="0 0 24 24" fill="${bookmarkFill}" stroke="${bookmarkStroke}" stroke-width="2">
                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                </svg>`;
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
        const safeUserId = sanitizeForJs(post.user_id);
        
        modal.innerHTML = `
            <div class="post-detail-header">
                <button class="back-btn" onclick="PublicationsManager.closePostDetail()">←</button>
                <span>Publicación</span>
                <button class="publication-menu-btn" onclick="PublicationsManager.showPostMenu(${parseInt(post.id)}, '${safeUserId}')">⋯</button>
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
                <input type="text" class="comment-input" id="comment-input-${parseInt(post.id)}" 
                       placeholder="Añade un comentario...">
                <button class="send-comment-btn" onclick="PublicationsManager.sendComment(${parseInt(post.id)})">➤</button>
            </div>
        `;
        
        document.body.appendChild(modal);
    },
    
    renderComments(comments) {
        if (!comments || comments.length === 0) {
            return '<p style="color: var(--text-muted); text-align: center; padding: 20px;">Sin comentarios aún</p>';
        }
        
        return comments.map(comment => {
            const safeAvatarUrl = escapeAttribute(comment.avatar_url || '/static/images/default-avatar.png');
            const safeUsername = escapeHtml(comment.username || 'Usuario');
            return `
            <div class="comment-item" data-comment-id="${parseInt(comment.id)}">
                <img src="${safeAvatarUrl}" 
                     class="comment-avatar" alt="${safeUsername}">
                <div class="comment-content">
                    <div class="comment-header">
                        <span class="comment-username">${safeUsername}</span>
                        <span class="comment-time">${this.formatTimeAgo(comment.created_at)}</span>
                    </div>
                    <div class="comment-text">${escapeHtml(comment.content || '')}</div>
                    <div class="comment-actions">
                        <button class="comment-action-btn" onclick="PublicationsManager.likeComment(${parseInt(comment.id)})">
                            ❤️ ${parseInt(comment.likes_count) || 0}
                        </button>
                        <button class="comment-action-btn" onclick="PublicationsManager.replyToComment(${parseInt(comment.id)})">
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
        `;}).join('');
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
    
    commentsState: {},
    
    async loadInlineComments(postId, append = false) {
        const container = document.getElementById(`comments-list-${postId}`);
        const viewBtn = document.querySelector(`[data-view-comments="${postId}"]`);
        
        if (!container) return;
        
        if (!this.commentsState[postId]) {
            this.commentsState[postId] = { offset: 0, hasMore: true, loading: false };
        }
        
        const state = this.commentsState[postId];
        
        if (state.loading) return;
        state.loading = true;
        
        if (!append) {
            container.innerHTML = '<div class="loading-comments">Cargando...</div>';
            state.offset = 0;
            if (viewBtn) viewBtn.style.display = 'none';
        }
        
        try {
            const limit = 5;
            const response = await this.apiRequest(`/api/publications/${postId}/comments?limit=${limit}&offset=${state.offset}`);
            
            if (response.success && response.comments) {
                const comments = response.comments;
                state.hasMore = comments.length === limit;
                
                if (append) {
                    const loadMoreBtn = container.querySelector('.load-more-comments-btn');
                    if (loadMoreBtn) loadMoreBtn.remove();
                    container.insertAdjacentHTML('beforeend', this.renderInlineComments(comments, postId));
                } else {
                    container.innerHTML = this.renderInlineComments(comments, postId);
                }
                
                state.offset += comments.length;
                
                if (state.hasMore) {
                    container.insertAdjacentHTML('beforeend', `
                        <button class="load-more-comments-btn" onclick="PublicationsManager.loadMoreComments(${postId})">
                            Ver mas comentarios
                        </button>
                    `);
                }
            } else if (!append) {
                container.innerHTML = '<p class="no-comments">No hay comentarios</p>';
            }
        } catch (error) {
            console.error('Error loading comments:', error);
            if (!append) {
                container.innerHTML = '<p class="no-comments">Error al cargar comentarios</p>';
            }
        } finally {
            state.loading = false;
        }
    },
    
    loadMoreComments(postId) {
        this.loadInlineComments(postId, true);
    },
    
    renderInlineComments(comments, postId) {
        if (!comments || comments.length === 0) {
            return '<p class="no-comments">No hay comentarios aún</p>';
        }
        
        const currentUserId = String(App?.user?.id || App?.user?.telegram_id || 0);
        
        return comments.map(comment => {
            const safeAvatarUrl = escapeAttribute(comment.avatar_url || this.DEFAULT_AVATAR);
            const username = escapeHtml(comment.first_name || comment.username || 'Usuario');
            const safeUsernameForJs = sanitizeForJs(comment.first_name || comment.username || 'Usuario');
            const timeAgo = this.formatTimeAgo(comment.created_at);
            const isOwner = String(comment.user_id) === currentUserId;
            const isEditable = isOwner && this.isCommentEditable(comment.created_at);
            const isEdited = comment.is_edited;
            
            return `
                <div class="inline-comment" data-comment-id="${parseInt(comment.id)}" data-post-id="${parseInt(postId)}">
                    <img src="${safeAvatarUrl}" class="inline-comment-avatar" alt="${username}" onerror="this.src='${this.DEFAULT_AVATAR}'">
                    <div class="inline-comment-body">
                        <div class="inline-comment-bubble">
                            <span class="inline-comment-name">${username}</span>
                            <span class="inline-comment-text" id="comment-text-${parseInt(comment.id)}">${escapeHtml(comment.content || '')}</span>
                            ${isEdited ? '<span class="comment-edited-label">(editado)</span>' : ''}
                        </div>
                        <div class="inline-comment-meta">
                            <span class="inline-comment-time">${timeAgo}</span>
                            <div class="comment-reaction-wrap" id="reaction-wrap-${parseInt(comment.id)}">
                                <button class="comment-reaction-btn" onclick="PublicationsManager.toggleCommentReactions(${parseInt(comment.id)})">
                                    ${this.getReactionEmoji(comment.user_reaction)} ${comment.reactions_count > 0 ? comment.reactions_count : ''}
                                </button>
                                <div class="comment-reactions-picker hidden" id="reactions-picker-${parseInt(comment.id)}">
                                    <button onclick="PublicationsManager.reactToComment(${parseInt(comment.id)}, 'like')">👍</button>
                                    <button onclick="PublicationsManager.reactToComment(${parseInt(comment.id)}, 'love')">❤️</button>
                                    <button onclick="PublicationsManager.reactToComment(${parseInt(comment.id)}, 'laugh')">😂</button>
                                    <button onclick="PublicationsManager.reactToComment(${parseInt(comment.id)}, 'wow')">😮</button>
                                    <button onclick="PublicationsManager.reactToComment(${parseInt(comment.id)}, 'sad')">😢</button>
                                    <button onclick="PublicationsManager.reactToComment(${parseInt(comment.id)}, 'angry')">😠</button>
                                </div>
                            </div>
                            <button class="inline-comment-reply" onclick="PublicationsManager.focusReply(${parseInt(postId)}, '${safeUsernameForJs}')">
                                Responder
                            </button>
                            ${isEditable ? `
                                <button class="inline-comment-edit" onclick="PublicationsManager.startEditComment(${parseInt(comment.id)}, ${parseInt(postId)})">
                                    Editar
                                </button>
                            ` : ''}
                        </div>
                        ${comment.replies && comment.replies.length > 0 ? `
                            <div class="inline-comment-replies">
                                ${comment.replies.map(reply => {
                                    const safeReplyAvatar = escapeAttribute(reply.avatar_url || this.DEFAULT_AVATAR);
                                    const replyName = escapeHtml(reply.first_name || reply.username || 'Usuario');
                                    const isReplyOwner = String(reply.user_id) === currentUserId;
                                    const isReplyEditable = isReplyOwner && this.isCommentEditable(reply.created_at);
                                    const isReplyEdited = reply.is_edited;
                                    return `
                                        <div class="inline-comment inline-reply" data-comment-id="${parseInt(reply.id)}" data-post-id="${parseInt(postId)}">
                                            <img src="${safeReplyAvatar}" class="inline-comment-avatar small" alt="${replyName}" onerror="this.src='${this.DEFAULT_AVATAR}'">
                                            <div class="inline-comment-body">
                                                <div class="inline-comment-bubble">
                                                    <span class="inline-comment-name">${replyName}</span>
                                                    <span class="inline-comment-text" id="comment-text-${parseInt(reply.id)}">${escapeHtml(reply.content || '')}</span>
                                                    ${isReplyEdited ? '<span class="comment-edited-label">(editado)</span>' : ''}
                                                </div>
                                                <div class="inline-comment-meta">
                                                    <span class="inline-comment-time">${this.formatTimeAgo(reply.created_at)}</span>
                                                    <div class="comment-reaction-wrap" id="reaction-wrap-${parseInt(reply.id)}">
                                                        <button class="comment-reaction-btn small" onclick="PublicationsManager.toggleCommentReactions(${parseInt(reply.id)})">
                                                            ${this.getReactionEmoji(reply.user_reaction)} ${reply.reactions_count > 0 ? reply.reactions_count : ''}
                                                        </button>
                                                        <div class="comment-reactions-picker hidden" id="reactions-picker-${parseInt(reply.id)}">
                                                            <button onclick="PublicationsManager.reactToComment(${parseInt(reply.id)}, 'like')">👍</button>
                                                            <button onclick="PublicationsManager.reactToComment(${parseInt(reply.id)}, 'love')">❤️</button>
                                                            <button onclick="PublicationsManager.reactToComment(${parseInt(reply.id)}, 'laugh')">😂</button>
                                                            <button onclick="PublicationsManager.reactToComment(${parseInt(reply.id)}, 'wow')">😮</button>
                                                            <button onclick="PublicationsManager.reactToComment(${parseInt(reply.id)}, 'sad')">😢</button>
                                                            <button onclick="PublicationsManager.reactToComment(${parseInt(reply.id)}, 'angry')">😠</button>
                                                        </div>
                                                    </div>
                                                    ${isReplyEditable ? `
                                                        <button class="inline-comment-edit" onclick="PublicationsManager.startEditComment(${parseInt(reply.id)}, ${parseInt(postId)})">
                                                            Editar
                                                        </button>
                                                    ` : ''}
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
    
    isCommentEditable(createdAt) {
        if (!createdAt) return false;
        const created = new Date(createdAt);
        const now = new Date();
        const diffMinutes = (now - created) / (1000 * 60);
        return diffMinutes <= 15;
    },
    
    async startEditComment(commentId, postId) {
        const textEl = document.getElementById(`comment-text-${commentId}`);
        if (!textEl) return;
        
        const currentText = textEl.textContent;
        const commentEl = textEl.closest('.inline-comment');
        const bubble = textEl.closest('.inline-comment-bubble');
        
        if (!bubble) return;
        
        bubble.innerHTML = `
            <textarea class="edit-comment-input" id="edit-comment-${commentId}" maxlength="2000">${escapeHtml(currentText)}</textarea>
            <div class="edit-comment-actions">
                <button class="edit-comment-cancel" onclick="PublicationsManager.cancelEditComment(${commentId}, ${postId})">Cancelar</button>
                <button class="edit-comment-save" onclick="PublicationsManager.saveEditComment(${commentId}, ${postId})">Guardar</button>
            </div>
        `;
        
        const textarea = document.getElementById(`edit-comment-${commentId}`);
        if (textarea) {
            textarea.focus();
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        }
    },
    
    cancelEditComment(commentId, postId) {
        this.loadInlineComments(postId);
    },
    
    async saveEditComment(commentId, postId) {
        const textarea = document.getElementById(`edit-comment-${commentId}`);
        if (!textarea) return;
        
        const newContent = textarea.value.trim();
        if (!newContent) {
            this.showToast('El comentario no puede estar vacío', 'error');
            return;
        }
        
        textarea.disabled = true;
        
        try {
            const response = await this.apiRequest(`/api/comments/${commentId}`, {
                method: 'PUT',
                body: JSON.stringify({ content: newContent })
            });
            
            if (response.success) {
                this.showToast('Comentario actualizado', 'success');
                this.loadInlineComments(postId);
            } else {
                this.showToast(response.error || 'Error al actualizar', 'error');
                textarea.disabled = false;
            }
        } catch (error) {
            console.error('Error editing comment:', error);
            this.showToast('Error al actualizar comentario', 'error');
            textarea.disabled = false;
        }
    },
    
    getReactionEmoji(reactionType) {
        const emojis = {
            'like': '👍',
            'love': '❤️',
            'laugh': '😂',
            'wow': '😮',
            'sad': '😢',
            'angry': '😠'
        };
        return emojis[reactionType] || '😊';
    },
    
    toggleCommentReactions(commentId) {
        document.querySelectorAll('.comment-reactions-picker').forEach(picker => {
            if (picker.id !== `reactions-picker-${commentId}`) {
                picker.classList.add('hidden');
            }
        });
        
        const picker = document.getElementById(`reactions-picker-${commentId}`);
        if (picker) {
            picker.classList.toggle('hidden');
        }
    },
    
    async reactToComment(commentId, reactionType) {
        const picker = document.getElementById(`reactions-picker-${commentId}`);
        if (picker) picker.classList.add('hidden');
        
        try {
            const response = await this.apiRequest(`/api/comments/${commentId}/react`, {
                method: 'POST',
                body: JSON.stringify({ reaction_type: reactionType })
            });
            
            if (response.success) {
                const btn = document.querySelector(`#reaction-wrap-${commentId} .comment-reaction-btn`);
                if (btn) {
                    const count = response.total > 0 ? response.total : '';
                    btn.innerHTML = `${this.getReactionEmoji(response.user_reaction)} ${count}`;
                }
                
                if (typeof App !== 'undefined' && App.tg && App.tg.HapticFeedback) {
                    App.tg.HapticFeedback.impactOccurred('light');
                }
            }
        } catch (error) {
            console.error('Error reacting to comment:', error);
            this.showToast('Error al reaccionar', 'error');
        }
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
                    this.updateCommentsCountUI(postId, post.comments_count);
                }
                
                this.loadInlineComments(postId);
                this.showToast('Comentario publicado', 'success');
                
                if (typeof App !== 'undefined' && App.tg && App.tg.HapticFeedback) {
                    App.tg.HapticFeedback.impactOccurred('light');
                }
            }
        } catch (error) {
            console.error('Comment error:', error);
            this.showToast('Error al comentar', 'error');
        } finally {
            input.disabled = false;
        }
    },
    
    updateCommentsCountUI(postId, newCount) {
        const section = document.getElementById(`comments-section-${postId}`);
        if (!section) return;
        
        let btn = section.querySelector(`[data-view-comments="${postId}"]`);
        
        if (newCount > 0) {
            const btnText = newCount > 2 
                ? `Ver los ${newCount} comentarios` 
                : newCount === 1 
                    ? 'Ver 1 comentario' 
                    : 'Ver comentarios';
            
            if (btn) {
                btn.textContent = btnText;
                btn.classList.add('count-updated');
                setTimeout(() => btn.classList.remove('count-updated'), 300);
            } else {
                const btnHtml = `
                    <button class="view-comments-btn count-updated" 
                            onclick="PublicationsManager.loadInlineComments(${postId})" 
                            data-view-comments="${postId}">
                        ${btnText}
                    </button>
                `;
                const list = section.querySelector('.inline-comments-list');
                if (list) {
                    list.insertAdjacentHTML('beforebegin', btnHtml);
                    setTimeout(() => {
                        const newBtn = section.querySelector(`[data-view-comments="${postId}"]`);
                        if (newBtn) newBtn.classList.remove('count-updated');
                    }, 300);
                }
            }
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
        const safeAvatarUrl = escapeAttribute(story.avatar_url || '/static/images/default-avatar.png');
        const safeMediaUrl = escapeAttribute(story.media_url || '');
        const safeUsername = escapeHtml(story.username || 'Usuario');
        const isOwnStory = story.user_id == (App?.user?.id || App?.user?.telegram_id);
        const timeRemaining = this.getStoryTimeRemaining(story.created_at);
        const viewsCount = story.views_count || 0;
        
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
                    <img src="${safeAvatarUrl}" 
                         class="story-viewer-avatar" alt="">
                    <div>
                        <div class="story-viewer-username">${safeUsername}</div>
                        <div class="story-viewer-time">
                            ${this.formatTimeAgo(story.created_at)}
                            ${timeRemaining ? ` • ${timeRemaining}` : ''}
                        </div>
                    </div>
                </div>
                <div class="story-header-actions">
                    ${isOwnStory ? `
                        <button class="story-action-btn story-viewers-btn" onclick="PublicationsManager.showStoryViewers(${story.id})" title="Visto por">
                            👁 ${viewsCount}
                        </button>
                        <button class="story-action-btn story-delete-btn" onclick="PublicationsManager.deleteStory(${story.id})" title="Eliminar">
                            🗑
                        </button>
                    ` : ''}
                    <button class="story-close-btn" onclick="PublicationsManager.closeStoryViewer()">×</button>
                </div>
            </div>
            <div class="story-content">
                ${story.media_type === 'video' 
                    ? `<video src="${safeMediaUrl}" autoplay playsinline></video>`
                    : `<img src="${safeMediaUrl}" alt="Story">`
                }
            </div>
            <div class="story-nav-area prev" onclick="PublicationsManager.prevStory()"></div>
            <div class="story-nav-area next" onclick="PublicationsManager.nextStory()"></div>
            ${!isOwnStory ? `
                <div class="story-reactions-bar">
                    ${['❤️', '🔥', '😂', '😮', '😢', '👏'].map(emoji => 
                        `<button class="story-react-btn" onclick="PublicationsManager.reactToStory(${story.id}, '${emoji}')">${emoji}</button>`
                    ).join('')}
                </div>
            ` : ''}
        `;
        
        document.body.appendChild(viewer);
        
        this._currentStories = stories;
        this._currentStoryIndex = index;
        
        this.markStoryViewed(story.id);
        this.startStoryProgress(stories[index]);
    },

    getStoryTimeRemaining(createdAt) {
        if (!createdAt) return '';
        const created = new Date(createdAt);
        const expiresAt = new Date(created.getTime() + 24 * 60 * 60 * 1000);
        const now = new Date();
        const remaining = expiresAt - now;
        
        if (remaining <= 0) return '';
        
        const hours = Math.floor(remaining / (60 * 60 * 1000));
        const minutes = Math.floor((remaining % (60 * 60 * 1000)) / (60 * 1000));
        
        if (hours > 0) {
            return `${hours}h restantes`;
        }
        return `${minutes}m restantes`;
    },

    async deleteStory(storyId) {
        if (!confirm('¿Eliminar esta historia?')) return;
        
        try {
            const response = await this.apiRequest(`/api/stories/${storyId}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                this.showToast('Historia eliminada', 'success');
                this.closeStoryViewer();
                this.loadStories();
            } else {
                this.showToast(response.error || 'Error al eliminar', 'error');
            }
        } catch (error) {
            console.error('Error deleting story:', error);
            this.showToast('Error al eliminar historia', 'error');
        }
    },

    async showStoryViewers(storyId) {
        if (this._storyTimeout) clearTimeout(this._storyTimeout);
        
        try {
            const response = await this.apiRequest(`/api/stories/${storyId}/viewers`);
            
            if (response.success) {
                const viewers = response.viewers || [];
                const viewersList = viewers.length > 0 
                    ? viewers.map(v => `
                        <div class="story-viewer-item">
                            <img src="${escapeAttribute(v.avatar_url || this.DEFAULT_AVATAR)}" class="story-viewer-item-avatar">
                            <span>${escapeHtml(v.username || v.first_name || 'Usuario')}</span>
                        </div>
                    `).join('')
                    : '<p class="story-viewers-empty">Nadie ha visto esta historia aun</p>';
                
                const modal = document.createElement('div');
                modal.className = 'story-viewers-modal';
                modal.innerHTML = `
                    <div class="story-viewers-content">
                        <div class="story-viewers-header">
                            <h3>Visto por ${viewers.length}</h3>
                            <button onclick="this.closest('.story-viewers-modal').remove(); PublicationsManager.startStoryProgress(PublicationsManager._currentStories[PublicationsManager._currentStoryIndex])">×</button>
                        </div>
                        <div class="story-viewers-list">
                            ${viewersList}
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            }
        } catch (error) {
            console.error('Error loading story viewers:', error);
        }
    },

    async reactToStory(storyId, emoji) {
        try {
            const response = await this.apiRequest(`/api/stories/${storyId}/react`, {
                method: 'POST',
                body: JSON.stringify({ reaction: emoji })
            });
            
            if (response.success) {
                this.showToast('Reaccion enviada', 'success');
            }
        } catch (error) {
            console.error('Error reacting to story:', error);
        }
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
        if (typeof App !== 'undefined' && App.showScreen) {
            App.showScreen('explore-screen');
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.value = `#${tag}`;
                App.performSearch(`#${tag}`);
            }
        } else {
            window.location.href = `/explore?hashtag=${tag}`;
        }
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
    
    async apiRequest(url, options = {}, cancelKey = null) {
        const headers = {
            'Content-Type': 'application/json',
            ...this.getAuthHeaders(),
            ...options.headers
        };
        
        if (cancelKey && typeof RequestManager !== 'undefined') {
            const result = await RequestManager.fetch(url, { ...options, headers, cancelKey });
            return result.json();
        }
        
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
    openCreateModal: (type) => PublicationsManager.showCreateModal(type),
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
