"""
AI Service - Multi-provider AI chat service with automatic fallback
Supports: DeepSeek, Groq, Google Gemini, Cerebras, Hugging Face
All providers offer free tiers
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """Base class for AI providers"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.name = "base"
        self.available = bool(api_key)
    
    @abstractmethod
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
        """Send chat request and return response"""
        pass
    
    def is_available(self) -> bool:
        return self.available


class DeepSeekV32Provider(AIProvider):
    """DeepSeek V3.2 via Hugging Face - Main AI Model"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "deepseek-v3.2"
        self.model = "deepseek-ai/DeepSeek-V3.2"
        self.base_url = "https://router.huggingface.co/hf"
    
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
        try:
            import requests
            
            prompt = ""
            if system_prompt:
                prompt = f"<|system|>\n{system_prompt}<|end|>\n"
            
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    prompt += f"<|user|>\n{content}<|end|>\n"
                elif role == "assistant":
                    prompt += f"<|assistant|>\n{content}<|end|>\n"
            
            prompt += "<|assistant|>\n"
            
            response = requests.post(
                f"{self.base_url}/{self.model}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 2048,
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "return_full_text": False,
                        "do_sample": True
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get("generated_text", "")
                    return {"success": True, "response": text, "provider": self.name}
                return {"success": False, "error": "Invalid response format", "provider": self.name}
            elif response.status_code == 503:
                return {"success": False, "error": "Model is loading, please wait", "provider": self.name}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"DeepSeek V3.2 error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class HuggingFaceProvider(AIProvider):
    """Hugging Face Inference API - Free tier ~1000 req/day"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "huggingface"
        self.model = "meta-llama/Meta-Llama-3-8B-Instruct"
        self.base_url = "https://router.huggingface.co/hf"
    
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
        try:
            import requests
            
            prompt = ""
            if system_prompt:
                prompt = f"<|system|>\n{system_prompt}</s>\n"
            
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    prompt += f"<|user|>\n{content}</s>\n"
                elif role == "assistant":
                    prompt += f"<|assistant|>\n{content}</s>\n"
            
            prompt += "<|assistant|>\n"
            
            response = requests.post(
                f"{self.base_url}/{self.model}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 1024,
                        "temperature": 0.7,
                        "return_full_text": False
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get("generated_text", "")
                    return {"success": True, "response": text, "provider": self.name}
                return {"success": False, "error": "Invalid response format", "provider": self.name}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"HuggingFace error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class GroqProvider(AIProvider):
    """Groq API - Free tier, very fast inference"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "groq"
        self.model = "llama3-8b-8192"
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
        try:
            import requests
            
            chat_messages = []
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            chat_messages.extend(messages)
            
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": chat_messages,
                    "temperature": 0.7,
                    "max_tokens": 1024
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"success": True, "response": text, "provider": self.name}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"Groq error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class GeminiProvider(AIProvider):
    """Google Gemini API - Free tier with generous limits"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "gemini"
        self.model = "gemini-1.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
        try:
            import requests
            
            contents = []
            for msg in messages:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })
            
            payload = {"contents": contents}
            
            if system_prompt:
                payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
            
            payload["generationConfig"] = {
                "temperature": 0.7,
                "maxOutputTokens": 1024
            }
            
            response = requests.post(
                f"{self.base_url}/{self.model}:generateContent?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [])
                if candidates:
                    text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    return {"success": True, "response": text, "provider": self.name}
                return {"success": False, "error": "No candidates in response", "provider": self.name}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class CerebrasProvider(AIProvider):
    """Cerebras API - Free tier 30 req/min, very fast"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "cerebras"
        self.model = "llama3.1-8b"
        self.base_url = "https://api.cerebras.ai/v1/chat/completions"
    
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
        try:
            import requests
            
            chat_messages = []
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            chat_messages.extend(messages)
            
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": chat_messages,
                    "temperature": 0.7,
                    "max_tokens": 1024
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"success": True, "response": text, "provider": self.name}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"Cerebras error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class DeepSeekProvider(AIProvider):
    """DeepSeek API - High quality, affordable, OpenAI-compatible"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "deepseek"
        self.model = "deepseek-chat"
        self.base_url = "https://api.deepseek.com/chat/completions"
    
    def chat(self, messages: List[Dict], system_prompt: str = None) -> Dict:
        try:
            import requests
            
            chat_messages = []
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            chat_messages.extend(messages)
            
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": chat_messages,
                    "temperature": 0.7,
                    "max_tokens": 1024
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"success": True, "response": text, "provider": self.name}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": self.name}
                
        except Exception as e:
            logger.error(f"DeepSeek error: {e}")
            return {"success": False, "error": str(e), "provider": self.name}


class AIService:
    """
    Multi-provider AI service with automatic fallback
    Manages conversation history and persistence
    BUNK3R AI - Sistema de IA Avanzado con Capacidades de los 15 Volumenes
    """
    
    DEFAULT_SYSTEM_PROMPT = """═══════════════════════════════════════════════════════════════════════════════
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    BUNK3R AI - SISTEMA DE IA AVANZADO                         ║
║           Arquitecto de Software + Experto en Seguridad + UX Designer         ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Eres BUNK3R AI, un sistema de inteligencia artificial de ultima generacion integrado en la plataforma BUNK3R.
No eres solo un asistente - eres un Arquitecto de Software, Experto en Ciberseguridad y Disenador UX.

═══════════════════════════════════════════════════════════════════════════════
SECCION 1: IDENTIDAD CORE
═══════════════════════════════════════════════════════════════════════════════

- NOMBRE: BUNK3R AI
- VERSION: Sistema Multi-Volumen (v3-v15)
- IDIOMA: Respondo en el idioma que el usuario utilice (espanol por defecto)
- TONO: Profesional pero accesible, tecnico cuando es necesario

═══════════════════════════════════════════════════════════════════════════════
SECCION 2: CAPACIDADES AVANZADAS
═══════════════════════════════════════════════════════════════════════════════

2.1 RAZONAMIENTO ESTRATEGICO (ARQUITECTO DE SOFTWARE)
- Antes de codificar, genero BLUEPRINTS con: Objetivo, Stack, Modelo de Datos, Flujo Critico
- Aplico pensamiento de primeros principios para resolver problemas complejos
- Genero ADRs (Architecture Decision Records) para justificar decisiones tecnologicas

2.2 METACOGNICION Y AUTO-CORRECCION
- Uso protocolo "STOP & THINK" antes de acciones complejas
- Me auto-corrijo en tiempo real si detecto errores en mi razonamiento
- Declaro mi estado mental: INVESTIGANDO | CONSTRUYENDO | PROBANDO | BLOQUEADO

2.3 CIBERSEGURIDAD Y RED TEAMING
- Auditoria de codigo estatico (SAST) y dinamico (DAST)
- Deteccion de OWASP Top 10: SQL Injection, XSS, CSRF, secretos expuestos
- Sugiero fixes con codigo corregido

2.4 LOGICA DE NEGOCIO Y LEGAL
- Auditoria de licencias (GPL, MIT, Apache)
- Calculadora de costos cloud (FinOps)
- Verificacion de compliance GDPR/CCPA

2.5 PSICOLOGIA UX Y DISENO EMOCIONAL
- Paletas de colores basadas en psicologia (confianza, urgencia, calma)
- Accesibilidad WCAG 2.1 AA/AAA
- Copywriting y microcopy profesional

2.6 WEB3 Y BLOCKCHAIN
- Interaccion con smart contracts
- Soporte para TON, Ethereum, Polygon
- Integracion con BUNK3RCO1N (B3C)

═══════════════════════════════════════════════════════════════════════════════
SECCION 3: AREAS DE CONOCIMIENTO
═══════════════════════════════════════════════════════════════════════════════

- Rastreo de paquetes y logistica avanzada
- Criptomonedas, DeFi y blockchain (especialmente TON)
- Desarrollo web full-stack (Flask, React, Vue, Node.js)
- Arquitectura de microservicios y DevOps
- Base de datos SQL y NoSQL
- APIs RESTful y GraphQL
- Seguridad informatica y pentesting
- Machine Learning y LLMOps
- IoT y automatizacion
- Marketing digital y growth hacking

═══════════════════════════════════════════════════════════════════════════════
SECCION 4: PROTOCOLO DE RESPUESTA
═══════════════════════════════════════════════════════════════════════════════

1. ANALIZO la intencion real del usuario (no solo las palabras literales)
2. EVALUO riesgos potenciales de mi respuesta
3. BUSCO informacion faltante antes de actuar
4. PLANIFICO estrategicamente mi respuesta
5. EJECUTO con precision y calidad profesional
6. VERIFICO que mi respuesta sea correcta y completa

═══════════════════════════════════════════════════════════════════════════════
SECCION 5: REGLAS CRITICAS
═══════════════════════════════════════════════════════════════════════════════

- NUNCA invento datos - si no se algo, lo admito
- SIEMPRE priorizo la seguridad del usuario
- CUESTIONO ideas peligrosas o ineficientes (con respeto)
- DOCUMENTO mis decisiones cuando son importantes
- GENERO codigo limpio, seguro y mantenible

Respondo de manera concisa pero completa, adaptando mi nivel tecnico al usuario."""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.providers: List[AIProvider] = []
        self.conversations: Dict[str, List[Dict]] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available AI providers"""
        
        hf_key = os.environ.get('HUGGINGFACE_API_KEY', '')
        if hf_key:
            self.providers.append(DeepSeekV32Provider(hf_key))
            logger.info("DeepSeek V3.2 (Main Model) provider initialized")
        
        deepseek_key = os.environ.get('DEEPSEEK_API_KEY', '')
        if deepseek_key:
            self.providers.append(DeepSeekProvider(deepseek_key))
            logger.info("DeepSeek API provider initialized")
        
        groq_key = os.environ.get('GROQ_API_KEY', '')
        if groq_key:
            self.providers.append(GroqProvider(groq_key))
            logger.info("Groq provider initialized")
        
        gemini_key = os.environ.get('GEMINI_API_KEY', '')
        if gemini_key:
            self.providers.append(GeminiProvider(gemini_key))
            logger.info("Gemini provider initialized")
        
        cerebras_key = os.environ.get('CEREBRAS_API_KEY', '')
        if cerebras_key:
            self.providers.append(CerebrasProvider(cerebras_key))
            logger.info("Cerebras provider initialized")
        
        if hf_key:
            self.providers.append(HuggingFaceProvider(hf_key))
            logger.info("HuggingFace Llama provider initialized")
        
        if not self.providers:
            logger.warning("No AI providers configured. Set API keys in environment variables.")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return [p.name for p in self.providers if p.is_available()]
    
    def chat(self, user_id: str, message: str, system_prompt: str = None, 
             preferred_provider: str = None) -> Dict:
        """
        Send a chat message and get response
        Uses automatic fallback between providers
        """
        if not self.providers:
            return {
                "success": False,
                "error": "No hay proveedores de IA configurados. Configura las claves API.",
                "provider": None
            }
        
        conversation = self._get_conversation(user_id)
        conversation.append({"role": "user", "content": message})
        
        system = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        
        providers_to_try = self.providers.copy()
        if preferred_provider:
            providers_to_try.sort(key=lambda p: 0 if p.name == preferred_provider else 1)
        
        for provider in providers_to_try:
            if not provider.is_available():
                continue
            
            logger.info(f"Trying provider: {provider.name}")
            result = provider.chat(conversation, system)
            
            if result.get("success"):
                response_text = result.get("response", "")
                conversation.append({"role": "assistant", "content": response_text})
                self._save_conversation(user_id, conversation)
                
                return {
                    "success": True,
                    "response": response_text,
                    "provider": provider.name,
                    "conversation_length": len(conversation)
                }
            else:
                logger.warning(f"Provider {provider.name} failed: {result.get('error')}")
        
        conversation.pop()
        
        return {
            "success": False,
            "error": "Todos los proveedores de IA fallaron. Intenta más tarde.",
            "provider": None
        }
    
    def _get_conversation(self, user_id: str) -> List[Dict]:
        """Get conversation history for user"""
        if user_id not in self.conversations:
            if self.db_manager:
                history = self._load_conversation_from_db(user_id)
                self.conversations[user_id] = history
            else:
                self.conversations[user_id] = []
        return self.conversations[user_id]
    
    def _save_conversation(self, user_id: str, conversation: List[Dict]):
        """Save conversation to memory and database"""
        self.conversations[user_id] = conversation
        
        if self.db_manager:
            self._save_conversation_to_db(user_id, conversation)
    
    def _load_conversation_from_db(self, user_id: str) -> List[Dict]:
        """Load conversation history from database"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT role, content FROM ai_chat_messages
                        WHERE user_id = %s
                        ORDER BY created_at ASC
                        LIMIT 50
                    """, (user_id,))
                    rows = cur.fetchall()
                    return [{"role": row[0], "content": row[1]} for row in rows]
        except Exception as e:
            logger.error(f"Error loading conversation from DB: {e}")
            return []
    
    def _save_conversation_to_db(self, user_id: str, conversation: List[Dict]):
        """Save latest messages to database"""
        try:
            if len(conversation) < 2:
                return
            
            last_two = conversation[-2:]
            
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    for msg in last_two:
                        cur.execute("""
                            INSERT INTO ai_chat_messages (user_id, role, content, created_at)
                            VALUES (%s, %s, %s, %s)
                        """, (user_id, msg["role"], msg["content"], datetime.now()))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving conversation to DB: {e}")
    
    def clear_conversation(self, user_id: str) -> bool:
        """Clear conversation history for user"""
        try:
            if user_id in self.conversations:
                del self.conversations[user_id]
            
            if self.db_manager:
                with self.db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM ai_chat_messages WHERE user_id = %s", (user_id,))
                    conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return False
    
    def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history for user"""
        conversation = self._get_conversation(user_id)
        return conversation[-limit:] if len(conversation) > limit else conversation
    
    def get_stats(self) -> Dict:
        """Get AI service statistics"""
        return {
            "providers_available": self.get_available_providers(),
            "total_providers": len(self.providers),
            "active_conversations": len(self.conversations)
        }
    
    def generate_code(self, user_id: str, message: str, current_files: Dict[str, str], 
                      project_name: str) -> Dict:
        """
        Generate code for web projects based on user instructions.
        Returns files to create/update and a response message.
        """
        if not self.providers:
            return {
                "success": False,
                "error": "No hay proveedores de IA configurados.",
                "provider": None
            }
        
        files_context = ""
        for filename, content in current_files.items():
            preview = content[:500] + "..." if len(content) > 500 else content
            files_context += f"\n--- {filename} ---\n{preview}\n"
        
        code_system_prompt = f"""═══════════════════════════════════════════════════════════════════════════════
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    BUNK3R CODE BUILDER - ELITE WEB GENERATOR                  ║
║              Generador de Paginas Web Profesionales de Alta Calidad           ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Eres BUNK3R Code Builder, un arquitecto de interfaces web de nivel ELITE.
Tu especialidad: crear experiencias digitales de calidad Fintech/Neo-bank (Binance, Revolut, N26).

═══════════════════════════════════════════════════════════════════════════════
SECCION 1: FORMATO DE RESPUESTA OBLIGATORIO
═══════════════════════════════════════════════════════════════════════════════

Responde SIEMPRE en formato JSON valido con esta estructura exacta:
{{
    "files": {{
        "nombre_archivo.ext": "contenido completo del archivo"
    }},
    "message": "Explicacion detallada de lo que creaste"
}}

═══════════════════════════════════════════════════════════════════════════════
SECCION 2: ESTANDARES DE DISENO PROFESIONAL
═══════════════════════════════════════════════════════════════════════════════

2.1 PALETA DE COLORES NEO-BANK:
- Fondos Ultra-Oscuros: #0B0E11, #12161C, #1E2329, #2B3139
- Acentos Dorados: #F0B90B (primario), #FCD535 (hover), #D4A20B (activo)
- Estados: #22C55E (exito), #EF4444 (error), #F59E0B (advertencia)
- Textos: #FFFFFF (principal), #848E9C (secundario), #5E6673 (muted)
- Degradados: linear-gradient(135deg, #F0B90B 0%, #D4A20B 100%)

2.2 TIPOGRAFIA PROFESIONAL:
- Font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif
- Headings: font-weight: 600-700, letter-spacing: -0.02em
- Body: font-weight: 400-500, line-height: 1.6

2.3 EFECTOS PREMIUM:
- Sombras suaves: box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3), 0 2px 4px -2px rgba(0,0,0,0.2)
- Bordes sutiles: border: 1px solid rgba(255,255,255,0.1)
- Glass morphism: backdrop-filter: blur(10px); background: rgba(30,35,41,0.8)
- Transiciones: transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)
- Hover effects: transform: translateY(-2px); box-shadow aumentado
- Glow effects: 0 0 20px rgba(240,185,11,0.3)

2.4 COMPONENTES UI PROFESIONALES:
- Cards: bordes redondeados (12-16px), padding generoso (24px), efecto hover
- Botones: gradientes dorados, padding 12px 24px, font-weight 600, hover con glow
- Inputs: fondo oscuro, borde sutil, focus con glow dorado
- Modales: backdrop blur, animaciones de entrada/salida
- Iconos: SVG inline de Lucide/Feather Icons, stroke-width: 1.5-2
- Skeleton loaders: animacion pulse con gradiente

2.5 LAYOUT Y ESPACIADO:
- Grid/Flexbox moderno con gap
- Espaciado consistente: 8px, 16px, 24px, 32px, 48px, 64px
- Max-width contenedores: 1200px, 1400px
- Responsive breakpoints: 640px, 768px, 1024px, 1280px

═══════════════════════════════════════════════════════════════════════════════
SECCION 3: REGLAS DE CODIGO
═══════════════════════════════════════════════════════════════════════════════

3.1 HTML5:
- Semantico: header, nav, main, section, article, aside, footer
- Accesible: aria-labels, roles, alt texts
- Meta tags completos: viewport, charset, description

3.2 CSS MODERNO:
- Variables CSS (custom properties)
- Flexbox y Grid como base
- Animaciones con @keyframes
- Media queries para responsive
- NO usar !important

3.3 JAVASCRIPT ES6+:
- Const/let (nunca var)
- Arrow functions
- Template literals
- Async/await
- Event delegation
- Animaciones suaves con requestAnimationFrame

═══════════════════════════════════════════════════════════════════════════════
SECCION 4: CONTEXTO DEL PROYECTO
═══════════════════════════════════════════════════════════════════════════════

NOMBRE DEL PROYECTO: {project_name}

ARCHIVOS ACTUALES:
{files_context if files_context else "(Proyecto nuevo, sin archivos)"}

═══════════════════════════════════════════════════════════════════════════════
SECCION 5: INSTRUCCIONES FINALES
═══════════════════════════════════════════════════════════════════════════════

- Genera codigo COMPLETO y funcional, nunca fragmentos
- Si modificas un archivo, incluye TODO el archivo con los cambios
- Prioriza la experiencia de usuario y la estetica profesional
- Crea interfaces que parezcan de aplicaciones valoradas en millones
- Responde SOLO con JSON valido, nada mas"""

        messages = [{"role": "user", "content": message}]
        
        for provider in self.providers:
            if not provider.is_available():
                continue
            
            logger.info(f"Code builder trying provider: {provider.name}")
            result = provider.chat(messages, code_system_prompt)
            
            if result.get("success"):
                response_text = result.get("response", "")
                
                try:
                    json_match = None
                    if response_text.strip().startswith('{'):
                        json_match = response_text.strip()
                    else:
                        import re
                        json_pattern = r'\{[\s\S]*\}'
                        matches = re.findall(json_pattern, response_text)
                        if matches:
                            for match in matches:
                                try:
                                    sanitized = self._sanitize_json(match)
                                    json.loads(sanitized)
                                    json_match = sanitized
                                    break
                                except:
                                    continue
                    
                    if json_match:
                        sanitized_json = self._sanitize_json(json_match)
                        parsed = json.loads(sanitized_json)
                        files = parsed.get("files", {})
                        msg = parsed.get("message", "Codigo generado exitosamente")
                        
                        if files:
                            return {
                                "success": True,
                                "files": files,
                                "response": msg,
                                "provider": provider.name
                            }
                    
                    extracted = self._extract_code_blocks(response_text)
                    if extracted:
                        return {
                            "success": True,
                            "files": extracted,
                            "response": "He generado el codigo solicitado.",
                            "provider": provider.name
                        }
                    
                    return {
                        "success": False,
                        "error": "No se pudo extraer codigo de la respuesta. Intenta de nuevo.",
                        "provider": provider.name
                    }
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse error: {e}")
                    extracted = self._extract_code_blocks(response_text)
                    if extracted:
                        return {
                            "success": True,
                            "files": extracted,
                            "response": "He generado el codigo. Revisa los archivos actualizados.",
                            "provider": provider.name
                        }
                    return {
                        "success": False,
                        "error": "No se pudo parsear la respuesta de la IA. Intenta de nuevo con instrucciones mas claras.",
                        "provider": provider.name
                    }
            else:
                logger.warning(f"Provider {provider.name} failed: {result.get('error')}")
        
        return {
            "success": False,
            "error": "No se pudo generar el codigo. Intenta de nuevo.",
            "provider": None
        }
    
    def _sanitize_json(self, json_str: str) -> str:
        """Sanitize JSON string by escaping control characters in string values"""
        import re
        
        result = []
        in_string = False
        escape_next = False
        
        for char in json_str:
            if escape_next:
                result.append(char)
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                result.append(char)
                continue
                
            if char == '"':
                in_string = not in_string
                result.append(char)
                continue
            
            if in_string:
                if char == '\n':
                    result.append('\\n')
                elif char == '\r':
                    result.append('\\r')
                elif char == '\t':
                    result.append('\\t')
                elif ord(char) < 32:
                    result.append(f'\\u{ord(char):04x}')
                else:
                    result.append(char)
            else:
                result.append(char)
        
        return ''.join(result)
    
    def _extract_code_blocks(self, text: str) -> Dict[str, str]:
        """Extract code blocks from markdown-style response"""
        import re
        files = {}
        
        pattern = r'```(\w+)?\s*\n?([\s\S]*?)```'
        matches = re.findall(pattern, text)
        
        lang_to_ext = {
            'html': 'index.html',
            'css': 'styles.css',
            'javascript': 'script.js',
            'js': 'script.js'
        }
        
        for lang, code in matches:
            lang = lang.lower() if lang else 'html'
            filename = lang_to_ext.get(lang, f'file.{lang}')
            files[filename] = code.strip()
        
        if not files and '<!DOCTYPE html>' in text.lower():
            html_match = re.search(r'(<!DOCTYPE html>[\s\S]*?</html>)', text, re.IGNORECASE)
            if html_match:
                files['index.html'] = html_match.group(1).strip()
        
        return files


ai_service: Optional[AIService] = None


def get_ai_service(db_manager=None) -> AIService:
    """Get or create the global AI service instance"""
    global ai_service
    if ai_service is None:
        ai_service = AIService(db_manager)
    return ai_service
