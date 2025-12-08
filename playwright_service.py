"""
Playwright service for mobile browser emulation.
Captures screenshots of web pages as they would appear on an iPhone.
"""
import asyncio
import base64
from threading import Thread
import time

IPHONE_CONFIG = {
    'viewport': {'width': 375, 'height': 667},
    'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'device_scale_factor': 2,
    'is_mobile': True,
    'has_touch': True,
}

MAX_CONCURRENT = 6

class PlaywrightService:
    def __init__(self):
        self.loop = None
        self.thread = None
        self.playwright = None
        self.browser = None
        self.ready = False
        self.semaphore = None
        self._start_worker()
    
    def _start_worker(self):
        self.thread = Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        timeout = 30
        start = time.time()
        while not self.ready and (time.time() - start) < timeout:
            time.sleep(0.1)
        if not self.ready:
            raise RuntimeError("Playwright service failed to start")
    
    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._init_playwright())
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        self.ready = True
        self.loop.run_forever()
    
    async def _init_playwright(self):
        from playwright.async_api import async_playwright
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--single-process'
            ]
        )
    
    async def _capture_async(self, url):
        async with self.semaphore:
            context = None
            try:
                context = await self.browser.new_context(
                    viewport=IPHONE_CONFIG['viewport'],
                    user_agent=IPHONE_CONFIG['user_agent'],
                    device_scale_factor=IPHONE_CONFIG['device_scale_factor'],
                    is_mobile=IPHONE_CONFIG['is_mobile'],
                    has_touch=IPHONE_CONFIG['has_touch'],
                )
                page = await context.new_page()
                await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                await page.wait_for_timeout(500)
                screenshot_bytes = await page.screenshot(type='png')
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                return {
                    'success': True,
                    'screenshot': screenshot_base64,
                    'url': url
                }
            except Exception as e:
                error_msg = str(e).lower()
                if 'timeout' in error_msg:
                    user_error = 'La pagina tardo demasiado en responder'
                elif 'net::err_name_not_resolved' in error_msg:
                    user_error = 'No se pudo encontrar el sitio web'
                elif 'net::err_connection' in error_msg:
                    user_error = 'Error de conexion con el sitio'
                elif 'navigation' in error_msg:
                    user_error = 'Error al navegar a la pagina'
                else:
                    user_error = 'No se pudo cargar la pagina'
                return {
                    'success': False,
                    'error': user_error,
                    'url': url
                }
            finally:
                if context:
                    try:
                        await context.close()
                    except:
                        pass
    
    def capture(self, url, session_id='default'):
        if not self.ready or not self.loop:
            return {'success': False, 'error': 'Servicio no disponible'}
        
        future = asyncio.run_coroutine_threadsafe(self._capture_async(url), self.loop)
        try:
            result = future.result(timeout=25)
            return result
        except Exception:
            return {'success': False, 'error': 'Tiempo de espera agotado'}

_service = None

def get_service():
    global _service
    if _service is None:
        _service = PlaywrightService()
    return _service

def capture_mobile_screenshot(url, session_id='default'):
    service = get_service()
    return service.capture(url, session_id)
