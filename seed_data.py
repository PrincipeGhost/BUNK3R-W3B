#!/usr/bin/env python3
"""
Seed Data Script for BUNK3R-W3B Development
Creates sample data for testing the admin dashboard and other features.
"""
import os
import sys
import random
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

SAMPLE_USERNAMES = [
    'carlos_trader', 'maria_crypto', 'juan_b3c', 'ana_holder', 'pedro_wallet',
    'lucia_ton', 'miguel_dev', 'sofia_nft', 'diego_defi', 'valentina_stake',
    'alejandro_moon', 'camila_hodl', 'sebastian_pump', 'isabella_diamond', 'mateo_whale'
]

SAMPLE_FIRST_NAMES = [
    'Carlos', 'Maria', 'Juan', 'Ana', 'Pedro',
    'Lucia', 'Miguel', 'Sofia', 'Diego', 'Valentina',
    'Alejandro', 'Camila', 'Sebastian', 'Isabella', 'Mateo'
]

COUNTRIES = ['ES', 'MX', 'AR', 'CO', 'CL', 'PE', 'VE', 'EC', 'US', 'BR']
DEVICES = ['iOS', 'Android', 'Web Desktop', 'Web Mobile']


def generate_telegram_id():
    return random.randint(100000000, 999999999)


def generate_wallet_address():
    return 'EQ' + hashlib.sha256(os.urandom(32)).hexdigest()[:46]


def create_seed_data():
    """Create sample data for development testing."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        print("Creating seed data for BUNK3R-W3B...")
        
        created_user_ids = []
        now = datetime.now()
        
        for i, username in enumerate(SAMPLE_USERNAMES):
            telegram_id = generate_telegram_id()
            first_name = SAMPLE_FIRST_NAMES[i]
            created_at = now - timedelta(days=random.randint(1, 60))
            last_seen = now - timedelta(hours=random.randint(0, 72))
            country = random.choice(COUNTRIES)
            device = random.choice(DEVICES)
            ip_address = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
            
            cur.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
            if cur.fetchone():
                continue
            
            cur.execute("""
                INSERT INTO users (
                    telegram_id, username, first_name, created_at, last_seen,
                    country, device_type, last_ip, is_verified, is_active
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                telegram_id, username, first_name, created_at, last_seen,
                country, device, ip_address, random.choice([True, False]), True
            ))
            result = cur.fetchone()
            if result:
                user_id = result[0]
                created_user_ids.append(user_id)
                
                cur.execute("""
                    INSERT INTO user_wallets (user_id, b3c_balance, ton_address, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id) DO NOTHING
                """, (
                    user_id,
                    Decimal(str(random.uniform(0, 10000))),
                    generate_wallet_address(),
                    created_at
                ))
        
        print(f"  Created {len(created_user_ids)} sample users")
        
        tx_count = 0
        for user_id in created_user_ids:
            num_transactions = random.randint(1, 10)
            for _ in range(num_transactions):
                tx_type = random.choice(['deposit', 'withdrawal', 'transfer', 'purchase'])
                amount = Decimal(str(random.uniform(10, 1000)))
                created_at = now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
                
                cur.execute("""
                    INSERT INTO wallet_transactions (
                        user_id, amount, transaction_type, status, created_at, description
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    user_id, amount, tx_type, 
                    random.choice(['completed', 'pending', 'failed']),
                    created_at,
                    f"Sample {tx_type} transaction"
                ))
                tx_count += 1
        
        print(f"  Created {tx_count} sample transactions")
        
        alert_types = ['warning', 'danger', 'info']
        alert_messages = [
            'Multiple login attempts detected',
            'Unusual transaction pattern detected',
            'New device login from unusual location',
            'Large withdrawal request pending approval',
            'System performance degradation detected'
        ]
        
        for i in range(5):
            cur.execute("""
                INSERT INTO security_alerts (
                    alert_type, description, is_resolved, created_at
                )
                VALUES (%s, %s, %s, %s)
            """, (
                random.choice(alert_types),
                random.choice(alert_messages),
                random.choice([True, False]),
                now - timedelta(hours=random.randint(1, 48))
            ))
        
        print("  Created 5 sample security alerts")
        
        conn.commit()
        print("\nSeed data created successfully!")
        print(f"  Total users: {len(created_user_ids)}")
        print(f"  Total transactions: {tx_count}")
        print("  Total alerts: 5")
        
    except Exception as e:
        conn.rollback()
        print(f"Error creating seed data: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def clear_seed_data():
    """Remove all seed data (for testing purposes)."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        print("Clearing seed data...")
        
        cur.execute("DELETE FROM wallet_transactions WHERE description LIKE 'Sample%'")
        deleted_tx = cur.rowcount
        
        cur.execute("DELETE FROM security_alerts WHERE description IN (%s, %s, %s, %s, %s)", (
            'Multiple login attempts detected',
            'Unusual transaction pattern detected',
            'New device login from unusual location',
            'Large withdrawal request pending approval',
            'System performance degradation detected'
        ))
        deleted_alerts = cur.rowcount
        
        conn.commit()
        print(f"  Deleted {deleted_tx} transactions")
        print(f"  Deleted {deleted_alerts} alerts")
        print("Seed data cleared successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error clearing seed data: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--clear':
        clear_seed_data()
    else:
        create_seed_data()
        print("\nTo clear seed data, run: python seed_data.py --clear")
