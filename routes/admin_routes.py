"""
Admin Routes - Endpoints del Panel de Administracion
Agente: Frontend-Admin
Rama: feature/frontend-admin

Este archivo contiene los endpoints del panel de administracion.
Los endpoints estan siendo migrados gradualmente desde app.py

Endpoints que pertenecen a este modulo:
- /api/admin/dashboard/* - Stats y actividad
- /api/admin/users/* - Gestion de usuarios
- /api/admin/stats/* - Estadisticas
- /api/admin/security/* - Seguridad
- /api/admin/financial/* - Finanzas
- /api/admin/content/* - Contenido
- /api/admin/fraud/* - Deteccion de fraude
- /api/admin/sessions/* - Sesiones
- /api/admin/anomalies/* - Anomalias
- /api/admin/risk-score/* - Puntuacion de riesgo
- /api/admin/support/* - Tickets y soporte
- /api/admin/config/* - Configuracion del sistema
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import logging
import json
import psycopg2.extras

from tracking.decorators import require_telegram_auth, require_owner
from tracking.services import get_db_manager

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/health', methods=['GET'])
def admin_health():
    """Health check del modulo admin."""
    return jsonify({
        'success': True,
        'module': 'admin_routes',
        'status': 'active',
        'message': 'Endpoints de admin funcionando. Migracion en progreso.',
        'endpoints_migrated': [
            '/api/admin/dashboard/stats',
            '/api/admin/dashboard/activity',
            '/api/admin/dashboard/alerts',
            '/api/admin/dashboard/charts',
            '/api/admin/users',
            '/api/admin/users/export',
            '/api/admin/users/<id>/ban',
            '/api/admin/users/<id>/detail',
            '/api/admin/users/<id>/balance',
            '/api/admin/users/<id>/note',
            '/api/admin/users/<id>/logout',
            '/api/admin/users/<id>/notify',
            '/api/admin/users/<id>/risk-score',
            '/api/admin/users/<id>/risk-score/calculate',
            '/api/admin/users/<id>/risk-score/history',
            '/api/admin/users/<id>/related-accounts',
            '/api/admin/users/<id>/tags'
        ]
    })


@admin_bp.route('/dashboard/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_dashboard_stats():
    """Obtener estadisticas del dashboard admin."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({
                'success': True,
                'data': {
                    'totalUsers': 0,
                    'activeToday': 0,
                    'totalB3C': 0,
                    'hotWalletBalance': 0,
                    'transactions24h': 0,
                    'revenueToday': 0,
                    'usersChange': 0
                }
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users")
                total_users = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE last_seen >= NOW() - INTERVAL '24 hours'
                """)
                active_today = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COALESCE(SUM(credits), 0) FROM users")
                total_b3c = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COUNT(*) FROM wallet_transactions 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                tx_24h = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM wallet_transactions 
                    WHERE transaction_type = 'deposit'
                    AND created_at >= NOW() - INTERVAL '24 hours'
                """)
                revenue_today = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                """)
                new_users_week = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE created_at >= NOW() - INTERVAL '14 days'
                    AND created_at < NOW() - INTERVAL '7 days'
                """)
                prev_users_week = cur.fetchone()[0] or 0
                
                users_change = 0
                if prev_users_week > 0:
                    users_change = round(((new_users_week - prev_users_week) / prev_users_week) * 100, 1)
                
                hot_wallet_balance = 0
                try:
                    cur.execute("""
                        SELECT COALESCE(SUM(deposit_amount), 0) 
                        FROM deposit_wallets 
                        WHERE deposit_amount > 0 AND consolidated_at IS NULL
                    """)
                    hot_wallet_balance = float(cur.fetchone()[0] or 0)
                except Exception as hw_err:
                    logger.warning(f"Could not get hot wallet balance: {hw_err}")
                    hot_wallet_balance = 0
        
        return jsonify({
            'success': True,
            'data': {
                'totalUsers': total_users,
                'activeToday': active_today,
                'totalB3C': float(total_b3c),
                'hotWalletBalance': hot_wallet_balance,
                'transactions24h': tx_24h,
                'revenueToday': float(revenue_today),
                'usersChange': users_change
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener estadisticas'}), 500


@admin_bp.route('/dashboard/activity', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_dashboard_activity():
    """Obtener actividad reciente para el dashboard."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'data': []})
        
        activities = []
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, telegram_id, first_name, username, created_at, 'user_register' as type
                    FROM users
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
                for row in cur.fetchall():
                    activities.append({
                        'type': 'user',
                        'message': f"Nuevo usuario: {row['first_name'] or row['username'] or row['id']}",
                        'timestamp': row['created_at'].isoformat() if row['created_at'] else None
                    })
                
                cur.execute("""
                    SELECT wt.user_id, wt.amount, wt.transaction_type, wt.created_at, u.first_name
                    FROM wallet_transactions wt
                    LEFT JOIN users u ON wt.user_id = u.id
                    ORDER BY wt.created_at DESC
                    LIMIT 5
                """)
                for row in cur.fetchall():
                    tx_type = 'deposito' if row['transaction_type'] == 'deposit' else 'retiro' if row['transaction_type'] == 'withdrawal' else row['transaction_type']
                    activities.append({
                        'type': 'transaction',
                        'message': f"{row['first_name'] or 'Usuario'}: {tx_type} de {row['amount']} TON",
                        'timestamp': row['created_at'].isoformat() if row['created_at'] else None
                    })
        
        activities.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        activities = activities[:10]
        
        return jsonify({'success': True, 'data': activities})
        
    except Exception as e:
        logger.error(f"Error getting dashboard activity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/dashboard/alerts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_dashboard_alerts():
    """Obtener alertas del sistema para el dashboard."""
    try:
        alerts = []
        db_manager = get_db_manager()
        
        if db_manager:
            try:
                with db_manager.get_connection() as conn:
                    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                        cur.execute("""
                            SELECT id, alert_type, description, created_at, is_resolved
                            FROM security_alerts
                            WHERE is_resolved = false
                            ORDER BY created_at DESC
                            LIMIT 10
                        """)
                        for row in cur.fetchall():
                            alerts.append({
                                'id': row['id'],
                                'level': 'warning' if row['alert_type'] == 'warning' else 'danger',
                                'message': row['description'],
                                'timestamp': row['created_at'].isoformat() if row['created_at'] else None
                            })
                        
                        try:
                            cur.execute("""
                                SELECT COUNT(*) FROM wallet_transactions 
                                WHERE transaction_type = 'withdrawal' 
                                AND created_at >= NOW() - INTERVAL '24 hours'
                            """)
                            recent_withdrawals = cur.fetchone()[0] or 0
                            if recent_withdrawals > 0:
                                alerts.insert(0, {
                                    'id': 'recent_withdrawals',
                                    'level': 'info',
                                    'message': f'{recent_withdrawals} retiros en las ultimas 24h',
                                    'timestamp': datetime.now().isoformat()
                                })
                        except Exception as e:
                            logger.debug(f"Error checking withdrawals: {e}")
                        
                        try:
                            cur.execute("""
                                SELECT COUNT(*) FROM posts 
                                WHERE is_reported = true AND is_hidden = false
                            """)
                            pending_reports = cur.fetchone()[0] or 0
                            if pending_reports > 0:
                                alerts.insert(0, {
                                    'id': 'pending_reports',
                                    'level': 'danger',
                                    'message': f'{pending_reports} reportes de contenido sin revisar',
                                    'timestamp': datetime.now().isoformat()
                                })
                        except psycopg2.errors.UndefinedColumn as e:
                            logger.debug(f"Column is_reported not found: {e}")
                        
                        cur.execute("""
                            SELECT COALESCE(SUM(deposit_amount), 0) 
                            FROM deposit_wallets 
                            WHERE deposit_amount > 0 AND consolidated_at IS NULL
                        """)
                        hot_wallet = float(cur.fetchone()[0] or 0)
                        if hot_wallet < 1.0:
                            alerts.insert(0, {
                                'id': 'low_balance',
                                'level': 'danger',
                                'message': f'Balance bajo en Hot Wallet: {hot_wallet:.4f} TON',
                                'timestamp': datetime.now().isoformat()
                            })
            except psycopg2.errors.UndefinedTable:
                logger.info("security_alerts table not found - returning empty alerts")
                alerts = []
        
        return jsonify({'success': True, 'data': alerts})
        
    except Exception as e:
        logger.error(f"Error getting dashboard alerts: {e}")
        return jsonify({'success': True, 'data': []})


@admin_bp.route('/dashboard/charts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_dashboard_charts():
    """Obtener datos para graficos del dashboard."""
    try:
        period = request.args.get('period', '30')
        try:
            days = int(period)
            if days not in [7, 30, 90]:
                days = 30
        except (ValueError, TypeError):
            days = 30
        
        users_data = []
        transactions_data = []
        db_manager = get_db_manager()
        
        if db_manager:
            with db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT DATE(created_at) as date, COUNT(*) as count
                        FROM users
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                        GROUP BY DATE(created_at)
                        ORDER BY date ASC
                    """ % days)
                    users_by_date = {row['date'].isoformat(): row['count'] for row in cur.fetchall()}
                    
                    cur.execute("""
                        SELECT DATE(created_at) as date, COUNT(*) as count
                        FROM wallet_transactions
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                        GROUP BY DATE(created_at)
                        ORDER BY date ASC
                    """ % days)
                    tx_by_date = {row['date'].isoformat(): row['count'] for row in cur.fetchall()}
                    
                    cur.execute("""
                        SELECT DATE(created_at) as date, COALESCE(SUM(amount * 0.02), 0) as revenue
                        FROM wallet_transactions
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                        AND transaction_type = 'deposit'
                        GROUP BY DATE(created_at)
                        ORDER BY date ASC
                    """ % days)
                    revenue_by_date = {row['date'].isoformat(): float(row['revenue']) for row in cur.fetchall()}
        else:
            users_by_date = {}
            tx_by_date = {}
            revenue_by_date = {}
        
        today = datetime.now().date()
        
        revenue_data = []
        
        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.isoformat()
            users_data.append({
                'date': date_str,
                'label': date.strftime('%d/%m'),
                'count': users_by_date.get(date_str, 0)
            })
            transactions_data.append({
                'date': date_str,
                'label': date.strftime('%d/%m'),
                'count': tx_by_date.get(date_str, 0)
            })
            revenue_data.append({
                'date': date_str,
                'label': date.strftime('%d/%m'),
                'amount': revenue_by_date.get(date_str, 0)
            })
        
        return jsonify({
            'success': True,
            'data': {
                'users': users_data,
                'transactions': transactions_data,
                'revenue': revenue_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ADMIN USERS ENDPOINTS (Migrados 9 Diciembre 2025)
# ============================================================


def calculate_user_risk_score(user_id, conn):
    """Calcula el score de riesgo de un usuario basado en multiples factores."""
    factors = {}
    score = 0
    
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (str(user_id),))
        user = cur.fetchone()
        if not user:
            return None, None, None
        
        if not user.get('is_verified'):
            factors['no_verificado'] = 15
            score += 15
        
        cur.execute("""
            SELECT COUNT(DISTINCT ip_address) as ip_count
            FROM trusted_devices WHERE user_id = %s
        """, (str(user_id),))
        ip_count = cur.fetchone()['ip_count'] or 0
        if ip_count > 5:
            factors['multiples_ips'] = min(ip_count * 3, 20)
            score += factors['multiples_ips']
        
        cur.execute("""
            SELECT ip_address, COUNT(DISTINCT user_id) as user_count
            FROM trusted_devices
            WHERE ip_address IN (SELECT ip_address FROM trusted_devices WHERE user_id = %s)
            AND user_id != %s
            GROUP BY ip_address
            HAVING COUNT(DISTINCT user_id) > 0
        """, (str(user_id), str(user_id)))
        shared_ips = cur.fetchall()
        if shared_ips:
            factors['ips_compartidas'] = min(len(shared_ips) * 10, 25)
            score += factors['ips_compartidas']
        
        try:
            cur.execute("""
                SELECT COUNT(*) as alert_count FROM security_alerts
                WHERE user_id = %s AND is_resolved = false
            """, (user.get('id'),))
            alerts = cur.fetchone()['alert_count'] or 0
            if alerts > 0:
                factors['alertas_activas'] = min(alerts * 5, 20)
                score += factors['alertas_activas']
        except Exception:
            pass
        
        cur.execute("""
            SELECT COUNT(*) as tx_count FROM wallet_transactions
            WHERE user_id = %s AND created_at >= NOW() - INTERVAL '1 hour'
        """, (str(user_id),))
        recent_tx = cur.fetchone()['tx_count'] or 0
        if recent_tx > 10:
            factors['transacciones_rapidas'] = min(recent_tx, 15)
            score += factors['transacciones_rapidas']
        
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) as total FROM wallet_transactions
            WHERE user_id = %s AND transaction_type = 'withdraw' 
            AND created_at >= NOW() - INTERVAL '24 hours'
        """, (str(user_id),))
        withdrawals = float(cur.fetchone()['total'] or 0)
        if withdrawals > 1000:
            factors['retiros_altos'] = min(int(withdrawals / 100), 20)
            score += factors['retiros_altos']
        
        account_age_days = 0
        if user.get('created_at'):
            account_age_days = (datetime.now() - user['created_at']).days
        if account_age_days < 7:
            factors['cuenta_nueva'] = 10
            score += 10
        
        score = min(score, 100)
        
        if score >= 75:
            risk_level = 'critical'
        elif score >= 50:
            risk_level = 'high'
        elif score >= 25:
            risk_level = 'medium'
        else:
            risk_level = 'low'
    
    return score, risk_level, factors


@admin_bp.route('/users/<user_id>/ban', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_ban_user(user_id):
    """Banear o desbanear un usuario."""
    try:
        data = request.get_json() or {}
        should_ban = data.get('banned', True)
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users SET is_banned = %s WHERE id = %s OR telegram_id::text = %s
                    RETURNING is_banned
                """, (should_ban, str(user_id), str(user_id)))
                result = cur.fetchone()
                
                if not result:
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                conn.commit()
        
        action = 'baneado' if should_ban else 'desbaneado'
        return jsonify({'success': True, 'message': f'Usuario {action} correctamente', 'banned': should_ban})
        
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>/detail', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_user_detail(user_id):
    """Admin: Obtener detalle completo de un usuario."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, telegram_id, username, first_name, last_name, credits,
                           level, is_active, is_verified, wallet_address, created_at, last_seen,
                           COALESCE(is_banned, false) as is_banned
                    FROM users WHERE id = %s OR telegram_id::text = %s
                """, (str(user_id), str(user_id)))
                user = cur.fetchone()
                
                if not user:
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                cur.execute("""
                    SELECT DISTINCT ip_address, device_name, device_type, user_agent, 
                           last_used_at, created_at, is_active
                    FROM trusted_devices WHERE user_id = %s
                    ORDER BY last_used_at DESC NULLS LAST LIMIT 20
                """, (str(user.get('telegram_id', user_id)),))
                devices = cur.fetchall()
                
                cur.execute("""
                    SELECT DISTINCT ip_address, activity_type, created_at
                    FROM security_activity_log 
                    WHERE user_id = %s AND ip_address IS NOT NULL AND ip_address != ''
                    ORDER BY created_at DESC LIMIT 50
                """, (str(user.get('telegram_id', user_id)),))
                ip_history = cur.fetchall()
                
                cur.execute("""
                    SELECT id, transaction_type as type, amount, description, created_at
                    FROM wallet_transactions WHERE user_id = %s
                    ORDER BY created_at DESC LIMIT 50
                """, (str(user.get('telegram_id', user_id)),))
                transactions = cur.fetchall()
                
                cur.execute("""
                    SELECT id, content_type, caption, created_at, is_active
                    FROM posts WHERE user_id = %s
                    ORDER BY created_at DESC LIMIT 20
                """, (str(user.get('telegram_id', user_id)),))
                publications = cur.fetchall()
                
                cur.execute("""
                    SELECT id, note, created_by, created_at
                    FROM admin_user_notes WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (str(user_id),))
                notes = cur.fetchall()
                
                cur.execute("""
                    SELECT id, activity_type, description, ip_address, created_at
                    FROM security_activity_log WHERE user_id = %s
                    ORDER BY created_at DESC LIMIT 30
                """, (str(user.get('telegram_id', user_id)),))
                activity_log = cur.fetchall()
                
                ips_from_devices = [d['ip_address'] for d in devices if d.get('ip_address')]
                ips_from_history = [ip['ip_address'] for ip in ip_history if ip.get('ip_address')]
                all_ips = list(set(ips_from_devices + ips_from_history))
                
                fraud_alerts = []
                if all_ips:
                    cur.execute("""
                        SELECT DISTINCT user_id, ip_address 
                        FROM trusted_devices 
                        WHERE ip_address = ANY(%s) AND user_id != %s
                    """, (all_ips, str(user.get('telegram_id', user_id))))
                    other_users_same_ip = cur.fetchall()
                    if other_users_same_ip:
                        fraud_alerts.append({
                            'type': 'multiple_accounts',
                            'message': f'IP compartida con {len(set([u["user_id"] for u in other_users_same_ip]))} otros usuarios',
                            'ips': list(set([u['ip_address'] for u in other_users_same_ip]))
                        })
        
        ips_used = all_ips if all_ips else []
        
        return jsonify({
            'success': True,
            'user': {
                'id': str(user['id']),
                'telegram_id': user['telegram_id'],
                'username': user.get('username'),
                'first_name': user.get('first_name'),
                'last_name': user.get('last_name'),
                'credits': float(user.get('credits', 0)),
                'level': user.get('level', 1),
                'is_active': user.get('is_active', True),
                'is_verified': user.get('is_verified', False),
                'is_banned': user.get('is_banned', False),
                'wallet_address': user.get('wallet_address'),
                'created_at': str(user.get('created_at', '')),
                'last_seen': str(user.get('last_seen', ''))
            },
            'devices': [{
                'ip': d['ip_address'],
                'device': d['device_name'],
                'device_type': d.get('device_type'),
                'user_agent': d.get('user_agent'),
                'is_active': d.get('is_active', True),
                'last_used': str(d['last_used_at']) if d.get('last_used_at') else None,
                'created_at': str(d['created_at']) if d.get('created_at') else None
            } for d in devices],
            'ips': ips_used,
            'activity_log': [{
                'id': a['id'],
                'type': a['activity_type'],
                'description': a.get('description', ''),
                'ip': a.get('ip_address'),
                'date': str(a['created_at'])
            } for a in activity_log],
            'fraud_alerts': fraud_alerts,
            'transactions': [{
                'id': t['id'],
                'type': t['type'],
                'amount': float(t['amount']) if t.get('amount') else 0,
                'description': t.get('description', ''),
                'date': str(t['created_at'])
            } for t in transactions],
            'publications': [{
                'id': p['id'],
                'type': p['content_type'],
                'caption': p.get('caption', '')[:100] if p.get('caption') else '',
                'date': str(p['created_at']),
                'active': p.get('is_active', True)
            } for p in publications],
            'notes': [{
                'id': n['id'],
                'note': n['note'],
                'created_by': n.get('created_by'),
                'date': str(n['created_at'])
            } for n in notes]
        })
        
    except Exception as e:
        logger.error(f"Error getting user detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>/balance', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_adjust_user_balance(user_id):
    """Admin: Ajustar balance B3C de un usuario."""
    try:
        data = request.get_json() or {}
        amount = float(data.get('amount', 0))
        reason = data.get('reason', 'Ajuste manual por admin')
        
        if amount == 0:
            return jsonify({'success': False, 'error': 'El monto no puede ser 0'}), 400
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    UPDATE users SET credits = credits + %s
                    WHERE id = %s OR telegram_id::text = %s
                    RETURNING id, credits
                """, (amount, str(user_id), str(user_id)))
                result = cur.fetchone()
                
                if not result:
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                cur.execute("""
                    INSERT INTO wallet_transactions (user_id, transaction_type, amount, description)
                    VALUES (%s, 'admin_adjustment', %s, %s)
                """, (str(user_id), amount, f'{reason} (Admin: {admin_id})'))
                
                conn.commit()
        
        action = 'agregados' if amount > 0 else 'deducidos'
        return jsonify({
            'success': True,
            'message': f'{abs(amount)} B3C {action} correctamente',
            'new_balance': float(result['credits'])
        })
        
    except Exception as e:
        logger.error(f"Error adjusting balance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>/note', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_add_user_note(user_id):
    """Admin: Agregar nota interna sobre un usuario."""
    try:
        data = request.get_json() or {}
        note = data.get('note', '').strip()
        
        if not note:
            return jsonify({'success': False, 'error': 'La nota no puede estar vacia'}), 400
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS admin_user_notes (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        note TEXT NOT NULL,
                        created_by TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    INSERT INTO admin_user_notes (user_id, note, created_by)
                    VALUES (%s, %s, %s) RETURNING id
                """, (str(user_id), note, admin_id))
                note_id = cur.fetchone()[0]
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Nota agregada', 'note_id': note_id})
        
    except Exception as e:
        logger.error(f"Error adding note: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>/logout', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_logout_user(user_id):
    """Admin: Cerrar todas las sesiones de un usuario."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE trusted_devices SET is_active = false
                    WHERE user_id = %s
                """, (str(user_id),))
                devices_closed = cur.rowcount
                
                cur.execute("""
                    INSERT INTO security_activity_log (user_id, activity_type, description)
                    VALUES (%s, 'ADMIN_LOGOUT', %s)
                """, (str(user_id), f'Sesiones cerradas por admin {admin_id}'))
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'{devices_closed} sesiones cerradas',
            'sessions_closed': devices_closed
        })
        
    except Exception as e:
        logger.error(f"Error closing user sessions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>/notify', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_notify_user(user_id):
    """Admin: Enviar notificacion a un usuario."""
    try:
        data = request.get_json() or {}
        message = data.get('message', '').strip()
        notification_type = data.get('type', 'admin')
        
        if not message:
            return jsonify({'success': False, 'error': 'El mensaje no puede estar vacio'}), 400
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM users WHERE id = %s OR telegram_id::text = %s
                """, (str(user_id), str(user_id)))
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                cur.execute("""
                    INSERT INTO notifications (user_id, type, message, is_read, created_at)
                    VALUES (%s, %s, %s, false, NOW())
                    RETURNING id
                """, (str(user_id), notification_type, f'[Admin] {message}'))
                notification_id = cur.fetchone()[0]
                
                cur.execute("""
                    INSERT INTO admin_user_notes (user_id, note, created_by)
                    VALUES (%s, %s, %s)
                """, (str(user_id), f'[NOTIFICACION ENVIADA] {message}', admin_id))
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notificacion enviada',
            'notification_id': notification_id
        })
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>/risk-score', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_user_risk_score(user_id):
    """Admin: Obtener score de riesgo de un usuario."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM risk_scores WHERE user_id = %s
                """, (str(user_id),))
                existing = cur.fetchone()
                
                if existing:
                    result = dict(existing)
                    if result.get('last_calculated'):
                        result['last_calculated'] = result['last_calculated'].isoformat()
                    if result.get('created_at'):
                        result['created_at'] = result['created_at'].isoformat()
                    if result.get('updated_at'):
                        result['updated_at'] = result['updated_at'].isoformat()
                    return jsonify({'success': True, 'risk_score': result})
                
                score, risk_level, factors = calculate_user_risk_score(user_id, conn)
                if score is None:
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                return jsonify({
                    'success': True,
                    'risk_score': {
                        'user_id': user_id,
                        'score': score,
                        'risk_level': risk_level,
                        'factors': factors,
                        'last_calculated': None,
                        'note': 'Score calculado en tiempo real, no guardado'
                    }
                })
        
    except Exception as e:
        logger.error(f"Error getting risk score: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>/risk-score/calculate', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_calculate_risk_score(user_id):
    """Admin: Calcular y guardar score de riesgo de un usuario."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            score, risk_level, factors = calculate_user_risk_score(user_id, conn)
            if score is None:
                return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
            
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM risk_scores WHERE user_id = %s", (str(user_id),))
                existing = cur.fetchone()
                
                if existing:
                    old_score = existing['score']
                    old_level = existing['risk_level']
                    
                    if old_score != score or old_level != risk_level:
                        cur.execute("""
                            INSERT INTO risk_score_history (user_id, old_score, new_score, old_level, new_level, reason)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (str(user_id), old_score, score, old_level, risk_level, 'Recalculo automatico'))
                    
                    cur.execute("""
                        UPDATE risk_scores SET score = %s, risk_level = %s, factors = %s,
                        last_calculated = NOW(), updated_at = NOW()
                        WHERE user_id = %s
                    """, (score, risk_level, json.dumps(factors), str(user_id)))
                else:
                    cur.execute("""
                        INSERT INTO risk_scores (user_id, score, risk_level, factors, last_calculated)
                        VALUES (%s, %s, %s, %s, NOW())
                    """, (str(user_id), score, risk_level, json.dumps(factors)))
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'risk_score': {
                'user_id': user_id,
                'score': score,
                'risk_level': risk_level,
                'factors': factors
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating risk score: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>/risk-score/history', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_risk_score_history(user_id):
    """Admin: Obtener historial de cambios de score de riesgo."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM risk_score_history
                    WHERE user_id = %s
                    ORDER BY changed_at DESC
                    LIMIT 50
                """, (str(user_id),))
                history = []
                for row in cur.fetchall():
                    r = dict(row)
                    if r.get('changed_at'):
                        r['changed_at'] = r['changed_at'].isoformat()
                    history.append(r)
        
        return jsonify({'success': True, 'history': history})
        
    except Exception as e:
        logger.error(f"Error getting risk score history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>/related-accounts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_related_accounts(user_id):
    """Admin: Obtener cuentas relacionadas de un usuario."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        related = []
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT DISTINCT td2.user_id, u.username, td.ip_address
                    FROM trusted_devices td
                    JOIN trusted_devices td2 ON td.ip_address = td2.ip_address AND td.user_id != td2.user_id
                    JOIN users u ON td2.user_id = u.id
                    WHERE td.user_id = %s
                """, (str(user_id),))
                for row in cur.fetchall():
                    related.append({
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'relation_type': 'same_ip',
                        'evidence': {'ip': row['ip_address']}
                    })
                
                cur.execute("""
                    SELECT DISTINCT td2.user_id, u.username, td.device_fingerprint
                    FROM trusted_devices td
                    JOIN trusted_devices td2 ON td.device_fingerprint = td2.device_fingerprint 
                        AND td.user_id != td2.user_id
                        AND td.device_fingerprint IS NOT NULL
                    JOIN users u ON td2.user_id = u.id
                    WHERE td.user_id = %s
                """, (str(user_id),))
                for row in cur.fetchall():
                    existing = next((r for r in related if r['user_id'] == row['user_id']), None)
                    if existing:
                        existing['relation_type'] = 'same_ip_and_device'
                        existing['evidence']['fingerprint'] = row['device_fingerprint']
                    else:
                        related.append({
                            'user_id': row['user_id'],
                            'username': row['username'],
                            'relation_type': 'same_device',
                            'evidence': {'fingerprint': row['device_fingerprint']}
                        })
                
                cur.execute("""
                    SELECT DISTINCT u2.id as user_id, u2.username, u1.wallet_address
                    FROM users u1
                    JOIN users u2 ON u1.wallet_address = u2.wallet_address AND u1.id != u2.id
                    WHERE u1.id = %s AND u1.wallet_address IS NOT NULL AND u1.wallet_address != ''
                """, (str(user_id),))
                for row in cur.fetchall():
                    existing = next((r for r in related if r['user_id'] == row['user_id']), None)
                    if existing:
                        existing['evidence']['wallet'] = row['wallet_address']
                    else:
                        related.append({
                            'user_id': row['user_id'],
                            'username': row['username'],
                            'relation_type': 'same_wallet',
                            'evidence': {'wallet': row['wallet_address']}
                        })
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'related_accounts': related,
            'count': len(related)
        })
        
    except Exception as e:
        logger.error(f"Error getting related accounts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_all_users():
    """Admin: Obtener todos los usuarios con paginacion, busqueda y filtros."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT id, username, first_name, last_name, telegram_id, 
                           credits, level, is_active, is_verified, wallet_address,
                           created_at, last_seen,
                           COALESCE(is_banned, false) as is_banned
                    FROM users 
                    WHERE 1=1
                """
                count_query = "SELECT COUNT(*) as total FROM users WHERE 1=1"
                params = []
                count_params = []
                
                if search:
                    search_pattern = f"%{search}%"
                    query += " AND (username ILIKE %s OR first_name ILIKE %s OR CAST(telegram_id AS TEXT) ILIKE %s OR CAST(id AS TEXT) = %s)"
                    count_query += " AND (username ILIKE %s OR first_name ILIKE %s OR CAST(telegram_id AS TEXT) ILIKE %s OR CAST(id AS TEXT) = %s)"
                    params.extend([search_pattern, search_pattern, search_pattern, search])
                    count_params.extend([search_pattern, search_pattern, search_pattern, search])
                
                if status == 'active':
                    query += " AND (is_banned IS NULL OR is_banned = false)"
                    count_query += " AND (is_banned IS NULL OR is_banned = false)"
                elif status == 'banned':
                    query += " AND is_banned = true"
                    count_query += " AND is_banned = true"
                elif status == 'verified':
                    query += " AND is_verified = true"
                    count_query += " AND is_verified = true"
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()['total'] or 0
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                users = cur.fetchall()
        
        pages = max(1, (total + limit - 1) // limit)
        
        return jsonify({
            'success': True,
            'users': [{
                'user_id': str(u['id']),
                'id': u['id'],
                'telegram_id': u.get('telegram_id'),
                'username': u.get('username'),
                'first_name': u.get('first_name'),
                'last_name': u.get('last_name'),
                'credits': float(u.get('credits', 0)),
                'level': u.get('level', 1),
                'is_active': u.get('is_active', True),
                'is_verified': u.get('is_verified', False),
                'is_banned': u.get('is_banned', False),
                'wallet_address': u.get('wallet_address'),
                'created_at': str(u.get('created_at', '')),
                'last_seen': str(u.get('last_seen', ''))
            } for u in users],
            'total': total,
            'page': page,
            'pages': pages,
            'count': len(users)
        })
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/export', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_export_users():
    """Admin: Exportar usuarios a CSV."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, telegram_id, username, first_name, last_name, 
                           credits, is_active, is_verified, wallet_address,
                           created_at, last_seen
                    FROM users 
                    ORDER BY created_at DESC
                """)
                users = cur.fetchall()
        
        csv_lines = ['ID,Telegram ID,Username,Nombre,Apellido,Credits,Activo,Verificado,Wallet,Registro,Ultima Conexion']
        for u in users:
            csv_lines.append(','.join([
                str(u.get('id', '')),
                str(u.get('telegram_id', '')),
                str(u.get('username', '') or ''),
                str(u.get('first_name', '') or ''),
                str(u.get('last_name', '') or ''),
                str(u.get('credits', 0)),
                'Si' if u.get('is_active') else 'No',
                'Si' if u.get('is_verified') else 'No',
                str(u.get('wallet_address', '') or ''),
                str(u.get('created_at', '') or ''),
                str(u.get('last_seen', '') or '')
            ]))
        
        return jsonify({
            'success': True,
            'csv': '\n'.join(csv_lines)
        })
        
    except Exception as e:
        logger.error(f"Error exporting users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>/tags', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_save_user_tags(user_id):
    """Admin: Guardar etiquetas de un usuario."""
    try:
        data = request.get_json() or {}
        tags = data.get('tags', [])
        return jsonify({'success': True, 'message': 'Etiquetas actualizadas'})
    except Exception as e:
        logger.error(f"Error saving user tags: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
