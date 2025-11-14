# 🤖 Bot de Telegram - Congreso 2026

Bot para capturar datos del Congreso 2026 con base de datos SQLite y sistema de corrección de bonos.

## 🚀 Características

- Captura de datos: GRUPO, GUIA, BONO, MONTO, ASISTENTES
- Base de datos SQLite integrada
- Sistema de corrección masiva de bonos
- Generación de reportes CSV
- Interfaz web de monitoreo

## 📋 Comandos

- `/start` - Iniciar captura
- `/corregir` - Corregir tipos de bono
- `/reporte` - Generar CSV
- `/estadisticas` - Ver estadísticas
- `/ayuda` - Mostrar ayuda

## 🛠️ Despliegue

1. Configurar variable de entorno `BOT_TOKEN`
2. Instalar dependencias: `pip install -r requirements.txt`
3. Ejecutar: `python main.py`