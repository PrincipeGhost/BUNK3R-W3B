# PROMPT MAESTRO - BUNK3R-W3B

---

## TABLERO DE INICIO

Al iniciar cada sesión, el agente DEBE mostrar este tablero automáticamente:

```
╔══════════════════════════════════════════════════════════════════╗
║                    🏦 BUNK3R-W3B - ESTADO ACTUAL                 ║
╠══════════════════════════════════════════════════════════════════╣
║ Última actualización: 7 Diciembre 2025                           ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║ ✅ COMPLETADAS: 9 secciones                                      ║
║    27.1 Dashboard | 27.2 Usuarios (95%) | 27.3 Transacciones     ║
║    27.4 Wallets | 27.5 Contenido | 27.6 Números Virtuales        ║
║    27.7 Bots | 27.8 Logs | 27.9 Analytics                        ║
║                                                                  ║
║ 🔄 EN PROGRESO: Ninguna                                          ║
║                                                                  ║
║ ⏳ PENDIENTES: 27.10→27.25, Secciones 28, 29, 30, 31, 32, 33     ║
║                                                                  ║
║ 🔴 CRÍTICO: 3 problemas                                          ║
║    30.2 innerHTML XSS | 31.1 Botones | 32.5 Auditar secretos     ║
║    ✅ 30.1 except vacíos | ✅ 31.2 Códigos 2FA en logs            ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                        COMANDOS DISPONIBLES                      ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  1️⃣  STATUS          → Ver este tablero actualizado              ║
║  2️⃣  CONTINUAR        → Retomar la siguiente tarea pendiente     ║
║  3️⃣  FRONTEND         → Trabajar solo en archivos frontend       ║
║  4️⃣  BACKEND          → Trabajar solo en archivos backend        ║
║  5️⃣  ADMIN            → Trabajar solo en panel admin             ║
║  6️⃣  BLOCKCHAIN       → Trabajar solo en servicios blockchain    ║
║  7️⃣  NUEVA TAREA      → Agregar nueva funcionalidad              ║
║  8️⃣  VER PENDIENTES   → Lista detallada de tareas                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
Escribe un número o comando...
```

---

## SISTEMA DE 4 AGENTES - DIVISIÓN DE TRABAJO

### 🔵 AGENTE 1: FRONTEND USUARIO
**Rama Git:** `feature/frontend-user`
**Comando para activar:** `3` o `FRONTEND`

| Archivo | Función | SOLO ESTE AGENTE |
|---------|---------|------------------|
| `static/js/app.js` | Lógica frontend principal | ✅ |
| `static/js/publications.js` | Publicaciones/feed | ✅ |
| `static/js/virtual-numbers.js` | Números virtuales UI | ✅ |
| `static/js/utils.js` | Utilidades compartidas | ✅ |
| `static/css/styles.css` | Estilos generales | ✅ |
| `templates/index.html` | Template principal | ✅ |
| `templates/virtual_numbers.html` | Template VN | ✅ |

---

### 🟢 AGENTE 2: FRONTEND ADMIN
**Rama Git:** `feature/frontend-admin`
**Comando para activar:** `5` o `ADMIN`

| Archivo | Función | SOLO ESTE AGENTE |
|---------|---------|------------------|
| `static/js/admin.js` | Lógica panel admin | ✅ |
| `static/css/admin.css` | Estilos admin | ✅ |
| `templates/admin.html` | Template admin | ✅ |

---

### 🟡 AGENTE 3: BACKEND API
**Rama Git:** `feature/backend-api`
**Comando para activar:** `4` o `BACKEND`

| Archivo | Función | SOLO ESTE AGENTE |
|---------|---------|------------------|
| `app.py` | Endpoints API y rutas | ✅ |
| `tracking/database.py` | Operaciones BD | ✅ |
| `tracking/models.py` | Modelos de datos | ✅ |
| `tracking/email_service.py` | Servicio de emails | ✅ |
| `tracking/security.py` | Seguridad y 2FA | ✅ |
| `init_db.py` | Inicialización BD | ✅ |
| `requirements.txt` | Dependencias Python | ✅ |

---

### 🔴 AGENTE 4: BLOCKCHAIN & SERVICIOS EXTERNOS
**Rama Git:** `feature/blockchain-services`
**Comando para activar:** `6` o `BLOCKCHAIN`

| Archivo | Función | SOLO ESTE AGENTE |
|---------|---------|------------------|
| `tracking/b3c_service.py` | Token B3C en TON | ✅ |
| `tracking/wallet_pool_service.py` | Pool de wallets | ✅ |
| `tracking/deposit_scheduler.py` | Detección de depósitos | ✅ |
| `tracking/smspool_service.py` | API números virtuales | ✅ |
| `tracking/cloudinary_service.py` | Subida de media | ✅ |
| `tracking/encryption.py` | Encriptación contenido | ✅ |

---

### ⚠️ ARCHIVOS COMPARTIDOS (SOLO LECTURA)

| Archivo | Puede leer | Puede editar |
|---------|------------|--------------|
| `run.py` | Todos | Ninguno |
| `replit.md` | Todos | El que complete tarea |
| `PROMPT_PENDIENTES_BUNK3R.md` | Todos | El que complete tarea |

---

## 🚫 REGLA CRÍTICA: PROHIBIDO TOCAR ARCHIVOS DE OTROS

```
╔═══════════════════════════════════════════════════════════════════╗
║  ⛔ ABSOLUTAMENTE PROHIBIDO MODIFICAR ARCHIVOS DE OTRO AGENTE ⛔  ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Si trabajas en FRONTEND:                                         ║
║  ❌ NO toques app.py, tracking/*.py                               ║
║  ✅ SÍ puedes tocar static/js/app.js, static/css/styles.css      ║
║                                                                   ║
║  Si trabajas en BACKEND:                                          ║
║  ❌ NO toques static/js/*.js, static/css/*.css, templates/*.html ║
║  ✅ SÍ puedes tocar app.py, tracking/database.py, etc.           ║
║                                                                   ║
║  Si trabajas en ADMIN:                                            ║
║  ❌ NO toques app.js, styles.css, archivos de backend             ║
║  ✅ SÍ puedes tocar admin.js, admin.css, admin.html              ║
║                                                                   ║
║  Si trabajas en BLOCKCHAIN:                                       ║
║  ❌ NO toques frontend ni backend principal                       ║
║  ✅ SÍ puedes tocar b3c_service.py, wallet_pool_service.py, etc. ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## SISTEMA DE PRIORIDADES

Las tareas se trabajan por PRIORIDAD, no por orden numérico:

| Prioridad | Símbolo | Significado | Acción |
|-----------|---------|-------------|--------|
| CRÍTICA | 🔴 | Bloquea otras tareas o afecta producción | Trabajar PRIMERO |
| ALTA | 🟡 | Importante pero no urgente | Trabajar después de críticas |
| MEDIA | 🟢 | Mejoras y optimizaciones | Cuando no hay críticas/altas |
| BAJA | ⚪ | Nice to have | Solo si hay tiempo |

---

## FORMATO DE COMMITS

Cada commit DEBE seguir este formato:
```
[ÁREA] Descripción breve

Ejemplos:
[FRONTEND] Agregado modal de seguidores
[BACKEND] Implementado endpoint /api/settings/privacy
[ADMIN] Corregido filtro de usuarios por país
[BLOCKCHAIN] Optimizado pool de wallets
[DOCS] Actualizado estado de secciones
```

---

## 💾 SISTEMA DE PERSISTENCIA Y MEMORIA

### ⚠️ REGLA SUPREMA DE PERSISTENCIA

```
╔═══════════════════════════════════════════════════════════════════╗
║     🧠 EL AGENTE DEBE GUARDAR TODO, SIEMPRE, INMEDIATAMENTE 🧠    ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  La memoria del agente SE PIERDE entre sesiones.                  ║
║  Este archivo ES la memoria del proyecto.                         ║
║  Si no está escrito aquí, NO EXISTE para el próximo agente.       ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

### 📍 CUÁNDO GUARDAR (OBLIGATORIO)

| Momento | Acción de Guardado |
|---------|-------------------|
| Al COMPLETAR cualquier tarea | Actualizar `⏳` → `✅` inmediatamente |
| Al COMPLETAR un checkbox | Cambiar `[ ]` → `[x]` inmediatamente |
| Al EMPEZAR una sección | Marcar como `🔄 En progreso` |
| Al DETECTAR un error | Documentarlo en la sección de errores |
| Al MODIFICAR un archivo | Agregarlo al historial de cambios |
| Al AGREGAR dependencia | Documentar en requirements/package |
| Al 90% del contexto | PARAR y guardar TODO |
| ANTES de terminar sesión | Actualizar punto de guardado |

---

### 📝 ACTUALIZACIÓN INMEDIATA DESPUÉS DE CADA TAREA

El agente DEBE ejecutar estos pasos **inmediatamente** después de completar cualquier tarea:

```
PASO 1: Actualizar este archivo (PROMPT_PENDIENTES_BUNK3R.md)
────────────────────────────────────────────────────────────
✓ Cambiar el símbolo de la tarea: ⏳ → ✅ o [ ] → [x]
✓ Agregar fecha de completado si es sección completa
✓ Actualizar contadores en el TABLERO DE INICIO
✓ Mover tarea de "EN PROGRESO" a "COMPLETADAS"

PASO 2: Actualizar replit.md
────────────────────────────
✓ Agregar entrada en "Cambios Recientes"
✓ Listar archivos modificados
✓ Documentar decisiones técnicas importantes

PASO 3: Guardar contexto en memoria persistente
───────────────────────────────────────────────
✓ Crear/actualizar .local/state/memory/persisted_information.md
✓ Incluir: qué se hizo, qué falta, próximo paso
```

---

### 🔴 GUARDADO DE EMERGENCIA AL 90%

Cuando el agente detecte que su contexto está cerca del límite:

```
╔═══════════════════════════════════════════════════════════════════╗
║                    🚨 PROTOCOLO DE EMERGENCIA 🚨                  ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  1. DETENER inmediatamente cualquier trabajo en curso             ║
║                                                                   ║
║  2. GUARDAR en este archivo:                                      ║
║     - Última línea de código modificada                           ║
║     - Último archivo tocado                                       ║
║     - Estado exacto de la tarea (% completado)                    ║
║     - Errores encontrados                                         ║
║     - Decisiones tomadas                                          ║
║                                                                   ║
║  3. ACTUALIZAR el PUNTO DE GUARDADO al final del archivo          ║
║                                                                   ║
║  4. CREAR memoria persistente en:                                 ║
║     .local/state/memory/persisted_information.md                  ║
║                                                                   ║
║  5. INFORMAR al usuario que se pausó por límite de contexto       ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

### 📋 FORMATO DEL PUNTO DE GUARDADO

Al final de este archivo siempre debe existir esta sección actualizada:

```markdown
## PUNTO DE GUARDADO

**Fecha:** [DD/MM/YYYY HH:MM]
**Sesión:** [Número de sesión del día]
**Agente activo:** [FRONTEND/BACKEND/ADMIN/BLOCKCHAIN]

### Última tarea trabajada
- Sección: [27.X.X]
- Nombre: [Nombre de la tarea]
- Estado: [Completada / En progreso X%]
- Archivos modificados: [lista]

### Próximos pasos
1. [Siguiente acción inmediata]
2. [Acción posterior]

### Errores pendientes
- [ ] [Error 1 si hay]
- [ ] [Error 2 si hay]

### Notas para el próximo agente
[Cualquier información importante que el próximo agente necesite saber]
```

---

### 🔄 HISTORIAL DE CAMBIOS (Actualizar con cada modificación)

El agente debe mantener un log de cambios recientes:

```markdown
### CAMBIOS RECIENTES (Últimos 10)

| Fecha | Sección | Cambio | Archivos |
|-------|---------|--------|----------|
| DD/MM | 27.X.X | Descripción | archivo1.js, archivo2.py |
```

---

### ⚠️ ERRORES QUE NUNCA DEBEN OCURRIR

```
❌ Cerrar sesión sin actualizar este archivo
❌ Completar tarea sin cambiar ⏳ → ✅
❌ Modificar archivo sin documentarlo
❌ Perder contexto sin guardar estado
❌ Dejar sección "En progreso" sin especificar %
❌ No actualizar el tablero de inicio
```

---

## REGLAS BASE DEL AGENTE – OBLIGATORIAS

### 1. Comunicación de Progreso
```
INICIO:   "🚀 Comenzando sección [X]: [Nombre]"
FIN:      "✅ Completada sección [X]: [Nombre] | Pendientes: [lista]"
ERROR:    "❌ Problema en sección [X]: [Descripción]"
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
Actualizar `replit.md` con:
- Qué se hizo
- Qué falta
- Errores detectados
- Siguientes pasos
- Nuevas dependencias
- Cambios en arquitectura

### 5. Normas de Seguridad
**NO HACER:**
- Eliminar archivos sin confirmación
- Cambios destructivos sin aprobación
- Exponer datos sensibles
- Gestionar API keys en el panel (usar Secrets de Replit)

**OBLIGATORIO:**
- Respaldo antes de cambios mayores
- Validar entradas del usuario
- Mantener integridad del proyecto
- Correr tests antes de marcar completado

---

## ⚠️ REGLA CRÍTICA: TODO DEBE FUNCIONAR AL 100% ⚠️

**PROHIBIDO DEJAR COSAS SIN FUNCIONALIDAD:**

El agente NUNCA debe crear elementos de UI que no funcionen. TODO lo que se implemente DEBE:

1. **Botones:** Cada botón DEBE tener su evento y ejecutar una acción real
2. **Links/Navegación:** Cada link DEBE llevar a una página/sección que EXISTA
3. **Formularios:** Cada formulario DEBE enviar datos al backend correctamente
4. **Modales:** Cada modal DEBE abrirse, cerrarse y funcionar completamente
5. **Tablas:** Los datos DEBEN cargarse de la base de datos real, NO datos mock
6. **Filtros/Búsquedas:** DEBEN filtrar datos realmente, no ser solo visuales
7. **Paginación:** DEBE funcionar con datos reales
8. **Gráficos:** DEBEN mostrar datos reales de la BD
9. **Acciones:** Aprobar, rechazar, banear, etc. DEBEN ejecutarse en el backend
10. **Exportaciones:** DEBEN generar archivos descargables reales

**ANTES DE MARCAR CUALQUIER TAREA COMO COMPLETADA:**
- [ ] Verificar que TODOS los botones funcionan
- [ ] Verificar que TODAS las páginas/secciones existen
- [ ] Verificar que los datos vienen de la BD (no hardcodeados)
- [ ] Verificar que las acciones modifican la BD correctamente
- [ ] Verificar en consola que NO hay errores JS
- [ ] Verificar en logs del servidor que NO hay errores 500
- [ ] Probar cada funcionalidad como usuario real

**SI ALGO NO SE PUEDE IMPLEMENTAR COMPLETAMENTE:**
- Informar al usuario ANTES de crear el elemento
- NO crear botones/links que digan "Próximamente" o no hagan nada
- Mejor no crear el elemento hasta que pueda funcionar

**CERO TOLERANCIA A:**
- Botones que no hacen nada
- Links que llevan a páginas 404
- Formularios que no envían datos
- Tablas con datos falsos/hardcodeados
- Acciones que solo muestran toast pero no ejecutan nada
- Gráficos con datos inventados

---

## LEYENDA DE ESTADOS

| Símbolo | Significado |
|---------|-------------|
| ✅ | Completado |
| 🔄 | En progreso |
| ⏳ | Pendiente |
| ❌ | Bloqueado/Error |

---

# ════════════════════════════════════════════════════════════════
# SECCIONES DE TRABAJO
# ════════════════════════════════════════════════════════════════

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 27: PANEL DE ADMINISTRACIÓN COMPLETO
## ════════════════════════════════════════════════════════════════

**Prioridad:** 🔴 CRÍTICA  
**Agregado:** 6 Diciembre 2025  
**Agente asignado:** 🟢 FRONTEND ADMIN + 🟡 BACKEND API

---

### OBJETIVO PRINCIPAL:
Crear un Panel de Administración profesional y completo que permita al owner/admin tener visibilidad y control TOTAL sobre la plataforma BUNK3R en tiempo real.

---

### ARQUITECTURA DEL PANEL ADMIN

**Acceso:** Solo usuarios con `is_owner = true` o rol `admin`
**Ruta:** `/admin` o sección especial en la app
**Seguridad:** Requiere 2FA + validación de IP

---

## ═══════════════════════════════════════
## FASE 27.1: DASHBOARD PRINCIPAL ✅
## ═══════════════════════════════════════

**Agente:** 🟢 FRONTEND ADMIN
**Archivos:** `static/js/admin.js`, `static/css/admin.css`, `templates/admin.html`

### 27.1.1 - Métricas en Tiempo Real (Cards superiores)
- [x] Total de usuarios registrados
- [x] Usuarios activos HOY
- [x] Total B3C en circulación
- [x] Balance Hot Wallet (TON)
- [x] Transacciones últimas 24h
- [x] Ingresos del día (comisiones)

### 27.1.2 - Gráficos del Dashboard
- [x] Gráfico de usuarios nuevos (últimos 30 días)
- [x] Gráfico de transacciones (últimos 7 días)
- [x] Gráfico de ingresos por comisiones
- [x] Gráfico de uso por sección de la app

### 27.1.3 - Actividad Reciente (Feed en vivo)
- [x] Últimas 10 transacciones
- [x] Últimos 5 usuarios registrados
- [x] Últimas alertas del sistema
- [x] Auto-refresh cada 30 segundos

### 27.1.4 - Alertas Críticas
- [x] Banner rojo si hay errores del sistema
- [x] Alerta si hot wallet tiene bajo balance
- [x] Alerta de retiros pendientes de aprobar
- [x] Alerta de reportes de contenido sin revisar

---

## ═══════════════════════════════════════
## FASE 27.2: GESTIÓN DE USUARIOS ✅ (95%)
## ═══════════════════════════════════════

**Agente:** 🟢 FRONTEND ADMIN + 🟡 BACKEND API
**Archivos Frontend:** `static/js/admin.js`, `templates/admin.html`
**Archivos Backend:** `app.py`, `tracking/database.py`

### 27.2.1 - Lista de Usuarios
- [x] Tabla paginada con TODOS los usuarios
- [x] Columnas: ID, Username, Nombre, Email, Fecha registro
- [x] Columnas: Última conexión, IP, País, Dispositivo
- [x] Columnas: Balance B3C, Estado (activo/baneado), Verificado
- [x] Búsqueda por username, ID, IP
- [x] Filtros: Estado, País, Fecha de registro
- [x] Ordenar por cualquier columna
- [x] Exportar a CSV

### 27.2.2 - Detalle de Usuario (al hacer clic)
- [x] Información completa del perfil
- [x] Historial de IPs usadas
- [x] Dispositivos conectados
- [x] Historial de sesiones (Activity Log)
- [x] Todas las transacciones del usuario
- [x] Publicaciones del usuario
- [x] Compras de números virtuales
- [x] Notas del admin sobre el usuario

### 27.2.3 - Acciones sobre Usuario
- [x] Banear/Suspender (temporal o permanente)
- [x] Desbanear
- [x] Cerrar todas las sesiones activas
- [x] Ajustar balance B3C manualmente (con razón)
- [x] Enviar notificación al usuario
- [x] Agregar nota interna
- [ ] Ver como este usuario (impersonar) - Pendiente por seguridad

### 27.2.4 - Detección de Fraude
- [x] Alertas de múltiples cuentas (misma IP)
- [x] Alertas de cambios de IP frecuentes
- [x] Alertas de actividad sospechosa
- [x] Lista de IPs bloqueadas
- [x] Agregar IP a blacklist

---

## ═══════════════════════════════════════
## FASE 27.3: TRANSACCIONES Y FINANZAS ✅
## ═══════════════════════════════════════

**Agente:** 🟢 FRONTEND ADMIN + 🟡 BACKEND API

### 27.3.1 - Dashboard Financiero
- [x] Total B3C vendidos (histórico)
- [x] Total TON recibidos
- [x] Total comisiones ganadas
- [x] Gráfico de ingresos diarios
- [x] Gráfico de volumen de transacciones
- [x] Comparativa mes actual vs anterior

### 27.3.2 - Lista de Transacciones
- [x] Tabla con TODAS las transacciones
- [x] Tipos: Compra B3C, Venta B3C, Transferencia P2P, Retiro
- [x] Columnas: ID, Usuario, Tipo, Monto, Estado, Fecha, TX Hash
- [x] Filtros: Tipo, Estado, Fecha, Usuario
- [x] Búsqueda por TX hash o ID
- [x] Ver detalle de cada transacción
- [x] Link a TonScan para transacciones blockchain

### 27.3.3 - Compras de B3C
- [x] Lista de todas las compras
- [x] Estado: Pendiente, Confirmada, Fallida, Expirada
- [x] Acreditar manualmente si es necesario
- [x] Ver wallet de depósito usada
- [x] Ver transacción en blockchain

### 27.3.4 - Retiros
- [x] Lista de solicitudes de retiro
- [x] Estados: Pendiente, Aprobado, Procesado, Rechazado
- [x] Aprobar retiro (requiere 2FA)
- [x] Rechazar retiro (con razón)
- [x] Marcar como procesado
- [x] Ver historial de retiros procesados

### 27.3.5 - Transferencias P2P
- [x] Lista de transferencias entre usuarios
- [x] Ver emisor y receptor
- [x] Detectar transferencias sospechosas
- [ ] Revertir transferencia (si es necesario) - Pendiente por seguridad

### 27.3.6 - Estadísticas por Período
- [x] Selector de rango de fechas
- [x] Estadísticas del período seleccionado
- [x] Exportar reporte a CSV/PDF

---

## ═══════════════════════════════════════
## FASE 27.4: WALLETS Y BLOCKCHAIN ✅
## ═══════════════════════════════════════

**Agente:** 🔴 BLOCKCHAIN + 🟢 FRONTEND ADMIN

### 27.4.1 - Hot Wallet
- [x] Balance actual en TON (tiempo real)
- [x] Dirección de la hot wallet
- [x] Botón para ver en TonScan
- [x] Historial de transacciones entrantes/salientes
- [x] Alerta si balance bajo (configurable)

### 27.4.2 - Wallets de Depósito
- [x] Lista de todas las wallets generadas
- [x] Estado: Disponible, Asignada, Usada, Consolidada
- [x] Balance de cada wallet
- [x] Usuario asignado (si aplica)
- [x] Consolidar fondos manualmente (individual)
- [x] Consolidar todas las wallets con balance
- [x] Filtro por estado
- [x] Link a TonScan por wallet

### 27.4.3 - Pool de Wallets
- [x] Estadísticas del pool
- [x] Wallets disponibles vs usadas
- [x] Generar más wallets (llenar pool)
- [x] Configurar tamaño mínimo del pool
- [x] Configurar umbral de auto-rellenado
- [x] Configurar umbral de balance bajo

### 27.4.4 - Historial Blockchain
- [x] Todas las transacciones on-chain
- [x] Consolidaciones realizadas
- [x] Retiros enviados
- [x] Estado de confirmaciones
- [x] Tabs para filtrar por tipo
- [x] Link a TonScan por transacción

---

## ═══════════════════════════════════════
## FASE 27.5: CONTENIDO Y PUBLICACIONES ✅
## ═══════════════════════════════════════

**Agente:** 🟢 FRONTEND ADMIN + 🟡 BACKEND API

### 27.5.1 - Moderación de Contenido
- [x] Lista de publicaciones recientes
- [x] Publicaciones reportadas (prioridad)
- [x] Preview del contenido (texto + media)
- [x] Aprobar publicación
- [x] Eliminar publicación
- [x] Advertir al usuario
- [x] Banear usuario por contenido

### 27.5.2 - Reportes de Contenido
- [x] Lista de reportes pendientes
- [x] Ver publicación reportada
- [x] Ver quién reportó
- [x] Razón del reporte
- [x] Resolver reporte (acción tomada)
- [x] Desestimar reporte

### 27.5.3 - Gestión de Hashtags
- [x] Hashtags trending actuales
- [x] Bloquear hashtags inapropiados
- [x] Promover hashtags manualmente
- [x] Estadísticas por hashtag

### 27.5.4 - Stories
- [x] Stories activas
- [x] Moderar stories
- [x] Eliminar stories

---

## ═══════════════════════════════════════
## FASE 27.6: NÚMEROS VIRTUALES ✅
## ═══════════════════════════════════════

**Agente:** 🔴 BLOCKCHAIN (SMSPool) + 🟢 FRONTEND ADMIN

### 27.6.1 - Estadísticas VN
- [x] Total números comprados
- [x] Ingresos por números virtuales
- [x] Servicios más usados (WhatsApp, Telegram, etc.)
- [x] Países más solicitados

### 27.6.2 - Compras de Números
- [x] Lista de todas las compras VN
- [x] Estado: Activo, SMS Recibido, Cancelado, Expirado
- [x] Usuario que compró
- [x] Servicio y país
- [x] Costo (B3C)
- [x] SMS recibidos

### 27.6.3 - Balance SMSPool
- [x] Balance actual de la API
- [x] Alerta si balance bajo
- [x] Link para recargar

---

## ═══════════════════════════════════════
## FASE 27.7: GESTIÓN DE BOTS ✅
## ═══════════════════════════════════════

**Agente:** 🟢 FRONTEND ADMIN + 🟡 BACKEND API

### 27.7.1 - Lista de Bots
- [x] Todos los bots disponibles
- [x] Nombre, descripción, estado
- [x] Precio/comisión de cada bot
- [x] Usuarios usando cada bot

### 27.7.2 - Estadísticas por Bot
- [x] Usos totales
- [x] Ingresos generados
- [x] Usuarios activos
- [x] Gráfico de uso en el tiempo

### 27.7.3 - Configuración de Bots
- [x] Activar/desactivar bot
- [x] Cambiar precio/comisión
- [x] Editar descripción
- [ ] Ver logs del bot (pendiente - requiere sistema de logs específico por bot)

### 27.7.4 - Ingresos por Bots
- [x] Total ingresos por bots
- [x] Desglose por bot
- [x] Historial de cobros

---

## ═══════════════════════════════════════
## FASE 27.8: LOGS Y AUDITORÍA ✅
## ═══════════════════════════════════════

**Agente:** 🟡 BACKEND API + 🟢 FRONTEND ADMIN

### 27.8.1 - Log de Acciones Admin
- [x] Todas las acciones de administradores
- [x] Quién, qué, cuándo
- [x] IP desde donde se hizo
- [x] Filtrar por admin, acción, fecha

### 27.8.2 - Log de Errores del Sistema
- [x] Errores con stack traces
- [x] Nivel: Error, Warning, Critical
- [x] Fecha y hora
- [x] Endpoint afectado
- [x] Marcar como resuelto

### 27.8.3 - Log de Intentos de Login
- [x] Logins exitosos y fallidos
- [x] IP, usuario, fecha
- [x] Detectar intentos de fuerza bruta
- [x] Bloquear IP automáticamente después de X intentos

### 27.8.4 - Historial de Configuración
- [x] Cambios en configuración del sistema
- [x] Quién lo cambió
- [x] Valor anterior vs nuevo
- [x] Fecha del cambio

### 27.8.5 - Exportación de Logs
- [x] Exportar a CSV
- [x] Exportar a JSON
- [x] Rango de fechas seleccionable
- [x] Filtros aplicados

---

## ═══════════════════════════════════════
## FASE 27.9: ANALYTICS Y MÉTRICAS ✅
## ═══════════════════════════════════════

**Agente:** 🟢 FRONTEND ADMIN + 🟡 BACKEND API

### 27.9.1 - Usuarios
- [x] Usuarios activos: Hoy, Esta semana, Este mes
- [x] Usuarios nuevos por día (gráfico 30 días)
- [x] Tasa de retención
- [x] Usuarios por país (tabla con banderas)
- [x] Usuarios por dispositivo (iOS, Android, Desktop)

### 27.9.2 - Uso de la App
- [x] Secciones más visitadas
- [x] Tiempo promedio en la app
- [x] Horarios pico de actividad (gráfico 24h)
- [x] Días más activos

### 27.9.3 - Conversión
- [x] Usuarios que compraron B3C
- [x] Usuarios que usaron números virtuales
- [x] Usuarios que publicaron contenido
- [x] Funnel de conversión

---

## ═══════════════════════════════════════
## FASE 27.10: SOPORTE Y TICKETS ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟡 ALTA
**Agente:** 🟢 FRONTEND ADMIN + 🟡 BACKEND API
**Archivos Frontend:** `static/js/admin.js`, `templates/admin.html`
**Archivos Backend:** `app.py`, `tracking/database.py`

### 27.10.1 - Sistema de Tickets
- [ ] Lista de tickets abiertos
- [ ] Prioridad: Baja, Media, Alta, Urgente
- [ ] Estado: Nuevo, En progreso, Resuelto, Cerrado
- [ ] Asignar ticket a admin
- [ ] Historial de respuestas

### 27.10.2 - Chat con Usuario
- [ ] Responder ticket
- [ ] Adjuntar imágenes
- [ ] Templates de respuestas comunes
- [ ] Cerrar ticket

### 27.10.3 - FAQ Editable
- [ ] Lista de preguntas frecuentes
- [ ] Agregar/editar/eliminar FAQs
- [ ] Ordenar por categoría
- [ ] Publicar/despublicar

### 27.10.4 - Mensajes Masivos
- [ ] Enviar notificación a TODOS los usuarios
- [ ] Enviar a usuarios específicos (filtros)
- [ ] Programar envío
- [ ] Ver historial de envíos

---

## ═══════════════════════════════════════
## FASE 27.11: MARKETPLACE ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟢 MEDIA
**Agente:** 🟢 FRONTEND ADMIN + 🟡 BACKEND API

### 27.11.1 - Productos/Servicios
- [ ] Lista de todos los listings
- [ ] Estado: Activo, Pausado, Eliminado
- [ ] Vendedor
- [ ] Precio, categoría
- [ ] Ventas realizadas

### 27.11.2 - Moderación de Listings
- [ ] Aprobar nuevos listings
- [ ] Rechazar con razón
- [ ] Editar listing (admin)
- [ ] Eliminar listing

### 27.11.3 - Ventas del Marketplace
- [ ] Historial de ventas
- [ ] Comisiones cobradas
- [ ] Disputas activas

### 27.11.4 - Disputas
- [ ] Lista de disputas
- [ ] Ver conversación
- [ ] Resolver a favor de comprador/vendedor
- [ ] Reembolsar

---

## ═══════════════════════════════════════
## FASE 27.12: CONFIGURACIÓN DEL SISTEMA ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟡 ALTA
**Agente:** 🟢 FRONTEND ADMIN + 🟡 BACKEND API

### 27.12.1 - Precios y Comisiones
- [ ] Precio actual de B3C (ver, NO editar aquí)
- [ ] Comisión por transacción
- [ ] Comisión por retiro
- [ ] Monto mínimo de retiro
- [ ] Monto máximo por transacción

### 27.12.2 - Modo Mantenimiento
- [ ] Activar/desactivar modo mantenimiento
- [ ] Mensaje personalizado para usuarios
- [ ] Permitir acceso solo a admins
- [ ] Programar mantenimiento

### 27.12.3 - Estado del Sistema
- [ ] Estado de la base de datos
- [ ] Estado de conexión a TonCenter API
- [ ] Estado de SMSPool API
- [ ] Uptime del servidor

### 27.12.4 - Variables de Entorno (Solo vista)
- [ ] Ver qué secrets están configurados (SÍ/NO, no el valor)
- [ ] Indicador de secrets faltantes
- [ ] Link a panel de Secrets de Replit para configurar

---

## ═══════════════════════════════════════
## FASE 27.13: NOTIFICACIONES ADMIN ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟢 MEDIA
**Agente:** 🟢 FRONTEND ADMIN + 🟡 BACKEND API

### 27.13.1 - Alertas en el Panel
- [ ] Centro de notificaciones
- [ ] Notificaciones no leídas
- [ ] Marcar como leída
- [ ] Categorías: Transacciones, Seguridad, Sistema, Usuarios

### 27.13.2 - Notificaciones Telegram
- [ ] Notificar al owner cuando:
  - Nueva compra grande (>X TON)
  - Nuevo retiro pendiente
  - Error crítico del sistema
  - Nuevo reporte de contenido
  - Usuario baneado por sistema
  - Hot wallet con balance bajo

### 27.13.3 - Configurar Notificaciones
- [ ] Activar/desactivar cada tipo
- [ ] Definir umbrales (ej: notificar si compra > 10 TON)
- [ ] Horario de no molestar (opcional)

---

## ═══════════════════════════════════════
## FASE 27.14: BACKUP Y MANTENIMIENTO ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟡 ALTA
**Agente:** 🟡 BACKEND API

### 27.14.1 - Backups
- [ ] Último backup realizado
- [ ] Crear backup manual
- [ ] Descargar backup
- [ ] Programar backups automáticos

### 27.14.2 - Estado del Servidor
- [ ] Uso de CPU
- [ ] Uso de memoria RAM
- [ ] Uso de disco
- [ ] Conexiones activas

### 27.14.3 - Acciones de Mantenimiento
- [ ] Limpiar cache
- [ ] Limpiar sesiones expiradas
- [ ] Limpiar logs antiguos
- [ ] Reiniciar servicios

---

## ═══════════════════════════════════════
## FASE 27.15: ACCESO Y SESIONES ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟡 ALTA
**Agente:** 🟢 FRONTEND ADMIN + 🟡 BACKEND API

### 27.15.1 - Sesiones Activas
- [ ] Lista de sesiones activas de TODOS los usuarios
- [ ] Usuario, IP, Dispositivo, Última actividad
- [ ] Cerrar sesión específica
- [ ] Cerrar TODAS las sesiones de un usuario

### 27.15.2 - Control de IPs
- [ ] Lista de IPs bloqueadas
- [ ] Agregar IP a blacklist
- [ ] Quitar IP de blacklist
- [ ] Whitelist de IPs para admin
- [ ] Ver historial de bloqueos

### 27.15.3 - Forzar Logout
- [ ] Forzar logout de un usuario específico
- [ ] Forzar logout de TODOS los usuarios
- [ ] Excluir admins del logout masivo

---

## ═══════════════════════════════════════
## FASE 27.16-27.25: FUNCIONALIDADES AVANZADAS ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟢 MEDIA
**Estado:** Pendiente - Ver detalle completo en secciones expandidas

- 27.16: Centro de Vigilancia en Tiempo Real
- 27.17: Perfil Completo del Usuario (Vista 360°)
- 27.18: Sistema de Puntuación de Riesgo
- 27.19: Modo Shadow (Impersonación Avanzada)
- 27.20: Sistema de Etiquetas y Clasificación
- 27.21: Comunicación Directa con Usuarios
- 27.22: Detector de Cuentas Relacionadas
- 27.23: Gestión de Verificaciones
- 27.24: Reportes y Exportaciones Avanzadas
- 27.25: Monitoreo de Patrones y Anomalías

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 28: PERFIL DE USUARIO COMPLETO ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** 🟡 ALTA  
**Agente:** 🔵 FRONTEND USUARIO + 🟡 BACKEND API
**Archivos Frontend:** `static/js/app.js`, `static/css/styles.css`, `templates/index.html`
**Archivos Backend:** `app.py`, `tracking/database.py`

### OBJETIVO:
Rediseñar el perfil de usuario con estilo profesional tipo Instagram/Binance

### FASES:
- 28.1: Header del Perfil (avatar, stats, botones)
- 28.2: Información del Perfil (bio, badges, links)
- 28.3: Acciones del Perfil (editar, seguir, compartir)
- 28.4: Contenido del Usuario (grid de publicaciones)
- 28.5: Información Adicional (wallet, badges, links externos)
- 28.6: Diseño Visual Mejorado
- 28.7: Endpoints Backend

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 29: CONFIGURACIÓN COMPLETA DEL USUARIO ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** 🟡 ALTA  
**Agente:** 🔵 FRONTEND USUARIO + 🟡 BACKEND API
**Archivos Frontend:** `static/js/app.js`, `static/css/styles.css`, `templates/index.html`
**Archivos Backend:** `app.py`, `tracking/database.py`, `tracking/security.py`

### OBJETIVO:
Rediseñar la pantalla de Configuración/Ajustes con estilo Telegram/Binance

### FASES:
- 29.1: Estructura Principal
- 29.2: Sección Cuenta
- 29.3: Sección Seguridad
- 29.4: Sección Privacidad
- 29.5: Sección Notificaciones
- 29.6: Sección Apariencia
- 29.7: Sección Wallet
- 29.8: Sección Datos y Almacenamiento
- 29.9: Sección Ayuda
- 29.10: Cerrar Sesión y Eliminar

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 30: CORRECCIONES DE AUDITORÍA - BUNK3R ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** 🔴 CRÍTICA  
**Agregado:** 7 Diciembre 2025  
**Basado en:** AUDITORIA_COMPLETA_BUNK3R.md  
**Tiempo total estimado:** 20 horas

---

### FASE 30.1: CORRECCIÓN DE BLOQUES EXCEPT VACÍOS ✅
**Prioridad:** 🔴 ALTA  
**Tiempo:** 1 hora  
**Agente:** 🟡 BACKEND API  
**Completado:** 7 Diciembre 2025

#### Objetivo:
Corregir los 14 bloques `except:` vacíos que causan errores silenciosos.

#### Tareas:
- [x] app.py:625 - Función is_owner → `except Exception as e:` + logging
- [x] app.py:633 - Función is_test_user → `except Exception as e:` + logging
- [x] app.py:3053 - Pago TON → `except Exception as e:` + logging
- [x] app.py:5507 → `except Exception as e:` + logging
- [x] app.py:5545 → `except Exception as e:` + logging
- [x] app.py:6644 → `except Exception as e:` + logging
- [x] app.py:6947 → `except Exception as e:` + logging
- [x] app.py:6957 → `except Exception as e:` + logging
- [x] app.py:12532 - Analytics → `except Exception as e:` + logging
- [x] app.py:12542 - Analytics → `except Exception as e:` + logging
- [x] email_service.py:58 → `except Exception as e:` + print error
- [x] email_service.py:74 → `except Exception as e:` + print error
- [x] smspool_service.py:43 → `except Exception as e:` + print error
- [x] smspool_service.py:513 → `except Exception as e:` + print error

#### Criterios de éxito:
- [x] 0 bloques except: vacíos en el proyecto
- [x] Todos los errores se registran en logs
- [x] La aplicación no crashea silenciosamente

---

### FASE 30.2: SANITIZACIÓN INNERHTML (XSS PREVENTION) 🔄
**Prioridad:** 🔴 CRÍTICA  
**Tiempo:** 4 horas  
**Agente:** 🔵 FRONTEND USUARIO + 🟢 FRONTEND ADMIN
**Progreso:** 85% - 7 Diciembre 2025

#### Objetivo:
Implementar DOMPurify para sanitizar los 351 usos de innerHTML.

#### Tareas:
- [x] Añadir DOMPurify CDN en <head> de todos los templates:
  - [x] templates/index.html (ya tenía)
  - [x] templates/admin.html (ya tenía)
  - [x] templates/virtual_numbers.html (ya tenía)
  - [x] templates/workspace.html (agregado)
  
- [x] Crear función SafeDOM.setHTML() en static/js/utils.js (global):
```javascript
const SafeDOM = {
    setHTML: function(element, html) {
        if (typeof DOMPurify !== 'undefined') {
            element.innerHTML = DOMPurify.sanitize(html, {
                ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'div', 'span', 
                               'ul', 'ol', 'li', 'img', 'button', 'input', 'label',
                               'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'tr', 'td', 'th'],
                ALLOWED_ATTR: ['href', 'src', 'alt', 'class', 'id', 'style', 'onclick', 
                               'type', 'value', 'placeholder', 'name', 'data-*']
            });
        } else {
            element.innerHTML = html;
        }
        return element;
    }
};
```

- [x] Reemplazar innerHTML en archivos críticos:
  - [x] static/js/app.js - Eliminada duplicación SafeDOM, usa global de utils.js
  - [x] static/js/publications.js - renderFeed() usa SafeDOM.setHTML()
  - [x] static/js/admin.js - renderUsersTable() usa SafeDOM.setHTML()
  - [ ] static/js/ai-chat.js - Pendiente (menor prioridad)
  - [ ] static/js/virtual-numbers.js - Pendiente (menor prioridad)
  - [ ] static/js/workspace.js - Pendiente (menor prioridad)

**NOTA:** El código ya usa escapeHtml(), escapeAttribute(), sanitizeForJs() extensivamente (133+ usos) para sanitizar contenido de usuarios antes de inyectarlo. SafeDOM proporciona una capa adicional de protección.

**MEJORA ADICIONAL (7 Dic 2025):**
- [x] Añadida función escapeForOnclick() en utils.js para escapar valores en onclick handlers
- [x] admin.js renderUsersTable() ahora usa escapeForOnclick() para user_id en handlers onclick
- [ ] **PENDIENTE**: Migrar todos los onclick handlers a event delegation (arquitectura más segura)

#### Patrón de reemplazo:
```
ANTES: element.innerHTML = htmlContent;
DESPUÉS: SafeDOM.setHTML(element, htmlContent);
```

#### Excepciones (NO sanitizar):
- innerHTML = '' (limpiar elemento)
- innerHTML = texto_estático_sin_variables
- innerHTML = número.toString()

#### Criterios de éxito:
- [x] DOMPurify cargado en todos los templates
- [x] SafeDOM.setHTML() disponible globalmente (window.SafeDOM)
- [x] Funciones de escape (escapeHtml, escapeAttribute, sanitizeForJs) usadas en 133+ lugares
- [x] La aplicación funciona igual que antes
- [ ] Completar reemplazo en archivos restantes (ai-chat.js, virtual-numbers.js, workspace.js)

---

### FASE 30.3: HEADERS CSP (CONTENT SECURITY POLICY) ⏳
**Prioridad:** 🟠 MEDIA  
**Tiempo:** 1 hora  
**Agente:** 🟡 BACKEND API

#### Objetivo:
Implementar Content Security Policy headers para prevenir inyecciones.

#### Tareas:
- [ ] Crear middleware @app.after_request en app.py:
```python
@app.after_request
def add_security_headers(response):
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://telegram.org; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https: blob:; "
        "connect-src 'self' https://api.telegram.org https://*.ton.org wss://*; "
        "frame-src 'self' https://telegram.org; "
        "object-src 'none'; "
        "base-uri 'self';"
    )
    response.headers['Content-Security-Policy'] = csp
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response
```

- [ ] Configurar flag para desarrollo vs producción
- [ ] Verificar que Telegram WebApp sigue funcionando
- [ ] Verificar que TON Connect sigue funcionando

#### Criterios de éxito:
- [ ] Headers CSP presentes en todas las respuestas
- [ ] No hay errores de CSP en consola del navegador

---

### FASE 30.4: LIMPIEZA DE IMPORTS NO USADOS ⏳
**Prioridad:** 🟠 MEDIA  
**Tiempo:** 1 hora  
**Agente:** 🟡 BACKEND API

#### Objetivo:
Limpiar los imports no utilizados reportados por LSP.

#### Tareas:
- [ ] Limpiar imports en app.py (364 diagnósticos LSP)
- [ ] Limpiar imports en tracking/ai_service.py (17 diagnósticos LSP)
- [ ] Verificar que la aplicación inicia sin errores
- [ ] Ejecutar LSP para confirmar 0 warnings de imports

#### Criterios de éxito:
- [ ] 0 warnings de imports no usados en LSP
- [ ] Todas las funciones siguen operativas

---

### FASE 30.5: SESIONES PERSISTENTES ⏳
**Prioridad:** 🟡 MEDIA-BAJA  
**Tiempo:** 2 horas  
**Agente:** 🟡 BACKEND API

#### Objetivo:
Migrar sesiones de memoria a base de datos para persistencia.

#### Tareas:
- [ ] Añadir Flask-Session a requirements.txt
- [ ] Configurar SESSION_TYPE = 'filesystem' o 'sqlalchemy'
- [ ] Crear tabla flask_sessions si se usa sqlalchemy
- [ ] Migrar demo_2fa_sessions de diccionario a tabla BD:
```sql
CREATE TABLE demo_2fa_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);
```
- [ ] Verificar que login/logout funcionan correctamente
- [ ] Verificar expiración automática

#### Criterios de éxito:
- [ ] Sesiones persisten después de reiniciar servidor
- [ ] demo_2fa_sessions en base de datos

---

### FASE 30.6: DOCUMENTACIÓN DE APIs ⏳
**Prioridad:** 🟢 BAJA  
**Tiempo:** 3 horas  
**Agente:** 🟡 BACKEND API

#### Objetivo:
Crear documentación completa de las 311 rutas API.

#### Tareas:
- [ ] Crear archivo docs/API_DOCUMENTATION.md
- [ ] Documentar endpoints prioritarios:
  - [ ] API de Autenticación (7 rutas 2FA)
  - [ ] API de Wallet/Pagos (18 rutas)
  - [ ] API de B3C Token (10 rutas)
  - [ ] API de Admin críticas (30 rutas)
- [ ] Incluir ejemplos request/response para cada endpoint
- [ ] Documentar códigos de error

#### Formato por endpoint:
```markdown
### [MÉTODO] /api/ruta
**Descripción:** Qué hace
**Auth:** SÍ/NO
**Rate Limit:** X/min
**Request:** { campos }
**Response:** { ejemplo }
```

---

### FASE 30.7: TESTS AUTOMATIZADOS ⏳
**Prioridad:** 🟢 BAJA  
**Tiempo:** 8 horas  
**Agente:** 🟡 BACKEND API

#### Objetivo:
Implementar suite de tests para funcionalidades críticas.

#### Estructura:
```
tests/
├── __init__.py
├── conftest.py
├── test_auth.py
├── test_2fa.py
├── test_wallet.py
├── test_b3c.py
├── test_trackings.py
├── test_publications.py
├── test_admin.py
└── test_security.py
```

#### Dependencias:
```
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0
```

#### Tareas:
- [ ] Configurar pytest y fixtures
- [ ] Tests de autenticación (4 tests)
- [ ] Tests de 2FA (4 tests)
- [ ] Tests de wallet (3 tests)
- [ ] Tests de seguridad (4 tests)
- [ ] Cobertura mínima 60%

---

### FASE 30.8: OPTIMIZACIONES DE RENDIMIENTO ⏳
**Prioridad:** 🟢 OPCIONAL  
**Tiempo:** 2-4 horas  
**Agente:** 🟡 BACKEND API

#### Tareas:
- [ ] Añadir índices BD faltantes:
```sql
CREATE INDEX idx_posts_user_created ON posts(user_id, created_at DESC);
CREATE INDEX idx_transactions_user_date ON wallet_transactions(user_id, created_at DESC);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = false;
```
- [ ] Implementar caché con Flask-Caching
- [ ] Añadir paginación a endpoints pesados

---

### FASE 30.9: ENDPOINT LOGOUT DEMO 2FA ⏳
**Prioridad:** 🟢 BAJA  
**Tiempo:** 30 minutos  
**Agente:** 🟡 BACKEND API

#### Objetivo:
Implementar endpoint explícito para cerrar sesión del demo 2FA.

#### Tareas:
- [ ] Crear endpoint `/api/demo/2fa/logout` en app.py
- [ ] Eliminar sesión de demo_2fa_sessions al hacer logout
- [ ] Añadir botón de logout en UI de demo 2FA
- [ ] Verificar que la sesión se cierra correctamente

#### Código sugerido:
```python
@app.route('/api/demo/2fa/logout', methods=['POST'])
def demo_2fa_logout():
    session_id = request.cookies.get('demo_session_id')
    if session_id and session_id in demo_2fa_sessions:
        del demo_2fa_sessions[session_id]
    return jsonify({'success': True, 'message': 'Sesión cerrada'})
```

---

### FASE 30.10: MEJORAR SISTEMA DE LOGS ⏳
**Prioridad:** 🟢 BAJA  
**Tiempo:** 1 hora  
**Agente:** 🟡 BACKEND API

#### Objetivo:
Mejorar el sistema de logs para capturar más información útil.

#### Tareas:
- [ ] Configurar logging estructurado con formato JSON
- [ ] Añadir logs en puntos críticos que faltan:
  - [ ] Inicios de sesión fallidos
  - [ ] Transacciones de wallet
  - [ ] Errores de API externa
  - [ ] Cambios de configuración admin
- [ ] Implementar rotación de logs (max 10MB por archivo)
- [ ] Añadir campo request_id para trazabilidad

#### Configuración sugerida:
```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('logs/app.log', maxBytes=10*1024*1024, backupCount=5)
handler.setFormatter(logging.Formatter(
    '{"time":"%(asctime)s","level":"%(levelname)s","module":"%(module)s","message":"%(message)s"}'
))
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
```

---

## RESUMEN SECCIÓN 30

| Fase | Descripción | Prioridad | Tiempo | Estado |
|------|-------------|-----------|--------|--------|
| 30.1 | Corregir except: vacíos | 🔴 ALTA | 1h | ✅ |
| 30.2 | Implementar DOMPurify | 🔴 CRÍTICA | 4h | ⏳ |
| 30.3 | Headers CSP | 🟠 MEDIA | 1h | ⏳ |
| 30.4 | Limpiar imports | 🟠 MEDIA | 1h | ⏳ |
| 30.5 | Sesiones persistentes | 🟡 MEDIA-BAJA | 2h | ⏳ |
| 30.6 | Documentar APIs | 🟢 BAJA | 3h | ⏳ |
| 30.7 | Tests automatizados | 🟢 BAJA | 8h | ⏳ |
| 30.8 | Optimizaciones BD | 🟢 OPCIONAL | 2-4h | ⏳ |
| 30.9 | Logout demo 2FA | 🟢 BAJA | 30min | ⏳ |
| 30.10 | Mejorar logs | 🟢 BAJA | 1h | ⏳ |

**TOTAL TIEMPO ESTIMADO: ~22 horas**

**ORDEN RECOMENDADO:** 30.1 → 30.2 → 30.3 → 30.4 → 30.5 → 30.9 → 30.10 → 30.6 → 30.7 → 30.8

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 31: AUDITORÍA EXHAUSTIVA - PROBLEMAS DETECTADOS ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** 🔴 CRÍTICA  
**Agregado:** 7 Diciembre 2025  
**Basado en:** Auditoría exhaustiva del código completo  
**Tiempo total estimado:** 30+ horas

---

### FASE 31.1: BOTONES Y FUNCIONES SIN IMPLEMENTAR ⏳
**Prioridad:** 🔴 CRÍTICA  
**Tiempo:** 4 horas  
**Agente:** 🔵 FRONTEND USUARIO + 🟢 FRONTEND ADMIN

#### Objetivo:
Implementar funcionalidad real para botones que actualmente no hacen nada o solo muestran un toast.

#### Tareas:

**31.1.1 - Funciones vacías en app.js:**
- [ ] `setupAvatarUpload()` (línea ~1979-1982) - Función VACÍA, no implementa subida de avatar
- [ ] `viewUserProfile(userId)` (línea ~2132-2135) - Solo muestra toast "Navegando al perfil...", no navega realmente
- [ ] Implementar navegación real a perfil de usuario con datos reales

**31.1.2 - Modales de Admin sin funcionalidad completa:**
- [ ] `showAddBotForm()` - Verificar que el formulario funciona y guarda en BD
- [ ] `showAddProductForm()` - Verificar que el formulario funciona y guarda en BD
- [ ] `closeAdminModal()` - Verificar cierre correcto de todos los modales
- [ ] `saveSystemSettings()` - Verificar que guarda cambios en BD
- [ ] `loadSystemLogs()` - Verificar que carga logs reales

**31.1.3 - MultiBrowser Module:**
- [ ] `closeMultiBrowserModule()` - Verificar implementación completa
- [ ] Revisar toda la funcionalidad del módulo MultiBrowser

#### Criterios de éxito:
- [ ] 0 funciones vacías en el código
- [ ] Todos los botones ejecutan acciones reales
- [ ] Todos los modales abren, funcionan y cierran correctamente

---

### FASE 31.2: SEGURIDAD - CÓDIGO 2FA EN LOGS ✅
**Prioridad:** 🔴 CRÍTICA  
**Tiempo:** 1 hora  
**Agente:** 🟡 BACKEND API  
**Completado:** 7 Diciembre 2025

#### Objetivo:
Eliminar la exposición de códigos 2FA sensibles en los logs del servidor.

#### Problema detectado:
```
INFO:__main__:🔐 DEMO 2FA CODE: 272557
```
El código 2FA se muestra en logs del servidor, lo cual es un riesgo de seguridad en producción.

#### Solución implementada:
- Creada función `log_demo_2fa_code()` en app.py (línea ~112)
- Verifica IS_PRODUCTION y HIDE_2FA_LOGS antes de mostrar código
- En producción solo muestra: "🔐 Demo 2FA code generated for IP: X"
- En desarrollo muestra el código completo para debugging

#### Tareas:
- [x] Buscar todas las líneas que loguean códigos 2FA en app.py
- [x] Reemplazar logs de códigos 2FA con logs genéricos: "2FA code sent to user"
- [x] Solo mantener logging de códigos 2FA en modo DEBUG, NO en producción
- [x] Añadir variable de entorno `HIDE_2FA_LOGS=true` para producción

#### Criterios de éxito:
- [x] 0 códigos 2FA visibles en logs de producción
- [x] Logs de desarrollo mantienen visibilidad para debugging

---

### FASE 31.3: NAVEGACIÓN INCONSISTENTE ⏳
**Prioridad:** 🟡 ALTA  
**Tiempo:** 3 horas  
**Agente:** 🔵 FRONTEND USUARIO

#### Objetivo:
Corregir la navegación que lleva a páginas inexistentes o mal implementadas.

#### Problemas detectados:
- `handleBottomNav()` tiene casos que llaman a `showPage()` con páginas que pueden no existir
- `showPage('marketplace')`, `showPage('bots')`, `showPage('exchange')` - Verificar que existen

#### Tareas:
- [ ] Auditar función `handleBottomNav()` en app.js (línea ~1311)
- [ ] Verificar que cada caso del switch tiene su página correspondiente en el HTML
- [ ] Verificar que `showPage()` valida si la página existe antes de mostrarla
- [ ] Agregar fallback a página de error o home si la página no existe
- [ ] Documentar todas las páginas disponibles en la navegación

#### Páginas a verificar:
- [ ] `marketplace` - ¿Existe en index.html?
- [ ] `bots` - ¿Existe en index.html?
- [ ] `exchange` - ¿Existe en index.html?
- [ ] `ai-chat` - ¿Existe en index.html?
- [ ] `wallet` - ¿Existe en index.html?
- [ ] `notifications` - ¿Existe en index.html?
- [ ] `profile` - ¿Existe en index.html?
- [ ] `home` - ¿Existe en index.html?

#### Criterios de éxito:
- [ ] Todas las navegaciones llevan a páginas que existen
- [ ] Si una página no existe, se muestra mensaje apropiado

---

### FASE 31.4: ESTADÍSTICAS DEL ADMIN SIN DATOS ⏳
**Prioridad:** 🟡 ALTA  
**Tiempo:** 2 horas  
**Agente:** 🟡 BACKEND API + 🟢 FRONTEND ADMIN

#### Objetivo:
Asegurar que el dashboard admin muestre datos reales y maneje correctamente el caso de tablas vacías.

#### Problemas detectados:
- Las estadísticas muestran 0 cuando no hay datos (correcto pero sin indicador visual)
- Falta mensaje de "No hay datos" vs "Cargando..." vs "0 registros"
- No hay datos de prueba para desarrollo

#### Tareas:
- [ ] Agregar indicadores visuales cuando no hay datos vs cuando hay 0 real
- [ ] Crear script de seed data para desarrollo con datos de prueba
- [ ] Verificar que `/api/admin/dashboard/stats` retorna datos correctos
- [ ] Verificar que `/api/admin/dashboard/activity` retorna actividad real
- [ ] Verificar que `/api/admin/dashboard/alerts` retorna alertas reales
- [ ] Verificar que `/api/admin/dashboard/charts` retorna datos de gráficos

#### Tablas a verificar:
- [ ] `users` - ¿Tiene registros?
- [ ] `wallet_transactions` - ¿Tiene registros?
- [ ] `deposit_wallets` - ¿Tiene registros?
- [ ] `security_alerts` - ¿Existe la tabla?

#### Criterios de éxito:
- [ ] Dashboard muestra "Sin datos" cuando tablas están vacías
- [ ] Datos de desarrollo disponibles para testing
- [ ] Estadísticas se actualizan en tiempo real

---

### FASE 31.5: TABLAS DE BD FALTANTES ⏳
**Prioridad:** 🟡 ALTA  
**Tiempo:** 2 horas  
**Agente:** 🟡 BACKEND API

#### Objetivo:
Crear tablas de base de datos que son referenciadas pero podrían no existir.

#### Tablas a verificar/crear:
- [ ] `blocked_ips` - Usada en `/api/admin/blocked-ips`
- [ ] `support_tickets` - Usada en `/api/admin/support/tickets`
- [ ] `faq` - Usada en `/api/admin/faq`
- [ ] `admin_user_notes` - Usada en detalle de usuario admin
- [ ] `security_alerts` - Usada en dashboard de alertas

#### Tareas:
- [ ] Verificar existencia de cada tabla en init_db.py
- [ ] Crear tablas faltantes con estructura correcta
- [ ] Agregar migraciones si es necesario
- [ ] Actualizar endpoints para manejar tablas inexistentes gracefully

#### Criterios de éxito:
- [ ] Todas las tablas referenciadas existen
- [ ] Los endpoints no crashean si la tabla está vacía

---

### FASE 31.6: PWA - PROGRESSIVE WEB APP ⏳
**Prioridad:** 🟠 MEDIA  
**Tiempo:** 4 horas  
**Agente:** 🔵 FRONTEND USUARIO

#### Objetivo:
Implementar soporte completo de PWA para instalación y funcionamiento offline.

#### Componentes faltantes:
- [ ] **manifest.json** - No existe o está incompleto
- [ ] **Service Worker** - No implementado
- [ ] **Iconos PWA** - Diferentes tamaños para dispositivos

#### Tareas:

**31.6.1 - Crear manifest.json:**
```json
{
  "name": "BUNK3R-W3B",
  "short_name": "BUNK3R",
  "description": "Plataforma Web3 con Telegram",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1a1a2e",
  "theme_color": "#0f3460",
  "icons": [
    { "src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

**31.6.2 - Crear Service Worker (sw.js):**
- [ ] Cachear assets estáticos (CSS, JS, imágenes)
- [ ] Implementar estrategia cache-first para assets
- [ ] Implementar network-first para API calls
- [ ] Manejar modo offline con página de fallback

**31.6.3 - Registrar Service Worker:**
- [ ] Agregar script de registro en index.html
- [ ] Manejar actualizaciones del SW

**31.6.4 - Iconos:**
- [ ] Crear iconos en tamaños: 72, 96, 128, 144, 152, 192, 384, 512
- [ ] Agregar apple-touch-icon para iOS

#### Criterios de éxito:
- [ ] App instalable en dispositivos móviles
- [ ] Lighthouse PWA score > 80
- [ ] Funcionalidad básica offline

---

### FASE 31.7: SISTEMA DE BACKUP AUTOMÁTICO ⏳
**Prioridad:** 🟠 MEDIA  
**Tiempo:** 4 horas  
**Agente:** 🟡 BACKEND API

#### Objetivo:
Implementar sistema de backup automático de la base de datos.

#### Componentes faltantes:
- [ ] Backup automático de BD
- [ ] Snapshots periódicos
- [ ] Sistema de restore

#### Tareas:
- [ ] Crear script de backup: `scripts/backup_db.py`
- [ ] Programar backup diario con cron o scheduler
- [ ] Almacenar backups en ubicación segura
- [ ] Implementar endpoint admin para backup manual
- [ ] Implementar endpoint admin para restore
- [ ] Limitar retención de backups (últimos 7 días)

#### Código sugerido:
```python
# scripts/backup_db.py
import subprocess
from datetime import datetime

def create_backup():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"backup_{timestamp}.sql"
    # pg_dump command
    subprocess.run([
        'pg_dump', 
        '-h', os.getenv('PGHOST'),
        '-U', os.getenv('PGUSER'),
        '-d', os.getenv('PGDATABASE'),
        '-f', f'backups/{filename}'
    ])
```

#### Criterios de éxito:
- [ ] Backups automáticos funcionando
- [ ] Admin puede descargar backup manualmente
- [ ] Sistema de restore probado

---

### FASE 31.8: NOTIFICACIONES PUSH TELEGRAM ⏳
**Prioridad:** 🟠 MEDIA  
**Tiempo:** 4 horas  
**Agente:** 🟡 BACKEND API + 🔴 BLOCKCHAIN

#### Objetivo:
Implementar sistema completo de notificaciones via bot de Telegram.

#### Estado actual:
- `BOT_TOKEN` y `CHANNEL_ID` configurados pero no utilizados completamente
- Falta bot de Telegram implementado
- Faltan preferencias de usuario para notificaciones

#### Tareas:
- [ ] Crear servicio `tracking/telegram_bot_service.py`
- [ ] Implementar función `send_notification(user_id, message)`
- [ ] Crear tabla `notification_preferences` en BD
- [ ] Agregar endpoints para gestionar preferencias
- [ ] Implementar notificaciones para:
  - [ ] Depósitos recibidos
  - [ ] Retiros completados
  - [ ] Nuevos seguidores
  - [ ] Menciones en publicaciones
  - [ ] Alertas de seguridad

#### Criterios de éxito:
- [ ] Usuarios reciben notificaciones en Telegram
- [ ] Usuarios pueden activar/desactivar tipos de notificación

---

### FASE 31.9: RATE LIMITING GLOBAL ⏳
**Prioridad:** 🟠 MEDIA  
**Tiempo:** 2 horas  
**Agente:** 🟡 BACKEND API

#### Objetivo:
Implementar rate limiting global por IP para protección contra DDoS.

#### Estado actual:
- Rate limiting solo en algunos endpoints específicos
- No hay protección global por IP
- No hay blacklist automática

#### Tareas:
- [ ] Implementar middleware de rate limit global por IP
- [ ] Configurar límites por tipo de endpoint:
  - [ ] Lectura: 100 req/min
  - [ ] Escritura: 30 req/min
  - [ ] Login: 5 req/min
- [ ] Agregar auto-blacklist tras 1000 requests en 1 minuto
- [ ] Crear endpoint admin para ver IPs bloqueadas
- [ ] Crear endpoint admin para desbloquear IP

#### Código sugerido:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per minute", "1000 per hour"],
    storage_uri="memory://"
)
```

#### Criterios de éxito:
- [ ] Rate limiting activo en todas las rutas
- [ ] Respuestas 429 cuando se excede límite
- [ ] Admin puede ver/gestionar IPs bloqueadas

---

### FASE 31.10: MODO MANTENIMIENTO COMPLETO ⏳
**Prioridad:** 🟢 BAJA  
**Tiempo:** 2 horas  
**Agente:** 🟢 FRONTEND ADMIN + 🟡 BACKEND API

#### Objetivo:
Implementar sistema de mantenimiento con UI para usuarios.

#### Componentes faltantes:
- [ ] Página de mantenimiento para usuarios
- [ ] Programación automática de mantenimiento
- [ ] Banner de "sistema en mantenimiento"

#### Tareas:
- [ ] Crear template `templates/maintenance.html`
- [ ] Agregar middleware que redirige a mantenimiento cuando está activo
- [ ] Crear endpoints admin para activar/desactivar mantenimiento
- [ ] Agregar programación de mantenimiento en admin
- [ ] Permitir bypass para admins durante mantenimiento

#### Criterios de éxito:
- [ ] Admin puede activar modo mantenimiento
- [ ] Usuarios ven página de mantenimiento amigable
- [ ] Admins pueden acceder durante mantenimiento

---

### FASE 31.11: MONITOREO Y ALERTAS DEL SISTEMA ⏳
**Prioridad:** 🟢 BAJA  
**Tiempo:** 3 horas  
**Agente:** 🟡 BACKEND API

#### Objetivo:
Implementar sistema de monitoreo con alertas automáticas.

#### Componentes faltantes:
- [ ] Uptime monitoring
- [ ] Alertas cuando BD está lenta
- [ ] Alertas de errores críticos por Telegram
- [ ] Health check endpoints

#### Tareas:
- [ ] Crear endpoint `/health` para health checks
- [ ] Crear endpoint `/api/admin/system/status` con métricas:
  - [ ] CPU usage
  - [ ] Memory usage
  - [ ] DB connection status
  - [ ] Response time promedio
- [ ] Implementar alertas automáticas cuando:
  - [ ] Response time > 2 segundos
  - [ ] Error rate > 5%
  - [ ] DB disconnected
- [ ] Enviar alertas críticas al Telegram del admin

#### Criterios de éxito:
- [ ] Health check funcionando
- [ ] Admin recibe alertas críticas en Telegram
- [ ] Dashboard muestra estado del sistema

---

### FASE 31.12: CLOUDINARY FALLBACK ⏳
**Prioridad:** 🟢 BAJA  
**Tiempo:** 1 hora  
**Agente:** 🔴 BLOCKCHAIN

#### Objetivo:
Implementar fallback cuando Cloudinary no está configurado.

#### Problema:
Si las credenciales de Cloudinary no están configuradas, las publicaciones con imágenes/videos fallan silenciosamente.

#### Tareas:
- [ ] Verificar existencia de credenciales Cloudinary al iniciar
- [ ] Mostrar error claro cuando se intenta subir sin credenciales
- [ ] Implementar almacenamiento local como fallback opcional
- [ ] Documentar requisitos de Cloudinary

#### Criterios de éxito:
- [ ] Error claro si Cloudinary no está configurado
- [ ] Opción de fallback a almacenamiento local

---

### FASE 31.13: WORKSPACE/AI CONSTRUCTOR ⏳
**Prioridad:** 🟢 BAJA  
**Tiempo:** 3 horas  
**Agente:** 🟡 BACKEND API

#### Objetivo:
Verificar y completar funcionalidad del AI Constructor.

#### Estado actual:
- Endpoint `/api/ai-constructor/process` existe
- Funcionalidad puede no estar completa

#### Tareas:
- [ ] Auditar todos los endpoints de AI Constructor
- [ ] Verificar integración con servicios AI externos
- [ ] Documentar requisitos de API keys AI
- [ ] Implementar fallback si API AI no está disponible
- [ ] Agregar rate limiting específico para AI endpoints

#### Criterios de éxito:
- [ ] AI Constructor funciona completamente
- [ ] Errores manejados gracefully

---

## RESUMEN SECCIÓN 31

| Fase | Descripción | Prioridad | Tiempo | Agente | Estado |
|------|-------------|-----------|--------|--------|--------|
| 31.1 | Botones sin funcionalidad | 🔴 CRÍTICA | 4h | FRONTEND | ⏳ |
| 31.2 | Códigos 2FA en logs | 🔴 CRÍTICA | 1h | BACKEND | ✅ |
| 31.3 | Navegación inconsistente | 🟡 ALTA | 3h | FRONTEND | ⏳ |
| 31.4 | Estadísticas admin vacías | 🟡 ALTA | 2h | BACKEND/ADMIN | ⏳ |
| 31.5 | Tablas BD faltantes | 🟡 ALTA | 2h | BACKEND | ⏳ |
| 31.6 | PWA completo | 🟠 MEDIA | 4h | FRONTEND | ⏳ |
| 31.7 | Backup automático | 🟠 MEDIA | 4h | BACKEND | ⏳ |
| 31.8 | Notificaciones Telegram | 🟠 MEDIA | 4h | BACKEND/BLOCKCHAIN | ⏳ |
| 31.9 | Rate limiting global | 🟠 MEDIA | 2h | BACKEND | ⏳ |
| 31.10 | Modo mantenimiento | 🟢 BAJA | 2h | ADMIN/BACKEND | ⏳ |
| 31.11 | Monitoreo y alertas | 🟢 BAJA | 3h | BACKEND | ⏳ |
| 31.12 | Cloudinary fallback | 🟢 BAJA | 1h | BLOCKCHAIN | ⏳ |
| 31.13 | AI Constructor | 🟢 BAJA | 3h | BACKEND | ⏳ |

**TOTAL TIEMPO ESTIMADO: ~35 horas**

**ORDEN RECOMENDADO POR PRIORIDAD:**
1. 🔴 **CRÍTICO:** 31.1 → 31.2
2. 🟡 **ALTA:** 31.3 → 31.4 → 31.5
3. 🟠 **MEDIA:** 31.6 → 31.7 → 31.8 → 31.9
4. 🟢 **BAJA:** 31.10 → 31.11 → 31.12 → 31.13

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 32: LIMPIEZA Y OPTIMIZACIÓN DE CÓDIGO ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** 🟡 ALTA  
**Agregado:** 7 Diciembre 2025  
**Basado en:** Auditoría de código y búsqueda de patrones  
**Tiempo total estimado:** 15 horas

---

### FASE 32.1: ELIMINAR CONSOLE.LOG DE PRODUCCIÓN ⏳
**Prioridad:** 🟡 ALTA  
**Tiempo:** 2 horas  
**Agente:** 🔵 FRONTEND USUARIO + 🟢 FRONTEND ADMIN

#### Objetivo:
Eliminar o condicionar todos los `console.log` para que no aparezcan en producción.

#### Problema detectado:
- **47 console.log** en `static/js/app.js`
- **5 console.log** en `static/js/ai-chat.js`
- **2 console.log** en `static/js/utils.js`
- **1 console.log** en `static/js/publications.js`

#### Tareas:
- [ ] Crear wrapper de logging condicional:
```javascript
const Logger = {
    isDev: window.location.hostname === 'localhost' || window.location.hostname.includes('replit'),
    log: function(...args) { if(this.isDev) console.log(...args); },
    warn: function(...args) { if(this.isDev) console.warn(...args); },
    error: function(...args) { console.error(...args); } // Errores siempre se muestran
};
```
- [ ] Reemplazar `console.log` por `Logger.log` en app.js (47 instancias)
- [ ] Reemplazar `console.log` por `Logger.log` en ai-chat.js (5 instancias)
- [ ] Reemplazar `console.log` por `Logger.log` en utils.js (2 instancias)
- [ ] Reemplazar `console.log` por `Logger.log` en publications.js (1 instancia)

#### Criterios de éxito:
- [ ] 0 console.log visibles en producción
- [ ] Logs de desarrollo siguen funcionando

---

### FASE 32.2: IMPLEMENTAR LEGIT SMS API ⏳
**Prioridad:** 🟡 ALTA  
**Tiempo:** 4 horas  
**Agente:** 🔴 BLOCKCHAIN

#### Objetivo:
Implementar la integración con Legit SMS que actualmente devuelve error 501.

#### Problema detectado:
```python
# app.py línea 10631
return jsonify({'success': False, 'error': 'Legit SMS not yet implemented'}), 501
```

#### Tareas:
- [ ] Investigar API de Legit SMS (documentación, endpoints, autenticación)
- [ ] Crear servicio `tracking/legitsms_service.py`
- [ ] Implementar endpoints:
  - [ ] Obtener lista de países disponibles
  - [ ] Obtener servicios disponibles
  - [ ] Comprar número
  - [ ] Verificar estado del SMS
  - [ ] Cancelar orden
- [ ] Integrar con el sistema de números virtuales existente
- [ ] Agregar manejo de errores y fallback a SMSPool

#### Criterios de éxito:
- [ ] Legit SMS funcional como alternativa a SMSPool
- [ ] Usuario puede elegir proveedor

---

### FASE 32.3: LIMPIAR DATOS DEMO HARDCODEADOS ⏳
**Prioridad:** 🟠 MEDIA  
**Tiempo:** 2 horas  
**Agente:** 🔵 FRONTEND USUARIO + 🟡 BACKEND API

#### Objetivo:
Eliminar o condicionar datos de demostración que están hardcodeados.

#### Problemas detectados:
- `username: 'demo_user'` en app.js línea 175
- `@demo_user` en templates/index.html línea 1186
- `demo_2fa_sessions` almacenado en memoria (no persistente)

#### Tareas:
- [ ] Verificar que `demo_user` solo aparece cuando no hay usuario real
- [ ] Cambiar placeholder `@demo_user` por `@usuario` o vacío
- [ ] Documentar cuándo se usa el modo demo
- [ ] Asegurar que modo demo NO está activo en producción

#### Criterios de éxito:
- [ ] No hay datos demo visibles para usuarios reales
- [ ] Modo demo claramente documentado

---

### FASE 32.4: FUNCIÓN "EN DESARROLLO" SIN IMPLEMENTAR ⏳
**Prioridad:** 🟠 MEDIA  
**Tiempo:** 3 horas  
**Agente:** 🔵 FRONTEND USUARIO

#### Objetivo:
Implementar o eliminar funciones marcadas como "en desarrollo".

#### Problema detectado:
```javascript
// app.js línea 8193
this.showToast('Funcion en desarrollo', 'info');
```

#### Tareas:
- [ ] Buscar todas las funciones que muestran "en desarrollo"
- [ ] Por cada una, decidir:
  - Implementar la funcionalidad completa
  - O eliminar el botón/link que la llama
- [ ] Documentar cualquier funcionalidad que quede pendiente

#### Criterios de éxito:
- [ ] 0 toasts de "en desarrollo" en la aplicación
- [ ] Todas las funciones implementadas o removidas

---

### FASE 32.5: AUDITAR SECRETOS EN CÓDIGO ⏳
**Prioridad:** 🔴 CRÍTICA  
**Tiempo:** 2 horas  
**Agente:** 🟡 BACKEND API + 🔴 BLOCKCHAIN

#### Objetivo:
Verificar que no hay secretos hardcodeados en el código.

#### Archivos a auditar:
- [ ] `static/js/utils.js` - Buscar API keys
- [ ] `static/js/admin.js` - Buscar tokens
- [ ] `static/js/app.js` - Buscar credenciales
- [ ] `tracking/encryption.py` - Verificar claves
- [ ] `tracking/cloudinary_service.py` - Verificar credenciales
- [ ] `tracking/smspool_service.py` - Verificar API keys
- [ ] `tracking/b3c_service.py` - Verificar wallet keys
- [ ] `tracking/security.py` - Verificar secrets
- [ ] `tracking/wallet_pool_service.py` - Verificar mnemonics
- [ ] `tracking/database.py` - Verificar connection strings

#### Tareas:
- [ ] Revisar cada archivo listado
- [ ] Mover cualquier secreto hardcodeado a variables de entorno
- [ ] Verificar que `.env` está en `.gitignore`
- [ ] Documentar todas las variables de entorno requeridas

#### Criterios de éxito:
- [ ] 0 secretos hardcodeados en el código
- [ ] Todos los secretos en variables de entorno
- [ ] Documentación de variables requeridas

---

### FASE 32.6: VALIDACIÓN DE INPUTS EN FRONTEND ⏳
**Prioridad:** 🟠 MEDIA  
**Tiempo:** 3 horas  
**Agente:** 🔵 FRONTEND USUARIO + 🟢 FRONTEND ADMIN

#### Objetivo:
Agregar validación de inputs del lado del cliente para mejor UX.

#### Tareas:
- [ ] Validar formularios de login/registro
- [ ] Validar formularios de wallet (direcciones, montos)
- [ ] Validar formularios de publicaciones
- [ ] Validar formularios de admin
- [ ] Agregar mensajes de error claros
- [ ] Prevenir envío de formularios inválidos

#### Patrón de validación:
```javascript
function validateWalletAddress(address) {
    // TON address: 48 characters, starts with EQ or UQ
    const tonRegex = /^(EQ|UQ)[A-Za-z0-9_-]{46}$/;
    return tonRegex.test(address);
}
```

#### Criterios de éxito:
- [ ] Todos los formularios tienen validación
- [ ] Mensajes de error claros y útiles
- [ ] Mejor experiencia de usuario

---

### FASE 32.7: OPTIMIZACIÓN DE CARGA DE PÁGINA ⏳
**Prioridad:** 🟢 BAJA  
**Tiempo:** 2 horas  
**Agente:** 🔵 FRONTEND USUARIO

#### Objetivo:
Mejorar el tiempo de carga inicial de la aplicación.

#### Tareas:
- [ ] Minificar archivos CSS en producción
- [ ] Minificar archivos JS en producción
- [ ] Implementar lazy loading para imágenes
- [ ] Agregar prefetch para rutas comunes
- [ ] Optimizar fuentes web
- [ ] Agregar loading skeleton mientras carga contenido

#### Criterios de éxito:
- [ ] Lighthouse Performance score > 80
- [ ] First Contentful Paint < 2 segundos

---

## RESUMEN SECCIÓN 32

| Fase | Descripción | Prioridad | Tiempo | Agente | Estado |
|------|-------------|-----------|--------|--------|--------|
| 32.1 | Eliminar console.log | 🟡 ALTA | 2h | FRONTEND | ⏳ |
| 32.2 | Implementar Legit SMS | 🟡 ALTA | 4h | BLOCKCHAIN | ⏳ |
| 32.3 | Limpiar datos demo | 🟠 MEDIA | 2h | FRONTEND/BACKEND | ⏳ |
| 32.4 | Funciones "en desarrollo" | 🟠 MEDIA | 3h | FRONTEND | ⏳ |
| 32.5 | Auditar secretos | 🔴 CRÍTICA | 2h | BACKEND/BLOCKCHAIN | ⏳ |
| 32.6 | Validación inputs | 🟠 MEDIA | 3h | FRONTEND | ⏳ |
| 32.7 | Optimización carga | 🟢 BAJA | 2h | FRONTEND | ⏳ |

**TOTAL TIEMPO ESTIMADO: ~18 horas**

**ORDEN RECOMENDADO:** 32.5 → 32.1 → 32.2 → 32.3 → 32.4 → 32.6 → 32.7

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 33: FEATURES NUEVAS PENDIENTES ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** 🟢 MEDIA  
**Agregado:** 7 Diciembre 2025  
**Tiempo total estimado:** 6 horas

---

### FASE 33.1: CHAT PRIVADO ENTRE USUARIOS ⏳
**Prioridad:** 🟠 MEDIA  
**Tiempo:** 6 horas  
**Agente:** 🟡 BACKEND API + 🔵 FRONTEND USUARIO

#### Objetivo:
Implementar sistema de mensajes privados.

#### Tareas:
- [ ] Crear tabla `private_messages`
- [ ] Implementar endpoints de envío/recepción
- [ ] Crear UI de chat estilo Telegram
- [ ] Agregar notificaciones de nuevos mensajes
- [ ] Encriptar mensajes end-to-end (opcional)

---

## RESUMEN SECCIÓN 33

| Fase | Descripción | Prioridad | Tiempo | Estado |
|------|-------------|-----------|--------|--------|
| 33.1 | Chat privado | 🟠 MEDIA | 6h | ⏳ |

**TOTAL TIEMPO ESTIMADO: ~6 horas**

---

## PUNTO DE GUARDADO

**Última actualización:** 7 Diciembre 2025 17:30
**Sesión:** 2
**Agente activo:** FRONTEND ADMIN + FRONTEND USUARIO

### Última tarea trabajada
- Sección: 30.2
- Nombre: Sanitización innerHTML (XSS Prevention)
- Estado: En progreso 85%
- Archivos modificados: 
  - templates/workspace.html (agregado DOMPurify CDN)
  - static/js/utils.js (SafeDOM global, escapeForOnclick() para onclick handlers)
  - static/js/app.js (eliminada duplicación de SafeDOM)
  - static/js/publications.js (renderFeed() usa SafeDOM.setHTML())
  - static/js/admin.js (renderUsersTable() usa SafeDOM.setHTML() + escapeForOnclick())

### Próximos pasos
1. Completar reemplazo de innerHTML en ai-chat.js, virtual-numbers.js, workspace.js
2. Continuar con FASE 30.3: Headers CSP
3. Abordar problemas críticos 31.1 (Botones sin funcionalidad)

### Notas para el próximo agente
- SafeDOM está ahora disponible globalmente via window.SafeDOM (definido en utils.js)
- El código ya usa escapeHtml(), escapeAttribute(), sanitizeForJs() en 133+ lugares
- DOMPurify CDN ya está en todos los templates HTML
- La función SafeDOM.setHTML() tiene una opción { allowEvents: true } para permitir onclick handlers

---
