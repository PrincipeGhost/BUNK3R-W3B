"""
noVNC Service - Interactive browser sessions using VNC streaming.
Provides full browser interactivity through WebSocket-based VNC.
"""
import subprocess
import time
import os
import signal
import shutil
from threading import Thread, Lock
import uuid

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
        
    def start(self, url="https://www.google.com"):
        """Start the VNC session with browser."""
        try:
            self.current_url = url
            self._start_xvfb()
            time.sleep(1)
            self._start_vnc_server()
            time.sleep(1)
            self._start_browser(url)
            time.sleep(1)
            self._start_websockify()
            self.active = True
            return True
        except Exception as e:
            print(f"Error starting noVNC session: {e}")
            self.stop()
            return False
    
    def _start_xvfb(self):
        """Start virtual framebuffer."""
        cmd = [
            'Xvfb', self.display,
            '-screen', '0', '390x844x24',
            '-ac'
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(proc)
        
    def _start_vnc_server(self):
        """Start x11vnc pointing to virtual display."""
        cmd = [
            'x11vnc',
            '-display', self.display,
            '-rfbport', str(self.vnc_port),
            '-forever',
            '-shared',
            '-nopw',
            '-noxdamage',
            '-cursor', 'arrow',
            '-repeat'
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(proc)
        
    def _start_browser(self, url):
        """Launch Chromium on virtual display."""
        env = os.environ.copy()
        env['DISPLAY'] = self.display
        
        chromium_path = shutil.which('chromium') or shutil.which('chromium-browser')
        
        cmd = [
            chromium_path,
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--window-size=390,844',
            '--window-position=0,0',
            '--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            '--force-device-scale-factor=1',
            url
        ]
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(proc)
        
    def _start_websockify(self):
        """Start websockify proxy for noVNC."""
        novnc_path = os.path.join(os.getcwd(), 'static', 'novnc')
        
        cmd = [
            'websockify',
            '--web', novnc_path,
            f'0.0.0.0:{self.ws_port}',
            f'localhost:{self.vnc_port}'
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(proc)
        
    def navigate(self, url):
        """Navigate browser to a new URL (uses xdotool)."""
        if not self.active:
            return False
        self.current_url = url
        env = os.environ.copy()
        env['DISPLAY'] = self.display
        try:
            subprocess.run(['xdotool', 'key', 'ctrl+l'], env=env, timeout=2)
            time.sleep(0.1)
            subprocess.run(['xdotool', 'type', '--clearmodifiers', url], env=env, timeout=5)
            subprocess.run(['xdotool', 'key', 'Return'], env=env, timeout=2)
            return True
        except:
            return False
        
    def stop(self):
        """Terminate all processes."""
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
    
    def __init__(self, base_display=50, base_vnc_port=5950, base_ws_port=6100, max_sessions=10):
        self.base_display = base_display
        self.base_vnc_port = base_vnc_port
        self.base_ws_port = base_ws_port
        self.max_sessions = max_sessions
        self.sessions = {}
        self.lock = Lock()
        self._cleanup_thread = Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
    def create_session(self, url="https://www.google.com"):
        """Create a new interactive browser session."""
        with self.lock:
            if len(self.sessions) >= self.max_sessions:
                oldest = min(self.sessions.values(), key=lambda s: s.created_at)
                self.stop_session(oldest.session_id)
            
            session_id = str(uuid.uuid4())[:8]
            slot = len(self.sessions)
            
            display_num = self.base_display + slot
            vnc_port = self.base_vnc_port + slot
            ws_port = self.base_ws_port + slot
            
            session = NoVNCSession(session_id, display_num, vnc_port, ws_port)
            
            if session.start(url):
                self.sessions[session_id] = session
                return {
                    'success': True,
                    'session_id': session_id,
                    'ws_port': ws_port,
                    'url': url
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to start browser session'
                }
    
    def stop_session(self, session_id):
        """Stop a specific session."""
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].stop()
                del self.sessions[session_id]
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
            time.sleep(60)
            with self.lock:
                dead_sessions = [
                    sid for sid, session in self.sessions.items()
                    if not session.is_alive() or (time.time() - session.created_at) > 3600
                ]
                for sid in dead_sessions:
                    self.sessions[sid].stop()
                    del self.sessions[sid]


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
