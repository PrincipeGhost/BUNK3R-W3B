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

### ÚLTIMA ACTUALIZACIÓN: 2025-12-13 - Fase 2.2 completada

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

**Estado:** [x] COMPLETADA - 2025-12-13

### Tareas:

#### 1.1 Limpiar usuarios existentes
- [!] OMITIDO - Se mantienen usuarios existentes para pruebas
- [x] Mantener estructura de tabla
- Archivos modificados: N/A
- Probado: SI

#### 1.2 Modificar tabla users
- [x] Agregar columna `email` VARCHAR(255) UNIQUE
- [x] Agregar columna `password_hash` TEXT
- [x] Agregar columna `email_verified` BOOLEAN DEFAULT FALSE
- [x] Agregar columna `registration_approved` BOOLEAN DEFAULT FALSE
- [x] Agregar columna `application_id` INTEGER
- [x] Agregar columna `telegram_linked` BOOLEAN DEFAULT FALSE
- [x] Agregar columna `linked_telegram_id` BIGINT
- Archivos modificados: Base de datos (ALTER TABLE)
- Probado: SI

#### 1.3 Crear tabla registration_applications
- [x] id SERIAL PRIMARY KEY
- [x] email VARCHAR(255)
- [x] responses JSONB (respuestas de encuesta)
- [x] status VARCHAR(20) DEFAULT 'pending'
- [x] created_at TIMESTAMP
- [x] reviewed_at TIMESTAMP
- [x] reviewed_by VARCHAR(255)
- [x] approval_token VARCHAR(255) (para link de registro)
- Archivos modificados: Base de datos (CREATE TABLE)
- Probado: SI

#### 1.4 Crear tabla survey_questions
- [x] id SERIAL PRIMARY KEY
- [x] question_text TEXT
- [x] question_type VARCHAR(20) (text/select/checkbox)
- [x] options JSONB
- [x] is_required BOOLEAN DEFAULT TRUE
- [x] order_position INTEGER
- [x] is_active BOOLEAN DEFAULT TRUE
- Archivos modificados: Base de datos (CREATE TABLE)
- Probado: SI

#### 1.5 Crear tabla email_verifications
- [x] id SERIAL PRIMARY KEY
- [x] user_id VARCHAR(255)
- [x] code VARCHAR(6)
- [x] created_at TIMESTAMP
- [x] expires_at TIMESTAMP
- [x] used BOOLEAN DEFAULT FALSE
- Archivos modificados: Base de datos (CREATE TABLE)
- Probado: SI

#### 1.6 Crear nuevos decoradores de autenticación
- [x] @require_web_auth - Requiere usuario logueado
- [x] @require_admin - Requiere ser admin/owner
- [x] @require_email_verified - Requiere email verificado
- [x] Funciones helper para sesiones (get_current_web_user, create_web_session, invalidate_web_session)
- Archivos modificados: bot/tracking_correos/decorators.py
- Probado: SI

---

## FASE 2: SISTEMA DE ENCUESTAS Y SOLICITUDES

**Estado:** [!] En progreso

### Tareas:

#### 2.1 Panel Admin - CRUD Encuestas
- [x] Endpoint GET /api/admin/survey/questions
- [x] Endpoint POST /api/admin/survey/questions
- [x] Endpoint PUT /api/admin/survey/questions/:id
- [x] Endpoint DELETE /api/admin/survey/questions/:id
- [x] UI en panel admin para gestionar preguntas
- Archivos modificados: routes/admin_routes.py (lineas 7323-7535), templates/admin.html, static/js/admin.js, static/css/admin.css
- Probado: SI (endpoints funcionan, requieren auth)

#### 2.2 Panel Admin - Solicitudes
- [x] Endpoint GET /api/admin/applications
- [x] Endpoint GET /api/admin/applications/:id
- [x] Endpoint POST /api/admin/applications/:id/approve
- [x] Endpoint POST /api/admin/applications/:id/reject
- [x] UI con lista de solicitudes y botones aprobar/rechazar
- Archivos modificados: routes/admin_routes.py (lineas 7537-7773), static/js/admin.js (ApplicationsModule actualizado), static/css/admin.css
- Probado: SI

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
| 2025-12-13 | 1 | 1.2 Modificar tabla users | Completado | 7 columnas agregadas |
| 2025-12-13 | 1 | 1.3 Crear registration_applications | Completado | Tabla e índices creados |
| 2025-12-13 | 1 | 1.4 Crear survey_questions | Completado | Tabla creada |
| 2025-12-13 | 1 | 1.5 Crear email_verifications | Completado | Tabla e índices creados |
| 2025-12-13 | 1 | 1.6 Crear decoradores web | Completado | 3 decoradores + 3 helpers |
| 2025-12-13 | 2.1 | UI Panel Admin Encuestas | Completado | SurveyModule + ApplicationsModule |
| 2025-12-13 | 2.2 | Panel Admin Solicitudes | Completado | 4 endpoints + UI completa |

---

## ERRORES ENCONTRADOS

| Fecha | Descripción | Archivo | Estado |
|-------|-------------|---------|--------|
| - | Ninguno hasta ahora | - | - |

---

## ARCHIVOS MODIFICADOS (RESUMEN)

- **bot/tracking_correos/decorators.py** - Agregados: @require_web_auth, @require_admin, @require_email_verified, get_current_web_user(), create_web_session(), invalidate_web_session()
- **Base de datos** - Nuevas columnas en users, nuevas tablas: registration_applications, survey_questions, email_verifications
- **templates/admin.html** - Agregadas secciones section-survey y section-applications con navegación "Registro Web"
- **static/js/admin.js** - Agregados módulos SurveyModule y ApplicationsModule
- **static/css/admin.css** - Agregados estilos para las nuevas secciones de encuestas y solicitudes
