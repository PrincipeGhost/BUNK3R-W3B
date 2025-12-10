"""
User Routes - Endpoints de Usuario (perfil, publicaciones, social, mensajes)
Agente: Frontend-User
Rama: feature/frontend-user

Este archivo contiene los endpoints de usuario migrados desde app.py
Migracion: 10 Diciembre 2025

Endpoints migrados:
- /api/users/* - Perfil, follow, stats (14 endpoints)
- /api/messages/* - Chat privado (5 endpoints)
- /api/user/notifications/* - Notificaciones (2 endpoints)
"""

from flask import Blueprint, jsonify, request, Response, current_app
from datetime import datetime
import logging
import html
import base64
import os
import time
from werkzeug.utils import secure_filename
import psycopg2.extras

from tracking.decorators import require_telegram_auth, require_telegram_user
from tracking.services import get_db_manager, get_security_manager
from tracking.utils import rate_limit
import re

logger = logging.getLogger(__name__)


def validate_ton_address(address):
    """Validate TON wallet address format server-side."""
    if not address or not isinstance(address, str):
        return False, 'Direccion de wallet requerida'
    
    address = address.strip()
    
    if len(address) != 48:
        return False, 'La direccion debe tener 48 caracteres'
    
    prefix = address[:2]
    if prefix not in ['EQ', 'UQ']:
        return False, 'Direccion invalida. Debe empezar con EQ o UQ'
    
    if not re.match(r'^[A-Za-z0-9_-]+$', address):
        return False, 'La direccion contiene caracteres invalidos'
    
    return True, None

user_bp = Blueprint('user', __name__, url_prefix='/api')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename, extensions=None):
    """Verifica si el archivo tiene una extension permitida."""
    if extensions is None:
        extensions = ALLOWED_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


def sanitize_error(error, error_type='api_error'):
    """Sanitiza errores para no exponer informacion sensible."""
    return f"Error en operacion ({error_type})"


@user_bp.route('/user/health', methods=['GET'])
def user_health():
    """Health check del modulo user."""
    return jsonify({
        'success': True,
        'module': 'user_routes',
        'status': 'active',
        'message': 'Endpoints de usuario funcionando.',
        'endpoints_migrated': [
            '/api/users/<id>/profile (GET/PUT)',
            '/api/users/<id>/posts',
            '/api/users/<id>/follow (POST/DELETE)',
            '/api/users/<id>/followers',
            '/api/users/<id>/following',
            '/api/users/<id>/stats',
            '/api/users/me',
            '/api/users/me/profile (PUT)',
            '/api/users/me/avatar',
            '/api/users/avatar',
            '/api/avatar/<id>',
            '/api/messages (POST)',
            '/api/messages/conversations',
            '/api/messages/<id>',
            '/api/messages/<id>/read',
            '/api/messages/unread-count',
            '/api/user/notifications',
            '/api/user/notifications/read',
            '/api/posts (GET/POST)',
            '/api/posts/<id> (GET/DELETE)',
            '/api/posts/<id>/like (POST/DELETE)',
            '/api/publications/feed',
            '/api/publications/check-new',
            '/api/publications/<id> (GET/PUT/DELETE)',
            '/api/publications/gallery/<user_id>',
            '/api/publications/<id>/react (POST)',
            '/api/publications/<id>/unreact (POST)',
            '/api/publications/<id>/save (POST)',
            '/api/publications/<id>/unsave (POST)',
            '/api/publications/saved',
            '/api/publications/<id>/share (POST)',
            '/api/publications/<id>/share-count (POST)',
            '/api/publications/<id>/comments (GET/POST)',
            '/api/publications/<id>/pin-comment (POST)',
            '/api/comments/<id>/like (POST)',
            '/api/comments/<id>/unlike (POST)',
            '/api/comments/<id> (GET/PUT)',
            '/api/comments/<id>/react (POST/DELETE)',
            '/api/comments/<id>/reactions',
            '/api/devices/trusted (GET)',
            '/api/devices/trusted/check (POST)',
            '/api/devices/trusted/add (POST)',
            '/api/devices/trusted/remove (POST)',
            '/api/security/wallet/validate (POST)',
            '/api/security/wallet/primary (GET)',
            '/api/security/wallet/backup (POST)',
            '/api/security/wallet/primary/check (GET)',
            '/api/security/wallet/primary/register (POST)',
            '/api/wallet/debit (POST)',
            '/api/security/status (GET)',
            '/api/security/devices (GET)',
            '/api/security/devices/check (POST)',
            '/api/security/devices/add (POST)',
            '/api/security/devices/remove (POST)',
            '/api/security/devices/remove-all (POST)',
            '/api/security/activity (GET)',
            '/api/security/lockout/check (GET)'
        ]
    })


# ============================================================
# ENDPOINTS DE PERFIL DE USUARIO
# ============================================================

@user_bp.route('/users/<user_id>/profile', methods=['GET'])
@require_telegram_user
def get_user_profile(user_id):
    """Obtener perfil de un usuario."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        viewer = request.telegram_user
        viewer_id = str(viewer.get('id'))
        
        profile = db_manager.get_user_profile(user_id, viewer_id)
        
        if not profile:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({
            'success': True,
            'profile': {
                'id': profile.get('id'),
                'username': profile.get('username'),
                'firstName': profile.get('first_name'),
                'lastName': profile.get('last_name'),
                'avatarUrl': profile.get('avatar_url'),
                'bio': profile.get('bio'),
                'level': profile.get('level', 1),
                'credits': profile.get('credits', 0),
                'isVerified': profile.get('is_verified', False),
                'followersCount': profile.get('followers_count', 0),
                'followingCount': profile.get('following_count', 0),
                'postsCount': profile.get('posts_count', 0),
                'isFollowing': profile.get('is_following', False),
                'createdAt': profile.get('created_at').isoformat() if profile.get('created_at') else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user profile {user_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@user_bp.route('/users/<user_id>/profile', methods=['PUT'])
@require_telegram_user
def update_user_profile(user_id):
    """Actualizar perfil de un usuario."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        current_user = request.telegram_user
        current_user_id = str(current_user.get('id'))
        
        if current_user_id != user_id:
            return jsonify({'error': 'No autorizado'}), 403
        
        data = request.get_json()
        bio = data.get('bio')
        
        success = db_manager.update_user_profile(user_id, bio=bio)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Perfil actualizado correctamente'
            })
        else:
            return jsonify({'error': 'Error al actualizar perfil'}), 500
            
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@user_bp.route('/users/<user_id>/posts', methods=['GET'])
@require_telegram_user
def get_user_posts(user_id):
    """Obtener publicaciones de un usuario."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        limit = min(limit, 50)
        
        posts = db_manager.get_user_posts(user_id, limit=limit, offset=offset)
        
        result = []
        for post in posts:
            caption = post.get('caption')
            
            result.append({
                'id': post.get('id'),
                'userId': post.get('user_id'),
                'username': post.get('username'),
                'firstName': post.get('first_name'),
                'avatarUrl': post.get('avatar_url'),
                'contentType': post.get('content_type'),
                'contentUrl': post.get('content_url'),
                'caption': caption,
                'media': post.get('media') or [],
                'likesCount': post.get('likes_count', 0),
                'commentsCount': post.get('comments_count', 0),
                'sharesCount': post.get('shares_count', 0),
                'createdAt': post.get('created_at').isoformat() if post.get('created_at') else None
            })
        
        return jsonify({
            'success': True,
            'posts': result,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting user posts {user_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@user_bp.route('/users/me', methods=['GET'])
@require_telegram_user
def get_my_profile():
    """Obtener mi perfil actual con avatar."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        user_profile = db_manager.get_user_profile(user_id, user_id)
        
        if user_profile:
            return jsonify({
                'success': True,
                'profile': {
                    'id': user_profile.get('id'),
                    'username': user_profile.get('username'),
                    'firstName': user_profile.get('first_name'),
                    'lastName': user_profile.get('last_name'),
                    'avatarUrl': user_profile.get('avatar_url'),
                    'bio': user_profile.get('bio'),
                    'level': user_profile.get('level'),
                    'credits': user_profile.get('credits'),
                    'isVerified': user_profile.get('is_verified'),
                    'followersCount': user_profile.get('followers_count', 0),
                    'followingCount': user_profile.get('following_count', 0),
                    'postsCount': user_profile.get('posts_count', 0)
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Perfil no encontrado'}), 404
            
    except Exception as e:
        logger.error(f"Error getting my profile: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@user_bp.route('/users/me/profile', methods=['PUT'])
@require_telegram_user
def update_my_profile():
    """Actualizar mi perfil."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        data = request.get_json()
        
        bio = data.get('bio')
        avatar_url = data.get('avatarUrl')
        
        success = db_manager.update_user_profile(user_id, bio=bio, avatar_url=avatar_url)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Perfil actualizado correctamente'
            })
        else:
            return jsonify({'error': 'Error al actualizar perfil'}), 500
            
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@user_bp.route('/users/me/avatar', methods=['POST'])
@require_telegram_user
def upload_avatar():
    """Subir foto de perfil."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        if 'avatar' not in request.files:
            return jsonify({'error': 'No se envio ninguna imagen'}), 400
        
        file = request.files['avatar']
        
        if file.filename == '':
            return jsonify({'error': 'No se selecciono ninguna imagen'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de archivo no permitido. Usa PNG, JPG, JPEG, GIF o WEBP'}), 400
        
        db_manager.get_or_create_user(
            user_id=user_id,
            username=user.get('username'),
            first_name=user.get('first_name'),
            last_name=user.get('last_name'),
            telegram_id=user.get('id')
        )
        
        file_content = file.read()
        ext = file.filename.rsplit('.', 1)[1].lower()
        
        content_type = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }.get(ext, 'image/png')
        
        avatar_data = f"data:{content_type};base64,{base64.b64encode(file_content).decode('utf-8')}"
        
        success = db_manager.update_user_avatar_data(user_id, avatar_data)
        
        avatar_url = f"/api/avatar/{user_id}"
        
        if success:
            db_manager.update_user_profile(user_id, avatar_url=avatar_url)
            return jsonify({
                'success': True,
                'message': 'Foto de perfil actualizada',
                'avatarUrl': avatar_url
            })
        else:
            return jsonify({'error': 'Error al actualizar perfil'}), 500
            
    except Exception as e:
        logger.error(f"Error uploading avatar: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@user_bp.route('/avatar/<user_id>')
def serve_avatar(user_id):
    """Servir avatar desde la base de datos."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        avatar_data = db_manager.get_user_avatar_data(user_id)
        
        if not avatar_data:
            return jsonify({'error': 'Avatar not found'}), 404
        
        if avatar_data.startswith('data:'):
            header, encoded = avatar_data.split(',', 1)
            content_type = header.split(':')[1].split(';')[0]
            image_data = base64.b64decode(encoded)
            return Response(image_data, mimetype=content_type)
        else:
            return jsonify({'error': 'Invalid avatar format'}), 500
            
    except Exception as e:
        logger.error(f"Error serving avatar: {e}")
        return jsonify({'error': 'Avatar not found'}), 404


@user_bp.route('/users/avatar', methods=['POST'])
@require_telegram_user
def upload_user_avatar():
    """Subir avatar de usuario (alternativo)."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        if 'avatar' not in request.files:
            return jsonify({'error': 'No se envio archivo'}), 400
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'error': 'Archivo vacio'}), 400
        
        if file and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif', 'webp'}):
            filename = secure_filename(f"avatar_{user_id}_{int(time.time())}.{file.filename.rsplit('.', 1)[1].lower()}")
            
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads/avatars')
            avatars_folder = os.path.join(upload_folder)
            os.makedirs(avatars_folder, exist_ok=True)
            
            file_path = os.path.join(avatars_folder, filename)
            file.save(file_path)
            
            avatar_url = f"/static/uploads/avatars/{filename}"
            
            success = db_manager.update_user_profile(user_id, avatar_url=avatar_url)
            
            if success:
                return jsonify({
                    'success': True,
                    'avatar_url': avatar_url
                })
            else:
                return jsonify({'error': 'Error al guardar avatar'}), 500
        else:
            return jsonify({'error': 'Formato de archivo no permitido'}), 400
            
    except Exception as e:
        logger.error(f"Error uploading avatar: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


# ============================================================
# ENDPOINTS DE SEGUIR/DEJAR DE SEGUIR
# ============================================================

@user_bp.route('/users/<user_id>/follow', methods=['POST'])
@require_telegram_user
def follow_user(user_id):
    """Seguir a un usuario."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        follower = request.telegram_user
        follower_id = str(follower.get('id'))
        
        if follower_id == user_id:
            return jsonify({'error': 'No puedes seguirte a ti mismo'}), 400
        
        db_manager.get_or_create_user(
            user_id=follower_id,
            username=follower.get('username'),
            first_name=follower.get('first_name'),
            last_name=follower.get('last_name'),
            telegram_id=follower.get('id')
        )
        
        success = db_manager.follow_user(follower_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Ahora sigues a este usuario'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Ya sigues a este usuario'
            })
            
    except Exception as e:
        logger.error(f"Error following user {user_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@user_bp.route('/users/<user_id>/follow', methods=['DELETE'])
@require_telegram_user
def unfollow_user(user_id):
    """Dejar de seguir a un usuario."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        follower = request.telegram_user
        follower_id = str(follower.get('id'))
        
        success = db_manager.unfollow_user(follower_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Has dejado de seguir a este usuario'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No seguias a este usuario'
            })
            
    except Exception as e:
        logger.error(f"Error unfollowing user {user_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@user_bp.route('/users/<user_id>/followers', methods=['GET'])
@require_telegram_user
def get_user_followers(user_id):
    """Obtener lista de seguidores de un usuario."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        limit = min(limit, 100)
        
        followers = db_manager.get_followers(user_id, limit=limit, offset=offset)
        
        result = []
        for follower in followers:
            result.append({
                'id': follower.get('id'),
                'username': follower.get('username'),
                'firstName': follower.get('first_name'),
                'lastName': follower.get('last_name'),
                'avatarUrl': follower.get('avatar_url'),
                'bio': follower.get('bio'),
                'isVerified': follower.get('is_verified', False),
                'followedAt': follower.get('followed_at').isoformat() if follower.get('followed_at') else None
            })
        
        return jsonify({
            'success': True,
            'followers': result,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting followers for {user_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@user_bp.route('/users/<user_id>/following', methods=['GET'])
@require_telegram_user
def get_user_following(user_id):
    """Obtener lista de usuarios que sigue."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        limit = min(limit, 100)
        
        following = db_manager.get_following(user_id, limit=limit, offset=offset)
        
        result = []
        for user in following:
            result.append({
                'id': user.get('id'),
                'username': user.get('username'),
                'firstName': user.get('first_name'),
                'lastName': user.get('last_name'),
                'avatarUrl': user.get('avatar_url'),
                'bio': user.get('bio'),
                'isVerified': user.get('is_verified', False),
                'followedAt': user.get('followed_at').isoformat() if user.get('followed_at') else None
            })
        
        return jsonify({
            'success': True,
            'following': result,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting following for {user_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@user_bp.route('/users/<user_id>/stats', methods=['GET'])
@require_telegram_user
def get_user_stats(user_id):
    """Obtener estadisticas del perfil de un usuario."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        posts_count = db_manager.count_user_publications(user_id)
        followers = db_manager.get_followers(user_id, limit=1000)
        following = db_manager.get_following(user_id, limit=1000)
        
        return jsonify({
            'success': True,
            'stats': {
                'posts': posts_count,
                'followers': len(followers) if followers else 0,
                'following': len(following) if following else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user stats for {user_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


# ============================================================
# ENDPOINTS DE MENSAJES PRIVADOS
# ============================================================

@user_bp.route('/messages', methods=['POST'])
@require_telegram_auth
def send_private_message():
    """Enviar un mensaje privado a otro usuario."""
    try:
        db_manager = get_db_manager()
        sender_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        receiver_id = str(data.get('receiver_id', '')).strip()
        content = str(data.get('content', '')).strip()
        
        if not receiver_id or not content:
            return jsonify({'success': False, 'error': 'Receptor y contenido son requeridos'}), 400
        
        if len(content) > 2000:
            return jsonify({'success': False, 'error': 'Mensaje muy largo (max 2000 caracteres)'}), 400
        
        if sender_id == receiver_id:
            return jsonify({'success': False, 'error': 'No puedes enviarte mensajes a ti mismo'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        sanitized_content = html.escape(content)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id, username FROM users WHERE id = %s", (receiver_id,))
                receiver = cur.fetchone()
                if not receiver:
                    return jsonify({'success': False, 'error': 'Usuario receptor no encontrado'}), 404
                
                cur.execute("""
                    INSERT INTO private_messages (sender_id, receiver_id, content)
                    VALUES (%s, %s, %s)
                    RETURNING id, created_at
                """, (sender_id, receiver_id, sanitized_content))
                message = cur.fetchone()
                conn.commit()
        
        logger.info(f"Private message sent from {sender_id} to {receiver_id}")
        
        return jsonify({
            'success': True,
            'message': {
                'id': message['id'],
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'content': sanitized_content,
                'created_at': message['created_at'].isoformat() if message.get('created_at') else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error sending private message: {e}")
        return jsonify({'success': False, 'error': 'Error al enviar mensaje'}), 500


@user_bp.route('/messages/conversations', methods=['GET'])
@require_telegram_auth
def get_conversations():
    """Obtener lista de conversaciones del usuario."""
    try:
        db_manager = get_db_manager()
        user_id = str(request.telegram_user.get('id', 0))
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    WITH conversations AS (
                        SELECT 
                            CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END as other_user_id,
                            MAX(created_at) as last_message_at,
                            COUNT(*) FILTER (WHERE receiver_id = %s AND is_read = false) as unread_count
                        FROM private_messages
                        WHERE sender_id = %s OR receiver_id = %s
                        GROUP BY CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END
                    )
                    SELECT 
                        c.other_user_id,
                        c.last_message_at,
                        c.unread_count,
                        u.username,
                        u.avatar_url,
                        (SELECT content FROM private_messages pm 
                         WHERE (pm.sender_id = %s AND pm.receiver_id = c.other_user_id)
                            OR (pm.sender_id = c.other_user_id AND pm.receiver_id = %s)
                         ORDER BY pm.created_at DESC LIMIT 1) as last_message
                    FROM conversations c
                    JOIN users u ON c.other_user_id = u.id
                    ORDER BY c.last_message_at DESC
                    LIMIT 50
                """, (user_id, user_id, user_id, user_id, user_id, user_id, user_id))
                
                conversations = []
                for row in cur.fetchall():
                    conv = dict(row)
                    if conv.get('last_message_at'):
                        conv['last_message_at'] = conv['last_message_at'].isoformat()
                    conversations.append(conv)
        
        return jsonify({'success': True, 'conversations': conversations})
        
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/messages/<other_user_id>', methods=['GET'])
@require_telegram_auth
def get_messages_with_user(other_user_id):
    """Obtener mensajes con un usuario especifico."""
    try:
        db_manager = get_db_manager()
        user_id = str(request.telegram_user.get('id', 0))
        limit = min(int(request.args.get('limit', 50)), 100)
        before_id = request.args.get('before_id', None)
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT pm.*, 
                        s.username as sender_username,
                        r.username as receiver_username
                    FROM private_messages pm
                    LEFT JOIN users s ON pm.sender_id = s.id
                    LEFT JOIN users r ON pm.receiver_id = r.id
                    WHERE ((pm.sender_id = %s AND pm.receiver_id = %s) 
                        OR (pm.sender_id = %s AND pm.receiver_id = %s))
                """
                params = [user_id, other_user_id, other_user_id, user_id]
                
                if before_id:
                    query += " AND pm.id < %s"
                    params.append(before_id)
                
                query += " ORDER BY pm.created_at DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                messages = []
                for row in cur.fetchall():
                    msg = dict(row)
                    if msg.get('created_at'):
                        msg['created_at'] = msg['created_at'].isoformat()
                    if msg.get('read_at'):
                        msg['read_at'] = msg['read_at'].isoformat()
                    messages.append(msg)
                
                cur.execute("""
                    UPDATE private_messages
                    SET is_read = true, read_at = NOW()
                    WHERE receiver_id = %s AND sender_id = %s AND is_read = false
                """, (user_id, other_user_id))
                conn.commit()
        
        return jsonify({
            'success': True,
            'messages': messages[::-1],
            'count': len(messages)
        })
        
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/messages/<int:message_id>/read', methods=['POST'])
@require_telegram_auth
def mark_message_read(message_id):
    """Marcar un mensaje como leido."""
    try:
        db_manager = get_db_manager()
        user_id = str(request.telegram_user.get('id', 0))
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE private_messages
                    SET is_read = true, read_at = NOW()
                    WHERE id = %s AND receiver_id = %s AND is_read = false
                """, (message_id, user_id))
                updated = cur.rowcount
                conn.commit()
        
        return jsonify({'success': True, 'updated': updated > 0})
        
    except Exception as e:
        logger.error(f"Error marking message as read: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/messages/unread-count', methods=['GET'])
@require_telegram_auth
def get_unread_messages_count():
    """Obtener cantidad de mensajes no leidos."""
    try:
        db_manager = get_db_manager()
        user_id = str(request.telegram_user.get('id', 0))
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM private_messages
                    WHERE receiver_id = %s AND is_read = false
                """, (user_id,))
                count = cur.fetchone()[0] or 0
        
        return jsonify({'success': True, 'unread_count': count})
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ENDPOINTS DE NOTIFICACIONES DE USUARIO
# ============================================================

@user_bp.route('/user/notifications', methods=['GET'])
@require_telegram_auth
def get_user_notifications():
    """Get notifications for logged in user"""
    try:
        db_manager = get_db_manager()
        user_id = request.telegram_user.get('id')
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM user_notifications
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 50
                """, (user_id,))
                notifications = cur.fetchall()
                
                cur.execute("""
                    SELECT COUNT(*) as unread FROM user_notifications
                    WHERE user_id = %s AND is_read = false
                """, (user_id,))
                unread_count = cur.fetchone()['unread']
                
                return jsonify({
                    'success': True,
                    'notifications': [dict(n) for n in notifications],
                    'unread_count': unread_count
                })
                
    except Exception as e:
        logger.error(f"Error getting user notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/user/notifications/read', methods=['POST'])
@require_telegram_auth
def mark_notifications_read():
    """Mark notifications as read"""
    try:
        db_manager = get_db_manager()
        user_id = request.telegram_user.get('id')
        data = request.json or {}
        notification_ids = data.get('notification_ids', [])
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                if notification_ids:
                    cur.execute("""
                        UPDATE user_notifications
                        SET is_read = true
                        WHERE user_id = %s AND id = ANY(%s)
                    """, (user_id, notification_ids))
                else:
                    cur.execute("""
                        UPDATE user_notifications
                        SET is_read = true
                        WHERE user_id = %s
                    """, (user_id,))
                conn.commit()
                
                return jsonify({'success': True})
                
    except Exception as e:
        logger.error(f"Error marking notifications read: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ENDPOINTS DE POSTS - MIGRADO 10 Diciembre 2025
# ============================================================

@user_bp.route('/posts', methods=['POST'])
@require_telegram_user
@rate_limit('posts_create')
def create_post():
    """Crear una nueva publicacion."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        data = request.get_json()
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        content_type = data.get('contentType', 'text')
        if content_type not in ['text', 'image', 'video']:
            return jsonify({'error': 'Tipo de contenido invalido'}), 400
        
        content_url = data.get('contentUrl')
        caption = html.escape(data.get('caption', ''))[:2000] if data.get('caption') else ''
        
        if content_type == 'text' and not caption:
            return jsonify({'error': 'El texto es requerido para posts de tipo texto'}), 400
        
        if content_type in ['image', 'video'] and not content_url:
            return jsonify({'error': 'La URL del contenido es requerida'}), 400
        
        db_manager.get_or_create_user(
            user_id=user_id,
            username=user.get('username', ''),
            first_name=user.get('first_name', ''),
            last_name=user.get('last_name', ''),
            telegram_id=user.get('id')
        )
        
        post_id = db_manager.create_post(
            user_id=user_id,
            content_type=content_type,
            content_url=content_url,
            caption=caption
        )
        
        if post_id:
            return jsonify({
                'success': True,
                'message': 'Publicacion creada correctamente',
                'postId': post_id
            })
        else:
            return jsonify({'error': 'Error al crear la publicacion'}), 500
            
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        return jsonify({'error': sanitize_error(e, 'create_post')}), 500


@user_bp.route('/posts', methods=['GET'])
@require_telegram_user
def get_posts_feed():
    """Obtener feed de publicaciones."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        limit = min(limit, 50)
        
        posts = db_manager.get_posts_feed(user_id=user_id, limit=limit, offset=offset)
        
        result = []
        for post in posts:
            result.append({
                'id': post.get('id'),
                'userId': post.get('user_id'),
                'username': post.get('username'),
                'firstName': post.get('first_name'),
                'avatarUrl': post.get('avatar_url'),
                'contentType': post.get('content_type'),
                'contentUrl': post.get('content_url'),
                'caption': post.get('caption'),
                'likesCount': post.get('likes_count', 0),
                'commentsCount': post.get('comments_count', 0),
                'sharesCount': post.get('shares_count', 0),
                'userLiked': post.get('user_liked', False),
                'createdAt': post.get('created_at').isoformat() if post.get('created_at') else None
            })
        
        return jsonify({
            'success': True,
            'posts': result,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting posts feed: {e}")
        return jsonify({'error': sanitize_error(e, 'get_posts_feed')}), 500


@user_bp.route('/posts/<int:post_id>', methods=['GET'])
@require_telegram_user
def get_post_detail(post_id):
    """Obtener detalles de una publicacion."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        post = db_manager.get_post(post_id)
        
        if not post:
            return jsonify({'error': 'Publicacion no encontrada'}), 404
        
        return jsonify({
            'success': True,
            'post': {
                'id': post.get('id'),
                'userId': post.get('user_id'),
                'username': post.get('username'),
                'firstName': post.get('first_name'),
                'avatarUrl': post.get('avatar_url'),
                'contentType': post.get('content_type'),
                'contentUrl': post.get('content_url'),
                'caption': post.get('caption'),
                'likesCount': post.get('likes_count', 0),
                'commentsCount': post.get('comments_count', 0),
                'sharesCount': post.get('shares_count', 0),
                'createdAt': post.get('created_at').isoformat() if post.get('created_at') else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting post {post_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@user_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@require_telegram_user
def delete_post(post_id):
    """Eliminar una publicacion."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        success = db_manager.delete_post(post_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Publicacion eliminada correctamente'
            })
        else:
            return jsonify({'error': 'No se pudo eliminar la publicacion'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting post {post_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@user_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@require_telegram_user
@rate_limit('posts_like')
def like_post(post_id):
    """Dar like a una publicacion."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        result = db_manager.like_post(post_id, user_id)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Like agregado' if result.get('message') == 'liked' else 'Ya habias dado like'
            })
        elif result.get('error') == 'post_not_found':
            return jsonify({'error': 'Publicacion no encontrada'}), 404
        else:
            return jsonify({'error': 'Error al agregar like'}), 500
            
    except Exception as e:
        logger.error(f"Error liking post {post_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


@user_bp.route('/posts/<int:post_id>/like', methods=['DELETE'])
@require_telegram_user
def unlike_post(post_id):
    """Quitar like de una publicacion."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user = request.telegram_user
        user_id = str(user.get('id'))
        
        result = db_manager.unlike_post(post_id, user_id)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Like removido' if result.get('message') == 'unliked' else 'No habias dado like'
            })
        elif result.get('error') == 'post_not_found':
            return jsonify({'error': 'Publicacion no encontrada'}), 404
        else:
            return jsonify({'error': 'Error al quitar like'}), 500
            
    except Exception as e:
        logger.error(f"Error unliking post {post_id}: {e}")
        return jsonify({'error': sanitize_error(e, 'api_error')}), 500


# ============================================================
# ENDPOINTS DE PUBLICATIONS - MIGRADO 10 Diciembre 2025
# ============================================================

@user_bp.route('/publications/feed', methods=['GET'])
@require_telegram_auth
def get_publications_feed():
    """Get user's feed with decrypted content for viewing"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        posts = db_manager.get_feed_posts(user_id, limit, offset)
        
        for post in posts:
            if not post.get('avatar_url') and post.get('user_id'):
                avatar_data = db_manager.get_user_avatar_data(str(post.get('user_id')))
                if avatar_data:
                    post['avatar_url'] = f"/api/avatar/{post.get('user_id')}"
        
        return jsonify({
            'success': True,
            'posts': posts,
            'has_more': len(posts) == limit
        })
        
    except Exception as e:
        logger.error(f"Error getting feed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/publications/check-new', methods=['GET'])
@require_telegram_auth
def check_new_publications():
    """Check for new publications since last check"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        last_id = request.args.get('last_id', 0, type=int)
        
        count = db_manager.count_new_posts(user_id, last_id)
        
        return jsonify({
            'success': True,
            'new_count': count
        })
        
    except Exception as e:
        logger.error(f"Error checking new publications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/publications/<int:post_id>', methods=['GET'])
@require_telegram_auth
def get_publication_detail(post_id):
    """Get a single publication with full details"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        viewer_id = str(request.telegram_user.get('id', 0))
        post = db_manager.get_post_detail(post_id, viewer_id)
        
        if not post:
            return jsonify({'success': False, 'error': 'Publicacion no encontrada'}), 404
        
        return jsonify({
            'success': True,
            'post': post
        })
        
    except Exception as e:
        logger.error(f"Error getting publication: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/publications/<int:post_id>', methods=['PUT'])
@require_telegram_auth
def update_publication(post_id):
    """Update a publication (caption, comments enabled)"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        
        success = db_manager.update_post(
            post_id=post_id,
            user_id=user_id,
            caption=data.get('caption'),
            comments_enabled=data.get('comments_enabled')
        )
        
        if not success:
            return jsonify({'success': False, 'error': 'No se pudo actualizar'}), 400
        
        return jsonify({
            'success': True,
            'message': 'Publicacion actualizada'
        })
        
    except Exception as e:
        logger.error(f"Error updating publication: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/publications/<int:post_id>', methods=['DELETE'])
@require_telegram_auth
def delete_publication(post_id):
    """Delete a publication"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.delete_post(post_id, user_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'No se pudo eliminar'}), 400
        
        return jsonify({
            'success': True,
            'message': 'Publicacion eliminada'
        })
        
    except Exception as e:
        logger.error(f"Error deleting publication: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/publications/gallery/<user_id>', methods=['GET'])
@require_telegram_auth
def get_user_gallery(user_id):
    """Get user's gallery (grid of posts)"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        viewer_id = str(request.telegram_user.get('id', 0))
        limit = int(request.args.get('limit', 30))
        offset = int(request.args.get('offset', 0))
        
        posts = db_manager.get_user_gallery(user_id, viewer_id, limit, offset)
        
        return jsonify({
            'success': True,
            'posts': posts,
            'has_more': len(posts) == limit
        })
        
    except Exception as e:
        logger.error(f"Error getting gallery: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/publications/<int:post_id>/react', methods=['POST'])
@require_telegram_auth
def react_to_post(post_id):
    """Add or change reaction to a post"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        reaction_type = data.get('reaction', 'like')
        
        success = db_manager.add_reaction(user_id, post_id, reaction_type)
        
        return jsonify({
            'success': success,
            'reaction': reaction_type
        })
        
    except Exception as e:
        logger.error(f"Error reacting to post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/publications/<int:post_id>/unreact', methods=['POST'])
@require_telegram_auth
def unreact_to_post(post_id):
    """Remove reaction from a post"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.remove_reaction(user_id, post_id)
        
        return jsonify({
            'success': success
        })
        
    except Exception as e:
        logger.error(f"Error unreacting to post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/publications/<int:post_id>/save', methods=['POST'])
@require_telegram_auth
def save_publication(post_id):
    """Save a post to favorites"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.save_post(user_id, post_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error saving post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/publications/<int:post_id>/unsave', methods=['POST'])
@require_telegram_auth
def unsave_publication(post_id):
    """Remove post from favorites"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.unsave_post(user_id, post_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error unsaving post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/publications/saved', methods=['GET'])
@require_telegram_auth
def get_saved_publications():
    """Get user's saved posts"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        limit = int(request.args.get('limit', 30))
        offset = int(request.args.get('offset', 0))
        
        posts = db_manager.get_saved_posts(user_id, limit, offset)
        
        return jsonify({
            'success': True,
            'posts': posts,
            'has_more': len(posts) == limit
        })
        
    except Exception as e:
        logger.error(f"Error getting saved posts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/publications/<int:post_id>/share', methods=['POST'])
@require_telegram_auth
def share_publication(post_id):
    """Share/repost a publication"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        share_type = data.get('type', 'repost')
        quote_text = data.get('quote')
        recipient_id = data.get('recipient_id')
        
        share_id = db_manager.share_post(user_id, post_id, share_type, quote_text, recipient_id)
        
        return jsonify({
            'success': share_id is not None,
            'share_id': share_id
        })
        
    except Exception as e:
        logger.error(f"Error sharing post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/publications/<int:post_id>/share-count', methods=['POST'])
@require_telegram_auth
def increment_publication_share_count(post_id):
    """Increment share count for external shares (copy link, Telegram share)"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        db_manager.increment_share_count(post_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error incrementing share count: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ENDPOINTS DE COMENTARIOS - MIGRADO 10 Diciembre 2025
# ============================================================

@user_bp.route('/publications/<int:post_id>/comments', methods=['GET'])
@require_telegram_auth
def get_post_comments(post_id):
    """Get comments for a post"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        comments = db_manager.get_post_comments(post_id, limit, offset)
        
        return jsonify({
            'success': True,
            'comments': comments
        })
        
    except Exception as e:
        logger.error(f"Error getting comments: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/publications/<int:post_id>/comments', methods=['POST'])
@require_telegram_auth
@rate_limit('comments_create')
def add_comment(post_id):
    """Add a comment to a post"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')
        
        if not content:
            return jsonify({'success': False, 'error': 'Contenido requerido'}), 400
        
        content = html.escape(content)[:2000]
        
        comment_id = db_manager.add_comment(user_id, post_id, content, parent_id)
        
        if comment_id:
            db_manager.process_mentions(post_id, content, 'comment')
        
        return jsonify({
            'success': comment_id is not None,
            'comment_id': comment_id
        })
        
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/publications/<int:post_id>/pin-comment', methods=['POST'])
@require_telegram_auth
def pin_comment(post_id):
    """Pin a comment (post owner only)"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        comment_id = data.get('comment_id')
        
        if not comment_id:
            return jsonify({'success': False, 'error': 'ID de comentario requerido'}), 400
        
        success = db_manager.pin_comment(user_id, post_id, comment_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error pinning comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/comments/<int:comment_id>/like', methods=['POST'])
@require_telegram_auth
def like_comment(comment_id):
    """Like a comment"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.like_comment(user_id, comment_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error liking comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/comments/<int:comment_id>/unlike', methods=['POST'])
@require_telegram_auth
def unlike_comment(comment_id):
    """Unlike a comment"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        
        success = db_manager.unlike_comment(user_id, comment_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error unliking comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@require_telegram_auth
@rate_limit('comments_create')
def update_comment(comment_id):
    """Update a comment - only author can edit within time limit"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'error': 'Contenido requerido'}), 400
        
        if len(content) > 2000:
            return jsonify({'success': False, 'error': 'Comentario muy largo (maximo 2000 caracteres)'}), 400
        
        content = html.escape(content)
        
        result = db_manager.update_comment(user_id, comment_id, content)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error updating comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/comments/<int:comment_id>', methods=['GET'])
@require_telegram_auth
def get_comment(comment_id):
    """Get a single comment by ID"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        comment = db_manager.get_comment_by_id(comment_id)
        
        if comment:
            return jsonify({'success': True, 'comment': comment})
        else:
            return jsonify({'success': False, 'error': 'Comentario no encontrado'}), 404
        
    except Exception as e:
        logger.error(f"Error getting comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/comments/<int:comment_id>/react', methods=['POST'])
@require_telegram_auth
def add_comment_reaction(comment_id):
    """Add or update reaction to a comment"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        reaction_type = data.get('reaction_type', '').strip()
        
        if not reaction_type:
            return jsonify({'success': False, 'error': 'Tipo de reaccion requerido'}), 400
        
        result = db_manager.add_comment_reaction(user_id, comment_id, reaction_type)
        
        if result.get('success'):
            reactions = db_manager.get_comment_reactions(comment_id)
            return jsonify({
                'success': True,
                'reactions': reactions.get('reactions', {}),
                'total': reactions.get('total', 0),
                'user_reaction': reaction_type
            })
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error adding comment reaction: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/comments/<int:comment_id>/react', methods=['DELETE'])
@require_telegram_auth
def remove_comment_reaction(comment_id):
    """Remove reaction from a comment"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        
        result = db_manager.remove_comment_reaction(user_id, comment_id)
        
        if result.get('success'):
            reactions = db_manager.get_comment_reactions(comment_id)
            return jsonify({
                'success': True,
                'reactions': reactions.get('reactions', {}),
                'total': reactions.get('total', 0),
                'user_reaction': None
            })
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error removing comment reaction: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/comments/<int:comment_id>/reactions', methods=['GET'])
@require_telegram_auth
def get_comment_reactions_api(comment_id):
    """Get reactions for a comment"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        
        reactions = db_manager.get_comment_reactions(comment_id)
        user_reaction = db_manager.get_user_comment_reaction(user_id, comment_id)
        
        return jsonify({
            'success': True,
            'reactions': reactions.get('reactions', {}),
            'total': reactions.get('total', 0),
            'user_reaction': user_reaction
        })
        
    except Exception as e:
        logger.error(f"Error getting comment reactions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ENDPOINTS DE DISPOSITIVOS DE CONFIANZA
# Migrado desde app.py - 10 Diciembre 2025
# ============================================================

@user_bp.route('/devices/trusted', methods=['GET'])
@require_telegram_user
def get_trusted_devices():
    """Obtener lista de dispositivos de confianza del usuario."""
    try:
        db_manager = get_db_manager()
        user_id = str(request.telegram_user.get('id', 0))
        
        if not db_manager:
            return jsonify({'success': True, 'devices': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, device_id, device_name, device_type, created_at, last_used_at, is_active
                    FROM trusted_devices 
                    WHERE user_id = %s AND is_active = TRUE
                    ORDER BY last_used_at DESC
                """, (user_id,))
                rows = cur.fetchall()
                devices = []
                for row in rows:
                    devices.append({
                        'id': row[0],
                        'deviceId': row[1],
                        'deviceName': row[2],
                        'deviceType': row[3],
                        'createdAt': row[4].isoformat() if row[4] else None,
                        'lastUsedAt': row[5].isoformat() if row[5] else None,
                        'isActive': row[6]
                    })
                    
        return jsonify({'success': True, 'devices': devices})
        
    except Exception as e:
        logger.error(f"Error getting trusted devices: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener dispositivos'}), 500


@user_bp.route('/devices/trusted/check', methods=['POST'])
@require_telegram_user
def check_trusted_device():
    """Verificar si el dispositivo actual es de confianza."""
    try:
        db_manager = get_db_manager()
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        device_id = data.get('deviceId', '')
        
        if not device_id or not db_manager:
            return jsonify({'success': True, 'isTrusted': False})
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, device_name FROM trusted_devices 
                    WHERE user_id = %s AND device_id = %s AND is_active = TRUE
                """, (user_id, device_id))
                result = cur.fetchone()
                
                if result:
                    cur.execute("""
                        UPDATE trusted_devices SET last_used_at = NOW()
                        WHERE id = %s
                    """, (result[0],))
                    conn.commit()
                    return jsonify({
                        'success': True, 
                        'isTrusted': True,
                        'deviceName': result[1]
                    })
                    
        return jsonify({'success': True, 'isTrusted': False})
        
    except Exception as e:
        logger.error(f"Error checking trusted device: {e}")
        return jsonify({'success': True, 'isTrusted': False})


@user_bp.route('/devices/trusted/add', methods=['POST'])
@require_telegram_user
def add_trusted_device():
    """Agregar un dispositivo de confianza."""
    try:
        db_manager = get_db_manager()
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        device_id = data.get('deviceId', '')
        device_name = data.get('deviceName', 'Dispositivo desconocido')
        device_type = data.get('deviceType', 'unknown')
        user_agent = request.headers.get('User-Agent', '')[:500]
        ip_address = request.remote_addr or ''
        
        if not device_id:
            return jsonify({'success': False, 'error': 'ID de dispositivo requerido'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO trusted_devices (user_id, device_id, device_name, device_type, user_agent, ip_address)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, device_id) 
                    DO UPDATE SET 
                        device_name = EXCLUDED.device_name,
                        is_active = TRUE,
                        last_used_at = NOW()
                    RETURNING id
                """, (user_id, device_id, device_name, device_type, user_agent, ip_address))
                result = cur.fetchone()
                conn.commit()
                
        logger.info(f"Dispositivo de confianza agregado para usuario {user_id}: {device_name}")
        return jsonify({'success': True, 'message': 'Dispositivo agregado correctamente', 'deviceId': result[0] if result else None})
        
    except Exception as e:
        logger.error(f"Error adding trusted device: {e}")
        return jsonify({'success': False, 'error': 'Error al agregar dispositivo'}), 500


@user_bp.route('/devices/trusted/remove', methods=['POST'])
@require_telegram_user
def remove_trusted_device():
    """Eliminar un dispositivo de confianza."""
    try:
        from tracking.services import get_security_manager
        
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        device_id = data.get('deviceId', '')
        
        if not device_id:
            return jsonify({'success': False, 'error': 'ID de dispositivo requerido'}), 400
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        result = security_manager.remove_trusted_device(user_id, device_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error removing trusted device: {e}")
        return jsonify({'success': False, 'error': 'Error al eliminar dispositivo'}), 500


# ============================================================
# ENDPOINTS DE SEGURIDAD - WALLET Y DISPOSITIVOS
# Migrado desde app.py - 10 Diciembre 2025
# ============================================================


@user_bp.route('/security/wallet/validate', methods=['POST'])
@require_telegram_user
def validate_wallet_security():
    """Validar que la wallet conectada es la registrada del usuario."""
    try:
        from tracking.services import get_security_manager
        
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        wallet_address = data.get('walletAddress', '')
        device_id = data.get('deviceId', '')
        
        if not wallet_address:
            return jsonify({'success': False, 'error': 'Direccion de wallet requerida'}), 400
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': True, 'message': 'Demo mode'})
        
        ip_address = request.remote_addr or ''
        result = security_manager.validate_wallet_connection(user_id, wallet_address, device_id, ip_address)
        
        if result.get('is_locked'):
            return jsonify(result), 423
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error validating wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/security/wallet/primary', methods=['GET'])
@require_telegram_user
def get_primary_wallet():
    """Obtener la wallet primaria registrada del usuario."""
    try:
        from tracking.services import get_security_manager
        
        user_id = str(request.telegram_user.get('id', 0))
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': True, 'wallet': None})
        
        wallet = security_manager.get_user_primary_wallet(user_id)
        return jsonify({
            'success': True,
            'hasWallet': wallet is not None,
            'walletHint': f"{wallet[:8]}...{wallet[-4:]}" if wallet else None
        })
        
    except Exception as e:
        logger.error(f"Error getting primary wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/security/wallet/backup', methods=['POST'])
@require_telegram_user
def register_backup_wallet():
    """Registrar una wallet de respaldo para emergencias."""
    try:
        from tracking.services import get_security_manager
        
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        backup_wallet = data.get('backupWallet', '')
        
        is_valid, error_msg = validate_ton_address(backup_wallet)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        result = security_manager.register_backup_wallet(user_id, backup_wallet.strip())
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error registering backup wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/security/wallet/primary/check', methods=['GET'])
@require_telegram_user
def check_primary_wallet():
    """Verificar si el usuario ya tiene wallet primaria registrada."""
    try:
        from tracking.services import get_security_manager
        
        user_id = str(request.telegram_user.get('id', 0))
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': True, 'hasPrimaryWallet': False})
        
        wallet = security_manager.get_user_primary_wallet(user_id)
        return jsonify({
            'success': True,
            'hasPrimaryWallet': wallet is not None,
            'walletHint': f"{wallet[:8]}...{wallet[-4:]}" if wallet else None
        })
        
    except Exception as e:
        logger.error(f"Error checking primary wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/security/wallet/primary/register', methods=['POST'])
@require_telegram_user
def register_primary_wallet_endpoint():
    """Registrar wallet como primaria (solo si no tiene una)."""
    try:
        from tracking.services import get_security_manager
        
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        wallet_address = data.get('walletAddress', '')
        
        is_valid, error_msg = validate_ton_address(wallet_address)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        result = security_manager.register_primary_wallet(user_id, wallet_address.strip())
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error registering primary wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/wallet/debit', methods=['POST'])
@require_telegram_user
def debit_wallet():
    """Realizar un debito de BUNK3RCO1N."""
    try:
        from tracking.services import get_security_manager
        
        db_manager = get_db_manager()
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        
        amount = data.get('amount', 0)
        transaction_type = data.get('type', 'purchase')
        description = data.get('description', 'Gasto')
        reference_id = data.get('reference_id', '')
        
        if not amount or amount <= 0:
            return jsonify({'success': False, 'error': 'Cantidad invalida'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as balance
                    FROM wallet_transactions
                    WHERE user_id = %s
                """, (user_id,))
                result = cur.fetchone()
                current_balance = float(result[0]) if result else 0
                
                if current_balance < amount:
                    return jsonify({
                        'success': False,
                        'error': 'insufficient_balance',
                        'message': 'Saldo insuficiente',
                        'currentBalance': current_balance,
                        'required': amount
                    }), 402
                
                cur.execute("""
                    INSERT INTO wallet_transactions 
                    (user_id, amount, transaction_type, description, reference_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (user_id, -amount, transaction_type, description, reference_id))
                conn.commit()
                
                new_balance = current_balance - amount
        
        db_manager.create_transaction_notification(
            user_id=user_id,
            amount=amount,
            transaction_type='debit',
            new_balance=new_balance
        )
        
        security_manager = get_security_manager()
        if amount > 100 and security_manager:
            security_manager.send_telegram_notification(
                user_id,
                f"💸 <b>Gasto registrado</b>\n\n"
                f"📦 {description}\n"
                f"💰 -{amount} BUNK3RCO1N\n"
                f"📊 Saldo restante: {new_balance:.2f} B3C"
            )
        
        logger.info(f"Debito de {amount} B3C para usuario {user_id}: {description}")
        return jsonify({
            'success': True,
            'newBalance': new_balance,
            'amountDebited': amount
        })
        
    except Exception as e:
        logger.error(f"Error debiting wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/security/status', methods=['GET'])
@require_telegram_user
def get_security_status():
    """Obtener estado de seguridad completo del usuario."""
    try:
        from tracking.services import get_security_manager
        
        user_id = str(request.telegram_user.get('id', 0))
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({
                'success': True,
                'wallet_connected': False,
                'two_factor_enabled': False,
                'trusted_devices_count': 0,
                'max_devices': 2,
                'security_score': 0,
                'security_level': 'bajo'
            })
        
        status = security_manager.get_security_status(user_id)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting security status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/security/devices', methods=['GET'])
@require_telegram_user
def get_security_devices():
    """Obtener lista de dispositivos de confianza con info completa."""
    try:
        from tracking.services import get_security_manager
        
        user_id = str(request.telegram_user.get('id', 0))
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': True, 'devices': [], 'count': 0, 'max': 2})
        
        devices = security_manager.get_trusted_devices(user_id)
        return jsonify({
            'success': True,
            'devices': devices,
            'count': len(devices),
            'max': security_manager.MAX_TRUSTED_DEVICES
        })
        
    except Exception as e:
        logger.error(f"Error getting security devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/security/devices/check', methods=['POST'])
@require_telegram_user
def check_device_trust():
    """Verificar si el dispositivo actual es de confianza."""
    try:
        from tracking.services import get_security_manager
        
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        device_id = data.get('deviceId', '')
        
        if not device_id:
            return jsonify({'success': True, 'isTrusted': False})
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': True, 'isTrusted': False})
        
        result = security_manager.is_device_trusted(user_id, device_id)
        return jsonify({
            'success': True,
            'isTrusted': result.get('is_trusted', False),
            'deviceName': result.get('device_name'),
            'deviceType': result.get('device_type'),
            'expired': result.get('expired', False)
        })
        
    except Exception as e:
        logger.error(f"Error checking device trust: {e}")
        return jsonify({'success': True, 'isTrusted': False})


@user_bp.route('/security/devices/add', methods=['POST'])
@require_telegram_user
def add_security_device():
    """Agregar un dispositivo de confianza (requiere wallet + 2FA)."""
    try:
        from tracking.services import get_security_manager
        
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        device_id = data.get('deviceId', '')
        device_name = data.get('deviceName', 'Dispositivo')
        device_type = data.get('deviceType', 'unknown')
        wallet_verified = data.get('walletVerified', False)
        twofa_verified = data.get('twofaVerified', False)
        
        if not device_id:
            return jsonify({'success': False, 'error': 'ID de dispositivo requerido'}), 400
        
        if not wallet_verified:
            return jsonify({'success': False, 'error': 'Debes conectar tu wallet primero', 'requiresWallet': True}), 400
        
        if not twofa_verified:
            return jsonify({'success': False, 'error': 'Debes verificar 2FA primero', 'requires2FA': True}), 400
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        user_agent = request.headers.get('User-Agent', '')[:500]
        ip_address = request.remote_addr or ''
        
        result = security_manager.add_trusted_device(
            user_id, device_id, device_name, device_type, user_agent, ip_address
        )
        
        if result.get('max_reached'):
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error adding security device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/security/devices/remove', methods=['POST'])
@require_telegram_user
def remove_security_device():
    """Eliminar un dispositivo de confianza (requiere 2FA)."""
    try:
        from tracking.services import get_security_manager
        import pyotp
        
        db_manager = get_db_manager()
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        device_id = data.get('deviceId', '')
        twofa_code = data.get('twofaCode', '')
        
        if not device_id:
            return jsonify({'success': False, 'error': 'ID de dispositivo requerido'}), 400
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        if db_manager:
            status = db_manager.get_user_2fa_status(user_id)
            if status['enabled']:
                if not twofa_code or len(twofa_code) != 6:
                    return jsonify({'success': False, 'error': 'Codigo 2FA requerido', 'requires2FA': True}), 400
                
                secret = db_manager.get_user_totp_secret(user_id)
                if secret:
                    totp = pyotp.TOTP(secret)
                    if not totp.verify(twofa_code, valid_window=1):
                        return jsonify({'success': False, 'error': 'Codigo 2FA incorrecto'}), 401
        
        result = security_manager.remove_trusted_device(user_id, device_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error removing security device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/security/devices/remove-all', methods=['POST'])
@require_telegram_user
def remove_all_devices():
    """Cerrar sesion en todos los dispositivos excepto el actual."""
    try:
        from tracking.services import get_security_manager
        import pyotp
        
        db_manager = get_db_manager()
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        current_device_id = data.get('currentDeviceId', '')
        twofa_code = data.get('twofaCode', '')
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        if db_manager:
            status = db_manager.get_user_2fa_status(user_id)
            if status['enabled']:
                if not twofa_code or len(twofa_code) != 6:
                    return jsonify({'success': False, 'error': 'Codigo 2FA requerido', 'requires2FA': True}), 400
                
                secret = db_manager.get_user_totp_secret(user_id)
                if secret:
                    totp = pyotp.TOTP(secret)
                    if not totp.verify(twofa_code, valid_window=1):
                        return jsonify({'success': False, 'error': 'Codigo 2FA incorrecto'}), 401
        
        result = security_manager.remove_all_devices_except_current(user_id, current_device_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error removing all devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/security/activity', methods=['GET'])
@require_telegram_user
def get_security_activity():
    """Obtener historial de actividad de seguridad."""
    try:
        from tracking.services import get_security_manager
        
        user_id = str(request.telegram_user.get('id', 0))
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 50)
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': True, 'activities': []})
        
        activities = security_manager.get_security_activity(user_id, limit)
        return jsonify({
            'success': True,
            'activities': activities
        })
        
    except Exception as e:
        logger.error(f"Error getting security activity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/security/lockout/check', methods=['GET'])
@require_telegram_user
def check_user_lockout():
    """Verificar si el usuario esta bloqueado."""
    try:
        from tracking.services import get_security_manager
        
        user_id = str(request.telegram_user.get('id', 0))
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': True, 'isLocked': False})
        
        is_locked = security_manager.is_user_locked_out(user_id, 'wallet_attempts')
        lockout_time = None
        if is_locked:
            lockout_time = security_manager.get_lockout_time(user_id, 'wallet_attempts')
        
        return jsonify({
            'success': True,
            'isLocked': is_locked,
            'lockedUntil': lockout_time.isoformat() if lockout_time else None
        })
        
    except Exception as e:
        logger.error(f"Error checking lockout: {e}")
        return jsonify({'success': True, 'isLocked': False})


# ============================================================
# STORIES ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================

@user_bp.route('/stories/create', methods=['POST'])
@require_telegram_user
def create_story():
    """Create a new story (24h expiry)"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Archivo requerido'}), 400
        
        file = request.files['file']
        file_data = file.read()
        
        try:
            from tracking.cloudinary_service import cloudinary_service
            upload_result = cloudinary_service.upload_story_media(
                file_data=file_data,
                content_type=file.content_type
            )
            
            if not upload_result['success']:
                return jsonify({'success': False, 'error': upload_result.get('error')}), 500
            
            story_id = db_manager.create_story(
                user_id=user_id,
                media_type=upload_result['resource_type'],
                media_url=upload_result['url'],
                encrypted_url=upload_result['url'],
                encryption_key=upload_result['encryption_key'],
                encryption_iv=upload_result['encryption_iv']
            )
            
            return jsonify({
                'success': story_id is not None,
                'story_id': story_id
            })
        except ImportError:
            return jsonify({'success': False, 'error': 'Cloudinary service not available'}), 500
        
    except Exception as e:
        logger.error(f"Error creating story: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/stories/feed', methods=['GET'])
@require_telegram_user
def get_stories_feed():
    """Get stories from followed users"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': True, 'stories': []})
        
        stories = db_manager.get_stories_feed(user_id)
        
        return jsonify({
            'success': True,
            'stories': stories
        })
        
    except Exception as e:
        logger.error(f"Error getting stories feed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/stories/user/<target_user_id>', methods=['GET'])
@require_telegram_user
def get_user_stories(target_user_id):
    """Get all stories from a specific user"""
    try:
        viewer_id = str(request.telegram_user.get('id', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': True, 'stories': []})
        
        stories = db_manager.get_user_stories(target_user_id, viewer_id)
        
        return jsonify({
            'success': True,
            'stories': stories
        })
        
    except Exception as e:
        logger.error(f"Error getting user stories: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/stories/<int:story_id>/view', methods=['POST'])
@require_telegram_user
def view_story(story_id):
    """Mark a story as viewed"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        success = db_manager.view_story(story_id, user_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error viewing story: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/stories/<int:story_id>/viewers', methods=['GET'])
@require_telegram_user
def get_story_viewers(story_id):
    """Get list of users who viewed a story (owner only)"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': True, 'viewers': []})
        
        viewers = db_manager.get_story_viewers(story_id, user_id)
        
        return jsonify({
            'success': True,
            'viewers': viewers
        })
        
    except Exception as e:
        logger.error(f"Error getting story viewers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/stories/<int:story_id>', methods=['DELETE'])
@require_telegram_user
def delete_story(story_id):
    """Delete a story (owner only)"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        success = db_manager.delete_story(story_id, user_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'No se pudo eliminar la historia'}), 400
        
        return jsonify({'success': True, 'message': 'Historia eliminada'})
        
    except Exception as e:
        logger.error(f"Error deleting story: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/stories/<int:story_id>/react', methods=['POST'])
@require_telegram_user
def react_to_story(story_id):
    """React to a story with an emoji"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        reaction = data.get('reaction', '❤️')
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        success = db_manager.react_to_story(story_id, user_id, reaction)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error reacting to story: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# EXPLORE & SEARCH ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================

@user_bp.route('/explore', methods=['GET'])
@require_telegram_user
def explore_posts():
    """Get trending/popular posts for explore page"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        limit = int(request.args.get('limit', 30))
        offset = int(request.args.get('offset', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': True, 'posts': [], 'has_more': False})
        
        posts = db_manager.get_explore_posts(user_id, limit, offset)
        
        return jsonify({
            'success': True,
            'posts': posts,
            'has_more': len(posts) == limit
        })
        
    except Exception as e:
        logger.error(f"Error getting explore posts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/search/posts', methods=['GET'])
@require_telegram_user
def search_posts():
    """Search posts by caption text"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 30))
        offset = int(request.args.get('offset', 0))
        db_manager = get_db_manager()
        
        if not query:
            return jsonify({'success': True, 'posts': []})
        
        if not db_manager:
            return jsonify({'success': True, 'posts': [], 'has_more': False})
        
        posts = db_manager.search_posts(query, user_id, limit, offset)
        
        return jsonify({
            'success': True,
            'posts': posts,
            'has_more': len(posts) == limit
        })
        
    except Exception as e:
        logger.error(f"Error searching posts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/search/users', methods=['GET'])
@require_telegram_user
def search_users():
    """Search users by username or name"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))
        db_manager = get_db_manager()
        
        if not query:
            return jsonify({'success': True, 'users': []})
        
        if not db_manager:
            return jsonify({'success': True, 'users': []})
        
        users = db_manager.search_users(query, user_id, limit)
        
        return jsonify({
            'success': True,
            'users': users
        })
        
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/hashtag/<hashtag>', methods=['GET'])
@require_telegram_user
def get_hashtag_posts(hashtag):
    """Get posts by hashtag"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        limit = int(request.args.get('limit', 30))
        offset = int(request.args.get('offset', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': True, 'hashtag': hashtag, 'posts': [], 'has_more': False})
        
        posts = db_manager.get_posts_by_hashtag(hashtag, user_id, limit, offset)
        
        return jsonify({
            'success': True,
            'hashtag': hashtag,
            'posts': posts,
            'has_more': len(posts) == limit
        })
        
    except Exception as e:
        logger.error(f"Error getting hashtag posts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/trending/hashtags', methods=['GET'])
@require_telegram_user
def get_trending_hashtags():
    """Get trending hashtags"""
    try:
        limit = int(request.args.get('limit', 10))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': True, 'hashtags': []})
        
        hashtags = db_manager.get_trending_hashtags(limit)
        
        return jsonify({
            'success': True,
            'hashtags': hashtags
        })
        
    except Exception as e:
        logger.error(f"Error getting trending hashtags: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/suggested/users', methods=['GET'])
@require_telegram_user
def get_suggested_users():
    """Get suggested users to follow"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        limit = int(request.args.get('limit', 10))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': True, 'users': []})
        
        users = db_manager.get_suggested_users(user_id, limit)
        
        return jsonify({
            'success': True,
            'users': users
        })
        
    except Exception as e:
        logger.error(f"Error getting suggested users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# NOTIFICATIONS ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================

@user_bp.route('/notifications', methods=['GET'])
@require_telegram_user
def get_notifications():
    """Get user notifications"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        filter_type = request.args.get('filter', 'all')
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': True, 'notifications': []})
        
        notifications = db_manager.get_notifications(
            user_id, limit, offset, unread_only, filter_type
        )
        
        return jsonify({
            'success': True,
            'notifications': notifications
        })
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/notifications/count', methods=['GET'])
@require_telegram_user
def get_notifications_count():
    """Get unread notifications count"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': True, 'count': 0})
        
        count = db_manager.get_unread_notifications_count(user_id)
        
        return jsonify({
            'success': True,
            'count': count
        })
        
    except Exception as e:
        logger.error(f"Error getting notifications count: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/notifications/read', methods=['POST'])
@require_telegram_user
def mark_notifications_read_api():
    """Mark notifications as read"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        notification_ids = data.get('ids')
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        success = db_manager.mark_notifications_read(user_id, notification_ids)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error marking notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/notifications/unread-count', methods=['GET'])
@require_telegram_user
def get_unread_notifications_count():
    """Get unread notifications count (alias)"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': True, 'count': 0})
        
        count = db_manager.get_unread_notifications_count(user_id)
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/notifications/mark-all-read', methods=['POST'])
@require_telegram_user
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        success = db_manager.mark_notifications_read(user_id, None)
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error marking all notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@require_telegram_user
def mark_single_notification_read(notification_id):
    """Mark single notification as read"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        success = db_manager.mark_notifications_read(user_id, [notification_id])
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error marking notification: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/notifications/preferences', methods=['GET'])
@require_telegram_user
def get_notification_preferences():
    """Get user notification preferences"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': True, 'preferences': {}})
        
        preferences = db_manager.get_notification_preferences(user_id)
        return jsonify({'success': True, 'preferences': preferences})
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/notifications/preferences', methods=['POST'])
@require_telegram_user
def update_notification_preferences():
    """Update user notification preferences"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        preferences = data.get('preferences', {})
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        valid_keys = ['likes', 'comments', 'follows', 'mentions', 'transactions', 'stories', 'push_enabled']
        clean_prefs = {k: bool(v) for k, v in preferences.items() if k in valid_keys}
        
        success = db_manager.update_notification_preferences(user_id, clean_prefs)
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# BLOCK & REPORT ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================

@user_bp.route('/users/<blocked_user_id>/block', methods=['POST'])
@require_telegram_user
def block_user(blocked_user_id):
    """Block a user"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        db_manager = get_db_manager()
        
        if user_id == blocked_user_id:
            return jsonify({'success': False, 'error': 'No puedes bloquearte a ti mismo'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        success = db_manager.block_user(user_id, blocked_user_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error blocking user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/users/<blocked_user_id>/unblock', methods=['POST'])
@require_telegram_user
def unblock_user(blocked_user_id):
    """Unblock a user"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        success = db_manager.unblock_user(user_id, blocked_user_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error unblocking user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/users/blocked', methods=['GET'])
@require_telegram_user
def get_blocked_users():
    """Get list of blocked users"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        db_manager = get_db_manager()
        
        if not db_manager:
            return jsonify({'success': True, 'blocked_users': []})
        
        blocked = db_manager.get_blocked_users(user_id)
        
        return jsonify({
            'success': True,
            'blocked_users': blocked
        })
        
    except Exception as e:
        logger.error(f"Error getting blocked users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/report', methods=['POST'])
@require_telegram_user
def create_report():
    """Create a content report"""
    try:
        user_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        db_manager = get_db_manager()
        
        content_type = data.get('content_type')
        content_id = data.get('content_id')
        reason = data.get('reason')
        description = data.get('description')
        
        if not all([content_type, content_id, reason]):
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        report_id = db_manager.create_report(
            user_id, content_type, content_id, reason, description
        )
        
        return jsonify({
            'success': report_id is not None,
            'report_id': report_id
        })
        
    except Exception as e:
        logger.error(f"Error creating report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# PUBLIC FAQ ENDPOINT (Migrado 10 Diciembre 2025 - Sesion 5)
# ============================================================


@user_bp.route('/faq', methods=['GET'])
def get_public_faqs():
    """Get published FAQs for users"""
    try:
        db_manager = get_db_manager()
        category = request.args.get('category', '')
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                where_clause = "is_published = true"
                params = []
                
                if category:
                    where_clause += " AND category = %s"
                    params.append(category)
                
                cur.execute(f"""
                    SELECT id, question, answer, category FROM faqs
                    WHERE {where_clause}
                    ORDER BY display_order ASC
                """, params)
                faqs = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'faqs': [dict(f) for f in faqs]
                })
                
    except Exception as e:
        logger.error(f"Error getting public FAQs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
