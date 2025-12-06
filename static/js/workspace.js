const Workspace = {
    state: {
        currentFile: null,
        files: [],
        messages: [],
        mentalState: 'LISTO',
        isProcessing: false
    },

    init() {
        this.setupEventListeners();
        this.loadFiles();
        this.updateTime();
        this.setupResizers();
        setInterval(() => this.updateTime(), 1000);
    },

    setupEventListeners() {
        document.getElementById('send-btn').addEventListener('click', () => this.sendMessage());
        document.getElementById('chat-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        document.getElementById('chat-input').addEventListener('input', (e) => {
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
        });

        document.getElementById('clear-chat').addEventListener('click', () => this.clearChat());
        document.getElementById('refresh-files').addEventListener('click', () => this.loadFiles());
        document.getElementById('refresh-preview').addEventListener('click', () => this.refreshPreview());
        document.getElementById('open-external').addEventListener('click', () => this.openExternal());

        document.getElementById('preview-url').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.refreshPreview();
            }
        });

        document.getElementById('files-search').addEventListener('input', (e) => {
            this.filterFiles(e.target.value);
        });

        document.getElementById('close-file-modal').addEventListener('click', () => {
            document.getElementById('file-modal').classList.add('hidden');
        });

        document.getElementById('save-file-btn').addEventListener('click', () => this.saveFile());

        document.getElementById('new-file-btn').addEventListener('click', () => this.createNewFile());
        document.getElementById('new-folder-btn').addEventListener('click', () => this.createNewFolder());
    },

    setupResizers() {
        const resizerLeft = document.getElementById('resizer-left');
        const resizerRight = document.getElementById('resizer-right');
        const panelLeft = document.getElementById('panel-chat');
        const panelRight = document.getElementById('panel-files');

        this.makeResizable(resizerLeft, panelLeft, 'left');
        this.makeResizable(resizerRight, panelRight, 'right');
    },

    makeResizable(resizer, panel, direction) {
        let startX, startWidth;

        resizer.addEventListener('mousedown', (e) => {
            startX = e.clientX;
            startWidth = panel.offsetWidth;
            resizer.classList.add('active');

            document.addEventListener('mousemove', resize);
            document.addEventListener('mouseup', stopResize);
        });

        const resize = (e) => {
            const diff = direction === 'left' ? e.clientX - startX : startX - e.clientX;
            const newWidth = startWidth + diff;
            const minWidth = parseInt(getComputedStyle(panel).minWidth) || 200;
            const maxWidth = parseInt(getComputedStyle(panel).maxWidth) || 500;

            if (newWidth >= minWidth && newWidth <= maxWidth) {
                panel.style.width = newWidth + 'px';
            }
        };

        const stopResize = () => {
            resizer.classList.remove('active');
            document.removeEventListener('mousemove', resize);
            document.removeEventListener('mouseup', stopResize);
        };
    },

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message || this.state.isProcessing) return;

        this.addMessage(message, 'user');
        input.value = '';
        input.style.height = 'auto';

        this.setMentalState('PROCESANDO', '🤔');
        this.state.isProcessing = true;

        try {
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            if (data.response) {
                this.addMessage(data.response, 'assistant');
            } else if (data.error) {
                this.addMessage('Error: ' + data.error, 'assistant');
            }
        } catch (error) {
            this.addMessage('Error de conexion. Intenta de nuevo.', 'assistant');
        }

        this.setMentalState('LISTO', '🧘');
        this.state.isProcessing = false;
    },

    addMessage(text, type) {
        const container = document.getElementById('chat-messages');
        const now = new Date();
        const time = now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });

        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;

        if (type === 'assistant') {
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <span class="avatar-icon">🤖</span>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-author">BUNK3R</span>
                        <span class="message-time">${time}</span>
                    </div>
                    <div class="message-text">${this.formatMessage(text)}</div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <span class="avatar-icon">👤</span>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-author">Tu</span>
                        <span class="message-time">${time}</span>
                    </div>
                    <div class="message-text">${this.escapeHtml(text)}</div>
                </div>
            `;
        }

        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    },

    formatMessage(text) {
        let formatted = this.escapeHtml(text);
        formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/\n/g, '<br>');
        return formatted;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    clearChat() {
        const container = document.getElementById('chat-messages');
        container.innerHTML = `
            <div class="message message-assistant">
                <div class="message-avatar">
                    <span class="avatar-icon">🤖</span>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-author">BUNK3R</span>
                        <span class="message-time">Ahora</span>
                    </div>
                    <div class="message-text">
                        <p>Chat limpiado. ¿En que puedo ayudarte?</p>
                    </div>
                </div>
            </div>
        `;
    },

    async loadFiles() {
        const tree = document.getElementById('files-tree');
        tree.innerHTML = '<div class="tree-loading"><div class="spinner"></div><span>Cargando archivos...</span></div>';

        try {
            const response = await fetch('/api/files/tree');
            const data = await response.json();

            if (data.tree) {
                this.state.files = data.tree;
                this.renderFileTree(data.tree);
                document.getElementById('files-count').textContent = `${data.total_files || 0} archivos`;
            }
        } catch (error) {
            tree.innerHTML = '<div class="tree-loading"><span>Error cargando archivos</span></div>';
        }
    },

    renderFileTree(items, container = null) {
        if (!container) {
            container = document.getElementById('files-tree');
            container.innerHTML = '';
        }

        items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = `tree-item tree-item-${item.type}`;
            itemDiv.dataset.path = item.path;

            const icon = item.type === 'folder' ? '📁' : this.getFileIcon(item.name);

            if (item.type === 'folder') {
                itemDiv.innerHTML = `
                    <span class="tree-toggle">▶</span>
                    <span class="tree-item-icon">${icon}</span>
                    <span class="tree-item-name">${item.name}</span>
                `;

                itemDiv.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleFolder(itemDiv, item);
                });
            } else {
                itemDiv.innerHTML = `
                    <span class="tree-item-icon">${icon}</span>
                    <span class="tree-item-name">${item.name}</span>
                `;

                itemDiv.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.openFile(item);
                });
            }

            container.appendChild(itemDiv);

            if (item.type === 'folder' && item.children) {
                const childrenDiv = document.createElement('div');
                childrenDiv.className = 'tree-children collapsed';
                this.renderFileTree(item.children, childrenDiv);
                container.appendChild(childrenDiv);
            }
        });
    },

    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const icons = {
            'py': '🐍',
            'js': '📜',
            'ts': '📘',
            'html': '🌐',
            'css': '🎨',
            'json': '📋',
            'md': '📝',
            'txt': '📄',
            'sql': '🗃️',
            'png': '🖼️',
            'jpg': '🖼️',
            'gif': '🖼️',
            'svg': '🎨'
        };
        return icons[ext] || '📄';
    },

    toggleFolder(element, item) {
        const toggle = element.querySelector('.tree-toggle');
        const children = element.nextElementSibling;

        if (children && children.classList.contains('tree-children')) {
            children.classList.toggle('collapsed');
            toggle.classList.toggle('expanded');
        }
    },

    async openFile(item) {
        document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('selected'));
        document.querySelector(`[data-path="${item.path}"]`)?.classList.add('selected');

        try {
            const response = await fetch(`/api/files/content?path=${encodeURIComponent(item.path)}`);
            const data = await response.json();

            if (data.content !== undefined) {
                this.state.currentFile = item.path;
                document.getElementById('file-modal-title').textContent = item.name;
                document.getElementById('editor-file-path').textContent = item.path;
                document.getElementById('file-content').value = data.content;
                document.getElementById('file-modal').classList.remove('hidden');
            }
        } catch (error) {
            console.error('Error opening file:', error);
        }
    },

    async saveFile() {
        if (!this.state.currentFile) return;

        const content = document.getElementById('file-content').value;

        try {
            const response = await fetch('/api/files/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    path: this.state.currentFile,
                    content: content
                })
            });

            const data = await response.json();

            if (data.success) {
                this.addMessage(`Archivo guardado: ${this.state.currentFile}`, 'assistant');
                document.getElementById('file-modal').classList.add('hidden');
            }
        } catch (error) {
            console.error('Error saving file:', error);
        }
    },

    filterFiles(query) {
        const items = document.querySelectorAll('.tree-item');
        query = query.toLowerCase();

        items.forEach(item => {
            const name = item.querySelector('.tree-item-name').textContent.toLowerCase();
            const matches = name.includes(query);
            item.style.display = matches || !query ? '' : 'none';
        });
    },

    refreshPreview() {
        const url = document.getElementById('preview-url').value || '/';
        const iframe = document.getElementById('preview-iframe');
        const placeholder = document.getElementById('preview-placeholder');

        placeholder.classList.add('hidden');
        iframe.src = url;
    },

    openExternal() {
        const url = document.getElementById('preview-url').value || '/';
        window.open(url, '_blank');
    },

    createNewFile() {
        const name = prompt('Nombre del archivo:');
        if (name) {
            this.addMessage(`Creando archivo: ${name}`, 'assistant');
        }
    },

    createNewFolder() {
        const name = prompt('Nombre de la carpeta:');
        if (name) {
            this.addMessage(`Creando carpeta: ${name}`, 'assistant');
        }
    },

    setMentalState(state, emoji) {
        this.state.mentalState = state;
        document.querySelector('.mental-state .state-emoji').textContent = emoji;
        document.querySelector('.mental-state .state-text').textContent = state;

        const indicator = document.getElementById('status-indicator');
        indicator.className = 'status-indicator ' + (state === 'PROCESANDO' ? 'working' : 'online');
    },

    updateTime() {
        const now = new Date();
        document.getElementById('current-time').textContent = now.toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
};

document.addEventListener('DOMContentLoaded', () => Workspace.init());
