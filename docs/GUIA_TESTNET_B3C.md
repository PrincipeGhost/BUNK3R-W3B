# Guía de Configuración: Token B3C en TON Testnet

## Resumen

Esta guía te ayudará a crear y configurar el token BUNK3RCO1N (B3C) en la **testnet de TON** para probar todo el sistema antes de pasar a producción (mainnet).

---

## Requisitos Previos

| Requisito | Descripción |
|-----------|-------------|
| Wallet TON | Tonkeeper, TonHub o similar |
| TON de prueba | ~0.5 TON (gratis del faucet) |
| Tiempo | ~15 minutos |

---

## Paso 1: Configurar Wallet en Testnet

### 1.1 Usando Tonkeeper (Recomendado)

1. Abre Tonkeeper
2. Ve a **Configuración** (engranaje)
3. Busca **"Cambiar a Testnet"** o **"Developer Mode"**
4. Activa el modo testnet
5. Tu wallet cambiará a la red de prueba

### 1.2 Crear nueva wallet (si no tienes)

1. Descarga Tonkeeper desde https://tonkeeper.com/
2. Crea una nueva wallet
3. **GUARDA las 24 palabras de recuperación**
4. Activa testnet como se indica arriba

---

## Paso 2: Obtener TON de Prueba (Gratis)

### 2.1 Usar el Faucet Bot

1. Abre Telegram
2. Busca el bot: **@testgiver_ton_bot**
3. Envía el comando `/start`
4. El bot te enviará **5 TON de prueba** a tu wallet

### 2.2 Verificar recepción

1. Abre tu wallet en testnet
2. Deberías ver **5 TON** (testnet)
3. Si no aparece, espera 1-2 minutos

---

## Paso 3: Crear el Token B3C

### 3.1 Ir a TON Minter Testnet

1. Abre: **https://testnet.minter.ton.org/**
2. Haz clic en **"Connect Wallet"**
3. Conecta tu wallet Tonkeeper (testnet)

### 3.2 Configurar el Token

Usa estos valores exactos:

| Campo | Valor |
|-------|-------|
| **Name** | BUNK3RCO1N |
| **Symbol** | B3C |
| **Decimals** | 9 |
| **Amount** | 1000000000 |
| **Description** | Token interno de BUNK3R para servicios y marketplace |
| **Logo URL** | (opcional - puedes agregar después) |

### 3.3 Crear el Token

1. Revisa todos los datos
2. Haz clic en **"Deploy"** o **"Create Token"**
3. Confirma la transacción en tu wallet (~0.25 TON fee)
4. Espera confirmación (30-60 segundos)

### 3.4 Guardar la Dirección del Token

**MUY IMPORTANTE:**

1. Después de crear, copia la **dirección del contrato**
2. Se verá algo como: `EQxxxxx...` o `kQxxxxx...`
3. Guárdala en un lugar seguro

---

## Paso 4: Verificar el Token

### 4.1 En el Explorador

1. Abre: **https://testnet.tonscan.org/**
2. Pega la dirección del token
3. Deberías ver:
   - Nombre: BUNK3RCO1N
   - Símbolo: B3C
   - Supply: 1,000,000,000

### 4.2 En tu Wallet

1. Abre Tonkeeper (testnet)
2. Ve a la pestaña **"Jettons"** o **"Tokens"**
3. Deberías ver tu balance de B3C

---

## Paso 5: Configurar en BUNK3R

### 5.1 Variables de Entorno Necesarias

Una vez creado el token, necesitas configurar estas variables en el proyecto:

```
B3C_TOKEN_ADDRESS=EQxxxxx...     # Dirección del token (del paso 3.4)
B3C_HOT_WALLET=EQyyyyy...        # Tu wallet de testnet
B3C_USE_TESTNET=true             # Ya configurado
```

### 5.2 Pasos en Replit

1. Ve a la pestaña **"Secrets"** en Replit
2. Agrega cada variable con su valor
3. El servidor se reiniciará automáticamente

---

## Paso 6: Probar el Sistema

### 6.1 Verificar Configuración

1. Abre la app BUNK3R
2. Ve a la sección de Wallet/Token
3. Deberías ver:
   - Badge **"TESTNET"** (naranja)
   - Precio simulado de B3C
   - Opciones de compra/venta

### 6.2 Probar Funcionalidades

- [ ] Ver precio del token
- [ ] Ver balance de B3C
- [ ] Crear orden de compra (simulada)
- [ ] Ver dirección de depósito
- [ ] Ver historial de transacciones

---

## Diferencias Testnet vs Mainnet

| Aspecto | Testnet | Mainnet |
|---------|---------|---------|
| TON | Gratis (faucet) | Dinero real |
| Token | Solo pruebas | Valor real |
| Explorer | testnet.tonscan.org | tonscan.org |
| Minter | testnet.minter.ton.org | minter.ton.org |
| Riesgo | Ninguno | Pérdida de fondos |

---

## Solución de Problemas

### "No tengo suficiente TON"
- Usa el bot @testgiver_ton_bot para obtener más

### "El token no aparece en mi wallet"
- Asegúrate de estar en testnet
- Espera 2-3 minutos después de crear
- Agrega el token manualmente con su dirección

### "Error al conectar wallet"
- Verifica que la wallet esté en modo testnet
- Intenta desconectar y reconectar

### "La transacción falló"
- Espera 1-2 minutos e intenta de nuevo
- Verifica que tengas al menos 0.3 TON para fees

---

## Próximos Pasos (Cuando esté listo para Mainnet)

1. Cambiar `B3C_USE_TESTNET=false`
2. Crear token en https://minter.ton.org/ (mainnet)
3. Actualizar `B3C_TOKEN_ADDRESS` con la nueva dirección
4. Crear pool de liquidez en STON.fi
5. Configurar wallet de comisiones

---

## Enlaces Útiles

| Recurso | URL |
|---------|-----|
| TON Minter (Testnet) | https://testnet.minter.ton.org/ |
| TON Minter (Mainnet) | https://minter.ton.org/ |
| Explorer (Testnet) | https://testnet.tonscan.org/ |
| Explorer (Mainnet) | https://tonscan.org/ |
| Faucet Bot | https://t.me/testgiver_ton_bot |
| Tonkeeper | https://tonkeeper.com/ |
| STON.fi DEX | https://ston.fi/ |

---

## Notas de Seguridad

- **NUNCA** compartas tu frase de recuperación (24 palabras)
- Usa wallets separadas para testnet y mainnet
- Guarda las direcciones de contrato en un lugar seguro
- En testnet puedes experimentar sin riesgo

---

*Última actualización: 5 Diciembre 2025*
