import sqlite3
import psycopg2
from datetime import datetime

# Configuração dos bancos
SQLITE_DB = 'dados.db'

POSTGRESQL_CONFIG = {
    'dbname': 'monitor_energia',
    'user': 'energia_user',
    'password': 'monitor_817',
    'host': 'localhost',
    'port': 5432
}

def migrar_historico():
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()

    pg_conn = psycopg2.connect(**POSTGRESQL_CONFIG)
    pg_cursor = pg_conn.cursor()

    sqlite_cursor.execute('SELECT timestamp, corrente, tensao, potencia FROM historico')
    rows = sqlite_cursor.fetchall()
    print(f"Migrando {len(rows)} registros da tabela historico...")

    for row in rows:
        timestamp = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
        corrente = row[1]
        tensao = row[2]
        potencia = row[3]

        pg_cursor.execute(
            'INSERT INTO historico (timestamp, corrente, tensao, potencia) VALUES (%s, %s, %s, %s)',
            (timestamp, corrente, tensao, potencia)
        )

    pg_conn.commit()
    print("Histórico migrado com sucesso!")

    sqlite_conn.close()
    pg_conn.close()

def migrar_eventos():
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()

    pg_conn = psycopg2.connect(**POSTGRESQL_CONFIG)
    pg_cursor = pg_conn.cursor()

    sqlite_cursor.execute('SELECT timestamp, tipo, mensagem FROM eventos')
    rows = sqlite_cursor.fetchall()
    print(f"Migrando {len(rows)} registros da tabela eventos...")

    for row in rows:
        timestamp = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
        tipo = row[1]
        mensagem = row[2]

        pg_cursor.execute(
            'INSERT INTO eventos (timestamp, tipo, mensagem) VALUES (%s, %s, %s)',
            (timestamp, tipo, mensagem)
        )

    pg_conn.commit()
    print("Eventos migrados com sucesso!")

    sqlite_conn.close()
    pg_conn.close()

if __name__ == '__main__':
    migrar_historico()
    migrar_eventos()
