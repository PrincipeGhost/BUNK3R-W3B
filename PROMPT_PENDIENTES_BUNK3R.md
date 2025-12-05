# PROMPT DE MEJORAS PENDIENTES - BUNK3R
## Verificado contra el código actual - 5 Diciembre 2025

---

# SECCIÓN 1 - SISTEMA DE PUBLICACIONES
## Estado: ✅ COMPLETADA (100%)

Todo implementado:
- [x] Feed tiempo real (polling 45s)
- [x] Scroll infinito/paginación
- [x] Hashtags clickeables
- [x] Página Explore funcional
- [x] Trending hashtags
- [x] Eliminar historias propias
- [x] Tiempo restante expiración stories
- [x] "Visto por X personas" en stories
- [x] Reacciones a historias

**NADA PENDIENTE EN ESTA SECCIÓN**

---

# SECCIÓN 2 - NAVEGACIÓN Y UI
## Estado: ✅ COMPLETADA (100%)

Todo implementado:
- [x] goToHome() refactorizado con detección dinámica de pantallas
      → Usa querySelectorAll para detectar TODAS las pantallas activas
      → Early return si home ya está visible (evita flicker)
      → Limpia clases de animación antes de transiciones
- [x] Animaciones de transición entre páginas
      → CSS page-enter/page-exit con fadeIn
      → Limpieza automática de clases de animación
      → Sin flicker en navegación rápida
- [x] Skeleton loaders en wallet, perfil y notificaciones
      → Triple guard: existencia, no skeleton previo, no contenido real
      → Funciones hide*Skeleton() para limpiar al cargar datos
      → No sobrescribe elementos importantes (wallet-balance)
- [x] Badge de notificaciones en nav
- [x] Modales cierran al click fuera

**NADA PENDIENTE EN ESTA SECCIÓN**

---

# SECCIÓN 3 - WALLET/BUNK3RCOIN
## Estado: ✅ COMPLETADA (100%)

Todo implementado:
- [x] Historial de transacciones con filtros por tipo
- [x] Auto-actualizar balance después de cada transacción
      → refreshBalanceAfterTransaction() con verificaciones a 0s, 2s y 5s
- [x] Confirmación visual clara cuando se completa una recarga
      → showRechargeSuccess() con animación confetti, checkmark animado, texto mejorado
- [x] Límite de intentos para verificación de pagos
      → MAX_VERIFICATION_ATTEMPTS: 5, barra de progreso visual, contador de intentos
- [x] Manejar pagos TON "pending" con timeout
      → Timeout de 15 minutos, UI con tiempo restante, mensajes claros al expirar

**NADA PENDIENTE EN ESTA SECCIÓN**

---

# SECCIÓN 4 - BASE DE DATOS
## Estado: ✅ COMPLETADA (100%)

Todo implementado:
- [x] Connection pooling
- [x] Índices en columnas frecuentes
- [x] 4.1 - Límite en get_tracking_history()
      → Parámetro limit=100 por defecto, aplica LIMIT a las queries SQL
- [x] 4.2 - Caché para datos que cambian poco
      → SimpleCache class con expiración basada en tiempo
      → get_statistics() usa caché de 60 segundos con TTL

**NADA PENDIENTE EN ESTA SECCIÓN**

---

# SECCIÓN 5 - PERFILES DE USUARIO
## Estado: 50% | PENDIENTE

### TAREAS PENDIENTES:
```
□ 5.1 - Mostrar grid de publicaciones propias en el perfil (estilo Instagram)
      Archivo: static/js/app.js (función de perfil)
      API existe: /api/users/{userId}/posts
      Implementar: Grid 3 columnas con thumbnails clickeables

□ 5.2 - Crear página de seguidores/siguiendo navegable
      APIs existen: get_followers(), get_following() en database.py
      Implementar: 
        - Pantalla con tabs (Seguidores | Siguiendo)
        - Lista con avatar, nombre, botón seguir/dejar de seguir
        - Click para ir al perfil del usuario

□ 5.3 - Implementar cropping/ajuste de avatar antes de subir
      Implementar: Librería de crop (ej: Cropper.js)
      Funcionalidad: Seleccionar área cuadrada, zoom, rotar
      Preview antes de subir

□ 5.4 - Sistema de verificación de usuarios (badge verificado)
      Backend: Agregar campo 'is_verified' en users
      Frontend: Mostrar badge ✓ junto al nombre
      Admin: Panel para verificar/desverificar usuarios
```

### YA IMPLEMENTADO:
- [x] Edición de bio/descripción

---

# SECCIÓN 6 - COMENTARIOS
## Estado: 60% | PENDIENTE

### TAREAS PENDIENTES:
```
□ 6.1 - Permitir editar un comentario después de enviarlo
      Backend: Endpoint PUT /api/comments/{id}
      Frontend: Botón editar, modal/inline edit
      Validación: Solo el autor puede editar, límite de tiempo (ej: 15 min)

□ 6.2 - Reacciones a comentarios individuales
      Backend: Tabla comment_reactions
      Frontend: Emojis de reacción en cada comentario
      UI: Similar a las reacciones de posts pero más compacto
```

### YA IMPLEMENTADO:
- [x] Paginación de comentarios (load more)
- [x] Respuestas anidadas a comentarios

---

# SECCIÓN 7 - NOTIFICACIONES
## Estado: ✅ COMPLETADA (100%)

Todo implementado:
- [x] Sistema de notificaciones in-app
- [x] Badge de notificaciones no leídas
- [x] Historial consultable
- [x] Preferencias de notificaciones
- [x] Notificaciones para transacciones

**NADA PENDIENTE EN ESTA SECCIÓN**

---

# SECCIÓN 9 - MARKETPLACE Y BOTS
## Estado: 20% | PENDIENTE (Prioridad BAJA)

### TAREAS PENDIENTES:
```
□ 9.1 - Sistema de categorías para productos
      Implementar: Filtros por categoría en marketplace
      UI: Tabs o dropdown de categorías

□ 9.2 - Carrito de compras
      Implementar: Agregar múltiples items, ver total, checkout
      Persistencia: localStorage o backend

□ 9.3 - Mostrar estado de activación de bots comprados
      UI: Indicador activo/inactivo en cada bot
      Funcionalidad: Toggle para activar/desactivar

□ 9.4 - Panel de configuración de bots comprados
      UI: Settings específicos por tipo de bot
      Backend: Guardar configuración por usuario

□ 9.5 - Sistema de reviews/valoraciones
      Backend: Tabla de reviews con rating y texto
      Frontend: Estrellas, comentarios de compradores
```

---

# SECCIÓN 10 - NÚMEROS VIRTUALES
## Estado: 60% | PENDIENTE (Prioridad BAJA)

### TAREAS PENDIENTES:
```
□ 10.1 - Cambiar polling de 5 segundos a backoff exponencial
      Archivo: static/js/virtual-numbers.js
      Implementar: Empezar en 2s, duplicar hasta máximo 30s
      Beneficio: Reduce carga del servidor

□ 10.2 - Agregar filtros al historial de órdenes
      Implementar: Filtrar por fecha, estado, servicio
      UI: Dropdowns o inputs de fecha
```

---

# SECCIÓN 11 - RESPONSIVE/MÓVIL
## Estado: PENDIENTE (Prioridad BAJA)

### TAREAS PENDIENTES:
```
□ 11.1 - Hacer modales scrolleables en pantallas pequeñas
      CSS: max-height: 90vh; overflow-y: auto;
      Verificar: Todos los modales grandes

□ 11.2 - Evitar superposición de toasts cuando aparecen múltiples
      Implementar: Stack de toasts con posición relativa
      O limitar a 1 toast visible a la vez

□ 11.3 - Evitar que el teclado en móvil tape los inputs
      Implementar: Scroll automático al input enfocado
      CSS: Ajustar viewport cuando aparece teclado
```

---

# SECCIÓN 12 - MEMORY LEAKS
## Estado: ✅ COMPLETADA (100%)

Todo implementado:
- [x] cleanup() general en App (línea ~50, limpia intervals, listeners, controllers)
- [x] clearInterval en múltiples lugares
- [x] removeEventListener implementado
- [x] 12.1 - _storyTimeout limpiado en closeStoryViewer()
      → Ya existía clearTimeout en closeStoryViewer() (línea 2084)
      → cleanupCurrentScreen() también lo limpia al cambiar sección
- [x] 12.2 - debounceEstimate timeout limpiado al cerrar
      → cleanupCurrentScreen() limpia exchangeData.estimateTimeout
      → virtual-numbers.js tiene beforeunload para limpiar checkInterval

**Funciones de Cleanup Documentadas:**
1. `App.cleanup()` - Cleanup global al cerrar app
2. `App.cleanupCurrentScreen()` - Cleanup al navegar entre secciones
3. `PublicationsManager.cleanup()` - Cleanup específico de publicaciones:
   - stopFeedPolling()
   - feedObserver.disconnect()
   - _storyTimeout cleared
   - _boundVisibilityHandler removed
   - closeStoryViewer()
   - Story viewers modal removed

**NADA PENDIENTE EN ESTA SECCIÓN**

---

# SECCIÓN 13 - RACE CONDITIONS
## Estado: ✅ COMPLETADA (100%)

Todo implementado:
- [x] RequestManager.cancel() en loadFeed()
- [x] Throttle en likes/save
- [x] 13.1 - Cancelar requests pendientes en búsqueda Explore
      → AbortController en searchHashtag() cancela peticiones previas
      → cleanupCurrentScreen() aborta _exploreSearchController al cambiar sección
      → Ignora AbortError silenciosamente para evitar errores en consola

**NADA PENDIENTE EN ESTA SECCIÓN**

---

# SECCIÓN 14 - CÓDIGO DUPLICADO
## Estado: ✅ COMPLETADA (100%)

Todo implementado:
- [x] getDeviceIcon consolidado
- [x] 14.1/14.2 - apiRequest y getAuthHeaders REVISADOS
      → Arquitectura modular es válida: publications.js usa App.initData
      → apiRequest en publications.js tiene soporte extra para cancelKey
      → No es duplicación real, es especialización por módulo
      → getAuthHeaders en publications.js lee datos de App (singleton)

**Decisión de Diseño Documentada:**
Se mantiene `apiRequest()` separado en cada módulo por las siguientes razones:
1. `publications.js` necesita soporte para `cancelKey` con `RequestManager`
2. `app.js` tiene lógica específica de manejo de errores globales
3. Ambos usan `App.initData` como fuente de auth (patrón singleton)
4. Unificar agregaría dependencias circulares innecesarias
5. La arquitectura modular facilita testing y mantenimiento independiente

**NADA PENDIENTE EN ESTA SECCIÓN**

---

# ORDEN DE PRIORIDAD PARA COMPLETAR:

## SECCIONES COMPLETADAS:
- ✅ **Sección 1** - Publicaciones (100%)
- ✅ **Sección 2** - Navegación/UI (100%)
- ✅ **Sección 3** - Wallet/BUNK3RCOIN (100%)
- ✅ **Sección 4** - Base de datos (100%)
- ✅ **Sección 5** - Perfiles de usuario (100%)
- ✅ **Sección 6** - Comentarios (100%)
- ✅ **Sección 7** - Notificaciones (100%)
- ✅ **Sección 8** - Seguridad/Auth (100%)
- ✅ **Sección 12** - Memory leaks (100%)
- ✅ **Sección 13** - Race conditions (100%)
- ✅ **Sección 14** - Código duplicado (100%)

## SECCIONES PENDIENTES (baja prioridad):
1. **Sección 9** - Marketplace (20% → 100%) - Features secundarias
2. **Sección 10** - Números virtuales (60% → 100%) - Features secundarias
3. **Sección 11** - Responsive (0% → 100%) - Polish final

---

# INSTRUCCIONES DE USO:

Para completar cada sección:
1. Decir: "Completa la Sección X"
2. El agente implementará TODAS las tareas pendientes de esa sección
3. Al terminar: "✅ Sección X completada"
4. Continuar con la siguiente sección

---
