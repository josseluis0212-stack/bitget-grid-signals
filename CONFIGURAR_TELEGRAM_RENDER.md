# 🚀 Configuración de Telegram en Render (PASO FINAL)

Para que el bot envíe señales a tu Telegram desde la nube:

## Paso 1: Ir a Render Dashboard
1. Abre **Render.com** y ve a tu servicio "bitget-grid-signals"
2. Haz clic en **"Environment"** (en el menú lateral izquierdo)

## Paso 2: Agregar Variables de Entorno
Haz clic en **"Add Environment Variable"** y agrega estas 2:

### Variable 1:
- **Key:** `TELEGRAM_BOT_TOKEN`
- **Value:** `8366697616:AAEnKLwY-s8lsjSuiI342KR86PCW5he4Pj8`

### Variable 2:
- **Key:** `TELEGRAM_CHAT_ID`  
- **Value:** `7840645929`

## Paso 3: Guardar y Reiniciar
1. Haz clic en **"Save Changes"**
2. Render reiniciará automáticamente el servicio
3. En 1-2 minutos recibirás el mensaje de prueba en Telegram

---

## ✅ Resultado Esperado
Verás en tu bot de Telegram:
```
🚀 SISTEMA IA INICIADO 🚀

✅ BOT IA: Triple Pantalla (1D/1H/5m)
📡 Conexión Telegram: ESTABLE
🐺 El lobo está cazando...

🔔 PRUEBA DE ALERTA: Si lees esto, el sistema funciona.
```

**Y luego empezará a enviarte señales reales cuando detecte oportunidades.**

---

## 📊 Dashboard
El bot ahora guarda todas las señales en `data/signal_history.json` para que puedas verlas en el dashboard (si lo abres en el navegador).
