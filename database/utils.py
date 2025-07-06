from config import DADOS_DB, USERS_DB
import sqlite3

def salvar_historico(timestamp, corrente, tensao, potencia):
    conn = sqlite3.connect(DADOS_DB)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO historico (timestamp, corrente, tensao, potencia) VALUES (?, ?, ?, ?)',
                   (timestamp, corrente, tensao, potencia))
    conn.commit()
    conn.close()

def registrar_evento(timestamp, tipo, mensagem):
    conn = sqlite3.connect(DADOS_DB)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO eventos (timestamp, tipo, mensagem) VALUES (?, ?, ?)',
                   (timestamp, tipo, mensagem))
    conn.commit()
    conn.close()

def buscar_historico(query, params):
    conn = sqlite3.connect(DADOS_DB)
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def buscar_eventos(limit=50):
    conn = sqlite3.connect(DADOS_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, tipo, mensagem FROM eventos ORDER BY id DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_device_by_id(device_id=None):
    # Adapte para usar psycopg2 ou sqlite3 conforme seu banco atual
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    if device_id:
        cursor.execute('SELECT device_id, token, ip, port, last_seen FROM devices WHERE device_id = ?', (device_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(zip(['device_id','token','ip','port','last_seen'], row)) if row else None
    else:
        cursor.execute('SELECT device_id, token, ip, port, last_seen FROM devices')
        rows = cursor.fetchall()
        conn.close()
        return [ dict(zip(['device_id','token','ip','port','last_seen'], r)) for r in rows ]