const CodeBuilder = {
    editor: null,
    files: {},
    activeFile: null,
    openTabs: [],
    isAIPanelOpen: false,
    isGenerating: false,
    projectId: null,
    
    defaultFiles: {
        'index.html': `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mi Proyecto</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <h1>Hola Mundo!</h1>
    <p>Edita este archivo o pidele a la IA que cree algo para ti.</p>
    
    <script src="script.js"></script>
</body>
</html>`,
        'styles.css': `* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    text-align: center;
    padding: 20px;
}

h1 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

p {
    font-size: 1.1rem;
    opacity: 0.9;
}`,
        'script.js': `// Tu JavaScript aqui
console.log('Proyecto iniciado!');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado');
});`
    },
    
    async init() {
        await this.loadMonacoEditor();
        this.loadProject();
        this.renderFileList();
        this.bindEvents();
        this.openFile('index.html');
        this.updatePreview();
    },
    
    async loadMonacoEditor() {
        return new Promise((resolve) => {
            require.config({ 
                paths: { 
                    'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' 
                }
            });
            
            require(['vs/editor/editor.main'], () => {
                monaco.editor.defineTheme('bunkr-dark', {
                    base: 'vs-dark',
                    inherit: true,
                    rules: [
                        { token: 'comment', foreground: '5E6673', fontStyle: 'italic' },
                        { token: 'keyword', foreground: 'F0B90B' },
                        { token: 'string', foreground: '0ECB81' },
                        { token: 'number', foreground: 'FCD535' },
                        { token: 'tag', foreground: 'F6465D' },
                        { token: 'attribute.name', foreground: 'F0B90B' },
                        { token: 'attribute.value', foreground: '0ECB81' },
                    ],
                    colors: {
                        'editor.background': '#0B0E11',
                        'editor.foreground': '#EAECEF',
                        'editorLineNumber.foreground': '#5E6673',
                        'editorLineNumber.activeForeground': '#F0B90B',
                        'editor.selectionBackground': '#2B3139',
                        'editor.lineHighlightBackground': '#12161C',
                        'editorCursor.foreground': '#F0B90B',
                        'editorIndentGuide.background': '#2B3139',
                    }
                });
                
                this.editor = monaco.editor.create(document.getElementById('editor-container'), {
                    value: '',
                    language: 'html',
                    theme: 'bunkr-dark',
                    fontSize: 13,
                    fontFamily: "'Fira Code', 'Monaco', 'Menlo', monospace",
                    minimap: { enabled: false },
                    lineNumbers: 'on',
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    tabSize: 2,
                    wordWrap: 'on',
                    renderWhitespace: 'selection',
                    bracketPairColorization: { enabled: true },
                    padding: { top: 10 }
                });
                
                this.editor.onDidChangeModelContent(() => {
                    if (this.activeFile) {
                        this.files[this.activeFile] = this.editor.getValue();
                        this.updatePreview();
                    }
                });
                
                resolve();
            });
        });
    },
    
    loadProject() {
        const savedProject = localStorage.getItem('bunkr_code_project');
        if (savedProject) {
            try {
                const data = JSON.parse(savedProject);
                this.files = data.files || this.defaultFiles;
                this.projectId = data.projectId;
                document.getElementById('project-name').value = data.name || 'Mi Proyecto';
            } catch (e) {
                this.files = { ...this.defaultFiles };
            }
        } else {
            this.files = { ...this.defaultFiles };
        }
    },
    
    saveProject() {
        const data = {
            projectId: this.projectId || Date.now().toString(),
            name: document.getElementById('project-name').value,
            files: this.files,
            savedAt: new Date().toISOString()
        };
        localStorage.setItem('bunkr_code_project', JSON.stringify(data));
        this.showStatus('Proyecto guardado', 'success');
    },
    
    renderFileList() {
        const list = document.getElementById('file-list');
        list.innerHTML = '';
        
        Object.keys(this.files).forEach(filename => {
            const ext = filename.split('.').pop();
            const item = document.createElement('div');
            item.className = `file-item ${filename === this.activeFile ? 'active' : ''}`;
            item.innerHTML = `
                <span class="file-icon ${ext}">${this.getFileIcon(ext)}</span>
                <span class="file-name">${filename}</span>
            `;
            item.onclick = () => this.openFile(filename);
            list.appendChild(item);
        });
    },
    
    getFileIcon(ext) {
        const icons = {
            html: '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M1.5 0h21l-1.91 21.563L11.977 24l-8.564-2.438L1.5 0zm7.031 9.75l-.232-2.718 10.059.003.23-2.622L5.412 4.41l.698 8.01h9.126l-.326 3.426-2.91.804-2.955-.81-.188-2.11H6.248l.33 4.171L12 19.351l5.379-1.443.744-8.157H8.531z"/></svg>',
            css: '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M1.5 0h21l-1.91 21.563L11.977 24l-8.565-2.438L1.5 0zm17.09 4.413L5.41 4.41l.213 2.622 10.125.002-.255 2.716h-6.64l.24 2.573h6.182l-.366 3.523-2.91.804-2.956-.81-.188-2.11h-2.61l.29 3.855L12 19.288l5.373-1.53L18.59 4.414z"/></svg>',
            js: '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M0 0h24v24H0V0zm22.034 18.276c-.175-1.095-.888-2.015-3.003-2.873-.736-.345-1.554-.585-1.797-1.14-.091-.33-.105-.51-.046-.705.15-.646.915-.84 1.515-.66.39.12.75.42.976.9 1.034-.676 1.034-.676 1.755-1.125-.27-.42-.404-.601-.586-.78-.63-.705-1.469-1.065-2.834-1.034l-.705.089c-.676.165-1.32.525-1.71 1.005-1.14 1.291-.811 3.541.569 4.471 1.365 1.02 3.361 1.244 3.616 2.205.24 1.17-.87 1.545-1.966 1.41-.811-.18-1.26-.586-1.755-1.336l-1.83 1.051c.21.48.45.689.81 1.109 1.74 1.756 6.09 1.666 6.871-1.004.029-.09.24-.705.074-1.65l.046.067zm-8.983-7.245h-2.248c0 1.938-.009 3.864-.009 5.805 0 1.232.063 2.363-.138 2.711-.33.689-1.18.601-1.566.48-.396-.196-.597-.466-.83-.855-.063-.105-.11-.196-.127-.196l-1.825 1.125c.305.63.75 1.172 1.324 1.517.855.51 2.004.675 3.207.405.783-.226 1.458-.691 1.811-1.411.51-.93.402-2.07.397-3.346.012-2.054 0-4.109 0-6.179l.004-.056z"/></svg>'
        };
        return icons[ext] || '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>';
    },
    
    getLanguage(filename) {
        const ext = filename.split('.').pop();
        const langs = {
            html: 'html',
            css: 'css',
            js: 'javascript',
            json: 'json'
        };
        return langs[ext] || 'plaintext';
    },
    
    openFile(filename) {
        if (!this.files[filename]) return;
        
        this.activeFile = filename;
        
        if (!this.openTabs.includes(filename)) {
            this.openTabs.push(filename);
        }
        
        this.renderTabs();
        this.renderFileList();
        
        const model = monaco.editor.createModel(
            this.files[filename],
            this.getLanguage(filename)
        );
        this.editor.setModel(model);
    },
    
    renderTabs() {
        const tabsContainer = document.getElementById('editor-tabs');
        tabsContainer.innerHTML = '';
        
        this.openTabs.forEach(filename => {
            const ext = filename.split('.').pop();
            const tab = document.createElement('div');
            tab.className = `editor-tab ${filename === this.activeFile ? 'active' : ''}`;
            tab.innerHTML = `
                <span class="file-icon ${ext}">${this.getFileIcon(ext)}</span>
                <span>${filename}</span>
                <span class="close-tab" onclick="event.stopPropagation(); CodeBuilder.closeTab('${filename}')">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </span>
            `;
            tab.onclick = () => this.openFile(filename);
            tabsContainer.appendChild(tab);
        });
    },
    
    closeTab(filename) {
        const idx = this.openTabs.indexOf(filename);
        if (idx > -1) {
            this.openTabs.splice(idx, 1);
            if (this.activeFile === filename && this.openTabs.length > 0) {
                this.openFile(this.openTabs[Math.max(0, idx - 1)]);
            }
            this.renderTabs();
        }
    },
    
    createFile(filename) {
        if (!filename) return;
        if (this.files[filename]) {
            this.showStatus('El archivo ya existe', 'error');
            return;
        }
        
        const ext = filename.split('.').pop();
        const templates = {
            html: '<!DOCTYPE html>\n<html lang="es">\n<head>\n    <meta charset="UTF-8">\n    <title>Nuevo</title>\n</head>\n<body>\n    \n</body>\n</html>',
            css: '/* Estilos */\n',
            js: '// JavaScript\n'
        };
        
        this.files[filename] = templates[ext] || '';
        this.renderFileList();
        this.openFile(filename);
        this.showStatus(`Archivo ${filename} creado`, 'success');
    },
    
    deleteFile(filename) {
        if (Object.keys(this.files).length <= 1) {
            this.showStatus('Debe haber al menos un archivo', 'error');
            return;
        }
        
        delete this.files[filename];
        this.closeTab(filename);
        this.renderFileList();
        
        if (this.activeFile === filename) {
            const remaining = Object.keys(this.files)[0];
            if (remaining) this.openFile(remaining);
        }
    },
    
    updatePreview() {
        const iframe = document.getElementById('preview-frame');
        const html = this.files['index.html'] || '';
        const css = this.files['styles.css'] || '';
        const js = this.files['script.js'] || '';
        
        let processedHtml = html;
        
        if (processedHtml.includes('<link rel="stylesheet" href="styles.css">')) {
            processedHtml = processedHtml.replace(
                '<link rel="stylesheet" href="styles.css">',
                `<style>${css}</style>`
            );
        } else if (!processedHtml.includes('<style>') && css) {
            processedHtml = processedHtml.replace('</head>', `<style>${css}</style></head>`);
        }
        
        if (processedHtml.includes('<script src="script.js">')) {
            processedHtml = processedHtml.replace(
                '<script src="script.js"></script>',
                `<script>${js}<\/script>`
            );
        } else if (!processedHtml.includes('<script>') && js) {
            processedHtml = processedHtml.replace('</body>', `<script>${js}<\/script></body>`);
        }
        
        iframe.srcdoc = processedHtml;
    },
    
    bindEvents() {
        document.getElementById('ai-assist-btn').onclick = () => this.toggleAIPanel();
        document.getElementById('close-ai-panel').onclick = () => this.toggleAIPanel();
        document.getElementById('run-btn').onclick = () => this.updatePreview();
        document.getElementById('save-btn').onclick = () => this.saveProject();
        document.getElementById('refresh-preview').onclick = () => this.updatePreview();
        document.getElementById('add-file-btn').onclick = () => this.showNewFileModal();
        
        document.getElementById('ai-builder-send').onclick = () => this.sendAIMessage();
        document.getElementById('ai-builder-input').onkeydown = (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendAIMessage();
            }
        };
        
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.onclick = () => {
                document.getElementById('ai-builder-input').value = btn.dataset.prompt;
                this.sendAIMessage();
            };
        });
        
        document.querySelectorAll('.file-type-btn').forEach(btn => {
            btn.onclick = () => {
                document.querySelectorAll('.file-type-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const input = document.getElementById('new-file-name');
                const name = input.value.split('.')[0] || 'nuevo';
                input.value = `${name}.${btn.dataset.ext}`;
            };
        });
        
        document.getElementById('cancel-new-file').onclick = () => this.hideNewFileModal();
        document.getElementById('create-file').onclick = () => {
            const name = document.getElementById('new-file-name').value.trim();
            if (name) {
                this.createFile(name);
                this.hideNewFileModal();
            }
        };
        
        document.getElementById('new-file-modal').onclick = (e) => {
            if (e.target.id === 'new-file-modal') this.hideNewFileModal();
        };
    },
    
    showNewFileModal() {
        document.getElementById('new-file-modal').classList.remove('hidden');
        document.getElementById('new-file-name').value = 'nuevo.html';
        document.getElementById('new-file-name').focus();
    },
    
    hideNewFileModal() {
        document.getElementById('new-file-modal').classList.add('hidden');
    },
    
    toggleAIPanel() {
        this.isAIPanelOpen = !this.isAIPanelOpen;
        document.getElementById('ai-panel').classList.toggle('hidden', !this.isAIPanelOpen);
        if (this.isAIPanelOpen) {
            document.getElementById('ai-builder-input').focus();
        }
    },
    
    async sendAIMessage() {
        const input = document.getElementById('ai-builder-input');
        const message = input.value.trim();
        
        if (!message || this.isGenerating) return;
        
        this.isGenerating = true;
        input.value = '';
        
        this.appendAIMessage('user', message);
        this.showTypingIndicator();
        this.setStatus('Generando codigo...', 'loading');
        
        try {
            const response = await fetch('/api/ai/code-builder', {
                method: 'POST',
                headers: this.getApiHeaders(),
                body: JSON.stringify({
                    message: message,
                    currentFiles: this.files,
                    projectName: document.getElementById('project-name').value
                })
            });
            
            const data = await response.json();
            this.hideTypingIndicator();
            
            if (data.success) {
                if (data.files) {
                    this.processAIFiles(data.files);
                }
                
                if (data.response) {
                    this.appendAIMessage('assistant', data.response);
                }
                
                this.setStatus(`Generado con ${data.provider || 'AI'}`, 'success');
            } else {
                this.appendAIMessage('assistant', data.error || 'Error al generar codigo. Intenta de nuevo.');
                this.setStatus('Error', 'error');
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.appendAIMessage('assistant', 'Error de conexion. Verifica tu internet.');
            this.setStatus('Error de conexion', 'error');
            console.error('AI Builder error:', error);
        }
        
        this.isGenerating = false;
    },
    
    processAIFiles(files) {
        let firstNewFile = null;
        
        for (const [filename, content] of Object.entries(files)) {
            const isNew = !this.files[filename];
            this.files[filename] = content;
            
            if (isNew && !firstNewFile) {
                firstNewFile = filename;
            }
            
            this.appendCodeAction(isNew ? 'create' : 'update', filename);
        }
        
        this.renderFileList();
        
        if (firstNewFile) {
            this.openFile(firstNewFile);
        } else if (this.activeFile && files[this.activeFile]) {
            this.openFile(this.activeFile);
        }
        
        this.updatePreview();
        this.saveProject();
    },
    
    appendAIMessage(role, content) {
        const container = document.getElementById('ai-builder-messages');
        const welcome = container.querySelector('.ai-welcome');
        if (welcome) welcome.style.display = 'none';
        
        const msg = document.createElement('div');
        msg.className = `ai-message ${role}`;
        
        if (role === 'assistant') {
            msg.innerHTML = `
                <div class="avatar">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="16" height="16">
                        <path d="M12 2a4 4 0 0 1 4 4v1h1a3 3 0 0 1 3 3v2a3 3 0 0 1-3 3h-1v1a4 4 0 0 1-8 0v-1H7a3 3 0 0 1-3-3v-2a3 3 0 0 1 3-3h1V6a4 4 0 0 1 4-4z"/>
                    </svg>
                </div>
                <div class="bubble">${this.formatMessage(content)}</div>
            `;
        } else {
            msg.innerHTML = `<div class="bubble">${this.escapeHtml(content)}</div>`;
        }
        
        container.appendChild(msg);
        container.scrollTop = container.scrollHeight;
    },
    
    appendCodeAction(action, filename) {
        const container = document.getElementById('ai-builder-messages');
        const actionDiv = document.createElement('div');
        actionDiv.className = 'code-action-indicator';
        
        const icon = action === 'create' ? 
            '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>' :
            '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>';
        
        actionDiv.innerHTML = `
            <div class="action-title">${icon} ${action === 'create' ? 'Archivo creado' : 'Archivo actualizado'}</div>
            <div class="action-file">${filename}</div>
        `;
        
        container.appendChild(actionDiv);
        container.scrollTop = container.scrollHeight;
    },
    
    showTypingIndicator() {
        const container = document.getElementById('ai-builder-messages');
        const typing = document.createElement('div');
        typing.id = 'ai-typing';
        typing.className = 'ai-message assistant';
        typing.innerHTML = `
            <div class="avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="16" height="16">
                    <path d="M12 2a4 4 0 0 1 4 4v1h1a3 3 0 0 1 3 3v2a3 3 0 0 1-3 3h-1v1a4 4 0 0 1-8 0v-1H7a3 3 0 0 1-3-3v-2a3 3 0 0 1 3-3h1V6a4 4 0 0 1 4-4z"/>
                </svg>
            </div>
            <div class="bubble">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        container.appendChild(typing);
        container.scrollTop = container.scrollHeight;
    },
    
    hideTypingIndicator() {
        const typing = document.getElementById('ai-typing');
        if (typing) typing.remove();
    },
    
    setStatus(text, type = '') {
        const status = document.getElementById('ai-status');
        status.textContent = text;
        status.className = 'ai-status ' + type;
    },
    
    showStatus(message, type = 'info') {
        console.log(`[${type}] ${message}`);
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
    
    getApiHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        if (typeof App !== 'undefined') {
            if (App.isDemoMode) {
                headers['X-Demo-Mode'] = 'true';
                if (App.demoSessionToken) {
                    headers['X-Demo-Session'] = App.demoSessionToken;
                }
            } else if (App.initData) {
                headers['X-Telegram-Init-Data'] = App.initData;
            }
        }
        return headers;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    CodeBuilder.init();
});
