# PROMPT_PENDIENTES_BUNK3R-W3B.md

---

## 🚀 MENÚ DE INICIO
Al iniciar cada sesión, el agente DEBE preguntar:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 ¿Qué quieres hacer?
1️⃣ CONTINUAR    → Retomo la siguiente sección pendiente
2️⃣ NUEVO PROMPT → Agrega nueva tarea/funcionalidad  
3️⃣ VER PROGRESO → Muestra estado actual del proyecto
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Esperando tu respuesta...
```

---

## 📊 ESTADO GENERAL DEL PROYECTO

| Métrica | Valor |
|---------|-------|
| Proyecto | BUNK3R-W3B |
| Última actualización | 5 Diciembre 2025 |
| Sección actual | - |
| Total secciones | 14 |
| Completadas | 14 ✅ |
| Pendientes | 0 ⏳ |
| En progreso | 0 🔄 |

---

## 🔥 REGLAS BASE DEL AGENTE – OBLIGATORIAS

### 1. Comunicación de Progreso
```
INICIO:   "🔄 Comenzando sección [X]: [Nombre]"
FIN:      "✅ Completada sección [X]: [Nombre] | Pendientes: [lista]"
ERROR:    "⚠️ Problema en sección [X]: [Descripción]"
```

### 2. Verificación Obligatoria
Antes de marcar como completado, el agente DEBE:
- [ ] Probar la funcionalidad como usuario real
- [ ] Confirmar que no rompe funcionalidades previas
- [ ] Verificar comportamiento correcto de la UI
- [ ] Revisar logs y consola para errores ocultos
- [ ] Solo marcar completado cuando funcione al 100%

### 3. Normas de Desarrollo
- Código limpio, ordenado y legible
- Comentarios cuando sea adecuado
- Evitar complejidad innecesaria
- Detectar duplicaciones y refactorizar
- Mantener consistencia en estilo y arquitectura

### 4. Normas de Documentación
Actualizar replit.md con:
- Qué se hizo
- Qué falta
- Errores detectados
- Siguientes pasos
- Nuevas dependencias
- Cambios en arquitectura

### 5. Normas de Análisis
- Revisar estructura de carpetas
- Detectar archivos o código muerto
- Proponer mejoras de arquitectura
- Evaluar rendimiento
- Identificar redundancias

### 6. Normas de Interacción
- Pedir confirmación para cambios críticos
- Explicar claramente cada modificación
- No omitir detalles técnicos
- Proponer alternativas cuando existan

### 7. Normas de Seguridad
**NO HACER:**
- Eliminar archivos sin confirmación
- Cambios destructivos sin aprobación
- Exponer datos sensibles

**OBLIGATORIO:**
- Respaldo antes de cambios mayores
- Validar entradas del usuario
- Mantener integridad del proyecto

### 8. Actualización Continua
- Leer siempre replit.md antes de empezar
- Mantener sincronizados: código, documentación, progreso
- Corregir inconsistencias
- Registrar cada avance

### 9. Detección de Vulnerabilidades
Revisar cada cambio para detectar:
- Inyección SQL/XSS/CSRF
- Exposición de datos
- Accesos sin autorización
- Código inseguro o deprecated
- Dependencias vulnerables

### 10. Protocolo de Vulnerabilidad Detectada
Si se detecta vulnerabilidad → **DETENER TODO**

1. Explicar en chat:
   - Qué es la vulnerabilidad
   - Qué daño podría causar
   - Cómo se previene

2. Corregir inmediatamente

3. Registrar en replit.md:
```
### Seguridad / Auditoría
- Vulnerabilidad: [...]
- Riesgos: [...]
- Corrección: [...]
- Fecha: [...]
```

4. Reanalizar funciones relacionadas

---

## 📋 SECCIONES DE TRABAJO

### Leyenda de Estados:
| Símbolo | Significado |
|---------|-------------|
| ✅ | Completado |
| 🔄 | En progreso |
| ⏳ | Pendiente |
| ❌ | Bloqueado/Error |
| 🔒 | Requiere confirmación |

---

### SECCIÓN 1: Sistema de Publicaciones ✅
**Estado:** COMPLETADA (100%)

**Tareas completadas:**
- [x] Feed tiempo real (polling 45s)
- [x] Scroll infinito/paginación
- [x] Hashtags clickeables
- [x] Página Explore funcional
- [x] Trending hashtags
- [x] Eliminar historias propias
- [x] Tiempo restante expiración stories
- [x] "Visto por X personas" en stories
- [x] Reacciones a historias

---

### SECCIÓN 2: Navegación y UI ✅
**Estado:** COMPLETADA (100%)

**Tareas completadas:**
- [x] goToHome() refactorizado con detección dinámica de pantallas
- [x] Animaciones de transición entre páginas
- [x] Skeleton loaders en wallet, perfil y notificaciones
- [x] Badge de notificaciones en nav
- [x] Modales cierran al click fuera

---

### SECCIÓN 3: Wallet/BUNK3RCOIN ✅
**Estado:** COMPLETADA (100%)

**Tareas completadas:**
- [x] Historial de transacciones con filtros por tipo
- [x] Auto-actualizar balance después de cada transacción
- [x] Confirmación visual clara cuando se completa una recarga
- [x] Límite de intentos para verificación de pagos
- [x] Manejar pagos TON "pending" con timeout

---

### SECCIÓN 4: Base de Datos ✅
**Estado:** COMPLETADA (100%)

**Tareas completadas:**
- [x] Connection pooling
- [x] Índices en columnas frecuentes
- [x] Límite en get_tracking_history()
- [x] Caché para datos que cambian poco

---

### SECCIÓN 5: Perfiles de Usuario ✅
**Estado:** COMPLETADA (100%)

**Tareas completadas:**
- [x] Edición de bio/descripción
- [x] Grid de publicaciones propias en el perfil (estilo Instagram)
- [x] Página de seguidores/siguiendo navegable
- [x] Cropping/ajuste de avatar (Cropper.js)
- [x] Sistema de verificación de usuarios (badge verificado)

---

### SECCIÓN 6: Comentarios ✅
**Estado:** COMPLETADA (100%)

**Tareas completadas:**
- [x] Paginación de comentarios (load more)
- [x] Respuestas anidadas a comentarios
- [x] Editar comentario (límite 15 min)
- [x] Reacciones a comentarios individuales

---

### SECCIÓN 7: Notificaciones ✅
**Estado:** COMPLETADA (100%)

**Tareas completadas:**
- [x] Sistema de notificaciones in-app
- [x] Badge de notificaciones no leídas
- [x] Historial consultable
- [x] Preferencias de notificaciones
- [x] Notificaciones para transacciones

---

### SECCIÓN 8: [RESERVADA] ⏳
**Nota:** Sección 8 no existe en el proyecto original. Disponible para futuras tareas.

---

### SECCIÓN 9: Marketplace y Bots ✅
**Estado:** COMPLETADA (100%)

**Tareas completadas:**
- [x] Sistema de categorías para productos (campo category en bot_types)
- [x] Estado de activación de bots (toggle activo/inactivo)
  - API: /api/bots/{id}/toggle
  - UI: Toggle switch con estados visuales
  - Bots inactivos aparecen atenuados
- [x] Panel de configuración de bots comprados
  - API: /api/bots/{id}/config GET/POST
  - UI: Modal con opciones de notificaciones, frecuencia, modo silencioso
  - Configuración persistente en base de datos

---

### SECCIÓN 10: Números Virtuales ✅
**Estado:** COMPLETADA (100%)

**Tareas completadas:**
- [x] Backoff exponencial en polling (2s→4s→8s→16s→30s max)
  - Archivo: static/js/virtual-numbers.js
  - Función scheduleNextPoll() con setTimeout dinámico
  - Reset a 2s cuando se recibe SMS
- [x] Filtros en historial de órdenes
  - Filtro por estado (recibidos, pendientes, cancelados, expirados)
  - Filtro por servicio (dinámico desde datos)
  - Filtro por fecha (desde/hasta)

---

### SECCIÓN 11: Responsive/Móvil ✅
**Estado:** COMPLETADA (100%)

**Tareas completadas:**
- [x] Modales scrolleables en pantallas pequeñas
  - CSS: max-height: 90vh; overflow-y: auto
  - Todos los tipos de modal cubiertos
  - Sticky headers y footers en mobile
- [x] Sistema de toasts sin superposición
  - Toast container con flex-direction: column-reverse
  - Animaciones de entrada/salida
  - Toasts se apilan correctamente
- [x] Scroll automático al input enfocado (teclado móvil)
  - Archivo: static/js/utils.js - setupMobileKeyboardHandler()
  - Detecta apertura de teclado por cambio de viewport
  - scrollIntoView automático con delay de 300ms

---

### SECCIÓN 12: Memory Leaks ✅
**Estado:** COMPLETADA (100%)

**Tareas completadas:**
- [x] cleanup() general en App
- [x] clearInterval en múltiples lugares
- [x] removeEventListener implementado
- [x] _storyTimeout limpiado en closeStoryViewer()
- [x] debounceEstimate timeout limpiado al cerrar

---

### SECCIÓN 13: Race Conditions ✅
**Estado:** COMPLETADA (100%)

**Tareas completadas:**
- [x] RequestManager.cancel() en loadFeed()
- [x] Throttle en likes/save
- [x] Cancelar requests pendientes en búsqueda Explore

---

### SECCIÓN 14: Código Duplicado ✅
**Estado:** COMPLETADA (100%)

**Tareas completadas:**
- [x] getDeviceIcon consolidado
- [x] apiRequest y getAuthHeaders revisados

---

## 📝 HISTORIAL DE PROMPTS

| # | Fecha | Prompt del Usuario | Acción Tomada | Estado |
|---|-------|-------------------|---------------|--------|
| 1 | 05/12/2025 | Configuración inicial del sistema de pendientes | Creado archivo PROMPT_PENDIENTES con estructura completa | ✅ |

---

## 🔄 INSTRUCCIONES DE CONTINUACIÓN AUTOMÁTICA

Cuando el usuario diga "continúa", el agente DEBE:
1. Leer este archivo completo
2. Identificar la siguiente sección pendiente (⏳)
3. Informar: "🔄 Comenzando sección [X]: [Nombre]"
4. Ejecutar todas las tareas de esa sección
5. Verificar funcionamiento
6. Actualizar este archivo (marcar ✅, agregar notas)
7. Actualizar replit.md
8. Informar: "✅ Completada sección [X]. ¿Continúo con la siguiente?"

---

## ➕ INSTRUCCIONES PARA NUEVO PROMPT

Cuando el usuario agregue una nueva tarea:
1. Analizar el prompt del usuario
2. Determinar si es nueva sección o tarea dentro de sección existente
3. Agregar al archivo en el lugar correcto
4. Registrar en historial de prompts
5. Preguntar: "¿Ejecuto ahora o continúo con las secciones pendientes?"

---

## 📊 INSTRUCCIONES PARA VER PROGRESO

Cuando el usuario pida ver progreso, mostrar:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 PROGRESO DEL PROYECTO: BUNK3R-W3B
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Completadas: X/Y secciones (XX%)
🔄 En progreso: Sección [X] - [Nombre]
⏳ Pendientes: [Lista de secciones]
Última actividad: [Fecha] - [Descripción]
¿Qué quieres hacer?
1️⃣ Continuar trabajo
2️⃣ Ver detalle de sección específica
3️⃣ Agregar nueva tarea
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🎯 PLANTILLA RÁPIDA PARA NUEVA SECCIÓN

```markdown
### SECCIÓN [X]: [Nombre] ⏳
**Prioridad:** [Alta/Media/Baja]  
**Agregado:** [Fecha]  
**Origen:** [Prompt del usuario o sugerencia del agente]

**Tareas:**
- [ ] X.1 [Tarea]
- [ ] X.2 [Tarea]

**Criterios de aceptación:**
- [ ] [Criterio]

**Notas:**
> [Observaciones]
```

---

## 📌 NOTAS IMPORTANTES

- Este archivo es la **fuente de verdad** del proyecto
- El agente **SIEMPRE** debe leerlo al iniciar
- Cualquier cambio importante debe quedar registrado aquí
- El usuario puede modificar prioridades en cualquier momento
- Las reglas base son **OBLIGATORIAS** y **PERMANENTES**

---

## 📈 RESUMEN FINAL

### TODAS LAS SECCIONES COMPLETADAS:
- ✅ **Sección 1** - Publicaciones (100%)
- ✅ **Sección 2** - Navegación/UI (100%)
- ✅ **Sección 3** - Wallet/BUNK3RCOIN (100%)
- ✅ **Sección 4** - Base de datos (100%)
- ✅ **Sección 5** - Perfiles de usuario (100%)
- ✅ **Sección 6** - Comentarios (100%)
- ✅ **Sección 7** - Notificaciones (100%)
- ✅ **Sección 9** - Marketplace y Bots (100%)
- ✅ **Sección 10** - Números virtuales (100%)
- ✅ **Sección 11** - Responsive/Móvil (100%)
- ✅ **Sección 12** - Memory leaks (100%)
- ✅ **Sección 13** - Race conditions (100%)
- ✅ **Sección 14** - Código duplicado (100%)

### 🏆 PROYECTO COMPLETADO AL 100%

**Siguiente paso:** Agregar nuevas funcionalidades usando el menú de inicio.
