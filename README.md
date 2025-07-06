
# Monitor de Energia - ESP32 + Flask + WebSocket + SQLite

Este é um sistema de monitoramento de energia residencial/industrial que recebe dados de um ESP32, armazena em banco de dados e exibe tudo em um dashboard web em tempo real.

## 📂 Estrutura de Pastas

```
monitor_energia/
├── app.py                      # Arquivo principal do Flask
├── config.py                   # Configurações globais (banco, alarmes)
├── requirements.txt            # Dependências Python
│
├── database/
│   ├── init_db.py              # Criação de tabelas SQLite
│   ├── utils.py                # Funções de histórico e eventos
│   └── users.py                # Funções de autenticação e cadastro
│
├── utils/
│   ├── timezone_utils.py       # Conversões UTC ↔ Local
│   ├── alarms.py               # Lógica de alarmes
│   └── energy_calc.py          # Cálculo de energia acumulada
│
├── export/
│   ├── export_monthly_csv.py   # Exportação de CSV mensal
│   └── export_monthly_pdf.py   # Exportação de PDF mensal
│
├── static/
│   └── js/
│       └── dashboard.js        # JavaScript do Dashboard
│
├── templates/
│   ├── dashboard.html
│   ├── historico.html
│   ├── eventos.html
│   ├── login.html
│   └── cadastro.html
│
├── dados.db                    # Banco de medições
└── users.db                    # Banco de usuários
```

## ✅ Principais Recursos

- ✅ Dashboard em tempo real com WebSocket  
- ✅ Gráficos de Corrente, Tensão, Potência  
- ✅ Alarmes com notificação visual + histórico de eventos  
- ✅ Exportação mensal em CSV e PDF  
- ✅ Filtros de período e dados históricos  
- ✅ Autenticação com login e senha criptografada  
- ✅ Status online/offline do ESP32  
- ✅ Animações suaves nos gráficos e valores  

## ✅ Instalação

1. Crie um ambiente virtual (opcional, mas recomendado):

```bash
python -m venv venv
```

2. Ative o ambiente:

- No Windows:
```bash
venv\Scripts\activate
```
- No Linux/macOS:
```bash
source venv/bin/activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Execute o servidor:

```bash
python app.py
```

## ✅ Como acessar:

Abra o navegador e acesse:

```
http://localhost:5000
```

## ✅ Funções adicionais:

- ✅ Para exportar CSV/PDF manualmente:  
```
http://localhost:5000/exportar_dados
```

- ✅ Página de Eventos/Alarmes:  
```
http://localhost:5000/eventos
```

- ✅ Histórico de medições:  
```
http://localhost:5000/historico
```

## ✅ To Do / Melhorias futuras:

- ✅ Envio de e-mail ou Telegram em caso de alarmes críticos  
- ✅ Integração com armazenamento em nuvem (ex.: Google Sheets, Firebase)  
- ✅ Implementação de autenticação por nível de acesso (Admin / Usuário)  
- ✅ Dashboard Mobile First com melhorias de layout  

Projeto desenvolvido para aprendizado em **programação embarcada**, **sistemas web**, **controle de energia** e **bancos de dados**.
