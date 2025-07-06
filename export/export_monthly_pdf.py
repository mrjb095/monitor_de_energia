import sqlite3
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
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

def exportar_pdf():
    inicio, fim = get_month_range()
    inicio_str = inicio.strftime('%Y-%m-%d 00:00:00')
    fim_str = fim.strftime('%Y-%m-%d 23:59:59')

    conn = sqlite3.connect(DADOS_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, corrente, tensao, potencia FROM historico WHERE timestamp BETWEEN ? AND ?', (inicio_str, fim_str))
    rows = cursor.fetchall()
    conn.close()

    filename = f"export_{inicio.strftime('%Y%m%d')}_to_{fim.strftime('%Y%m%d')}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, f"Exportação de Dados: {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}")

    y = height - 80
    c.setFont("Helvetica", 10)

    c.drawString(50, y, "Timestamp        Corrente (A)    Tensão (V)    Potência (W)")
    y -= 15

    for row in rows:
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)

        linha = f"{row[0]}    {row[1]:.2f}A    {row[2]:.2f}V    {row[3]:.2f}W"
        c.drawString(50, y, linha)
        y -= 12

    c.save()
    print(f'✅ PDF exportado: {filename}')

if __name__ == '__main__':
    exportar_pdf()
