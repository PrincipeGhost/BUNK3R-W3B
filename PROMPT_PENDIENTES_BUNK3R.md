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
| Sección actual | 15 |
| Total secciones | 15 |
| Completadas | 14 ✅ |
| Pendientes | 1 ⏳ |
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

### SECCIÓN 15: Token BUNK3RCO1N Real en Blockchain ⏳
**Prioridad:** ALTA  
**Agregado:** 5 Diciembre 2025  
**Origen:** Prompt del usuario - Crear token real con liquidez automática

---

#### 📋 DESCRIPCIÓN GENERAL

Crear el token BUNK3RCO1N (B3C) como un **Jetton real en la blockchain TON** con las siguientes características:
- Token visible en wallets (Tonkeeper, Telegram Wallet, etc.)
- Cada compra en la app agrega liquidez al DEX
- Los usuarios pueden retirar tokens reales a su wallet
- El token tiene valor de mercado real
- Sistema de comisiones para el propietario
- Bot de estabilización cuando llegue a ~$1 USD

---

#### 🎯 OBJETIVOS

1. **Token con valor real** - No solo créditos internos, sino un token que se puede tradear
2. **Liquidez automática** - Cada compra suma al pool del DEX
3. **Doble uso** - Interno en la app + externo en mercado
4. **Ingresos por comisión** - % de cada transacción
5. **Precio estable (futuro)** - Bot que mantenga precio máximo ~$1 USD

---

#### 📦 FASE 15.1: Creación del Token Jetton ⏳

**Tareas:**
- [ ] 15.1.1 Crear token BUNK3RCO1N usando TON Minter (https://minter.ton.org)
  - Nombre: BUNK3RCO1N
  - Símbolo: B3C
  - Supply: 1,000,000,000 (mil millones)
  - Decimales: 9 (estándar TON)
  - Logo: Usar logo existente de BUNK3R
  - Costo: ~0.25 TON (~$1.50 USD)

- [ ] 15.1.2 Guardar datos del token
  - Dirección del contrato Jetton Master
  - Guardar en variables de entorno/secrets
  - Documentar en replit.md

- [ ] 15.1.3 Verificar token en exploradores
  - Confirmar en https://tonviewer.com
  - Confirmar en https://tonscan.org

**Criterios de aceptación:**
- [ ] Token creado y visible en blockchain
- [ ] Logo aparece correctamente
- [ ] Supply total correcto

---

#### 📦 FASE 15.2: Pool de Liquidez Inicial ⏳

**Tareas:**
- [ ] 15.2.1 Crear pool en STON.fi o DeDust
  - Par: B3C/TON
  - Liquidez inicial mínima: ~$10 USD
  - Ejemplo: 2 TON + 20,000 B3C
  - Precio inicial: 1 B3C = 0.0001 TON (~$0.0006 USD)

- [ ] 15.2.2 Documentar dirección del pool
  - Guardar address del pool
  - Link al pool en el DEX

- [ ] 15.2.3 Verificar que el token es tradeable
  - Probar swap pequeño
  - Confirmar precio visible

**Criterios de aceptación:**
- [ ] Pool creado y funcional
- [ ] Token aparece en DEX
- [ ] Se puede comprar/vender

**Notas:**
> El precio inicial es muy bajo intencionalmente. 
> Crecerá con cada compra que agregue liquidez.

---

#### 📦 FASE 15.3: Integración con la App - Compra vía DEX ⏳

**Tareas:**
- [ ] 15.3.1 Backend: Endpoint para swap via DEX
  ```
  POST /api/token/buy
  {
    "tonAmount": 10,        // TON que paga el usuario
    "slippage": 1           // % tolerancia de precio
  }
  
  Proceso:
  1. Calcular comisión (ej: 5% = 0.5 TON)
  2. Comisión → Wallet del propietario
  3. Resto (9.5 TON) → Swap en DEX
  4. B3C recibidos → Acreditar en balance interno del usuario
  5. Registrar transacción
  
  Response:
  {
    "success": true,
    "tokensReceived": 95000,
    "commission": 0.5,
    "newBalance": 95000
  }
  ```

- [ ] 15.3.2 Integrar SDK de STON.fi o DeDust
  - Instalar: @ston-fi/sdk o @dedust/sdk
  - Configurar conexión al pool
  - Implementar función de swap

- [ ] 15.3.3 Frontend: UI de compra actualizada
  - Mostrar precio actual del token (desde DEX)
  - Mostrar cantidad que recibirá
  - Mostrar comisión
  - Confirmar compra
  - Animación de éxito

- [ ] 15.3.4 Actualizar sistema de balance
  - El balance interno ahora representa tokens REALES
  - Cada compra = swap real en blockchain
  - Sincronizar balance interno con transacción real

**Criterios de aceptación:**
- [ ] Usuario puede comprar B3C pagando TON
- [ ] La compra va al DEX (agrega liquidez)
- [ ] Comisión va a wallet del propietario
- [ ] Balance se actualiza correctamente

---

#### 📦 FASE 15.4: Sistema de Retiro de Tokens ⏳

**Tareas:**
- [ ] 15.4.1 Backend: Endpoint para retiro
  ```
  POST /api/token/withdraw
  {
    "amount": 1000,                    // B3C a retirar
    "walletAddress": "UQ..."           // Wallet destino
  }
  
  Proceso:
  1. Verificar saldo suficiente
  2. Verificar dirección TON válida
  3. Enviar tokens reales desde hot wallet
  4. Descontar del balance interno
  5. Registrar transacción
  6. Notificar por Telegram
  
  Response:
  {
    "success": true,
    "txHash": "abc123...",
    "amountSent": 1000,
    "newBalance": 4000
  }
  ```

- [ ] 15.4.2 Implementar hot wallet para envíos
  - Wallet del sistema con B3C para retiros
  - Mantener saldo suficiente
  - Alertas cuando saldo bajo

- [ ] 15.4.3 Frontend: UI de retiro
  - Input de cantidad a retirar
  - Input de dirección de wallet (validar formato TON)
  - Mostrar fee de red (~0.05 TON)
  - Confirmación antes de enviar
  - Estado del retiro (pendiente/completado)

- [ ] 15.4.4 Límites y seguridad
  - Mínimo de retiro: 100 B3C
  - Máximo diario: 100,000 B3C
  - Cooldown entre retiros: 1 hora
  - Verificación 2FA para retiros grandes

**Criterios de aceptación:**
- [ ] Usuario puede retirar B3C a su wallet
- [ ] Tokens llegan a la wallet del usuario
- [ ] Balance interno se descuenta
- [ ] Límites funcionan correctamente

---

#### 📦 FASE 15.5: Sistema de Depósito de Tokens ⏳

**Tareas:**
- [ ] 15.5.1 Generar dirección de depósito por usuario
  - Cada usuario tiene dirección única
  - O usar memo/comment para identificar

- [ ] 15.5.2 Backend: Detectar depósitos entrantes
  - Polling de transacciones a la wallet
  - O usar webhooks de TON
  - Identificar usuario por dirección/memo
  - Acreditar balance interno

- [ ] 15.5.3 Frontend: UI de depósito
  - Mostrar dirección de depósito
  - QR code de la dirección
  - Instrucciones claras
  - Historial de depósitos

**Criterios de aceptación:**
- [ ] Usuario puede depositar B3C desde su wallet
- [ ] Sistema detecta el depósito
- [ ] Balance se acredita automáticamente

---

#### 📦 FASE 15.6: Comisiones y Ganancias ⏳

**Tareas:**
- [ ] 15.6.1 Configurar estructura de comisiones
  ```
  COMISIONES:
  - Compra de B3C: 5% (va a wallet propietario)
  - Retiro: Fee fijo (0.5 TON) + fee de red
  - Depósito: Gratis (solo fee de red del usuario)
  - Uso interno (compras en app): Sin comisión adicional
  ```

- [ ] 15.6.2 Dashboard de ganancias (admin)
  - Total comisiones recaudadas
  - Por período (día/semana/mes)
  - Por tipo de transacción
  - Exportar reportes

- [ ] 15.6.3 Wallet de comisiones
  - Wallet separada para recibir comisiones
  - Auto-transfer cuando acumule X cantidad

**Criterios de aceptación:**
- [ ] Comisiones se cobran correctamente
- [ ] Dashboard muestra ganancias
- [ ] Fondos llegan a wallet correcta

---

#### 📦 FASE 15.7: Precio en Tiempo Real ⏳

**Tareas:**
- [ ] 15.7.1 API para obtener precio actual
  ```
  GET /api/token/price
  
  Response:
  {
    "priceInTon": 0.0001,
    "priceInUsd": 0.0006,
    "change24h": "+15.5%",
    "volume24h": 1500,
    "liquidity": 5000,
    "marketCap": 6000
  }
  ```

- [ ] 15.7.2 Integrar con API de DEX
  - STON.fi API o DeDust API
  - Cache de precio (actualizar cada 30s)

- [ ] 15.7.3 UI de precio
  - Mostrar precio actual en la app
  - Gráfico simple de precio (24h/7d)
  - Indicador de cambio (+/-)

**Criterios de aceptación:**
- [ ] Precio se muestra en tiempo real
- [ ] Gráfico funciona
- [ ] Datos son precisos

---

#### 📦 FASE 15.8: Bot de Estabilización (Futuro - Cuando llegue a ~$1) 🔒

**Descripción:**
Cuando el precio del token se acerque a $1 USD, implementar un bot de market making que:
- Venda tokens cuando el precio suba de $1
- Compre tokens cuando baje de $0.95
- Mantenga el precio estable en el rango $0.95 - $1.05

**Tareas:**
- [ ] 15.8.1 Diseñar estrategia de estabilización
- [ ] 15.8.2 Implementar bot de trading
- [ ] 15.8.3 Configurar límites y parámetros
- [ ] 15.8.4 Monitoreo y alertas
- [ ] 15.8.5 Dashboard de operaciones del bot

**Nota:** Esta fase se activa SOLO cuando el token alcance ~$0.80 USD.
Requiere capital para operar (de las ganancias acumuladas).

---

#### 🔧 REQUISITOS TÉCNICOS

**Secrets/Variables de entorno necesarias:**
```
B3C_CONTRACT_ADDRESS=EQ...         # Dirección del token
B3C_POOL_ADDRESS=EQ...             # Dirección del pool DEX
B3C_HOT_WALLET_MNEMONIC=...        # Wallet para envíos (cifrado)
B3C_COMMISSION_WALLET=UQ...        # Wallet para comisiones
DEX_PROVIDER=stonfi                # stonfi o dedust
COMMISSION_PERCENT=5               # Porcentaje de comisión
```

**Dependencias nuevas:**
```
# Python
pytoniq          # Interacción con TON
tonsdk           # SDK de TON

# O usar API HTTP directamente a STON.fi/DeDust
```

**Base de datos - Nuevas tablas:**
```sql
-- Transacciones de tokens reales
CREATE TABLE token_transactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    type VARCHAR(20),           -- buy, sell, withdraw, deposit
    amount DECIMAL(20,9),       -- cantidad de B3C
    ton_amount DECIMAL(20,9),   -- cantidad de TON involucrado
    commission DECIMAL(20,9),   -- comisión cobrada
    tx_hash VARCHAR(100),       -- hash de transacción blockchain
    status VARCHAR(20),         -- pending, confirmed, failed
    wallet_address VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Direcciones de depósito por usuario
CREATE TABLE user_deposit_addresses (
    user_id VARCHAR(50) PRIMARY KEY,
    deposit_address VARCHAR(100),
    deposit_memo VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Cache de precio
CREATE TABLE token_price_cache (
    id SERIAL PRIMARY KEY,
    price_ton DECIMAL(20,9),
    price_usd DECIMAL(20,9),
    liquidity_ton DECIMAL(20,9),
    volume_24h DECIMAL(20,9),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

#### 📊 MÉTRICAS DE ÉXITO

| Métrica | Objetivo |
|---------|----------|
| Token creado | ✅ Visible en blockchain |
| Pool de liquidez | ✅ Funcional en DEX |
| Compras via DEX | ✅ Cada compra suma liquidez |
| Retiros | ✅ Usuarios pueden retirar |
| Precio visible | ✅ Tiempo real en la app |
| Comisiones | ✅ Se cobran correctamente |

---

#### ⚠️ RIESGOS Y MITIGACIONES

| Riesgo | Mitigación |
|--------|------------|
| Hot wallet hackeada | Mantener saldo mínimo, recargar frecuentemente |
| Precio manipulado | Bot de estabilización (Fase 8) |
| Run on bank | Límites de retiro diarios |
| Errores en swaps | Testing extensivo, transacciones reversibles |

---

#### 💰 COSTOS ESTIMADOS

| Concepto | Costo |
|----------|-------|
| Crear token | ~0.25 TON (~$1.50) |
| Pool inicial | ~2 TON (~$12) |
| Hot wallet inicial | ~5 TON (~$30) |
| Fees de operación | ~0.05 TON por tx |
| **TOTAL INICIAL** | **~$45-50 USD** |

---

## 📝 HISTORIAL DE PROMPTS

| # | Fecha | Prompt del Usuario | Acción Tomada | Estado |
|---|-------|-------------------|---------------|--------|
| 1 | 05/12/2025 | Configuración inicial del sistema de pendientes | Creado archivo PROMPT_PENDIENTES con estructura completa | ✅ |
| 2 | 05/12/2025 | Crear token BUNK3RCO1N real en blockchain con liquidez automática, retiros, comisiones y bot de estabilización | Creada SECCIÓN 15 con 8 fases detalladas | ⏳ |

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

### SECCIONES COMPLETADAS:
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

### SECCIONES PENDIENTES:
- ⏳ **Sección 15** - Token BUNK3RCO1N Real en Blockchain (0%)
  - 8 fases: Creación token → Pool liquidez → Compras DEX → Retiros → Depósitos → Comisiones → Precio real-time → Bot estabilización

### 📊 PROGRESO: 14/15 secciones (93%)

**Siguiente paso:** Ejecutar Sección 15 - Crear token real BUNK3RCO1N
