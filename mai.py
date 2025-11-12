import os
import csv
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, ContextTypes
from telegram.ext import filters

# Configuración de estados para la conversación
GRUPO, GUIA, BONO, MONTO, ASISTENTES = range(5)

# Estructura para almacenar los datos (en memoria)
datos = []

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Comando de inicio
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    await update.message.reply_text(
        f'¡Hola {user.first_name}! 🤖\n'
        'Vamos a capturar datos para el Congreso 2026.\n\n'
        'Por favor, ingresa el **NOMBRE DEL GRUPO**:\n'
        '_(Envía /cancel en cualquier momento para cancelar)_'
    )
    return GRUPO

# Captura del GRUPO
async def capturar_grupo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['grupo'] = update.message.text
    await update.message.reply_text(
        '✅ **GRUPO** guardado.\n\n'
        'Ahora ingresa el **NOMBRE DEL GUÍA**:'
    )
    return GUIA

# Captura del GUÍA
async def capturar_guia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['guia'] = update.message.text
    await update.message.reply_text(
        '✅ **GUÍA** guardado.\n\n'
        'Ahora ingresa el **TIPO DE BONO**:'
    )
    return BONO

# Captura del BONO
async def capturar_bono(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['bono'] = update.message.text
    await update.message.reply_text(
        '✅ **BONO** guardado.\n\n'
        'Ahora ingresa el **MONTO**:'
    )
    return MONTO

# Captura del MONTO
async def capturar_monto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['monto'] = update.message.text
    await update.message.reply_text(
        '✅ **MONTO** guardado.\n\n'
        'Último paso! Ingresa el **NÚMERO DE ASISTENTES**:'
    )
    return ASISTENTES

# Captura de ASISTENTES y almacenamiento
async def capturar_asistentes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['asistentes'] = update.message.text
    
    # Guardar en la estructura de datos
    datos.append({
        'GRUPO': context.user_data['grupo'],
        'GUIA': context.user_data['guia'],
        'BONO': context.user_data['bono'],
        'MONTO': context.user_data['monto'],
        'ASISTENTES': context.user_data['asistentes']
    })
    
    await update.message.reply_text(
        '🎉 **REGISTRO COMPLETADO!** ✅\n\n'
        '¿Qué deseas hacer ahora?\n\n'
        '📝 /nuevo - Agregar otro registro\n'
        '📊 /reporte - Generar reporte CSV\n'
        '👀 /ver - Ver datos capturados\n'
        '📈 /estadisticas - Ver estadísticas\n'
        '🗑️ /limpiar - Limpiar todos los datos\n'
        '❌ /cancel - Salir'
    )
    return ConversationHandler.END

# Generar reporte CSV
async def generar_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not datos:
        await update.message.reply_text('📭 No hay datos registrados aún.')
        return
    
    filename = 'reporte_congreso_2026.csv'
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['GRUPO', 'GUIA', 'BONO', 'MONTO', 'ASISTENTES']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for registro in datos:
                writer.writerow(registro)
        
        with open(filename, 'rb') as csvfile:
            await update.message.reply_document(
                document=csvfile,
                filename=filename,
                caption='📊 **Reporte del Congreso 2026**\n'
                       'Formato CSV listo para descargar'
            )
    except Exception as e:
        await update.message.reply_text(f'❌ Error al generar el reporte: {str(e)}')

# Ver datos actuales
async def ver_datos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not datos:
        await update.message.reply_text('📭 No hay datos registrados aún.')
        return
    
    mensaje = "📋 **DATOS CAPTURADOS:**\n\n"
    for i, registro in enumerate(datos, 1):
        mensaje += f"**Registro {i}:**\n"
        mensaje += f"• 🏷️ **GRUPO:** {registro['GRUPO']}\n"
        mensaje += f"• 👤 **GUÍA:** {registro['GUIA']}\n"
        mensaje += f"• 🎫 **BONO:** {registro['BONO']}\n"
        mensaje += f"• 💰 **MONTO:** {registro['MONTO']}\n"
        mensaje += f"• 👥 **ASISTENTES:** {registro['ASISTENTES']}\n\n"
    
    await update.message.reply_text(mensaje)

# Estadísticas
async def estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not datos:
        await update.message.reply_text('📭 No hay datos registrados aún.')
        return
    
    try:
        total_asistentes = sum(int(registro['ASISTENTES']) for registro in datos)
        total_registros = len(datos)
        
        mensaje = (
            "📈 **ESTADÍSTICAS**\n\n"
            f"📊 **Total de registros:** {total_registros}\n"
            f"👥 **Total de asistentes:** {total_asistentes}\n"
            f"📅 **Última actualización:** Ahora"
        )
        
        await update.message.reply_text(mensaje)
    except Exception as e:
        await update.message.reply_text(f'❌ Error al calcular estadísticas: {str(e)}')

# Limpiar datos
async def limpiar_datos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global datos
    datos_count = len(datos)
    datos = []
    await update.message.reply_text(f'🗑️ **{datos_count} registros** han sido eliminados.')

# Cancelar proceso
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('❌ Operación cancelada.')
    return ConversationHandler.END

# Comando para nuevo registro
async def nuevo_registro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await start(update, context)

# Comando de ayuda
async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mensaje = (
        "🤖 **BOT DEL CONGRESO 2026**\n\n"
        "**Comandos disponibles:**\n\n"
        "🚀 /start o /nuevo - Iniciar captura de datos\n"
        "📊 /reporte - Generar reporte CSV\n"
        "👀 /ver - Ver datos capturados\n"
        "📈 /estadisticas - Ver estadísticas\n"
        "🗑️ /limpiar - Limpiar todos los datos\n"
        "ℹ️ /ayuda - Mostrar esta ayuda\n"
        "❌ /cancel - Cancelar operación actual\n\n"
        "**Formato CSV:** GRUPO, GUIA, BONO, MONTO, ASISTENTES"
    )
    await update.message.reply_text(mensaje)

# Manejo de errores
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f'Error: {context.error}', exc_info=context.error)

def main() -> None:
    # Obtener token desde variable de entorno
    TOKEN = os.getenv('BOT_TOKEN')
    if not TOKEN:
        logger.error("❌ No se encontró BOT_TOKEN en las variables de entorno")
        print("❌ ERROR: No se configuró BOT_TOKEN")
        print("💡 Configura la variable de entorno BOT_TOKEN en Railway")
        return
    
    # Crear application
    application = Application.builder().token(TOKEN).build()

    # Configurar el manejador de conversación
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('nuevo', nuevo_registro)
        ],
        states={
            GRUPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_grupo)],
            GUIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_guia)],
            BONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_bono)],
            MONTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_monto)],
            ASISTENTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_asistentes)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Registrar handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("reporte", generar_reporte))
    application.add_handler(CommandHandler("ver", ver_datos))
    application.add_handler(CommandHandler("estadisticas", estadisticas))
    application.add_handler(CommandHandler("limpiar", limpiar_datos))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CommandHandler("nuevo", nuevo_registro))
    
    # Manejo de errores
    application.add_error_handler(error_handler)

    # Iniciar el bot
    logger.info("🤖 Bot del Congreso 2026 iniciado correctamente")
    print("🚀 Bot iniciado - Esperando mensajes...")
    application.run_polling()

if __name__ == '__main__':
    main()