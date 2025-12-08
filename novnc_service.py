"""
noVNC Service - Interactive browser sessions using VNC streaming.
Provides full browser interactivity through WebSocket-based VNC.
"""
import subprocess
import time
import os
import shutil
from threading import Thread, Lock
import uuid
import logging

logger = logging.getLogger(__name__)

def check_dependencies():
    """Verify all required binaries are available."""
    required = ['Xvfb', 'x11vnc', 'chromium', 'websockify', 'xdotool']
    missing = []
    for cmd in required:
        if not shutil.which(cmd):
            alt = shutil.which(cmd + '-browser') if cmd == 'chromium' else None
            if not alt:
                missing.append(cmd)
    if missing:
        logger.warning(f"Missing dependencies for noVNC: {missing}")
        return False
    return True


class NoVNCSession:
    """Manages a single interactive browser session with VNC streaming."""
    
    def __init__(self, session_id, display_num, vnc_port, ws_port):
        self.session_id = session_id
        self.display = f":{display_num}"
        self.vnc_port = vnc_port
        self.ws_port = ws_port
        self.processes = []
        self.current_url = None
        self.active = False
        self.created_at = time.time()
        self.error = None
        
    def start(self, url="https://www.google.com"):
        """Start the VNC session with browser."""
        if not check_dependencies():
            self.error = "Faltan dependencias del sistema"
            return False
            
        try:
            self.current_url = url
            
            if not self._start_xvfb():
                self.error = "Error al iniciar display virtual"
                self.stop()
                return False
            time.sleep(1.5)
            
            if not self._start_vnc_server():
                self.error = "Error al iniciar servidor VNC"
                self.stop()
                return False
            time.sleep(1)
            
            if not self._start_browser(url):
                self.error = "Error al iniciar navegador"
                self.stop()
                return False
            time.sleep(1.5)
            
            if not self._start_websockify():
                self.error = "Error al iniciar WebSocket"
                self.stop()
                return False
                
            self.active = True
            logger.info(f"noVNC session {self.session_id} started on ws_port {self.ws_port}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting noVNC session: {e}")
            self.error = str(e)
            self.stop()
            return False
    
    def _start_xvfb(self):
        """Start virtual framebuffer."""
        try:
            cmd = [
                'Xvfb', self.display,
                '-screen', '0', '400x850x24',
                '-ac'
            ]
            proc = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            time.sleep(0.5)
            if proc.poll() is not None:
                stderr = proc.stderr.read().decode() if proc.stderr else ""
                logger.error(f"Xvfb failed: {stderr}")
                return False
            self.processes.append(proc)
            return True
        except Exception as e:
            logger.error(f"Xvfb start error: {e}")
            return False
        
    def _start_vnc_server(self):
        """Start x11vnc pointing to virtual display."""
        try:
            cmd = [
                'x11vnc',
                '-display', self.display,
                '-rfbport', str(self.vnc_port),
                '-forever',
                '-shared',
                '-nopw',
                '-noxdamage',
                '-cursor', 'arrow',
                '-repeat',
                '-localhost'
            ]
            proc = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            time.sleep(0.5)
            if proc.poll() is not None:
                stderr = proc.stderr.read().decode() if proc.stderr else ""
                logger.error(f"x11vnc failed: {stderr}")
                return False
            self.processes.append(proc)
            return True
        except Exception as e:
            logger.error(f"x11vnc start error: {e}")
            return False
        
    def _start_browser(self, url):
        """Launch Chromium on virtual display."""
        try:
            env = os.environ.copy()
            env['DISPLAY'] = self.display
            
            chromium_path = shutil.which('chromium') or shutil.which('chromium-browser')
            if not chromium_path:
                logger.error("Chromium not found")
                return False
            
            cmd = [
                chromium_path,
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--window-size=400,850',
                '--window-position=0,0',
                '--kiosk',
                '--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                '--force-device-scale-factor=1',
                url
            ]
            proc = subprocess.Popen(
                cmd, 
                env=env, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            self.processes.append(proc)
            return True
        except Exception as e:
            logger.error(f"Browser start error: {e}")
            return False
        
    def _start_websockify(self):
        """Start websockify proxy for noVNC with token authentication."""
        try:
            novnc_path = os.path.join(os.getcwd(), 'static', 'novnc')
            
            token_file = f'/tmp/vnc_token_{self.session_id}.txt'
            self.token = str(uuid.uuid4())[:16]
            with open(token_file, 'w') as f:
                f.write(f'{self.token}: localhost:{self.vnc_port}')
            self._token_file = token_file
            
            cmd = [
                'websockify',
                '--web', novnc_path,
                '--token-plugin', 'TokenFile',
                '--token-source', token_file,
                f'0.0.0.0:{self.ws_port}'
            ]
            proc = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            time.sleep(0.5)
            if proc.poll() is not None:
                stderr = proc.stderr.read().decode() if proc.stderr else ""
                logger.error(f"websockify failed: {stderr}")
                os.remove(token_file)
                return False
            self.processes.append(proc)
            return True
        except Exception as e:
            logger.error(f"websockify start error: {e}")
            return False
        
    def navigate(self, url):
        """Navigate browser to a new URL using xdotool."""
        if not self.active:
            return False
        self.current_url = url
        env = os.environ.copy()
        env['DISPLAY'] = self.display
        try:
            subprocess.run(['xdotool', 'key', 'ctrl+l'], env=env, timeout=2, capture_output=True)
            time.sleep(0.2)
            subprocess.run(['xdotool', 'type', '--clearmodifiers', url], env=env, timeout=5, capture_output=True)
            subprocess.run(['xdotool', 'key', 'Return'], env=env, timeout=2, capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Navigate error: {e}")
            return False
        
    def stop(self):
        """Terminate all processes and cleanup."""
        self.active = False
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except:
                try:
                    proc.kill()
                except:
                    pass
        self.processes = []
        
        if hasattr(self, '_token_file') and os.path.exists(self._token_file):
            try:
                os.remove(self._token_file)
            except:
                pass
        logger.info(f"noVNC session {self.session_id} stopped")
        
    def is_alive(self):
        """Check if session is still running."""
        if not self.active:
            return False
        for proc in self.processes:
            if proc.poll() is not None:
                return False
        return True


class NoVNCManager:
    """Manages multiple noVNC sessions."""
    
    BASE_DISPLAY = 50
    BASE_VNC_PORT = 5950
    BASE_WS_PORT = 6100
    MAX_SESSIONS = 6
    
    def __init__(self):
        self.sessions = {}
        self.available_slots = list(range(self.MAX_SESSIONS))
        self.lock = Lock()
        self.session_tokens = {}
        self._cleanup_thread = Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
    def create_session(self, url="https://www.google.com"):
        """Create a new interactive browser session."""
        with self.lock:
            if not self.available_slots:
                oldest = min(self.sessions.values(), key=lambda s: s.created_at)
                self._release_session(oldest.session_id)
            
            slot = self.available_slots.pop(0)
            session_id = str(uuid.uuid4())[:8]
            
            display_num = self.BASE_DISPLAY + slot
            vnc_port = self.BASE_VNC_PORT + slot
            ws_port = self.BASE_WS_PORT + slot
            
            session = NoVNCSession(session_id, display_num, vnc_port, ws_port)
            session._slot = slot
            
            if session.start(url):
                self.sessions[session_id] = session
                return {
                    'success': True,
                    'session_id': session_id,
                    'ws_port': ws_port,
                    'token': session.token,
                    'url': url
                }
            else:
                self.available_slots.insert(0, slot)
                return {
                    'success': False,
                    'error': session.error or 'Error al iniciar sesion de navegador'
                }
    
    def _release_session(self, session_id):
        """Release a session and return its slot to the pool."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.stop()
            if hasattr(session, '_slot'):
                self.available_slots.append(session._slot)
            del self.sessions[session_id]
    
    def stop_session(self, session_id):
        """Stop a specific session."""
        with self.lock:
            if session_id in self.sessions:
                self._release_session(session_id)
                return True
            return False
    
    def get_session(self, session_id):
        """Get session info."""
        with self.lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                return {
                    'session_id': session_id,
                    'ws_port': session.ws_port,
                    'url': session.current_url,
                    'active': session.is_alive()
                }
            return None
    
    def navigate_session(self, session_id, url):
        """Navigate a session to a new URL."""
        with self.lock:
            if session_id in self.sessions:
                return self.sessions[session_id].navigate(url)
            return False
    
    def list_sessions(self):
        """List all active sessions."""
        with self.lock:
            return [
                {
                    'session_id': s.session_id,
                    'ws_port': s.ws_port,
                    'url': s.current_url,
                    'active': s.is_alive()
                }
                for s in self.sessions.values()
            ]
    
    def _cleanup_loop(self):
        """Periodically clean up dead sessions."""
        while True:
            time.sleep(30)
            with self.lock:
                dead_sessions = [
                    sid for sid, session in self.sessions.items()
                    if not session.is_alive() or (time.time() - session.created_at) > 900
                ]
                for sid in dead_sessions:
                    logger.info(f"Auto-cleanup session {sid}")
                    self._release_session(sid)


_manager = None

def get_manager():
    global _manager
    if _manager is None:
        _manager = NoVNCManager()
    return _manager

def create_interactive_session(url="https://www.google.com"):
    return get_manager().create_session(url)

def stop_interactive_session(session_id):
    return get_manager().stop_session(session_id)

def get_interactive_session(session_id):
    return get_manager().get_session(session_id)

def navigate_interactive_session(session_id, url):
    return get_manager().navigate_session(session_id, url)

def list_interactive_sessions():
    return get_manager().list_sessions()
