import sqlite3
import numpy as np
from config import DADOS_DB

def calcular_estatisticas_periodo(inicio, fim):
    conn = sqlite3.connect(DADOS_DB)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT corrente, tensao, potencia
        FROM historico
        WHERE timestamp BETWEEN ? AND ?
    ''', (inicio, fim))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    correntes = np.array([r[0] for r in rows])
    tensoens = np.array([r[1] for r in rows])
    potencias = np.array([r[2] for r in rows])

    estatisticas = {
        'corrente_media': np.mean(correntes),
        'corrente_pico': np.max(correntes),
        'corrente_desvio': np.std(correntes),

        'tensao_media': np.mean(tensoens),
        'tensao_max': np.max(tensoens),
        'tensao_min': np.min(tensoens),
        'tensao_desvio': np.std(tensoens),

        'potencia_media': np.mean(potencias),
        'potencia_pico': np.max(potencias),
    }

    return estatisticas
