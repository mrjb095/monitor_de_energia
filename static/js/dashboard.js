
const socket = io();
let correnteAcumulada = 0;
let tensaoAcumulada = 0;
let amostras = 0;
let modoHistorico = false;

const graficoCorrente = criarGrafico('graficoCorrente', 'Corrente (A)', 'cyan');
const graficoTensao = criarGrafico('graficoTensao', 'Tensão (V)', 'orange');
const graficoPotencia = criarGrafico('graficoPotencia', 'Potência (W)', 'lime');

function criarGrafico(id, label, cor) {
    return new Chart(document.getElementById(id), {
        type: 'line',
        data: { labels: [], datasets: [{ label: label, data: [], borderColor: cor, backgroundColor: cor, fill: false, tension: 0.3 }] },
        options: {
            animation: { duration: 500, easing: 'easeOutQuart' },
            scales: {
                x: { ticks: { color: 'white' }, grid: { color: '#444' } },
                y: { ticks: { color: 'white' }, grid: { color: '#444' } }
            },
            plugins: { legend: { labels: { color: 'white' } } },
            responsive: true
        }
    });
}

function atualizarGrafico(grafico, valor) {
    if (grafico.data.datasets[0].data.length >= 30) {
        grafico.data.labels.shift();
        grafico.data.datasets[0].data.shift();
    }
    grafico.data.labels.push('');
    grafico.data.datasets[0].data.push(valor);
    grafico.update();
}



function animarValor(elementId, novoValor, unidades = '', casasDecimais = 2) {
    const elemento = document.getElementById(elementId);
    const atual = parseFloat(elemento.innerText) || 0;
    const inicio = atual;
    const fim = novoValor;
    const duracao = 500;
    let inicioTempo = null;

    function step(timestamp) {
        if (!inicioTempo) inicioTempo = timestamp;
        const progresso = Math.min((timestamp - inicioTempo) / duracao, 1);
        const valorInterpolado = inicio + (fim - inicio) * progresso;
        elemento.innerText = valorInterpolado.toFixed(casasDecimais) + unidades;
        if (progresso < 1) {
            requestAnimationFrame(step);
        }
    }
    requestAnimationFrame(step);
}

async function atualizarAcumuladoMensal() {
    const r1 = await fetch('/acumulado_mensal');
    const json1 = await r1.json();
    animarValor('energia_mes', json1.energia_kwh, ' kWh', 4);
    animarValor('custo_mes', json1.custo_reais, '', 2);

    const r2 = await fetch('/previsao_consumo');
    const json2 = await r2.json();
    animarValor('previsao_mes', json2.consumo_estimado_kwh, ' kWh', 4);
    animarValor('previsao_custo', json2.custo_estimado, '', 2);

}


async function verificarUltimoAlarme() {
    const r = await fetch('/ultimo_alarme');
    const json = await r.json();

    if (json.mensagem) {
        document.getElementById('alerta_alarme').style.display = 'block';
        document.getElementById('texto_alarme').innerText = json.mensagem + " (" + json.timestamp + ")";
    } else {
        document.getElementById('alerta_alarme').style.display = 'none';
    }
}

async function verificarStatusESP() {
    const r = await fetch('/status_esp');
    const json = await r.json();
    const statusDiv = document.getElementById('status_esp');

    if (json.status === 'online') {
        statusDiv.style.backgroundColor = 'green';
        statusDiv.innerText = '🟢 ESP';
    } else  {
        statusDiv.style.backgroundColor = 'gray';
        statusDiv.innerText = '🔴 ESP';
    }
}
function carregarPeriodo() {
    modoHistorico = true;
    const periodo = document.getElementById('periodoSelect').value;
    let url = `/dados_periodo?periodo=${periodo}`;

    if (periodo === 'personalizado') {
        const inicio = document.getElementById('inicioPersonalizado').value;
        const fim = document.getElementById('fimPersonalizado').value;
        url += `&inicio=${inicio}&fim=${fim}`;
    }

    fetch(url)
        .then(response => response.json())
        .then(data => {
            atualizarGraficoCompleto(graficoCorrente, data.timestamps, data.correntes);
            atualizarGraficoCompleto(graficoTensao, data.timestamps, data.tensoens);
            atualizarGraficoCompleto(graficoPotencia, data.timestamps, data.potencias);
            modoHistorico = false;
        });
}

function atualizarGraficoCompleto(grafico, labels, dados) {
    grafico.data.labels = [...labels];
    grafico.data.datasets[0].data = [...dados];
    grafico.update();
}

socket.on('new_data', (data) => {
    console.log('Recebi novos dados');
    if (!modoHistorico) {
        atualizarGrafico(graficoCorrente, data.corrente);
        atualizarGrafico(graficoTensao, data.tensao);
        atualizarGrafico(graficoPotencia, data.potencia);
    }
    animarValor('corrente', data.corrente);
    animarValor('tensao', data.tensao);
    animarValor('potencia', data.potencia);

    correnteAcumulada += data.corrente;
    tensaoAcumulada += data.tensao;
    amostras++;

    animarValor('corrente_media', correnteAcumulada / amostras);
    animarValor('tensao_media', tensaoAcumulada / amostras);
});

socket.on('connect', () => console.log('Socket.IO conectado'));

document.getElementById('periodoSelect').addEventListener('change', function() {
    document.getElementById('personalizadoCampos').style.display = (this.value === 'personalizado') ? 'inline' : 'none';
});

setInterval(atualizarAcumuladoMensal, 10000);
setInterval(verificarUltimoAlarme, 10000);
setInterval(verificarStatusESP, 30000);

atualizarAcumuladoMensal();
verificarUltimoAlarme();
verificarStatusESP();
