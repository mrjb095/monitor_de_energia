from config import DADOS_DB, USERS_DB
from werkzeug.security import generate_password_hash
import sqlite3
import os

def init_users_db():
    novo = not os.path.exists(USERS_DB)
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()

    if novo:
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()
        print('✅ Banco de usuários criado com sucesso.')

        # Criar um usuário admin padrão
        hashed = generate_password_hash('admin')
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', hashed))
        conn.commit()
        print('✅ Usuário admin criado (senha: admin).')

    conn.close()


def init_dados_db():
    if not os.path.exists(DADOS_DB):
        conn = sqlite3.connect(DADOS_DB)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            corrente REAL,
            tensao REAL,
            potencia REAL
        )''')
        cursor.execute('''CREATE TABLE eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            tipo TEXT,
            mensagem TEXT
        )''')
        conn.commit()
        print('Banco de dados de medições criado.')

        cursor.execute('PRAGMA journal_mode=WAL;')
        modo_atual = cursor.fetchone()
        print(f"✅ Modo WAL ativado no SQLite: {modo_atual}")

        conn.close()
