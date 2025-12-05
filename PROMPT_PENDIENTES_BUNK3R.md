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
## Estado: 60% | PENDIENTE

### TAREAS PENDIENTES:
```
□ 2.1 - Refactorizar goToHome() para ocultar pantallas dinámicamente
      Archivo: static/js/app.js línea 666
      Problema: Usa lista hardcodeada de pantallas a ocultar
      Solución: Detectar automáticamente todas las pantallas con clase 'screen' u otro selector

□ 2.2 - Agregar animaciones de transición entre páginas/secciones
      Archivos: static/js/app.js, static/css/styles.css
      Implementar: fadeIn/fadeOut o slide transitions al cambiar de sección

□ 2.3 - Skeleton loaders en todos los lugares necesarios
      Verificar: feed, perfil, wallet, notificaciones
      Asegurar que aparezcan durante carga inicial
```

### YA IMPLEMENTADO:
- [x] Badge de notificaciones en nav
- [x] Modales cierran al click fuera (onclick="if(event.target === this)")

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
## Estado: 70% | PENDIENTE

### TAREAS PENDIENTES:
```
□ 4.1 - Agregar límite a get_tracking_history
      Archivo: tracking/database.py
      Problema: Puede ser lento con historial muy largo
      Solución: Agregar parámetro limit con valor por defecto (ej: 100)

□ 4.2 - Implementar caché para datos que cambian poco
      Datos candidatos: 
        - Estadísticas generales
        - Configuraciones del sistema
        - Lista de países/servicios de números virtuales
      Opciones: Redis, caché en memoria, o decorador @lru_cache
```

### YA IMPLEMENTADO:
- [x] Connection pooling
- [x] Índices en columnas frecuentes

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
## Estado: 80% | PENDIENTE

### TAREAS PENDIENTES:
```
□ 12.1 - Limpiar _storyTimeout en el visor de stories al cerrar
      Archivo: static/js/publications.js
      Verificar: clearTimeout en closeStoryViewer()

□ 12.2 - Limpiar timeouts de debounceEstimate en exchange al cerrar modal
      Verificar: Cualquier setTimeout activo debe limpiarse
```

### YA IMPLEMENTADO:
- [x] cleanup() general en App
- [x] clearInterval en múltiples lugares
- [x] removeEventListener implementado

---

# SECCIÓN 13 - RACE CONDITIONS
## Estado: 70% | PENDIENTE

### TAREAS PENDIENTES:
```
□ 13.1 - Cancelar requests pendientes al iniciar búsqueda nueva
      Archivo: static/js/app.js (performExploreSearch)
      Usar: RequestManager.cancel() antes de nuevo request
```

### YA IMPLEMENTADO:
- [x] RequestManager.cancel() en loadFeed()
- [x] Throttle en likes/save

---

# SECCIÓN 14 - CÓDIGO DUPLICADO
## Estado: 30% | PENDIENTE (Prioridad BAJA)

### TAREAS PENDIENTES:
```
□ 14.1 - Unificar apiRequest() 
      Duplicado en: app.js Y publications.js
      Solución: Mover a utils.js y usar en ambos

□ 14.2 - Unificar getAuthHeaders()
      Duplicado en: app.js:2650 Y publications.js:1988
      Solución: Función única en utils.js
```

### YA IMPLEMENTADO:
- [x] getDeviceIcon consolidado

---

# ORDEN DE PRIORIDAD PARA COMPLETAR:

1. **Sección 3** - Wallet (40% → 100%) - CRÍTICO para $BUNK3R
2. **Sección 5** - Perfiles (50% → 100%) - UX importante
3. **Sección 6** - Comentarios (60% → 100%) - Funcionalidad social
4. **Sección 2** - Navegación (60% → 100%) - UX general
5. **Sección 4** - Base de datos (70% → 100%) - Optimización
6. **Sección 12** - Memory leaks (80% → 100%) - Estabilidad
7. **Sección 13** - Race conditions (70% → 100%) - Estabilidad
8. **Sección 14** - Código duplicado (30% → 100%) - Mantenibilidad
9. **Sección 9** - Marketplace (20% → 100%) - Features secundarias
10. **Sección 10** - Números virtuales (60% → 100%) - Features secundarias
11. **Sección 11** - Responsive (0% → 100%) - Polish final

---

# INSTRUCCIONES DE USO:

Para completar cada sección:
1. Decir: "Completa la Sección X"
2. El agente implementará TODAS las tareas pendientes de esa sección
3. Al terminar: "✅ Sección X completada"
4. Continuar con la siguiente sección

---
