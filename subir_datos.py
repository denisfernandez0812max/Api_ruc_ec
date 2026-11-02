import pandas as pd
import libsql

# --- CONFIGURACIÓN ---
TURSO_URL = "libsql://rucec-denisfer2000.aws-sa-east-1.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3OTI5OTY1NzgsImlkIjoiMDFhMTc2NjgtOTcwMS03ZmE2LTllNmEtNTk0ZDUzZmU1MDY2Iiwia2lkIjoiM3kxS1lKREdwM0V2ZkZLQkxpdjc1WE9fSndzVGt6TGY2OWhFenNiTnl5ayIsInJpZCI6ImYxMTU2MTM0LTg1MTUtNGUwOS1hMmRjLWYzNDI0OGM2Y2U0YiJ9.dbtRIbQ7mnANp4BDO_iEC8QkJTpgKfzVbNUPMqT9Nd3Ka1dISqaeMZEABlAREKUMyFfDdCUjUDCsJXR_nAAWDw"
ARCHIVO_CSV = 'catastro_ruc_pichincha.csv' 

def subir_datos():
    print("Conectando a Turso...")
    # Usamos libsql.connect (la librería nueva)
    conn = libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)

    # Crear la tabla
    conn.execute('''
        CREATE TABLE IF NOT EXISTS contribuyentes (
            ruc TEXT PRIMARY KEY,
            razon_social TEXT,
            estado TEXT
        )
    ''')

    print(f"Leyendo el archivo {ARCHIVO_CSV}...")
    # Usamos sep='|' porque los archivos del SRI suelen venir así
    try:
        df = pd.read_csv(ARCHIVO_CSV, sep='|', encoding='latin-1', dtype=str, on_bad_lines='skip')
    except Exception as e:
        print(f"Error leyendo el archivo: {e}")
        return

    print("Columnas encontradas:", df.columns.tolist())

    col_ruc = 'NUMERO_RUC'
    col_nombre = 'RAZON_SOCIAL'
    col_estado = 'ESTADO_CONTRIBUYENTE'

    if col_ruc not in df.columns:
        print("ERROR: No se encontró la columna del RUC. Revisa los nombres de arriba.")
        return

    # Limpieza
    df = df[[col_ruc, col_nombre, col_estado]]
    df.columns = ['ruc', 'razon_social', 'estado']
    df = df.dropna(subset=['ruc', 'razon_social'])
    df = df.fillna('')
    
    datos = list(df.itertuples(index=False, name=None))
    print(f"Subiendo {len(datos)} registros a Turso en bloques...")

    # Subimos en bloques de 1000
    batch_size = 1000
    for i in range(0, len(datos), batch_size):
        chunk = datos[i:i+batch_size]
        
        # Usamos executemany para insertar todo el bloque de una vez
        conn.executemany(
            "INSERT OR IGNORE INTO contribuyentes (ruc, razon_social, estado) VALUES (?, ?, ?)", 
            chunk
        )
        conn.commit() # Guardamos los cambios en la base de datos
        print(f"Subidos {min(i+batch_size, len(datos))} de {len(datos)}...")

    conn.close()
    print("¡Datos subidos exitosamente a Turso!")

if __name__ == "__main__":
    subir_datos()