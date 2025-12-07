"""
BUNK3R AI Constructor - Sistema de IA Constructora de 8 Fases
Arquitectura completa para generación inteligente de proyectos web

Fases:
1. Recepción y Análisis Inicial (IntentParser)
2. Investigación Autónoma (ResearchEngine)
3. Clarificación Inteligente (ClarificationManager)
4. Construcción del Prompt Maestro (PromptBuilder)
5. Presentación del Plan (PlanPresenter)
6. Ejecución Controlada (TaskOrchestrator)
7. Verificación Automática (OutputVerifier)
8. Entrega Final (DeliveryManager)
"""

import os
import json
import logging
import re
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Tipos de tareas que BUNK3R puede manejar"""
    CREAR_WEB = "crear_web"
    CREAR_LANDING = "crear_landing"
    CREAR_DASHBOARD = "crear_dashboard"
    CREAR_FORMULARIO = "crear_formulario"
    CREAR_API = "crear_api"
    MODIFICAR_CODIGO = "modificar_codigo"
    CORREGIR_ERROR = "corregir_error"
    OPTIMIZAR = "optimizar"
    EXPLICAR = "explicar"
    CONSULTA_GENERAL = "consulta_general"
    DESCONOCIDO = "desconocido"


class ProjectStyle(Enum):
    """Estilos de diseño disponibles"""
    MODERNO_OSCURO = "moderno_oscuro"
    MINIMALISTA = "minimalista"
    CORPORATIVO = "corporativo"
    CALIDO = "calido"
    FUTURISTA = "futurista"
    NEOBANCO = "neobanco"


@dataclass
class IntentAnalysis:
    """Resultado del análisis de intención"""
    tipo_tarea: TaskType
    contexto: str
    especificaciones_usuario: Dict[str, Any]
    requiere_investigacion: bool
    requiere_clarificacion: bool
    nivel_detalle: str  # "alto", "medio", "bajo", "vago"
    keywords: List[str]
    idioma: str
    urgencia: str  # "alta", "media", "baja"
    
    def to_dict(self) -> Dict:
        return {
            "tipo_tarea": self.tipo_tarea.value,
            "contexto": self.contexto,
            "especificaciones_usuario": self.especificaciones_usuario,
            "requiere_investigacion": self.requiere_investigacion,
            "requiere_clarificacion": self.requiere_clarificacion,
            "nivel_detalle": self.nivel_detalle,
            "keywords": self.keywords,
            "idioma": self.idioma,
            "urgencia": self.urgencia
        }


@dataclass
class ResearchResult:
    """Resultado de la investigación autónoma"""
    referencias: List[str]
    elementos_recomendados: List[str]
    paleta_sugerida: List[str]
    estilo: str
    insights: str
    mejores_practicas: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ClarificationResult:
    """Resultado de la clarificación con el usuario"""
    preguntas_realizadas: int
    respuestas_usuario: Dict[str, str]
    clarificacion_completa: bool
    preferencias_detectadas: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TaskItem:
    """Item de tarea individual"""
    id: int
    descripcion: str
    estado: str  # "pendiente", "en_progreso", "completada", "error"
    archivo_destino: Optional[str] = None
    codigo_generado: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ExecutionPlan:
    """Plan de ejecución completo"""
    tareas: List[TaskItem]
    tiempo_estimado: str
    riesgos: List[str]
    archivos_a_crear: List[str]
    dependencias: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "tareas": [t.to_dict() for t in self.tareas],
            "tiempo_estimado": self.tiempo_estimado,
            "riesgos": self.riesgos,
            "archivos_a_crear": self.archivos_a_crear,
            "dependencias": self.dependencias
        }


@dataclass
class VerificationResult:
    """Resultado de la verificación automática"""
    sintaxis_valida: bool
    completitud: bool
    funcionalidad: bool
    responsive: bool
    coincide_requisitos: bool
    errores: List[str]
    advertencias: List[str]
    puntuacion: int  # 0-100
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ConstructorSession:
    """Sesión del constructor - mantiene estado entre fases"""
    session_id: str
    user_id: str
    fase_actual: int
    intent: Optional[IntentAnalysis] = None
    research: Optional[ResearchResult] = None
    clarification: Optional[ClarificationResult] = None
    plan: Optional[ExecutionPlan] = None
    prompt_maestro: Optional[str] = None
    archivos_generados: Dict[str, str] = field(default_factory=dict)
    verification: Optional[VerificationResult] = None
    esperando_confirmacion: bool = False
    esperando_clarificacion: bool = False
    preguntas_pendientes: List[str] = field(default_factory=list)
    historial: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "fase_actual": self.fase_actual,
            "intent": self.intent.to_dict() if self.intent else None,
            "research": self.research.to_dict() if self.research else None,
            "clarification": self.clarification.to_dict() if self.clarification else None,
            "plan": self.plan.to_dict() if self.plan else None,
            "prompt_maestro": self.prompt_maestro,
            "archivos_generados": self.archivos_generados,
            "verification": self.verification.to_dict() if self.verification else None,
            "esperando_confirmacion": self.esperando_confirmacion,
            "esperando_clarificacion": self.esperando_clarificacion,
            "preguntas_pendientes": self.preguntas_pendientes,
            "fase_nombre": self._get_fase_nombre()
        }
    
    def _get_fase_nombre(self) -> str:
        nombres = {
            1: "Análisis Inicial",
            2: "Investigación",
            3: "Clarificación",
            4: "Construcción Prompt",
            5: "Presentación Plan",
            6: "Ejecución",
            7: "Verificación",
            8: "Entrega"
        }
        return nombres.get(self.fase_actual, "Desconocida")


class IntentParser:
    """
    FASE 1: Analizador de Intención
    Extrae qué quiere el usuario y decide los siguientes pasos
    """
    
    TASK_PATTERNS = {
        TaskType.CREAR_LANDING: [
            r"landing\s*page", r"página\s*de\s*aterrizaje", r"landing",
            r"one\s*page", r"página\s*única"
        ],
        TaskType.CREAR_WEB: [
            r"sitio\s*web", r"página\s*web", r"website", r"web\s*app",
            r"aplicación\s*web", r"portal"
        ],
        TaskType.CREAR_DASHBOARD: [
            r"dashboard", r"panel", r"tablero", r"admin\s*panel",
            r"panel\s*de\s*control"
        ],
        TaskType.CREAR_FORMULARIO: [
            r"formulario", r"form", r"contacto", r"registro",
            r"encuesta", r"survey"
        ],
        TaskType.CREAR_API: [
            r"api", r"endpoint", r"backend", r"servidor",
            r"rest\s*api", r"servicio"
        ],
        TaskType.MODIFICAR_CODIGO: [
            r"modifica", r"cambia", r"actualiza", r"edita",
            r"agrega", r"añade", r"quita", r"elimina"
        ],
        TaskType.CORREGIR_ERROR: [
            r"error", r"bug", r"falla", r"no\s*funciona", r"arregla",
            r"corrige", r"fix", r"problema"
        ],
        TaskType.OPTIMIZAR: [
            r"optimiza", r"mejora", r"más\s*rápido", r"rendimiento",
            r"performance", r"refactoriza"
        ],
        TaskType.EXPLICAR: [
            r"explica", r"qué\s*es", r"cómo\s*funciona", r"por\s*qué",
            r"enseña", r"tutorial"
        ]
    }
    
    CONTEXT_KEYWORDS = {
        "restaurante": ["restaurante", "café", "cafetería", "bar", "comida", "menú", "cocina", "chef", "platos", "reserva"],
        "ecommerce": ["tienda online", "ecommerce", "e-commerce", "carrito", "checkout", "vender", "comprar", "productos", "stripe", "paypal", "pagos online"],
        "portfolio": ["portfolio", "portafolio", "proyectos", "trabajos", "cv", "curriculum", "fotógrafo", "diseñador", "freelance"],
        "blog": ["blog", "artículos", "posts", "noticias", "contenido", "publicaciones"],
        "saas": ["saas", "suscripción", "plataforma", "software", "app", "dashboard", "panel", "métricas", "usuarios"],
        "fintech": ["fintech", "banco", "inversiones", "wallet", "cripto", "finanzas", "trading", "bolsa", "acciones"],
        "negocio": ["negocio", "empresa", "comercio", "servicio", "startup", "compañía"]
    }
    
    def analyze(self, message: str) -> IntentAnalysis:
        """Analiza el mensaje del usuario y extrae la intención"""
        message_lower = message.lower().strip()
        
        # Detectar tipo de tarea
        tipo_tarea = self._detect_task_type(message_lower)
        
        # Extraer contexto
        contexto = self._extract_context(message_lower)
        
        # Extraer especificaciones
        specs = self._extract_specifications(message)
        
        # Evaluar nivel de detalle
        nivel_detalle = self._evaluate_detail_level(message, specs)
        
        # Extraer keywords
        keywords = self._extract_keywords(message_lower)
        
        # Detectar idioma
        idioma = self._detect_language(message)
        
        # Detectar urgencia
        urgencia = self._detect_urgency(message_lower)
        
        # Decidir si necesita investigación o clarificación
        requiere_investigacion = self._needs_research(tipo_tarea, nivel_detalle, specs)
        requiere_clarificacion = self._needs_clarification(tipo_tarea, nivel_detalle, specs)
        
        return IntentAnalysis(
            tipo_tarea=tipo_tarea,
            contexto=contexto,
            especificaciones_usuario=specs,
            requiere_investigacion=requiere_investigacion,
            requiere_clarificacion=requiere_clarificacion,
            nivel_detalle=nivel_detalle,
            keywords=keywords,
            idioma=idioma,
            urgencia=urgencia
        )
    
    def _detect_task_type(self, message: str) -> TaskType:
        """Detecta el tipo de tarea basándose en patrones"""
        for task_type, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return task_type
        return TaskType.CONSULTA_GENERAL
    
    def _extract_context(self, message: str) -> str:
        """Extrae el contexto del negocio/proyecto usando puntuación"""
        context_scores = {}
        
        for context_name, keywords in self.CONTEXT_KEYWORDS.items():
            score = 0
            for kw in keywords:
                if kw in message:
                    score += len(kw)
            if score > 0:
                context_scores[context_name] = score
        
        if not context_scores:
            return "general"
        
        return max(context_scores.keys(), key=lambda x: context_scores[x])
    
    def _extract_specifications(self, message: str) -> Dict[str, Any]:
        """Extrae especificaciones mencionadas"""
        specs = {
            "colores": [],
            "secciones": [],
            "funcionalidades": [],
            "estilo": None,
            "recursos_disponibles": [],
            "objetivo": None
        }
        
        # Detectar colores mencionados
        color_patterns = [
            r"color(?:es)?\s*(?:como\s*)?(azul|rojo|verde|negro|blanco|dorado|morado|naranja)",
            r"(azul|rojo|verde|negro|blanco|dorado|morado|naranja)\s*y\s*(azul|rojo|verde|negro|blanco|dorado|morado|naranja)"
        ]
        for pattern in color_patterns:
            matches = re.findall(pattern, message.lower())
            if matches:
                if isinstance(matches[0], tuple):
                    specs["colores"].extend(list(matches[0]))
                else:
                    specs["colores"].extend(matches)
        
        # Detectar secciones mencionadas
        section_keywords = ["hero", "menú", "contacto", "about", "servicios", "productos", 
                          "testimonios", "galería", "precios", "equipo", "faq"]
        for kw in section_keywords:
            if kw in message.lower():
                specs["secciones"].append(kw)
        
        # Detectar estilo
        style_keywords = {
            "minimalista": ["minimalista", "minimal", "simple", "limpio"],
            "moderno": ["moderno", "contemporáneo", "actual"],
            "elegante": ["elegante", "lujoso", "premium", "sofisticado"],
            "colorido": ["colorido", "vibrante", "llamativo"],
            "corporativo": ["corporativo", "profesional", "formal"],
            "oscuro": ["oscuro", "dark", "negro"],
            "claro": ["claro", "light", "blanco"]
        }
        for style, keywords in style_keywords.items():
            for kw in keywords:
                if kw in message.lower():
                    specs["estilo"] = style
                    break
        
        # Detectar recursos disponibles
        if any(kw in message.lower() for kw in ["tengo logo", "tengo fotos", "tengo imágenes"]):
            specs["recursos_disponibles"].append("imagenes")
        if any(kw in message.lower() for kw in ["tengo textos", "tengo contenido"]):
            specs["recursos_disponibles"].append("contenido")
        
        # Detectar objetivo
        objective_patterns = {
            "vender": ["vender", "ventas", "comprar", "ecommerce"],
            "contacto": ["contactar", "contacto", "llamar", "whatsapp"],
            "informar": ["informar", "mostrar", "presentar", "portfolio"],
            "reservar": ["reservar", "cita", "agenda", "booking"]
        }
        for obj, keywords in objective_patterns.items():
            for kw in keywords:
                if kw in message.lower():
                    specs["objetivo"] = obj
                    break
        
        return specs
    
    def _evaluate_detail_level(self, message: str, specs: Dict) -> str:
        """Evalúa cuánto detalle proporcionó el usuario"""
        score = 0
        
        # Longitud del mensaje
        if len(message) > 200:
            score += 2
        elif len(message) > 100:
            score += 1
        
        # Especificaciones encontradas
        if specs["colores"]:
            score += 1
        if specs["secciones"]:
            score += len(specs["secciones"]) // 2
        if specs["estilo"]:
            score += 1
        if specs["objetivo"]:
            score += 1
        if specs["recursos_disponibles"]:
            score += 1
        
        if score >= 5:
            return "alto"
        elif score >= 3:
            return "medio"
        elif score >= 1:
            return "bajo"
        else:
            return "vago"
    
    def _extract_keywords(self, message: str) -> List[str]:
        """Extrae palabras clave del mensaje"""
        stop_words = {"quiero", "necesito", "para", "una", "un", "que", "con", "de", "la", "el", "mi", "me"}
        words = re.findall(r'\b\w+\b', message.lower())
        return [w for w in words if len(w) > 3 and w not in stop_words][:10]
    
    def _detect_language(self, message: str) -> str:
        """Detecta el idioma del mensaje"""
        spanish_words = {"quiero", "necesito", "para", "página", "sitio", "negocio", "crear"}
        english_words = {"want", "need", "website", "page", "create", "build"}
        
        message_words = set(message.lower().split())
        spanish_count = len(message_words & spanish_words)
        english_count = len(message_words & english_words)
        
        return "es" if spanish_count >= english_count else "en"
    
    def _detect_urgency(self, message: str) -> str:
        """Detecta la urgencia del pedido"""
        urgent_words = ["urgente", "rápido", "ya", "hoy", "ahora", "pronto", "asap"]
        if any(w in message for w in urgent_words):
            return "alta"
        return "media"
    
    def _needs_research(self, task_type: TaskType, detail_level: str, specs: Dict) -> bool:
        """Decide si necesita investigación"""
        # Tareas de creación con poco detalle necesitan investigación
        creation_tasks = {TaskType.CREAR_WEB, TaskType.CREAR_LANDING, TaskType.CREAR_DASHBOARD}
        if task_type in creation_tasks and detail_level in ["vago", "bajo"]:
            return True
        return False
    
    def _needs_clarification(self, task_type: TaskType, detail_level: str, specs: Dict) -> bool:
        """Decide si necesita clarificación del usuario"""
        # Si es tarea de creación y no tiene objetivo claro
        creation_tasks = {TaskType.CREAR_WEB, TaskType.CREAR_LANDING, TaskType.CREAR_DASHBOARD}
        if task_type in creation_tasks:
            if not specs.get("objetivo"):
                return True
            if detail_level == "vago":
                return True
        return False


class ResearchEngine:
    """
    FASE 2: Motor de Investigación Autónoma
    Genera recomendaciones basadas en mejores prácticas
    (Sin scraping real - usa conocimiento interno optimizado)
    """
    
    # Base de conocimiento de mejores prácticas por contexto
    BEST_PRACTICES = {
        "restaurante": {
            "elementos": ["hero con foto de plato estrella", "menú visual", "horarios", 
                         "ubicación con mapa", "reservas online", "galería de fotos", "reseñas"],
            "paleta": ["#3E2723", "#EFEBE9", "#D7CCC8", "#795548", "#BCAAA4"],
            "estilo": "cálido-acogedor",
            "insights": "Las mejores webs de restaurantes usan fotos de alta calidad de sus platos, " +
                       "menú fácil de leer, y botón de reserva/WhatsApp prominente. " +
                       "El 70% de usuarios visitan desde móvil para ver menú y ubicación.",
            "practicas": [
                "Fotos profesionales de platos (mínimo 5)",
                "Menú con precios visibles",
                "Botón de WhatsApp/llamar flotante",
                "Mapa de ubicación interactivo",
                "Horarios claros y actualizados"
            ]
        },
        "ecommerce": {
            "elementos": ["hero con producto destacado", "categorías", "productos destacados",
                         "carrito", "filtros de búsqueda", "reviews", "checkout"],
            "paleta": ["#1A1A2E", "#16213E", "#E94560", "#FFFFFF", "#0F3460"],
            "estilo": "moderno-confiable",
            "insights": "Las tiendas online exitosas priorizan velocidad de carga, fotos de producto " +
                       "de alta calidad desde múltiples ángulos, y checkout simplificado. " +
                       "Botones de compra claros y urgencia aumentan conversión 30%.",
            "practicas": [
                "Imágenes de producto en alta resolución",
                "Precios claros con descuentos visibles",
                "Botón 'Añadir al carrito' prominente",
                "Reviews de clientes",
                "Envío gratis destacado si aplica"
            ]
        },
        "portfolio": {
            "elementos": ["hero con nombre/título", "proyectos destacados", "sobre mí",
                         "skills/tecnologías", "contacto", "testimonios"],
            "paleta": ["#0D1117", "#161B22", "#58A6FF", "#F0F6FC", "#238636"],
            "estilo": "minimalista-profesional",
            "insights": "Los portfolios más efectivos muestran 4-6 proyectos destacados con casos de estudio, " +
                       "demuestran expertise con stack tecnológico visual, y tienen CTA claro para contacto.",
            "practicas": [
                "Máximo 6 proyectos destacados",
                "Cada proyecto con problema/solución",
                "Stack tecnológico visual (iconos)",
                "Links a LinkedIn/GitHub",
                "Formulario de contacto simple"
            ]
        },
        "saas": {
            "elementos": ["hero con propuesta de valor", "features", "pricing", "testimonios",
                         "FAQ", "CTA de registro", "demo/video"],
            "paleta": ["#0F172A", "#1E293B", "#3B82F6", "#FFFFFF", "#10B981"],
            "estilo": "moderno-tech",
            "insights": "Las landing pages SaaS más exitosas tienen una propuesta de valor clara en 5 palabras, " +
                       "muestran el producto en acción (video/gif), y tienen máximo 3 planes de precios.",
            "practicas": [
                "Headline clara de 5-7 palabras",
                "Demo del producto visible",
                "3 planes de precio máximo",
                "Social proof (logos clientes)",
                "CTA de 'Prueba gratis' prominente"
            ]
        },
        "fintech": {
            "elementos": ["hero con propuesta seguridad", "features", "seguridad/certificaciones",
                         "how it works", "testimonios", "app download"],
            "paleta": ["#0B0E11", "#12161C", "#F0B90B", "#FFFFFF", "#22C55E"],
            "estilo": "neo-bank-oscuro",
            "insights": "Las apps fintech priorizan la sensación de seguridad y modernidad. " +
                       "Uso de colores oscuros con acentos brillantes transmite confianza y tecnología. " +
                       "Glass morphism y animaciones sutiles son trending.",
            "practicas": [
                "Indicadores de seguridad prominentes",
                "Interfaz dark mode por defecto",
                "Animaciones suaves en números",
                "Gráficos de crecimiento/rendimiento",
                "Badges de certificación/regulación"
            ]
        },
        "general": {
            "elementos": ["hero", "servicios/features", "sobre nosotros", "contacto"],
            "paleta": ["#1F2937", "#374151", "#3B82F6", "#FFFFFF", "#10B981"],
            "estilo": "profesional-moderno",
            "insights": "Para cualquier tipo de web, los principios fundamentales son: " +
                       "claridad en la propuesta de valor, navegación intuitiva, responsive design, " +
                       "y CTA visibles.",
            "practicas": [
                "Hero claro con propuesta de valor",
                "Navegación simple (máx 5 items)",
                "Mobile-first design",
                "Tiempos de carga < 3 segundos",
                "CTA visible above the fold"
            ]
        }
    }
    
    def research(self, intent: IntentAnalysis) -> ResearchResult:
        """Realiza la investigación basada en el contexto"""
        context = intent.contexto if intent.contexto in self.BEST_PRACTICES else "general"
        practices = self.BEST_PRACTICES[context]
        
        # Combinar con estilo preferido del usuario si existe
        estilo = intent.especificaciones_usuario.get("estilo") or practices["estilo"]
        
        # Ajustar paleta según preferencias
        paleta = practices["paleta"].copy()
        user_colors = intent.especificaciones_usuario.get("colores", [])
        if user_colors:
            # El usuario mencionó colores, ajustar insights
            pass
        
        return ResearchResult(
            referencias=[
                f"Mejores prácticas para {context} 2024",
                f"Tendencias de diseño {estilo}",
                "Patrones de conversión web"
            ],
            elementos_recomendados=practices["elementos"],
            paleta_sugerida=paleta,
            estilo=estilo,
            insights=practices["insights"],
            mejores_practicas=practices["practicas"]
        )


class ClarificationManager:
    """
    FASE 3: Sistema de Clarificación Inteligente
    Genera preguntas relevantes basadas en lo que falta
    """
    
    QUESTION_TEMPLATES = {
        "objetivo": "¿Cuál es el objetivo principal? ¿Qué quieres que hagan los visitantes? (comprar, contactar, informarse, etc.)",
        "recursos": "¿Tienes recursos disponibles? (logo, fotos, textos del negocio)",
        "estilo": "¿Hay algún estilo de diseño que te guste o no te guste? (minimalista, colorido, oscuro, etc.)",
        "secciones": "¿Qué secciones necesitas? (menú, galería, precios, contacto, etc.)",
        "referencia": "¿Hay alguna web que te guste como referencia?",
        "funcionalidad": "¿Necesitas alguna funcionalidad especial? (formulario, mapa, reservas, chat)",
        "publico": "¿Quién es tu público objetivo?",
        "diferenciador": "¿Qué hace único a tu negocio/producto?"
    }
    
    def generate_questions(self, intent: IntentAnalysis, research: Optional[ResearchResult] = None) -> List[str]:
        """Genera preguntas basadas en lo que falta por clarificar"""
        questions = []
        specs = intent.especificaciones_usuario
        
        # Priorizar preguntas según lo que falta
        if not specs.get("objetivo"):
            questions.append(self.QUESTION_TEMPLATES["objetivo"])
        
        if not specs.get("recursos_disponibles"):
            questions.append(self.QUESTION_TEMPLATES["recursos"])
        
        if not specs.get("estilo"):
            questions.append(self.QUESTION_TEMPLATES["estilo"])
        
        # Máximo 3 preguntas para no abrumar
        return questions[:3]
    
    def format_clarification_message(self, intent: IntentAnalysis, research: Optional[ResearchResult], 
                                     questions: List[str]) -> str:
        """Formatea el mensaje de clarificación para el usuario"""
        message = ""
        
        # Si hay investigación, mostrar insights
        if research:
            message += f"📊 **Basándome en mi investigación sobre {intent.contexto}:**\n\n"
            message += f"Las mejores páginas de este tipo incluyen:\n"
            for elem in research.elementos_recomendados[:5]:
                message += f"• {elem.capitalize()}\n"
            message += "\n"
        
        message += "🤔 **Antes de continuar, necesito saber:**\n\n"
        for i, q in enumerate(questions, 1):
            message += f"{i}. {q}\n\n"
        
        return message
    
    def process_response(self, user_response: str, pending_questions: List[str]) -> ClarificationResult:
        """Procesa la respuesta del usuario a las preguntas"""
        respuestas = {}
        preferencias = {}
        
        response_lower = user_response.lower()
        
        # Analizar objetivo
        if "comprar" in response_lower or "vender" in response_lower:
            preferencias["objetivo"] = "venta"
        elif "contactar" in response_lower or "whatsapp" in response_lower or "llamar" in response_lower:
            preferencias["objetivo"] = "contacto"
        elif "informar" in response_lower or "ver" in response_lower or "mostrar" in response_lower:
            preferencias["objetivo"] = "informativo"
        elif "reservar" in response_lower or "cita" in response_lower:
            preferencias["objetivo"] = "reservas"
        
        # Analizar recursos
        if "tengo" in response_lower:
            if "logo" in response_lower:
                preferencias["tiene_logo"] = True
            if "foto" in response_lower:
                preferencias["tiene_fotos"] = True
        
        # Analizar estilo
        if "minimalista" in response_lower or "simple" in response_lower:
            preferencias["estilo"] = "minimalista"
        elif "oscuro" in response_lower or "dark" in response_lower:
            preferencias["estilo"] = "oscuro"
        elif "colorido" in response_lower or "vibrante" in response_lower:
            preferencias["estilo"] = "colorido"
        
        respuestas["raw"] = user_response
        
        return ClarificationResult(
            preguntas_realizadas=len(pending_questions),
            respuestas_usuario=respuestas,
            clarificacion_completa=True,
            preferencias_detectadas=preferencias
        )


class PromptBuilder:
    """
    FASE 4: Constructor del Prompt Maestro
    Combina toda la información en un super-prompt optimizado
    """
    
    def build(self, intent: IntentAnalysis, research: Optional[ResearchResult], 
              clarification: Optional[ClarificationResult]) -> str:
        """Construye el prompt maestro optimizado"""
        
        # Determinar contexto y objetivo
        contexto = intent.contexto
        objetivo = intent.especificaciones_usuario.get("objetivo", "informativo")
        
        if clarification and clarification.preferencias_detectadas:
            objetivo = clarification.preferencias_detectadas.get("objetivo", objetivo)
        
        # Determinar estilo
        estilo = intent.especificaciones_usuario.get("estilo", "moderno")
        if clarification and clarification.preferencias_detectadas.get("estilo"):
            estilo = clarification.preferencias_detectadas["estilo"]
        elif research:
            estilo = research.estilo
        
        # Determinar paleta
        paleta = research.paleta_sugerida if research else ["#1F2937", "#3B82F6", "#FFFFFF"]
        
        # Determinar secciones
        secciones = intent.especificaciones_usuario.get("secciones", [])
        if not secciones and research:
            secciones = research.elementos_recomendados[:5]
        
        # Construir el prompt
        prompt = f"""[PROMPT MAESTRO - GENERACIÓN DE CÓDIGO]

═══════════════════════════════════════════════════════════════
CONTEXTO DEL PROYECTO
═══════════════════════════════════════════════════════════════
- Tipo: {intent.tipo_tarea.value}
- Contexto: {contexto}
- Objetivo principal: {objetivo}
- Idioma del usuario: {intent.idioma}

═══════════════════════════════════════════════════════════════
ESPECIFICACIONES DE DISEÑO
═══════════════════════════════════════════════════════════════
- Estilo visual: {estilo}
- Paleta de colores: {', '.join(paleta)}
- Keywords del usuario: {', '.join(intent.keywords[:5])}

═══════════════════════════════════════════════════════════════
SECCIONES REQUERIDAS
═══════════════════════════════════════════════════════════════
"""
        for i, seccion in enumerate(secciones, 1):
            prompt += f"{i}. {seccion.capitalize()}\n"
        
        if research:
            prompt += f"""
═══════════════════════════════════════════════════════════════
MEJORES PRÁCTICAS A APLICAR
═══════════════════════════════════════════════════════════════
"""
            for practica in research.mejores_practicas[:5]:
                prompt += f"• {practica}\n"
        
        prompt += f"""
═══════════════════════════════════════════════════════════════
REQUISITOS TÉCNICOS OBLIGATORIOS
═══════════════════════════════════════════════════════════════
1. Mobile-first y 100% responsive
2. HTML5 semántico con accesibilidad
3. CSS moderno con variables
4. JavaScript ES6+ para interactividad
5. Optimizado para carga rápida
6. Sin dependencias externas innecesarias

═══════════════════════════════════════════════════════════════
FORMATO DE SALIDA
═══════════════════════════════════════════════════════════════
Genera el código completo en formato JSON:
{{
    "files": {{
        "index.html": "<!DOCTYPE html>...",
        "styles.css": "/* CSS completo */",
        "script.js": "// JS si es necesario"
    }},
    "message": "Explicación de lo creado y sugerencias"
}}
"""
        
        return prompt


class TaskOrchestrator:
    """
    FASE 5-6: Orquestador de Tareas y Ejecución
    Divide el trabajo en tareas y controla la ejecución
    """
    
    def create_plan(self, intent: IntentAnalysis, research: Optional[ResearchResult]) -> ExecutionPlan:
        """Crea el plan de ejecución basado en el análisis"""
        tareas = []
        archivos = []
        
        # Determinar tareas según el tipo
        if intent.tipo_tarea in [TaskType.CREAR_WEB, TaskType.CREAR_LANDING, TaskType.CREAR_DASHBOARD]:
            tareas = [
                TaskItem(1, "Crear estructura HTML con secciones", "pendiente", "index.html"),
                TaskItem(2, "Diseñar estilos CSS responsivos", "pendiente", "styles.css"),
                TaskItem(3, "Implementar interactividad JavaScript", "pendiente", "script.js"),
                TaskItem(4, "Optimizar para mobile y rendimiento", "pendiente"),
                TaskItem(5, "Verificar accesibilidad y SEO básico", "pendiente"),
            ]
            archivos = ["index.html", "styles.css", "script.js"]
        elif intent.tipo_tarea == TaskType.CREAR_FORMULARIO:
            tareas = [
                TaskItem(1, "Crear formulario HTML con validación", "pendiente", "index.html"),
                TaskItem(2, "Estilos del formulario", "pendiente", "styles.css"),
                TaskItem(3, "Validación JavaScript", "pendiente", "script.js"),
            ]
            archivos = ["index.html", "styles.css", "script.js"]
        else:
            tareas = [
                TaskItem(1, "Analizar requerimiento", "pendiente"),
                TaskItem(2, "Implementar solución", "pendiente"),
                TaskItem(3, "Verificar resultado", "pendiente"),
            ]
        
        # Estimar tiempo
        tiempo = f"{len(tareas) * 2} minutos aprox."
        
        # Identificar riesgos
        riesgos = []
        if intent.nivel_detalle == "vago":
            riesgos.append("Especificaciones vagas - resultado puede necesitar ajustes")
        if not intent.especificaciones_usuario.get("recursos_disponibles"):
            riesgos.append("Sin recursos (logo/fotos) - se usarán placeholders")
        
        return ExecutionPlan(
            tareas=tareas,
            tiempo_estimado=tiempo,
            riesgos=riesgos if riesgos else ["Ninguno identificado"],
            archivos_a_crear=archivos,
            dependencias=[]
        )
    
    def format_plan_message(self, plan: ExecutionPlan) -> str:
        """Formatea el plan para mostrar al usuario"""
        message = "📋 **PLAN DE EJECUCIÓN**\n\n"
        message += "**Tareas a realizar:**\n"
        for tarea in plan.tareas:
            message += f"  {tarea.id}. {tarea.descripcion}\n"
        
        message += f"\n⏱️ **Tiempo estimado:** {plan.tiempo_estimado}\n"
        
        if plan.archivos_a_crear:
            message += f"\n📁 **Archivos a crear:**\n"
            for archivo in plan.archivos_a_crear:
                message += f"  • {archivo}\n"
        
        if plan.riesgos:
            message += f"\n⚠️ **Consideraciones:**\n"
            for riesgo in plan.riesgos:
                message += f"  • {riesgo}\n"
        
        message += "\n¿Procedo con la generación? (sí/no/ajustar)"
        
        return message


class OutputVerifier:
    """
    FASE 7: Verificador de Salidas
    Valida que el código generado sea correcto y completo
    """
    
    def verify(self, files: Dict[str, str], intent: IntentAnalysis, 
               plan: ExecutionPlan) -> VerificationResult:
        """Verifica el código generado"""
        errores = []
        advertencias = []
        puntuacion = 100
        
        # Verificar que existan los archivos esperados
        for archivo_esperado in plan.archivos_a_crear:
            if archivo_esperado not in files:
                errores.append(f"Archivo faltante: {archivo_esperado}")
                puntuacion -= 20
        
        # Verificar HTML
        html_content = files.get("index.html", "")
        if html_content:
            # Verificar estructura básica
            if "<!DOCTYPE html>" not in html_content:
                advertencias.append("Falta <!DOCTYPE html>")
                puntuacion -= 5
            if "<meta name=\"viewport\"" not in html_content:
                advertencias.append("Falta meta viewport para responsive")
                puntuacion -= 10
            if "</html>" not in html_content:
                errores.append("HTML incompleto - falta cierre </html>")
                puntuacion -= 15
            
            # Verificar secciones requeridas
            secciones_usuario = intent.especificaciones_usuario.get("secciones", [])
            for seccion in secciones_usuario:
                if seccion.lower() not in html_content.lower():
                    advertencias.append(f"Posible sección faltante: {seccion}")
                    puntuacion -= 5
        
        # Verificar CSS
        css_content = files.get("styles.css", "")
        if css_content:
            if "@media" not in css_content:
                advertencias.append("No se detectan media queries - verificar responsive")
                puntuacion -= 10
            if ":root" not in css_content:
                advertencias.append("No se usan variables CSS")
                puntuacion -= 5
        
        # Verificar JS
        js_content = files.get("script.js", "")
        if js_content:
            if "var " in js_content and "const " not in js_content and "let " not in js_content:
                advertencias.append("Usar const/let en lugar de var")
                puntuacion -= 5
        
        # Calcular flags booleanos
        sintaxis_valida = len([e for e in errores if "incompleto" in e.lower()]) == 0
        completitud = len(errores) == 0
        funcionalidad = len([e for e in errores if "faltante" in e.lower()]) == 0
        responsive = "@media" in css_content if css_content else False
        coincide = puntuacion >= 70
        
        return VerificationResult(
            sintaxis_valida=sintaxis_valida,
            completitud=completitud,
            funcionalidad=funcionalidad,
            responsive=responsive,
            coincide_requisitos=coincide,
            errores=errores,
            advertencias=advertencias,
            puntuacion=max(0, puntuacion)
        )
    
    def format_verification_message(self, result: VerificationResult) -> str:
        """Formatea el resultado de verificación"""
        message = "🔍 **VERIFICACIÓN AUTOMÁTICA**\n\n"
        
        checks = [
            ("Sintaxis válida", result.sintaxis_valida),
            ("Código completo", result.completitud),
            ("Funcionalidad OK", result.funcionalidad),
            ("Diseño responsive", result.responsive),
            ("Cumple requisitos", result.coincide_requisitos),
        ]
        
        for check_name, passed in checks:
            icon = "✅" if passed else "❌"
            message += f"{icon} {check_name}\n"
        
        message += f"\n📊 **Puntuación:** {result.puntuacion}/100\n"
        
        if result.errores:
            message += "\n🔴 **Errores encontrados:**\n"
            for error in result.errores:
                message += f"  • {error}\n"
        
        if result.advertencias:
            message += "\n🟡 **Advertencias:**\n"
            for adv in result.advertencias:
                message += f"  • {adv}\n"
        
        return message


class AIConstructorService:
    """
    Servicio Principal del Constructor de IA
    Orquesta todas las fases y mantiene el estado de las sesiones
    """
    
    def __init__(self, ai_service=None, db_manager=None):
        self.ai_service = ai_service
        self.db_manager = db_manager
        self.sessions: Dict[str, ConstructorSession] = {}
        
        # Inicializar componentes
        self.intent_parser = IntentParser()
        self.research_engine = ResearchEngine()
        self.clarification_manager = ClarificationManager()
        self.prompt_builder = PromptBuilder()
        self.task_orchestrator = TaskOrchestrator()
        self.output_verifier = OutputVerifier()
        
        logger.info("AIConstructorService initialized with all components")
    
    def get_or_create_session(self, user_id: str) -> ConstructorSession:
        """Obtiene o crea una sesión para el usuario"""
        session_id = f"constructor_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if user_id not in self.sessions:
            self.sessions[user_id] = ConstructorSession(
                session_id=session_id,
                user_id=user_id,
                fase_actual=1
            )
        
        return self.sessions[user_id]
    
    def reset_session(self, user_id: str) -> ConstructorSession:
        """Reinicia la sesión del usuario"""
        session_id = f"constructor_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.sessions[user_id] = ConstructorSession(
            session_id=session_id,
            user_id=user_id,
            fase_actual=1
        )
        return self.sessions[user_id]
    
    def process_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario a través del flujo de fases
        Retorna la respuesta y el estado actual
        """
        session = self.get_or_create_session(user_id)
        
        # Guardar mensaje en historial
        session.historial.append({"role": "user", "content": message, "timestamp": datetime.now().isoformat()})
        
        # Si estaba esperando clarificación, procesarla
        if session.esperando_clarificacion:
            return self._process_clarification_response(session, message)
        
        # Si estaba esperando confirmación del plan
        if session.esperando_confirmacion:
            return self._process_confirmation(session, message)
        
        # Nuevo flujo desde fase 1
        return self._run_full_flow(session, message)
    
    def _run_full_flow(self, session: ConstructorSession, message: str) -> Dict[str, Any]:
        """Ejecuta el flujo completo de fases"""
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 1: ANÁLISIS INICIAL
        # ═══════════════════════════════════════════════════════════════
        session.fase_actual = 1
        intent = self.intent_parser.analyze(message)
        session.intent = intent
        
        logger.info(f"[FASE 1] Intent analizado: {intent.tipo_tarea.value}, contexto: {intent.contexto}")
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 2: INVESTIGACIÓN (si es necesaria)
        # ═══════════════════════════════════════════════════════════════
        research = None
        if intent.requiere_investigacion:
            session.fase_actual = 2
            research = self.research_engine.research(intent)
            session.research = research
            logger.info(f"[FASE 2] Investigación completada: {research.estilo}")
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 3: CLARIFICACIÓN (si es necesaria)
        # ═══════════════════════════════════════════════════════════════
        if intent.requiere_clarificacion:
            session.fase_actual = 3
            questions = self.clarification_manager.generate_questions(intent, research)
            
            if questions:
                session.preguntas_pendientes = questions
                session.esperando_clarificacion = True
                
                clarification_msg = self.clarification_manager.format_clarification_message(
                    intent, research, questions
                )
                
                return {
                    "success": True,
                    "response": clarification_msg,
                    "fase": session.fase_actual,
                    "fase_nombre": "Clarificación",
                    "esperando_input": True,
                    "session": session.to_dict()
                }
        
        # Si no necesita clarificación, continuar al plan
        return self._continue_to_plan(session)
    
    def _process_clarification_response(self, session: ConstructorSession, response: str) -> Dict[str, Any]:
        """Procesa la respuesta de clarificación del usuario"""
        clarification = self.clarification_manager.process_response(
            response, session.preguntas_pendientes
        )
        session.clarification = clarification
        session.esperando_clarificacion = False
        session.preguntas_pendientes = []
        
        logger.info(f"[FASE 3] Clarificación procesada: {clarification.preferencias_detectadas}")
        
        return self._continue_to_plan(session)
    
    def _continue_to_plan(self, session: ConstructorSession) -> Dict[str, Any]:
        """Continúa con las fases 4 y 5: Prompt y Plan"""
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 4: CONSTRUCCIÓN DEL PROMPT MAESTRO
        # ═══════════════════════════════════════════════════════════════
        session.fase_actual = 4
        prompt_maestro = self.prompt_builder.build(
            session.intent, session.research, session.clarification
        )
        session.prompt_maestro = prompt_maestro
        
        logger.info(f"[FASE 4] Prompt maestro construido ({len(prompt_maestro)} chars)")
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 5: PRESENTACIÓN DEL PLAN
        # ═══════════════════════════════════════════════════════════════
        session.fase_actual = 5
        plan = self.task_orchestrator.create_plan(session.intent, session.research)
        session.plan = plan
        session.esperando_confirmacion = True
        
        plan_message = self.task_orchestrator.format_plan_message(plan)
        
        return {
            "success": True,
            "response": plan_message,
            "fase": session.fase_actual,
            "fase_nombre": "Presentación del Plan",
            "esperando_input": True,
            "plan": plan.to_dict(),
            "session": session.to_dict()
        }
    
    def _process_confirmation(self, session: ConstructorSession, response: str) -> Dict[str, Any]:
        """Procesa la confirmación del usuario para ejecutar"""
        response_lower = response.lower().strip()
        
        # Detectar confirmación
        confirmaciones = ["sí", "si", "dale", "procede", "ok", "adelante", "hazlo", "yes", "go"]
        rechazos = ["no", "cancelar", "parar", "stop", "espera"]
        
        if any(c in response_lower for c in rechazos):
            session.esperando_confirmacion = False
            return {
                "success": True,
                "response": "Entendido. ¿Qué te gustaría ajustar del plan? Puedes decirme los cambios o empezar de nuevo.",
                "fase": session.fase_actual,
                "cancelado": True,
                "session": session.to_dict()
            }
        
        if any(c in response_lower for c in confirmaciones):
            session.esperando_confirmacion = False
            return self._execute_generation(session)
        
        # No se entiende la respuesta
        return {
            "success": True,
            "response": "No entendí tu respuesta. Por favor responde 'sí' para proceder o 'no' para cancelar/ajustar.",
            "fase": session.fase_actual,
            "esperando_input": True,
            "session": session.to_dict()
        }
    
    def _execute_generation(self, session: ConstructorSession) -> Dict[str, Any]:
        """Ejecuta la generación del código (Fase 6)"""
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 6: EJECUCIÓN CONTROLADA
        # ═══════════════════════════════════════════════════════════════
        session.fase_actual = 6
        
        # Marcar tareas como en progreso
        for tarea in session.plan.tareas:
            tarea.estado = "en_progreso"
        
        # Usar el AI Service para generar el código
        if not self.ai_service:
            return {
                "success": False,
                "error": "No hay servicio de IA configurado",
                "fase": session.fase_actual,
                "session": session.to_dict()
            }
        
        # Construir mensaje con el prompt maestro
        generation_prompt = f"""Eres BUNK3R Code Builder. Genera el código completo siguiendo estas instrucciones:

{session.prompt_maestro}

IMPORTANTE: Responde ÚNICAMENTE con el JSON solicitado, sin texto adicional antes o después.
"""
        
        # Llamar al AI Service
        result = self.ai_service.chat(
            user_id=f"constructor_{session.user_id}",
            message=generation_prompt,
            enable_auto_rectify=True
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Error desconocido en la generación"),
                "fase": session.fase_actual,
                "session": session.to_dict()
            }
        
        # Parsear la respuesta para extraer los archivos
        response_text = result.get("response", "")
        files, parse_message = self._parse_generated_code(response_text)
        
        if not files:
            # Si no se pudo parsear, intentar de nuevo con instrucciones más claras
            return {
                "success": True,
                "response": f"He generado el código. Aquí está el resultado:\n\n{response_text}",
                "fase": session.fase_actual,
                "raw_response": True,
                "session": session.to_dict()
            }
        
        session.archivos_generados = files
        
        # Marcar tareas como completadas
        for tarea in session.plan.tareas:
            tarea.estado = "completada"
        
        logger.info(f"[FASE 6] Generación completada: {list(files.keys())}")
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 7: VERIFICACIÓN AUTOMÁTICA
        # ═══════════════════════════════════════════════════════════════
        session.fase_actual = 7
        verification = self.output_verifier.verify(files, session.intent, session.plan)
        session.verification = verification
        
        verification_msg = self.output_verifier.format_verification_message(verification)
        
        logger.info(f"[FASE 7] Verificación: {verification.puntuacion}/100")
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 8: ENTREGA FINAL
        # ═══════════════════════════════════════════════════════════════
        session.fase_actual = 8
        
        delivery_message = self._format_delivery(session, verification_msg, parse_message)
        
        return {
            "success": True,
            "response": delivery_message,
            "fase": session.fase_actual,
            "fase_nombre": "Entrega Final",
            "files": files,
            "verification": verification.to_dict(),
            "session": session.to_dict()
        }
    
    def _parse_generated_code(self, response: str) -> Tuple[Dict[str, str], str]:
        """Intenta parsear el código generado del response"""
        files = {}
        message = ""
        
        # Buscar JSON en la respuesta
        json_patterns = [
            r'\{[\s\S]*"files"[\s\S]*\}',  # Formato esperado
            r'```json\s*([\s\S]*?)\s*```',  # Código en bloque
            r'```\s*([\s\S]*?)\s*```'  # Cualquier bloque de código
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response)
            for match in matches:
                try:
                    # Limpiar el match
                    json_str = match if isinstance(match, str) else match
                    json_str = json_str.strip()
                    
                    # Intentar parsear
                    data = json.loads(json_str)
                    
                    if "files" in data:
                        files = data["files"]
                        message = data.get("message", "Código generado exitosamente")
                        return files, message
                except json.JSONDecodeError:
                    continue
        
        # Si no se encontró JSON, buscar bloques de código individuales
        html_match = re.search(r'```html\s*([\s\S]*?)\s*```', response)
        css_match = re.search(r'```css\s*([\s\S]*?)\s*```', response)
        js_match = re.search(r'```(?:javascript|js)\s*([\s\S]*?)\s*```', response)
        
        if html_match:
            files["index.html"] = html_match.group(1).strip()
        if css_match:
            files["styles.css"] = css_match.group(1).strip()
        if js_match:
            files["script.js"] = js_match.group(1).strip()
        
        if files:
            message = "Código extraído de bloques"
        
        return files, message
    
    def _format_delivery(self, session: ConstructorSession, verification_msg: str, 
                         ai_message: str) -> str:
        """Formatea el mensaje de entrega final"""
        message = "✨ **ENTREGA COMPLETADA**\n\n"
        
        # Resumen de lo creado
        if session.archivos_generados:
            message += "📁 **Archivos creados:**\n"
            for filename in session.archivos_generados.keys():
                message += f"  • {filename}\n"
            message += "\n"
        
        # Secciones implementadas
        if session.plan:
            completed = [t for t in session.plan.tareas if t.estado == "completada"]
            message += f"✅ **Tareas completadas:** {len(completed)}/{len(session.plan.tareas)}\n\n"
        
        # Verificación
        message += verification_msg
        message += "\n"
        
        # Mensaje del AI
        if ai_message:
            message += f"\n💬 **Notas:** {ai_message}\n"
        
        message += "\n¿Te gustaría que ajuste algo?"
        
        return message
    
    def get_session_status(self, user_id: str) -> Optional[Dict]:
        """Obtiene el estado de la sesión del usuario"""
        if user_id in self.sessions:
            return self.sessions[user_id].to_dict()
        return None
    
    def get_generated_files(self, user_id: str) -> Optional[Dict[str, str]]:
        """Obtiene los archivos generados en la sesión"""
        if user_id in self.sessions:
            return self.sessions[user_id].archivos_generados
        return None
