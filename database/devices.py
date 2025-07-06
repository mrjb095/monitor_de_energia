import sqlite3
from config import USERS_DB

def validar_dispositivo(device_id, token):
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT token FROM devices WHERE device_id = ?', (device_id,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0] == token:
        return True
    else:
        return False
