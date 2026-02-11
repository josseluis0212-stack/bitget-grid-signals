// Dashboard App - Real-time updates
class Dashboard {
    constructor() {
        this.updateInterval = 2000; // 2 segundos
        this.init();
    }

    init() {
        this.fetchState();
        setInterval(() => this.fetchState(), this.updateInterval);
    }

    async fetchState() {
        try {
            const response = await fetch('/api/state');
            const data = await response.json();
            this.updateUI(data);
        } catch (error) {
            console.error('Error fetching state:', error);
            document.getElementById('bot-status').textContent = 'Error de conexión';
        }
    }

    updateUI(data) {
        // Status
        document.getElementById('bot-status').textContent = 'Online';

        // BTC
        this.updateBTC(data.btc);

        // Scanning
        this.updateScanning(data.scanning);

        // Stats
        this.updateStats(data.signals, data.stats);

        // Signals
        this.updateSignals(data.signals.recent);

        // Last update
        const now = new Date();
        const timeStr = now.toLocaleTimeString('es-ES');
        document.getElementById('last-update').textContent = timeStr;
        document.getElementById('footer-update').textContent = timeStr;
    }

    updateBTC(btc) {
        const priceEl = document.getElementById('btc-price');
        const changeEl = document.getElementById('btc-change');
        const trendEl = document.getElementById('btc-trend');

        priceEl.textContent = `$${btc.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;

        const change = btc.change_24h;
        changeEl.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
        changeEl.className = `btc-change ${change >= 0 ? 'positive' : 'negative'}`;

        trendEl.className = `btc-trend-badge ${btc.trend}`;
        trendEl.querySelector('.trend-text').textContent = btc.trend;

        // Cambiar color del icono según tendencia
        const icon = trendEl.querySelector('.trend-icon');
        if (btc.trend === 'ALCISTA') {
            icon.style.color = '#10b981';
        } else if (btc.trend === 'BAJISTA') {
            icon.style.color = '#ef4444';
        } else {
            icon.style.color = '#9ca3af';
        }
    }

    updateScanning(scanning) {
        const coinEl = document.getElementById('current-coin');
        const progressFillEl = document.getElementById('progress-fill');
        const progressTextEl = document.getElementById('progress-text');
        const pulseEl = document.getElementById('scan-pulse');

        if (scanning.is_active && scanning.current_symbol) {
            coinEl.querySelector('.coin-name').textContent = scanning.current_symbol;
            const progress = (scanning.progress.current / scanning.progress.total) * 100;
            progressFillEl.style.width = `${progress}%`;
            progressTextEl.textContent = `${scanning.progress.current} / ${scanning.progress.total} monedas`;
            pulseEl.style.display = 'block';
        } else {
            coinEl.querySelector('.coin-name').textContent = 'Esperando próximo ciclo...';
            progressFillEl.style.width = '0%';
            progressTextEl.textContent = 'Escaneo completado';
            pulseEl.style.display = 'none';
        }
    }

    updateStats(signals, stats) {
        document.getElementById('total-signals').textContent = signals.total_today;
        document.getElementById('long-signals').textContent = signals.long_count;
        document.getElementById('short-signals').textContent = signals.short_count;
        document.getElementById('uptime').textContent = `${stats.uptime_hours}h`;
    }

    updateSignals(signals) {
        const listEl = document.getElementById('signals-list');

        if (!signals || signals.length === 0) {
            listEl.innerHTML = `
                <div class="no-signals">
                    <span class="no-signals-icon">🔍</span>
                    <p>No se han encontrado señales aún</p>
                    <small>El bot está escaneando el mercado...</small>
                </div>
            `;
            return;
        }

        // Invertir para mostrar las más recientes primero
        const reversedSignals = [...signals].reverse();

        listEl.innerHTML = reversedSignals.map(signal => {
            const time = new Date(signal.timestamp).toLocaleTimeString('es-ES');
            const params = signal.params;

            return `
                <div class="signal-item">
                    <div class="signal-direction ${signal.direction}">${signal.direction}</div>
                    <div class="signal-info">
                        <div class="signal-symbol">${signal.symbol}</div>
                        <div class="signal-time">${time}</div>
                    </div>
                    <div class="signal-params">
                        <span>Rango: ${params.min} - ${params.max}</span>
                        <span>Grids: ${params.grids}</span>
                    </div>
                    <div class="signal-price">$${params.last_price.toFixed(2)}</div>
                </div>
            `;
        }).join('');
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});
