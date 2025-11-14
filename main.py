import os
import csv
import logging
import threading
import sqlite3
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, CallbackQueryHandler
from telegram.ext import filters
from flask import Flask
import time

# ================= CONFIGURACIÓN =================
GRUPO, GUIA, BONO, MONTO, ASISTENTES = range(5)
CORREGIR_BONO, NUEVO_BONO = range(5, 7)

# Silenciar logs de Flask
logging.getLogger('werkzeug').setLevel(logging.ERROR)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= BASE DE DATOS =================
class Database:
    def __init__(self, db_name="congreso.db"):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        """Inicializa la base de datos y crea la tabla si no existe"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grupo TEXT NOT NULL,
                guia TEXT NOT NULL,
                bono TEXT NOT NULL,
                monto REAL NOT NULL,
                asistentes INTEGER NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Base de datos inicializada")
    
    def agregar_registro(self, grupo, guia, bono, monto, asistentes):
        """Agrega un nuevo registro a la base de datos"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO registros (grupo, guia, bono, monto, asistentes)
            VALUES (?, ?, ?, ?, ?)
        ''', (grupo, guia, bono, float(monto), int(asistentes)))
        
        conn.commit()
        registro_id = cursor.lastrowid
        conn.close()
        
        return registro_id
    
    def obtener_todos_registros(self):
        """Obtiene todos los registros de la base de datos"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, grupo, guia, bono, monto, asistentes, fecha_creacion 
            FROM registros 
            ORDER BY fecha_creacion DESC
        ''')
        
        registros = cursor.fetchall()
        conn.close()
        
        return registros
    
    def obtener_registros_por_bono(self, bono):
        """Obtiene registros por tipo de bono"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, grupo, guia, bono, monto, asistentes, fecha_creacion 
            FROM registros 
            WHERE bono = ?
            ORDER BY fecha_creacion DESC
        ''', (bono,))
        
        registros = cursor.fetchall()
        conn.close()
        
        return registros
    
    def obtener_tipos_bono(self):
        """Obtiene todos los tipos de bono únicos"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT bono FROM registros ORDER BY bono')
        bonos = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return bonos
    
    def actualizar_bono(self, registro_id, nuevo_bono):
        """Actualiza el tipo de bono de un registro"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE registros 
            SET bono = ? 
            WHERE id = ?
        ''', (nuevo_bono, registro_id))
        
        conn.commit()
        filas_afectadas = cursor.rowcount
        conn.close()
        
        return filas_afectadas > 0
    
    def obtener_estadisticas(self):
        """Obtiene estadísticas de los registros"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*), SUM(asistentes) FROM registros')
        total_registros, total_asistentes = cursor.fetchone()
        
        cursor.execute('''
            SELECT bono, COUNT(*), SUM(asistentes), SUM(monto)
            FROM registros 
            GROUP BY bono
        ''')
        
        estadisticas_bono = cursor.fetchall()
        conn.close()
        
        return {
            'total_registros': total_registros or 0,
            'total_asistentes': total_asistentes or 0,
            'por_bono': estadisticas_bono
        }
    
    def limpiar_registros(self):
        """Elimina todos los registros"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM registros')
        registros_eliminados = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return registros_eliminados

# ================= INICIALIZAR DB =================
db = Database()

# ================= SERVICIO WEB =================
app = Flask(__name__)

@app.route('/')
def home():
    stats = db.obtener_estadisticas()
    return f"""
    <html>
        <head>
            <title>🤖 Bot Congreso 2026</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .card {{ background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 10px 0; }}
                .success {{ color: green; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>🤖 Bot del Congreso 2026</h1>
            <div class="card">
                <p class="success">✅ Sistema con Corrección de Bonos</p>
                <p><strong>Total registros:</strong> {stats['total_registros']}</p>
                <p><strong>Total asistentes:</strong> {stats['total_asistentes']}</p>
                <p><strong>Tipos de bono:</strong> {len(db.obtener_tipos_bono())}</p>
            </div>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ================= ACTIVIDAD PERIÓDICA =================
def mantener_activo():
    """Función para mantener el bot activo enviando pings periódicos"""
    def ping_web():
        while True:
            try:
                # Obtener la URL dinámica de Replit
                repl_url = os.environ.get('REPLIT_URL', '')
                if repl_url:
                    requests.get(f'{repl_url}/health', timeout=10)
                    logger.info("🔄 Ping enviado para mantener activo")
                else:
                    # Si no hay URL, hacer ping a la ruta local
                    requests.get('http://localhost:8080/health', timeout=10)
            except Exception as e:
                logger.warning(f"Ping falló: {e}")
            time.sleep(300)  # Cada 5 minutos
    
    ping_thread = threading.Thread(target=ping_web)
    ping_thread.daemon = True
    ping_thread.start()
    return ping_thread

# ================= FUNCIONES PRINCIPALES DEL BOT =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        '¡Hola! 🤖\n'
        'Vamos a capturar datos para el Congreso 2026.\n\n'
        'Por favor, ingresa el **NOMBRE DEL GRUPO**:'
    )
    return GRUPO

async def capturar_grupo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['grupo'] = update.message.text
    await update.message.reply_text('✅ GRUPO guardado. Ahora ingresa el **GUÍA**:')
    return GUIA

async def capturar_guia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['guia'] = update.message.text
    await update.message.reply_text('✅ GUÍA guardado. Ahora ingresa el **BONO**:')
    return BONO

async def capturar_bono(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['bono'] = update.message.text
    await update.message.reply_text('✅ BONO guardado. Ahora ingresa el **MONTO**:')
    return MONTO

async def capturar_monto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['monto'] = update.message.text
    await update.message.reply_text('✅ MONTO guardado. Ingresa los **ASISTENTES**:')
    return ASISTENTES

async def capturar_asistentes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        grupo = context.user_data['grupo']
        guia = context.user_data['guia']
        bono = context.user_data['bono']
        monto = context.user_data['monto']
        asistentes = update.message.text
        
        # Guardar en base de datos
        registro_id = db.agregar_registro(grupo, guia, bono, monto, asistentes)
        
        await update.message.reply_text(
            f'🎉 **REGISTRO #{registro_id} COMPLETADO!**\n\n'
            f'📋 Resumen:\n'
            f'• 🏷️ Grupo: {grupo}\n'
            f'• 👤 Guía: {guia}\n'
            f'• 🎫 Bono: {bono}\n'
            f'• 💰 Monto: {monto}\n'
            f'• 👥 Asistentes: {asistentes}\n\n'
            '💾 **Guardado en base de datos**\n\n'
            'Usa /nuevo para otro registro o /corregir para editar bonos'
        )
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error guardando en BD: {e}")
        await update.message.reply_text('❌ Error al guardar el registro')
        return ConversationHandler.END

# ================= SISTEMA DE CORRECCIÓN DE BONOS =================
async def corregir_bono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los tipos de bono disponibles para corregir"""
    bonos = db.obtener_tipos_bono()
    
    if not bonos:
        await update.message.reply_text('📭 No hay registros con tipos de bono para corregir')
        return
    
    # Crear teclado inline con los bonos
    keyboard = []
    for bono in bonos:
        keyboard.append([InlineKeyboardButton(f"🎫 {bono}", callback_data=f"corregir_{bono}")])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_correccion")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        '🔧 **CORRECCIÓN DE BONOS**\n\n'
        'Selecciona el tipo de bono que quieres corregir:',
        reply_markup=reply_markup
    )

async def handle_corregir_bono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la selección de bono a corregir"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancelar_correccion":
        await query.edit_message_text('❌ Corrección cancelada')
        return
    
    if query.data.startswith("corregir_"):
        bono_actual = query.data.replace("corregir_", "")
        context.user_data['bono_a_corregir'] = bono_actual
        
        # Mostrar registros con este bono
        registros = db.obtener_registros_por_bono(bono_actual)
        
        if not registros:
            await query.edit_message_text(f'❌ No hay registros con bono: {bono_actual}')
            return
        
        mensaje = f'📋 **Registros con bono: {bono_actual}**\n\n'
        for i, (id_reg, grupo, guia, bono, monto, asistentes, fecha) in enumerate(registros[:10], 1):
            fecha_simple = fecha.split()[0] if isinstance(fecha, str) else str(fecha)[:10]
            mensaje += f"{i}. #{id_reg} - {grupo} ({guia})\n"
            mensaje += f"   👥{asistentes} 💰${float(monto):,.2f} 📅{fecha_simple}\n\n"
        
        # Botones para este bono
        keyboard = [
            [InlineKeyboardButton(f"✏️ Cambiar TODOS los '{bono_actual}'", callback_data=f"cambiar_todos_{bono_actual}")],
            [InlineKeyboardButton("🔙 Volver a bonos", callback_data="volver_bonos")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_correccion")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            mensaje + '¿Qué acción deseas realizar?',
            reply_markup=reply_markup
        )

async def handle_cambiar_todos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el cambio masivo de bonos"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("cambiar_todos_"):
        bono_actual = query.data.replace("cambiar_todos_", "")
        context.user_data['bono_a_corregir'] = bono_actual
        
        await query.edit_message_text(
            f'✏️ **CAMBIAR BONO: {bono_actual}**\n\n'
            f'Vas a cambiar TODOS los registros con bono "{bono_actual}"\n\n'
            'Por favor, escribe el **NUEVO NOMBRE** para este bono:'
        )
        
        return NUEVO_BONO

async def capturar_nuevo_bono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura el nuevo nombre del bono y realiza el cambio"""
    try:
        bono_actual = context.user_data.get('bono_a_corregir')
        nuevo_bono = update.message.text
        
        if not bono_actual:
            await update.message.reply_text('❌ Error: No se encontró el bono a corregir')
            return ConversationHandler.END
        
        # Obtener registros con el bono actual
        registros = db.obtener_registros_por_bono(bono_actual)
        
        if not registros:
            await update.message.reply_text(f'❌ No hay registros con bono: {bono_actual}')
            return ConversationHandler.END
        
        # Contador de cambios
        cambios_realizados = 0
        
        # Actualizar cada registro
        for registro in registros:
            registro_id = registro[0]
            if db.actualizar_bono(registro_id, nuevo_bono):
                cambios_realizados += 1
        
        await update.message.reply_text(
            f'✅ **CORRECCIÓN COMPLETADA**\n\n'
            f'• Bono anterior: `{bono_actual}`\n'
            f'• Bono nuevo: `{nuevo_bono}`\n'
            f'• Registros actualizados: {cambios_realizados}\n\n'
            '📊 Los cambios se han aplicado a todos los registros.'
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error en corrección de bono: {e}")
        await update.message.reply_text('❌ Error al realizar la corrección')
        return ConversationHandler.END

async def handle_volver_bonos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Vuelve a la lista de bonos"""
    query = update.callback_query
    await query.answer()
    
    bonos = db.obtener_tipos_bono()
    
    keyboard = []
    for bono in bonos:
        keyboard.append([InlineKeyboardButton(f"🎫 {bono}", callback_data=f"corregir_{bono}")])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_correccion")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        '🔧 **CORRECCIÓN DE BONOS**\n\n'
        'Selecciona el tipo de bono que quieres corregir:',
        reply_markup=reply_markup
    )

# ================= COMANDOS ADICIONALES =================
async def generar_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        registros = db.obtener_todos_registros()
        
        if not registros:
            await update.message.reply_text('📭 No hay datos en la base de datos')
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
                caption='📊 Reporte CSV desde Base de Datos'
            )
            
    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        await update.message.reply_text('❌ Error al generar reporte')

async def ver_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stats = db.obtener_estadisticas()
        
        mensaje = "📊 **ESTADÍSTICAS DEL CONGRESO**\n\n"
        mensaje += f"📈 Total registros: {stats['total_registros']}\n"
        mensaje += f"👥 Total asistentes: {stats['total_asistentes']}\n\n"
        
        if stats['por_bono']:
            mensaje += "🎫 **Por tipo de bono:**\n"
            for bono, cantidad, asistentes, monto in stats['por_bono']:
                mensaje += f"• {bono}: {cantidad} reg, {asistentes} asis, ${monto:,.2f}\n"
        
        await update.message.reply_text(mensaje)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        await update.message.reply_text('❌ Error al obtener estadísticas')

async def limpiar_base(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para limpiar la base de datos"""
    try:
        registros_eliminados = db.limpiar_registros()
        await update.message.reply_text(f'🗑️ Base de datos limpiada. {registros_eliminados} registros eliminados.')
    except Exception as e:
        logger.error(f"Error limpiando BD: {e}")
        await update.message.reply_text('❌ Error al limpiar base de datos')

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **COMANDOS DISPONIBLES:**\n\n"
        "🚀 /start - Iniciar captura de datos\n"
        "📝 /nuevo - Nuevo registro\n"
        "🔧 /corregir - Corregir tipos de bono\n"
        "📊 /reporte - Generar CSV desde BD\n"
        "📈 /estadisticas - Ver estadísticas\n"
        "🗑️ /limpiar - Limpiar base de datos\n"
        "ℹ️ /ayuda - Mostrar esta ayuda\n\n"
        "💾 **Sistema con corrección de bonos**"
    )

# ================= INICIAR BOT =================
def iniciar_bot():
    token = os.environ.get('BOT_TOKEN')
    
    if not token:
        logger.error("❌ BOT_TOKEN no encontrado")
        print("💡 Configura BOT_TOKEN en Secrets (🔒)")
        return
    
    try:
        application = Application.builder().token(token).build()
        
        # Conversación principal para capturar datos
        conv_principal = ConversationHandler(
            entry_points=[CommandHandler('start', start), CommandHandler('nuevo', start)],
            states={
                GRUPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_grupo)],
                GUIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_guia)],
                BONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_bono)],
                MONTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_monto)],
                ASISTENTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_asistentes)],
            },
            fallbacks=[CommandHandler('cancel', lambda u,c: u.message.reply_text('❌ Cancelado'))]
        )
        
        # Conversación para corrección de bonos
        conv_correccion = ConversationHandler(
            entry_points=[CallbackQueryHandler(handle_cambiar_todos, pattern='^cambiar_todos_')],
            states={
                NUEVO_BONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_nuevo_bono)],
            },
            fallbacks=[CommandHandler('cancel', lambda u,c: u.message.reply_text('❌ Corrección cancelada'))]
        )
        
        # Handlers principales
        application.add_handler(conv_principal)
        application.add_handler(conv_correccion)
        application.add_handler(CommandHandler("corregir", corregir_bono))
        application.add_handler(CommandHandler("reporte", generar_reporte))
        application.add_handler(CommandHandler("estadisticas", ver_estadisticas))
        application.add_handler(CommandHandler("limpiar", limpiar_base))
        application.add_handler(CommandHandler("ayuda", ayuda))
        
        # Handlers para botones inline
        application.add_handler(CallbackQueryHandler(handle_corregir_bono, pattern='^corregir_'))
        application.add_handler(CallbackQueryHandler(handle_volver_bonos, pattern='^volver_bonos'))
        application.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.edit_message_text('❌ Corrección cancelada'), pattern='^cancelar_correccion'))
        
        print("🤖 Bot con Corrección de Bonos iniciado correctamente")
        print("✅ Envía /start a tu bot en Telegram")
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def iniciar_servidor_web():
    """Inicia el servidor web sin modo debug"""
    app.run(host='0.0.0.0', port=8080, debug=False)

if __name__ == '__main__':
    print("🚀 Iniciando Bot 24/7 del Congreso 2026...")
    
    # Iniciar sistema de mantenimiento activo
    mantener_activo()
    
    # Iniciar bot en hilo separado
    bot_thread = threading.Thread(target=iniciar_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Iniciar servidor web
    iniciar_servidor_web()