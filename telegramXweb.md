# PROYECTO: MIGRACIÓN DE TELEGRAM A WEB TRADICIONAL

## INSTRUCCIONES PARA EL AGENTE

### REGLAS OBLIGATORIAS:
1. **CADA TAREA DEBE PROBARSE** - No marcar como completada hasta verificar que funciona
2. **ACTUALIZAR ESTE ARCHIVO** - Después de cada tarea completada, actualizar el estado aquí
3. **NO ACEPTAR ERRORES** - Si hay errores en el código, corregirlos antes de continuar
4. **ORDEN ESTRICTO** - Seguir las fases en orden, no saltar tareas
5. **DOCUMENTAR CAMBIOS** - Anotar qué archivos se modificaron en cada tarea
6. **MANTENER CONTEXTO** - Leer este archivo al inicio de cada sesión

### ESTADOS DE TAREAS:
- [ ] = Pendiente
- [x] = Completada y probada
- [!] = En progreso
- [E] = Error (requiere atención)

### ÚLTIMA ACTUALIZACIÓN: Pendiente de comenzar

---

## CONTEXTO DEL PROYECTO

### ¿QUÉ ESTAMOS HACIENDO?
Migrar el sistema de autenticación de Telegram WebApp a un sistema web tradicional con:
- Registro con usuario + correo + contraseña
- Verificación de correo
- 2FA obligatorio
- Aprobación manual de registros por admin

### ¿POR QUÉ?
- El owner quiere control total sobre quién se registra
- Ya no depender de Telegram para el acceso
- Mantener 2FA para seguridad

### ¿QUÉ MANTENER INTACTO?
- Sistema de billeteras (B3C, USDT, TON)
- telegram_service.py (para notificaciones opcionales)
- Toda la lógica de blockchain y pagos
- Cloudinary (para fotos de perfil)

### ¿QUÉ ELIMINAR/CAMBIAR?
- Autenticación via Telegram WebApp
- Decoradores @require_telegram_auth, @require_telegram_user
- Foto de perfil desde Telegram
- Validación de initData de Telegram

---

## FASE 1: BASE Y LIMPIEZA

**Estado:** [ ] No iniciada

### Tareas:

#### 1.1 Limpiar usuarios existentes
- [ ] Borrar todos los usuarios de la tabla users
- [ ] Mantener estructura de tabla
- Archivos modificados: 
- Probado: NO

#### 1.2 Modificar tabla users
- [ ] Agregar columna `email` VARCHAR(255) UNIQUE
- [ ] Agregar columna `password_hash` TEXT
- [ ] Agregar columna `email_verified` BOOLEAN DEFAULT FALSE
- [ ] Agregar columna `registration_approved` BOOLEAN DEFAULT FALSE
- [ ] Agregar columna `application_id` INTEGER
- [ ] Agregar columna `telegram_linked` BOOLEAN DEFAULT FALSE
- [ ] Agregar columna `linked_telegram_id` BIGINT
- Archivos modificados:
- Probado: NO

#### 1.3 Crear tabla registration_applications
- [ ] id SERIAL PRIMARY KEY
- [ ] email VARCHAR(255)
- [ ] responses JSONB (respuestas de encuesta)
- [ ] status VARCHAR(20) DEFAULT 'pending'
- [ ] created_at TIMESTAMP
- [ ] reviewed_at TIMESTAMP
- [ ] reviewed_by VARCHAR(255)
- [ ] approval_token VARCHAR(255) (para link de registro)
- Archivos modificados:
- Probado: NO

#### 1.4 Crear tabla survey_questions
- [ ] id SERIAL PRIMARY KEY
- [ ] question_text TEXT
- [ ] question_type VARCHAR(20) (text/select/checkbox)
- [ ] options JSONB
- [ ] is_required BOOLEAN DEFAULT TRUE
- [ ] order_position INTEGER
- [ ] is_active BOOLEAN DEFAULT TRUE
- Archivos modificados:
- Probado: NO

#### 1.5 Crear tabla email_verifications
- [ ] id SERIAL PRIMARY KEY
- [ ] user_id VARCHAR(255)
- [ ] code VARCHAR(6)
- [ ] created_at TIMESTAMP
- [ ] expires_at TIMESTAMP
- [ ] used BOOLEAN DEFAULT FALSE
- Archivos modificados:
- Probado: NO

#### 1.6 Crear nuevos decoradores de autenticación
- [ ] @require_web_auth - Requiere usuario logueado
- [ ] @require_admin - Requiere ser admin/owner
- [ ] @require_email_verified - Requiere email verificado
- [ ] Funciones helper para sesiones
- Archivos modificados:
- Probado: NO

---

## FASE 2: SISTEMA DE ENCUESTAS Y SOLICITUDES

**Estado:** [ ] No iniciada

### Tareas:

#### 2.1 Panel Admin - CRUD Encuestas
- [ ] Endpoint GET /api/admin/survey/questions
- [ ] Endpoint POST /api/admin/survey/questions
- [ ] Endpoint PUT /api/admin/survey/questions/:id
- [ ] Endpoint DELETE /api/admin/survey/questions/:id
- [ ] UI en panel admin para gestionar preguntas
- Archivos modificados:
- Probado: NO

#### 2.2 Panel Admin - Solicitudes
- [ ] Endpoint GET /api/admin/applications
- [ ] Endpoint GET /api/admin/applications/:id
- [ ] Endpoint POST /api/admin/applications/:id/approve
- [ ] Endpoint POST /api/admin/applications/:id/reject
- [ ] UI con lista de solicitudes y botones aprobar/rechazar
- Archivos modificados:
- Probado: NO

#### 2.3 Página pública de solicitud
- [ ] Ruta /solicitud (página pública)
- [ ] Formulario que carga preguntas de survey_questions
- [ ] Endpoint POST /api/public/apply
- [ ] Validación de campos requeridos
- [ ] Mensaje de confirmación al enviar
- Archivos modificados:
- Probado: NO

---

## FASE 3: REGISTRO Y VERIFICACIÓN DE EMAIL

**Estado:** [ ] No iniciada

### Tareas:

#### 3.1 Configurar servicio de email
- [ ] Integrar Gmail de Replit
- [ ] Crear función send_verification_email()
- [ ] Template de email para verificación
- Archivos modificados:
- Probado: NO

#### 3.2 Página de registro
- [ ] Ruta /registro (solo con token de aprobación válido)
- [ ] Formulario: usuario, email, contraseña, repetir contraseña
- [ ] Validaciones (usuario único, email coincide con solicitud, passwords match)
- [ ] Endpoint POST /api/auth/register
- Archivos modificados:
- Probado: NO

#### 3.3 Verificación de email
- [ ] Enviar código de 6 dígitos al correo
- [ ] Página /verificar-email
- [ ] Endpoint POST /api/auth/verify-email
- [ ] Marcar email_verified = true
- Archivos modificados:
- Probado: NO

#### 3.4 Configuración obligatoria de 2FA
- [ ] Después de verificar email, redirigir a /setup-2fa
- [ ] Generar secreto TOTP
- [ ] Mostrar QR code
- [ ] Validar primer código 2FA
- [ ] Activar cuenta completamente
- Archivos modificados:
- Probado: NO

---

## FASE 4: LOGIN Y SESIONES

**Estado:** [ ] No iniciada

### Tareas:

#### 4.1 Página de login
- [ ] Ruta /login
- [ ] Formulario paso 1: solo usuario
- [ ] Formulario paso 2: código 2FA (si usuario existe)
- [ ] Mensaje "Acceso denegado" si no existe (sin detalles)
- Archivos modificados:
- Probado: NO

#### 4.2 Endpoints de login
- [ ] POST /api/auth/login/step1 - Verificar si usuario existe
- [ ] POST /api/auth/login/step2 - Verificar código 2FA
- [ ] Crear sesión segura con Flask-Session
- Archivos modificados:
- Probado: NO

#### 4.3 Logout
- [ ] Endpoint POST /api/auth/logout
- [ ] Invalidar sesión
- [ ] Redirigir a /login
- Archivos modificados:
- Probado: NO

---

## FASE 5: PERFIL DE USUARIO

**Estado:** [ ] No iniciada

### Tareas:

#### 5.1 Foto de perfil
- [ ] Endpoint POST /api/user/avatar
- [ ] Subir a Cloudinary
- [ ] Actualizar avatar_url en BD
- [ ] UI para cambiar foto
- Archivos modificados:
- Probado: NO

#### 5.2 Editar información
- [ ] Endpoint PUT /api/user/profile
- [ ] Cambiar nombre, bio, etc.
- [ ] UI en perfil
- Archivos modificados:
- Probado: NO

#### 5.3 Cambiar contraseña
- [ ] Endpoint POST /api/user/change-password
- [ ] Pedir: contraseña actual + nueva + confirmar
- [ ] Validar contraseña actual
- [ ] Actualizar password_hash
- Archivos modificados:
- Probado: NO

---

## FASE 6: VINCULACIÓN DE TELEGRAM

**Estado:** [ ] No iniciada

### Tareas:

#### 6.1 UI de vinculación
- [ ] Sección en perfil "Vincular Telegram"
- [ ] Mostrar instrucciones y nombre del bot
- [ ] Estado: vinculado/no vinculado
- Archivos modificados:
- Probado: NO

#### 6.2 Comando en bot
- [ ] Comando /vincular en el bot
- [ ] Bot pide código 2FA
- [ ] Verificar código contra la cuenta
- [ ] Si válido, guardar linked_telegram_id
- [ ] Marcar telegram_linked = true
- Archivos modificados:
- Probado: NO

---

## FASE 7: LIMPIEZA FINAL

**Estado:** [ ] No iniciada

### Tareas:

#### 7.1 Remover código muerto
- [ ] Eliminar validate_telegram_webapp_data (si no se usa)
- [ ] Eliminar download_telegram_photo
- [ ] Limpiar decoradores viejos no usados
- [ ] Limpiar imports no usados
- Archivos modificados:
- Probado: NO

#### 7.2 Actualizar rutas
- [ ] Verificar todas las rutas usan nuevos decoradores
- [ ] Actualizar index.html y templates
- [ ] Probar flujo completo
- Archivos modificados:
- Probado: NO

#### 7.3 Documentación
- [ ] Actualizar replit.md
- [ ] Documentar nuevos endpoints
- Archivos modificados:
- Probado: NO

---

## REGISTRO DE CAMBIOS

| Fecha | Fase | Tarea | Estado | Notas |
|-------|------|-------|--------|-------|
| - | - | - | - | Pendiente de comenzar |

---

## ERRORES ENCONTRADOS

| Fecha | Descripción | Archivo | Estado |
|-------|-------------|---------|--------|
| - | - | - | - |

---

## ARCHIVOS MODIFICADOS (RESUMEN)

- (Se actualizará conforme avance el proyecto)
