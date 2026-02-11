#!/bin/bash
# Script de inicio para Render que ejecuta el scanner en background y el dashboard con Gunicorn

# Iniciar el scanner en background
python scanner.py &

# Iniciar el dashboard con Gunicorn
gunicorn -w 1 -b 0.0.0.0:$PORT dashboard.app:app --timeout 120
