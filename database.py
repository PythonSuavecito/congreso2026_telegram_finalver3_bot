import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name="congreso_2026.db"):
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
    
    def obtener_registro_por_id(self, registro_id):
        """Obtiene un registro específico por ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, grupo, guia, bono, monto, asistentes, fecha_creacion 
            FROM registros 
            WHERE id = ?
        ''', (registro_id,))
        
        registro = cursor.fetchone()
        conn.close()
        
        return registro
    
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
    
    def eliminar_registro(self, registro_id):
        """Elimina un registro por ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM registros WHERE id = ?', (registro_id,))
        
        conn.commit()
        filas_afectadas = cursor.rowcount
        conn.close()
        
        return filas_afectadas > 0
    
    def eliminar_registros_por_bono(self, bono):
        """Elimina todos los registros de un tipo de bono"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM registros WHERE bono = ?', (bono,))
        
        conn.commit()
        filas_afectadas = cursor.rowcount
        conn.close()
        
        return filas_afectadas
    
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
    
    def buscar_registros_por_grupo(self, grupo):
        """Busca registros por nombre de grupo"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, grupo, guia, bono, monto, asistentes, fecha_creacion 
            FROM registros 
            WHERE grupo LIKE ? 
            ORDER BY fecha_creacion DESC
        ''', (f'%{grupo}%',))
        
        registros = cursor.fetchall()
        conn.close()
        
        return registros
