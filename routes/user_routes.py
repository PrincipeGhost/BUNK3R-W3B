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
from tracking.services import get_db_manager

logger = logging.getLogger(__name__)

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
            '/api/users/<id>/profile (GET)',
            '/api/users/<id>/profile (PUT)',
            '/api/users/<id>/posts',
            '/api/users/<id>/follow (POST)',
            '/api/users/<id>/follow (DELETE)',
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
            '/api/user/notifications/read'
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
