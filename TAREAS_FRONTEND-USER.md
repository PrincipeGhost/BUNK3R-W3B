# TAREAS AGENTE 🔵 FRONTEND USUARIO
**Rama Git:** `feature/frontend-user`
**Archivos asignados:** app.js, publications.js, virtual-numbers.js, utils.js, ai-chat.js, workspace.js, styles.css, ai-chat.css, workspace.css, templates/index.html, templates/virtual_numbers.html, templates/workspace.html

---

## SECCIÓN 31: VERIFICACIÓN DE FUNCIONALIDADES

### FASE 31.1: BOTONES SIN FUNCIONALIDAD ⏳ 🔴 CRÍTICA
**Tiempo:** 4 horas

**Objetivo:** Verificar y conectar todos los botones de la interfaz.

**Tareas:**
- [ ] Auditar todos los botones en index.html
- [ ] Verificar que cada onclick está conectado a una función
- [ ] Implementar funciones faltantes
- [ ] Agregar loading states a botones de acción
- [ ] Deshabilitar botones durante operaciones async

---

### FASE 31.3: NAVEGACIÓN INCONSISTENTE ⏳ 🟡 ALTA
**Tiempo:** 3 horas

**Objetivo:** Unificar el sistema de navegación.

**Tareas:**
- [ ] Crear sistema único de navegación en app.js
- [ ] Implementar back button con historial
- [ ] Agregar transiciones entre pantallas
- [ ] Manejar deep linking correctamente
- [ ] Agregar breadcrumbs donde aplique

---

### FASE 31.6: PWA COMPLETO ⏳ 🟠 MEDIA
**Tiempo:** 4 horas

**Objetivo:** Completar funcionalidad Progressive Web App.

**Tareas:**
- [ ] Verificar manifest.json completo
- [ ] Implementar service worker con caching
- [ ] Agregar offline fallback page
- [ ] Configurar push notifications
- [ ] Agregar install prompt

---

## SECCIÓN 32: LIMPIEZA Y OPTIMIZACIÓN

### FASE 32.1: ELIMINAR CONSOLE.LOG ⏳ 🟡 ALTA
**Tiempo:** 2 horas (parte frontend)

**Archivos afectados:**
- static/js/app.js (47 instancias)
- static/js/ai-chat.js (5 instancias)
- static/js/utils.js (2 instancias)
- static/js/publications.js (1 instancia)

**Tareas:**
- [ ] Crear wrapper Logger condicional en utils.js
- [ ] Reemplazar console.log por Logger en app.js
- [ ] Reemplazar console.log por Logger en ai-chat.js
- [ ] Reemplazar console.log por Logger en utils.js
- [ ] Reemplazar console.log por Logger en publications.js

---

### FASE 32.3: LIMPIAR DATOS DEMO ⏳ 🟠 MEDIA (parte frontend)
**Tiempo:** 1 hora

**Tareas:**
- [ ] Verificar que demo_user solo aparece sin usuario real
- [ ] Cambiar placeholder @demo_user por @usuario o vacío
- [ ] Documentar cuándo se usa el modo demo

---

### FASE 32.6: VALIDACIÓN INPUTS ⏳ 🟠 MEDIA (parte frontend)
**Tiempo:** 2 horas

**Tareas:**
- [ ] Validar formularios de login/registro
- [ ] Validar formularios de wallet (direcciones, montos)
- [ ] Validar formularios de publicaciones
- [ ] Agregar mensajes de error claros
- [ ] Prevenir envío de formularios inválidos

---

### FASE 32.7: OPTIMIZACIÓN CARGA ⏳ 🟢 BAJA
**Tiempo:** 2 horas

**Tareas:**
- [ ] Minificar archivos CSS en producción
- [ ] Minificar archivos JS en producción
- [ ] Implementar lazy loading para imágenes
- [ ] Agregar prefetch para rutas comunes
- [ ] Agregar loading skeleton mientras carga contenido

---

## SECCIÓN 33: FEATURES NUEVAS

### FASE 33.1: CHAT PRIVADO (parte frontend) ⏳ 🟠 MEDIA
**Tiempo:** 3 horas

**Tareas:**
- [ ] Crear UI de chat estilo Telegram
- [ ] Implementar lista de conversaciones
- [ ] Agregar indicadores de mensajes no leídos
- [ ] Crear input de mensaje con emojis

---

## SECCIÓN 29: CONFIGURACIÓN USUARIO

### FASE 29.1: ESTRUCTURA PRINCIPAL ⏳ 🔴 CRÍTICA
**Tiempo:** 2 horas

**Tareas:**
- [ ] Sidebar con iconos de cada sección
- [ ] Panel principal que cambia según sección
- [ ] Header con "Configuración" y botón de volver
- [ ] Animaciones de transición entre secciones

### FASE 29.2-29.10: SECCIONES DE CONFIGURACIÓN ⏳
**Tiempo:** 10+ horas

**Tareas:**
- [ ] Sección Cuenta (29.2)
- [ ] Sección Seguridad (29.3)
- [ ] Sección Privacidad (29.4)
- [ ] Sección Notificaciones (29.5)
- [ ] Sección Apariencia (29.6)
- [ ] Sección Wallet (29.7)
- [ ] Sección Datos y Almacenamiento (29.8)
- [ ] Sección Ayuda (29.9)
- [ ] Cerrar Sesión y Eliminar (29.10)

---

## SECCIÓN 34: AI CONSTRUCTOR (parte frontend)

### FASE 34.x: FRONTEND AI CONSTRUCTOR ⏳ 🔴 CRÍTICA
**Tiempo:** 8+ horas

**Objetivo:** Conectar ai-chat.js con ai_constructor.py (8 fases)

**Tareas:**
- [ ] Cambiar endpoint de /api/ai/code-builder a /api/ai-constructor/process
- [ ] Implementar visualización de fases en el chat
- [ ] Mostrar progreso de cada fase en UI
- [ ] Actualizar preview en tiempo real
- [ ] Mostrar archivos creados en panel derecho
- [ ] Implementar streaming de respuestas

---

## RESUMEN DE HORAS ESTIMADAS

| Sección | Horas |
|---------|-------|
| 31.1 Botones | 4h |
| 31.3 Navegación | 3h |
| 31.6 PWA | 4h |
| 32.1 Console.log | 2h |
| 32.3 Datos demo | 1h |
| 32.6 Validación | 2h |
| 32.7 Optimización | 2h |
| 33.1 Chat privado | 3h |
| 29.x Configuración | 12h |
| 34.x AI Constructor | 8h |
| **TOTAL** | **~41 horas** |

---

## ORDEN RECOMENDADO

1. 🔴 **CRÍTICO:** 31.1 → 34.x → 29.1
2. 🟡 **ALTA:** 31.3 → 32.1
3. 🟠 **MEDIA:** 31.6 → 32.3 → 32.6 → 33.1
4. 🟢 **BAJA:** 32.7
