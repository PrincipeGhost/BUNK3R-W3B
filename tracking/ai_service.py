"""
AI Service - Multi-provider AI chat service with automatic fallback
Supports: Hugging Face, Groq, Google Gemini, Cerebras
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


class HuggingFaceProvider(AIProvider):
    """Hugging Face Inference API - Free tier ~1000 req/day"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "huggingface"
        self.model = "meta-llama/Meta-Llama-3-8B-Instruct"
        self.base_url = "https://api-inference.huggingface.co/models"
    
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


class AIService:
    """
    Multi-provider AI service with automatic fallback
    Manages conversation history and persistence
    """
    
    DEFAULT_SYSTEM_PROMPT = """Eres BUNK3R AI, un asistente inteligente integrado en la plataforma BUNK3R.
Eres amable, profesional y ayudas a los usuarios con sus consultas.
Respondes en español a menos que el usuario escriba en otro idioma.
Tienes conocimiento sobre:
- Rastreo de paquetes y envíos
- Criptomonedas y blockchain
- La plataforma BUNK3R y sus funcionalidades
- Programación y tecnología en general

Mantén tus respuestas concisas pero informativas.
Si no sabes algo, admítelo honestamente."""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.providers: List[AIProvider] = []
        self.conversations: Dict[str, List[Dict]] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available AI providers"""
        
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
        
        hf_key = os.environ.get('HUGGINGFACE_API_KEY', '')
        if hf_key:
            self.providers.append(HuggingFaceProvider(hf_key))
            logger.info("HuggingFace provider initialized")
        
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


ai_service: Optional[AIService] = None


def get_ai_service(db_manager=None) -> AIService:
    """Get or create the global AI service instance"""
    global ai_service
    if ai_service is None:
        ai_service = AIService(db_manager)
    return ai_service
