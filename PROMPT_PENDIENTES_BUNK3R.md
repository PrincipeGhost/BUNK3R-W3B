# PROMPT MAESTRO - BUNK3R-W3B

---

## TABLERO DE INICIO

Al iniciar cada sesión, el agente DEBE mostrar este tablero automáticamente:

```
╔══════════════════════════════════════════════════════════════════╗
║                    🏦 BUNK3R-W3B - ESTADO ACTUAL                 ║
╠══════════════════════════════════════════════════════════════════╣
║ Última actualización: 7 Diciembre 2025 19:30                     ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║ ✅ COMPLETADAS: 9 secciones + 4 críticos resueltos               ║
║    27.1 Dashboard | 27.2 Usuarios (95%) | 27.3 Transacciones     ║
║    27.4 Wallets | 27.5 Contenido | 27.6 Números Virtuales        ║
║    27.7 Bots | 27.8 Logs | 27.9 Analytics                        ║
║                                                                  ║
║ 🔄 EN PROGRESO: Ninguna                                          ║
║                                                                  ║
║ ⏳ PENDIENTES: 27.10→27.25, Secciones 28, 29, 30, 31, 32, 33, 34 ║
║                                                                  ║
║ 🔴 CRÍTICO NUEVO: SECCIÓN 34 - IA BUNK3R CONSTRUCTOR             ║
║    ⏳ 34.1 Conectar frontend con 8 fases                         ║
║    ⏳ 34.2 Expandir capacidades IA (no solo páginas)             ║
║    ⏳ 34.6 Entendimiento de intenciones                          ║
║    ✅ Sistema 8 fases existe pero no se usa                      ║
║    ✅ Multi-proveedor IA configurado                             ║
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

### FASE 30.4: LIMPIEZA DE IMPORTS NO USADOS ✅
**Prioridad:** 🟠 MEDIA  
**Tiempo:** 1 hora  
**Agente:** 🟡 BACKEND API
**Completado:** 7 Diciembre 2025

#### Objetivo:
Limpiar los imports no utilizados reportados por LSP.

#### Tareas:
- [x] Limpiar imports en app.py - Consolidados al principio del archivo
- [x] Limpiar imports en tracking/ai_service.py - Ya estaban correctos
- [x] Verificar que la aplicación inicia sin errores
- [x] Ejecutar LSP para confirmar 0 warnings de imports

#### Cambios realizados:
- Consolidados imports dispersos al principio de app.py (re, html, time, threading, requests, urlparse, defaultdict)
- Eliminados imports duplicados (import time en 3 ubicaciones, import requests duplicado)
- Eliminados imports locales innecesarios dentro de funciones (urlparse)
- Actualizado browser_proxy() para usar `requests` en lugar de alias `req`

#### Criterios de éxito:
- [x] 0 warnings de imports no usados en LSP (los 368 restantes son errores de tipado de Pyright, no imports)
- [x] Todas las funciones siguen operativas

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
| 30.2 | Implementar DOMPurify | 🔴 CRÍTICA | 4h | ✅ |
| 30.3 | Headers CSP | 🟠 MEDIA | 1h | ✅ |
| 30.4 | Limpiar imports | 🟠 MEDIA | 1h | ✅ |
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

## ════════════════════════════════════════════════════════════════
## SECCIÓN 34: SISTEMA IA BUNK3R CONSTRUCTOR ⏳ 🔴 CRÍTICA
## ════════════════════════════════════════════════════════════════

**Prioridad:** 🔴 CRÍTICA  
**Agregado:** 7 Diciembre 2025  
**Tiempo total estimado:** 20+ horas  
**Agente:** 🔵 FRONTEND + 🟡 BACKEND + 🟣 IA

---

### OBJETIVO PRINCIPAL:
Crear un **AI Constructor tipo Replit/Bolt.new** donde la IA BUNK3R pueda:
- Entender lo que el usuario quiere (no solo crear páginas)
- Programar, ejecutar, editar y eliminar archivos
- Ejecutar comandos (npm, pip, etc.)
- Mostrar preview en tiempo real
- Trabajar paso a paso con flujo visible

**Referencia visual:** Como Replit Agent / Bolt.new / Cursor

---

### DIAGNÓSTICO ACTUAL DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────────┐
│  PROBLEMA DETECTADO                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ai-chat.js ──────> /api/ai/code-builder                        │
│                         │                                       │
│                         ▼                                       │
│               ai_service.generate_code()                        │
│                         │                                       │
│                         ▼                                       │
│          GENERA TODO DE UNA VEZ (sin fases, sin plan)           │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  EXISTE PERO NO SE USA:                                         │
│                                                                 │
│  ai_constructor.py ──> 8 FASES completas                        │
│         │                                                       │
│         ├── Fase 1: Analizar intención                          │
│         ├── Fase 2: Investigar                                  │
│         ├── Fase 3: Clarificar (preguntar)                      │
│         ├── Fase 4: Construir prompt                            │
│         ├── Fase 5: Presentar plan                              │
│         ├── Fase 6: Ejecutar                                    │
│         ├── Fase 7: Verificar                                   │
│         └── Fase 8: Entregar                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### ARQUITECTURA DESEADA (Layout 3 columnas)

```
┌─────────────────────────────────────────────────────────────────┐
│  [BUNK3R AI CONSTRUCTOR]                                        │
├─────────────────────────────────────────────────────────────────┤
│                              │                │                 │
│     CHAT CON LA IA           │   WEB PREVIEW  │  ARCHIVOS       │
│     (Lado izquierdo)         │   (Centro)     │  (Derecha)      │
│                              │                │                 │
│  Usuario: Crea un landing    │  ┌──────────┐  │  📁 proyecto/   │
│                              │  │          │  │  ├── index.html │
│  IA: [Fase 1] Analizando...  │  │  PREVIEW │  │  ├── style.css  │
│  IA: [Fase 2] Investigando...│  │  EN VIVO │  │  └── script.js  │
│  IA: [Fase 5] Plan listo...  │  │          │  │                 │
│  IA: ✅ Archivos creados     │  └──────────┘  │                 │
│                              │                │                 │
│  [Escribe tu mensaje...]     │                │                 │
│                              │                │                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### ARCHIVOS INVOLUCRADOS

| Archivo | Función | Estado |
|---------|---------|--------|
| `tracking/ai_constructor.py` | Constructor 8 fases | ✅ Existe, no se usa |
| `tracking/ai_service.py` | Multi-proveedor IA | ✅ Funciona |
| `tracking/ai_flow_logger.py` | Logger de flujo | ✅ Existe |
| `static/js/ai-chat.js` | Frontend IA Builder | ⚠️ Usa endpoint incorrecto |
| `static/js/workspace.js` | Workspace IDE | ⚠️ Solo chat, no genera |
| `static/css/ai-chat.css` | Estilos IA | ✅ Existe |
| `templates/workspace.html` | Layout IDE | ✅ Tiene 3 columnas |
| `app.py` | Endpoints API | ⚠️ Falta conectar |

---

### PROVEEDORES IA CONFIGURADOS

| Prioridad | Proveedor | Modelo | Estado |
|-----------|-----------|--------|--------|
| 1 | Groq | llama-3.3-70b-versatile | ✅ Configurado |
| 2 | Cerebras | llama-3.3-70b | ✅ Configurado |
| 3 | Gemini | gemini-2.0-flash | ✅ Configurado |
| 4 | DeepSeek | deepseek-chat | ✅ Configurado |
| 5 | HuggingFace | Meta-Llama-3-8B | ✅ Configurado |
| Local | DeepSeek V3.2 | via HuggingFace | ⏳ Pendiente como cerebro principal |

---

## ═══════════════════════════════════════
## ANÁLISIS COMPLETO: REPLIT AGENT vs BUNK3R IA
## ═══════════════════════════════════════

### CÓMO TRABAJO YO (REPLIT AGENT) - PARA QUE TU IA APRENDA

```
┌─────────────────────────────────────────────────────────────────┐
│  EJEMPLO: Usuario dice "Agrega autenticación JWT a mi API"     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PASO 1: LEO EL PROYECTO                                        │
│  ├── Abro app.py para ver estructura actual                    │
│  ├── Leo requirements.txt para ver qué dependencias hay        │
│  ├── Busco si ya existe algo de auth                           │
│  └── Entiendo el contexto completo                             │
│                                                                 │
│  PASO 2: CREO UN PLAN                                           │
│  ├── "Voy a hacer esto:"                                        │
│  ├── 1. Instalar PyJWT y bcrypt                                 │
│  ├── 2. Crear modelo User en database.py                        │
│  ├── 3. Crear endpoints /login y /register                      │
│  └── 4. Proteger rutas existentes                               │
│                                                                 │
│  PASO 3: EJECUTO PASO A PASO                                    │
│  ├── Corro: pip install PyJWT bcrypt                            │
│  ├── EDITO app.py (no reemplazo, agrego código)                 │
│  ├── CREO tracking/auth.py con la lógica                        │
│  └── MUESTRO cada cambio al usuario                             │
│                                                                 │
│  PASO 4: VERIFICO                                                │
│  ├── Reinicio el servidor                                       │
│  ├── Leo los logs buscando errores                              │
│  ├── Si hay error → LO CORRIJO automáticamente                  │
│  └── Confirmo que funciona                                      │
│                                                                 │
│  PASO 5: ENTREGO                                                 │
│  └── "Listo, la autenticación está implementada"                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### CÓMO TRABAJA TU IA (BUNK3R) ACTUALMENTE

```
┌─────────────────────────────────────────────────────────────────┐
│  EJEMPLO: Usuario dice "Agrega autenticación JWT a mi API"     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PASO 1: DETECTA INTENCIÓN                                      │
│  └── IntentParser detecta: CREAR_API (✅ bien)                  │
│                                                                 │
│  PASO 2: GENERA HTML/CSS/JS                                     │
│  └── ¿¿¿ Genera un formulario de login en HTML ???              │
│                                                                 │
│  ❌ NO lee el código existente                                  │
│  ❌ NO entiende que es Python/Flask                             │
│  ❌ NO instala dependencias                                     │
│  ❌ NO edita archivos, solo genera nuevos                       │
│  ❌ NO verifica errores                                         │
│  ❌ NO corrige si falla                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### COMPARACIÓN DE HERRAMIENTAS

| Herramienta | Replit Agent | BUNK3R IA | Prioridad |
|-------------|--------------|-----------|-----------|
| Leer archivos del proyecto | ✅ | ❌ | 🔴 CRÍTICA |
| Editar archivos existentes | ✅ | ❌ | 🔴 CRÍTICA |
| Crear archivos nuevos | ✅ | ⚠️ Solo HTML/CSS/JS | 🔴 CRÍTICA |
| Eliminar archivos | ✅ | ❌ | 🟡 ALTA |
| Ejecutar comandos (npm, pip) | ✅ | ❌ | 🔴 CRÍTICA |
| Ver logs del servidor | ✅ | ❌ | 🔴 CRÍTICA |
| Buscar en código (grep) | ✅ | ❌ | 🟡 ALTA |
| Instalar dependencias | ✅ | ❌ | 🔴 CRÍTICA |
| Ejecutar SQL | ✅ | ❌ | 🟠 MEDIA |
| Tomar screenshots | ✅ | ❌ | 🟠 MEDIA |
| Buscar en internet | ✅ | ❌ | 🟠 MEDIA |
| Corregir errores automático | ✅ | ❌ | 🔴 CRÍTICA |
| Entender múltiples lenguajes | ✅ | ❌ Solo HTML/CSS/JS | 🔴 CRÍTICA |
| Crear subdirectorios | ✅ | ❌ | 🟡 ALTA |
| Listar estructura proyecto | ✅ | ❌ | 🟡 ALTA |

---

### TIPOS DE INTENCIONES

| Intención | Replit Agent | BUNK3R IA | Estado |
|-----------|--------------|-----------|--------|
| "Crea una página/landing" | ✅ | ✅ | Funciona |
| "Crea un dashboard" | ✅ | ✅ | Funciona |
| "Crea un formulario" | ✅ | ✅ | Funciona |
| "Crea una API" | ✅ | ⚠️ Genera HTML | FALTA |
| "Modifica este archivo" | ✅ | ❌ | FALTA |
| "Arregla este error" | ✅ | ❌ | FALTA |
| "Explica este código" | ✅ | ⚠️ Responde texto | Parcial |
| "Optimiza esto" | ✅ | ❌ | FALTA |
| "Ejecuta npm install" | ✅ | ❌ | FALTA |
| "Instala Flask" | ✅ | ❌ | FALTA |
| "Elimina este archivo" | ✅ | ❌ | FALTA |
| "Muéstrame app.py" | ✅ | ❌ | FALTA |
| "¿Por qué falla esto?" | ✅ | ❌ | FALTA |
| "Refactoriza este código" | ✅ | ❌ | FALTA |
| "Testea esta función" | ✅ | ❌ | FALTA |
| "Documenta esto" | ✅ | ❌ | FALTA |
| "Despliega el proyecto" | ✅ | ❌ | FALTA |
| "Crea base de datos" | ✅ | ❌ | FALTA |
| "Agrega esta tabla SQL" | ✅ | ❌ | FALTA |

---

### LO QUE YA TIENE TU IA (BIEN PROGRAMADO)

| Componente | Archivo | Estado | Descripción |
|------------|---------|--------|-------------|
| `IntentParser` | ai_constructor.py | ✅ Existe | Detecta tipo de tarea |
| `ResearchEngine` | ai_constructor.py | ✅ Existe | Investiga mejores prácticas |
| `ClarificationManager` | ai_constructor.py | ✅ Existe | Hace preguntas si falta info |
| `PromptBuilder` | ai_constructor.py | ✅ Existe | Construye prompt maestro |
| `TaskOrchestrator` | ai_constructor.py | ✅ Existe | Crea plan de tareas |
| `OutputVerifier` | ai_constructor.py | ✅ Existe | Verifica código generado |
| `ConstructorSession` | ai_constructor.py | ✅ Existe | Mantiene estado de sesión |
| Multi-proveedor IA | ai_service.py | ✅ Funciona | 5+ proveedores con fallback |
| Auto-rectificación | ai_service.py | ✅ Funciona | Corrige respuestas malas |
| Flow Logger | ai_flow_logger.py | ✅ Existe | Debug del flujo |

---

### LO QUE LE FALTA A TU IA (NUEVAS TAREAS)

```python
class BunkrAICapabilities:
    """Capacidades que DEBE tener BUNK3R IA"""
    
    # ════════════════════════════════════════════════════════════
    # GRUPO 1: LEER CONTEXTO (Prioridad 🔴 CRÍTICA)
    # ════════════════════════════════════════════════════════════
    
    def read_file(self, path: str) -> str:
        """Leer cualquier archivo del proyecto"""
        # Permite a la IA entender el código existente
        pass
    
    def list_directory(self, path: str = ".") -> List[str]:
        """Ver estructura de carpetas"""
        # Permite a la IA entender la estructura del proyecto
        pass
    
    def search_in_code(self, query: str, path: str = ".") -> List[Match]:
        """Buscar texto/patrón en todo el código"""
        # Como grep, para encontrar cosas
        pass
    
    def get_file_info(self, path: str) -> Dict:
        """Obtener info de un archivo (tamaño, tipo, modificado)"""
        pass
    
    # ════════════════════════════════════════════════════════════
    # GRUPO 2: MODIFICAR PROYECTO (Prioridad 🔴 CRÍTICA)
    # ════════════════════════════════════════════════════════════
    
    def create_file(self, path: str, content: str) -> bool:
        """Crear archivo nuevo (cualquier tipo, no solo HTML)"""
        # .py, .js, .json, .sql, .md, etc.
        pass
    
    def edit_file(self, path: str, old_content: str, new_content: str) -> bool:
        """EDITAR archivo existente (no reemplazar todo)"""
        # Crucial: editar una sección sin perder el resto
        pass
    
    def replace_in_file(self, path: str, find: str, replace: str) -> bool:
        """Reemplazar texto en archivo"""
        pass
    
    def append_to_file(self, path: str, content: str) -> bool:
        """Agregar contenido al final de un archivo"""
        pass
    
    def delete_file(self, path: str, confirm: bool = True) -> bool:
        """Eliminar archivo (con confirmación)"""
        pass
    
    def create_directory(self, path: str) -> bool:
        """Crear carpeta/directorio"""
        pass
    
    def move_file(self, old_path: str, new_path: str) -> bool:
        """Mover/renombrar archivo"""
        pass
    
    # ════════════════════════════════════════════════════════════
    # GRUPO 3: EJECUTAR COMANDOS (Prioridad 🔴 CRÍTICA)
    # ════════════════════════════════════════════════════════════
    
    def run_command(self, command: str, timeout: int = 60) -> CommandResult:
        """Ejecutar comando del sistema"""
        # npm install, pip install, python script.py, etc.
        pass
    
    def run_server(self, command: str, port: int) -> ServerProcess:
        """Iniciar servidor (Flask, Node, etc.)"""
        pass
    
    def stop_server(self, process_id: str) -> bool:
        """Detener servidor"""
        pass
    
    def restart_server(self) -> bool:
        """Reiniciar servidor actual"""
        pass
    
    # ════════════════════════════════════════════════════════════
    # GRUPO 4: VERIFICAR Y DEBUGGEAR (Prioridad 🔴 CRÍTICA)
    # ════════════════════════════════════════════════════════════
    
    def read_logs(self, lines: int = 100) -> List[str]:
        """Leer logs del servidor"""
        pass
    
    def check_errors(self) -> List[Error]:
        """Detectar errores en consola/logs"""
        pass
    
    def analyze_error(self, error: str) -> ErrorAnalysis:
        """Analizar un error y sugerir solución"""
        pass
    
    def auto_fix_error(self, error: Error) -> bool:
        """Intentar corregir error automáticamente"""
        pass
    
    def take_screenshot(self, url: str) -> str:
        """Tomar captura de pantalla del resultado"""
        pass
    
    # ════════════════════════════════════════════════════════════
    # GRUPO 5: INTELIGENCIA AVANZADA (Prioridad 🟡 ALTA)
    # ════════════════════════════════════════════════════════════
    
    def understand_project(self) -> ProjectAnalysis:
        """Entender el proyecto completo (lenguaje, estructura, dependencias)"""
        pass
    
    def detect_language(self, file_path: str = None) -> str:
        """Detectar lenguaje de programación"""
        # Python, JavaScript, TypeScript, etc.
        pass
    
    def read_dependencies(self) -> Dict[str, str]:
        """Leer dependencias (requirements.txt, package.json, etc.)"""
        pass
    
    def suggest_improvements(self, file_path: str) -> List[Suggestion]:
        """Sugerir mejoras para un archivo"""
        pass
    
    # ════════════════════════════════════════════════════════════
    # GRUPO 6: BASE DE DATOS (Prioridad 🟠 MEDIA)
    # ════════════════════════════════════════════════════════════
    
    def execute_sql(self, query: str) -> QueryResult:
        """Ejecutar consulta SQL"""
        pass
    
    def get_tables(self) -> List[str]:
        """Listar tablas de la base de datos"""
        pass
    
    def describe_table(self, table_name: str) -> TableSchema:
        """Describir estructura de una tabla"""
        pass
    
    # ════════════════════════════════════════════════════════════
    # GRUPO 7: BÚSQUEDA EXTERNA (Prioridad 🟠 MEDIA)
    # ════════════════════════════════════════════════════════════
    
    def web_search(self, query: str) -> List[SearchResult]:
        """Buscar en internet"""
        pass
    
    def fetch_documentation(self, library: str) -> str:
        """Obtener documentación de una librería"""
        pass
```

---

## ════════════════════════════════════════════════════════════════
## ESPECIFICACIÓN TÉCNICA COMPLETA: AIToolkit
## ════════════════════════════════════════════════════════════════

### CLASE PRINCIPAL: AIToolkit

```python
class AIToolkit:
    """
    Herramientas que la IA puede usar para interactuar con el proyecto.
    INSPIRADO EN: Replit Agent tools (read, write, edit, bash, grep)
    
    ARCHIVO: tracking/ai_toolkit.py
    """
    
    def __init__(self, project_root: str, user_id: str):
        self.project_root = project_root
        self.user_id = user_id
        self.logger = AIFlowLogger()
        self.operation_history = []
    
    # ═══════════════════════════════════════════════════════════
    # GRUPO 1: LECTURA DE ARCHIVOS
    # ═══════════════════════════════════════════════════════════
    
    def read_file(self, path: str, limit: int = 1000, offset: int = 0) -> Dict:
        """
        Lee el contenido de un archivo.
        
        Parámetros:
        - path: Ruta relativa al proyecto (ej: "app.py", "static/js/main.js")
        - limit: Número máximo de líneas a leer (default: 1000)
        - offset: Línea desde la que empezar (default: 0)
        
        Retorna:
        {
            "success": True,
            "content": "contenido del archivo...",
            "lines": 150,
            "language": "python",
            "truncated": False
        }
        
        Seguridad:
        - Validar que path no salga del proyecto (no ../)
        - Validar que archivo existe
        - Limitar tamaño máximo de lectura
        
        Uso típico por la IA:
        - ANTES de editar cualquier archivo
        - Para entender código existente
        - Para ver qué hay en el proyecto
        
        Ejemplo:
        content = toolkit.read_file("app.py")
        content = toolkit.read_file("static/js/app.js", limit=500)
        content = toolkit.read_file("app.py", offset=100, limit=50)  # líneas 100-150
        """
        # Validar seguridad
        safe_path = self._validate_path(path)
        if not safe_path:
            return {"success": False, "error": "Ruta no permitida"}
        
        full_path = os.path.join(self.project_root, safe_path)
        
        if not os.path.exists(full_path):
            return {"success": False, "error": f"Archivo no existe: {path}"}
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            selected_lines = lines[offset:offset + limit]
            content = ''.join(selected_lines)
            
            return {
                "success": True,
                "content": content,
                "lines": total_lines,
                "language": self._detect_language(path),
                "truncated": (offset + limit) < total_lines
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_directory(self, path: str = ".", recursive: bool = True, 
                       max_files: int = 500) -> Dict:
        """
        Lista archivos y carpetas.
        
        Parámetros:
        - path: Ruta relativa (default: raíz del proyecto)
        - recursive: Si incluir subcarpetas (default: True)
        - max_files: Límite de archivos a listar (default: 500)
        
        Retorna:
        {
            "success": True,
            "files": [
                {"path": "app.py", "type": "file", "size": 1234},
                {"path": "static/", "type": "directory"},
                {"path": "static/js/main.js", "type": "file", "size": 567}
            ],
            "total": 45
        }
        
        Uso típico:
        - Para entender estructura del proyecto
        - Para encontrar archivos
        - Al inicio de cada sesión
        
        Ejemplo:
        files = toolkit.list_directory(".")  # Todo el proyecto
        files = toolkit.list_directory("static/js", recursive=False)  # Solo JS
        """
        pass
    
    def search_code(self, pattern: str, path: str = ".", 
                    file_type: str = None, case_sensitive: bool = False) -> Dict:
        """
        Busca texto/patrón en archivos (como grep).
        
        Parámetros:
        - pattern: Texto o regex a buscar
        - path: Dónde buscar (default: todo el proyecto)
        - file_type: Filtrar por extensión (ej: "py", "js")
        - case_sensitive: Si distinguir mayúsculas/minúsculas
        
        Retorna:
        {
            "success": True,
            "matches": [
                {
                    "file": "app.py",
                    "line": 45,
                    "content": "def login(username, password):",
                    "context_before": "# Función de login",
                    "context_after": "    user = User.query.filter_by..."
                }
            ],
            "total_matches": 5
        }
        
        Uso típico:
        - Encontrar dónde se usa una función
        - Buscar imports específicos
        - Encontrar código con errores
        
        Ejemplo:
        matches = toolkit.search_code("def login", ".")
        matches = toolkit.search_code("import flask", ".", file_type="py")
        matches = toolkit.search_code("getUserId", "static/js")
        matches = toolkit.search_code("TODO|FIXME", ".", file_type="py")
        """
        pass
    
    def get_file_info(self, path: str) -> Dict:
        """
        Obtiene información de un archivo.
        
        Retorna:
        {
            "exists": True,
            "path": "app.py",
            "size": 15234,
            "lines": 456,
            "language": "python",
            "last_modified": "2025-12-07 20:00:00",
            "permissions": "rw-r--r--"
        }
        """
        pass
    
    # ═══════════════════════════════════════════════════════════
    # GRUPO 2: ESCRITURA Y EDICIÓN DE ARCHIVOS
    # ═══════════════════════════════════════════════════════════
    
    def write_file(self, path: str, content: str) -> Dict:
        """
        Crea o sobrescribe un archivo.
        
        Parámetros:
        - path: Ruta del archivo (crea carpetas intermedias si no existen)
        - content: Contenido del archivo
        
        Retorna:
        {
            "success": True,
            "path": "tracking/auth.py",
            "size": 1234,
            "created": True  # o False si sobrescribió
        }
        
        IMPORTANTE: 
        - Para archivos existentes, preferir edit_file
        - Esto sobrescribe TODO el contenido
        
        Seguridad:
        - Validar que path está dentro del proyecto
        - No permitir sobrescribir archivos críticos sin confirmación
        - Logging de todas las operaciones
        
        Ejemplo:
        toolkit.write_file("tracking/auth.py", auth_code)
        toolkit.write_file("config.json", json.dumps(config, indent=2))
        toolkit.write_file("static/css/custom.css", css_styles)
        """
        pass
    
    def edit_file(self, path: str, old_string: str, new_string: str) -> Dict:
        """
        Edita una sección específica de un archivo.
        
        ⚠️ ESTA ES LA HERRAMIENTA MÁS IMPORTANTE ⚠️
        Permite modificar código sin perder el resto del archivo.
        
        Parámetros:
        - path: Archivo a editar
        - old_string: Texto exacto a reemplazar
        - new_string: Nuevo texto
        
        Retorna:
        {
            "success": True,
            "path": "app.py",
            "changes": 1,  # número de reemplazos hechos
            "diff": "..."  # diff visual de los cambios
        }
        
        REGLAS CRÍTICAS:
        1. SIEMPRE leer el archivo primero con read_file
        2. old_string debe ser EXACTO (incluyendo espacios/indentación)
        3. Incluir suficiente contexto para que sea único
        4. Si old_string no se encuentra, retornar error
        
        Uso típico:
        - Agregar imports
        - Modificar funciones existentes
        - Corregir errores
        - Agregar nuevo código en lugar específico
        
        Ejemplo:
        # Agregar un import
        toolkit.edit_file("app.py", 
            "from flask import Flask",
            "from flask import Flask\nfrom flask_login import LoginManager"
        )
        
        # Corregir un error
        toolkit.edit_file("app.py",
            "def login():\n    return None",
            "def login():\n    # Validación añadida\n    if not user:\n        return None"
        )
        
        # Agregar una ruta
        toolkit.edit_file("app.py",
            "@app.route('/dashboard')",
            "@app.route('/profile')\ndef profile():\n    return render_template('profile.html')\n\n@app.route('/dashboard')"
        )
        """
        # 1. Leer archivo actual
        current = self.read_file(path)
        if not current["success"]:
            return {"success": False, "error": current["error"]}
        
        content = current["content"]
        
        # 2. Verificar que old_string existe
        if old_string not in content:
            return {
                "success": False, 
                "error": "No se encontró el texto a reemplazar",
                "hint": "Asegúrate de copiar el texto exacto incluyendo espacios"
            }
        
        # 3. Contar ocurrencias
        count = content.count(old_string)
        if count > 1:
            return {
                "success": False,
                "error": f"Se encontraron {count} coincidencias. Incluye más contexto para que sea único."
            }
        
        # 4. Hacer el reemplazo
        new_content = content.replace(old_string, new_string)
        
        # 5. Guardar el archivo
        result = self.write_file(path, new_content)
        
        # 6. Generar diff
        diff = self._generate_diff(content, new_content)
        
        return {
            "success": True,
            "path": path,
            "changes": 1,
            "diff": diff
        }
    
    def append_to_file(self, path: str, content: str) -> Dict:
        """
        Agrega contenido al final de un archivo.
        
        Uso típico:
        - Agregar nuevas funciones
        - Agregar nuevas rutas
        - Agregar estilos CSS
        
        Ejemplo:
        toolkit.append_to_file("app.py", "\n@app.route('/new')\ndef new():\n    pass")
        toolkit.append_to_file("static/css/styles.css", "\n.new-class { color: red; }")
        """
        pass
    
    def delete_file(self, path: str, confirm: bool = True) -> Dict:
        """
        Elimina un archivo.
        
        SEGURIDAD: 
        - Siempre pedir confirmación al usuario
        - Logging de archivos eliminados
        - No permitir eliminar archivos críticos
        
        Archivos protegidos (no se pueden eliminar):
        - app.py, main.py (archivo principal)
        - requirements.txt, package.json
        - .env, config.py
        
        Ejemplo:
        result = toolkit.delete_file("temp.py")
        result = toolkit.delete_file("old_backup.txt")
        """
        pass
    
    def create_directory(self, path: str) -> Dict:
        """
        Crea una carpeta.
        
        Ejemplo:
        toolkit.create_directory("tracking/auth")
        toolkit.create_directory("static/uploads/images")
        """
        pass
    
    def move_file(self, old_path: str, new_path: str) -> Dict:
        """
        Mueve o renombra un archivo.
        
        Ejemplo:
        toolkit.move_file("temp.py", "tracking/temp.py")
        toolkit.move_file("old_name.py", "new_name.py")
        """
        pass
    
    def copy_file(self, source: str, destination: str) -> Dict:
        """
        Copia un archivo.
        
        Ejemplo:
        toolkit.copy_file("app.py", "app_backup.py")
        """
        pass
    
    # ═══════════════════════════════════════════════════════════
    # GRUPO 3: EJECUCIÓN DE COMANDOS
    # ═══════════════════════════════════════════════════════════
    
    def run_command(self, command: str, timeout: int = 60, 
                    working_dir: str = None) -> Dict:
        """
        Ejecuta un comando del sistema.
        
        Parámetros:
        - command: Comando a ejecutar
        - timeout: Segundos máximos de ejecución
        - working_dir: Directorio de trabajo (default: project_root)
        
        Retorna:
        {
            "success": True,
            "stdout": "output del comando...",
            "stderr": "",
            "exit_code": 0,
            "duration": 2.5
        }
        
        SEGURIDAD:
        - Solo comandos de la WHITELIST
        - Bloquear comandos peligrosos
        - Timeout obligatorio
        - Logging de todos los comandos
        
        Ejemplo:
        result = toolkit.run_command("pip install flask-login")
        result = toolkit.run_command("npm install express")
        result = toolkit.run_command("python -c 'print(1+1)'")
        result = toolkit.run_command("ls -la static/")
        """
        # Validar comando contra whitelist/blacklist
        if not self._is_command_allowed(command):
            return {
                "success": False,
                "error": "Comando no permitido por seguridad"
            }
        
        try:
            import subprocess
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir or self.project_root
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Comando excedió timeout de {timeout}s"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def install_package(self, name: str, manager: str = "auto") -> Dict:
        """
        Instala un paquete/dependencia.
        
        Parámetros:
        - name: Nombre del paquete
        - manager: "pip", "npm", "auto" (detecta según proyecto)
        
        Acciones:
        1. Detectar manager si es "auto"
        2. Ejecutar instalación
        3. Actualizar archivo de dependencias
        
        Ejemplo:
        toolkit.install_package("flask-login")  # auto-detecta pip
        toolkit.install_package("express", manager="npm")
        toolkit.install_package("requests==2.28.0")  # con versión
        """
        if manager == "auto":
            manager = self._detect_package_manager()
        
        if manager == "pip":
            cmd = f"pip install {name}"
        elif manager == "npm":
            cmd = f"npm install {name}"
        else:
            return {"success": False, "error": f"Manager no soportado: {manager}"}
        
        result = self.run_command(cmd, timeout=120)
        
        if result["success"]:
            # Actualizar archivo de dependencias
            self._update_dependencies_file(name, manager)
        
        return result
    
    def run_script(self, path: str, args: str = "") -> Dict:
        """
        Ejecuta un script Python o Node.
        
        Ejemplo:
        toolkit.run_script("test.py")
        toolkit.run_script("scripts/migrate.py", args="--force")
        toolkit.run_script("server.js")
        """
        language = self._detect_language(path)
        
        if language == "python":
            cmd = f"python {path} {args}"
        elif language == "javascript":
            cmd = f"node {path} {args}"
        else:
            return {"success": False, "error": f"Lenguaje no soportado: {language}"}
        
        return self.run_command(cmd)
    
    # ═══════════════════════════════════════════════════════════
    # GRUPO 4: LECTURA DE LOGS Y ERRORES
    # ═══════════════════════════════════════════════════════════
    
    def read_server_logs(self, lines: int = 100) -> Dict:
        """
        Lee los logs del servidor.
        
        Retorna:
        {
            "success": True,
            "logs": [
                {"time": "20:15:30", "level": "INFO", "message": "Server started"},
                {"time": "20:15:35", "level": "ERROR", "message": "..."}
            ],
            "has_errors": True,
            "error_count": 2
        }
        
        Uso típico:
        - Después de reiniciar servidor
        - Para debuggear problemas
        - Para verificar que algo funciona
        """
        pass
    
    def detect_errors(self, logs: List[str] = None) -> Dict:
        """
        Detecta errores en logs.
        
        Retorna:
        {
            "success": True,
            "errors": [
                {
                    "type": "ModuleNotFoundError",
                    "message": "No module named 'flask_login'",
                    "file": "app.py",
                    "line": 5,
                    "severity": "critical",
                    "suggestion": "pip install flask-login"
                }
            ]
        }
        
        Patrones que detecta:
        - Python: ModuleNotFoundError, ImportError, SyntaxError, etc.
        - Node: Cannot find module, SyntaxError, TypeError, etc.
        - General: Exception, Error, Failed, etc.
        """
        pass
    
    def analyze_error(self, error: str) -> Dict:
        """
        Analiza un error usando IA para entender causa y solución.
        
        Retorna:
        {
            "success": True,
            "error_type": "ModuleNotFoundError",
            "cause": "El módulo flask_login no está instalado",
            "solution": "Ejecutar: pip install flask-login",
            "auto_fix_available": True,
            "fix_steps": [
                {"action": "run_command", "command": "pip install flask-login"},
                {"action": "restart_server"}
            ],
            "related_files": ["app.py", "requirements.txt"],
            "documentation_url": "https://flask-login.readthedocs.io/"
        }
        """
        pass
    
    def auto_fix_error(self, error: Dict) -> Dict:
        """
        Intenta corregir un error automáticamente.
        
        Flujo:
        1. Analizar error
        2. Determinar si es auto-corregible
        3. Ejecutar pasos de corrección
        4. Verificar que se corrigió
        
        Errores auto-corregibles:
        - ModuleNotFoundError → pip/npm install
        - SyntaxError simple → editar archivo
        - ImportError → agregar import faltante
        
        Retorna:
        {
            "success": True,
            "fixed": True,
            "actions_taken": [
                "Instalado flask-login",
                "Reiniciado servidor"
            ],
            "verification": "Sin errores en logs"
        }
        """
        pass
    
    # ═══════════════════════════════════════════════════════════
    # GRUPO 5: ANÁLISIS DEL PROYECTO
    # ═══════════════════════════════════════════════════════════
    
    def analyze_project(self) -> Dict:
        """
        Analiza el proyecto completo para entender su contexto.
        
        DEBE ejecutarse al inicio de cada sesión.
        
        Retorna:
        {
            "success": True,
            "language": "python",
            "framework": "flask",
            "dependencies": {
                "installed": ["flask", "sqlalchemy", "requests"],
                "file": "requirements.txt"
            },
            "structure": {
                "app.py": {"type": "main", "lines": 500},
                "tracking/": {"type": "services", "files": 10},
                "templates/": {"type": "views", "files": 25},
                "static/": {"type": "assets", "files": 50}
            },
            "entry_point": "app.py",
            "port": 5000,
            "database": {
                "type": "postgresql",
                "configured": True
            },
            "has_tests": False,
            "git_initialized": True,
            "environment_variables": ["DATABASE_URL", "SECRET_KEY"]
        }
        
        Esto permite a la IA:
        - Saber qué lenguaje usar
        - Entender la estructura
        - Saber qué dependencias hay
        - Adaptar sus respuestas al proyecto
        """
        pass
    
    def detect_language(self, path: str = None) -> str:
        """
        Detecta el lenguaje principal del proyecto o de un archivo.
        
        Sin parámetro: detecta del proyecto entero
        Con path: detecta del archivo específico
        
        Retorna: "python", "javascript", "typescript", "html", "css", "sql", etc.
        """
        pass
    
    def read_dependencies(self) -> Dict:
        """
        Lee las dependencias del proyecto.
        
        Detecta automáticamente:
        - requirements.txt (Python)
        - package.json (Node.js)
        - Pipfile (Pipenv)
        - pyproject.toml (Poetry)
        
        Retorna:
        {
            "success": True,
            "manager": "pip",
            "file": "requirements.txt",
            "dependencies": {
                "flask": "2.0.0",
                "sqlalchemy": "1.4.0",
                "requests": "*"
            }
        }
        """
        pass
    
    # ═══════════════════════════════════════════════════════════
    # GRUPO 6: UTILIDADES INTERNAS
    # ═══════════════════════════════════════════════════════════
    
    def _validate_path(self, path: str) -> str:
        """
        Valida que un path sea seguro.
        - No permite ..
        - No permite rutas absolutas
        - Normaliza el path
        """
        import os
        
        # Normalizar
        normalized = os.path.normpath(path)
        
        # No permitir escape del proyecto
        if normalized.startswith('..') or normalized.startswith('/'):
            return None
        
        # No permitir archivos ocultos del sistema
        if any(part.startswith('.') and part not in ['.env', '.gitignore'] 
               for part in normalized.split(os.sep)):
            return None
        
        return normalized
    
    def _is_command_allowed(self, command: str) -> bool:
        """
        Verifica si un comando está permitido.
        """
        import re
        
        # Whitelist de comandos
        ALLOWED_PREFIXES = [
            'pip install', 'pip list', 'pip show', 'pip freeze',
            'npm install', 'npm run', 'npm init', 'npm list',
            'python ', 'python3 ',
            'node ',
            'npx ',
            'ls ', 'ls', 
            'cat ', 'head ', 'tail ',
            'mkdir ',
            'touch ',
            'git status', 'git log', 'git diff', 'git branch',
            'echo ',
            'pwd',
            'which ',
            'env',
        ]
        
        # Blacklist de patrones peligrosos
        BLOCKED_PATTERNS = [
            r'rm\s+-rf',
            r'rm\s+-r\s+/',
            r'rm\s+/',
            r'sudo',
            r'chmod\s+777',
            r'curl.*\|.*bash',
            r'wget.*\|.*sh',
            r'>\s*/etc/',
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__',
            r'subprocess\.Popen',
        ]
        
        # Verificar whitelist
        allowed = any(command.strip().startswith(prefix) for prefix in ALLOWED_PREFIXES)
        
        # Verificar blacklist
        blocked = any(re.search(pattern, command, re.IGNORECASE) for pattern in BLOCKED_PATTERNS)
        
        return allowed and not blocked
    
    def _detect_language(self, path: str) -> str:
        """Detecta lenguaje por extensión"""
        EXTENSIONS = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.json': 'json',
            '.sql': 'sql',
            '.md': 'markdown',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.sh': 'bash',
            '.env': 'env',
        }
        
        ext = os.path.splitext(path)[1].lower()
        return EXTENSIONS.get(ext, 'text')
    
    def _detect_package_manager(self) -> str:
        """Detecta el package manager del proyecto"""
        if os.path.exists(os.path.join(self.project_root, 'requirements.txt')):
            return 'pip'
        if os.path.exists(os.path.join(self.project_root, 'package.json')):
            return 'npm'
        if os.path.exists(os.path.join(self.project_root, 'Pipfile')):
            return 'pipenv'
        if os.path.exists(os.path.join(self.project_root, 'pyproject.toml')):
            return 'poetry'
        return 'pip'  # default
    
    def _generate_diff(self, old: str, new: str) -> str:
        """Genera diff visual entre dos strings"""
        import difflib
        
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        
        diff = difflib.unified_diff(old_lines, new_lines, lineterm='')
        return ''.join(diff)
    
    def _update_dependencies_file(self, package: str, manager: str):
        """Actualiza el archivo de dependencias"""
        if manager == 'pip':
            deps_file = 'requirements.txt'
            # Agregar al final
            self.append_to_file(deps_file, f"\n{package}")
        elif manager == 'npm':
            # npm ya actualiza package.json automáticamente
            pass
```

---

## ════════════════════════════════════════════════════════════════
## ESPECIFICACIÓN: IntentParser EXPANDIDO
## ════════════════════════════════════════════════════════════════

### TIPOS DE TAREAS EXPANDIDOS

```python
from enum import Enum

class TaskType(Enum):
    """
    TODOS los tipos de tareas que la IA debe entender.
    EXPANDIDO de 10 a 30+ tipos.
    
    ARCHIVO: tracking/ai_constructor.py (reemplazar el existente)
    """
    
    # ═══════════════════════════════════════════════════════════
    # CREACIÓN - Ya funcionan parcialmente
    # ═══════════════════════════════════════════════════════════
    CREAR_PROYECTO = "crear_proyecto"          # "Crea un proyecto de..."
    CREAR_WEB = "crear_web"                    # "Crea una página web"
    CREAR_LANDING = "crear_landing"            # "Crea un landing page"
    CREAR_DASHBOARD = "crear_dashboard"        # "Crea un dashboard"
    CREAR_FORMULARIO = "crear_formulario"      # "Crea un formulario"
    CREAR_COMPONENTE = "crear_componente"      # "Crea un componente de..."
    CREAR_ARCHIVO = "crear_archivo"            # "Crea un archivo llamado..."
    CREAR_API = "crear_api"                    # "Crea una API REST"
    CREAR_ENDPOINT = "crear_endpoint"          # "Crea un endpoint para..."
    CREAR_MODELO = "crear_modelo"              # "Crea un modelo de datos"
    CREAR_SERVICIO = "crear_servicio"          # "Crea un servicio para..."
    CREAR_TEST = "crear_test"                  # "Crea tests para..."
    
    # ═══════════════════════════════════════════════════════════
    # MODIFICACIÓN - NO FUNCIONAN - CRÍTICO
    # ═══════════════════════════════════════════════════════════
    MODIFICAR_ARCHIVO = "modificar_archivo"    # "Modifica app.py"
    AGREGAR_CODIGO = "agregar_codigo"          # "Agrega esta función a..."
    AGREGAR_IMPORT = "agregar_import"          # "Agrega import de..."
    AGREGAR_RUTA = "agregar_ruta"              # "Agrega ruta /profile"
    ELIMINAR_CODIGO = "eliminar_codigo"        # "Quita esta parte de..."
    REEMPLAZAR_CODIGO = "reemplazar_codigo"    # "Cambia X por Y en..."
    MOVER_ARCHIVO = "mover_archivo"            # "Mueve este archivo a..."
    RENOMBRAR = "renombrar"                    # "Renombra X a Y"
    ELIMINAR_ARCHIVO = "eliminar_archivo"      # "Elimina temp.py"
    
    # ═══════════════════════════════════════════════════════════
    # CORRECCIÓN Y DEBUGGING - NO FUNCIONAN - CRÍTICO
    # ═══════════════════════════════════════════════════════════
    CORREGIR_ERROR = "corregir_error"          # "Arregla este error"
    DEBUGGEAR = "debuggear"                    # "¿Por qué no funciona?"
    ANALIZAR_LOGS = "analizar_logs"            # "Revisa los logs"
    BUSCAR_BUG = "buscar_bug"                  # "Encuentra el problema"
    VERIFICAR = "verificar"                    # "¿Está bien esto?"
    DIAGNOSTICAR = "diagnosticar"              # "Diagnostica el problema"
    
    # ═══════════════════════════════════════════════════════════
    # EJECUCIÓN - NO FUNCIONAN - CRÍTICO
    # ═══════════════════════════════════════════════════════════
    EJECUTAR_COMANDO = "ejecutar_comando"      # "Ejecuta npm install"
    INSTALAR_DEPENDENCIA = "instalar_dep"      # "Instala flask-login"
    CORRER_SCRIPT = "correr_script"            # "Corre python test.py"
    REINICIAR_SERVIDOR = "reiniciar_servidor"  # "Reinicia el servidor"
    CORRER_TESTS = "correr_tests"              # "Corre los tests"
    BUILD = "build"                            # "Haz el build"
    
    # ═══════════════════════════════════════════════════════════
    # LECTURA Y BÚSQUEDA - NO FUNCIONAN - CRÍTICO
    # ═══════════════════════════════════════════════════════════
    LEER_ARCHIVO = "leer_archivo"              # "Muéstrame app.py"
    BUSCAR_CODIGO = "buscar_codigo"            # "Busca dónde usamos X"
    LISTAR_ARCHIVOS = "listar_archivos"        # "¿Qué archivos hay?"
    VER_ESTRUCTURA = "ver_estructura"          # "Muestra la estructura"
    VER_DEPENDENCIAS = "ver_dependencias"      # "¿Qué dependencias tenemos?"
    VER_LOGS = "ver_logs"                      # "Muéstrame los logs"
    
    # ═══════════════════════════════════════════════════════════
    # OPTIMIZACIÓN Y MEJORA
    # ═══════════════════════════════════════════════════════════
    OPTIMIZAR = "optimizar"                    # "Optimiza este código"
    REFACTORIZAR = "refactorizar"              # "Refactoriza esto"
    LIMPIAR_CODIGO = "limpiar_codigo"          # "Limpia el código"
    MEJORAR = "mejorar"                        # "Mejora esto"
    SIMPLIFICAR = "simplificar"                # "Simplifica esta función"
    
    # ═══════════════════════════════════════════════════════════
    # EXPLICACIÓN Y DOCUMENTACIÓN
    # ═══════════════════════════════════════════════════════════
    EXPLICAR = "explicar"                      # "Explica este código"
    DOCUMENTAR = "documentar"                  # "Documenta esta función"
    COMENTAR = "comentar"                      # "Agrega comentarios"
    GENERAR_README = "generar_readme"          # "Genera un README"
    
    # ═══════════════════════════════════════════════════════════
    # BASE DE DATOS
    # ═══════════════════════════════════════════════════════════
    CREAR_TABLA = "crear_tabla"                # "Crea tabla users"
    MODIFICAR_TABLA = "modificar_tabla"        # "Agrega columna a..."
    QUERY_SQL = "query_sql"                    # "Ejecuta este SQL"
    MIGRAR_BD = "migrar_bd"                    # "Migra la base de datos"
    
    # ═══════════════════════════════════════════════════════════
    # DESPLIEGUE
    # ═══════════════════════════════════════════════════════════
    DESPLEGAR = "desplegar"                    # "Despliega el proyecto"
    CONFIGURAR_DEPLOY = "configurar_deploy"    # "Configura el deploy"
    
    # ═══════════════════════════════════════════════════════════
    # GENERAL
    # ═══════════════════════════════════════════════════════════
    CONSULTA_GENERAL = "consulta_general"      # Preguntas generales
    CONVERSAR = "conversar"                    # Conversación casual
    DESCONOCIDO = "desconocido"                # No se entiende
```

---

### PATRONES DE DETECCIÓN DE INTENCIONES

```python
class IntentPatterns:
    """
    Patrones regex para detectar qué quiere el usuario.
    
    ARCHIVO: tracking/ai_constructor.py
    """
    
    PATTERNS = {
        # ═══════════════════════════════════════════════════════════
        # CREAR
        # ═══════════════════════════════════════════════════════════
        TaskType.CREAR_ARCHIVO: [
            r"crea(?:r?)?\s+(?:un\s+)?archivo\s+(?:llamado\s+)?(\w+\.?\w*)",
            r"genera(?:r?)?\s+(?:un\s+)?archivo\s+(?:llamado\s+)?(\w+\.?\w*)",
            r"hazme?\s+(?:un\s+)?archivo\s+(?:llamado\s+)?(\w+\.?\w*)",
            r"nuevo\s+archivo\s+(\w+\.?\w*)",
        ],
        
        TaskType.CREAR_API: [
            r"crea(?:r?)?\s+(?:una?\s+)?api",
            r"genera(?:r?)?\s+(?:una?\s+)?api",
            r"hazme?\s+(?:una?\s+)?api",
            r"implementa(?:r?)?\s+(?:una?\s+)?api",
            r"necesito\s+(?:una?\s+)?api",
        ],
        
        TaskType.CREAR_ENDPOINT: [
            r"crea(?:r?)?\s+(?:un\s+)?endpoint\s+(?:para\s+)?(.+)",
            r"agrega(?:r?)?\s+(?:una?\s+)?ruta\s+(?:para\s+)?(.+)",
            r"nuevo\s+endpoint\s+(.+)",
        ],
        
        # ═══════════════════════════════════════════════════════════
        # MODIFICAR
        # ═══════════════════════════════════════════════════════════
        TaskType.MODIFICAR_ARCHIVO: [
            r"modifica(?:r?)?\s+(?:el\s+)?archivo\s+(\S+)",
            r"cambia(?:r?)?\s+(?:en\s+)?(\S+\.?\w*)",
            r"actualiza(?:r?)?\s+(?:el\s+)?(\S+\.?\w*)",
            r"edita(?:r?)?\s+(?:el\s+)?(\S+\.?\w*)",
            r"abre\s+(?:el\s+)?(\S+\.?\w*)\s+y\s+(?:modifica|cambia|agrega)",
        ],
        
        TaskType.AGREGAR_CODIGO: [
            r"agrega(?:r?)?\s+(?:esto\s+)?(?:a|en|al\s+archivo)\s+(\S+)",
            r"añade(?:r?)?\s+(?:esto\s+)?(?:a|en|al\s+archivo)\s+(\S+)",
            r"pon(?:er?)?\s+(?:esto\s+)?(?:en|al\s+archivo)\s+(\S+)",
            r"inserta(?:r?)?\s+(?:esto\s+)?(?:en|al\s+archivo)\s+(\S+)",
        ],
        
        TaskType.ELIMINAR_ARCHIVO: [
            r"elimina(?:r?)?\s+(?:el\s+)?archivo\s+(\S+)",
            r"borra(?:r?)?\s+(?:el\s+)?archivo\s+(\S+)",
            r"quita(?:r?)?\s+(?:el\s+)?archivo\s+(\S+)",
            r"delete\s+(\S+)",
            r"rm\s+(\S+)",
        ],
        
        # ═══════════════════════════════════════════════════════════
        # CORREGIR
        # ═══════════════════════════════════════════════════════════
        TaskType.CORREGIR_ERROR: [
            r"arregla(?:r?)?\s+(?:el\s+)?error",
            r"corrige(?:r?)?\s+(?:el\s+)?error",
            r"fix(?:ear?)?\s+(?:el\s+)?(?:error|bug)",
            r"no\s+funciona",
            r"está\s+(?:roto|mal|fallando)",
            r"da\s+error",
            r"hay\s+(?:un\s+)?error",
            r"tengo\s+(?:un\s+)?(?:error|problema)",
            r"(?:el\s+)?server\s+(?:no\s+)?(?:arranca|inicia|funciona)",
        ],
        
        TaskType.DEBUGGEAR: [
            r"(?:por\s+)?(?:qué|que)\s+no\s+funciona",
            r"(?:por\s+)?(?:qué|que)\s+falla",
            r"(?:por\s+)?(?:qué|que)\s+da\s+error",
            r"debugg?(?:ea(?:r)?)?",
            r"investiga(?:r?)?\s+(?:el\s+)?(?:error|problema)",
        ],
        
        # ═══════════════════════════════════════════════════════════
        # EJECUTAR
        # ═══════════════════════════════════════════════════════════
        TaskType.EJECUTAR_COMANDO: [
            r"ejecuta(?:r?)?\s+(.+)",
            r"corre(?:r?)?\s+(.+)",
            r"run\s+(.+)",
            r"haz\s+(.+)",
        ],
        
        TaskType.INSTALAR_DEPENDENCIA: [
            r"instala(?:r?)?\s+(\S+)",
            r"(?:pip|npm)\s+install\s+(\S+)",
            r"agrega(?:r?)?\s+(?:la\s+)?dependencia\s+(\S+)",
            r"necesito\s+(?:el\s+)?(?:paquete|módulo|librería)\s+(\S+)",
        ],
        
        TaskType.REINICIAR_SERVIDOR: [
            r"reinicia(?:r?)?\s+(?:el\s+)?(?:servidor|server)",
            r"restart(?:ear?)?\s+(?:el\s+)?(?:servidor|server)",
            r"vuelve\s+a\s+(?:iniciar|arrancar)",
        ],
        
        # ═══════════════════════════════════════════════════════════
        # LEER
        # ═══════════════════════════════════════════════════════════
        TaskType.LEER_ARCHIVO: [
            r"muestra(?:me?)?\s+(?:el\s+)?(?:contenido\s+(?:de|del)\s+)?(\S+\.?\w*)",
            r"enséñame?\s+(?:el\s+)?(\S+\.?\w*)",
            r"(?:qué\s+hay|cómo\s+está)\s+(?:en\s+)?(\S+\.?\w*)",
            r"lee(?:r?)?\s+(?:el\s+)?(\S+\.?\w*)",
            r"ver\s+(?:el\s+)?(\S+\.?\w*)",
            r"abre\s+(?:el\s+)?(\S+\.?\w*)",
            r"cat\s+(\S+)",
        ],
        
        TaskType.BUSCAR_CODIGO: [
            r"busca(?:r?)?\s+(?:dónde\s+)?(.+)",
            r"encuentra(?:r?)?\s+(.+)",
            r"(?:dónde|donde)\s+(?:está|usamos|se\s+usa)\s+(.+)",
            r"grep\s+(.+)",
            r"en\s+(?:qué|que)\s+archivo\s+(?:está|hay)\s+(.+)",
        ],
        
        TaskType.LISTAR_ARCHIVOS: [
            r"(?:qué|que)\s+archivos\s+(?:hay|tenemos)",
            r"lista(?:r?)?\s+(?:los\s+)?archivos",
            r"muestra(?:me?)?\s+(?:la\s+)?estructura",
            r"muestra(?:me?)?\s+(?:el\s+)?árbol",
            r"ls\s*$",
            r"tree\s*$",
        ],
        
        TaskType.VER_LOGS: [
            r"muestra(?:me?)?\s+(?:los\s+)?logs?",
            r"ver\s+(?:los\s+)?logs?",
            r"(?:qué|que)\s+dicen?\s+(?:los\s+)?logs?",
            r"(?:hay\s+)?errores?\s+en\s+(?:los\s+)?logs?",
        ],
        
        # ═══════════════════════════════════════════════════════════
        # EXPLICAR
        # ═══════════════════════════════════════════════════════════
        TaskType.EXPLICAR: [
            r"explica(?:me?)?\s+(.+)",
            r"(?:qué|que)\s+(?:es|hace|significa)\s+(.+)",
            r"(?:cómo|como)\s+funciona\s+(.+)",
            r"(?:para\s+)?(?:qué|que)\s+sirve\s+(.+)",
            r"no\s+entiendo\s+(.+)",
        ],
        
        TaskType.DOCUMENTAR: [
            r"documenta(?:r?)?\s+(.+)",
            r"(?:agrega|pon)\s+(?:la\s+)?documentación\s+(?:a|de)\s+(.+)",
            r"escribe\s+(?:la\s+)?documentación",
        ],
        
        # ═══════════════════════════════════════════════════════════
        # OPTIMIZAR
        # ═══════════════════════════════════════════════════════════
        TaskType.OPTIMIZAR: [
            r"optimiza(?:r?)?\s+(.+)",
            r"mejora(?:r?)?\s+(.+)",
            r"haz(?:lo)?\s+más\s+(?:rápido|eficiente)",
        ],
        
        TaskType.REFACTORIZAR: [
            r"refactoriza(?:r?)?\s+(.+)",
            r"reorganiza(?:r?)?\s+(.+)",
            r"limpia(?:r?)?\s+(?:el\s+)?código",
            r"reestructura(?:r?)?\s+(.+)",
        ],
        
        # ═══════════════════════════════════════════════════════════
        # BASE DE DATOS
        # ═══════════════════════════════════════════════════════════
        TaskType.CREAR_TABLA: [
            r"crea(?:r?)?\s+(?:una?\s+)?tabla\s+(\w+)",
            r"(?:agrega|añade)\s+(?:una?\s+)?tabla\s+(\w+)",
        ],
        
        TaskType.QUERY_SQL: [
            r"ejecuta(?:r?)?\s+(?:este\s+)?sql",
            r"(?:haz|corre)\s+(?:esta\s+)?(?:consulta|query)",
            r"SELECT\s+.+\s+FROM",
            r"INSERT\s+INTO",
            r"UPDATE\s+.+\s+SET",
            r"DELETE\s+FROM",
        ],
    }
    
    @classmethod
    def detect_intent(cls, message: str) -> Tuple[TaskType, Dict]:
        """
        Detecta la intención del usuario.
        
        Retorna: (TaskType, extracted_data)
        
        extracted_data puede contener:
        - file_path: ruta del archivo mencionado
        - search_query: término de búsqueda
        - command: comando a ejecutar
        - package_name: paquete a instalar
        """
        import re
        
        message_lower = message.lower().strip()
        
        for task_type, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, message_lower, re.IGNORECASE)
                if match:
                    # Extraer datos del match
                    extracted = {}
                    if match.groups():
                        extracted["captured"] = match.group(1)
                    
                    return task_type, extracted
        
        # Si no se detecta nada específico
        return TaskType.CONSULTA_GENERAL, {}
```

---

## ════════════════════════════════════════════════════════════════
## ESPECIFICACIÓN: AIExecutionFlow (Flujos de Ejecución)
## ════════════════════════════════════════════════════════════════

```python
class AIExecutionFlow:
    """
    Define cómo se ejecuta cada tipo de tarea paso a paso.
    
    ARCHIVO: tracking/ai_constructor.py o tracking/ai_execution_flow.py
    """
    
    FLOWS = {
        # ═══════════════════════════════════════════════════════════
        # FLUJO: MODIFICAR ARCHIVO
        # ═══════════════════════════════════════════════════════════
        TaskType.MODIFICAR_ARCHIVO: {
            "description": "Modificar un archivo existente",
            "steps": [
                {
                    "id": "read",
                    "action": "read_file",
                    "description": "Leer archivo actual",
                    "required": True
                },
                {
                    "id": "analyze",
                    "action": "ai_analyze",
                    "description": "Entender qué cambiar",
                    "required": True
                },
                {
                    "id": "plan",
                    "action": "create_plan",
                    "description": "Crear plan de cambios",
                    "required": True
                },
                {
                    "id": "confirm",
                    "action": "ask_confirmation",
                    "description": "Pedir confirmación al usuario",
                    "required": True
                },
                {
                    "id": "edit",
                    "action": "edit_file",
                    "description": "Aplicar cambios",
                    "required": True
                },
                {
                    "id": "verify",
                    "action": "verify_syntax",
                    "description": "Verificar sintaxis",
                    "required": False
                },
                {
                    "id": "report",
                    "action": "report_result",
                    "description": "Reportar resultado",
                    "required": True
                }
            ]
        },
        
        # ═══════════════════════════════════════════════════════════
        # FLUJO: CORREGIR ERROR
        # ═══════════════════════════════════════════════════════════
        TaskType.CORREGIR_ERROR: {
            "description": "Detectar y corregir un error",
            "steps": [
                {
                    "id": "read_logs",
                    "action": "read_server_logs",
                    "description": "Leer logs del servidor"
                },
                {
                    "id": "detect",
                    "action": "detect_errors",
                    "description": "Identificar el error"
                },
                {
                    "id": "analyze",
                    "action": "analyze_error",
                    "description": "Analizar causa del error"
                },
                {
                    "id": "find_code",
                    "action": "search_code",
                    "description": "Encontrar código problemático"
                },
                {
                    "id": "plan_fix",
                    "action": "plan_fix",
                    "description": "Planear corrección"
                },
                {
                    "id": "confirm",
                    "action": "ask_confirmation",
                    "description": "Confirmar con usuario"
                },
                {
                    "id": "apply_fix",
                    "action": "edit_file",
                    "description": "Aplicar corrección"
                },
                {
                    "id": "install_if_needed",
                    "action": "install_package",
                    "description": "Instalar dependencias si es necesario",
                    "conditional": True
                },
                {
                    "id": "restart",
                    "action": "restart_server",
                    "description": "Reiniciar servidor"
                },
                {
                    "id": "verify",
                    "action": "verify_no_errors",
                    "description": "Verificar que se corrigió"
                },
                {
                    "id": "report",
                    "action": "report_result",
                    "description": "Reportar resultado"
                }
            ]
        },
        
        # ═══════════════════════════════════════════════════════════
        # FLUJO: INSTALAR DEPENDENCIA
        # ═══════════════════════════════════════════════════════════
        TaskType.INSTALAR_DEPENDENCIA: {
            "description": "Instalar un paquete/dependencia",
            "steps": [
                {
                    "id": "detect_manager",
                    "action": "detect_package_manager",
                    "description": "Detectar pip o npm"
                },
                {
                    "id": "confirm",
                    "action": "ask_confirmation",
                    "description": "Confirmar instalación"
                },
                {
                    "id": "install",
                    "action": "install_package",
                    "description": "Ejecutar instalación"
                },
                {
                    "id": "verify",
                    "action": "verify_install",
                    "description": "Verificar instalación"
                },
                {
                    "id": "update_deps",
                    "action": "update_dependencies_file",
                    "description": "Actualizar requirements.txt/package.json"
                },
                {
                    "id": "report",
                    "action": "report_result",
                    "description": "Reportar resultado"
                }
            ]
        },
        
        # ═══════════════════════════════════════════════════════════
        # FLUJO: CREAR API
        # ═══════════════════════════════════════════════════════════
        TaskType.CREAR_API: {
            "description": "Crear una API REST completa",
            "steps": [
                {
                    "id": "analyze_project",
                    "action": "analyze_project",
                    "description": "Ver estructura actual"
                },
                {
                    "id": "detect_lang",
                    "action": "detect_language",
                    "description": "Python o Node?"
                },
                {
                    "id": "clarify",
                    "action": "ask_clarification",
                    "description": "Preguntar detalles de la API"
                },
                {
                    "id": "plan",
                    "action": "plan_api",
                    "description": "Diseñar endpoints y estructura"
                },
                {
                    "id": "confirm",
                    "action": "ask_confirmation",
                    "description": "Confirmar plan"
                },
                {
                    "id": "create_files",
                    "action": "create_api_files",
                    "description": "Crear archivos necesarios"
                },
                {
                    "id": "integrate",
                    "action": "integrate_with_main",
                    "description": "Integrar con archivo principal"
                },
                {
                    "id": "install_deps",
                    "action": "install_dependencies",
                    "description": "Instalar dependencias necesarias"
                },
                {
                    "id": "restart",
                    "action": "restart_server",
                    "description": "Reiniciar servidor"
                },
                {
                    "id": "verify",
                    "action": "verify_endpoints",
                    "description": "Verificar que endpoints funcionan"
                },
                {
                    "id": "report",
                    "action": "report_result",
                    "description": "Reportar resultado con documentación"
                }
            ]
        },
        
        # ═══════════════════════════════════════════════════════════
        # FLUJO: LEER ARCHIVO
        # ═══════════════════════════════════════════════════════════
        TaskType.LEER_ARCHIVO: {
            "description": "Mostrar contenido de un archivo",
            "steps": [
                {
                    "id": "validate",
                    "action": "validate_file_exists",
                    "description": "Verificar que archivo existe"
                },
                {
                    "id": "read",
                    "action": "read_file",
                    "description": "Leer contenido"
                },
                {
                    "id": "format",
                    "action": "format_for_display",
                    "description": "Formatear con syntax highlighting"
                },
                {
                    "id": "report",
                    "action": "show_content",
                    "description": "Mostrar al usuario"
                }
            ]
        },
        
        # ═══════════════════════════════════════════════════════════
        # FLUJO: BUSCAR EN CÓDIGO
        # ═══════════════════════════════════════════════════════════
        TaskType.BUSCAR_CODIGO: {
            "description": "Buscar texto/patrón en el código",
            "steps": [
                {
                    "id": "parse_query",
                    "action": "parse_search_query",
                    "description": "Entender qué buscar"
                },
                {
                    "id": "search",
                    "action": "search_code",
                    "description": "Ejecutar búsqueda"
                },
                {
                    "id": "format",
                    "action": "format_search_results",
                    "description": "Formatear resultados"
                },
                {
                    "id": "report",
                    "action": "show_results",
                    "description": "Mostrar resultados al usuario"
                }
            ]
        },
    }
    
    @classmethod
    def get_flow(cls, task_type: TaskType) -> Dict:
        """Obtiene el flujo de ejecución para un tipo de tarea"""
        return cls.FLOWS.get(task_type, cls.FLOWS[TaskType.CONSULTA_GENERAL])
    
    @classmethod
    def execute_flow(cls, task_type: TaskType, context: Dict, toolkit: AIToolkit) -> Dict:
        """
        Ejecuta un flujo completo paso a paso.
        
        Retorna progreso y resultado de cada paso.
        """
        flow = cls.get_flow(task_type)
        results = []
        
        for step in flow["steps"]:
            # Ejecutar paso
            step_result = cls._execute_step(step, context, toolkit)
            results.append(step_result)
            
            # Si falló y era requerido, parar
            if not step_result["success"] and step.get("required", True):
                return {
                    "success": False,
                    "failed_at": step["id"],
                    "results": results
                }
            
            # Actualizar contexto con resultado
            context[step["id"]] = step_result
        
        return {
            "success": True,
            "results": results
        }
```

---

## ════════════════════════════════════════════════════════════════
## ESPECIFICACIÓN: AIProjectContext (Memoria del Proyecto)
## ════════════════════════════════════════════════════════════════

```python
class AIProjectContext:
    """
    Mantiene contexto del proyecto entre peticiones.
    
    ARCHIVO: tracking/ai_project_context.py
    
    Esto permite a la IA recordar:
    - Qué archivos ha creado/modificado
    - Qué comandos ha ejecutado
    - Qué errores ha corregido
    - La estructura del proyecto
    """
    
    def __init__(self, user_id: str, project_id: str):
        self.user_id = user_id
        self.project_id = project_id
        self.session_start = datetime.now()
        
        # Estado del proyecto
        self.project_info = None
        self.file_tree = []
        
        # Historial de la sesión
        self.files_created = []
        self.files_modified = []
        self.files_deleted = []
        self.commands_executed = []
        self.errors_found = []
        self.errors_fixed = []
        self.packages_installed = []
        
        # Conversación
        self.conversation_history = []
        self.current_task = None
        self.pending_confirmations = []
    
    def initialize(self, toolkit: AIToolkit):
        """
        Inicializa el contexto analizando el proyecto.
        DEBE llamarse al inicio de cada sesión.
        """
        self.project_info = toolkit.analyze_project()
        self.file_tree = toolkit.list_directory(".")["files"]
    
    def remember_file_created(self, path: str, content: str, description: str = ""):
        """Registra que se creó un archivo"""
        self.files_created.append({
            "path": path,
            "size": len(content),
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
    
    def remember_file_modified(self, path: str, change_description: str, diff: str = ""):
        """Registra que se modificó un archivo"""
        self.files_modified.append({
            "path": path,
            "change": change_description,
            "diff": diff,
            "timestamp": datetime.now().isoformat()
        })
    
    def remember_command_executed(self, command: str, result: Dict):
        """Registra un comando ejecutado"""
        self.commands_executed.append({
            "command": command,
            "success": result.get("success", False),
            "output": result.get("stdout", "")[:500],  # Limitar tamaño
            "timestamp": datetime.now().isoformat()
        })
    
    def remember_error_found(self, error: Dict):
        """Registra un error encontrado"""
        self.errors_found.append({
            **error,
            "timestamp": datetime.now().isoformat()
        })
    
    def remember_error_fixed(self, error: Dict, fix: Dict):
        """Registra un error corregido"""
        self.errors_fixed.append({
            "error": error,
            "fix": fix,
            "timestamp": datetime.now().isoformat()
        })
    
    def remember_package_installed(self, package: str, manager: str):
        """Registra un paquete instalado"""
        self.packages_installed.append({
            "package": package,
            "manager": manager,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_conversation(self, role: str, message: str):
        """Agrega mensaje al historial de conversación"""
        self.conversation_history.append({
            "role": role,  # "user" o "assistant"
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_context_summary(self) -> str:
        """
        Genera resumen del contexto para incluir en prompts.
        Esto se pasa a la IA para que entienda el contexto.
        """
        summary = f"""
════════════════════════════════════════════════════════════════
CONTEXTO DEL PROYECTO
════════════════════════════════════════════════════════════════

INFORMACIÓN DEL PROYECTO:
- Lenguaje principal: {self.project_info.get('language', 'desconocido')}
- Framework: {self.project_info.get('framework', 'ninguno')}
- Punto de entrada: {self.project_info.get('entry_point', 'desconocido')}
- Base de datos: {self.project_info.get('database', {}).get('type', 'ninguna')}

ACTIVIDAD EN ESTA SESIÓN:
- Archivos creados: {len(self.files_created)}
- Archivos modificados: {len(self.files_modified)}
- Comandos ejecutados: {len(self.commands_executed)}
- Errores corregidos: {len(self.errors_fixed)}
- Paquetes instalados: {len(self.packages_installed)}
"""
        
        # Añadir archivos recientes
        if self.files_created:
            summary += "\nARCHIVOS CREADOS:\n"
            for f in self.files_created[-5:]:  # últimos 5
                summary += f"  - {f['path']}: {f.get('description', '')}\n"
        
        if self.files_modified:
            summary += "\nARCHIVOS MODIFICADOS:\n"
            for f in self.files_modified[-5:]:
                summary += f"  - {f['path']}: {f['change']}\n"
        
        if self.packages_installed:
            summary += "\nPAQUETES INSTALADOS:\n"
            for p in self.packages_installed:
                summary += f"  - {p['package']} ({p['manager']})\n"
        
        if self.errors_fixed:
            summary += "\nERRORES CORREGIDOS:\n"
            for e in self.errors_fixed[-3:]:
                summary += f"  - {e['error'].get('type', 'Error')}: {e['error'].get('message', '')[:50]}\n"
        
        return summary
    
    def get_recent_conversation(self, limit: int = 10) -> List[Dict]:
        """Obtiene los últimos mensajes de la conversación"""
        return self.conversation_history[-limit:]
    
    def save_to_db(self, db_session):
        """Guarda el contexto en la base de datos para persistencia"""
        # Implementar según el ORM usado
        pass
    
    @classmethod
    def load_from_db(cls, user_id: str, project_id: str, db_session) -> 'AIProjectContext':
        """Carga contexto guardado de la base de datos"""
        # Implementar según el ORM usado
        pass
```

---

## ════════════════════════════════════════════════════════════════
## ESPECIFICACIÓN: AIVerificationSystem
## ════════════════════════════════════════════════════════════════

```python
class AIVerificationSystem:
    """
    Verifica que las acciones de la IA se completaron correctamente.
    
    ARCHIVO: tracking/ai_verification.py
    """
    
    def __init__(self, toolkit: AIToolkit):
        self.toolkit = toolkit
    
    def verify_file_created(self, path: str) -> Dict:
        """Verificar que el archivo se creó correctamente"""
        info = self.toolkit.get_file_info(path)
        
        if not info.get("exists"):
            return {
                "success": False,
                "error": f"Archivo no fue creado: {path}"
            }
        
        return {
            "success": True,
            "file_info": info
        }
    
    def verify_file_syntax(self, path: str) -> Dict:
        """Verificar sintaxis del archivo creado/editado"""
        language = self.toolkit._detect_language(path)
        content = self.toolkit.read_file(path)
        
        if not content["success"]:
            return content
        
        if language == "python":
            return self._verify_python_syntax(content["content"])
        elif language == "javascript":
            return self._verify_js_syntax(content["content"])
        elif language == "json":
            return self._verify_json_syntax(content["content"])
        
        return {"success": True, "message": "Sintaxis no verificada para este tipo"}
    
    def _verify_python_syntax(self, code: str) -> Dict:
        """Verificar sintaxis Python"""
        try:
            import ast
            ast.parse(code)
            return {"success": True}
        except SyntaxError as e:
            return {
                "success": False,
                "error": "SyntaxError",
                "line": e.lineno,
                "message": str(e)
            }
    
    def _verify_js_syntax(self, code: str) -> Dict:
        """Verificar sintaxis JavaScript básica"""
        # Verificación básica de balance de llaves/paréntesis
        stack = []
        pairs = {')': '(', '}': '{', ']': '['}
        
        for i, char in enumerate(code):
            if char in '({[':
                stack.append((char, i))
            elif char in ')}]':
                if not stack or stack[-1][0] != pairs[char]:
                    return {
                        "success": False,
                        "error": f"Desbalance de {char} en posición {i}"
                    }
                stack.pop()
        
        if stack:
            return {
                "success": False,
                "error": f"Falta cerrar {stack[-1][0]} abierto en posición {stack[-1][1]}"
            }
        
        return {"success": True}
    
    def _verify_json_syntax(self, code: str) -> Dict:
        """Verificar sintaxis JSON"""
        try:
            import json
            json.loads(code)
            return {"success": True}
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": "JSONDecodeError",
                "line": e.lineno,
                "message": str(e)
            }
    
    def verify_server_running(self) -> Dict:
        """Verificar que el servidor está corriendo sin errores"""
        logs = self.toolkit.read_server_logs(20)
        
        if not logs["success"]:
            return logs
        
        errors = self.toolkit.detect_errors(logs["logs"])
        
        return {
            "success": len(errors.get("errors", [])) == 0,
            "errors": errors.get("errors", []),
            "server_status": "running" if len(errors.get("errors", [])) == 0 else "error"
        }
    
    def verify_endpoint_works(self, endpoint: str, method: str = "GET") -> Dict:
        """Verificar que un endpoint responde correctamente"""
        import requests
        
        try:
            url = f"http://localhost:5000{endpoint}"
            response = requests.request(method, url, timeout=5)
            
            return {
                "success": response.status_code < 500,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "No se pudo conectar al servidor"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_package_installed(self, package: str, manager: str = "pip") -> Dict:
        """Verificar que un paquete está instalado"""
        if manager == "pip":
            result = self.toolkit.run_command(f"pip show {package}")
        elif manager == "npm":
            result = self.toolkit.run_command(f"npm list {package}")
        else:
            return {"success": False, "error": f"Manager no soportado: {manager}"}
        
        return {
            "success": result["exit_code"] == 0,
            "installed": result["exit_code"] == 0
        }
    
    def full_verification(self, task_type: str, actions_taken: List[Dict]) -> Dict:
        """
        Verificación completa después de ejecutar una tarea.
        """
        results = {
            "success": True,
            "verifications": []
        }
        
        for action in actions_taken:
            verification = None
            
            if action["type"] == "create_file":
                verification = self.verify_file_created(action["path"])
                if verification["success"]:
                    syntax = self.verify_file_syntax(action["path"])
                    verification["syntax_valid"] = syntax["success"]
            
            elif action["type"] == "edit_file":
                verification = self.verify_file_syntax(action["path"])
            
            elif action["type"] == "install_package":
                verification = self.verify_package_installed(
                    action["package"], 
                    action.get("manager", "pip")
                )
            
            elif action["type"] == "restart_server":
                verification = self.verify_server_running()
            
            if verification:
                results["verifications"].append({
                    "action": action,
                    "result": verification
                })
                
                if not verification.get("success"):
                    results["success"] = False
        
        return results
```

---

## ════════════════════════════════════════════════════════════════
## LISTA DE PRIORIDADES DE IMPLEMENTACIÓN
## ════════════════════════════════════════════════════════════════

### PRIORIDAD CRÍTICA (Sin esto no funciona nada):

| # | Componente | Descripción | Archivo | Tiempo |
|---|------------|-------------|---------|--------|
| 1 | `AIToolkit.read_file()` | Leer cualquier archivo del proyecto | tracking/ai_toolkit.py | 2h |
| 2 | `AIToolkit.edit_file()` | Editar archivos existentes (no reemplazar) | tracking/ai_toolkit.py | 3h |
| 3 | `AIToolkit.write_file()` | Crear archivos (cualquier tipo, no solo HTML) | tracking/ai_toolkit.py | 2h |
| 4 | `AIToolkit.run_command()` | Ejecutar comandos (npm, pip, python) | tracking/ai_toolkit.py | 3h |
| 5 | `AIToolkit.read_logs()` | Leer logs del servidor | tracking/ai_toolkit.py | 2h |
| 6 | `IntentParser` expandido | Detectar 30+ tipos de peticiones | tracking/ai_constructor.py | 4h |

**Subtotal: 16 horas**

---

### PRIORIDAD ALTA (Para ser realmente útil):

| # | Componente | Descripción | Archivo | Tiempo |
|---|------------|-------------|---------|--------|
| 7 | `AIToolkit.search_code()` | Buscar texto en código (grep) | tracking/ai_toolkit.py | 2h |
| 8 | `AIToolkit.list_directory()` | Ver estructura de carpetas | tracking/ai_toolkit.py | 1h |
| 9 | `AIToolkit.analyze_project()` | Entender el proyecto completo | tracking/ai_toolkit.py | 3h |
| 10 | `AIVerificationSystem` | Verificar que todo funciona | tracking/ai_verification.py | 3h |
| 11 | `AIProjectContext` | Recordar lo que se hizo en la sesión | tracking/ai_project_context.py | 4h |

**Subtotal: 13 horas**

---

### PRIORIDAD MEDIA (Para ser excelente):

| # | Componente | Descripción | Archivo | Tiempo |
|---|------------|-------------|---------|--------|
| 12 | Auto-corrección de errores | Detectar y corregir errores automáticamente | tracking/ai_toolkit.py | 4h |
| 13 | Multi-lenguaje | Generar Python, Node, SQL (no solo HTML) | tracking/ai_constructor.py | 5h |
| 14 | Sistema de diff visual | Mostrar cambios antes de aplicar | Frontend + Backend | 3h |
| 15 | Memoria persistente | Recordar entre sesiones | Base de datos | 4h |

**Subtotal: 16 horas**

---

### RESUMEN TOTAL

| Prioridad | Tareas | Tiempo |
|-----------|--------|--------|
| 🔴 CRÍTICA | 6 componentes | 16 horas |
| 🟡 ALTA | 5 componentes | 13 horas |
| 🟠 MEDIA | 4 componentes | 16 horas |
| **TOTAL** | **15 componentes** | **45 horas** |

---

### ORDEN DE IMPLEMENTACIÓN

```
SEMANA 1 (CRÍTICO):
├── Día 1-2: AIToolkit básico (read_file, write_file, list_directory)
├── Día 3:   AIToolkit.edit_file() (la más importante)
├── Día 4:   AIToolkit.run_command() + seguridad
└── Día 5:   IntentParser expandido

SEMANA 2 (ALTO):
├── Día 1:   AIToolkit.search_code() + read_logs()
├── Día 2:   AIToolkit.analyze_project()
├── Día 3:   AIProjectContext
└── Día 4-5: AIVerificationSystem + testing

SEMANA 3 (MEDIO):
├── Día 1-2: Auto-corrección de errores
├── Día 3-4: Multi-lenguaje (Python, Node, SQL)
└── Día 5:   Sistema de diff + memoria persistente
```

---

## ═══════════════════════════════════════
## FASE 34.1: CONECTAR FRONTEND CON CONSTRUCTOR 8 FASES ⏳
## ═══════════════════════════════════════

**Prioridad:** 🔴 CRÍTICA  
**Tiempo:** 4 horas  
**Agente:** 🔵 FRONTEND

### Objetivo:
Cambiar el frontend para que use el sistema de 8 fases en vez de generación directa.

### Tareas:
- [ ] Modificar `ai-chat.js` para usar `/api/ai-constructor/process` en vez de `/api/ai/code-builder`
- [ ] Manejar respuestas de cada fase (clarificación, confirmación, etc.)
- [ ] Mostrar el proceso de fases visualmente al usuario
- [ ] Implementar botones de confirmación/cancelación del plan
- [ ] Conectar archivos generados con el panel de preview
- [ ] Actualizar panel de archivos cuando la IA genera archivos

### Criterios de éxito:
- [ ] Usuario ve las fases ejecutándose
- [ ] IA pregunta clarificaciones cuando necesita
- [ ] IA muestra plan antes de ejecutar
- [ ] Preview se actualiza en tiempo real

---

## ═══════════════════════════════════════
## FASE 34.2: EXPANDIR CAPACIDADES DE LA IA ⏳
## ═══════════════════════════════════════

**Prioridad:** 🔴 CRÍTICA  
**Tiempo:** 6 horas  
**Agente:** 🟡 BACKEND + 🟣 IA

### Objetivo:
La IA debe poder hacer MÁS que solo crear páginas web.

### Capacidades a implementar:

#### 34.2.1 - Crear archivos nuevos
- [ ] Detectar cuando usuario pide crear archivo
- [ ] Generar contenido del archivo
- [ ] Guardarlo en sistema de archivos virtual o real
- [ ] Notificar al frontend del nuevo archivo

#### 34.2.2 - Editar archivos existentes
- [ ] Leer contenido actual del archivo
- [ ] Entender qué cambios pide el usuario
- [ ] Aplicar cambios de forma inteligente
- [ ] Mostrar diff de cambios

#### 34.2.3 - Eliminar archivos
- [ ] Confirmar antes de eliminar
- [ ] Eliminar archivo del sistema
- [ ] Actualizar árbol de archivos

#### 34.2.4 - Ejecutar comandos
- [ ] Detectar cuando usuario pide ejecutar comando
- [ ] Ejecutar comandos permitidos (npm, pip, python, node, etc.)
- [ ] Mostrar output del comando en consola
- [ ] Manejar errores de comandos

#### 34.2.5 - Leer/Entender archivos del proyecto
- [ ] IA puede leer archivos existentes
- [ ] Entender contexto del proyecto
- [ ] Sugerir mejoras basadas en código existente

#### 34.2.6 - Descargar proyecto como ZIP
- [ ] Generar ZIP con todos los archivos
- [ ] Incluir estructura de carpetas
- [ ] Permitir descarga desde frontend

---

## ═══════════════════════════════════════
## FASE 34.3: SISTEMA DE ARCHIVOS VIRTUAL ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟡 ALTA  
**Tiempo:** 4 horas  
**Agente:** 🟡 BACKEND

### Objetivo:
Sistema de archivos en memoria para proyectos de la IA.

### Tareas:
- [ ] Crear clase `VirtualFileSystem` 
- [ ] Almacenar archivos en base de datos por usuario/proyecto
- [ ] Métodos: create, read, update, delete, list, search
- [ ] Persistir entre sesiones
- [ ] Límite de tamaño por usuario
- [ ] Endpoint para descargar como ZIP

### Estructura de BD:
```sql
CREATE TABLE ai_project_files (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    project_id VARCHAR(100),
    file_path VARCHAR(500),
    content TEXT,
    file_type VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## ═══════════════════════════════════════
## FASE 34.4: PREVIEW EN TIEMPO REAL ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟡 ALTA  
**Tiempo:** 3 horas  
**Agente:** 🔵 FRONTEND

### Objetivo:
El preview se actualiza mientras la IA trabaja, no solo al final.

### Tareas:
- [ ] Implementar WebSocket o polling para actualizaciones
- [ ] Actualizar iframe cuando cambia HTML/CSS/JS
- [ ] Mostrar indicador de "IA trabajando" en preview
- [ ] Manejar errores de preview gracefully
- [ ] Botón de refresh manual

---

## ═══════════════════════════════════════
## FASE 34.5: PANEL DE ARCHIVOS DINÁMICO ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟡 ALTA  
**Tiempo:** 3 horas  
**Agente:** 🔵 FRONTEND

### Objetivo:
Panel derecho muestra archivos del proyecto IA.

### Tareas:
- [ ] Cargar archivos del proyecto actual
- [ ] Árbol expandible de carpetas
- [ ] Click en archivo para ver/editar contenido
- [ ] Indicador de archivo nuevo/modificado
- [ ] Bloquear edición mientras IA trabaja
- [ ] Sincronizar con sistema de archivos virtual

---

## ═══════════════════════════════════════
## FASE 34.6: ENTENDIMIENTO DE INTENCIONES ⏳
## ═══════════════════════════════════════

**Prioridad:** 🔴 CRÍTICA  
**Tiempo:** 5 horas  
**Agente:** 🟣 IA

### Objetivo:
La IA entiende qué quiere el usuario, no solo "crear página".

### Tipos de intenciones a detectar:
- [ ] "Crea..." → Crear nuevos archivos/proyectos
- [ ] "Modifica..." → Editar archivos existentes
- [ ] "Arregla..." → Corregir errores
- [ ] "Explica..." → Explicar código/concepto
- [ ] "Optimiza..." → Mejorar rendimiento
- [ ] "Ejecuta..." → Correr comandos
- [ ] "Instala..." → Agregar dependencias
- [ ] "Elimina..." → Borrar archivos
- [ ] "Muéstrame..." → Ver archivos/código
- [ ] "¿Cómo...?" → Preguntas/consultas
- [ ] "Refactoriza..." → Reorganizar código
- [ ] "Testea..." → Crear/ejecutar tests
- [ ] "Documenta..." → Agregar documentación
- [ ] "Despliega..." → Deploy del proyecto

### Expandir `IntentParser` en `ai_constructor.py`:
```python
class TaskType(Enum):
    CREAR_PROYECTO = "crear_proyecto"
    CREAR_ARCHIVO = "crear_archivo"
    EDITAR_ARCHIVO = "editar_archivo"
    ELIMINAR_ARCHIVO = "eliminar_archivo"
    EJECUTAR_COMANDO = "ejecutar_comando"
    INSTALAR_DEPENDENCIA = "instalar_dependencia"
    CORREGIR_ERROR = "corregir_error"
    OPTIMIZAR = "optimizar"
    EXPLICAR = "explicar"
    DOCUMENTAR = "documentar"
    REFACTORIZAR = "refactorizar"
    TESTEAR = "testear"
    CONSULTA_GENERAL = "consulta_general"
```

---

## ═══════════════════════════════════════
## FASE 34.7: CONSOLA DE COMANDOS ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟠 MEDIA  
**Tiempo:** 4 horas  
**Agente:** 🔵 FRONTEND + 🟡 BACKEND

### Objetivo:
Consola tipo terminal donde la IA puede ejecutar comandos.

### Tareas:
- [ ] Agregar pestaña "Consola" junto a Preview
- [ ] Backend endpoint para ejecutar comandos seguros
- [ ] Lista blanca de comandos permitidos
- [ ] Mostrar output en tiempo real
- [ ] Historial de comandos
- [ ] Manejar errores y timeouts

### Comandos permitidos:
```python
ALLOWED_COMMANDS = [
    'npm install', 'npm run', 'npm init',
    'pip install', 'pip list',
    'python', 'python3',
    'node', 'npx',
    'ls', 'cat', 'head', 'tail',
    'mkdir', 'touch',
    'git status', 'git log', 'git diff'
]
```

---

## ═══════════════════════════════════════
## FASE 34.8: IA LOCAL (DeepSeek + HuggingFace) ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟠 MEDIA  
**Tiempo:** 4 horas  
**Agente:** 🟣 IA

### Objetivo:
DeepSeek + HuggingFace como "cerebro principal" que consulta a otras IAs.

### Arquitectura:
```
Usuario ──> BUNK3R AI (DeepSeek V3.2 local)
                │
                ├──> Para código: Groq/Cerebras
                ├──> Para diseño: Gemini
                ├──> Para análisis: DeepSeek API
                └──> Fallback: HuggingFace Llama
```

### Tareas:
- [ ] Configurar DeepSeek V3.2 como proveedor principal
- [ ] Implementar orquestador que decide qué IA usar
- [ ] Routing inteligente según tipo de tarea
- [ ] Caché de respuestas para eficiencia

---

## ═══════════════════════════════════════
## FASE 34.9: BLOQUEAR IA PARA USUARIOS NORMALES ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟡 ALTA  
**Tiempo:** 2 horas  
**Agente:** 🟡 BACKEND

### Objetivo:
Solo el OWNER ve la IA Constructor completa por ahora.

### Tareas:
- [ ] Verificar `is_owner` en endpoints de IA
- [ ] Ocultar botón IA para usuarios normales
- [ ] Mostrar IA básica (solo chat) para usuarios normales
- [ ] Configuración para activar IA completa por usuario

---

## ═══════════════════════════════════════
## FASE 34.10: TOOLKIT DE ARCHIVOS ⏳
## ═══════════════════════════════════════

**Prioridad:** 🔴 CRÍTICA  
**Tiempo:** 6 horas  
**Agente:** 🟡 BACKEND

### Objetivo:
Crear las herramientas para que la IA pueda leer/escribir/editar archivos.

### Tareas:
- [ ] Crear clase `AIFileToolkit` en `tracking/ai_toolkit.py`
- [ ] Método `read_file(path)` - Leer cualquier archivo
- [ ] Método `write_file(path, content)` - Crear/sobrescribir archivo
- [ ] Método `edit_file(path, old, new)` - Editar sección de archivo
- [ ] Método `append_file(path, content)` - Agregar al final
- [ ] Método `delete_file(path)` - Eliminar con confirmación
- [ ] Método `list_directory(path)` - Listar carpeta
- [ ] Método `search_code(query, path)` - Buscar en código (grep)
- [ ] Método `create_directory(path)` - Crear carpeta
- [ ] Método `move_file(old, new)` - Mover/renombrar
- [ ] Límites de seguridad (no acceder fuera del proyecto)
- [ ] Logging de todas las operaciones

### Ejemplo de uso:
```python
toolkit = AIFileToolkit(project_root="/user_projects/123")
content = toolkit.read_file("app.py")
toolkit.edit_file("app.py", "old_code", "new_code")
toolkit.create_file("tracking/auth.py", auth_code)
files = toolkit.list_directory("static/js")
matches = toolkit.search_code("def login", ".")
```

---

## ═══════════════════════════════════════
## FASE 34.11: EJECUTOR DE COMANDOS ⏳
## ═══════════════════════════════════════

**Prioridad:** 🔴 CRÍTICA  
**Tiempo:** 4 horas  
**Agente:** 🟡 BACKEND

### Objetivo:
Permitir que la IA ejecute comandos del sistema de forma segura.

### Tareas:
- [ ] Crear clase `AICommandExecutor` en `tracking/ai_toolkit.py`
- [ ] Método `run_command(cmd, timeout)` - Ejecutar comando
- [ ] Método `install_package(name, manager)` - npm/pip install
- [ ] Método `run_script(path)` - Ejecutar script Python/Node
- [ ] Whitelist de comandos permitidos
- [ ] Blacklist de comandos peligrosos (rm -rf, etc.)
- [ ] Timeout para evitar cuelgues
- [ ] Captura de stdout y stderr
- [ ] Logging de comandos ejecutados

### Whitelist:
```python
ALLOWED_COMMANDS = {
    'npm': ['install', 'run', 'init', 'list'],
    'pip': ['install', 'list', 'show'],
    'python': True,  # cualquier script
    'python3': True,
    'node': True,
    'npx': True,
    'ls': True,
    'cat': True,
    'head': True,
    'tail': True,
    'mkdir': True,
    'touch': True,
    'git': ['status', 'log', 'diff', 'branch'],
}

BLOCKED_PATTERNS = [
    r'rm\s+-rf',
    r'rm\s+-r\s+/',
    r'sudo',
    r'chmod\s+777',
    r'curl.*\|.*bash',
    r'wget.*\|.*sh',
]
```

---

## ═══════════════════════════════════════
## FASE 34.12: DETECTOR DE ERRORES ⏳
## ═══════════════════════════════════════

**Prioridad:** 🔴 CRÍTICA  
**Tiempo:** 4 horas  
**Agente:** 🟡 BACKEND + 🟣 IA

### Objetivo:
La IA detecta errores en logs y los corrige automáticamente.

### Tareas:
- [ ] Crear clase `AIErrorDetector` en `tracking/ai_toolkit.py`
- [ ] Método `read_server_logs(lines)` - Leer logs del servidor
- [ ] Método `detect_errors(logs)` - Encontrar errores
- [ ] Método `analyze_error(error)` - Analizar causa raíz
- [ ] Método `suggest_fix(error)` - Sugerir corrección
- [ ] Método `auto_fix(error)` - Intentar corregir
- [ ] Patrones de errores comunes (Python, Node, etc.)
- [ ] Integración con la IA para análisis inteligente

### Patrones de error:
```python
ERROR_PATTERNS = {
    'python': [
        r'ModuleNotFoundError: No module named \'(\w+)\'',
        r'ImportError: cannot import name \'(\w+)\'',
        r'SyntaxError: (.+)',
        r'IndentationError: (.+)',
        r'TypeError: (.+)',
        r'NameError: name \'(\w+)\' is not defined',
    ],
    'node': [
        r'Error: Cannot find module \'(\w+)\'',
        r'SyntaxError: (.+)',
        r'TypeError: (.+)',
        r'ReferenceError: (\w+) is not defined',
    ],
}
```

---

## ═══════════════════════════════════════
## FASE 34.13: ENTENDEDOR DE PROYECTOS ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟡 ALTA  
**Tiempo:** 5 horas  
**Agente:** 🟡 BACKEND + 🟣 IA

### Objetivo:
La IA entiende el proyecto completo antes de trabajar.

### Tareas:
- [ ] Crear clase `AIProjectAnalyzer` en `tracking/ai_toolkit.py`
- [ ] Método `analyze_project()` - Análisis completo
- [ ] Detectar lenguaje principal (Python, Node, etc.)
- [ ] Detectar framework (Flask, Express, React, etc.)
- [ ] Leer dependencias (requirements.txt, package.json)
- [ ] Mapear estructura de archivos
- [ ] Identificar archivos principales
- [ ] Detectar patrones de código
- [ ] Generar contexto para la IA

### Resultado del análisis:
```python
{
    "language": "python",
    "framework": "flask",
    "dependencies": ["flask", "sqlalchemy", "requests"],
    "structure": {
        "app.py": "main",
        "tracking/": "services",
        "templates/": "views",
        "static/": "assets"
    },
    "entry_point": "app.py",
    "port": 5000,
    "database": "postgresql",
    "has_tests": False
}
```

---

## ═══════════════════════════════════════
## FASE 34.14: MULTI-LENGUAJE ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟡 ALTA  
**Tiempo:** 6 horas  
**Agente:** 🟣 IA

### Objetivo:
La IA genera código en cualquier lenguaje, no solo HTML/CSS/JS.

### Tareas:
- [ ] Expandir prompts para Python
- [ ] Expandir prompts para Node.js/Express
- [ ] Expandir prompts para SQL
- [ ] Expandir prompts para React
- [ ] Expandir prompts para API REST
- [ ] Templates de código por lenguaje
- [ ] Detectar lenguaje del proyecto y adaptar respuestas

### Templates por lenguaje:
```python
LANGUAGE_TEMPLATES = {
    'python_flask': "...",
    'python_fastapi': "...",
    'node_express': "...",
    'react': "...",
    'sql': "...",
    'docker': "...",
}
```

---

## ═══════════════════════════════════════
## FASE 34.15: SISTEMA DE DIFF ⏳
## ═══════════════════════════════════════

**Prioridad:** 🟠 MEDIA  
**Tiempo:** 3 horas  
**Agente:** 🔵 FRONTEND + 🟡 BACKEND

### Objetivo:
Mostrar diferencias antes de aplicar cambios.

### Tareas:
- [ ] Implementar generación de diff en backend
- [ ] Mostrar diff visual en frontend (verde/rojo)
- [ ] Botón "Aceptar cambios" / "Rechazar"
- [ ] Historial de cambios por archivo
- [ ] Rollback a versión anterior

---

## RESUMEN SECCIÓN 34 (ACTUALIZADO)

| Fase | Descripción | Prioridad | Tiempo | Estado |
|------|-------------|-----------|--------|--------|
| 34.1 | Conectar frontend con 8 fases | 🔴 CRÍTICA | 4h | ⏳ |
| 34.2 | Expandir capacidades IA | 🔴 CRÍTICA | 6h | ⏳ |
| 34.3 | Sistema de archivos virtual | 🟡 ALTA | 4h | ⏳ |
| 34.4 | Preview tiempo real | 🟡 ALTA | 3h | ⏳ |
| 34.5 | Panel archivos dinámico | 🟡 ALTA | 3h | ⏳ |
| 34.6 | Entendimiento intenciones | 🔴 CRÍTICA | 5h | ⏳ |
| 34.7 | Consola de comandos | 🟠 MEDIA | 4h | ⏳ |
| 34.8 | IA Local DeepSeek | 🟠 MEDIA | 4h | ⏳ |
| 34.9 | Bloquear IA usuarios | 🟡 ALTA | 2h | ⏳ |
| **34.10** | **Toolkit de archivos** | 🔴 CRÍTICA | 6h | ⏳ |
| **34.11** | **Ejecutor de comandos** | 🔴 CRÍTICA | 4h | ⏳ |
| **34.12** | **Detector de errores** | 🔴 CRÍTICA | 4h | ⏳ |
| **34.13** | **Entendedor de proyectos** | 🟡 ALTA | 5h | ⏳ |
| **34.14** | **Multi-lenguaje** | 🟡 ALTA | 6h | ⏳ |
| **34.15** | **Sistema de diff** | 🟠 MEDIA | 3h | ⏳ |

**TOTAL TIEMPO ESTIMADO: ~63 horas**

**ORDEN RECOMENDADO:**
```
FASE 1 (Seguridad): 34.9
FASE 2 (Core):      34.10 → 34.11 → 34.12 → 34.1
FASE 3 (Inteligencia): 34.6 → 34.13 → 34.14
FASE 4 (Frontend):  34.3 → 34.4 → 34.5 → 34.15
FASE 5 (Avanzado):  34.2 → 34.7 → 34.8
```

---

## ════════════════════════════════════════════════════════════════
## FIN SECCIÓN 34
## ════════════════════════════════════════════════════════════════

---

## PUNTO DE GUARDADO

**Última actualización:** 7 Diciembre 2025 20:45
**Sesión:** 8
**Agente activo:** DOCUMENTACIÓN TÉCNICA COMPLETA

### Última tarea trabajada
- Sección: 34 (ESPECIFICACIÓN TÉCNICA COMPLETA)
- Nombre: Sistema IA BUNK3R Constructor
- Estado: Documentada con 15 fases + especificaciones técnicas detalladas

### Archivos modificados en esta sesión:
- PROMPT_PENDIENTES_BUNK3R.md (añadida especificación técnica completa de +2000 líneas)

### NUEVO CONTENIDO AÑADIDO EN ESTA SESIÓN

```
┌────────────────────────────────────────────────────────────────┐
│  ESPECIFICACIONES TÉCNICAS COMPLETAS AÑADIDAS                  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  1. AIToolkit - Clase completa con todos los métodos:          │
│     - read_file() con implementación completa                  │
│     - edit_file() con implementación completa                  │
│     - write_file(), append_to_file(), delete_file()            │
│     - list_directory(), search_code(), get_file_info()         │
│     - run_command() con whitelist/blacklist                    │
│     - install_package(), run_script()                          │
│     - read_server_logs(), detect_errors(), analyze_error()     │
│     - analyze_project(), detect_language()                     │
│     - _validate_path(), _is_command_allowed() (seguridad)      │
│                                                                │
│  2. TaskType expandido - 30+ tipos de intenciones              │
│     - Creación: 12 tipos                                       │
│     - Modificación: 9 tipos                                    │
│     - Corrección: 6 tipos                                      │
│     - Ejecución: 6 tipos                                       │
│     - Lectura: 6 tipos                                         │
│     - Optimización: 5 tipos                                    │
│     - Explicación: 4 tipos                                     │
│     - Base de datos: 4 tipos                                   │
│                                                                │
│  3. IntentPatterns - Patrones regex para cada tipo             │
│     - Patrones para crear, modificar, corregir, ejecutar       │
│     - Patrones para leer, buscar, explicar, optimizar          │
│     - Método detect_intent() que retorna (TaskType, data)      │
│                                                                │
│  4. AIExecutionFlow - Flujos de ejecución por tarea            │
│     - MODIFICAR_ARCHIVO: 7 pasos                               │
│     - CORREGIR_ERROR: 11 pasos                                 │
│     - INSTALAR_DEPENDENCIA: 6 pasos                            │
│     - CREAR_API: 11 pasos                                      │
│     - LEER_ARCHIVO: 4 pasos                                    │
│     - BUSCAR_CODIGO: 4 pasos                                   │
│                                                                │
│  5. AIProjectContext - Memoria del proyecto                    │
│     - remember_file_created(), remember_file_modified()        │
│     - remember_command_executed(), remember_error_fixed()      │
│     - get_context_summary() para incluir en prompts            │
│     - save_to_db(), load_from_db() para persistencia           │
│                                                                │
│  6. AIVerificationSystem - Verificar acciones                  │
│     - verify_file_created(), verify_file_syntax()              │
│     - verify_server_running(), verify_endpoint_works()         │
│     - verify_package_installed(), full_verification()          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### LISTA DE PRIORIDADES DEFINITIVA

```
PRIORIDAD CRÍTICA (16 horas):
├── 1. AIToolkit.read_file()      → 2h
├── 2. AIToolkit.edit_file()      → 3h
├── 3. AIToolkit.write_file()     → 2h
├── 4. AIToolkit.run_command()    → 3h
├── 5. AIToolkit.read_logs()      → 2h
└── 6. IntentParser expandido     → 4h

PRIORIDAD ALTA (13 horas):
├── 7. AIToolkit.search_code()    → 2h
├── 8. AIToolkit.list_directory() → 1h
├── 9. AIToolkit.analyze_project()→ 3h
├── 10. AIVerificationSystem      → 3h
└── 11. AIProjectContext          → 4h

PRIORIDAD MEDIA (16 horas):
├── 12. Auto-corrección errores   → 4h
├── 13. Multi-lenguaje            → 5h
├── 14. Sistema de diff visual    → 3h
└── 15. Memoria persistente       → 4h

TOTAL: 45 horas de trabajo
```

### PLAN DE IMPLEMENTACIÓN POR SEMANAS

```
SEMANA 1 (CRÍTICO):
├── Día 1-2: AIToolkit básico (read, write, list)
├── Día 3:   AIToolkit.edit_file() (la más importante)
├── Día 4:   AIToolkit.run_command() + seguridad
└── Día 5:   IntentParser expandido

SEMANA 2 (ALTO):
├── Día 1:   AIToolkit.search_code() + read_logs()
├── Día 2:   AIToolkit.analyze_project()
├── Día 3:   AIProjectContext
└── Día 4-5: AIVerificationSystem + testing

SEMANA 3 (MEDIO):
├── Día 1-2: Auto-corrección de errores
├── Día 3-4: Multi-lenguaje (Python, Node, SQL)
└── Día 5:   Sistema de diff + memoria persistente
```

### ARCHIVOS A CREAR

| Archivo | Descripción |
|---------|-------------|
| `tracking/ai_toolkit.py` | Clase principal AIToolkit con todas las herramientas |
| `tracking/ai_project_context.py` | Memoria y contexto del proyecto |
| `tracking/ai_verification.py` | Sistema de verificación |
| `tracking/ai_execution_flow.py` | Flujos de ejecución por tarea |
| `tracking/ai_intent_patterns.py` | Patrones de detección de intenciones |

### ORDEN DE IMPLEMENTACIÓN RECOMENDADO

```
1. SEGURIDAD:    34.9 (Bloquear IA usuarios normales)
2. CORE TOOLS:   34.10 → 34.11 → 34.12 (Toolkit archivos/comandos/errores)
3. CONECTAR:     34.1 (Frontend con 8 fases)
4. INTELIGENCIA: 34.6 → 34.13 → 34.14 (Intenciones/proyecto/multi-lenguaje)
5. FRONTEND:     34.3 → 34.4 → 34.5 → 34.15 (Archivos/preview/diff)
6. AVANZADO:     34.2 → 34.7 → 34.8 (Capacidades/consola/DeepSeek)
```

### Notas para el próximo agente
- **PRIORIDAD MÁXIMA**: Implementar 34.10 (Toolkit de archivos) primero
- Sin el toolkit, la IA no puede leer/editar archivos del proyecto
- Crear archivo `tracking/ai_toolkit.py` con las clases necesarias
- El constructor de 8 fases ya existe, solo falta conectar herramientas
- Referencia: Yo (Replit Agent) uso: read, write, edit, bash, grep
- La IA debe poder hacer lo mismo para ser útil

---
