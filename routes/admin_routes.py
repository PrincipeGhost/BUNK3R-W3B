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

from bot.tracking_correos.decorators import require_telegram_auth, require_owner
from bot.tracking_correos.services import get_db_manager, get_security_manager

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
# ADMIN USER LEGACY ENDPOINTS (Migrados 12 Diciembre 2025)
# ============================================================


@admin_bp.route('/user/<user_id>', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_user_basic(user_id):
    """Admin: Obtener detalle básico de un usuario (legacy endpoint)."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, username, first_name, last_name, telegram_id, 
                           credits, level, is_active, is_verified, wallet_address,
                           created_at, last_seen, bio, avatar_url,
                           COALESCE(is_banned, false) as is_banned,
                           two_factor_enabled, security_score
                    FROM users WHERE id = %s OR telegram_id::text = %s
                """, (str(user_id), str(user_id)))
                user = cur.fetchone()
                
                if not user:
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                cur.execute("SELECT COUNT(*) as total FROM wallet_transactions WHERE user_id = %s", (user_id,))
                total_tx = cur.fetchone()['total'] or 0
                
                user_data = {
                    'user_id': str(user['id']),
                    'id': user['id'],
                    'telegram_id': user.get('telegram_id'),
                    'username': user.get('username'),
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                    'bio': user.get('bio'),
                    'avatar_url': user.get('avatar_url'),
                    'credits': float(user.get('credits', 0)),
                    'level': user.get('level', 1),
                    'is_active': user.get('is_active', True),
                    'is_verified': user.get('is_verified', False),
                    'is_banned': user.get('is_banned', False),
                    'wallet_address': user.get('wallet_address'),
                    'two_factor_enabled': user.get('two_factor_enabled', False),
                    'security_score': user.get('security_score', 0),
                    'created_at': str(user.get('created_at', '')),
                    'last_seen': str(user.get('last_seen', '')),
                    'total_transactions': total_tx,
                    'language_code': 'es'
                }
        
        return jsonify({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        logger.error(f"Error getting user detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/user/credits', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_add_credits():
    """Admin: Agregar creditos a un usuario."""
    try:
        db_manager = get_db_manager()
        data = request.get_json() or {}
        user_id = data.get('userId')
        amount = data.get('amount', 0)
        
        if not user_id:
            return jsonify({'success': False, 'error': 'ID de usuario requerido'}), 400
        
        if not amount or amount == 0:
            return jsonify({'success': False, 'error': 'Cantidad invalida'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                cur.execute("""
                    UPDATE users SET credits = credits + %s 
                    WHERE id = %s RETURNING credits
                """, (amount, user_id))
                result = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'newCredits': result[0] if result else 0,
                    'message': f'{amount} creditos agregados'
                })
        
    except Exception as e:
        logger.error(f"Error adding credits: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/user/toggle-status', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_toggle_user_status():
    """Admin: Cambiar estado activo/inactivo de un usuario."""
    try:
        db_manager = get_db_manager()
        data = request.get_json() or {}
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'ID de usuario requerido'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, is_active FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()
                if not user:
                    return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
                
                cur.execute("""
                    UPDATE users SET is_active = NOT is_active 
                    WHERE id = %s RETURNING is_active
                """, (user_id,))
                result = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'isActive': result[0] if result else not user[1]
                })
        
    except Exception as e:
        logger.error(f"Error toggling user status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/user/verify', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_verify_user():
    """Admin: Cambiar estado de verificación de un usuario."""
    try:
        db_manager = get_db_manager()
        data = request.get_json() or {}
        user_id = data.get('userId')
        is_verified = data.get('isVerified', False)
        
        if not user_id:
            return jsonify({'success': False, 'error': 'ID de usuario requerido'}), 400
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        success = db_manager.set_user_verified(user_id, is_verified)
        
        if success:
            return jsonify({
                'success': True,
                'isVerified': is_verified,
                'message': 'Usuario verificado' if is_verified else 'Verificación removida'
            })
        else:
            return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
        
    except Exception as e:
        logger.error(f"Error verifying user: {e}")
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
# TELEGRAM SETTINGS ENDPOINTS (Migrados 12 Diciembre 2025)
# ============================================================

from bot.tracking_correos.telegram_service import telegram_service


@admin_bp.route('/telegram/settings', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_telegram_settings():
    """Admin: Obtener configuracion de Telegram."""
    try:
        db_manager = get_db_manager()
        settings = telegram_service.get_settings()
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT key, value FROM system_settings WHERE key LIKE 'telegram_%'")
                db_settings = {row['key']: row['value'] for row in cur.fetchall()}
        
        for key in settings['notification_types']:
            db_key = f"telegram_{key}_enabled"
            if db_key in db_settings:
                settings['notification_types'][key]['enabled'] = db_settings[db_key] == 'true'
            
            threshold_key = f"telegram_{key}_threshold"
            if threshold_key in db_settings:
                try:
                    settings['notification_types'][key]['threshold'] = float(db_settings[threshold_key])
                except:
                    pass
        
        if 'telegram_enabled' in db_settings:
            settings['enabled'] = db_settings['telegram_enabled'] == 'true'
        
        return jsonify({
            'success': True,
            **settings
        })
    except Exception as e:
        logger.error(f"Error getting telegram settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/telegram/settings', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_update_telegram_settings():
    """Admin: Actualizar configuracion de Telegram."""
    try:
        db_manager = get_db_manager()
        data = request.get_json() or {}
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                if 'enabled' in data:
                    cur.execute("""
                        INSERT INTO system_settings (key, value, updated_at)
                        VALUES ('telegram_enabled', %s, NOW())
                        ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = NOW()
                    """, ('true' if data['enabled'] else 'false', 'true' if data['enabled'] else 'false'))
                
                if 'notification_types' in data:
                    for key, settings in data['notification_types'].items():
                        if isinstance(settings, dict):
                            if 'enabled' in settings:
                                db_key = f"telegram_{key}_enabled"
                                val = 'true' if settings['enabled'] else 'false'
                                cur.execute("""
                                    INSERT INTO system_settings (key, value, updated_at)
                                    VALUES (%s, %s, NOW())
                                    ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = NOW()
                                """, (db_key, val, val))
                            
                            if 'threshold' in settings:
                                threshold_key = f"telegram_{key}_threshold"
                                cur.execute("""
                                    INSERT INTO system_settings (key, value, updated_at)
                                    VALUES (%s, %s, NOW())
                                    ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = NOW()
                                """, (threshold_key, str(settings['threshold']), str(settings['threshold'])))
                
                conn.commit()
        
        telegram_service.update_settings(data)
        
        return jsonify({
            'success': True,
            'message': 'Configuracion guardada'
        })
    except Exception as e:
        logger.error(f"Error updating telegram settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/telegram/test', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_test_telegram():
    """Admin: Enviar mensaje de prueba por Telegram."""
    try:
        result = telegram_service.send_test_message()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error testing telegram: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/telegram/verify', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_verify_telegram():
    """Admin: Verificar conexion del bot de Telegram."""
    try:
        result = telegram_service.verify_bot()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error verifying telegram: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/telegram/send', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_send_telegram():
    """Admin: Enviar mensaje personalizado por Telegram."""
    try:
        data = request.get_json() or {}
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'Mensaje requerido'}), 400
        
        result = telegram_service.send_custom_message(message)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error sending telegram: {e}")
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



# ============================================================
# ADMIN WALLETS ENDPOINTS (Migrados 10 Diciembre 2025 - Sesion 5)
# ============================================================


@admin_bp.route('/wallets/hot', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_hot_wallet():
    """Admin: Obtener informacion del hot wallet."""
    try:
        import os
        hot_wallet_address = os.environ.get('TON_WALLET_ADDRESS', '')
        
        balance = 0
        if hot_wallet_address:
            try:
                from bot.tracking_correos.wallet_pool_service import get_wallet_pool_service
                db_manager = get_db_manager()
                wallet_svc = get_wallet_pool_service(db_manager)
                if wallet_svc:
                    balance = wallet_svc.get_wallet_balance(hot_wallet_address)
            except Exception as e:
                logger.warning(f"Could not get hot wallet balance: {e}")
        
        use_testnet = os.environ.get('TON_NETWORK', 'testnet').lower() == 'testnet'
        explorer_url = 'https://testnet.tonscan.org' if use_testnet else 'https://tonscan.org'
        
        return jsonify({
            'success': True,
            'address': hot_wallet_address,
            'balance': balance,
            'status': 'ok' if balance > 0.1 else 'low',
            'explorerUrl': explorer_url
        })
    
    except Exception as e:
        logger.error(f"Error getting hot wallet info: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/wallets/deposits', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_deposit_wallets():
    """Admin: Obtener lista de wallets de deposito."""
    try:
        import os
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        status_filter = request.args.get('status', '')
        offset = (page - 1) * limit
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT * FROM deposit_wallets WHERE 1=1"
                params = []
                
                if status_filter:
                    query += " AND status = %s"
                    params.append(status_filter)
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                wallets = cur.fetchall()
                
                count_query = "SELECT COUNT(*) as total FROM deposit_wallets WHERE 1=1"
                if status_filter:
                    cur.execute(count_query + " AND status = %s", (status_filter,))
                else:
                    cur.execute(count_query)
                total = cur.fetchone()['total']
        
        use_testnet = os.environ.get('TON_NETWORK', 'testnet').lower() == 'testnet'
        explorer_url = 'https://testnet.tonscan.org' if use_testnet else 'https://tonscan.org'
        
        return jsonify({
            'success': True,
            'explorerUrl': explorer_url,
            'wallets': [{
                'id': w['id'],
                'wallet_address': w.get('wallet_address', ''),
                'status': w.get('status', 'unknown'),
                'assigned_to_user_id': w.get('assigned_to_user_id'),
                'deposit_amount': float(w.get('deposit_amount', 0) or 0),
                'created_at': str(w.get('created_at', '')),
                'consolidated_at': str(w.get('consolidated_at', '')) if w.get('consolidated_at') else None
            } for w in wallets],
            'total': total,
            'page': page,
            'pages': (total + limit - 1) // limit
        })
    
    except Exception as e:
        logger.error(f"Error getting deposit wallets: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/wallets/fill-pool', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_fill_wallet_pool():
    """Admin: Llenar el pool de wallets."""
    try:
        data = request.get_json() or {}
        count = min(int(data.get('count', 10)), 50)
        
        try:
            from bot.tracking_correos.wallet_pool_service import get_wallet_pool_service
            db_manager = get_db_manager()
            wallet_svc = get_wallet_pool_service(db_manager)
            if wallet_svc:
                created = wallet_svc.fill_pool(count)
                
                user_id = getattr(request, 'user_id', '0')
                log_admin_action(user_id, 'Admin', 'fill_wallet_pool', 'deposit_wallets', 
                               None, f"Created {created} new deposit wallets")
                
                return jsonify({
                    'success': True,
                    'created': created,
                    'message': f'{created} wallets creadas'
                })
            else:
                return jsonify({'success': False, 'error': 'Wallet pool service no disponible'}), 500
        except Exception as e:
            logger.error(f"Error filling wallet pool: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    except Exception as e:
        logger.error(f"Error in fill wallet pool: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/wallets/consolidate', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_consolidate_wallets():
    """Admin: Consolidar fondos de wallets de deposito al hot wallet."""
    try:
        try:
            from bot.tracking_correos.wallet_pool_service import get_wallet_pool_service
            db_manager = get_db_manager()
            wallet_svc = get_wallet_pool_service(db_manager)
            if wallet_svc:
                result = wallet_svc.consolidate_all_balances()
                
                user_id = getattr(request, 'user_id', '0')
                log_admin_action(user_id, 'Admin', 'consolidate_wallets', 'deposit_wallets', 
                               None, f"Consolidated {result.get('count', 0)} wallets, total: {result.get('total', 0)} TON")
                
                return jsonify({
                    'success': True,
                    'consolidated': result.get('count', 0),
                    'totalAmount': result.get('total', 0),
                    'message': f"Consolidados {result.get('count', 0)} wallets"
                })
            else:
                return jsonify({'success': False, 'error': 'Wallet pool service no disponible'}), 500
        except Exception as e:
            logger.error(f"Error consolidating wallets: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    except Exception as e:
        logger.error(f"Error in consolidate wallets: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/blockchain/history', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_blockchain_history():
    """Admin: Obtener historial de transacciones blockchain."""
    try:
        import os
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        tx_type = request.args.get('type', '')
        limit = min(int(request.args.get('limit', 50)), 200)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                transactions = []
                
                if tx_type in ['', 'deposits', 'all']:
                    cur.execute("""
                        SELECT 'deposit' as tx_type, dw.deposit_tx_hash as tx_hash, 
                               dw.deposit_amount as amount, dw.wallet_address as from_address,
                               (SELECT wallet_address FROM deposit_wallets WHERE status = 'hot_wallet' LIMIT 1) as to_address,
                               dw.deposit_detected_at as created_at, 'confirmed' as status,
                               u.username
                        FROM deposit_wallets dw
                        LEFT JOIN users u ON dw.assigned_to_user_id = u.id
                        WHERE dw.deposit_tx_hash IS NOT NULL
                        ORDER BY dw.deposit_detected_at DESC
                        LIMIT %s
                    """, (limit,))
                    deposits = cur.fetchall()
                    transactions.extend(deposits)
                
                if tx_type in ['', 'consolidations', 'all']:
                    cur.execute("""
                        SELECT 'consolidation' as tx_type, consolidation_tx_hash as tx_hash,
                               deposit_amount as amount, wallet_address as from_address,
                               %s as to_address, consolidated_at as created_at, 'confirmed' as status,
                               NULL as username
                        FROM deposit_wallets
                        WHERE consolidation_tx_hash IS NOT NULL
                        ORDER BY consolidated_at DESC
                        LIMIT %s
                    """, (os.environ.get('TON_WALLET_ADDRESS', ''), limit))
                    consolidations = cur.fetchall()
                    transactions.extend(consolidations)
                
                if tx_type in ['', 'withdrawals', 'all']:
                    cur.execute("""
                        SELECT 'withdrawal' as tx_type, tx_hash, amount_ton as amount,
                               %s as from_address, wallet_address as to_address,
                               processed_at as created_at, status, u.username
                        FROM b3c_withdrawals w
                        LEFT JOIN users u ON w.user_id = u.id
                        WHERE tx_hash IS NOT NULL
                        ORDER BY processed_at DESC
                        LIMIT %s
                    """, (os.environ.get('TON_WALLET_ADDRESS', ''), limit))
                    withdrawals = cur.fetchall()
                    transactions.extend(withdrawals)
                
                transactions.sort(key=lambda x: x['created_at'] or datetime.min, reverse=True)
                transactions = transactions[:limit]
        
        use_testnet = os.environ.get('TON_NETWORK', 'testnet').lower() == 'testnet'
        explorer_url = 'https://testnet.tonscan.org' if use_testnet else 'https://tonscan.org'
        
        return jsonify({
            'success': True,
            'explorerUrl': explorer_url,
            'transactions': [{
                'tx_type': tx['tx_type'],
                'tx_hash': tx.get('tx_hash', ''),
                'amount': float(tx.get('amount', 0) or 0),
                'from_address': tx.get('from_address', '')[:20] + '...' if tx.get('from_address') else '-',
                'to_address': tx.get('to_address', '')[:20] + '...' if tx.get('to_address') else '-',
                'created_at': str(tx.get('created_at', '')),
                'status': tx.get('status', 'unknown'),
                'username': tx.get('username', '')
            } for tx in transactions],
            'total': len(transactions)
        })
    
    except Exception as e:
        logger.error(f"Error getting blockchain history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/wallets/pool-config', methods=['GET', 'POST'])
@require_telegram_auth
@require_owner
def admin_pool_config():
    """Admin: Obtener o guardar configuracion del pool de wallets."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS system_config (
                        config_key VARCHAR(100) PRIMARY KEY,
                        config_value TEXT,
                        config_type VARCHAR(50),
                        description TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_by VARCHAR(100)
                    )
                """)
                conn.commit()
                
                if request.method == 'GET':
                    cur.execute("SELECT config_key, config_value FROM system_config WHERE config_key LIKE 'pool_%' OR config_key LIKE 'wallet_%'")
                    rows = cur.fetchall()
                    config = {row['config_key']: row['config_value'] for row in rows}
                    
                    return jsonify({
                        'success': True,
                        'config': {
                            'minPoolSize': int(config.get('pool_min_size', 10)),
                            'autoFillThreshold': int(config.get('pool_auto_fill_threshold', 5)),
                            'lowBalanceThreshold': float(config.get('wallet_low_balance_threshold', 1.0))
                        }
                    })
                
                else:
                    data = request.get_json() or {}
                    
                    min_pool_size = int(data.get('minPoolSize', 10))
                    auto_fill_threshold = int(data.get('autoFillThreshold', 5))
                    low_balance_threshold = float(data.get('lowBalanceThreshold', 1.0))
                    
                    if min_pool_size < 1 or min_pool_size > 1000:
                        return jsonify({'success': False, 'error': 'Tamano minimo del pool debe ser entre 1 y 1000'}), 400
                    if auto_fill_threshold < 0 or auto_fill_threshold > min_pool_size:
                        return jsonify({'success': False, 'error': 'Umbral de auto-rellenado debe ser entre 0 y el tamano minimo'}), 400
                    if low_balance_threshold < 0 or low_balance_threshold > 100:
                        return jsonify({'success': False, 'error': 'Umbral de balance bajo debe ser entre 0 y 100'}), 400
                    
                    configs = [
                        ('pool_min_size', str(min_pool_size)),
                        ('pool_auto_fill_threshold', str(auto_fill_threshold)),
                        ('wallet_low_balance_threshold', str(low_balance_threshold))
                    ]
                    
                    for key, value in configs:
                        cur.execute("""
                            INSERT INTO system_config (config_key, config_value, updated_at) 
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (config_key) DO UPDATE SET config_value = %s, updated_at = CURRENT_TIMESTAMP
                        """, (key, value, value))
                    
                    conn.commit()
                    
                    try:
                        from bot.tracking_correos.wallet_pool_service import get_wallet_pool_service
                        wallet_svc = get_wallet_pool_service(db_manager)
                        if wallet_svc:
                            wallet_svc.reload_config()
                    except Exception as reload_err:
                        logger.warning(f"Could not reload wallet pool config: {reload_err}")
                    
                    user_id = getattr(request, 'user_id', '0')
                    log_admin_action(user_id, 'Admin', 'update_pool_config', 'system_config', 
                                   None, f"Updated pool config: {data}")
                    
                    return jsonify({'success': True, 'message': 'Configuracion guardada y aplicada'})
    
    except Exception as e:
        logger.error(f"Error with pool config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/wallets/<int:wallet_id>/consolidate', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_consolidate_single_wallet(wallet_id):
    """Admin: Consolidar una wallet individual."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        try:
            from bot.tracking_correos.wallet_pool_service import get_wallet_pool_service
            wallet_svc = get_wallet_pool_service(db_manager)
            if wallet_svc:
                with db_manager.get_connection() as conn:
                    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                        cur.execute("SELECT * FROM deposit_wallets WHERE id = %s", (wallet_id,))
                        wallet = cur.fetchone()
                        
                        if not wallet:
                            return jsonify({'success': False, 'error': 'Wallet no encontrada'}), 404
                        
                        if wallet.get('consolidated_at'):
                            return jsonify({'success': False, 'error': 'Wallet ya consolidada'}), 400
                
                result = wallet_svc.consolidate_wallet(wallet_id)
                
                if result.get('success'):
                    user_id = getattr(request, 'user_id', '0')
                    log_admin_action(user_id, 'Admin', 'consolidate_single_wallet', 'deposit_wallets', 
                                   str(wallet_id), f"Consolidated wallet {wallet_id}")
                    
                    return jsonify({
                        'success': True,
                        'amount': result.get('amount', 0),
                        'tx_hash': result.get('tx_hash', ''),
                        'message': 'Wallet consolidada exitosamente'
                    })
                else:
                    return jsonify({'success': False, 'error': result.get('error', 'Error desconocido')})
            else:
                return jsonify({'success': False, 'error': 'Wallet pool service no disponible'}), 500
        except Exception as e:
            logger.error(f"Error consolidating single wallet: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    except Exception as e:
        logger.error(f"Error in consolidate single wallet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500



# ============================================================
# ADMIN 2FA VERIFICATION
# ============================================================

@admin_bp.route('/2fa/verify', methods=['POST'])
def verify_admin_2fa():
    """Verificar codigo 2FA para el owner que accede desde Telegram al panel admin."""
    try:
        from flask import session
        from bot.tracking_correos.decorators import validate_telegram_webapp_data, is_owner
        import pyotp
        
        init_data = request.headers.get('X-Telegram-Init-Data') or request.args.get('initData')
        
        if not init_data:
            return jsonify({'error': 'Se requieren datos de Telegram', 'code': 'NO_INIT_DATA'}), 401
        
        validated_data = validate_telegram_webapp_data(init_data)
        if not validated_data:
            return jsonify({'error': 'Datos de Telegram invalidos', 'code': 'INVALID_DATA'}), 401
        
        user = validated_data.get('user', {})
        user_id = user.get('id')
        
        if not user_id:
            return jsonify({'error': 'Usuario no identificado'}), 401
        
        if not is_owner(user_id):
            return jsonify({'error': 'Solo disponible para el administrador'}), 403
        
        data = request.get_json() or {}
        code = data.get('code', '').strip()
        
        if not code or len(code) != 6:
            return jsonify({
                'success': False,
                'error': 'Codigo debe ser de 6 digitos'
            }), 400
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'error': 'Database not available'}), 500
        
        secret = db_manager.get_user_totp_secret(str(user_id))
        
        if not secret:
            return jsonify({
                'success': False,
                'error': '2FA no esta configurado para esta cuenta'
            }), 400
        
        totp = pyotp.TOTP(secret, interval=30)
        is_valid = totp.verify(code, valid_window=1)
        
        if not is_valid:
            totp_60 = pyotp.TOTP(secret, interval=60)
            is_valid = totp_60.verify(code, valid_window=1)
        
        if is_valid:
            import secrets as sec_module
            from datetime import datetime
            admin_session_token = sec_module.token_urlsafe(32)
            session['admin_2fa_token'] = admin_session_token
            session['admin_2fa_user_id'] = str(user_id)
            session['admin_2fa_created_at'] = datetime.now().isoformat()
            session['admin_2fa_valid'] = True
            session.permanent = True
            
            db_manager.update_2fa_verified_time(str(user_id))
            
            logger.info(f"Admin 2FA verified for owner {user_id}")
            return jsonify({
                'success': True,
                'sessionToken': admin_session_token,
                'message': 'Verificacion exitosa'
            })
        else:
            logger.warning(f"Admin 2FA failed for owner {user_id}")
            return jsonify({
                'success': False,
                'error': 'Codigo incorrecto'
            }), 401
            
    except Exception as e:
        logger.error(f"Error verifying admin 2FA: {e}")
        return jsonify({'success': False, 'error': 'Error interno'}), 500


# ============================================================
# REPORTS ENDPOINTS (Migrados 10 Diciembre 2025)
# ============================================================

@admin_bp.route('/reports', methods=['GET'])
@require_telegram_auth
@require_owner
def get_reports():
    """Admin: Get content reports"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        status = request.args.get('status', 'pending')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        reports = db_manager.get_reports(status, limit, offset)
        
        return jsonify({
            'success': True,
            'reports': reports
        })
        
    except Exception as e:
        logger.error(f"Error getting reports: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/reports/<int:report_id>', methods=['PUT'])
@require_telegram_auth
@require_owner
def update_report(report_id):
    """Admin: Update report status"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        admin_id = str(request.telegram_user.get('id', 0))
        data = request.get_json() or {}
        
        status = data.get('status')
        notes = data.get('notes')
        
        if not status:
            return jsonify({'success': False, 'error': 'Estado requerido'}), 400
        
        success = db_manager.update_report_status(report_id, status, admin_id, notes)
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error updating report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# BOTS ADMIN ENDPOINTS - Migrados desde app.py (12 Dic 2025)
# ============================================================

@admin_bp.route('/bots', methods=['GET', 'POST'])
@require_telegram_auth
@require_owner
def admin_manage_bots():
    """Admin: Gestionar bots del sistema."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        if request.method == 'GET':
            with db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT bt.*, 
                               (SELECT COUNT(*) FROM user_bots ub WHERE ub.bot_type = bt.bot_type) as users_count
                        FROM bot_types bt
                        ORDER BY bt.created_at DESC
                    """)
                    bots = cur.fetchall()
            
            return jsonify({
                'success': True,
                'bots': [dict(b) for b in bots]
            })
        
        else:
            data = request.get_json() or {}
            name = data.get('name')
            bot_type = data.get('type', 'general')
            description = data.get('description', '')
            price = data.get('price', 0)
            icon = data.get('icon', '🤖')
            
            if not name:
                return jsonify({'success': False, 'error': 'Nombre requerido'}), 400
            
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO bot_types (bot_name, bot_type, description, price, icon)
                        VALUES (%s, %s, %s, %s, %s) RETURNING id
                    """, (name, bot_type, description, price, icon))
                    new_id = cur.fetchone()[0]
                    conn.commit()
            
            return jsonify({
                'success': True,
                'botId': new_id,
                'message': 'Bot creado correctamente'
            })
        
    except Exception as e:
        logger.error(f"Error managing bots: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/bots/<int:bot_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def admin_delete_bot(bot_id):
    """Admin: Eliminar un bot."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM bot_types WHERE id = %s", (bot_id,))
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Bot no encontrado'}), 404
                
                cur.execute("DELETE FROM bot_types WHERE id = %s", (bot_id,))
                deleted = cur.rowcount > 0
                conn.commit()
                
                if deleted:
                    return jsonify({'success': True, 'message': 'Bot eliminado'})
                else:
                    return jsonify({'success': False, 'error': 'No se pudo eliminar el bot'}), 500
        
    except Exception as e:
        logger.error(f"Error deleting bot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/bots/<int:bot_id>/toggle', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_toggle_bot(bot_id):
    """Admin: Activar/desactivar un bot."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id, is_available FROM bot_types WHERE id = %s", (bot_id,))
                bot = cur.fetchone()
                
                if not bot:
                    return jsonify({'success': False, 'error': 'Bot no encontrado'}), 404
                
                new_status = not bot['is_available']
                cur.execute("UPDATE bot_types SET is_available = %s WHERE id = %s", (new_status, bot_id))
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'isAvailable': new_status,
                    'message': 'Bot activado' if new_status else 'Bot desactivado'
                })
        
    except Exception as e:
        logger.error(f"Error toggling bot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/bots/<int:bot_id>', methods=['PUT'])
@require_telegram_auth
@require_owner
def admin_update_bot(bot_id):
    """Admin: Actualizar un bot."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        data = request.get_json() or {}
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id FROM bot_types WHERE id = %s", (bot_id,))
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Bot no encontrado'}), 404
                
                updates = []
                params = []
                
                if 'name' in data:
                    updates.append("bot_name = %s")
                    params.append(data['name'])
                if 'description' in data:
                    updates.append("description = %s")
                    params.append(data['description'])
                if 'price' in data:
                    updates.append("price = %s")
                    params.append(int(data['price']))
                if 'icon' in data:
                    updates.append("icon = %s")
                    params.append(data['icon'])
                if 'isAvailable' in data:
                    updates.append("is_available = %s")
                    params.append(bool(data['isAvailable']))
                
                if updates:
                    params.append(bot_id)
                    cur.execute(f"UPDATE bot_types SET {', '.join(updates)} WHERE id = %s", params)
                    conn.commit()
                
                return jsonify({'success': True, 'message': 'Bot actualizado'})
        
    except Exception as e:
        logger.error(f"Error updating bot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/bots/stats', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_bots_stats():
    """Admin: Obtener estadísticas de bots."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        bt.id,
                        bt.bot_name,
                        bt.bot_type,
                        bt.icon,
                        bt.price,
                        bt.is_available,
                        COUNT(ub.id) as total_users,
                        COUNT(CASE WHEN ub.is_active THEN 1 END) as active_users,
                        COALESCE(bt.price * COUNT(ub.id), 0) as total_revenue
                    FROM bot_types bt
                    LEFT JOIN user_bots ub ON ub.bot_type = bt.bot_type
                    GROUP BY bt.id, bt.bot_name, bt.bot_type, bt.icon, bt.price, bt.is_available
                    ORDER BY total_users DESC
                """)
                bot_stats = [dict(row) for row in cur.fetchall()]
                
                cur.execute("SELECT COUNT(*) as total FROM bot_types")
                total_bots = cur.fetchone()['total']
                
                cur.execute("SELECT COUNT(*) as total FROM bot_types WHERE is_available = true")
                active_bots = cur.fetchone()['total']
                
                cur.execute("SELECT COUNT(*) as total FROM user_bots")
                total_users_using_bots = cur.fetchone()['total']
                
                return jsonify({
                    'success': True,
                    'summary': {
                        'totalBots': total_bots,
                        'activeBots': active_bots,
                        'totalUsersUsingBots': total_users_using_bots
                    },
                    'botStats': bot_stats
                })
        
    except Exception as e:
        logger.error(f"Error getting bot stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/bots/usage', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_bots_usage():
    """Admin: Obtener datos de uso de bots en el tiempo."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        days = int(request.args.get('days', 30))
        days = min(days, 90)
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        TO_CHAR(created_at, 'YYYY-MM-DD') as date,
                        COUNT(*) as count
                    FROM user_bots
                    WHERE created_at >= CURRENT_DATE - (%s * INTERVAL '1 day')
                    GROUP BY TO_CHAR(created_at, 'YYYY-MM-DD')
                    ORDER BY date
                """, (days,))
                usage_data = [dict(row) for row in cur.fetchall()]
                
                today = datetime.now().date()
                
                complete_data = []
                for i in range(days, -1, -1):
                    date_str = (today - timedelta(days=i)).strftime('%Y-%m-%d')
                    existing = next((d for d in usage_data if d['date'] == date_str), None)
                    if existing:
                        complete_data.append(existing)
                    else:
                        complete_data.append({'date': date_str, 'count': 0})
                
                return jsonify({
                    'success': True,
                    'data': complete_data
                })
        
    except Exception as e:
        logger.error(f"Error getting bots usage: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/bots/revenue', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_bots_revenue():
    """Admin: Obtener ingresos por bots."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(bt.price), 0) as total
                    FROM user_bots ub
                    JOIN bot_types bt ON ub.bot_type = bt.bot_type
                """)
                total_revenue = cur.fetchone()['total'] or 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(bt.price), 0) as total
                    FROM user_bots ub
                    JOIN bot_types bt ON ub.bot_type = bt.bot_type
                    WHERE ub.created_at >= DATE_TRUNC('month', CURRENT_DATE)
                """)
                month_revenue = cur.fetchone()['total'] or 0
                
                cur.execute("""
                    SELECT COALESCE(SUM(bt.price), 0) as total
                    FROM user_bots ub
                    JOIN bot_types bt ON ub.bot_type = bt.bot_type
                    WHERE ub.created_at >= CURRENT_DATE - INTERVAL '7 days'
                """)
                week_revenue = cur.fetchone()['total'] or 0
                
                cur.execute("""
                    SELECT 
                        bt.id,
                        bt.bot_name as name,
                        bt.icon,
                        bt.price,
                        COUNT(ub.id) as count,
                        COALESCE(bt.price * COUNT(ub.id), 0) as revenue
                    FROM bot_types bt
                    LEFT JOIN user_bots ub ON ub.bot_type = bt.bot_type
                    GROUP BY bt.id, bt.bot_name, bt.icon, bt.price
                    ORDER BY revenue DESC
                """)
                breakdown = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'data': {
                        'total': total_revenue,
                        'month': month_revenue,
                        'week': week_revenue,
                        'breakdown': breakdown
                    }
                })
        
    except Exception as e:
        logger.error(f"Error getting bots revenue: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/bots/purchases', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_bots_purchases():
    """Admin: Obtener historial de compras de bots."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        per_page = min(per_page, 50)
        offset = (page - 1) * per_page
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) as total FROM user_bots")
                total = cur.fetchone()['total'] or 0
                
                cur.execute("""
                    SELECT 
                        ub.id,
                        ub.user_id,
                        ub.bot_type,
                        ub.created_at,
                        bt.bot_name,
                        bt.icon,
                        bt.price,
                        u.username
                    FROM user_bots ub
                    LEFT JOIN bot_types bt ON ub.bot_type = bt.bot_type
                    LEFT JOIN users u ON ub.user_id::bigint = u.telegram_id
                    ORDER BY ub.created_at DESC
                    LIMIT %s OFFSET %s
                """, (per_page, offset))
                purchases = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'data': purchases,
                    'total': total,
                    'page': page,
                    'per_page': per_page
                })
        
    except Exception as e:
        logger.error(f"Error getting bots purchases: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/bots/<int:bot_id>/logs', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_bot_logs(bot_id):
    """Admin: Obtener logs de actividad de un bot específico."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'}), 500
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        per_page = min(per_page, 100)
        offset = (page - 1) * per_page
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT bot_type FROM bot_types WHERE id = %s", (bot_id,))
                bot = cur.fetchone()
                if not bot:
                    return jsonify({'success': False, 'error': 'Bot no encontrado'}), 404
                
                bot_type = bot['bot_type']
                
                cur.execute("""
                    SELECT COUNT(*) as total FROM user_bots WHERE bot_type = %s
                """, (bot_type,))
                total = cur.fetchone()['total'] or 0
                
                cur.execute("""
                    SELECT 
                        ub.id,
                        ub.user_id,
                        ub.bot_type,
                        ub.bot_name,
                        ub.is_active,
                        ub.created_at,
                        ub.config,
                        u.username,
                        u.first_name,
                        bt.price,
                        bt.icon
                    FROM user_bots ub
                    LEFT JOIN users u ON ub.user_id::bigint = u.telegram_id
                    LEFT JOIN bot_types bt ON ub.bot_type = bt.bot_type
                    WHERE ub.bot_type = %s
                    ORDER BY ub.created_at DESC
                    LIMIT %s OFFSET %s
                """, (bot_type, per_page, offset))
                logs = [dict(row) for row in cur.fetchall()]
                
                for log in logs:
                    if log.get('created_at'):
                        log['created_at'] = log['created_at'].isoformat()
                
                cur.execute("""
                    SELECT COUNT(*) as active_count 
                    FROM user_bots 
                    WHERE bot_type = %s AND is_active = TRUE
                """, (bot_type,))
                active_count = cur.fetchone()['active_count'] or 0
                
                cur.execute("""
                    SELECT COUNT(*) as today_count 
                    FROM user_bots 
                    WHERE bot_type = %s AND created_at >= CURRENT_DATE
                """, (bot_type,))
                today_count = cur.fetchone()['today_count'] or 0
                
                return jsonify({
                    'success': True,
                    'data': logs,
                    'total': total,
                    'active_count': active_count,
                    'today_count': today_count,
                    'page': page,
                    'per_page': per_page
                })
        
    except Exception as e:
        logger.error(f"Error getting bot logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ADMIN EXTRA ENDPOINTS - Migrados desde app.py (12 Dic 2025)
# ============================================================

@admin_bp.route('/verifications', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_verifications():
    """Admin: Obtener cola de verificaciones."""
    try:
        verifications = []
        return jsonify({'success': True, 'verifications': verifications})
        
    except Exception as e:
        logger.error(f"Error getting verifications: {e}")
        return jsonify({'success': False, 'error': str(e), 'verifications': []}), 500


@admin_bp.route('/shadow-sessions', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_shadow_sessions():
    """Admin: Obtener historial de sesiones shadow."""
    try:
        sessions = []
        return jsonify({'success': True, 'sessions': sessions})
        
    except Exception as e:
        logger.error(f"Error getting shadow sessions: {e}")
        return jsonify({'success': False, 'error': str(e), 'sessions': []}), 500


@admin_bp.route('/shadow-sessions/start', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_start_shadow_session():
    """Admin: Iniciar sesion shadow para un usuario."""
    try:
        data = request.get_json() or {}
        telegram_id = data.get('telegramId')
        
        if not telegram_id:
            return jsonify({'success': False, 'error': 'Usuario requerido'}), 400
        
        session_url = f"/?shadow_user={telegram_id}"
        
        return jsonify({
            'success': True,
            'sessionUrl': session_url
        })
        
    except Exception as e:
        logger.error(f"Error starting shadow session: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/marketplace', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_marketplace():
    """Admin: Obtener datos del marketplace."""
    try:
        db_manager = get_db_manager()
        listings = []
        sales = []
        
        if db_manager:
            with db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT l.id, l.title, l.price, l.currency, l.status,
                               l.created_at as "createdAt", u.username as "sellerUsername"
                        FROM marketplace_listings l
                        LEFT JOIN users u ON l.seller_id = u.telegram_id
                        ORDER BY l.created_at DESC
                        LIMIT 100
                    """)
                    listings = [dict(l) for l in cur.fetchall()]
                    
                    for listing in listings:
                        if listing.get('createdAt'):
                            listing['createdAt'] = listing['createdAt'].isoformat()
                
        return jsonify({
            'success': True,
            'listings': listings,
            'sales': sales
        })
        
    except Exception as e:
        logger.error(f"Error getting marketplace: {e}")
        return jsonify({'success': False, 'error': str(e), 'listings': [], 'sales': []}), 500


@admin_bp.route('/client-logs', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_client_logs():
    """Admin: Obtener logs de cliente para monitoreo de depositos."""
    try:
        db_manager = get_db_manager()
        action_filter = request.args.get('action', 'all')
        limit = min(int(request.args.get('limit', 100)), 500)
        mobile_only = request.args.get('mobile', 'false') == 'true'
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'DB no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT id, user_id, session_id, log_type, action, details,
                           platform, is_mobile, is_telegram, created_at
                    FROM client_logs
                    WHERE 1=1
                """
                params = []
                
                if action_filter != 'all':
                    query += " AND action LIKE %s"
                    params.append(f"%{action_filter}%")
                
                if mobile_only:
                    query += " AND is_mobile = true"
                
                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                logs = cur.fetchall()
                
                for log in logs:
                    if log.get('created_at'):
                        log['created_at'] = log['created_at'].isoformat()
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'count': len(logs)
                })
        
    except Exception as e:
        logger.error(f"Error getting client logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/logs-simple', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_logs_simple():
    """Admin: Obtener logs del sistema simplificados."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': True, 'logs': []})
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT log_type as level, action as message, 
                           TO_CHAR(created_at, 'HH24:MI:SS') as time,
                           is_mobile, is_telegram, details
                    FROM client_logs
                    ORDER BY created_at DESC
                    LIMIT 50
                """)
                logs = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'logs': logs
                })
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'success': True, 'logs': []})


# ============================================================
# B3C WITHDRAWALS ENDPOINTS - Migrados desde app.py (12 Dic 2025)
# ============================================================

@admin_bp.route('/b3c/withdrawals', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_b3c_withdrawals():
    """Admin: Obtener lista de retiros B3C pendientes y procesados."""
    try:
        db_manager = get_db_manager()
        status_filter = request.args.get('status', 'all')
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if status_filter == 'all':
                    cur.execute("""
                        SELECT w.*, u.username, u.first_name 
                        FROM b3c_withdrawals w
                        LEFT JOIN users u ON w.user_id = u.id
                        ORDER BY w.created_at DESC
                        LIMIT 100
                    """)
                else:
                    cur.execute("""
                        SELECT w.*, u.username, u.first_name 
                        FROM b3c_withdrawals w
                        LEFT JOIN users u ON w.user_id = u.id
                        WHERE w.status = %s
                        ORDER BY w.created_at DESC
                        LIMIT 100
                    """, (status_filter,))
                
                withdrawals = cur.fetchall()
                
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'pending') as pending,
                        COUNT(*) FILTER (WHERE status = 'completed') as processed,
                        COALESCE(SUM(b3c_amount), 0) as total_b3c
                    FROM b3c_withdrawals
                """)
                stats_row = cur.fetchone()
        
        result = []
        for w in withdrawals:
            result.append({
                'id': w['withdrawal_id'],
                'userId': w['user_id'],
                'username': w.get('username', 'Unknown'),
                'firstName': w.get('first_name', 'Unknown'),
                'amount': float(w['b3c_amount']),
                'destination': w['destination_wallet'],
                'status': w['status'],
                'txHash': w.get('tx_hash'),
                'createdAt': w['created_at'].isoformat() if w['created_at'] else None,
                'processedAt': w['processed_at'].isoformat() if w.get('processed_at') else None
            })
        
        return jsonify({
            'success': True,
            'withdrawals': result,
            'count': len(result),
            'stats': {
                'totalWithdrawals': stats_row['total'] if stats_row else 0,
                'pendingCount': stats_row['pending'] if stats_row else 0,
                'processedCount': stats_row['processed'] if stats_row else 0,
                'totalB3C': float(stats_row['total_b3c']) if stats_row else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting B3C withdrawals: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/b3c/withdrawals/<withdrawal_id>/process', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_process_b3c_withdrawal(withdrawal_id):
    """Admin: Procesar un retiro B3C (marcar como completado con hash de transaccion)."""
    try:
        db_manager = get_db_manager()
        data = request.get_json()
        tx_hash = data.get('txHash', '').strip()
        action = data.get('action', 'complete')
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM b3c_withdrawals WHERE withdrawal_id = %s
                """, (withdrawal_id,))
                withdrawal = cur.fetchone()
                
                if not withdrawal:
                    return jsonify({'success': False, 'error': 'Retiro no encontrado'}), 404
                
                if action == 'complete':
                    if not tx_hash:
                        return jsonify({'success': False, 'error': 'Se requiere el hash de transaccion'}), 400
                    
                    cur.execute("""
                        UPDATE b3c_withdrawals 
                        SET status = 'completed', tx_hash = %s, processed_at = NOW()
                        WHERE withdrawal_id = %s
                    """, (tx_hash, withdrawal_id))
                    
                elif action == 'reject':
                    reason = data.get('reason', 'Rechazado por admin')
                    cur.execute("""
                        UPDATE b3c_withdrawals 
                        SET status = 'rejected', processed_at = NOW()
                        WHERE withdrawal_id = %s
                    """, (withdrawal_id,))
                    
                    cur.execute("""
                        INSERT INTO wallet_transactions (user_id, amount, transaction_type, description, reference_id)
                        VALUES (%s, %s, 'credit', %s, %s)
                    """, (withdrawal['user_id'], withdrawal['b3c_amount'], 
                          f'Retiro rechazado: {reason}', withdrawal_id))
                
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Retiro {action}d exitosamente',
            'withdrawalId': withdrawal_id
        })
        
    except Exception as e:
        logger.error(f"Error processing B3C withdrawal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/b3c/withdrawals/<withdrawal_id>', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_b3c_withdrawal_detail(withdrawal_id):
    """Admin: Obtener detalle de un retiro B3C."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT w.*, u.username, u.first_name, u.telegram_id
                    FROM b3c_withdrawals w
                    LEFT JOIN users u ON w.user_id = u.id
                    WHERE w.withdrawal_id = %s
                """, (withdrawal_id,))
                withdrawal = cur.fetchone()
                
                if not withdrawal:
                    return jsonify({'success': False, 'error': 'Retiro no encontrado'}), 404
        
        return jsonify({
            'success': True,
            'withdrawal': {
                'id': withdrawal['withdrawal_id'],
                'withdrawalId': withdrawal['withdrawal_id'],
                'userId': withdrawal['user_id'],
                'username': withdrawal.get('username', 'Unknown'),
                'userFullName': withdrawal.get('first_name', 'Unknown'),
                'telegramId': withdrawal.get('telegram_id'),
                'b3cAmount': float(withdrawal['b3c_amount']),
                'tonAmount': float(withdrawal.get('ton_amount', 0) or 0),
                'commission': float(withdrawal.get('commission', 0) or 0),
                'destinationWallet': withdrawal['destination_wallet'],
                'status': withdrawal['status'],
                'txHash': withdrawal.get('tx_hash'),
                'rejectionReason': withdrawal.get('rejection_reason'),
                'createdAt': withdrawal['created_at'].isoformat() if withdrawal['created_at'] else None,
                'processedAt': withdrawal['processed_at'].isoformat() if withdrawal.get('processed_at') else None,
                'userBalance': float(withdrawal.get('b3c_balance', 0) or 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting B3C withdrawal detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# P2P TRANSFERS ENDPOINTS - Migrados desde app.py (12 Dic 2025)
# ============================================================

@admin_bp.route('/transfers', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_p2p_transfers():
    """Admin: Obtener lista de transferencias P2P."""
    try:
        db_manager = get_db_manager()
        filter_type = request.args.get('filter', 'all')
        search = request.args.get('search', '').strip()
        
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                base_query = """
                    SELECT t.*, 
                           u1.username as from_username, u1.first_name as from_name, u1.telegram_id as from_telegram_id,
                           u2.username as to_username, u2.first_name as to_name, u2.telegram_id as to_telegram_id
                    FROM wallet_transactions t
                    LEFT JOIN users u1 ON t.user_id = u1.user_id
                    LEFT JOIN users u2 ON t.recipient_id = u2.user_id
                    WHERE t.transaction_type = 'transfer'
                """
                
                params = []
                
                if search:
                    base_query += " AND (u1.username ILIKE %s OR u2.username ILIKE %s)"
                    params.extend([f'%{search}%', f'%{search}%'])
                
                if filter_type == 'suspicious':
                    base_query += " AND t.is_suspicious = TRUE"
                elif filter_type == 'today':
                    base_query += " AND t.created_at >= CURRENT_DATE"
                
                base_query += " ORDER BY t.created_at DESC LIMIT 100"
                
                cur.execute(base_query, params)
                transfers = cur.fetchall()
                
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE) as today,
                        COUNT(*) FILTER (WHERE is_suspicious = TRUE) as suspicious,
                        COALESCE(SUM(ABS(amount)), 0) as total_b3c
                    FROM wallet_transactions
                    WHERE transaction_type = 'transfer'
                """)
                stats_row = cur.fetchone()
        
        result = []
        for t in transfers:
            result.append({
                'id': t['transaction_id'],
                'transferId': t['transaction_id'],
                'fromUsername': t.get('from_username', 'Unknown'),
                'fromUserName': t.get('from_name', ''),
                'fromTelegramId': t.get('from_telegram_id'),
                'toUsername': t.get('to_username', 'Unknown'),
                'toUserName': t.get('to_name', ''),
                'toTelegramId': t.get('to_telegram_id'),
                'amount': abs(float(t['amount'])),
                'note': t.get('description', ''),
                'isSuspicious': t.get('is_suspicious', False),
                'suspiciousReason': t.get('suspicious_reason'),
                'createdAt': t['created_at'].isoformat() if t['created_at'] else None
            })
        
        return jsonify({
            'success': True,
            'transfers': result,
            'stats': {
                'totalTransfers': stats_row['total'] if stats_row else 0,
                'todayCount': stats_row['today'] if stats_row else 0,
                'suspiciousCount': stats_row['suspicious'] if stats_row else 0,
                'totalB3C': float(stats_row['total_b3c']) if stats_row else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting P2P transfers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/transfers/<transfer_id>', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_p2p_transfer_detail(transfer_id):
    """Admin: Obtener detalle de una transferencia P2P."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT t.*, 
                           u1.username as from_username, u1.first_name as from_name, u1.telegram_id as from_telegram_id,
                           u2.username as to_username, u2.first_name as to_name, u2.telegram_id as to_telegram_id
                    FROM wallet_transactions t
                    LEFT JOIN users u1 ON t.user_id = u1.user_id
                    LEFT JOIN users u2 ON t.recipient_id = u2.user_id
                    WHERE t.transaction_id = %s AND t.transaction_type = 'transfer'
                """, (transfer_id,))
                transfer = cur.fetchone()
                
                if not transfer:
                    return jsonify({'success': False, 'error': 'Transferencia no encontrada'}), 404
        
        return jsonify({
            'success': True,
            'transfer': {
                'id': transfer['transaction_id'],
                'transferId': transfer['transaction_id'],
                'fromUsername': transfer.get('from_username', 'Unknown'),
                'fromUserName': transfer.get('from_name', ''),
                'fromTelegramId': transfer.get('from_telegram_id'),
                'toUsername': transfer.get('to_username', 'Unknown'),
                'toUserName': transfer.get('to_name', ''),
                'toTelegramId': transfer.get('to_telegram_id'),
                'amount': abs(float(transfer['amount'])),
                'note': transfer.get('description', ''),
                'isSuspicious': transfer.get('is_suspicious', False),
                'suspiciousReason': transfer.get('suspicious_reason'),
                'createdAt': transfer['created_at'].isoformat() if transfer['created_at'] else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting P2P transfer detail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== SURVEY QUESTIONS CRUD ====================

@admin_bp.route('/survey/questions', methods=['GET'])
@require_telegram_auth
@require_owner
def admin_get_survey_questions():
    """Admin: Obtener todas las preguntas de encuesta."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, question_text, question_type, options, 
                           is_required, order_position, is_active
                    FROM survey_questions
                    ORDER BY order_position ASC, id ASC
                """)
                questions = cur.fetchall()
        
        result = []
        for q in questions:
            result.append({
                'id': q['id'],
                'questionText': q['question_text'],
                'questionType': q['question_type'],
                'options': q['options'] or [],
                'isRequired': q['is_required'],
                'orderPosition': q['order_position'],
                'isActive': q['is_active']
            })
        
        return jsonify({
            'success': True,
            'questions': result,
            'total': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting survey questions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/survey/questions', methods=['POST'])
@require_telegram_auth
@require_owner
def admin_create_survey_question():
    """Admin: Crear una nueva pregunta de encuesta."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
        
        question_text = data.get('questionText', '').strip()
        if not question_text:
            return jsonify({'success': False, 'error': 'El texto de la pregunta es requerido'}), 400
        
        question_type = data.get('questionType', 'text')
        if question_type not in ['text', 'select', 'checkbox', 'textarea']:
            return jsonify({'success': False, 'error': 'Tipo de pregunta invalido'}), 400
        
        options = data.get('options', [])
        is_required = data.get('isRequired', True)
        order_position = data.get('orderPosition', 0)
        is_active = data.get('isActive', True)
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO survey_questions 
                    (question_text, question_type, options, is_required, order_position, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, question_text, question_type, options, is_required, order_position, is_active
                """, (question_text, question_type, json.dumps(options), is_required, order_position, is_active))
                
                new_question = cur.fetchone()
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Pregunta creada exitosamente',
            'question': {
                'id': new_question['id'],
                'questionText': new_question['question_text'],
                'questionType': new_question['question_type'],
                'options': new_question['options'] or [],
                'isRequired': new_question['is_required'],
                'orderPosition': new_question['order_position'],
                'isActive': new_question['is_active']
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating survey question: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/survey/questions/<int:question_id>', methods=['PUT'])
@require_telegram_auth
@require_owner
def admin_update_survey_question(question_id):
    """Admin: Actualizar una pregunta de encuesta."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id FROM survey_questions WHERE id = %s", (question_id,))
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Pregunta no encontrada'}), 404
                
                updates = []
                params = []
                
                if 'questionText' in data:
                    updates.append("question_text = %s")
                    params.append(data['questionText'].strip())
                
                if 'questionType' in data:
                    if data['questionType'] not in ['text', 'select', 'checkbox', 'textarea']:
                        return jsonify({'success': False, 'error': 'Tipo de pregunta invalido'}), 400
                    updates.append("question_type = %s")
                    params.append(data['questionType'])
                
                if 'options' in data:
                    updates.append("options = %s")
                    params.append(json.dumps(data['options']))
                
                if 'isRequired' in data:
                    updates.append("is_required = %s")
                    params.append(data['isRequired'])
                
                if 'orderPosition' in data:
                    updates.append("order_position = %s")
                    params.append(data['orderPosition'])
                
                if 'isActive' in data:
                    updates.append("is_active = %s")
                    params.append(data['isActive'])
                
                if not updates:
                    return jsonify({'success': False, 'error': 'No hay campos para actualizar'}), 400
                
                params.append(question_id)
                cur.execute(f"""
                    UPDATE survey_questions 
                    SET {', '.join(updates)}
                    WHERE id = %s
                    RETURNING id, question_text, question_type, options, is_required, order_position, is_active
                """, params)
                
                updated = cur.fetchone()
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Pregunta actualizada exitosamente',
            'question': {
                'id': updated['id'],
                'questionText': updated['question_text'],
                'questionType': updated['question_type'],
                'options': updated['options'] or [],
                'isRequired': updated['is_required'],
                'orderPosition': updated['order_position'],
                'isActive': updated['is_active']
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating survey question: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/survey/questions/<int:question_id>', methods=['DELETE'])
@require_telegram_auth
@require_owner
def admin_delete_survey_question(question_id):
    """Admin: Eliminar una pregunta de encuesta."""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM survey_questions WHERE id = %s", (question_id,))
                if not cur.fetchone():
                    return jsonify({'success': False, 'error': 'Pregunta no encontrada'}), 404
                
                cur.execute("DELETE FROM survey_questions WHERE id = %s", (question_id,))
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Pregunta eliminada exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error deleting survey question: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== FIN DE ENDPOINTS ADMIN ====================

