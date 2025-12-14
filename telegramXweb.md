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

### ÚLTIMA ACTUALIZACIÓN: 2025-12-14 - Fase 5 completada

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

**Estado:** [x] COMPLETADA - 2025-12-13

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
- [x] Ruta /solicitud (página pública)
- [x] Formulario que carga preguntas de survey_questions
- [x] Endpoint POST /api/public/apply
- [x] Validación de campos requeridos
- [x] Mensaje de confirmación al enviar
- Archivos modificados: app.py (lineas 1519-1636), templates/solicitud.html
- Probado: SI

---

## FASE 3: REGISTRO Y VERIFICACIÓN DE EMAIL

**Estado:** [x] COMPLETADA - 2025-12-14

### Tareas:

#### 3.1 Configurar servicio de email
- [x] OMITIDO - Usuario decidió no usar verificación por email
- Nota: Se simplificó el flujo eliminando verificación por código de email
- Archivos modificados: N/A
- Probado: N/A

#### 3.2 Página de registro
- [x] Ruta /registro (solo con token de aprobación válido)
- [x] Formulario: usuario, contraseña, repetir contraseña
- [x] Validaciones (usuario único, email coincide con solicitud, passwords match)
- [x] Endpoint GET /api/auth/verify-token
- [x] Endpoint POST /api/auth/register
- Archivos modificados: app.py (lineas 1640-1800), templates/registro.html
- Probado: SI (2025-12-14)

#### 3.3 Verificación de email
- [x] OMITIDO - Usuario decidió no usar verificación por email
- Nota: email_verified se marca como TRUE automáticamente al registrar
- Archivos modificados: N/A
- Probado: N/A

#### 3.4 Configuración obligatoria de 2FA
- [x] Después de registro, redirigir a /setup-2fa
- [x] Generar secreto TOTP
- [x] Mostrar QR code
- [x] Validar primer código 2FA
- [x] Activar cuenta completamente
- Archivos modificados: app.py (lineas 1802-1930), templates/setup_2fa.html
- Probado: SI (2025-12-14)

---

## FASE 4: LOGIN Y SESIONES

**Estado:** [x] COMPLETADA - 2025-12-14

### Tareas:

#### 4.1 Página de login
- [x] Ruta /login
- [x] Formulario paso 1: solo usuario
- [x] Formulario paso 2: código 2FA (si usuario existe)
- [x] Mensaje "Acceso denegado" si no existe (sin detalles)
- Archivos modificados: app.py (linea 1656-1659), templates/login.html
- Probado: SI (2025-12-14)

#### 4.2 Endpoints de login
- [x] POST /api/auth/login/step1 - Verificar si usuario existe
- [x] POST /api/auth/login/step2 - Verificar código 2FA
- [x] Crear sesión segura con Flask-Session
- Archivos modificados: app.py (lineas 1951-2059)
- Probado: SI (2025-12-14)

#### 4.3 Logout
- [x] Endpoint POST /api/auth/logout
- [x] Invalidar sesión
- [x] Redirigir a /login
- Archivos modificados: app.py (lineas 2062-2082)
- Probado: SI (2025-12-14)

---

## FASE 5: PERFIL DE USUARIO

**Estado:** [x] COMPLETADA - 2025-12-14

### Tareas:

#### 5.1 Foto de perfil
- [x] Endpoint POST /api/user/web/avatar
- [x] Endpoint DELETE /api/user/web/avatar
- [x] Subir a Cloudinary (método upload_avatar, sin encriptar, 256x256)
- [x] Actualizar avatar_url en BD
- Archivos modificados: routes/user_routes.py (lineas 3462-3541), bot/tracking_correos/cloudinary_service.py (lineas 215-265)
- Probado: SI (endpoints funcionan, requieren auth web)

#### 5.2 Editar información
- [x] Endpoint GET /api/user/web/profile
- [x] Endpoint PUT /api/user/web/profile
- [x] Cambiar first_name, last_name, bio
- [x] Sanitización de datos con html.escape
- Archivos modificados: routes/user_routes.py (lineas 3371-3459)
- Probado: SI

#### 5.3 Cambiar contraseña
- [x] Endpoint POST /api/user/web/change-password
- [x] Pedir: contraseña actual + nueva + confirmar
- [x] Validar contraseña actual con bcrypt
- [x] Actualizar password_hash
- [x] Validación mínimo 8 caracteres
- Archivos modificados: routes/user_routes.py (lineas 3544-3596)
- Probado: SI

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
| 2025-12-13 | 2.3 | Pagina publica solicitud | Completado | /solicitud + 2 endpoints publicos |
| 2025-12-14 | 3 | Registro y 2FA | Completado | /registro, /setup-2fa, 4 endpoints |
| 2025-12-14 | 4.1 | Pagina de login | Completado | /login con flujo de 2 pasos |
| 2025-12-14 | 4.2 | Endpoints de login | Completado | step1, step2 + sesiones |
| 2025-12-14 | 4.3 | Logout | Completado | Endpoint + invalidacion de sesion |
| 2025-12-14 | 5.1 | Foto de perfil | Completado | POST/DELETE /api/user/web/avatar + Cloudinary |
| 2025-12-14 | 5.2 | Editar informacion | Completado | GET/PUT /api/user/web/profile |
| 2025-12-14 | 5.3 | Cambiar contraseña | Completado | POST /api/user/web/change-password con bcrypt |

---

## ERRORES ENCONTRADOS

| Fecha | Descripción | Archivo | Estado |
|-------|-------------|---------|--------|
| - | Ninguno hasta ahora | - | - |

---

## ARCHIVOS MODIFICADOS (RESUMEN)

- **bot/tracking_correos/decorators.py** - Agregados: @require_web_auth, @require_admin, @require_email_verified, get_current_web_user(), create_web_session(), invalidate_web_session()
- **Base de datos** - Nuevas columnas en users (last_login_at), nuevas tablas: registration_applications, survey_questions, email_verifications
- **templates/admin.html** - Agregadas secciones section-survey y section-applications con navegación "Registro Web"
- **templates/login.html** - Nueva página de login con flujo de 2 pasos (usuario → 2FA)
- **templates/registro.html** - Página de registro con token de aprobación
- **templates/setup_2fa.html** - Página de configuración de 2FA con QR code
- **static/js/admin.js** - Agregados módulos SurveyModule y ApplicationsModule
- **static/css/admin.css** - Agregados estilos para las nuevas secciones de encuestas y solicitudes
- **app.py** - Rutas /login, /registro, /setup-2fa + endpoints de autenticación (login/step1, step2, logout, register, verify-token, setup-2fa, verify-2fa-setup)
