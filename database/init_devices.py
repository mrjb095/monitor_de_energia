import sqlite3
from config import USERS_DB

def init_devices_db():
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()

    # Criar a tabela devices se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE NOT NULL,
            token TEXT NOT NULL
        )
    ''')

    # Adicionar dispositivos padrão (exemplo)
    dispositivos_iniciais = [
        ('ESP001', '9fGx2pL7qVb5Zr1C'),
    ]

    for device_id, token in dispositivos_iniciais:
        try:
            cursor.execute('INSERT INTO devices (device_id, token) VALUES (?, ?)', (device_id, token))
        except sqlite3.IntegrityError:
            print(f'Dispositivo {device_id} já existe, pulando...')

    conn.commit()
    conn.close()
    print('Tabela devices criada e dispositivos iniciais adicionados.')

if __name__ == '__main__':
    init_devices_db()
