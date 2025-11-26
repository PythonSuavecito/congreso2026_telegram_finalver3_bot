import os
import csv
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler, 
    ContextTypes, CallbackQueryHandler, filters
)
from flask import Flask

from config import *
from database import Database

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Inicializar base de datos
db = Database(DB_NAME)

# Servidor web simple para mantener el bot activo
app = Flask(__name__)

@app.route('/')
def home():
    stats = db.obtener_estadisticas()
    return f"""
    <html>
        <head><title>🤖 Bot Congreso 2026</title></head>
        <body>
            <h1>🤖 Bot del Congreso 2026</h1>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 10px;">
                <p style="color: green; font-weight: bold;">✅ Sistema con Eliminación de Bonos</p>
                <p><strong>Total registros:</strong> {stats['total_registros']}</p>
                <p><strong>Total asistentes:</strong> {stats['total_asistentes']}</p>
            </div>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return 'OK'

# ================= FUNCIONES PRINCIPALES =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mensaje de bienvenida"""
    await update.message.reply_text(
        '🤖 **Bienvenido al Sistema del Congreso 2026**\n\n'
        '📋 **Comandos disponibles:**\n'
        '• /nuevo - Agregar nuevo registro\n'
        '• /reporte - Descargar reporte CSV\n'
        '• /estadisticas - Ver estadísticas\n'
        '• /corregir - Corregir tipos de bono\n'
        '• /eliminar - Eliminar registros\n'
        '• /buscar - Buscar por grupo\n'
        '• /ayuda - Mostrar ayuda completa'
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra ayuda completa"""
    await update.message.reply_text(
        "🤖 **SISTEMA DE GESTIÓN - CONGRESO 2026**\n\n"
        "🚀 **COMANDOS PRINCIPALES:**\n"
        "• /start - Mensaje de bienvenida\n"
        "• /nuevo - Agregar nuevo registro\n"
        "• /reporte - Descargar reporte completo (CSV)\n"
        "• /estadisticas - Ver estadísticas generales\n\n"
        
        "🔧 **GESTIÓN DE DATOS:**\n"
        "• /corregir - Corregir nombres de bonos\n"
        "• /eliminar - Eliminar registros específicos\n"
        "• /buscar - Buscar registros por grupo\n"
        "• /limpiar - Limpiar toda la base de datos\n\n"
        
        "💡 **Características:**\n"
        "✅ Captura de datos completa\n"
        "✅ Base de datos SQLite\n"
        "✅ Sistema de corrección de bonos\n"
        "✅ Eliminación de registros\n"
        "✅ Reportes en CSV\n"
        "✅ Estadísticas en tiempo real\n\n"
        
        "📝 **Para comenzar usa:** /nuevo"
    )

# ================= CAPTURA DE DATOS =================
async def iniciar_captura(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia el proceso de captura de datos"""
    await update.message.reply_text(
        '📝 **NUEVO REGISTRO**\n\n'
        'Por favor, ingresa el **NOMBRE DEL GRUPO**:'
    )
    return GRUPO

async def capturar_grupo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captura el nombre del grupo"""
    context.user_data['grupo'] = update.message.text
    await update.message.reply_text('✅ **GRUPO** guardado. Ahora ingresa el **GUÍA**:')
    return GUIA

async def capturar_guia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captura el nombre del guía"""
    context.user_data['guia'] = update.message.text
    await update.message.reply_text('✅ **GUÍA** guardado. Ahora ingresa el **BONO**:')
    return BONO

async def capturar_bono(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captura el tipo de bono"""
    context.user_data['bono'] = update.message.text
    await update.message.reply_text('✅ **BONO** guardado. Ahora ingresa el **MONTO**:')
    return MONTO

async def capturar_monto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captura el monto"""
    context.user_data['monto'] = update.message.text
    await update.message.reply_text('✅ **MONTO** guardado. Ingresa los **ASISTENTES**:')
    return ASISTENTES

async def capturar_asistentes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captura los asistentes y guarda el registro"""
    try:
        grupo = context.user_data['grupo']
        guia = context.user_data['guia']
        bono = context.user_data['bono']
        monto = context.user_data['monto']
        asistentes = update.message.text
        
        # Validar que el monto sea numérico
        try:
            monto_float = float(monto)
        except ValueError:
            await update.message.reply_text('❌ Error: El monto debe ser un número. Usa /nuevo para empezar de nuevo.')
            return ConversationHandler.END
        
        # Validar que los asistentes sean numéricos
        try:
            asistentes_int = int(asistentes)
        except ValueError:
            await update.message.reply_text('❌ Error: Los asistentes deben ser un número. Usa /nuevo para empezar de nuevo.')
            return ConversationHandler.END
        
        # Guardar en base de datos
        registro_id = db.agregar_registro(grupo, guia, bono, monto, asistentes)
        
        await update.message.reply_text(
            f'🎉 **REGISTRO #{registro_id} COMPLETADO!**\n\n'
            f'📋 **Resumen:**\n'
            f'• 🏷️ **Grupo:** {grupo}\n'
            f'• 👤 **Guía:** {guia}\n'
            f'• 🎫 **Bono:** {bono}\n'
            f'• 💰 **Monto:** ${monto_float:,.2f}\n'
            f'• 👥 **Asistentes:** {asistentes_int}\n\n'
            '💾 **Guardado en base de datos**\n\n'
            'Usa /nuevo para otro registro o /reporte para descargar datos.'
        )
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error guardando registro: {e}")
        await update.message.reply_text('❌ Error al guardar el registro. Usa /nuevo para intentar de nuevo.')
        return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela la conversación actual"""
    await update.message.reply_text('❌ Operación cancelada.')
    return ConversationHandler.END

# ================= ELIMINACIÓN DE REGISTROS =================
async def eliminar_registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra opciones para eliminar registros"""
    bonos = db.obtener_tipos_bono()
    
    if not bonos:
        await update.message.reply_text('📭 No hay registros en la base de datos.')
        return
    
    # Crear teclado con opciones de eliminación
    keyboard = [
        [InlineKeyboardButton("🗑️ Eliminar por Tipo de Bono", callback_data="eliminar_bono")],
        [InlineKeyboardButton("🔍 Eliminar por ID Específico", callback_data="eliminar_id")],
        [InlineKeyboardButton("📊 Ver Todos los Registros", callback_data="ver_registros")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_eliminacion")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        '🗑️ **SISTEMA DE ELIMINACIÓN**\n\n'
        'Selecciona el método de eliminación:',
        reply_markup=reply_markup
    )

async def handle_eliminar_opcion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la selección de opción de eliminación"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancelar_eliminacion":
        await query.edit_message_text('❌ Eliminación cancelada.')
        return
    
    elif query.data == "eliminar_bono":
        bonos = db.obtener_tipos_bono()
        
        keyboard = []
        for bono in bonos:
            keyboard.append([InlineKeyboardButton(f"🎫 {bono}", callback_data=f"eliminar_bono_{bono}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="volver_eliminar")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            '🗑️ **ELIMINAR POR TIPO DE BONO**\n\n'
            'Selecciona el tipo de bono a eliminar:\n\n'
            '⚠️ **ADVERTENCIA:** Esto eliminará TODOS los registros del bono seleccionado.',
            reply_markup=reply_markup
        )
    
    elif query.data == "eliminar_id":
        await query.edit_message_text(
            '🔍 **ELIMINAR POR ID**\n\n'
            'Por favor, ingresa el **ID del registro** que quieres eliminar:\n\n'
            '💡 **Consejo:** Usa /reporte para ver todos los IDs disponibles.'
        )
        return ELIMINAR_BONO
    
    elif query.data == "ver_registros":
        registros = db.obtener_todos_registros()
        
        if not registros:
            await query.edit_message_text('📭 No hay registros en la base de datos.')
            return
        
        mensaje = '📋 **ÚLTIMOS 10 REGISTROS**\n\n'
        for registro in registros[:10]:
            id_reg, grupo, guia, bono, monto, asistentes, fecha = registro
            fecha_simple = fecha.split()[0] if isinstance(fecha, str) else str(fecha)[:10]
            mensaje += f"🆔 **#{id_reg}** - {grupo}\n"
            mensaje += f"   👤 {guia} | 🎫 {bono}\n"
            mensaje += f"   👥 {asistentes} | 💰 ${float(monto):,.2f}\n"
            mensaje += f"   📅 {fecha_simple}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="volver_eliminar")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(mensaje, reply_markup=reply_markup)
    
    elif query.data == "volver_eliminar":
        keyboard = [
            [InlineKeyboardButton("🗑️ Eliminar por Tipo de Bono", callback_data="eliminar_bono")],
            [InlineKeyboardButton("🔍 Eliminar por ID Específico", callback_data="eliminar_id")],
            [InlineKeyboardButton("📊 Ver Todos los Registros", callback_data="ver_registros")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_eliminacion")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            '🗑️ **SISTEMA DE ELIMINACIÓN**\n\n'
            'Selecciona el método de eliminación:',
            reply_markup=reply_markup
        )

async def handle_eliminar_bono_especifico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la eliminación de un tipo de bono específico"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("eliminar_bono_"):
        bono_a_eliminar = query.data.replace("eliminar_bono_", "")
        
        # Obtener registros con este bono
        registros = db.obtener_registros_por_bono(bono_a_eliminar)
        
        if not registros:
            await query.edit_message_text(f'❌ No hay registros con bono: {bono_a_eliminar}')
            return
        
        total_asistentes = sum(registro[5] for registro in registros)
        total_monto = sum(float(registro[4]) for registro in registros)
        
        mensaje = f'⚠️ **CONFIRMAR ELIMINACIÓN**\n\n'
        mensaje += f'🎫 **Bono a eliminar:** {bono_a_eliminar}\n'
        mensaje += f'📊 **Registros afectados:** {len(registros)}\n'
        mensaje += f'👥 **Total asistentes:** {total_asistentes}\n'
        mensaje += f'💰 **Total monto:** ${total_monto:,.2f}\n\n'
        mensaje += '¿Estás seguro de que quieres eliminar TODOS estos registros?\n\n'
        mensaje += '🚨 **Esta acción no se puede deshacer.**'
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Sí, eliminar TODO", callback_data=f"confirmar_eliminar_bono_{bono_a_eliminar}"),
                InlineKeyboardButton("❌ No, cancelar", callback_data="eliminar_bono")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(mensaje, reply_markup=reply_markup)

async def handle_confirmar_eliminar_bono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma y ejecuta la eliminación de un tipo de bono"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("confirmar_eliminar_bono_"):
        bono_a_eliminar = query.data.replace("confirmar_eliminar_bono_", "")
        
        # Ejecutar eliminación
        registros_eliminados = db.eliminar_registros_por_bono(bono_a_eliminar)
        
        await query.edit_message_text(
            f'✅ **ELIMINACIÓN COMPLETADA**\n\n'
            f'• 🎫 **Bono eliminado:** {bono_a_eliminar}\n'
            f'• 📊 **Registros eliminados:** {registros_eliminados}\n\n'
            '🗑️ Todos los registros han sido eliminados permanentemente.'
        )

async def eliminar_por_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Elimina un registro por ID específico"""
    try:
        registro_id_text = update.message.text.strip()
        
        if not registro_id_text.isdigit():
            await update.message.reply_text('❌ Error: El ID debe ser un número. Intenta nuevamente:')
            return ELIMINAR_BONO
        
        registro_id = int(registro_id_text)
        registro = db.obtener_registro_por_id(registro_id)
        
        if not registro:
            await update.message.reply_text(
                f'❌ No se encontró ningún registro con ID: {registro_id}\n\n'
                'Por favor, ingresa un ID válido o usa /cancel para cancelar:'
            )
            return ELIMINAR_BONO
        
        # Mostrar información del registro
        id_reg, grupo, guia, bono, monto, asistentes, fecha = registro
        fecha_simple = fecha.split()[0] if isinstance(fecha, str) else str(fecha)[:10]
        
        mensaje = f'🔍 **REGISTRO ENCONTRADO**\n\n'
        mensaje += f'• 🆔 **ID:** {id_reg}\n'
        mensaje += f'• 🏷️ **Grupo:** {grupo}\n'
        mensaje += f'• 👤 **Guía:** {guia}\n'
        mensaje += f'• 🎫 **Bono:** {bono}\n'
        mensaje += f'• 💰 **Monto:** ${float(monto):,.2f}\n'
        mensaje += f'• 👥 **Asistentes:** {asistentes}\n'
        mensaje += f'• 📅 **Fecha:** {fecha_simple}\n\n'
        mensaje += '¿Estás seguro de que quieres eliminar este registro?\n\n'
        mensaje += '🚨 **Esta acción no se puede deshacer.**'
        
        # Guardar ID en contexto para confirmación
        context.user_data['registro_a_eliminar'] = registro_id
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Sí, eliminar", callback_data="confirmar_eliminar_id"),
                InlineKeyboardButton("❌ No, cancelar", callback_data="cancelar_eliminacion")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(mensaje, reply_markup=reply_markup)
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error en eliminación por ID: {e}")
        await update.message.reply_text('❌ Error al buscar el registro. Intenta nuevamente:')
        return ELIMINAR_BONO

async def handle_confirmar_eliminar_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma y ejecuta la eliminación por ID"""
    query = update.callback_query
    await query.answer()
    
    registro_id = context.user_data.get('registro_a_eliminar')
    
    if not registro_id:
        await query.edit_message_text('❌ Error: No se encontró el registro a eliminar')
        return
    
    # Obtener información del registro antes de eliminar
    registro = db.obtener_registro_por_id(registro_id)
    
    if not registro:
        await query.edit_message_text('❌ Error: El registro ya no existe')
        return
    
    # Ejecutar eliminación
    eliminado = db.eliminar_registro(registro_id)
    
    if eliminado:
        id_reg, grupo, guia, bono, monto, asistentes, fecha = registro
        await query.edit_message_text(
            f'✅ **REGISTRO ELIMINADO**\n\n'
            f'• 🆔 **ID:** {id_reg}\n'
            f'• 🏷️ **Grupo:** {grupo}\n'
            f'• 🎫 **Bono:** {bono}\n'
            f'• 💰 **Monto:** ${float(monto):,.2f}\n\n'
            '🗑️ El registro ha sido eliminado permanentemente.'
        )
    else:
        await query.edit_message_text('❌ Error: No se pudo eliminar el registro')

# ================= FUNCIONES ADICIONALES =================
async def generar_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera y envía un reporte CSV"""
    try:
        registros = db.obtener_todos_registros()
        
        if not registros:
            await update.message.reply_text('📭 No hay datos en la base de datos.')
            return
        
        filename = 'reporte_congreso_2026.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'GRUPO', 'GUIA', 'BONO', 'MONTO', 'ASISTENTES', 'FECHA'])
            
            for registro in registros:
                writer.writerow(registro)
        
        with open(filename, 'rb') as f:
            await update.message.reply_document(
                f, 
                filename=filename,
                caption='📊 **Reporte completo del Congreso 2026**\n\n'
                       f'Total de registros: {len(registros)}'
            )
        
        # Limpiar archivo temporal
        os.remove(filename)
            
    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        await update.message.reply_text('❌ Error al generar el reporte.')

async def ver_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra estadísticas generales"""
    try:
        stats = db.obtener_estadisticas()
        
        mensaje = "📊 **ESTADÍSTICAS DEL CONGRESO**\n\n"
        mensaje += f"📈 **Total registros:** {stats['total_registros']}\n"
        mensaje += f"👥 **Total asistentes:** {stats['total_asistentes']}\n\n"
        
        if stats['por_bono']:
            mensaje += "🎫 **Por tipo de bono:**\n"
            for bono, cantidad, asistentes, monto in stats['por_bono']:
                mensaje += f"• **{bono}:** {cantidad} reg, {asistentes} asis, ${float(monto):,.2f}\n"
        
        await update.message.reply_text(mensaje)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        await update.message.reply_text('❌ Error al obtener estadísticas.')

async def buscar_grupo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Busca registros por nombre de grupo"""
    try:
        if not context.args:
            await update.message.reply_text(
                '🔍 **BUSCAR GRUPO**\n\n'
                'Uso: /buscar <nombre_del_grupo>\n\n'
                'Ejemplo: /buscar juvenil'
            )
            return
        
        termino_busqueda = ' '.join(context.args)
        registros = db.buscar_registros_por_grupo(termino_busqueda)
        
        if not registros:
            await update.message.reply_text(f'🔍 No se encontraron registros para: "{termino_busqueda}"')
            return
        
        mensaje = f'🔍 **RESULTADOS PARA: "{termino_busqueda}"**\n\n'
        for registro in registros[:15]:  # Limitar a 15 resultados
            id_reg, grupo, guia, bono, monto, asistentes, fecha = registro
            fecha_simple = fecha.split()[0] if isinstance(fecha, str) else str(fecha)[:10]
            mensaje += f"🆔 **#{id_reg}** - {grupo}\n"
            mensaje += f"   👤 {guia} | 🎫 {bono}\n"
            mensaje += f"   👥 {asistentes} | 💰 ${float(monto):,.2f}\n"
            mensaje += f"   📅 {fecha_simple}\n\n"
        
        if len(registros) > 15:
            mensaje += f"📝 ... y {len(registros) - 15} registros más.\n"
            mensaje += "💡 Usa /reporte para ver todos los registros."
        
        await update.message.reply_text(mensaje)
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        await update.message.reply_text('❌ Error en la búsqueda.')

async def limpiar_base_datos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Limpia toda la base de datos (solo para administradores)"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Sí, limpiar TODO", callback_data="confirmar_limpiar"),
            InlineKeyboardButton("❌ No, cancelar", callback_data="cancelar_limpiar")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    stats = db.obtener_estadisticas()
    
    await update.message.reply_text(
        f'🚨 **LIMPIAR BASE DE DATOS**\n\n'
        f'📊 **Estadísticas actuales:**\n'
        f'• Registros: {stats["total_registros"]}\n'
        f'• Asistentes: {stats["total_asistentes"]}\n\n'
        '⚠️ **¿Estás seguro de que quieres eliminar TODOS los registros?**\n\n'
        '🚫 **Esta acción es IRREVERSIBLE y eliminará toda la información.**',
        reply_markup=reply_markup
    )

async def handle_limpiar_base_datos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la confirmación de limpieza de base de datos"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirmar_limpiar":
        registros_eliminados = db.limpiar_registros()
        
        await query.edit_message_text(
            f'🗑️ **BASE DE DATOS LIMPIADA**\n\n'
            f'• 📊 **Registros eliminados:** {registros_eliminados}\n\n'
            '✅ La base de datos ha sido reiniciada completamente.'
        )
    
    elif query.data == "cancelar_limpiar":
        await query.edit_message_text('❌ Limpieza cancelada. La base de datos permanece intacta.')

# ================= CONVERSATION HANDLERS =================
def setup_handlers(application):
    """Configura todos los handlers de la aplicación"""
    
    # Handler para captura de datos
    conv_captura = ConversationHandler(
        entry_points=[CommandHandler('nuevo', iniciar_captura)],
        states={
            GRUPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_grupo)],
            GUIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_guia)],
            BONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_bono)],
            MONTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_monto)],
            ASISTENTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_asistentes)],
        },
        fallbacks=[CommandHandler('cancel', cancelar)],
    )
    
    # Handler para eliminación por ID
    conv_eliminacion = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_eliminar_opcion, pattern='^eliminar_id$')],
        states={
            ELIMINAR_BONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, eliminar_por_id)],
        },
        fallbacks=[CommandHandler('cancel', cancelar)],
    )
    
    # Handlers principales
    application.add_handler(conv_captura)
    application.add_handler(conv_eliminacion)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CommandHandler("reporte", generar_reporte))
    application.add_handler(CommandHandler("estadisticas", ver_estadisticas))
    application.add_handler(CommandHandler("buscar", buscar_grupo))
    application.add_handler(CommandHandler("limpiar", limpiar_base_datos))
    application.add_handler(CommandHandler("eliminar", eliminar_registro))
    
    # Handlers para callbacks
    application.add_handler(CallbackQueryHandler(handle_eliminar_opcion, pattern='^(eliminar_bono|eliminar_id|ver_registros|volver_eliminar)$'))
    application.add_handler(CallbackQueryHandler(handle_eliminar_bono_especifico, pattern='^eliminar_bono_'))
    application.add_handler(CallbackQueryHandler(handle_confirmar_eliminar_bono, pattern='^confirmar_eliminar_bono_'))
    application.add_handler(CallbackQueryHandler(handle_confirmar_eliminar_id, pattern='^confirmar_eliminar_id$'))
    application.add_handler(CallbackQueryHandler(handle_limpiar_base_datos, pattern='^(confirmar_limpiar|cancelar_limpiar)$'))
    application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.edit_message_text('❌ Operación cancelada.'), pattern='^cancelar_eliminacion$'))

# ================= INICIALIZACIÓN =================
def run_bot():
    """Función principal para ejecutar el bot"""
    if BOT_TOKEN == 'TU_TOKEN_AQUI':
        print("❌ ERROR: Configura tu BOT_TOKEN en config.py")
        print("💡 Obtén tu token de @BotFather en Telegram")
        return
    
    try:
        # Crear aplicación de Telegram
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Configurar handlers
        setup_handlers(application)
        
        print("🤖 Bot del Congreso 2026 iniciado correctamente!")
        print("✅ Sistema con eliminación de registros")
        print("📊 Base de datos SQLite integrada")
        print("🌐 Servidor web activo en puerto 8080")
        print("💬 Envía /start a tu bot en Telegram")
        
        # Iniciar el bot
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Error al iniciar el bot: {e}")

def run_web_server():
    """Ejecuta el servidor web en un hilo separado"""
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

if __name__ == '__main__':
    import threading
    
    print("🚀 Iniciando Sistema del Congreso 2026...")
    print("📁 Ruta:", os.getcwd())
    print("🗄️ Base de datos: congreso_2026.db")
    
    # Iniciar servidor web en hilo separado
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Iniciar bot (bloqueante)
    run_bot()
