# PROMPT_PENDIENTES_BUNK3R-W3B.md

---

## MENÚ DE INICIO
Al iniciar cada sesión, el agente DEBE preguntar:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
¿Qué quieres hacer?
1️⃣ CONTINUAR    → Retomo la siguiente sección pendiente
2️⃣ NUEVO PROMPT → Agrega nueva tarea/funcionalidad  
3️⃣ VER PROGRESO → Muestra estado actual del proyecto
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Esperando tu respuesta...
```

---

## ESTADO GENERAL DEL PROYECTO

| Métrica | Valor |
|---------|-------|
| Proyecto | BUNK3R-W3B |
| Última actualización | 5 Diciembre 2025 |
| Sección actual | SECCIÓN 17-21 |
| Total secciones | 21 |
| Completadas | 14 ✅ |
| Pendientes | 5 ⏳ |
| En progreso | 0 |

---

## REGLAS BASE DEL AGENTE – OBLIGATORIAS

### 1. Comunicación de Progreso
```
INICIO:   "Comenzando sección [X]: [Nombre]"
FIN:      "Completada sección [X]: [Nombre] | Pendientes: [lista]"
ERROR:    "Problema en sección [X]: [Descripción]"
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

### 5. Normas de Seguridad
**NO HACER:**
- Eliminar archivos sin confirmación
- Cambios destructivos sin aprobación
- Exponer datos sensibles

**OBLIGATORIO:**
- Respaldo antes de cambios mayores
- Validar entradas del usuario
- Mantener integridad del proyecto

---

## SECCIONES DE TRABAJO PENDIENTES

### Leyenda de Estados:
| Símbolo | Significado |
|---------|-------------|
| ✅ | Completado |
| 🔄 | En progreso |
| ⏳ | Pendiente |
| ❌ | Bloqueado/Error |

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 17: AUDITORÍA COMPLETA DE PAGOS Y RETIROS B3C ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** CRÍTICA  
**Agregado:** 5 Diciembre 2025  
**Origen:** Error TON_CONNECT_SDK_ERROR detectado por usuario
**Estado:** PENDIENTE

---

### ERROR DETECTADO:
```
Error: [TON_CONNECT_SDK_ERROR] z
SendTransactionRequest validation failed:
Invalid 'payload' in message at index 0
```

**Ubicación:** Función `buildTextCommentPayload()` en `static/js/app.js` (líneas 4318-4338)
**Causa raíz:** El payload se construye de forma incorrecta para TON Connect SDK

---

### PROMPT MAESTRO 17: SISTEMA DE PAGOS TON CONNECT

**OBJETIVO:** Corregir el error de payload y hacer que TODOS los pagos funcionen correctamente.

---

#### FASE 17.1: Corregir buildTextCommentPayload() ⏳

**Código actual problemático (líneas 4318-4338):**
```javascript
buildTextCommentPayload(comment) {
    if (!comment) return undefined;
    try {
        const textBytes = new TextEncoder().encode(comment);
        const payload = new Uint8Array(textBytes.length + 4);
        payload[0] = 0; // Opcode incorrecto
        payload[1] = 0;
        payload[2] = 0;
        payload[3] = 0;
        payload.set(textBytes, 4);
        let binary = '';
        for (let i = 0; i < payload.length; i++) {
            binary += String.fromCharCode(payload[i]);
        }
        return btoa(binary); // NO ES BOC VÁLIDO
    } catch (e) {
        console.error('Error building comment payload:', e);
        return undefined;
    }
}
```

**PROBLEMA:** TON Connect espera un Cell serializado (BOC), no un array de bytes en base64.

**TAREAS:**
- [ ] 17.1.1 Investigar formato correcto de payload para TON Connect
- [ ] 17.1.2 Opción A: Enviar transacción SIN payload (solo monto y destino)
- [ ] 17.1.3 Opción B: Usar librería @ton/ton para construir Cell correctamente
- [ ] 17.1.4 Probar que el modal de wallet se abra sin errores
- [ ] 17.1.5 Verificar que la transacción se envíe correctamente

**SOLUCIÓN PROPUESTA (sin payload):**
```javascript
const transaction = {
    validUntil: Math.floor(Date.now() / 1000) + 600,
    messages: [
        {
            address: response.hotWallet,
            amount: amountNano
            // SIN payload - usar verificación por monto/timing
        }
    ]
};
```

---

#### FASE 17.2: Probar TODOS los Botones de Compra B3C ⏳

**Botones a probar uno por uno:**
- [ ] 17.2.1 Botón "0.5 TON" (Prueba)
- [ ] 17.2.2 Botón "1 TON"
- [ ] 17.2.3 Botón "5 TON" (Popular)
- [ ] 17.2.4 Botón "10 TON"
- [ ] 17.2.5 Botón "20 TON"
- [ ] 17.2.6 Input personalizado (monto custom)

**Checklist por cada botón:**
1. ¿Se muestra toast "Preparando compra..."?
2. ¿Se abre modal de TON Connect/Wallet?
3. ¿El monto mostrado es correcto?
4. ¿La wallet destino es la correcta (hotWallet)?
5. ¿No hay error de payload?
6. ¿Se puede confirmar la transacción?
7. ¿Se verifica automáticamente después?
8. ¿Se acreditan los B3C al balance?

---

#### FASE 17.3: Verificar Sistema de Retiros ⏳

**Endpoints a verificar:**
- [ ] 17.3.1 `POST /api/b3c/withdraw` - Crear solicitud
- [ ] 17.3.2 `GET /api/b3c/withdraw/{id}/status` - Estado
- [ ] 17.3.3 `GET /api/admin/b3c/withdrawals` - Lista admin
- [ ] 17.3.4 `POST /api/admin/b3c/withdrawals/{id}/process` - Procesar

**UI a verificar:**
- [ ] 17.3.5 Modal de retiro se abre correctamente
- [ ] 17.3.6 Input de wallet destino funciona
- [ ] 17.3.7 Validación de dirección TON
- [ ] 17.3.8 Confirmación antes de enviar
- [ ] 17.3.9 Feedback de estado (pending, completed)

---

#### FASE 17.4: Verificar buildJettonTransferPayload() ⏳

**Código problemático (líneas 5897-5906):**
```javascript
buildJettonTransferPayload(destination, amount, comment) {
    return btoa(JSON.stringify({
        op: 0xf8a7ea5,
        queryId: Date.now(),
        amount: amount,
        destination: destination,
        responseDestination: destination,
        forwardAmount: '1',
        forwardPayload: comment
    }));
}
```

**PROBLEMA:** JSON stringificado NO es un formato válido para Jetton Transfer.

**TAREAS:**
- [ ] 17.4.1 Determinar si esta función se usa activamente
- [ ] 17.4.2 Si se usa, implementar Cell construction correcta
- [ ] 17.4.3 Si no se usa, marcar como deprecated o eliminar

---

#### CRITERIOS DE ACEPTACIÓN SECCIÓN 17:
- [ ] Error TON_CONNECT_SDK_ERROR eliminado
- [ ] Todos los botones de compra funcionan
- [ ] No hay errores en consola del navegador
- [ ] Transacciones se envían correctamente
- [ ] Balance se actualiza después de compra

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 18: AUDITORÍA DE NÚMEROS VIRTUALES ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** ALTA  
**Agregado:** 5 Diciembre 2025  
**Origen:** Usuario reporta "sin servicio" y botón atrás cierra app
**Estado:** PENDIENTE

---

### ERRORES DETECTADOS:

**Error 1: Botón "Atrás" cierra toda la app**
- **Ubicación:** `static/js/virtual-numbers.js` líneas 624-630
- **Código problemático:**
```javascript
function goBack() {
    if (tg) {
        tg.close(); // CIERRA TODA LA MINI APP!
    } else {
        window.location.href = '/';
    }
}
```

**Error 2: "Sin servicio" al cargar países/servicios**
- **Posible causa:** API key de SMSPool no configurada
- **Ubicación:** `tracking/smspool_service.py` líneas 19-22
```python
self.api_key = api_key or os.environ.get('SMSPOOL_API_KEY')
if not self.api_key:
    logger.warning("SMSPOOL_API_KEY not configured")
```

---

### PROMPT MAESTRO 18: NÚMEROS VIRTUALES COMPLETO

**OBJETIVO:** Hacer que toda la sección de números virtuales funcione perfectamente.

---

#### FASE 18.1: Corregir Botón "Atrás" ⏳

**TAREAS:**
- [ ] 18.1.1 Modificar `goBack()` para navegar en lugar de cerrar
- [ ] 18.1.2 Implementar navegación a pantalla principal
- [ ] 18.1.3 Probar en ambiente Telegram y fuera de Telegram

**SOLUCIÓN PROPUESTA:**
```javascript
function goBack() {
    // Navegar a la pantalla principal en lugar de cerrar
    window.location.href = '/';
}
```

---

#### FASE 18.2: Verificar Carga de Países ⏳

**Endpoint:** `/api/vn/countries?provider=smspool`

**TAREAS:**
- [ ] 18.2.1 Verificar que SMSPOOL_API_KEY esté configurada
- [ ] 18.2.2 Probar endpoint en navegador/consola
- [ ] 18.2.3 Verificar respuesta JSON válida
- [ ] 18.2.4 Verificar que se renderizan los países
- [ ] 18.2.5 Verificar banderas y nombres correctos

**Checklist de respuesta esperada:**
```json
{
  "success": true,
  "countries": [
    {"id": "1", "name": "United States", "flag": "🇺🇸"},
    {"id": "7", "name": "Russia", "flag": "🇷🇺"},
    ...
  ]
}
```

---

#### FASE 18.3: Verificar Carga de Servicios ⏳

**Endpoint:** `/api/vn/services?provider=smspool&country={countryId}`

**TAREAS:**
- [ ] 18.3.1 Seleccionar un país
- [ ] 18.3.2 Verificar que servicios se carguen
- [ ] 18.3.3 Verificar precios correctos en BUNK3RCO1N
- [ ] 18.3.4 Verificar iconos de servicios
- [ ] 18.3.5 Verificar que botones de servicio funcionen

**Servicios esperados:**
- WhatsApp, Telegram, Instagram, Facebook, TikTok
- Google, Gmail, Microsoft, Apple
- Netflix, Spotify, Discord, Steam
- PayPal, Binance, Coinbase
- Uber, Tinder, etc.

---

#### FASE 18.4: Verificar Compra de Número ⏳

**Endpoint:** `POST /api/vn/purchase`

**TAREAS:**
- [ ] 18.4.1 Seleccionar país + servicio
- [ ] 18.4.2 Verificar que balance sea suficiente
- [ ] 18.4.3 Hacer clic en "Comprar"
- [ ] 18.4.4 Verificar que se descuente del balance
- [ ] 18.4.5 Verificar que aparezca número asignado
- [ ] 18.4.6 Verificar indicador "Esperando SMS..."

---

#### FASE 18.5: Verificar Recepción de SMS ⏳

**Endpoint:** `/api/vn/check/{orderId}`

**TAREAS:**
- [ ] 18.5.1 Verificar polling automático funciona
- [ ] 18.5.2 Verificar backoff exponencial (2s→4s→8s...)
- [ ] 18.5.3 Verificar botón "Verificar" manual
- [ ] 18.5.4 Verificar que código SMS se muestre
- [ ] 18.5.5 Verificar botón "Copiar" funciona

---

#### FASE 18.6: Verificar Cancelación ⏳

**Endpoint:** `POST /api/vn/cancel/{orderId}`

**TAREAS:**
- [ ] 18.6.1 Verificar confirmación antes de cancelar
- [ ] 18.6.2 Verificar reembolso parcial
- [ ] 18.6.3 Verificar que balance se actualice
- [ ] 18.6.4 Verificar que orden desaparezca de activos

---

#### FASE 18.7: Verificar Historial ⏳

**Endpoint:** `/api/vn/history`

**TAREAS:**
- [ ] 18.7.1 Verificar que historial cargue
- [ ] 18.7.2 Verificar filtro por estado
- [ ] 18.7.3 Verificar filtro por servicio
- [ ] 18.7.4 Verificar filtro por fecha
- [ ] 18.7.5 Verificar información correcta en cada item

---

#### FASE 18.8: Verificar UI/UX Completo ⏳

**TAREAS:**
- [ ] 18.8.1 Pestañas funcionan (Comprar, Activos, Historial)
- [ ] 18.8.2 Búsqueda de países funciona
- [ ] 18.8.3 Búsqueda de servicios funciona
- [ ] 18.8.4 Skeleton loaders mientras carga
- [ ] 18.8.5 Toasts de éxito/error aparecen
- [ ] 18.8.6 Loading overlay durante operaciones

---

#### CRITERIOS DE ACEPTACIÓN SECCIÓN 18:
- [ ] Botón "Atrás" navega correctamente (no cierra app)
- [ ] Países se cargan con banderas
- [ ] Servicios se cargan con precios
- [ ] Compra de número funciona
- [ ] SMS se recibe y muestra
- [ ] Cancelación funciona con reembolso
- [ ] Historial muestra todas las órdenes
- [ ] No hay errores en consola

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 19: TRANSFERENCIAS DE B3C ENTRE USUARIOS ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** ALTA  
**Agregado:** 5 Diciembre 2025  
**Origen:** Funcionalidad crítica para economía interna
**Estado:** PENDIENTE

---

### PROMPT MAESTRO 19: TRANSFERENCIAS ENTRE USUARIOS

**OBJETIVO:** Implementar y verificar sistema completo de transferencias P2P.

---

#### FASE 19.1: Verificar/Crear Endpoint de Transferencia ⏳

**Endpoint esperado:** `POST /api/b3c/transfer`

**TAREAS:**
- [ ] 19.1.1 Buscar si existe endpoint de transferencia
- [ ] 19.1.2 Si no existe, crear endpoint:
```python
@app.route('/api/b3c/transfer', methods=['POST'])
def transfer_b3c():
    # Validar usuario origen
    # Validar usuario destino (por username o wallet)
    # Validar monto suficiente
    # Descontar de origen
    # Acreditar a destino
    # Registrar transacción
    # Notificar a ambos usuarios
```

- [ ] 19.1.3 Implementar validaciones:
  - Monto mínimo
  - Monto máximo
  - Usuario destino existe
  - Balance suficiente
  - No auto-transferencia

---

#### FASE 19.2: UI de Transferencia ⏳

**TAREAS:**
- [ ] 19.2.1 Verificar botón "Transferir" en wallet
- [ ] 19.2.2 Modal de transferencia con:
  - Input de destinatario (username o wallet)
  - Input de monto
  - Preview de comisión (si aplica)
  - Botón confirmar
  - Botón cancelar

- [ ] 19.2.3 Validaciones en frontend:
  - Formato de username/wallet
  - Monto numérico positivo
  - Balance suficiente

---

#### FASE 19.3: Búsqueda de Usuario Destino ⏳

**TAREAS:**
- [ ] 19.3.1 Endpoint para buscar usuario: `/api/users/search?q={query}`
- [ ] 19.3.2 Autocompletado mientras escribe
- [ ] 19.3.3 Mostrar avatar y username del destinatario
- [ ] 19.3.4 Confirmar usuario correcto antes de enviar

---

#### FASE 19.4: Historial de Transferencias ⏳

**TAREAS:**
- [ ] 19.4.1 Mostrar transferencias en historial de transacciones
- [ ] 19.4.2 Distinguir "Enviado a @usuario" vs "Recibido de @usuario"
- [ ] 19.4.3 Filtrar por tipo: envíos, recibidos

---

#### FASE 19.5: Notificaciones ⏳

**TAREAS:**
- [ ] 19.5.1 Notificación al receptor: "Has recibido X B3C de @usuario"
- [ ] 19.5.2 Notificación al emisor: "Transferencia exitosa a @usuario"
- [ ] 19.5.3 Push notification si está habilitado

---

#### CRITERIOS DE ACEPTACIÓN SECCIÓN 19:
- [ ] Botón "Transferir" funciona
- [ ] Se puede buscar usuario destino
- [ ] Transferencia se ejecuta correctamente
- [ ] Balances se actualizan en tiempo real
- [ ] Historial muestra transferencias
- [ ] Notificaciones funcionan

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 20: CONEXIÓN DE WALLET Y SINCRONIZACIÓN ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** ALTA  
**Agregado:** 5 Diciembre 2025  
**Origen:** Funcionalidad base para todo el sistema de pagos
**Estado:** PENDIENTE

---

### PROMPT MAESTRO 20: WALLET CONNECT Y SYNC

**OBJETIVO:** Verificar que toda la conexión de wallet funcione perfectamente.

---

#### FASE 20.1: Verificar TON Connect Initialization ⏳

**Ubicación:** `static/js/app.js` líneas 3587-3624

**TAREAS:**
- [ ] 20.1.1 Verificar que tonconnect-manifest.json esté accesible
- [ ] 20.1.2 Verificar que TonConnectUI se inicialice
- [ ] 20.1.3 Verificar `onStatusChange` callback
- [ ] 20.1.4 Verificar reconexión automática de wallet guardada

---

#### FASE 20.2: Verificar Botón "Conectar Wallet" ⏳

**TAREAS:**
- [ ] 20.2.1 Verificar que botón sea visible cuando no hay wallet
- [ ] 20.2.2 Verificar que se abra modal de TON Connect
- [ ] 20.2.3 Verificar opciones: Telegram Wallet, Tonkeeper, etc.
- [ ] 20.2.4 Verificar que al conectar, se guarde la wallet

---

#### FASE 20.3: Verificar Sincronización con Servidor ⏳

**Endpoint:** `POST /api/wallet/address`

**TAREAS:**
- [ ] 20.3.1 Al conectar wallet, se sincroniza con servidor
- [ ] 20.3.2 Wallet se guarda en base de datos
- [ ] 20.3.3 Al reconectar, se verifica que sea la misma wallet
- [ ] 20.3.4 Si es wallet diferente, manejar conflicto

---

#### FASE 20.4: Verificar Desconexión de Wallet ⏳

**TAREAS:**
- [ ] 20.4.1 Botón "Desconectar" funciona
- [ ] 20.4.2 Se limpia estado local
- [ ] 20.4.3 UI se actualiza (mostrar "Conectar Wallet")
- [ ] 20.4.4 Se notifica al servidor

---

#### FASE 20.5: Verificar UI de Wallet ⏳

**TAREAS:**
- [ ] 20.5.1 Balance B3C se muestra correctamente
- [ ] 20.5.2 Dirección de wallet truncada visible
- [ ] 20.5.3 Botón copiar dirección funciona
- [ ] 20.5.4 Historial de transacciones carga
- [ ] 20.5.5 Botones: Depositar, Retirar, Transferir funcionan

---

#### FASE 20.6: Verificar Dispositivos Confiables ⏳

**TAREAS:**
- [ ] 20.6.1 Sistema de dispositivos confiables
- [ ] 20.6.2 Agregar dispositivo actual como confiable
- [ ] 20.6.3 Verificar dispositivo antes de transacciones
- [ ] 20.6.4 UI de gestión de dispositivos

---

#### CRITERIOS DE ACEPTACIÓN SECCIÓN 20:
- [ ] TON Connect se inicializa sin errores
- [ ] Conexión de wallet funciona con todas las opciones
- [ ] Wallet se sincroniza con servidor
- [ ] Desconexión funciona correctamente
- [ ] UI muestra estado correcto de wallet
- [ ] Dispositivos confiables funcionan

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 21: REDISEÑO UI PROFESIONAL ESTILO NEO-BANCO ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** ALTA  
**Agregado:** 5 Diciembre 2025  
**Origen:** Usuario solicita diseño profesional estilo Binance
**Estado:** PENDIENTE

---

### OBJETIVO PRINCIPAL:

Rediseñar TODA la interfaz de usuario para que tenga un aspecto profesional de **NEO-BANCO** similar a:
- **Binance** (referencia principal)
- **Revolut**
- **N26**
- **Crypto.com**

### PALETA DE COLORES PROPUESTA (Estilo Binance Oscuro):

```css
:root {
    /* Fondos - Ultra oscuros con profundidad */
    --bg-primary: #0B0E11;        /* Negro profundo principal */
    --bg-secondary: #12161C;       /* Gris oscuro para secciones */
    --bg-card: #1E2329;            /* Tarjetas y modales */
    --bg-elevated: #2B3139;        /* Elementos elevados */
    --bg-input: #14181E;           /* Inputs y campos */
    
    /* Acentos - Dorado/Amarillo sutil (estilo Binance) */
    --accent-primary: #F0B90B;     /* Dorado principal */
    --accent-secondary: #FCD535;   /* Amarillo brillante hover */
    --accent-muted: #C99D07;       /* Dorado apagado */
    
    /* Estados */
    --accent-success: #0ECB81;     /* Verde éxito */
    --accent-warning: #F6AD55;     /* Naranja advertencia */
    --accent-danger: #F6465D;      /* Rojo peligro */
    --accent-info: #3B82F6;        /* Azul info */
    
    /* Texto */
    --text-primary: #EAECEF;       /* Blanco suave */
    --text-secondary: #848E9C;     /* Gris claro */
    --text-muted: #5E6673;         /* Gris oscuro */
    --text-accent: #F0B90B;        /* Dorado para énfasis */
    
    /* Bordes */
    --border-color: #2B3139;       /* Borde sutil */
    --border-hover: #3C4451;       /* Borde hover */
    
    /* Efectos */
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
    --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);
    --glow-accent: 0 0 20px rgba(240, 185, 11, 0.15);
}
```

---

### PROMPT MAESTRO 21: REDISEÑO COMPLETO NEO-BANCO

---

#### FASE 21.1: Pantalla de Carga (Splash Screen) ⏳

**Estado actual:** Logo BUNK3R básico con barra de progreso multicolor

**Rediseño requerido:**
- [ ] 21.1.1 Fondo negro profundo (#0B0E11) con textura sutil
- [ ] 21.1.2 Logo BUNK3R minimalista y elegante
  - Tipografía: Sans-serif bold, peso 700
  - Color: Blanco (#EAECEF) con "3" en dorado (#F0B90B)
  - Sin efectos de brillo excesivos
- [ ] 21.1.3 Barra de progreso profesional
  - Una sola línea fina
  - Color: Dorado degradado (#F0B90B → #FCD535)
  - Sin cuadrados de colores
- [ ] 21.1.4 Texto "SECURE ACCESS" → Cambiar por badge sutil
- [ ] 21.1.5 Indicador de carga minimalista (spinner circular dorado)
- [ ] 21.1.6 Versión en footer con tipografía discreta

**Mockup de código:**
```html
<div class="splash-screen">
    <div class="splash-content">
        <div class="splash-logo">
            <span class="logo-text">BUNK<span class="accent">3</span>R</span>
        </div>
        <div class="splash-tagline">Secure Digital Banking</div>
        <div class="splash-loader">
            <div class="loader-bar"></div>
        </div>
        <div class="splash-status">Initializing...</div>
    </div>
    <div class="splash-footer">
        <span class="version">v2.0</span>
    </div>
</div>
```

---

#### FASE 21.2: Pantalla de Verificación 2FA ⏳

**Estado actual:** Icono de candado amarillo circular, inputs con bordes azules

**Rediseño requerido:**
- [ ] 21.2.1 Eliminar icono de candado amarillo circular
- [ ] 21.2.2 Usar icono minimalista de escudo o llave (SVG línea fina)
- [ ] 21.2.3 Inputs de código 6 dígitos:
  - Fondo: #14181E
  - Borde: #2B3139 (normal), #F0B90B (focus)
  - Tipografía: Monospace, tamaño grande (32px)
  - Sin bordes azules brillantes
- [ ] 21.2.4 Botón "Verificar":
  - Fondo: Dorado (#F0B90B)
  - Texto: Negro (#0B0E11)
  - Hover: Dorado más claro (#FCD535)
  - Border-radius: 8px (no tan redondeado)
- [ ] 21.2.5 Badge "Conexión segura":
  - Sin emoji de círculo verde
  - Icono SVG de candado pequeño
  - Color: Gris sutil (#848E9C)

**Mockup de código:**
```html
<div class="auth-2fa-screen">
    <div class="auth-logo">BUNK<span class="accent">3</span>R</div>
    
    <div class="auth-icon">
        <svg class="shield-icon"><!-- Shield SVG --></svg>
    </div>
    
    <h2 class="auth-title">Two-Factor Authentication</h2>
    <p class="auth-subtitle">Enter the 6-digit code from your authenticator app</p>
    
    <div class="otp-inputs">
        <input type="text" maxlength="1" class="otp-input" />
        <input type="text" maxlength="1" class="otp-input" />
        <input type="text" maxlength="1" class="otp-input" />
        <span class="otp-separator">-</span>
        <input type="text" maxlength="1" class="otp-input" />
        <input type="text" maxlength="1" class="otp-input" />
        <input type="text" maxlength="1" class="otp-input" />
    </div>
    
    <button class="btn-verify">Verify</button>
    
    <div class="security-badge">
        <svg class="lock-icon"><!-- Lock SVG --></svg>
        <span>Secure connection</span>
    </div>
</div>
```

---

#### FASE 21.3: Navbar y Header ⏳

**ELIMINAR HEADER DUPLICADO:**
El header secundario con "BUNK3R", campana y avatar (el que está debajo del header principal) debe ser ELIMINADO porque:
- Las notificaciones ya están en la barra de navegación inferior
- Es redundante y rompe la estética
- Ocupa espacio innecesario

**Buscar y eliminar en templates/index.html:**
```html
<!-- ELIMINAR ESTE BLOQUE COMPLETO -->
<div class="sub-header">
    <button class="sidebar-toggle">≡</button>
    <span>BUNK3R</span>
    <button class="notif-btn">🔔</button>
    <div class="avatar">D</div>
</div>
```

**Rediseño del header principal:**
- [ ] 21.3.1 Solo UN header con fondo translúcido oscuro
- [ ] 21.3.2 Logo BUNK3R a la izquierda (pequeño)
- [ ] 21.3.3 Menú hamburguesa minimalista
- [ ] 21.3.4 SIN campana de notificaciones (ya está abajo)
- [ ] 21.3.5 Avatar solo si es necesario para acceso rápido al perfil

**MOVER "Tu historia" A LA IZQUIERDA:**
- [ ] 21.3.6 El icono de "Tu historia" debe estar pegado al borde izquierdo
- [ ] 21.3.7 No centrado como está actualmente
- [ ] 21.3.8 Modificar CSS:
```css
.stories-container {
    justify-content: flex-start;  /* En lugar de center */
    padding-left: 16px;
}
```

---

#### FASE 21.4: Bottom Navigation ⏳

**Rediseño requerido:**
- [ ] 21.4.1 Fondo: #12161C con blur
- [ ] 21.4.2 Iconos: Línea fina (#848E9C)
- [ ] 21.4.3 Icono activo: Dorado (#F0B90B)
- [ ] 21.4.4 Sin labels de texto (solo iconos)
- [ ] 21.4.5 Indicador activo: Línea dorada arriba del icono

---

#### FASE 21.5: Cards y Modales ⏳

**Rediseño requerido:**
- [ ] 21.5.1 Background: #1E2329
- [ ] 21.5.2 Bordes: 1px solid #2B3139
- [ ] 21.5.3 Border-radius: 12px (consistente)
- [ ] 21.5.4 Sombras sutiles, no exageradas
- [ ] 21.5.5 Headers de modal con borde inferior sutil

---

#### FASE 21.6: Botones ⏳

**Sistema de botones:**
- [ ] 21.6.1 **Primario:** Fondo dorado, texto negro
- [ ] 21.6.2 **Secundario:** Borde dorado, texto dorado, fondo transparente
- [ ] 21.6.3 **Terciario:** Solo texto dorado
- [ ] 21.6.4 **Danger:** Fondo rojo (#F6465D)
- [ ] 21.6.5 **Success:** Fondo verde (#0ECB81)
- [ ] 21.6.6 Todos con border-radius: 8px

---

#### FASE 21.7: Inputs y Forms ⏳

**Rediseño requerido:**
- [ ] 21.7.1 Background: #14181E
- [ ] 21.7.2 Borde normal: #2B3139
- [ ] 21.7.3 Borde focus: #F0B90B
- [ ] 21.7.4 Label: Gris (#848E9C) arriba del input
- [ ] 21.7.5 Placeholder: Gris oscuro (#5E6673)
- [ ] 21.7.6 Border-radius: 8px

---

#### FASE 21.8: Wallet Screen con Logo B3C ⏳

**Logo oficial BUNK3RCO1N (B3C):**
- Archivo: `static/images/b3c-logo.png`
- Descripción: Bóveda metálica oscura con monedas doradas B3C
- Colores del logo: Azul (#4299E1) + Rojo (#E53E3E) en "B3C"

**Rediseño completo:**
- [ ] 21.8.1 **Header de Balance con Logo B3C:**
  ```html
  <div class="wallet-balance-header">
      <img src="/static/images/b3c-logo.png" class="b3c-logo" alt="B3C" />
      <div class="balance-info">
          <span class="balance-label">Balance Disponible</span>
          <span class="balance-value">1,234.56 <span class="currency">B3C</span></span>
          <span class="balance-usd">≈ $123.45 USD</span>
      </div>
  </div>
  ```
- [ ] 21.8.2 **Estilos del logo B3C:**
  ```css
  .b3c-logo {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      object-fit: cover;
      box-shadow: 0 0 20px rgba(240, 185, 11, 0.2);
  }
  .balance-value {
      font-size: 36px;
      font-weight: 700;
      color: #EAECEF;
  }
  .balance-value .currency {
      color: #F0B90B;
      font-size: 24px;
  }
  .balance-usd {
      color: #848E9C;
      font-size: 14px;
  }
  ```
- [ ] 21.8.3 Logo B3C también en:
  - Historial de transacciones (icono pequeño 24px)
  - Modal de compra/venta
  - Confirmaciones de pago
  - Toast de éxito al recibir B3C
- [ ] 21.8.4 Gráfico de precio minimalista (si aplica)
- [ ] 21.8.5 Acciones rápidas: Iconos circulares con fondo #2B3139
  - Depositar, Retirar, Transferir, Comprar
- [ ] 21.8.6 Lista de transacciones:
  - Logo B3C pequeño a la izquierda
  - Descripción y fecha
  - Monto a la derecha (verde +/rojo - según tipo)

---

#### FASE 21.9: Iconografía ⏳

**Reemplazar todos los emojis por iconos SVG:**
- [ ] 21.9.1 Crear/usar set de iconos consistente (Lucide, Heroicons, o custom)
- [ ] 21.9.2 Eliminar TODOS los emojis de la UI
- [ ] 21.9.3 Iconos en color #848E9C (normal) y #EAECEF (hover)
- [ ] 21.9.4 Iconos de acento en dorado #F0B90B

---

#### FASE 21.10: Tipografía ⏳

**Sistema tipográfico:**
- [ ] 21.10.1 Font principal: Inter, SF Pro, o similar sans-serif
- [ ] 21.10.2 Monospace para números/códigos: JetBrains Mono o similar
- [ ] 21.10.3 Pesos: 400 (normal), 500 (medium), 600 (semibold), 700 (bold)
- [ ] 21.10.4 Tamaños consistentes:
  - H1: 28px
  - H2: 24px
  - H3: 20px
  - Body: 16px
  - Small: 14px
  - Caption: 12px

---

#### FASE 21.11: Animaciones y Transiciones ⏳

**Mejoras de UX:**
- [ ] 21.11.1 Transiciones suaves (200-300ms)
- [ ] 21.11.2 Ease-out para entradas, ease-in para salidas
- [ ] 21.11.3 Micro-interacciones en botones (scale 0.98 on click)
- [ ] 21.11.4 Loading states con skeleton dorado
- [ ] 21.11.5 Page transitions suaves

---

#### FASE 21.12: Toasts y Notificaciones ⏳

**Rediseño:**
- [ ] 21.12.1 Fondo: #1E2329
- [ ] 21.12.2 Borde izquierdo de color según tipo:
  - Success: Verde
  - Error: Rojo
  - Warning: Naranja
  - Info: Azul
- [ ] 21.12.3 Iconos SVG en lugar de emojis
- [ ] 21.12.4 Posición: Top center con slide-down animation

---

#### CRITERIOS DE ACEPTACIÓN SECCIÓN 21:

- [ ] App se ve profesional como Binance/Revolut
- [ ] Paleta de colores consistente (negro + dorado)
- [ ] Sin emojis en la UI (solo iconos SVG)
- [ ] Tipografía limpia y legible
- [ ] Inputs y botones profesionales
- [ ] Animaciones suaves y elegantes
- [ ] Responsive en todos los tamaños
- [ ] Dark mode por defecto

---

## SECCIONES ARCHIVADAS (COMPLETADAS)

Las siguientes secciones han sido completadas y archivadas:

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
- ✅ **Sección 15** - Token BUNK3RCO1N Real en Blockchain (100%)
- ✅ **Sección 16** - Pagos Directos y Wallets Reales (100%)

---

## HISTORIAL DE PROMPTS

| # | Fecha | Prompt del Usuario | Acción Tomada | Estado |
|---|-------|-------------------|---------------|--------|
| 1 | 05/12/2025 | Configuración inicial | Creado archivo PROMPT_PENDIENTES | ✅ |
| 2 | 05/12/2025 | Token BUNK3RCO1N real | SECCIÓN 15 - Token MAINNET | ✅ |
| 3 | 05/12/2025 | Botones de pago directo | SECCIÓN 16 - TON Connect | ✅ |
| 4 | 05/12/2025 | Error TON_CONNECT_SDK_ERROR | SECCIÓN 17 - Auditoría pagos | ⏳ |
| 5 | 05/12/2025 | Números virtuales sin servicio + botón atrás | SECCIÓN 18 - Auditoría VN | ⏳ |
| 6 | 05/12/2025 | Transferencias entre usuarios | SECCIÓN 19 - Transferencias P2P | ⏳ |
| 7 | 05/12/2025 | Conexión wallet completa | SECCIÓN 20 - Wallet Connect | ⏳ |
| 8 | 05/12/2025 | Rediseño UI neo-banco estilo Binance | SECCIÓN 21 - UI Profesional | ⏳ |

---

## INSTRUCCIONES DE CONTINUACIÓN AUTOMÁTICA

Cuando el usuario diga "continúa", el agente DEBE:
1. Leer este archivo completo
2. Identificar la siguiente sección pendiente (⏳)
3. Informar: "Comenzando sección [X]: [Nombre]"
4. Ejecutar TODAS las tareas de esa sección
5. Probar como usuario real
6. Verificar logs y consola
7. Actualizar este archivo (marcar ✅)
8. Actualizar replit.md
9. Informar: "Completada sección [X]. ¿Continúo con la siguiente?"

---

## ORDEN DE EJECUCIÓN RECOMENDADO

1. **SECCIÓN 17** - Corregir error de payload TON Connect (CRÍTICO)
2. **SECCIÓN 20** - Verificar conexión de wallet (BASE)
3. **SECCIÓN 18** - Arreglar números virtuales 
4. **SECCIÓN 19** - Implementar transferencias P2P
5. **SECCIÓN 21** - Rediseño UI neo-banco (VISUAL)

---

## RESUMEN FINAL

### SECCIONES ACTIVAS:
- ⏳ **Sección 17** - Auditoría de Pagos B3C (0%) - CRÍTICO
- ⏳ **Sección 18** - Auditoría Números Virtuales (0%)
- ⏳ **Sección 19** - Transferencias entre Usuarios (0%)
- ⏳ **Sección 20** - Conexión de Wallet (0%)
- ⏳ **Sección 21** - Rediseño UI Neo-Banco (0%) - VISUAL

### PROGRESO: 14/21 secciones (67%)

**Próximo paso:** Ejecutar SECCIÓN 17 para corregir el error de payload TON Connect.
