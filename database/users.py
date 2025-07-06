import sqlite3
from config import USERS_DB
from werkzeug.security import generate_password_hash, check_password_hash

def criar_usuario(username, password):
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    hash_senha = generate_password_hash(password)
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_senha))
    conn.commit()
    conn.close()

def validar_usuario(username, password):
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()

    if row and check_password_hash(row[0], password):
        return True
    return False

def usuario_existe(username):
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    return row is not None
