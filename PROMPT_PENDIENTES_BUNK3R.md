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
║ ⏳ PENDIENTES: 27.10→27.25, Sección 28, 29, 30 (Auditoría)       ║
║                                                                  ║
║ 🔴 CRÍTICO: 2 (30.1 except vacíos, 30.2 innerHTML XSS)           ║
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

### FASE 30.1: CORRECCIÓN DE BLOQUES EXCEPT VACÍOS ⏳
**Prioridad:** 🔴 ALTA  
**Tiempo:** 1 hora  
**Agente:** 🟡 BACKEND API

#### Objetivo:
Corregir los 14 bloques `except:` vacíos que causan errores silenciosos.

#### Tareas:
- [ ] app.py:625 - Función is_owner → `except Exception as e:` + logging
- [ ] app.py:633 - Función is_test_user → `except Exception as e:` + logging
- [ ] app.py:3053 - Pago TON → `except Exception as e:` + logging
- [ ] app.py:5507 → `except Exception as e:` + logging
- [ ] app.py:5545 → `except Exception as e:` + logging
- [ ] app.py:6644 → `except Exception as e:` + logging
- [ ] app.py:6947 → `except Exception as e:` + logging
- [ ] app.py:6957 → `except Exception as e:` + logging
- [ ] app.py:12532 - Analytics → `except Exception as e:` + logging
- [ ] app.py:12542 - Analytics → `except Exception as e:` + logging
- [ ] email_service.py:58 → `except Exception as e:` + print error
- [ ] email_service.py:74 → `except Exception as e:` + print error
- [ ] smspool_service.py:43 → `except Exception as e:` + print error
- [ ] smspool_service.py:513 → `except Exception as e:` + print error

#### Criterios de éxito:
- [ ] 0 bloques except: vacíos en el proyecto
- [ ] Todos los errores se registran en logs
- [ ] La aplicación no crashea silenciosamente

---

### FASE 30.2: SANITIZACIÓN INNERHTML (XSS PREVENTION) ⏳
**Prioridad:** 🔴 CRÍTICA  
**Tiempo:** 4 horas  
**Agente:** 🔵 FRONTEND USUARIO + 🟢 FRONTEND ADMIN

#### Objetivo:
Implementar DOMPurify para sanitizar los 351 usos de innerHTML.

#### Tareas:
- [ ] Añadir DOMPurify CDN en <head> de todos los templates:
  - [ ] templates/index.html
  - [ ] templates/admin.html
  - [ ] templates/virtual_numbers.html
  - [ ] templates/workspace.html
  
- [ ] Crear función SafeDOM.setHTML() en static/js/app.js:
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

- [ ] Reemplazar innerHTML en archivos críticos:
  - [ ] static/js/app.js (~150 usos)
  - [ ] static/js/publications.js (~80 usos)
  - [ ] static/js/admin.js (~50 usos)
  - [ ] static/js/ai-chat.js (~30 usos)
  - [ ] static/js/virtual-numbers.js (~20 usos)
  - [ ] static/js/workspace.js (~15 usos)

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
- [ ] DOMPurify cargado en todos los templates
- [ ] SafeDOM.setHTML() usado para contenido dinámico
- [ ] 0 vulnerabilidades XSS detectables
- [ ] La aplicación funciona igual que antes

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

## RESUMEN SECCIÓN 30

| Fase | Descripción | Prioridad | Tiempo | Estado |
|------|-------------|-----------|--------|--------|
| 30.1 | Corregir except: vacíos | 🔴 ALTA | 1h | ⏳ |
| 30.2 | Implementar DOMPurify | 🔴 CRÍTICA | 4h | ⏳ |
| 30.3 | Headers CSP | 🟠 MEDIA | 1h | ⏳ |
| 30.4 | Limpiar imports | 🟠 MEDIA | 1h | ⏳ |
| 30.5 | Sesiones persistentes | 🟡 MEDIA-BAJA | 2h | ⏳ |
| 30.6 | Documentar APIs | 🟢 BAJA | 3h | ⏳ |
| 30.7 | Tests automatizados | 🟢 BAJA | 8h | ⏳ |
| 30.8 | Optimizaciones | 🟢 OPCIONAL | 2-4h | ⏳ |

**ORDEN RECOMENDADO:** 30.1 → 30.2 → 30.3 → 30.4 → 30.5 → 30.6 → 30.7 → 30.8

---

## PUNTO DE GUARDADO

**Última actualización:** 7 Diciembre 2025
**Estado:** Agregada SECCIÓN 30 con tareas de auditoría
**Próximo paso:** Ejecutar fase 30.1 (Corregir except: vacíos)

---
