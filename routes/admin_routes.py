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

from flask import Blueprint, jsonify, request, Response
from datetime import datetime, timedelta
import logging
import json
import io
import psycopg2.extras

from tracking.decorators import require_telegram_auth, require_owner
from tracking.services import get_db_manager, get_security_manager

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
            '/api/admin/users/<id>/tags',
            '/api/admin/stats',
            '/api/admin/stats/overview',
            '/api/admin/stats/users',
            '/api/admin/stats/transactions',
            '/api/admin/security/users',
            '/api/admin/security/user/<id>/devices',
            '/api/admin/security/user/<id>/device/remove',
            '/api/admin/security/alerts',
            '/api/admin/security/alerts/<id>/resolve',
            '/api/admin/security/statistics',
            '/api/admin/security/user/<id>/activity'
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


# ============================================================
# ADMIN STATS ENDPOINTS (Migrados 9 Diciembre 2025)
# ============================================================


@admin_bp.route('/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_stats():
    """Admin: Obtener estadisticas generales del sistema (solo owner)."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({
                'success': True,
                'total_users': 0,
                'active_bots': 0,
                'total_transactions': 0,
                'security_alerts': 0
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users")
                total_users = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM user_bots WHERE is_active = true")
                active_bots = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM wallet_transactions")
                total_transactions = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM security_alerts WHERE is_resolved = false")
                security_alerts = cur.fetchone()[0] or 0
        
        return jsonify({
            'success': True,
            'total_users': total_users,
            'active_bots': active_bots,
            'total_transactions': total_transactions,
            'security_alerts': security_alerts
        })
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Error al obtener estadisticas'
        }), 500


@admin_bp.route('/stats/overview', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_stats_overview():
    """Admin: Estadisticas generales detalladas del sistema."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) as total FROM users")
                total_users = cur.fetchone()['total'] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE last_seen >= NOW() - INTERVAL '24 hours'")
                active_24h = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE last_seen >= NOW() - INTERVAL '7 days'")
                active_7d = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '24 hours'")
                new_users_24h = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days'")
                new_users_7d = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM wallet_transactions")
                total_transactions = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM wallet_transactions WHERE created_at >= NOW() - INTERVAL '24 hours'")
                transactions_24h = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COALESCE(SUM(amount), 0) FROM wallet_transactions WHERE transaction_type = 'deposit'")
                total_deposits = float(cur.fetchone()[0] or 0)
                
                cur.execute("SELECT COALESCE(SUM(amount), 0) FROM wallet_transactions WHERE transaction_type = 'withdraw'")
                total_withdrawals = float(cur.fetchone()[0] or 0)
                
                cur.execute("SELECT COALESCE(SUM(credits), 0) FROM users")
                total_b3c_circulation = float(cur.fetchone()[0] or 0)
                
                cur.execute("SELECT COUNT(*) FROM posts WHERE is_active = true")
                total_posts = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM posts WHERE created_at >= NOW() - INTERVAL '24 hours'")
                posts_24h = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM security_alerts WHERE is_resolved = false")
                pending_alerts = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM user_bots WHERE is_active = true")
                active_bots = cur.fetchone()[0] or 0
        
        return jsonify({
            'success': True,
            'data': {
                'users': {
                    'total': total_users,
                    'active_24h': active_24h,
                    'active_7d': active_7d,
                    'new_24h': new_users_24h,
                    'new_7d': new_users_7d
                },
                'transactions': {
                    'total': total_transactions,
                    'last_24h': transactions_24h,
                    'total_deposits': total_deposits,
                    'total_withdrawals': total_withdrawals
                },
                'economy': {
                    'b3c_circulation': total_b3c_circulation
                },
                'content': {
                    'total_posts': total_posts,
                    'posts_24h': posts_24h
                },
                'security': {
                    'pending_alerts': pending_alerts,
                    'active_bots': active_bots
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting stats overview: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/stats/users', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_stats_users():
    """Admin: Estadisticas detalladas de usuarios."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) as total FROM users")
                total = cur.fetchone()['total'] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE is_verified = true")
                verified = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE is_active = true")
                active = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE is_active = false")
                banned = cur.fetchone()[0] or 0
                
                cur.execute("SELECT COUNT(*) FROM users WHERE last_seen >= NOW() - INTERVAL '1 hour'")
                online_now = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count 
                    FROM users 
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY DATE(created_at) 
                    ORDER BY date DESC
                """)
                registrations_by_day = [{'date': str(r['date']), 'count': r['count']} for r in cur.fetchall()]
                
                cur.execute("""
                    SELECT LOWER(role) as role, COUNT(*) as count 
                    FROM users 
                    GROUP BY LOWER(role)
                """)
                by_role = {r['role']: r['count'] for r in cur.fetchall()}
                
                cur.execute("""
                    SELECT level, COUNT(*) as count 
                    FROM users 
                    GROUP BY level 
                    ORDER BY level
                """)
                by_level = [{'level': r['level'], 'count': r['count']} for r in cur.fetchall()]
                
                cur.execute("""
                    SELECT u.id, u.username, u.credits, u.level, u.is_verified, u.last_seen
                    FROM users u
                    ORDER BY u.credits DESC
                    LIMIT 10
                """)
                top_users = [dict(r) for r in cur.fetchall()]
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total': total,
                    'verified': verified,
                    'active': active,
                    'banned': banned,
                    'online_now': online_now
                },
                'registrations_by_day': registrations_by_day,
                'by_role': by_role,
                'by_level': by_level,
                'top_users': top_users
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/stats/transactions', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_stats_transactions():
    """Admin: Estadisticas detalladas de transacciones."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) as total FROM wallet_transactions")
                total = cur.fetchone()['total'] or 0
                
                cur.execute("""
                    SELECT transaction_type, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
                    FROM wallet_transactions
                    GROUP BY transaction_type
                """)
                by_type = {r['transaction_type']: {'count': r['count'], 'amount': float(r['total_amount'])} for r in cur.fetchall()}
                
                cur.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count, COALESCE(SUM(amount), 0) as volume
                    FROM wallet_transactions
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """)
                by_day = [{'date': str(r['date']), 'count': r['count'], 'volume': float(r['volume'])} for r in cur.fetchall()]
                
                cur.execute("""
                    SELECT COUNT(*) FROM wallet_transactions WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                count_24h = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM wallet_transactions 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                volume_24h = float(cur.fetchone()[0] or 0)
                
                cur.execute("""
                    SELECT COALESCE(AVG(amount), 0) FROM wallet_transactions
                """)
                avg_amount = float(cur.fetchone()[0] or 0)
                
                cur.execute("""
                    SELECT wt.id, wt.user_id, u.username, wt.transaction_type, wt.amount, wt.description, wt.created_at
                    FROM wallet_transactions wt
                    LEFT JOIN users u ON wt.user_id = u.id
                    ORDER BY wt.created_at DESC
                    LIMIT 20
                """)
                recent = []
                for r in cur.fetchall():
                    row = dict(r)
                    if row.get('created_at'):
                        row['created_at'] = row['created_at'].isoformat()
                    recent.append(row)
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total': total,
                    'count_24h': count_24h,
                    'volume_24h': volume_24h,
                    'avg_amount': round(avg_amount, 2)
                },
                'by_type': by_type,
                'by_day': by_day,
                'recent': recent
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting transaction stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ADMIN SECURITY ENDPOINTS (Migrados 9 Diciembre 2025)
# ============================================================


@admin_bp.route('/security/users', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_users_devices():
    """Admin: Obtener todos los usuarios con sus dispositivos."""
    try:
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        users = security_manager.get_all_users_devices_admin()
        return jsonify({
            'success': True,
            'users': users,
            'count': len(users)
        })
        
    except Exception as e:
        logger.error(f"Error in admin get users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/security/user/<user_id>/devices', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_user_devices(user_id):
    """Admin: Obtener dispositivos de un usuario especifico."""
    try:
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        devices = security_manager.get_trusted_devices(user_id)
        return jsonify({
            'success': True,
            'devices': devices,
            'count': len(devices)
        })
        
    except Exception as e:
        logger.error(f"Error in admin get user devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/security/user/<user_id>/device/remove', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_remove_user_device(user_id):
    """Admin: Eliminar dispositivo de un usuario."""
    try:
        admin_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        device_id = data.get('deviceId', '')
        
        if not device_id:
            return jsonify({'success': False, 'error': 'ID de dispositivo requerido'}), 400
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        result = security_manager.admin_remove_user_device(user_id, device_id, admin_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in admin remove device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/security/alerts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_security_alerts():
    """Admin: Obtener alertas de seguridad."""
    try:
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        unresolved_only = request.args.get('unresolved', 'true').lower() == 'true'
        alerts = security_manager.get_security_alerts_admin(unresolved_only)
        return jsonify({
            'success': True,
            'alerts': alerts,
            'count': len(alerts)
        })
        
    except Exception as e:
        logger.error(f"Error in admin get alerts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/security/alerts/<int:alert_id>/resolve', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_resolve_alert(alert_id):
    """Admin: Resolver una alerta de seguridad."""
    try:
        admin_id = str(request.telegram_user.get('id', 0))
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        success = security_manager.resolve_alert_admin(alert_id, admin_id)
        return jsonify({
            'success': success,
            'message': 'Alerta resuelta' if success else 'No se pudo resolver la alerta'
        })
        
    except Exception as e:
        logger.error(f"Error in admin resolve alert: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/security/statistics', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_security_stats():
    """Admin: Obtener estadisticas de seguridad."""
    try:
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        stats = security_manager.get_device_statistics_admin()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error in admin get stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/security/user/<user_id>/activity', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_user_activity(user_id):
    """Admin: Obtener actividad de seguridad de un usuario."""
    try:
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        limit = request.args.get('limit', 50, type=int)
        activities = security_manager.get_security_activity(user_id, limit)
        return jsonify({
            'success': True,
            'activities': activities
        })
        
    except Exception as e:
        logger.error(f"Error in admin get user activity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ADMIN FINANCIAL ENDPOINTS (Migrados 9 Diciembre 2025)
# ============================================================


@admin_bp.route('/financial/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_financial_stats():
    """Admin: Dashboard financiero con métricas de B3C, TON y comisiones."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({
                'success': True,
                'data': {
                    'totalB3CSold': 0,
                    'totalTONReceived': 0,
                    'totalCommissions': 0,
                    'monthVolume': 0,
                    'lastMonthVolume': 0,
                    'volumeChange': 0,
                    'pendingWithdrawals': 0,
                    'pendingWithdrawalsAmount': 0,
                    'dailyRevenue': [],
                    'dailyVolume': []
                }
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(CASE WHEN transaction_type = 'deposit' THEN amount ELSE 0 END), 0) as total_b3c_sold,
                           COALESCE(SUM(CASE WHEN transaction_type = 'deposit' THEN amount * 0.1 ELSE 0 END), 0) as total_ton_received,
                           COALESCE(SUM(CASE WHEN transaction_type IN ('deposit', 'withdrawal') THEN amount * 0.02 ELSE 0 END), 0) as total_commissions
                    FROM wallet_transactions
                """)
                totals = cur.fetchone()
                total_b3c_sold = float(totals['total_b3c_sold']) if totals else 0
                total_ton_received = float(totals['total_ton_received']) if totals else 0
                total_commissions = float(totals['total_commissions']) if totals else 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as month_volume
                    FROM wallet_transactions
                    WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
                """)
                month_vol = cur.fetchone()
                month_volume = float(month_vol['month_volume']) if month_vol else 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as last_month_volume
                    FROM wallet_transactions
                    WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
                    AND created_at < DATE_TRUNC('month', CURRENT_DATE)
                """)
                last_month_vol = cur.fetchone()
                last_month_volume = float(last_month_vol['last_month_volume']) if last_month_vol else 0
                
                volume_change = 0
                if last_month_volume > 0:
                    volume_change = round(((month_volume - last_month_volume) / last_month_volume) * 100, 1)
                
                try:
                    cur.execute("""
                        SELECT COUNT(*) as count, COALESCE(SUM(amount_ton), 0) as total
                        FROM b3c_withdrawals
                        WHERE status = 'pending'
                    """)
                    pending = cur.fetchone()
                    pending_withdrawals = int(pending['count']) if pending else 0
                    pending_withdrawals_amount = float(pending['total']) if pending else 0
                except Exception as e:
                    logger.debug(f"b3c_withdrawals table not found: {e}")
                    pending_withdrawals = 0
                    pending_withdrawals_amount = 0
                
                cur.execute("""
                    SELECT DATE(created_at) as date, 
                           COALESCE(SUM(amount * 0.02), 0) as revenue
                    FROM wallet_transactions
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """)
                revenue_data = cur.fetchall()
                
                cur.execute("""
                    SELECT DATE(created_at) as date, 
                           COALESCE(SUM(amount), 0) as volume
                    FROM wallet_transactions
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """)
                volume_data = cur.fetchall()
        
        daily_revenue = []
        daily_volume = []
        revenue_dict = {row['date'].isoformat(): float(row['revenue']) for row in revenue_data} if revenue_data else {}
        volume_dict = {row['date'].isoformat(): float(row['volume']) for row in volume_data} if volume_data else {}
        
        for i in range(30):
            date = (datetime.now() - timedelta(days=29-i)).date()
            date_str = date.isoformat()
            daily_revenue.append({
                'date': date_str,
                'label': date.strftime('%d/%m'),
                'amount': revenue_dict.get(date_str, 0)
            })
            daily_volume.append({
                'date': date_str,
                'label': date.strftime('%d/%m'),
                'amount': volume_dict.get(date_str, 0)
            })
        
        return jsonify({
            'success': True,
            'data': {
                'totalB3CSold': total_b3c_sold,
                'totalTONReceived': total_ton_received,
                'totalCommissions': total_commissions,
                'monthVolume': month_volume,
                'lastMonthVolume': last_month_volume,
                'volumeChange': volume_change,
                'pendingWithdrawals': pending_withdrawals,
                'pendingWithdrawalsAmount': pending_withdrawals_amount,
                'dailyRevenue': daily_revenue,
                'dailyVolume': daily_volume
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting financial stats: {e}")
        return jsonify({
            'success': True,
            'data': {
                'totalB3CSold': 0,
                'totalTONReceived': 0,
                'totalCommissions': 0,
                'monthVolume': 0,
                'lastMonthVolume': 0,
                'volumeChange': 0,
                'pendingWithdrawals': 0,
                'pendingWithdrawalsAmount': 0,
                'dailyRevenue': [],
                'dailyVolume': []
            }
        })


@admin_bp.route('/financial/period-stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_financial_period_stats():
    """Admin: Estadísticas financieras por período personalizado."""
    try:
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        
        if not date_from or not date_to:
            return jsonify({'success': False, 'error': 'Fechas requeridas'}), 400
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({
                'success': True,
                'data': {
                    'txCount': 0,
                    'b3cVolume': 0,
                    'purchases': {'count': 0, 'tonAmount': 0, 'b3cAmount': 0},
                    'withdrawals': {'count': 0, 'b3cAmount': 0},
                    'transfers': {'count': 0, 'b3cAmount': 0},
                    'commissions': 0,
                    'dailyVolume': [],
                    'typeBreakdown': {'purchases': 0, 'withdrawals': 0, 'transfers': 0}
                }
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as volume
                    FROM wallet_transactions
                    WHERE created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                tx_totals = cur.fetchone()
                tx_count = int(tx_totals['count']) if tx_totals else 0
                b3c_volume = float(tx_totals['volume']) if tx_totals else 0
                
                cur.execute("""
                    SELECT COUNT(*) as count, 
                           COALESCE(SUM(amount), 0) as b3c_amount,
                           COALESCE(SUM(amount * 0.1), 0) as ton_amount
                    FROM wallet_transactions
                    WHERE transaction_type = 'deposit' 
                    AND created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                purchases = cur.fetchone()
                purchases_count = int(purchases['count']) if purchases else 0
                purchases_b3c = float(purchases['b3c_amount']) if purchases else 0
                purchases_ton = float(purchases['ton_amount']) if purchases else 0
                
                cur.execute("""
                    SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as b3c_amount
                    FROM wallet_transactions
                    WHERE transaction_type = 'withdrawal' 
                    AND created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                withdrawals = cur.fetchone()
                withdrawals_count = int(withdrawals['count']) if withdrawals else 0
                withdrawals_b3c = float(withdrawals['b3c_amount']) if withdrawals else 0
                
                cur.execute("""
                    SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as b3c_amount
                    FROM wallet_transactions
                    WHERE transaction_type = 'transfer' 
                    AND created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                transfers = cur.fetchone()
                transfers_count = int(transfers['count']) if transfers else 0
                transfers_b3c = float(transfers['b3c_amount']) if transfers else 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount * 0.02), 0) as commissions
                    FROM wallet_transactions
                    WHERE transaction_type IN ('deposit', 'withdrawal')
                    AND created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                comm = cur.fetchone()
                commissions = float(comm['commissions']) if comm else 0
                
                cur.execute("""
                    SELECT DATE(created_at) as date, COALESCE(SUM(amount), 0) as volume
                    FROM wallet_transactions
                    WHERE created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """, (date_from, date_to))
                daily_data = cur.fetchall()
        
        daily_volume = []
        if daily_data:
            for row in daily_data:
                daily_volume.append({
                    'date': row['date'].isoformat(),
                    'label': row['date'].strftime('%d/%m'),
                    'amount': float(row['volume'])
                })
        
        return jsonify({
            'success': True,
            'data': {
                'txCount': tx_count,
                'b3cVolume': b3c_volume,
                'purchases': {
                    'count': purchases_count,
                    'tonAmount': purchases_ton,
                    'b3cAmount': purchases_b3c
                },
                'withdrawals': {
                    'count': withdrawals_count,
                    'b3cAmount': withdrawals_b3c
                },
                'transfers': {
                    'count': transfers_count,
                    'b3cAmount': transfers_b3c
                },
                'commissions': commissions,
                'dailyVolume': daily_volume,
                'typeBreakdown': {
                    'purchases': purchases_count,
                    'withdrawals': withdrawals_count,
                    'transfers': transfers_count
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting period stats: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener estadísticas'}), 500


@admin_bp.route('/financial/period-stats/export', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_financial_period_stats_export():
    """Admin: Exportar estadísticas por período a CSV."""
    try:
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        
        if not date_from or not date_to:
            return jsonify({'success': False, 'error': 'Fechas requeridas'}), 400
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'csv': 'No hay datos disponibles'})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT wt.id, u.telegram_id, u.username, u.first_name,
                           wt.transaction_type, wt.amount, wt.status, wt.tx_hash, wt.created_at
                    FROM wallet_transactions wt
                    LEFT JOIN users u ON wt.user_id = u.id
                    WHERE wt.created_at >= %s AND wt.created_at <= %s::date + INTERVAL '1 day'
                    ORDER BY wt.created_at DESC
                """, (date_from, date_to))
                transactions = cur.fetchall()
        
        csv_lines = ['ID,Telegram ID,Username,Nombre,Tipo,Monto,Estado,TX Hash,Fecha']
        for tx in transactions:
            csv_lines.append(','.join([
                str(tx.get('id', '')),
                str(tx.get('telegram_id', '')),
                str(tx.get('username', '') or ''),
                str(tx.get('first_name', '') or ''),
                str(tx.get('transaction_type', '')),
                str(tx.get('amount', 0)),
                str(tx.get('status', '')),
                str(tx.get('tx_hash', '') or ''),
                str(tx.get('created_at', '') or '')
            ]))
        
        return jsonify({
            'success': True,
            'csv': '\n'.join(csv_lines),
            'filename': f'estadisticas_{date_from}_{date_to}.csv'
        })
        
    except Exception as e:
        logger.error(f"Error exporting period stats: {e}")
        return jsonify({'success': False, 'error': 'Error al exportar'}), 500


# ============================================================
# ADMIN LOGS ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================

def log_admin_action(admin_id, admin_name, action_type, target_type=None, target_id=None, description=None, metadata=None):
    """Helper function to log admin actions."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent', '')[:500] if request else None
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO admin_logs (admin_id, admin_name, action_type, target_type, target_id, description, ip_address, user_agent, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (admin_id, admin_name, action_type, target_type, target_id, description, ip_address, user_agent, json.dumps(metadata) if metadata else None))
            conn.commit()
    except Exception as e:
        logger.error(f"Error logging admin action: {e}")


@admin_bp.route('/logs/admin', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_admin_logs():
    """Admin: Obtener logs de acciones de administradores."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'logs': [], 'total': 0, 'actionTypes': []})
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('per_page', request.args.get('limit', 50))), 100)
        action_type = request.args.get('action_type', '')
        search = request.args.get('search', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT * FROM admin_logs WHERE 1=1"
                count_query = "SELECT COUNT(*) FROM admin_logs WHERE 1=1"
                params = []
                count_params = []
                
                if action_type:
                    query += " AND action_type = %s"
                    count_query += " AND action_type = %s"
                    params.append(action_type)
                    count_params.append(action_type)
                
                if search:
                    query += " AND (admin_name ILIKE %s OR description ILIKE %s OR target_id::text ILIKE %s)"
                    count_query += " AND (admin_name ILIKE %s OR description ILIKE %s OR target_id::text ILIKE %s)"
                    search_pattern = f'%{search}%'
                    params.extend([search_pattern, search_pattern, search_pattern])
                    count_params.extend([search_pattern, search_pattern, search_pattern])
                
                if date_from:
                    query += " AND created_at >= %s"
                    count_query += " AND created_at >= %s"
                    params.append(date_from)
                    count_params.append(date_from)
                
                if date_to:
                    query += " AND created_at <= %s::date + INTERVAL '1 day'"
                    count_query += " AND created_at <= %s::date + INTERVAL '1 day'"
                    params.append(date_to)
                    count_params.append(date_to)
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()['count']
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                logs = cur.fetchall()
                
                for log in logs:
                    if log.get('created_at'):
                        log['created_at'] = log['created_at'].isoformat()
                
                cur.execute("""
                    SELECT action_type, COUNT(*) as count
                    FROM admin_logs
                    GROUP BY action_type
                    ORDER BY count DESC
                """)
                action_types = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'total': total,
                    'page': page,
                    'pages': (total + limit - 1) // limit if total > 0 else 1,
                    'actionTypes': action_types
                })
    
    except Exception as e:
        logger.error(f"Error getting admin logs: {e}")
        return jsonify({'success': True, 'logs': [], 'total': 0, 'actionTypes': []})


@admin_bp.route('/logs/security', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_security_logs():
    """Admin: Obtener logs de seguridad (intentos de login, actividad sospechosa)."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'logs': [], 'total': 0})
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        activity_type = request.args.get('activity_type', '')
        user_id = request.args.get('user_id', '')
        
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT * FROM security_activity_log WHERE 1=1"
                count_query = "SELECT COUNT(*) FROM security_activity_log WHERE 1=1"
                params = []
                count_params = []
                
                if activity_type:
                    query += " AND activity_type = %s"
                    count_query += " AND activity_type = %s"
                    params.append(activity_type)
                    count_params.append(activity_type)
                
                if user_id:
                    query += " AND user_id = %s"
                    count_query += " AND user_id = %s"
                    params.append(user_id)
                    count_params.append(user_id)
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()['count']
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                logs = []
                
                for row in cur.fetchall():
                    log_entry = dict(row)
                    if log_entry.get('created_at'):
                        log_entry['created_at'] = log_entry['created_at'].isoformat()
                    logs.append(log_entry)
                
                cur.execute("""
                    SELECT activity_type, COUNT(*) as count
                    FROM security_activity_log
                    GROUP BY activity_type
                    ORDER BY count DESC
                """)
                activity_types = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'total': total,
                    'page': page,
                    'pages': (total + limit - 1) // limit if total > 0 else 1,
                    'activityTypes': activity_types
                })
    
    except Exception as e:
        logger.error(f"Error getting security logs: {e}")
        return jsonify({'success': True, 'logs': [], 'total': 0})


@admin_bp.route('/logs/errors', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_error_logs():
    """Admin: Obtener logs de errores del sistema."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'logs': [], 'total': 0})
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('per_page', 50)), 100)
        error_level = request.args.get('level', '')
        is_resolved = request.args.get('resolved', '')
        search = request.args.get('search', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT * FROM system_errors WHERE 1=1"
                count_query = "SELECT COUNT(*) FROM system_errors WHERE 1=1"
                params = []
                count_params = []
                
                if error_level:
                    query += " AND error_level = %s"
                    count_query += " AND error_level = %s"
                    params.append(error_level)
                    count_params.append(error_level)
                
                if is_resolved != '':
                    resolved_bool = is_resolved.lower() == 'true'
                    query += " AND is_resolved = %s"
                    count_query += " AND is_resolved = %s"
                    params.append(resolved_bool)
                    count_params.append(resolved_bool)
                
                if search:
                    query += " AND (error_message ILIKE %s OR endpoint ILIKE %s)"
                    count_query += " AND (error_message ILIKE %s OR endpoint ILIKE %s)"
                    search_param = f'%{search}%'
                    params.extend([search_param, search_param])
                    count_params.extend([search_param, search_param])
                
                if date_from:
                    query += " AND created_at >= %s"
                    count_query += " AND created_at >= %s"
                    params.append(date_from)
                    count_params.append(date_from)
                
                if date_to:
                    query += " AND created_at <= %s::date + interval '1 day'"
                    count_query += " AND created_at <= %s::date + interval '1 day'"
                    params.append(date_to)
                    count_params.append(date_to)
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()['count']
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                logs = []
                
                for row in cur.fetchall():
                    log_entry = dict(row)
                    if log_entry.get('created_at'):
                        log_entry['created_at'] = log_entry['created_at'].isoformat()
                    if log_entry.get('resolved_at'):
                        log_entry['resolved_at'] = log_entry['resolved_at'].isoformat()
                    logs.append(log_entry)
                
                cur.execute("""
                    SELECT error_level, COUNT(*) as count
                    FROM system_errors
                    GROUP BY error_level
                    ORDER BY count DESC
                """)
                error_levels = [dict(row) for row in cur.fetchall()]
                
                cur.execute("SELECT COUNT(*) FROM system_errors WHERE is_resolved = FALSE")
                unresolved_count = cur.fetchone()['count']
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'total': total,
                    'page': page,
                    'pages': (total + limit - 1) // limit if total > 0 else 1,
                    'errorLevels': error_levels,
                    'unresolvedCount': unresolved_count
                })
    
    except Exception as e:
        logger.error(f"Error getting error logs: {e}")
        return jsonify({'success': True, 'logs': [], 'total': 0})


@admin_bp.route('/logs/errors/<int:error_id>/resolve', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_resolve_error(error_id):
    """Admin: Marcar error como resuelto."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 503
        
        user_id = getattr(request, 'user_id', '0')
        user_data = getattr(request, 'user_data', {})
        admin_name = user_data.get('first_name', 'Admin')
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE system_errors
                    SET is_resolved = TRUE, resolved_by = %s, resolved_at = NOW()
                    WHERE id = %s
                """, (admin_name, error_id))
            conn.commit()
        
        log_admin_action(user_id, admin_name, 'error_resolve', 'system_error', str(error_id), 'Marked error as resolved')
        
        return jsonify({'success': True, 'message': 'Error marcado como resuelto'})
    
    except Exception as e:
        logger.error(f"Error resolving system error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/logs/logins', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_login_logs():
    """Admin: Obtener logs de intentos de login."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'logs': [], 'total': 0})
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('per_page', 50)), 100)
        status = request.args.get('status', '')
        search = request.args.get('search', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """SELECT * FROM security_activity_log 
                           WHERE activity_type IN ('LOGIN_SUCCESS', 'LOGIN_FAILED', 'WALLET_ACCESS', 
                                                   'WALLET_FAILED_ATTEMPT', 'WALLET_LOCKOUT', 'IP_BLOCKED')"""
                count_query = """SELECT COUNT(*) FROM security_activity_log 
                                WHERE activity_type IN ('LOGIN_SUCCESS', 'LOGIN_FAILED', 'WALLET_ACCESS', 
                                                        'WALLET_FAILED_ATTEMPT', 'WALLET_LOCKOUT', 'IP_BLOCKED')"""
                params = []
                count_params = []
                
                if status == 'success':
                    query += " AND activity_type IN ('LOGIN_SUCCESS', 'WALLET_ACCESS')"
                    count_query += " AND activity_type IN ('LOGIN_SUCCESS', 'WALLET_ACCESS')"
                elif status == 'failed':
                    query += " AND activity_type IN ('LOGIN_FAILED', 'WALLET_FAILED_ATTEMPT')"
                    count_query += " AND activity_type IN ('LOGIN_FAILED', 'WALLET_FAILED_ATTEMPT')"
                elif status == 'blocked':
                    query += " AND activity_type IN ('WALLET_LOCKOUT', 'IP_BLOCKED')"
                    count_query += " AND activity_type IN ('WALLET_LOCKOUT', 'IP_BLOCKED')"
                
                if search:
                    query += " AND (user_id ILIKE %s OR ip_address ILIKE %s)"
                    count_query += " AND (user_id ILIKE %s OR ip_address ILIKE %s)"
                    search_param = f'%{search}%'
                    params.extend([search_param, search_param])
                    count_params.extend([search_param, search_param])
                
                if date_from:
                    query += " AND created_at >= %s"
                    count_query += " AND created_at >= %s"
                    params.append(date_from)
                    count_params.append(date_from)
                
                if date_to:
                    query += " AND created_at <= %s::date + interval '1 day'"
                    count_query += " AND created_at <= %s::date + interval '1 day'"
                    params.append(date_to)
                    count_params.append(date_to)
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()['count']
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                logs = []
                
                for row in cur.fetchall():
                    log_entry = dict(row)
                    if log_entry.get('created_at'):
                        log_entry['created_at'] = log_entry['created_at'].isoformat()
                    logs.append(log_entry)
                
                cur.execute("""
                    SELECT activity_type, COUNT(*) as count
                    FROM security_activity_log
                    WHERE activity_type IN ('LOGIN_SUCCESS', 'LOGIN_FAILED', 'WALLET_ACCESS', 
                                           'WALLET_FAILED_ATTEMPT', 'WALLET_LOCKOUT', 'IP_BLOCKED')
                    GROUP BY activity_type
                    ORDER BY count DESC
                """)
                login_stats = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT ip_address, COUNT(*) as attempts
                    FROM security_activity_log
                    WHERE activity_type IN ('LOGIN_FAILED', 'WALLET_FAILED_ATTEMPT')
                    AND created_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY ip_address
                    HAVING COUNT(*) >= 5
                    ORDER BY attempts DESC
                    LIMIT 10
                """)
                suspicious_ips = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'total': total,
                    'page': page,
                    'pages': (total + limit - 1) // limit if total > 0 else 1,
                    'loginStats': login_stats,
                    'suspiciousIPs': suspicious_ips
                })
    
    except Exception as e:
        logger.error(f"Error getting login logs: {e}")
        return jsonify({'success': True, 'logs': [], 'total': 0})


@admin_bp.route('/logs/config-history', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_config_history():
    """Admin: Obtener historial de cambios de configuracion."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'logs': [], 'total': 0})
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('per_page', 50)), 100)
        config_key = request.args.get('key', '')
        search = request.args.get('search', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT * FROM config_history WHERE 1=1"
                count_query = "SELECT COUNT(*) FROM config_history WHERE 1=1"
                params = []
                count_params = []
                
                if config_key:
                    query += " AND config_key = %s"
                    count_query += " AND config_key = %s"
                    params.append(config_key)
                    count_params.append(config_key)
                
                if search:
                    query += " AND (config_key ILIKE %s OR changed_by_name ILIKE %s)"
                    count_query += " AND (config_key ILIKE %s OR changed_by_name ILIKE %s)"
                    search_param = f'%{search}%'
                    params.extend([search_param, search_param])
                    count_params.extend([search_param, search_param])
                
                if date_from:
                    query += " AND created_at >= %s"
                    count_query += " AND created_at >= %s"
                    params.append(date_from)
                    count_params.append(date_from)
                
                if date_to:
                    query += " AND created_at <= %s::date + interval '1 day'"
                    count_query += " AND created_at <= %s::date + interval '1 day'"
                    params.append(date_to)
                    count_params.append(date_to)
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()['count']
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                logs = []
                
                for row in cur.fetchall():
                    log_entry = dict(row)
                    if log_entry.get('created_at'):
                        log_entry['created_at'] = log_entry['created_at'].isoformat()
                    logs.append(log_entry)
                
                cur.execute("""
                    SELECT config_key, COUNT(*) as count
                    FROM config_history
                    GROUP BY config_key
                    ORDER BY count DESC
                """)
                config_keys = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'total': total,
                    'page': page,
                    'pages': (total + limit - 1) // limit if total > 0 else 1,
                    'configKeys': config_keys
                })
    
    except Exception as e:
        logger.error(f"Error getting config history: {e}")
        return jsonify({'success': True, 'logs': [], 'total': 0})


@admin_bp.route('/logs/export', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_export_logs():
    """Admin: Exportar logs a CSV o JSON."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        log_type = request.args.get('type', 'admin')
        export_format = request.args.get('format', 'csv')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        days = int(request.args.get('days', 30))
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if log_type == 'admin':
                    query = """
                        SELECT id, admin_id, admin_name, action_type, target_type, 
                               target_id, description, ip_address, created_at
                        FROM admin_logs WHERE 1=1
                    """
                    params = []
                    if date_from:
                        query += " AND created_at >= %s"
                        params.append(date_from)
                    if date_to:
                        query += " AND created_at <= %s::date + INTERVAL '1 day'"
                        params.append(date_to)
                    if not date_from and not date_to:
                        query += " AND created_at >= NOW() - INTERVAL '%s days'"
                        params.append(days)
                    query += " ORDER BY created_at DESC"
                    cur.execute(query, params)
                elif log_type == 'security':
                    query = """
                        SELECT id, user_id, activity_type, description, 
                               device_id, ip_address, created_at
                        FROM security_activity_log WHERE 1=1
                    """
                    params = []
                    if date_from:
                        query += " AND created_at >= %s"
                        params.append(date_from)
                    if date_to:
                        query += " AND created_at <= %s::date + INTERVAL '1 day'"
                        params.append(date_to)
                    if not date_from and not date_to:
                        query += " AND created_at >= NOW() - INTERVAL '%s days'"
                        params.append(days)
                    query += " ORDER BY created_at DESC"
                    cur.execute(query, params)
                elif log_type == 'client':
                    query = """
                        SELECT id, user_id, log_type, action, is_mobile, 
                               is_telegram, ip, created_at
                        FROM client_logs WHERE 1=1
                    """
                    params = []
                    if date_from:
                        query += " AND created_at >= %s"
                        params.append(date_from)
                    if date_to:
                        query += " AND created_at <= %s::date + INTERVAL '1 day'"
                        params.append(date_to)
                    if not date_from and not date_to:
                        query += " AND created_at >= NOW() - INTERVAL '%s days'"
                        params.append(days)
                    query += " ORDER BY created_at DESC"
                    cur.execute(query, params)
                elif log_type == 'errors':
                    query = """
                        SELECT id, error_level, endpoint, error_message, 
                               user_id, ip_address, is_resolved, created_at
                        FROM system_errors WHERE 1=1
                    """
                    params = []
                    if date_from:
                        query += " AND created_at >= %s"
                        params.append(date_from)
                    if date_to:
                        query += " AND created_at <= %s::date + INTERVAL '1 day'"
                        params.append(date_to)
                    if not date_from and not date_to:
                        query += " AND created_at >= NOW() - INTERVAL '%s days'"
                        params.append(days)
                    query += " ORDER BY created_at DESC"
                    cur.execute(query, params)
                elif log_type == 'logins':
                    query = """
                        SELECT id, user_id, activity_type, description, 
                               device_id, ip_address, created_at
                        FROM security_activity_log 
                        WHERE activity_type IN ('LOGIN_SUCCESS', 'LOGIN_FAILED') 
                    """
                    params = []
                    if date_from:
                        query += " AND created_at >= %s"
                        params.append(date_from)
                    if date_to:
                        query += " AND created_at <= %s::date + INTERVAL '1 day'"
                        params.append(date_to)
                    if not date_from and not date_to:
                        query += " AND created_at >= NOW() - INTERVAL '%s days'"
                        params.append(days)
                    query += " ORDER BY created_at DESC"
                    cur.execute(query, params)
                elif log_type == 'config':
                    query = """
                        SELECT id, config_key, old_value, new_value, 
                               changed_by_name, ip_address, description, created_at
                        FROM config_history WHERE 1=1
                    """
                    params = []
                    if date_from:
                        query += " AND created_at >= %s"
                        params.append(date_from)
                    if date_to:
                        query += " AND created_at <= %s::date + INTERVAL '1 day'"
                        params.append(date_to)
                    if not date_from and not date_to:
                        query += " AND created_at >= NOW() - INTERVAL '%s days'"
                        params.append(days)
                    query += " ORDER BY created_at DESC"
                    cur.execute(query, params)
                else:
                    return jsonify({'success': False, 'error': 'Tipo de log invalido'}), 400
                
                logs = [dict(row) for row in cur.fetchall()]
                
                for log in logs:
                    if log.get('created_at'):
                        log['created_at'] = log['created_at'].isoformat()
                
                if export_format == 'json':
                    return Response(
                        json.dumps(logs, indent=2, ensure_ascii=False),
                        mimetype='application/json',
                        headers={'Content-Disposition': f'attachment; filename={log_type}_logs.json'}
                    )
                else:
                    if not logs:
                        return Response(
                            '',
                            mimetype='text/csv',
                            headers={'Content-Disposition': f'attachment; filename={log_type}_logs.csv'}
                        )
                    
                    output = io.StringIO()
                    headers = list(logs[0].keys())
                    output.write(','.join(headers) + '\n')
                    
                    for log in logs:
                        row_values = []
                        for h in headers:
                            value = log.get(h, '')
                            if isinstance(value, str) and (',' in value or '"' in value or '\n' in value):
                                value = '"' + value.replace('"', '""') + '"'
                            row_values.append(str(value) if value is not None else '')
                        output.write(','.join(row_values) + '\n')
                    
                    return Response(
                        output.getvalue(),
                        mimetype='text/csv',
                        headers={'Content-Disposition': f'attachment; filename={log_type}_logs.csv'}
                    )
    
    except Exception as e:
        logger.error(f"Error exporting logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ADMIN CONFIG ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================

def log_config_change(config_key, old_value, new_value, changed_by_id, changed_by_name, description=None):
    """Helper function to log configuration changes."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return
        ip_address = request.remote_addr if request else None
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO config_history (config_key, old_value, new_value, changed_by_id, changed_by_name, ip_address, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (config_key, str(old_value) if old_value is not None else None, str(new_value), changed_by_id, changed_by_name, ip_address, description))
            conn.commit()
    except Exception as e:
        logger.error(f"Error logging config change: {e}")


@admin_bp.route('/config', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_config():
    """Admin: Obtener configuracion del sistema."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'config': {}})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT config_key, config_value, config_type FROM system_config")
                rows = cur.fetchall()
                
                config = {}
                for row in rows:
                    value = row['config_value']
                    if row['config_type'] == 'number':
                        value = float(value) if '.' in str(value) else int(value)
                    elif row['config_type'] == 'boolean':
                        value = value.lower() == 'true'
                    config[row['config_key']] = value
                
                return jsonify({'success': True, 'config': config})
    
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({'success': True, 'config': {}})


@admin_bp.route('/config', methods=['POST'])
@require_telegram_auth
@require_owner  
def admin_update_config():
    """Admin: Actualizar configuracion del sistema."""
    try:
        data = request.get_json()
        user_id = getattr(request, 'user_id', '0')
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                for key, value in data.items():
                    cur.execute("""
                        UPDATE system_config 
                        SET config_value = %s, updated_at = NOW(), updated_by = %s
                        WHERE config_key = %s
                    """, (str(value), user_id, key))
            conn.commit()
        
        log_admin_action(user_id, 'Admin', 'config_update', 'system_config', None, 
                        f"Updated config: {list(data.keys())}", {'changes': data})
        
        return jsonify({'success': True, 'message': 'Configuracion actualizada'})
    
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ADMIN ANALYTICS ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================

@admin_bp.route('/analytics/users', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_analytics_users():
    """Admin: Estadisticas de usuarios para analytics."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT COUNT(DISTINCT user_id) as count 
                    FROM security_activity_log 
                    WHERE created_at >= CURRENT_DATE
                """)
                active_today = cur.fetchone()['count'] or 0
                
                cur.execute("""
                    SELECT COUNT(DISTINCT user_id) as count 
                    FROM security_activity_log 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                """)
                active_week = cur.fetchone()['count'] or 0
                
                cur.execute("""
                    SELECT COUNT(DISTINCT user_id) as count 
                    FROM security_activity_log 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                """)
                active_month = cur.fetchone()['count'] or 0
                
                cur.execute("SELECT COUNT(*) as count FROM users")
                total_users = cur.fetchone()['count'] or 0
                
                cur.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM users
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """)
                new_users_chart = [{'date': row['date'].isoformat(), 'count': row['count']} for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT COUNT(DISTINCT user_id) as count
                    FROM security_activity_log
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    AND user_id IN (
                        SELECT DISTINCT user_id FROM security_activity_log
                        WHERE created_at < CURRENT_DATE - INTERVAL '7 days'
                        AND created_at >= CURRENT_DATE - INTERVAL '14 days'
                    )
                """)
                returning_users = cur.fetchone()['count'] or 0
                retention_rate = round((returning_users / max(active_week, 1)) * 100, 1)
                
                users_by_country = [{'country': 'No disponible', 'count': total_users}]
                
                cur.execute("""
                    SELECT 
                        CASE 
                            WHEN user_agent ILIKE '%android%' THEN 'Android'
                            WHEN user_agent ILIKE '%iphone%' OR user_agent ILIKE '%ipad%' THEN 'iOS'
                            WHEN user_agent ILIKE '%windows%' THEN 'Windows'
                            WHEN user_agent ILIKE '%macintosh%' THEN 'Mac'
                            WHEN user_agent ILIKE '%linux%' THEN 'Linux'
                            ELSE 'Otro'
                        END as device,
                        COUNT(DISTINCT user_id) as count
                    FROM security_activity_log
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY device
                    ORDER BY count DESC
                """)
                users_by_device = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'activeToday': active_today,
                    'activeWeek': active_week,
                    'activeMonth': active_month,
                    'totalUsers': total_users,
                    'newUsersChart': new_users_chart,
                    'retentionRate': retention_rate,
                    'returningUsers': returning_users,
                    'usersByCountry': users_by_country,
                    'usersByDevice': users_by_device
                })
    
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/analytics/usage', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_analytics_usage():
    """Admin: Estadisticas de uso de la app."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT activity_type as section, COUNT(*) as count
                    FROM security_activity_log
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY activity_type
                    ORDER BY count DESC
                    LIMIT 10
                """)
                top_sections = [dict(row) for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT EXTRACT(HOUR FROM created_at)::int as hour, COUNT(*) as count
                    FROM security_activity_log
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY hour
                    ORDER BY hour ASC
                """)
                hourly_activity = [{'hour': row['hour'], 'count': row['count']} for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT TO_CHAR(created_at, 'Day') as day_name, 
                           EXTRACT(DOW FROM created_at)::int as day_num,
                           COUNT(*) as count
                    FROM security_activity_log
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY day_name, day_num
                    ORDER BY day_num ASC
                """)
                daily_activity = [{'day': row['day_name'].strip(), 'count': row['count']} for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM security_activity_log
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """)
                activity_chart = [{'date': row['date'].isoformat(), 'count': row['count']} for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'topSections': top_sections,
                    'hourlyActivity': hourly_activity,
                    'dailyActivity': daily_activity,
                    'activityChart': activity_chart
                })
    
    except Exception as e:
        logger.error(f"Error getting usage analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/analytics/conversion', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_analytics_conversion():
    """Admin: Metricas de conversion."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 503
        
        import psycopg2.errors
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) as count FROM users")
                total_users = cur.fetchone()['count'] or 0
                
                cur.execute("""
                    SELECT COUNT(DISTINCT user_id) as count
                    FROM b3c_purchases
                    WHERE status = 'completed'
                """)
                users_purchased_b3c = cur.fetchone()['count'] or 0
                
                try:
                    cur.execute("""
                        SELECT COUNT(DISTINCT user_id) as count
                        FROM virtual_number_orders
                    """)
                    users_used_vn = cur.fetchone()['count'] or 0
                except Exception:
                    users_used_vn = 0
                
                try:
                    cur.execute("""
                        SELECT COUNT(DISTINCT user_id) as count
                        FROM posts
                        WHERE is_hidden = false
                    """)
                    users_published = cur.fetchone()['count'] or 0
                except Exception:
                    users_published = 0
                
                cur.execute("""
                    SELECT COUNT(*) as count
                    FROM users
                    WHERE wallet_address IS NOT NULL AND wallet_address != ''
                """)
                users_with_wallet = cur.fetchone()['count'] or 0
                
                b3c_rate = round((users_purchased_b3c / max(total_users, 1)) * 100, 1)
                vn_rate = round((users_used_vn / max(total_users, 1)) * 100, 1)
                publish_rate = round((users_published / max(total_users, 1)) * 100, 1)
                wallet_rate = round((users_with_wallet / max(total_users, 1)) * 100, 1)
                
                funnel = [
                    {'stage': 'Registrados', 'count': total_users, 'rate': 100},
                    {'stage': 'Wallet conectada', 'count': users_with_wallet, 'rate': wallet_rate},
                    {'stage': 'Compraron B3C', 'count': users_purchased_b3c, 'rate': b3c_rate},
                    {'stage': 'Publicaron contenido', 'count': users_published, 'rate': publish_rate},
                    {'stage': 'Usaron VN', 'count': users_used_vn, 'rate': vn_rate}
                ]
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount_ton), 0) as total_ton
                    FROM b3c_purchases
                    WHERE status = 'completed'
                """)
                total_revenue_ton = float(cur.fetchone()['total_ton'] or 0)
                
                return jsonify({
                    'success': True,
                    'totalUsers': total_users,
                    'usersPurchasedB3C': users_purchased_b3c,
                    'usersUsedVN': users_used_vn,
                    'usersPublished': users_published,
                    'usersWithWallet': users_with_wallet,
                    'b3cConversionRate': b3c_rate,
                    'vnConversionRate': vn_rate,
                    'publishRate': publish_rate,
                    'walletRate': wallet_rate,
                    'funnel': funnel,
                    'totalRevenueTON': total_revenue_ton
                })
    
    except Exception as e:
        logger.error(f"Error getting conversion analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ADMIN SUPPORT ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================

@admin_bp.route('/support/tickets', methods=['GET'])
@require_telegram_auth
@require_owner
def get_support_tickets():
    """Get all support tickets with filters and pagination"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({
                'success': True,
                'tickets': [],
                'total': 0,
                'page': 1,
                'per_page': 20,
                'pages': 0,
                'stats': {'new_count': 0, 'in_progress_count': 0, 'resolved_count': 0, 'urgent_count': 0}
            })
        
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                where_clauses = []
                params = []
                
                if status:
                    where_clauses.append("t.status = %s")
                    params.append(status)
                
                if priority:
                    where_clauses.append("t.priority = %s")
                    params.append(priority)
                
                if search:
                    where_clauses.append("(t.subject ILIKE %s OR u.username ILIKE %s)")
                    params.extend([f'%{search}%', f'%{search}%'])
                
                where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                cur.execute(f"""
                    SELECT t.*, u.username, u.first_name, u.last_name,
                           (SELECT COUNT(*) FROM ticket_messages WHERE ticket_id = t.id) as message_count
                    FROM support_tickets t
                    LEFT JOIN users u ON t.user_id = u.id
                    WHERE {where_sql}
                    ORDER BY 
                        CASE t.priority 
                            WHEN 'urgent' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            ELSE 4 
                        END,
                        t.created_at DESC
                    LIMIT %s OFFSET %s
                """, params + [per_page, offset])
                tickets = cur.fetchall()
                
                cur.execute(f"""
                    SELECT COUNT(*) as total FROM support_tickets t
                    LEFT JOIN users u ON t.user_id = u.id
                    WHERE {where_sql}
                """, params)
                total = cur.fetchone()['total']
                
                cur.execute("""
                    SELECT 
                        COUNT(*) FILTER (WHERE status = 'new') as new_count,
                        COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_count,
                        COUNT(*) FILTER (WHERE status = 'resolved') as resolved_count,
                        COUNT(*) FILTER (WHERE priority = 'urgent' AND status NOT IN ('closed', 'resolved')) as urgent_count
                    FROM support_tickets
                """)
                stats = cur.fetchone()
                
                return jsonify({
                    'success': True,
                    'tickets': [dict(t) for t in tickets],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'pages': (total + per_page - 1) // per_page,
                    'stats': dict(stats)
                })
                
    except Exception as e:
        logger.error(f"Error getting support tickets: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/support/tickets/<int:ticket_id>', methods=['GET'])
@require_telegram_auth
@require_owner
def get_ticket_detail(ticket_id):
    """Get single ticket with messages"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT t.*, u.username, u.first_name, u.last_name, u.telegram_id
                    FROM support_tickets t
                    LEFT JOIN users u ON t.user_id = u.id
                    WHERE t.id = %s
                """, (ticket_id,))
                ticket = cur.fetchone()
                
                if not ticket:
                    return jsonify({'success': False, 'error': 'Ticket not found'}), 404
                
                cur.execute("""
                    SELECT tm.*, 
                           CASE WHEN tm.is_admin THEN 'Admin' ELSE u.username END as sender_name
                    FROM ticket_messages tm
                    LEFT JOIN users u ON tm.sender_id = u.id
                    WHERE tm.ticket_id = %s
                    ORDER BY tm.created_at ASC
                """, (ticket_id,))
                messages = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'ticket': dict(ticket),
                    'messages': [dict(m) for m in messages]
                })
                
    except Exception as e:
        logger.error(f"Error getting ticket detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/support/tickets/<int:ticket_id>', methods=['PUT'])
@require_telegram_auth
@require_owner
def update_ticket(ticket_id):
    """Update ticket status or priority"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        data = request.json
        status = data.get('status')
        priority = data.get('priority')
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                updates = []
                params = []
                
                if status:
                    updates.append("status = %s")
                    params.append(status)
                    if status == 'closed':
                        updates.append("closed_at = NOW()")
                
                if priority:
                    updates.append("priority = %s")
                    params.append(priority)
                
                updates.append("updated_at = NOW()")
                params.append(ticket_id)
                
                cur.execute(f"""
                    UPDATE support_tickets
                    SET {', '.join(updates)}
                    WHERE id = %s
                    RETURNING *
                """, params)
                ticket = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'ticket': dict(ticket)
                })
                
    except Exception as e:
        logger.error(f"Error updating ticket: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/support/tickets/<int:ticket_id>/reply', methods=['POST'])
@require_telegram_auth
@require_owner
def reply_to_ticket(ticket_id):
    """Send reply to ticket"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        data = request.json
        message = data.get('message', '').strip()
        attachment_url = data.get('attachment_url')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        admin_id = getattr(request, 'user_id', 0)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO ticket_messages (ticket_id, sender_id, message, is_admin, attachment_url)
                    VALUES (%s, %s, %s, true, %s)
                    RETURNING *
                """, (ticket_id, admin_id, message, attachment_url))
                new_message = cur.fetchone()
                
                cur.execute("""
                    UPDATE support_tickets
                    SET status = CASE WHEN status = 'new' THEN 'in_progress' ELSE status END,
                        updated_at = NOW()
                    WHERE id = %s
                """, (ticket_id,))
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': dict(new_message)
                })
                
    except Exception as e:
        logger.error(f"Error replying to ticket: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/support/templates', methods=['GET'])
@require_telegram_auth
@require_owner
def get_response_templates():
    """Get response templates"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'templates': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM response_templates
                    WHERE is_active = true
                    ORDER BY name ASC
                """)
                templates = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'templates': [dict(t) for t in templates]
                })
                
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/support/templates', methods=['POST'])
@require_telegram_auth
@require_owner
def create_response_template():
    """Create new response template"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        data = request.json
        name = data.get('name', '').strip()
        content = data.get('content', '').strip()
        
        if not name or not content:
            return jsonify({'success': False, 'error': 'Name and content are required'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO response_templates (name, content)
                    VALUES (%s, %s)
                    RETURNING *
                """, (name, content))
                template = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'template': dict(template)
                })
                
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ADMIN FAQ ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================

@admin_bp.route('/faq', methods=['GET'])
@require_telegram_auth
@require_owner
def get_faqs():
    """Get all FAQs with filters"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'faqs': []})
        
        category = request.args.get('category', '')
        status = request.args.get('status', '')
        search = request.args.get('search', '')
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                where_clauses = []
                params = []
                
                if category:
                    where_clauses.append("category = %s")
                    params.append(category)
                
                if status == 'published':
                    where_clauses.append("is_published = true")
                elif status == 'draft':
                    where_clauses.append("is_published = false")
                
                if search:
                    where_clauses.append("(question ILIKE %s OR answer ILIKE %s)")
                    params.extend([f'%{search}%', f'%{search}%'])
                
                where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                cur.execute(f"""
                    SELECT * FROM faqs
                    WHERE {where_sql}
                    ORDER BY display_order ASC, created_at DESC
                """, params)
                faqs = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'faqs': [dict(f) for f in faqs]
                })
                
    except Exception as e:
        logger.error(f"Error getting FAQs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/faq', methods=['POST'])
@require_telegram_auth
@require_owner
def create_faq():
    """Create new FAQ"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        data = request.json
        question = data.get('question', '').strip()
        answer = data.get('answer', '').strip()
        category = data.get('category', 'general')
        display_order = data.get('display_order', 0)
        is_published = data.get('is_published', True)
        
        if not question or not answer:
            return jsonify({'success': False, 'error': 'Question and answer are required'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO faqs (question, answer, category, display_order, is_published)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                """, (question, answer, category, display_order, is_published))
                faq = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'faq': dict(faq)
                })
                
    except Exception as e:
        logger.error(f"Error creating FAQ: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/faq/<int:faq_id>', methods=['PUT'])
@require_telegram_auth
@require_owner
def update_faq(faq_id):
    """Update FAQ"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        data = request.json
        question = data.get('question', '').strip()
        answer = data.get('answer', '').strip()
        category = data.get('category', 'general')
        display_order = data.get('display_order', 0)
        is_published = data.get('is_published', True)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    UPDATE faqs
                    SET question = %s, answer = %s, category = %s, 
                        display_order = %s, is_published = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING *
                """, (question, answer, category, display_order, is_published, faq_id))
                faq = cur.fetchone()
                conn.commit()
                
                if not faq:
                    return jsonify({'success': False, 'error': 'FAQ not found'}), 404
                
                return jsonify({
                    'success': True,
                    'faq': dict(faq)
                })
                
    except Exception as e:
        logger.error(f"Error updating FAQ: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/faq/<int:faq_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def delete_faq(faq_id):
    """Delete FAQ"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM faqs WHERE id = %s", (faq_id,))
                conn.commit()
                
                return jsonify({'success': True})
                
    except Exception as e:
        logger.error(f"Error deleting FAQ: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ADMIN MESSAGES ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================

@admin_bp.route('/messages', methods=['GET'])
@require_telegram_auth
@require_owner
def get_mass_messages():
    """Get mass messages history"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'messages': [], 'total': 0, 'page': 1, 'per_page': 20})
        
        status = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                where_clause = ""
                params = []
                
                if status == 'sent':
                    where_clause = "WHERE status = 'sent'"
                elif status == 'scheduled':
                    where_clause = "WHERE status = 'scheduled'"
                elif status == 'draft':
                    where_clause = "WHERE status = 'draft'"
                
                cur.execute(f"""
                    SELECT m.*,
                           (SELECT COUNT(*) FROM mass_message_recipients WHERE message_id = m.id) as recipient_count,
                           (SELECT COUNT(*) FROM mass_message_recipients WHERE message_id = m.id AND is_delivered = true) as delivered_count
                    FROM mass_messages m
                    {where_clause}
                    ORDER BY m.created_at DESC
                    LIMIT %s OFFSET %s
                """, [per_page, offset])
                messages = cur.fetchall()
                
                cur.execute(f"SELECT COUNT(*) as total FROM mass_messages {where_clause}")
                total = cur.fetchone()['total']
                
                return jsonify({
                    'success': True,
                    'messages': [dict(m) for m in messages],
                    'total': total,
                    'page': page,
                    'per_page': per_page
                })
                
    except Exception as e:
        logger.error(f"Error getting mass messages: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/messages', methods=['POST'])
@require_telegram_auth
@require_owner
def send_mass_message():
    """Create and send mass message"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        data = request.json
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        recipient_type = data.get('recipient_type', 'all')
        specific_users = data.get('specific_users', '')
        send_type = data.get('send_type', 'now')
        scheduled_at = data.get('scheduled_at')
        msg_type = data.get('msg_type', 'info')
        
        if not title or not content:
            return jsonify({'success': False, 'error': 'Title and content are required'}), 400
        
        admin_id = getattr(request, 'user_id', 0)
        user_ids = []
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                status = 'scheduled' if send_type == 'scheduled' else 'sent'
                
                cur.execute(f"""
                    INSERT INTO mass_messages (title, content, message_type, recipient_filter, 
                                               status, scheduled_at, sent_at, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, {'NOW()' if send_type == 'now' else 'NULL'}, %s)
                    RETURNING *
                """, (title, content, msg_type, recipient_type, status, 
                      scheduled_at if send_type == 'scheduled' else None, admin_id))
                message = cur.fetchone()
                message_id = message['id']
                
                if send_type == 'now':
                    if recipient_type == 'all':
                        cur.execute("SELECT id FROM users WHERE is_banned = false")
                        user_ids = [row['id'] for row in cur.fetchall()]
                    elif recipient_type == 'active':
                        cur.execute("""
                            SELECT id FROM users 
                            WHERE is_banned = false AND last_active > NOW() - INTERVAL '7 days'
                        """)
                        user_ids = [row['id'] for row in cur.fetchall()]
                    elif recipient_type == 'premium':
                        cur.execute("""
                            SELECT id FROM users 
                            WHERE is_banned = false AND is_premium = true
                        """)
                        user_ids = [row['id'] for row in cur.fetchall()]
                    elif recipient_type == 'specific' and specific_users:
                        specific_ids = [int(x.strip()) for x in specific_users.split(',') if x.strip().isdigit()]
                        if specific_ids:
                            cur.execute("""
                                SELECT id FROM users WHERE id = ANY(%s) AND is_banned = false
                            """, (specific_ids,))
                            user_ids = [row['id'] for row in cur.fetchall()]
                    
                    for user_id in user_ids:
                        cur.execute("""
                            INSERT INTO mass_message_recipients (message_id, user_id, is_delivered)
                            VALUES (%s, %s, true)
                        """, (message_id, user_id))
                        
                        cur.execute("""
                            INSERT INTO user_notifications (user_id, title, message, notification_type, is_read)
                            VALUES (%s, %s, %s, %s, false)
                        """, (user_id, title, content, msg_type))
                    
                    cur.execute("""
                        UPDATE mass_messages SET recipients_count = %s WHERE id = %s
                    """, (len(user_ids), message_id))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': dict(message),
                    'recipients_count': len(user_ids) if send_type == 'now' else 0
                })
                
    except Exception as e:
        logger.error(f"Error sending mass message: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/messages/scheduled', methods=['GET'])
@require_telegram_auth
@require_owner
def get_scheduled_messages():
    """Get scheduled messages"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'messages': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM mass_messages
                    WHERE status = 'scheduled' AND scheduled_at > NOW()
                    ORDER BY scheduled_at ASC
                """)
                messages = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'messages': [dict(m) for m in messages]
                })
                
    except Exception as e:
        logger.error(f"Error getting scheduled messages: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/messages/<int:message_id>/cancel', methods=['POST'])
@require_telegram_auth
@require_owner
def cancel_scheduled_message(message_id):
    """Cancel scheduled message"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    UPDATE mass_messages
                    SET status = 'cancelled'
                    WHERE id = %s AND status = 'scheduled'
                    RETURNING *
                """, (message_id,))
                message = cur.fetchone()
                conn.commit()
                
                if not message:
                    return jsonify({'success': False, 'error': 'Message not found or already sent'}), 404
                
                return jsonify({
                    'success': True,
                    'message': dict(message)
                })
                
    except Exception as e:
        logger.error(f"Error cancelling message: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ENDPOINTS DE BLOCKED IPS, WALLET POOL Y SECRETS - Migrados 10 Diciembre 2025
# ============================================================

@admin_bp.route('/blocked-ips', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_blocked_ips():
    """Admin: Obtener lista de IPs bloqueadas."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'ips': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM blocked_ips 
                    WHERE is_active = true
                    ORDER BY blocked_at DESC
                """)
                ips = cur.fetchall()
                
                for ip in ips:
                    if ip.get('blocked_at'):
                        ip['blocked_at'] = ip['blocked_at'].isoformat()
                    if ip.get('expires_at'):
                        ip['expires_at'] = ip['expires_at'].isoformat()
                
                return jsonify({'success': True, 'ips': ips})
    
    except Exception as e:
        logger.error(f"Error getting blocked IPs: {e}")
        return jsonify({'success': True, 'ips': []})


@admin_bp.route('/blocked-ips', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_block_ip():
    """Admin: Bloquear una IP."""
    try:
        data = request.get_json()
        ip_address = data.get('ip_address', '').strip()
        reason = data.get('reason', '')
        is_permanent = data.get('is_permanent', False)
        user_id = getattr(request, 'user_id', '0')
        
        if not ip_address:
            return jsonify({'success': False, 'error': 'IP requerida'}), 400
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO blocked_ips (ip_address, reason, blocked_by, is_permanent)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (ip_address, reason, user_id, is_permanent))
            conn.commit()
        
        log_admin_action(user_id, 'Admin', 'ip_block', 'blocked_ips', ip_address, 
                        f"Blocked IP: {ip_address}", {'reason': reason, 'permanent': is_permanent})
        
        return jsonify({'success': True, 'message': f'IP {ip_address} bloqueada'})
    
    except Exception as e:
        logger.error(f"Error blocking IP: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/blocked-ips/<int:ip_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def admin_unblock_ip(ip_id):
    """Admin: Desbloquear una IP."""
    try:
        user_id = getattr(request, 'user_id', '0')
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT ip_address FROM blocked_ips WHERE id = %s", (ip_id,))
                row = cur.fetchone()
                ip_address = row['ip_address'] if row else 'Unknown'
                
                cur.execute("UPDATE blocked_ips SET is_active = false WHERE id = %s", (ip_id,))
            conn.commit()
        
        log_admin_action(user_id, 'Admin', 'ip_unblock', 'blocked_ips', str(ip_id), 
                        f"Unblocked IP: {ip_address}")
        
        return jsonify({'success': True, 'message': 'IP desbloqueada'})
    
    except Exception as e:
        logger.error(f"Error unblocking IP: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/wallet-pool/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_wallet_pool_stats():
    """Admin: Obtener estadisticas del pool de wallets."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) as total FROM deposit_wallets")
                total = cur.fetchone()['total']
                
                cur.execute("SELECT COUNT(*) as available FROM deposit_wallets WHERE status = 'available'")
                available = cur.fetchone()['available']
                
                cur.execute("SELECT COUNT(*) as assigned FROM deposit_wallets WHERE status = 'assigned'")
                assigned = cur.fetchone()['assigned']
                
                cur.execute("SELECT COUNT(*) as used FROM deposit_wallets WHERE status = 'used'")
                used = cur.fetchone()['used']
                
                cur.execute("SELECT COALESCE(SUM(deposit_amount), 0) as pending_balance FROM deposit_wallets WHERE deposit_amount > 0 AND consolidated_at IS NULL")
                pending_balance = float(cur.fetchone()['pending_balance'] or 0)
                
                return jsonify({
                    'success': True,
                    'stats': {
                        'total': total,
                        'available': available,
                        'assigned': assigned,
                        'used': used,
                        'pendingBalance': pending_balance
                    }
                })
    
    except Exception as e:
        logger.error(f"Error getting wallet pool stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/secrets-status', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_secrets_status():
    """Admin: Verificar que secrets estan configurados."""
    import os
    secrets_to_check = [
        'BOT_TOKEN',
        'ADMIN_TOKEN',
        'OWNER_TELEGRAM_ID',
        'TONCENTER_API_KEY',
        'B3C_HOT_WALLET_MNEMONIC',
        'WALLET_MASTER_KEY',
        'SMSPOOL_API_KEY',
        'CLOUDINARY_URL',
        'RESEND_API_KEY'
    ]
    
    status = {}
    for secret in secrets_to_check:
        status[secret] = bool(os.environ.get(secret))
    
    return jsonify({'success': True, 'secrets': status})


# ============================================================
# FRAUD DETECTION ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================


@admin_bp.route('/fraud/multiple-accounts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_fraud_multiple_accounts():
    """Admin: Detectar multiples cuentas usando misma IP."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'suspicious': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT ip_address, COUNT(DISTINCT user_id) as user_count,
                           ARRAY_AGG(DISTINCT user_id) as user_ids
                    FROM trusted_devices
                    WHERE ip_address IS NOT NULL AND ip_address != ''
                    GROUP BY ip_address
                    HAVING COUNT(DISTINCT user_id) > 1
                    ORDER BY user_count DESC
                    LIMIT 50
                """)
                results = cur.fetchall()
        
        suspicious = []
        for r in results:
            suspicious.append({
                'ip': r['ip_address'],
                'user_count': r['user_count'],
                'user_ids': r['user_ids']
            })
        
        return jsonify({'success': True, 'suspicious': suspicious, 'count': len(suspicious)})
        
    except Exception as e:
        logger.error(f"Error detecting multiple accounts: {e}")
        return jsonify({'success': True, 'suspicious': []})


@admin_bp.route('/fraud/ip-blacklist', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_ip_blacklist():
    """Admin: Obtener lista de IPs bloqueadas."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'blacklist': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ip_blacklist (
                        id SERIAL PRIMARY KEY,
                        ip_address TEXT UNIQUE NOT NULL,
                        reason TEXT,
                        created_by TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    SELECT id, ip_address, reason, created_by, created_at
                    FROM ip_blacklist ORDER BY created_at DESC
                """)
                ips = cur.fetchall()
                conn.commit()
        
        return jsonify({
            'success': True,
            'blacklist': [{
                'id': ip['id'],
                'ip': ip['ip_address'],
                'reason': ip.get('reason'),
                'created_by': ip.get('created_by'),
                'date': str(ip['created_at'])
            } for ip in ips]
        })
        
    except Exception as e:
        logger.error(f"Error getting IP blacklist: {e}")
        return jsonify({'success': True, 'blacklist': []})


@admin_bp.route('/fraud/ip-blacklist', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_add_ip_blacklist():
    """Admin: Agregar IP a la blacklist."""
    try:
        data = request.get_json() or {}
        ip = data.get('ip', '').strip()
        reason = data.get('reason', 'Sin razon especificada')
        
        if not ip:
            return jsonify({'success': False, 'error': 'IP requerida'}), 400
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO ip_blacklist (ip_address, reason, created_by)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (ip_address) DO UPDATE SET reason = EXCLUDED.reason
                    RETURNING id
                """, (ip, reason, admin_id))
                conn.commit()
        
        return jsonify({'success': True, 'message': f'IP {ip} agregada a blacklist'})
        
    except Exception as e:
        logger.error(f"Error adding IP to blacklist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/fraud/ip-blacklist/<int:ip_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def admin_remove_ip_blacklist(ip_id):
    """Admin: Remover IP de la blacklist."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ip_blacklist WHERE id = %s RETURNING ip_address", (ip_id,))
                result = cur.fetchone()
                if not result:
                    return jsonify({'success': False, 'error': 'IP no encontrada'}), 404
                conn.commit()
        
        return jsonify({'success': True, 'message': f'IP {result[0]} removida de blacklist'})
        
    except Exception as e:
        logger.error(f"Error removing IP from blacklist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# REALTIME / SESSIONS ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================


@admin_bp.route('/realtime/online', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_realtime_online():
    """Obtener usuarios online en tiempo real."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'count': 0, 'users': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, username, first_name, last_seen
                    FROM users
                    WHERE last_seen >= NOW() - INTERVAL '5 minutes'
                    ORDER BY last_seen DESC
                    LIMIT 50
                """)
                users = cur.fetchall()
                
                users_list = []
                for u in users:
                    users_list.append({
                        'user_id': u['id'],
                        'username': u['username'],
                        'first_name': u['first_name'],
                        'last_seen': u['last_seen'].isoformat() if u['last_seen'] else None
                    })
        
        return jsonify({'success': True, 'count': len(users_list), 'users': users_list})
        
    except Exception as e:
        logger.error(f"Error getting online users: {e}")
        return jsonify({'success': True, 'count': 0, 'users': []})


@admin_bp.route('/sessions', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_sessions():
    """Obtener sesiones activas."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'sessions': []})
        
        sessions = []
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT td.user_id, td.device_name, td.last_used_at, td.ip_address,
                           u.first_name, u.username
                    FROM trusted_devices td
                    LEFT JOIN users u ON td.user_id = u.id
                    WHERE td.last_used_at >= NOW() - INTERVAL '24 hours'
                    ORDER BY td.last_used_at DESC
                    LIMIT 100
                """)
                for row in cur.fetchall():
                    sessions.append({
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'first_name': row['first_name'],
                        'device': row['device_name'],
                        'ip': row['ip_address'],
                        'last_activity': row['last_used_at'].isoformat() if row['last_used_at'] else None
                    })
        
        return jsonify({'success': True, 'sessions': sessions})
        
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return jsonify({'success': True, 'sessions': []})


@admin_bp.route('/sessions/terminate', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_terminate_session():
    """Admin: Terminar sesion especifica de un dispositivo."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
            
        data = request.json or {}
        user_id = data.get('user_id')
        device_name = data.get('device_name')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'user_id requerido'}), 400
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                if device_name:
                    cur.execute("""
                        DELETE FROM trusted_devices
                        WHERE user_id = %s AND device_name = %s
                    """, (user_id, device_name))
                else:
                    cur.execute("""
                        DELETE FROM trusted_devices
                        WHERE user_id = %s
                    """, (user_id,))
                
                deleted = cur.rowcount
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'{deleted} sesion(es) terminada(s)',
                    'deleted': deleted
                })
                
    except Exception as e:
        logger.error(f"Error terminating session: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/sessions/terminate-all/<user_id>', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_terminate_all_user_sessions(user_id):
    """Admin: Terminar todas las sesiones de un usuario."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
            
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM trusted_devices WHERE user_id = %s
                """, (user_id,))
                deleted = cur.rowcount
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Todas las sesiones de usuario {user_id} terminadas ({deleted})',
                    'deleted': deleted
                })
                
    except Exception as e:
        logger.error(f"Error terminating all user sessions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/sessions/logout-all', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_logout_all_users():
    """Admin: Cerrar todas las sesiones de todos los usuarios (excepto admins)."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
            
        data = request.json or {}
        exclude_admins = data.get('exclude_admins', True)
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                if exclude_admins:
                    cur.execute("""
                        DELETE FROM trusted_devices
                        WHERE user_id NOT IN (
                            SELECT id FROM users WHERE LOWER(role) IN ('owner', 'admin')
                        )
                    """)
                else:
                    cur.execute("DELETE FROM trusted_devices")
                
                deleted = cur.rowcount
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Todas las sesiones cerradas ({deleted} dispositivos)',
                    'deleted': deleted
                })

                
    except Exception as e:
        logger.error(f"Error logging out all users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# PRODUCTS ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================


@admin_bp.route('/products', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_products():
    """Admin: Obtener todos los productos."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'products': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM products ORDER BY created_at DESC")
                products = cur.fetchall()
        
        return jsonify({
            'success': True,
            'products': [dict(p) for p in products] if products else []
        })
        
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return jsonify({'success': True, 'products': []})


@admin_bp.route('/products', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_create_product():
    """Admin: Crear nuevo producto."""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        price = float(data.get('price', 0))
        category = data.get('category', 'general').strip()
        stock = int(data.get('stock', 1))
        icon = data.get('icon', '')
        
        if not title:
            return jsonify({'success': False, 'error': 'El titulo es requerido'}), 400
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        user_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO products (user_id, title, description, price, category, stock, image_url, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                    RETURNING id
                """, (user_id, title, description, price, category, stock, icon))
                product_id = cur.fetchone()[0]
                conn.commit()
        
        logger.info(f"Product created: {title} (ID: {product_id})")
        return jsonify({'success': True, 'product_id': product_id, 'message': 'Producto creado correctamente'})
        
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/products/<int:product_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def admin_delete_product(product_id):
    """Admin: Eliminar producto."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
                conn.commit()
        
        logger.info(f"Product deleted: ID {product_id}")
        return jsonify({'success': True, 'message': 'Producto eliminado'})
        
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# TRANSACTIONS ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================


@admin_bp.route('/transactions', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_transactions():
    """Admin: Obtener todas las transacciones."""
    try:
        filter_type = request.args.get('filter', 'all')
        tx_type = request.args.get('type', '')
        status = request.args.get('status', '')
        period = request.args.get('period', 'all')
        user_id = request.args.get('user_id', '')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({
                'success': True,
                'transactions': [],
                'total': 0,
                'page': 1,
                'pages': 1,
                'totalVolume': 0,
                'totalFees': 0
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT wt.*, u.username, u.telegram_id
                    FROM wallet_transactions wt
                    LEFT JOIN users u ON CAST(wt.user_id AS INTEGER) = u.id
                    WHERE 1=1
                """
                count_query = "SELECT COUNT(*) FROM wallet_transactions wt WHERE 1=1"
                params = []
                count_params = []
                
                if filter_type != 'all':
                    query += " AND wt.transaction_type = %s"
                    count_query += " AND wt.transaction_type = %s"
                    params.append(filter_type)
                    count_params.append(filter_type)
                
                if tx_type:
                    query += " AND wt.transaction_type = %s"
                    count_query += " AND wt.transaction_type = %s"
                    params.append(tx_type)
                    count_params.append(tx_type)
                
                if user_id:
                    query += " AND wt.user_id = %s"
                    count_query += " AND wt.user_id = %s"
                    params.append(str(user_id))
                    count_params.append(str(user_id))
                
                if period == 'today':
                    query += " AND wt.created_at >= CURRENT_DATE"
                    count_query += " AND wt.created_at >= CURRENT_DATE"
                elif period == 'week':
                    query += " AND wt.created_at >= CURRENT_DATE - INTERVAL '7 days'"
                    count_query += " AND wt.created_at >= CURRENT_DATE - INTERVAL '7 days'"
                elif period == 'month':
                    query += " AND wt.created_at >= CURRENT_DATE - INTERVAL '30 days'"
                    count_query += " AND wt.created_at >= CURRENT_DATE - INTERVAL '30 days'"
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()[0] or 0
                
                query += " ORDER BY wt.created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                transactions = cur.fetchall()
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as volume,
                           COALESCE(SUM(CASE WHEN transaction_type IN ('buy', 'sell') THEN amount * 0.01 ELSE 0 END), 0) as fees
                    FROM wallet_transactions
                """)
                totals = cur.fetchone()
        
        pages = max(1, (total + limit - 1) // limit)
        
        return jsonify({
            'success': True,
            'transactions': [{
                'id': t['id'],
                'user_id': t.get('user_id', ''),
                'type': t.get('transaction_type', 'unknown'),
                'amount': float(t.get('amount', 0)),
                'currency': 'B3C',
                'status': 'completed',
                'username': t.get('username') or f"User {t.get('user_id', 'N/A')}",
                'description': t.get('description', ''),
                'reference_id': t.get('reference_id', ''),
                'tx_hash': t.get('reference_id', ''),
                'created_at': str(t.get('created_at', ''))
            } for t in transactions],
            'total': total,
            'page': page,
            'pages': pages,
            'totalVolume': float(totals['volume']) if totals else 0,
            'totalFees': float(totals['fees']) if totals else 0
        })
        
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        return jsonify({
            'success': True,
            'transactions': [],
            'totalDeposits': 0,
            'totalWithdrawals': 0
        })


@admin_bp.route('/transactions/<int:tx_id>', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_transaction_detail(tx_id):
    """Admin: Obtener detalle de una transaccion especifica."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT wt.*, u.username, u.telegram_id, u.first_name, u.last_name
                    FROM wallet_transactions wt
                    LEFT JOIN users u ON CAST(wt.user_id AS INTEGER) = u.id
                    WHERE wt.id = %s
                """, (tx_id,))
                tx = cur.fetchone()
                
                if not tx:
                    return jsonify({'success': False, 'error': 'Transaccion no encontrada'})
                
                tx_type = tx.get('transaction_type', 'unknown')
                tx_types_labels = {
                    'buy': 'Compra B3C',
                    'sell': 'Venta B3C',
                    'transfer_in': 'Transferencia Recibida',
                    'transfer_out': 'Transferencia Enviada',
                    'withdrawal': 'Retiro',
                    'deposit': 'Deposito',
                    'reward': 'Recompensa',
                    'fee': 'Comision'
                }
                
                return jsonify({
                    'success': True,
                    'transaction': {
                        'id': tx['id'],
                        'user_id': tx.get('user_id', ''),
                        'username': tx.get('username') or f"User {tx.get('user_id', 'N/A')}",
                        'user_name': f"{tx.get('first_name', '')} {tx.get('last_name', '')}".strip() or 'N/A',
                        'telegram_id': tx.get('telegram_id', ''),
                        'type': tx_type,
                        'type_label': tx_types_labels.get(tx_type, tx_type.capitalize()),
                        'amount': float(tx.get('amount', 0)),
                        'currency': 'B3C',
                        'status': 'completed',
                        'description': tx.get('description', ''),
                        'reference_id': tx.get('reference_id', ''),
                        'tx_hash': tx.get('reference_id', ''),
                        'created_at': str(tx.get('created_at', '')),
                        'balance_before': float(tx.get('balance_before', 0)) if tx.get('balance_before') else None,
                        'balance_after': float(tx.get('balance_after', 0)) if tx.get('balance_after') else None
                    }
                })
        
    except Exception as e:
        logger.error(f"Error getting transaction detail: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ============================================================
# PURCHASES ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================


@admin_bp.route('/purchases', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_purchases():
    """Admin: Obtener todas las compras de B3C."""
    try:
        status_filter = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({
                'success': True,
                'purchases': [],
                'total': 0,
                'page': 1,
                'pages': 1
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT 
                        bp.id, bp.purchase_id, bp.user_id, bp.ton_amount, bp.b3c_amount,
                        bp.commission_ton, bp.status, bp.tx_hash, bp.created_at, bp.confirmed_at,
                        u.username, u.first_name, u.last_name, u.telegram_id,
                        dw.wallet_address as deposit_wallet, dw.expected_amount as expected_amount
                    FROM b3c_purchases bp
                    LEFT JOIN users u ON bp.user_id::integer = u.id
                    LEFT JOIN deposit_wallets dw ON dw.assigned_to_purchase_id = bp.purchase_id
                    WHERE 1=1
                """
                count_query = "SELECT COUNT(*) FROM b3c_purchases WHERE 1=1"
                params = []
                count_params = []
                
                if status_filter:
                    query += " AND bp.status = %s"
                    count_query += " AND status = %s"
                    params.append(status_filter)
                    count_params.append(status_filter)
                
                cur.execute(count_query, count_params)
                total = cur.fetchone()[0] or 0
                
                query += " ORDER BY bp.created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                purchases = cur.fetchall()
                
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_purchases,
                        COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
                        COUNT(*) FILTER (WHERE status = 'confirmed') as confirmed_count,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
                        COUNT(*) FILTER (WHERE status = 'expired') as expired_count,
                        COALESCE(SUM(ton_amount) FILTER (WHERE status = 'confirmed'), 0) as total_ton,
                        COALESCE(SUM(b3c_amount) FILTER (WHERE status = 'confirmed'), 0) as total_b3c
                    FROM b3c_purchases
                """)
                stats = cur.fetchone()
        
        pages = max(1, (total + limit - 1) // limit)
        
        status_labels = {
            'pending': 'Pendiente',
            'confirmed': 'Confirmada',
            'failed': 'Fallida',
            'expired': 'Expirada'
        }
        
        return jsonify({
            'success': True,
            'purchases': [{
                'id': p['id'],
                'purchaseId': p['purchase_id'],
                'userId': p['user_id'],
                'username': p['username'] or f"User {p['user_id']}",
                'userFullName': f"{p['first_name'] or ''} {p['last_name'] or ''}".strip() or 'N/A',
                'telegramId': p['telegram_id'],
                'tonAmount': float(p['ton_amount']),
                'b3cAmount': float(p['b3c_amount']),
                'commissionTon': float(p['commission_ton']),
                'status': p['status'],
                'statusLabel': status_labels.get(p['status'], p['status']),
                'txHash': p['tx_hash'],
                'depositWallet': p['deposit_wallet'],
                'expectedAmount': float(p['expected_amount']) if p['expected_amount'] else None,
                'createdAt': p['created_at'].isoformat() if p['created_at'] else None,
                'confirmedAt': p['confirmed_at'].isoformat() if p['confirmed_at'] else None
            } for p in purchases],
            'total': total,
            'page': page,
            'pages': pages,
            'stats': {
                'totalPurchases': stats['total_purchases'] or 0,
                'pendingCount': stats['pending_count'] or 0,
                'confirmedCount': stats['confirmed_count'] or 0,
                'failedCount': stats['failed_count'] or 0,
                'expiredCount': stats['expired_count'] or 0,
                'totalTon': float(stats['total_ton'] or 0),
                'totalB3C': float(stats['total_b3c'] or 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting purchases: {e}")
        return jsonify({
            'success': True,
            'purchases': [],
            'total': 0,
            'page': 1,
            'pages': 1
        })


@admin_bp.route('/purchases/<purchase_id>', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_purchase_detail(purchase_id):
    """Admin: Obtener detalle de una compra especifica."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        bp.*, u.username, u.first_name, u.last_name, u.telegram_id, u.b3c_balance,
                        dw.wallet_address as deposit_wallet, dw.expected_amount, dw.deposit_amount, dw.status as wallet_status
                    FROM b3c_purchases bp
                    LEFT JOIN users u ON bp.user_id::integer = u.id
                    LEFT JOIN deposit_wallets dw ON dw.assigned_to_purchase_id = bp.purchase_id
                    WHERE bp.purchase_id = %s
                """, (purchase_id,))
                purchase = cur.fetchone()
                
                if not purchase:
                    return jsonify({'success': False, 'error': 'Compra no encontrada'}), 404
        
        status_labels = {
            'pending': 'Pendiente',
            'confirmed': 'Confirmada',
            'failed': 'Fallida',
            'expired': 'Expirada'
        }
        
        return jsonify({
            'success': True,
            'purchase': {
                'id': purchase['id'],
                'purchaseId': purchase['purchase_id'],
                'userId': purchase['user_id'],
                'username': purchase['username'] or f"User {purchase['user_id']}",
                'userFullName': f"{purchase['first_name'] or ''} {purchase['last_name'] or ''}".strip() or 'N/A',
                'telegramId': purchase['telegram_id'],
                'userBalance': float(purchase['b3c_balance']) if purchase['b3c_balance'] else 0,
                'tonAmount': float(purchase['ton_amount']),
                'b3cAmount': float(purchase['b3c_amount']),
                'commissionTon': float(purchase['commission_ton']),
                'status': purchase['status'],
                'statusLabel': status_labels.get(purchase['status'], purchase['status']),
                'txHash': purchase['tx_hash'],
                'depositWallet': purchase['deposit_wallet'],
                'expectedAmount': float(purchase['expected_amount']) if purchase['expected_amount'] else None,
                'depositAmount': float(purchase['deposit_amount']) if purchase['deposit_amount'] else None,
                'walletStatus': purchase['wallet_status'],
                'createdAt': purchase['created_at'].isoformat() if purchase['created_at'] else None,
                'confirmedAt': purchase['confirmed_at'].isoformat() if purchase['confirmed_at'] else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting purchase detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/purchases/<purchase_id>/credit', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_credit_purchase(purchase_id):
    """Admin: Acreditar manualmente una compra de B3C pendiente."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        admin_user = request.telegram_user
        admin_user_id = str(admin_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT bp.*, u.username, u.first_name
                    FROM b3c_purchases bp
                    LEFT JOIN users u ON bp.user_id::integer = u.id
                    WHERE bp.purchase_id = %s
                """, (purchase_id,))
                purchase = cur.fetchone()
                
                if not purchase:
                    return jsonify({'success': False, 'error': 'Compra no encontrada'}), 404
                
                if purchase['status'] == 'confirmed':
                    return jsonify({'success': False, 'error': 'Esta compra ya fue acreditada'}), 400
                
                user_id = purchase['user_id']
                b3c_amount = float(purchase['b3c_amount'])
                
                cur.execute("SELECT b3c_balance FROM users WHERE id = %s", (int(user_id),))
                user_row = cur.fetchone()
                balance_before = float(user_row['b3c_balance']) if user_row and user_row['b3c_balance'] else 0
                balance_after = balance_before + b3c_amount
                
                cur.execute("""
                    UPDATE users SET b3c_balance = b3c_balance + %s, updated_at = NOW() WHERE id = %s
                """, (b3c_amount, int(user_id)))
                
                cur.execute("""
                    UPDATE b3c_purchases SET status = 'confirmed', confirmed_at = NOW() WHERE purchase_id = %s
                """, (purchase_id,))
                
                cur.execute("""
                    INSERT INTO wallet_transactions 
                    (user_id, transaction_type, amount, balance_before, balance_after, description, reference_id)
                    VALUES (%s, 'buy', %s, %s, %s, %s, %s)
                """, (user_id, b3c_amount, balance_before, balance_after, 'Compra B3C acreditada manualmente por admin', purchase_id))
                
                cur.execute("UPDATE deposit_wallets SET status = 'used' WHERE assigned_to_purchase_id = %s", (purchase_id,))
                
                conn.commit()
                
                logger.info(f"[ADMIN] Compra {purchase_id} acreditada por admin {admin_user_id}. Usuario {user_id} recibio {b3c_amount} B3C")
        
        return jsonify({
            'success': True,
            'message': f'Compra acreditada correctamente. {b3c_amount} B3C fueron anadidos al usuario.',
            'credited': {
                'purchaseId': purchase_id,
                'userId': user_id,
                'username': purchase['username'],
                'b3cAmount': b3c_amount,
                'balanceBefore': balance_before,
                'balanceAfter': balance_after
            }
        })
        
    except Exception as e:
        logger.error(f"Error crediting purchase: {e}")
        return jsonify({'success': False, 'error': 'Error al acreditar la compra'}), 500


# ============================================================
# ACTIVITY & LOCKOUTS ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================


@admin_bp.route('/activity', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_activity():
    """Admin: Obtener actividad del sistema."""
    try:
        type_filter = request.args.get('type', 'all')
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': True, 'activities': []})
        
        activities = security_manager.get_all_activity_admin(type_filter)
        
        return jsonify({'success': True, 'activities': activities})
        
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        return jsonify({'success': True, 'activities': []})


@admin_bp.route('/lockouts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_lockouts():
    """Admin: Obtener usuarios bloqueados."""
    try:
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': True, 'lockouts': []})
        
        lockouts = security_manager.get_locked_users_admin()
        
        return jsonify({'success': True, 'lockouts': lockouts})
        
    except Exception as e:
        logger.error(f"Error getting lockouts: {e}")
        return jsonify({'success': True, 'lockouts': []})


@admin_bp.route('/unlock-user', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_unlock_user():
    """Admin: Desbloquear un usuario."""
    try:
        data = request.get_json() or {}
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'ID de usuario requerido'}), 400
        
        security_manager = get_security_manager()
        if not security_manager:
            return jsonify({'success': False, 'error': 'Security manager not available'}), 500
        
        result = security_manager.unlock_user_admin(user_id)
        
        return jsonify({'success': True, 'message': 'Usuario desbloqueado', 'result': result})
        
    except Exception as e:
        logger.error(f"Error unlocking user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# SETTINGS & NOTIFICATIONS ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================

import os


@admin_bp.route('/settings', methods=['GET', 'POST'])
@require_telegram_auth
@require_owner
def admin_system_settings():
    """Admin: Configuracion del sistema."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
            
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if request.method == 'GET':
                    cur.execute("SELECT key, value, category FROM system_settings")
                    rows = cur.fetchall()
                    settings = {row['key']: row['value'] for row in rows}
                    
                    return jsonify({
                        'success': True,
                        'maintenanceMode': settings.get('maintenance_mode', 'false') == 'true',
                        'maintenanceMessage': settings.get('maintenance_message', ''),
                        'registrationOpen': settings.get('registration_open', 'true') == 'true',
                        'merchantWallet': os.environ.get('TON_WALLET_ADDRESS', 'No configurada'),
                        'minDeposit': float(settings.get('min_deposit', '1')),
                        'minWithdrawal': float(settings.get('min_withdrawal', '0.5')),
                        'withdrawalFee': float(settings.get('withdrawal_fee', '0.05')),
                        'transactionFeePercent': float(settings.get('transaction_fee_percent', '2')),
                        'emailAlerts': settings.get('email_alerts', 'true') == 'true',
                        'telegramAlerts': settings.get('telegram_alerts', 'true') == 'true',
                        'largeTransactionThreshold': float(settings.get('large_transaction_threshold', '100'))
                    })
                else:
                    data = request.json or {}
                    updates = []
                    
                    setting_mappings = {
                        'maintenanceMode': ('maintenance_mode', lambda v: 'true' if v else 'false'),
                        'maintenanceMessage': ('maintenance_message', str),
                        'registrationOpen': ('registration_open', lambda v: 'true' if v else 'false'),
                        'minDeposit': ('min_deposit', str),
                        'minWithdrawal': ('min_withdrawal', str),
                        'withdrawalFee': ('withdrawal_fee', str),
                        'transactionFeePercent': ('transaction_fee_percent', str),
                        'emailAlerts': ('email_alerts', lambda v: 'true' if v else 'false'),
                        'telegramAlerts': ('telegram_alerts', lambda v: 'true' if v else 'false'),
                        'largeTransactionThreshold': ('large_transaction_threshold', str)
                    }
                    
                    for key, value in data.items():
                        if key in setting_mappings:
                            db_key, transform = setting_mappings[key]
                            cur.execute("""
                                INSERT INTO system_settings (key, value, updated_at)
                                VALUES (%s, %s, NOW())
                                ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = NOW()
                            """, (db_key, transform(value), transform(value)))
                            updates.append(db_key)
                    
                    conn.commit()
                    return jsonify({
                        'success': True,
                        'message': 'Configuracion guardada',
                        'updated': updates
                    })
        
    except Exception as e:
        logger.error(f"Error with settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/notifications', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_notifications():
    """Admin: Obtener notificaciones del panel."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'notifications': [], 'unread_count': 0})
            
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, type, title, message, data, is_read, created_at
                    FROM admin_notifications
                    ORDER BY created_at DESC
                    LIMIT 100
                """)
                notifications = cur.fetchall()
                
                cur.execute("SELECT COUNT(*) FROM admin_notifications WHERE is_read = false")
                unread_count = cur.fetchone()['count']
                
                for n in notifications:
                    if n.get('created_at'):
                        n['created_at'] = n['created_at'].isoformat()
                    if n.get('data'):
                        try:
                            n['data'] = json.loads(n['data']) if isinstance(n['data'], str) else n['data']
                        except:
                            pass
                
                return jsonify({
                    'success': True,
                    'notifications': notifications,
                    'unread_count': unread_count
                })
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/notifications/mark-read', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_mark_notification_read():
    """Admin: Marcar notificacion como leida."""
    try:
        data = request.get_json() or {}
        notification_id = data.get('id')
        mark_all = data.get('all', False)
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                if mark_all:
                    cur.execute("UPDATE admin_notifications SET is_read = true WHERE is_read = false")
                elif notification_id:
                    cur.execute("UPDATE admin_notifications SET is_read = true WHERE id = %s", (notification_id,))
                conn.commit()
                
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error marking notification: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/notifications/delete', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_delete_notification():
    """Admin: Eliminar notificacion."""
    try:
        data = request.get_json() or {}
        notification_id = data.get('id')
        delete_all = data.get('all', False)
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                if delete_all:
                    cur.execute("DELETE FROM admin_notifications")
                elif notification_id:
                    cur.execute("DELETE FROM admin_notifications WHERE id = %s", (notification_id,))
                conn.commit()
                
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/system-status', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_system_status():
    """Admin: Estado del sistema y APIs externas."""
    try:
        status = {
            'database': {'status': 'unknown', 'message': ''},
            'toncenter': {'status': 'unknown', 'message': ''},
            'smspool': {'status': 'unknown', 'message': ''},
            'cloudinary': {'status': 'unknown', 'message': ''}
        }
        
        db_manager = get_db_manager()
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    status['database'] = {'status': 'ok', 'message': 'Conectada'}
        except Exception as e:
            status['database'] = {'status': 'error', 'message': str(e)}
        
        toncenter_key = os.environ.get('TONCENTER_API_KEY', '')
        if toncenter_key:
            status['toncenter'] = {'status': 'ok', 'message': 'API Key configurada'}
        else:
            status['toncenter'] = {'status': 'warning', 'message': 'API Key no configurada'}
        
        smspool_key = os.environ.get('SMSPOOL_API_KEY', '')
        if smspool_key:
            status['smspool'] = {'status': 'ok', 'message': 'API Key configurada'}
        else:
            status['smspool'] = {'status': 'warning', 'message': 'API Key no configurada'}
        
        cloudinary_url = os.environ.get('CLOUDINARY_URL', '')
        if cloudinary_url:
            status['cloudinary'] = {'status': 'ok', 'message': 'Configurada'}
        else:
            status['cloudinary'] = {'status': 'warning', 'message': 'No configurada'}
        
        return jsonify({'success': True, 'services': status})
        
    except Exception as e:
        logger.error(f"Error checking system status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ADMIN FINANCIAL ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================

@admin_bp.route('/financial/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_financial_stats():
    """Admin: Dashboard financiero con metricas de B3C, TON y comisiones."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({
                'success': True,
                'data': {
                    'totalB3CSold': 0,
                    'totalTONReceived': 0,
                    'totalCommissions': 0,
                    'monthVolume': 0,
                    'lastMonthVolume': 0,
                    'volumeChange': 0,
                    'pendingWithdrawals': 0,
                    'pendingWithdrawalsAmount': 0,
                    'dailyRevenue': [],
                    'dailyVolume': []
                }
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(CASE WHEN transaction_type = 'deposit' THEN amount ELSE 0 END), 0) as total_b3c_sold,
                           COALESCE(SUM(CASE WHEN transaction_type = 'deposit' THEN amount * 0.1 ELSE 0 END), 0) as total_ton_received,
                           COALESCE(SUM(CASE WHEN transaction_type IN ('deposit', 'withdrawal') THEN amount * 0.02 ELSE 0 END), 0) as total_commissions
                    FROM wallet_transactions
                """)
                totals = cur.fetchone()
                total_b3c_sold = float(totals['total_b3c_sold']) if totals else 0
                total_ton_received = float(totals['total_ton_received']) if totals else 0
                total_commissions = float(totals['total_commissions']) if totals else 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as month_volume
                    FROM wallet_transactions
                    WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
                """)
                month_vol = cur.fetchone()
                month_volume = float(month_vol['month_volume']) if month_vol else 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0) as last_month_volume
                    FROM wallet_transactions
                    WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
                    AND created_at < DATE_TRUNC('month', CURRENT_DATE)
                """)
                last_month_vol = cur.fetchone()
                last_month_volume = float(last_month_vol['last_month_volume']) if last_month_vol else 0
                
                volume_change = 0
                if last_month_volume > 0:
                    volume_change = round(((month_volume - last_month_volume) / last_month_volume) * 100, 1)
                
                try:
                    cur.execute("""
                        SELECT COUNT(*) as count, COALESCE(SUM(amount_ton), 0) as total
                        FROM b3c_withdrawals
                        WHERE status = 'pending'
                    """)
                    pending = cur.fetchone()
                    pending_withdrawals = int(pending['count']) if pending else 0
                    pending_withdrawals_amount = float(pending['total']) if pending else 0
                except Exception:
                    pending_withdrawals = 0
                    pending_withdrawals_amount = 0
                
                cur.execute("""
                    SELECT DATE(created_at) as date, 
                           COALESCE(SUM(amount * 0.02), 0) as revenue
                    FROM wallet_transactions
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """)
                revenue_data = cur.fetchall()
                
                cur.execute("""
                    SELECT DATE(created_at) as date, 
                           COALESCE(SUM(amount), 0) as volume
                    FROM wallet_transactions
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """)
                volume_data = cur.fetchall()
        
        daily_revenue = []
        daily_volume = []
        revenue_dict = {row['date'].isoformat(): float(row['revenue']) for row in revenue_data} if revenue_data else {}
        volume_dict = {row['date'].isoformat(): float(row['volume']) for row in volume_data} if volume_data else {}
        
        for i in range(30):
            date = (datetime.now() - timedelta(days=29-i)).date()
            date_str = date.isoformat()
            daily_revenue.append({
                'date': date_str,
                'label': date.strftime('%d/%m'),
                'amount': revenue_dict.get(date_str, 0)
            })
            daily_volume.append({
                'date': date_str,
                'label': date.strftime('%d/%m'),
                'amount': volume_dict.get(date_str, 0)
            })
        
        return jsonify({
            'success': True,
            'data': {
                'totalB3CSold': total_b3c_sold,
                'totalTONReceived': total_ton_received,
                'totalCommissions': total_commissions,
                'monthVolume': month_volume,
                'lastMonthVolume': last_month_volume,
                'volumeChange': volume_change,
                'pendingWithdrawals': pending_withdrawals,
                'pendingWithdrawalsAmount': pending_withdrawals_amount,
                'dailyRevenue': daily_revenue,
                'dailyVolume': daily_volume
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting financial stats: {e}")
        return jsonify({
            'success': True,
            'data': {
                'totalB3CSold': 0,
                'totalTONReceived': 0,
                'totalCommissions': 0,
                'monthVolume': 0,
                'lastMonthVolume': 0,
                'volumeChange': 0,
                'pendingWithdrawals': 0,
                'pendingWithdrawalsAmount': 0,
                'dailyRevenue': [],
                'dailyVolume': []
            }
        })


@admin_bp.route('/financial/period-stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_financial_period_stats():
    """Admin: Estadisticas financieras por periodo personalizado."""
    try:
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        
        if not date_from or not date_to:
            return jsonify({'success': False, 'error': 'Fechas requeridas'}), 400
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({
                'success': True,
                'data': {
                    'txCount': 0,
                    'b3cVolume': 0,
                    'purchases': {'count': 0, 'tonAmount': 0, 'b3cAmount': 0},
                    'withdrawals': {'count': 0, 'b3cAmount': 0},
                    'transfers': {'count': 0, 'b3cAmount': 0},
                    'commissions': 0,
                    'dailyVolume': [],
                    'typeBreakdown': {'purchases': 0, 'withdrawals': 0, 'transfers': 0}
                }
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as volume
                    FROM wallet_transactions
                    WHERE created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                tx_totals = cur.fetchone()
                tx_count = int(tx_totals['count']) if tx_totals else 0
                b3c_volume = float(tx_totals['volume']) if tx_totals else 0
                
                cur.execute("""
                    SELECT COUNT(*) as count, 
                           COALESCE(SUM(amount), 0) as b3c_amount,
                           COALESCE(SUM(amount * 0.1), 0) as ton_amount
                    FROM wallet_transactions
                    WHERE transaction_type = 'deposit' 
                    AND created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                purchases = cur.fetchone()
                purchases_count = int(purchases['count']) if purchases else 0
                purchases_b3c = float(purchases['b3c_amount']) if purchases else 0
                purchases_ton = float(purchases['ton_amount']) if purchases else 0
                
                cur.execute("""
                    SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as b3c_amount
                    FROM wallet_transactions
                    WHERE transaction_type = 'withdrawal' 
                    AND created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                withdrawals = cur.fetchone()
                withdrawals_count = int(withdrawals['count']) if withdrawals else 0
                withdrawals_b3c = float(withdrawals['b3c_amount']) if withdrawals else 0
                
                cur.execute("""
                    SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as b3c_amount
                    FROM wallet_transactions
                    WHERE transaction_type = 'transfer' 
                    AND created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                transfers = cur.fetchone()
                transfers_count = int(transfers['count']) if transfers else 0
                transfers_b3c = float(transfers['b3c_amount']) if transfers else 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(amount * 0.02), 0) as commissions
                    FROM wallet_transactions
                    WHERE transaction_type IN ('deposit', 'withdrawal')
                    AND created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                """, (date_from, date_to))
                comm = cur.fetchone()
                commissions = float(comm['commissions']) if comm else 0
                
                cur.execute("""
                    SELECT DATE(created_at) as date, COALESCE(SUM(amount), 0) as volume
                    FROM wallet_transactions
                    WHERE created_at >= %s AND created_at <= %s::date + INTERVAL '1 day'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """, (date_from, date_to))
                daily_data = cur.fetchall()
        
        daily_volume = []
        if daily_data:
            for row in daily_data:
                daily_volume.append({
                    'date': row['date'].isoformat(),
                    'label': row['date'].strftime('%d/%m'),
                    'amount': float(row['volume'])
                })
        
        return jsonify({
            'success': True,
            'data': {
                'txCount': tx_count,
                'b3cVolume': b3c_volume,
                'purchases': {
                    'count': purchases_count,
                    'tonAmount': purchases_ton,
                    'b3cAmount': purchases_b3c
                },
                'withdrawals': {
                    'count': withdrawals_count,
                    'b3cAmount': withdrawals_b3c
                },
                'transfers': {
                    'count': transfers_count,
                    'b3cAmount': transfers_b3c
                },
                'commissions': commissions,
                'dailyVolume': daily_volume,
                'typeBreakdown': {
                    'purchases': purchases_count,
                    'withdrawals': withdrawals_count,
                    'transfers': transfers_count
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting period stats: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener estadisticas'}), 500


@admin_bp.route('/financial/period-stats/export', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_financial_period_stats_export():
    """Admin: Exportar estadisticas por periodo a CSV."""
    try:
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        
        if not date_from or not date_to:
            return jsonify({'success': False, 'error': 'Fechas requeridas'}), 400
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'csv': 'No hay datos disponibles'})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT wt.id, u.telegram_id, u.username, u.first_name,
                           wt.transaction_type, wt.amount, wt.status, wt.tx_hash, wt.created_at
                    FROM wallet_transactions wt
                    LEFT JOIN users u ON wt.user_id = u.id
                    WHERE wt.created_at >= %s AND wt.created_at <= %s::date + INTERVAL '1 day'
                    ORDER BY wt.created_at DESC
                """, (date_from, date_to))
                transactions = cur.fetchall()
        
        csv_lines = ['ID,Telegram ID,Username,Nombre,Tipo,Monto,Estado,TX Hash,Fecha']
        for tx in transactions:
            csv_lines.append(','.join([
                str(tx.get('id', '')),
                str(tx.get('telegram_id', '')),
                str(tx.get('username', '') or ''),
                str(tx.get('first_name', '') or ''),
                str(tx.get('transaction_type', '')),
                str(tx.get('amount', 0)),
                str(tx.get('status', '')),
                str(tx.get('tx_hash', '') or ''),
                str(tx.get('created_at', '') or '')
            ]))
        
        return jsonify({
            'success': True,
            'csv': '\n'.join(csv_lines),
            'filename': f'estadisticas_{date_from}_{date_to}.csv'
        })
        
    except Exception as e:
        logger.error(f"Error exporting period stats: {e}")
        return jsonify({'success': False, 'error': 'Error al exportar'}), 500


# ============================================================
# ADMIN CONTENT ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================

@admin_bp.route('/content/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_content_stats():
    """Admin: Estadisticas de contenido."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({
                'success': True,
                'totalPosts': 0,
                'postsToday': 0,
                'totalMedia': 0,
                'totalStories': 0,
                'reportedPosts': 0
            })
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM posts WHERE is_active = true")
                total_posts = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COUNT(*) FROM posts 
                    WHERE is_active = true AND created_at >= NOW() - INTERVAL '24 hours'
                """)
                posts_today = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT COUNT(*) FROM posts 
                    WHERE is_active = true AND content_type IN ('image', 'video')
                """)
                total_media = cur.fetchone()[0] or 0
                
                total_stories = 0
                try:
                    cur.execute("""
                        SELECT COUNT(*) FROM stories 
                        WHERE is_active = true AND expires_at > NOW()
                    """)
                    total_stories = cur.fetchone()[0] or 0
                except Exception:
                    pass
                
                reported_posts = 0
                try:
                    cur.execute("""
                        SELECT COUNT(DISTINCT post_id) FROM reports 
                        WHERE status = 'pending' AND post_id IS NOT NULL
                    """)
                    reported_posts = cur.fetchone()[0] or 0
                except Exception:
                    pass
        
        return jsonify({
            'success': True,
            'totalPosts': total_posts,
            'postsToday': posts_today,
            'totalMedia': total_media,
            'totalStories': total_stories,
            'reportedPosts': reported_posts
        })
        
    except Exception as e:
        logger.error(f"Error getting content stats: {e}")
        return jsonify({
            'success': True,
            'totalPosts': 0,
            'postsToday': 0,
            'totalMedia': 0,
            'totalStories': 0,
            'reportedPosts': 0
        })


@admin_bp.route('/content/posts', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_content_posts():
    """Admin: Listar publicaciones para moderacion con filtros."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'posts': [], 'total': 0})
        
        limit = request.args.get('limit', 50, type=int)
        search = request.args.get('search', '').strip()
        content_type = request.args.get('content_type', '').strip()
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT p.id, p.user_id, p.content_type, p.caption, p.content_url,
                           p.likes_count, p.comments_count, p.shares_count,
                           p.is_active, p.created_at,
                           u.username, u.first_name
                    FROM posts p
                    LEFT JOIN users u ON p.user_id = u.telegram_id::text
                    WHERE 1=1
                """
                params = []
                
                if search:
                    query += " AND (LOWER(p.caption) LIKE LOWER(%s) OR LOWER(u.username) LIKE LOWER(%s))"
                    search_pattern = f"%{search}%"
                    params.extend([search_pattern, search_pattern])
                
                if content_type:
                    query += " AND p.content_type = %s"
                    params.append(content_type)
                
                query += " ORDER BY p.created_at DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                posts = cur.fetchall()
                
                count_query = "SELECT COUNT(*) as total FROM posts p LEFT JOIN users u ON p.user_id = u.telegram_id::text WHERE 1=1"
                count_params = []
                
                if search:
                    count_query += " AND (LOWER(p.caption) LIKE LOWER(%s) OR LOWER(u.username) LIKE LOWER(%s))"
                    count_params.extend([f"%{search}%", f"%{search}%"])
                
                if content_type:
                    count_query += " AND p.content_type = %s"
                    count_params.append(content_type)
                
                cur.execute(count_query, count_params)
                total_row = cur.fetchone()
                total = total_row['total'] if total_row else 0
        
        result = []
        for p in posts:
            p_dict = dict(p)
            if p_dict.get('created_at'):
                p_dict['created_at'] = p_dict['created_at'].isoformat()
            result.append(p_dict)
        
        return jsonify({
            'success': True,
            'posts': result,
            'total': total
        })
        
    except Exception as e:
        logger.error(f"Error getting content posts: {e}")
        return jsonify({'success': True, 'posts': [], 'total': 0})


@admin_bp.route('/content/posts/<int:post_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def admin_delete_post(post_id):
    """Admin: Eliminar una publicacion."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE posts SET is_active = false WHERE id = %s", (post_id,))
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Publicacion eliminada'})
        
    except Exception as e:
        logger.error(f"Error deleting post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/content/posts/<int:post_id>', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_post_detail(post_id):
    """Admin: Obtener detalle de una publicacion."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT p.*, u.username, u.first_name, u.last_name, u.avatar_url,
                           u.is_banned as user_banned
                    FROM posts p
                    LEFT JOIN users u ON p.user_id = u.telegram_id::text
                    WHERE p.id = %s
                """, (post_id,))
                post = cur.fetchone()
                
                if not post:
                    return jsonify({'success': False, 'error': 'Publicacion no encontrada'}), 404
                
                report_count = 0
                reports = []
                try:
                    cur.execute("""
                        SELECT COUNT(*) as report_count FROM content_reports 
                        WHERE content_type = 'post' AND content_id = %s
                    """, (post_id,))
                    report_count = cur.fetchone()['report_count'] or 0
                    
                    cur.execute("""
                        SELECT id, reporter_id, reason, description, status, created_at 
                        FROM content_reports 
                        WHERE content_type = 'post' AND content_id = %s
                        ORDER BY created_at DESC
                    """, (post_id,))
                    reports = cur.fetchall()
                except Exception:
                    pass
        
        post_data = dict(post)
        post_data['report_count'] = report_count
        post_data['reports'] = [dict(r) for r in reports]
        
        if post_data.get('created_at'):
            post_data['created_at'] = post_data['created_at'].isoformat()
        
        return jsonify({'success': True, 'post': post_data})
        
    except Exception as e:
        logger.error(f"Error getting post detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/content/posts/<int:post_id>/warn', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_warn_post_author(post_id):
    """Admin: Advertir al autor de una publicacion."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        data = request.get_json() or {}
        reason = data.get('reason', 'Contenido inapropiado')
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
                post = cur.fetchone()
                
                if not post:
                    return jsonify({'success': False, 'error': 'Publicacion no encontrada'}), 404
                
                user_id = post['user_id']
                
                try:
                    cur.execute("""
                        INSERT INTO admin_warnings (user_id, admin_id, reason, post_id, created_at)
                        VALUES (%s, %s, %s, %s, NOW())
                    """, (user_id, admin_id, reason, post_id))
                except Exception:
                    pass
                
                try:
                    cur.execute("""
                        INSERT INTO admin_logs (admin_id, action, target_type, target_id, details, created_at)
                        VALUES (%s, 'warn_user', 'post', %s, %s, NOW())
                    """, (admin_id, str(post_id), reason))
                except Exception:
                    pass
                
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Advertencia enviada al usuario'})
        
    except Exception as e:
        logger.error(f"Error warning post author: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/content/posts/<int:post_id>/ban-author', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_ban_post_author(post_id):
    """Admin: Banear al autor de una publicacion por contenido inapropiado."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        data = request.get_json() or {}
        reason = data.get('reason', 'Contenido inapropiado')
        admin_id = str(request.telegram_user.get('id', 0))
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
                post = cur.fetchone()
                
                if not post:
                    return jsonify({'success': False, 'error': 'Publicacion no encontrada'}), 404
                
                user_id = post['user_id']
                
                cur.execute("""
                    UPDATE users SET is_banned = true, ban_reason = %s, banned_at = NOW()
                    WHERE telegram_id::text = %s
                """, (reason, user_id))
                
                cur.execute("""
                    UPDATE posts SET is_active = false WHERE user_id = %s
                """, (user_id,))
                
                try:
                    cur.execute("""
                        INSERT INTO admin_logs (admin_id, action, target_type, target_id, details, created_at)
                        VALUES (%s, 'ban_user_content', 'user', %s, %s, NOW())
                    """, (admin_id, user_id, reason))
                except Exception:
                    pass
                
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Usuario baneado y contenido eliminado'})
        
    except Exception as e:
        logger.error(f"Error banning post author: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/content/reported', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_reported_content():
    """Admin: Obtener publicaciones reportadas con prioridad."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'posts': []})
        
        limit = request.args.get('limit', 50, type=int)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                try:
                    cur.execute("""
                        SELECT p.id, p.user_id, p.content_type, p.caption, p.content_url,
                               p.likes_count, p.comments_count, p.is_active, p.created_at,
                               u.username, u.first_name,
                               COUNT(cr.id) as report_count,
                               ARRAY_AGG(DISTINCT cr.reason) as report_reasons
                        FROM posts p
                        LEFT JOIN users u ON p.user_id = u.telegram_id::text
                        INNER JOIN content_reports cr ON cr.content_type = 'post' AND cr.content_id = p.id
                        WHERE p.is_active = true AND cr.status = 'pending'
                        GROUP BY p.id, p.user_id, p.content_type, p.caption, p.content_url,
                                 p.likes_count, p.comments_count, p.is_active, p.created_at,
                                 u.username, u.first_name
                        ORDER BY report_count DESC, p.created_at DESC
                        LIMIT %s
                    """, (limit,))
                    posts = cur.fetchall()
                except Exception:
                    posts = []
        
        result = []
        for p in posts:
            post_dict = dict(p)
            if post_dict.get('created_at'):
                post_dict['created_at'] = post_dict['created_at'].isoformat()
            result.append(post_dict)
        
        return jsonify({'success': True, 'posts': result})
        
    except Exception as e:
        logger.error(f"Error getting reported content: {e}")
        return jsonify({'success': True, 'posts': []})
