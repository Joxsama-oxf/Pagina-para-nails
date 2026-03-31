import sqlite3
import os

# 1. UBICAR LA BASE DE DATOS
# Buscamos en la carpeta 'instance' que es donde suele estar en tu proyecto
db_path = os.path.join(os.getcwd(), 'instance', 'lauranails.db')

if not os.path.exists(db_path):
    print(f"⚠️ NO ENCUENTRO LA BASE DE DATOS EN: {db_path}")
    print("Buscando en la carpeta raíz...")
    db_path = 'lauranails.db'

print(f"🔌 Conectando a: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 2. BORRAR TODO (NUCLEAR)
    cursor.execute("DELETE FROM servicio")
    print("🗑️  TABLA LIMPIADA (Se borraron todos los servicios viejos).")

    # 3. DATOS EXACTOS DE TU FACTURACIÓN
    # (Nombre, Precio, Categoria)
    servicios = [
        ('Manicure Tradicional', 5.00, 'Manos'),
        ('Semipermanente', 7.00, 'Manos'),
        ('Rubber', 12.00, 'Manos'),
        ('Softgel', 15.00, 'Manos'),
        ('Esculpidas #3', 25.00, 'Manos'),
        ('Poligel', 28.00, 'Manos'),
        ('Baño Acrílico', 15.00, 'Manos'),
        
        ('Pedicure Tradicional', 7.00, 'Pies'),
        ('Pedicure Profunda', 12.00, 'Pies'),
        ('Semipermanente Pies', 12.00, 'Pies'),
        
        ('Retiro Manos', 5.00, 'Retiros'),
        ('Retiro Gel', 2.00, 'Retiros'),
        
        ('Ojo de Gato', 5.00, 'Adicionales'),
        ('Efecto Espejo', 3.00, 'Adicionales'),
        ('Flores 3D', 1.50, 'Adicionales'),
        ('Encapsulado', 1.00, 'Adicionales')
    ]

    # 4. INSERTAR UNO POR UNO
    cursor.executemany("INSERT INTO servicio (nombre, precio, categoria) VALUES (?, ?, ?)", servicios)
    conn.commit()
    print(f"✅ SE INSERTARON {len(servicios)} SERVICIOS NUEVOS.")

    conn.close()
    print("✨ LISTO. CIERRA Y ABRE TU VISUALIZADOR DE BD PARA VER LOS CAMBIOS.")

except Exception as e:
    print(f"❌ ERROR FATAL: {e}")