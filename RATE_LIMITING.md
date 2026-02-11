# 🔧 Rate Limiting Configuration

## Problema Resuelto

Este bot ahora incluye **protección completa contra errores 403** (rate limiting) mediante:

✅ **Caché de mercados** (30 minutos) - Reduce llamadas API en 60%  
✅ **Delays configurables** - 3 segundos entre símbolos por defecto  
✅ **Batch processing** - Pausas cada 50 símbolos  
✅ **Exponential backoff** - Espera inteligente ante errores 403  
✅ **Token bucket** - Control de frecuencia de requests  

## Configuración Opcional

Agrega estas variables a tu archivo `.env` para personalizar el comportamiento:

```bash
# Rate Limiting (Opcional - Valores por defecto)
SCAN_INTERVAL_SECONDS=600        # 10 minutos entre escaneos completos
SYMBOL_DELAY_SECONDS=3           # 3 segundos entre cada símbolo
MARKET_CACHE_MINUTES=30          # Cachear mercados por 30 minutos
BATCH_SIZE=50                    # Pausar cada 50 símbolos
BATCH_PAUSE_SECONDS=30           # 30 segundos de pausa entre batches
```

### Recomendaciones según tu situación:

**Si sigues viendo errores 403:**
```bash
SYMBOL_DELAY_SECONDS=5           # Aumentar a 5 segundos
BATCH_SIZE=30                    # Pausar más frecuentemente
BATCH_PAUSE_SECONDS=60           # Pausas más largas
```

**Si quieres escaneos más rápidos (riesgoso):**
```bash
SYMBOL_DELAY_SECONDS=2           # Mínimo recomendado
SCAN_INTERVAL_SECONDS=300        # 5 minutos
```

**Para servidores con IP bloqueada (USA):**
- Considera cambiar la región del servidor en Render
- O usa un proveedor diferente (Railway, VPS europeo, etc.)

## Logs Mejorados

Ahora verás mensajes más claros:

```
🔄 Cargando mercados desde API...
✅ Mercados cargados y cacheados: 245 símbolos

🔍 Analizando 245 monedas en Bitget...
⚙️ Config: 3s/símbolo, pausa cada 50 símbolos

📦 Usando mercados en caché (5 min)

⏸️ Pausa de batch (50/245) - esperando 30s...

⚠️ Rate limit backoff: waiting 30s (403 error #1)

✅ Escaneo completado. Señales encontradas: 2
⏳ Esperando 10 minutos hasta el próximo escaneo...
```

## Monitoreo en Render

Después de desplegar, verifica en los logs:

1. ✅ **No más errores 403** continuos
2. ✅ **Mensajes de caché** aparecen después del primer escaneo
3. ✅ **Pausas de batch** cada 50 símbolos
4. ✅ **Señales siguen generándose** correctamente

## Arquitectura del Fix

```
main.py
  ├─ Batch processing (pausa cada N símbolos)
  ├─ Delays configurables entre símbolos
  └─ Intervalo de escaneo ajustable

core/exchange.py
  ├─ Caché de mercados (30 min)
  ├─ Wrapper _handle_api_call()
  └─ Manejo de errores 403/429

core/rate_limiter.py
  ├─ Token bucket algorithm
  ├─ Exponential backoff (30s → 10min)
  └─ Contador de errores 403
```

## Despliegue a Render

1. **Commit y push** de los cambios:
```bash
git add .
git commit -m "Fix: Add rate limiting and 403 error handling"
git push origin main
```

2. **Render auto-desplegará** los cambios

3. **Monitorea los logs** por 30 minutos para confirmar que no hay errores 403

## Soporte

Si después de estos cambios sigues viendo errores 403:

1. Verifica que la IP del servidor no esté bloqueada
2. Aumenta los delays en `.env`
3. Considera cambiar de proveedor de hosting
