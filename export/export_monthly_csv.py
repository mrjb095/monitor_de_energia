import sqlite3
import csv
from datetime import datetime, timedelta
from config import DADOS_DB

def get_month_range():
    hoje = datetime.now()
    if hoje.day >= 13:
        inicio = hoje.replace(day=13)
        fim = (inicio + timedelta(days=31)).replace(day=12)
    else:
        fim = hoje.replace(day=12)
        inicio = (fim - timedelta(days=31)).replace(day=13)
    return inicio, fim

def exportar_csv():
    inicio, fim = get_month_range()
    inicio_str = inicio.strftime('%Y-%m-%d 00:00:00')
    fim_str = fim.strftime('%Y-%m-%d 23:59:59')

    conn = sqlite3.connect(DADOS_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM historico WHERE timestamp BETWEEN ? AND ?', (inicio_str, fim_str))
    rows = cursor.fetchall()
    conn.close()

    filename = f"export_{inicio.strftime('%Y%m%d')}_to_{fim.strftime('%Y%m%d')}.csv"
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID', 'Timestamp', 'Corrente (A)', 'Tensão (V)', 'Potência (W)'])
        writer.writerows(rows)

    print(f'✅ CSV exportado: {filename}')

if __name__ == '__main__':
    exportar_csv()
