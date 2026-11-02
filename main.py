import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import libsql

app = FastAPI(title="API Catastro RUC SRI")

# Lee las variables ocultas desde Render (Environment)
TURSO_URL = os.environ.get("TURSO_URL")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN")

class Contribuyente(BaseModel):
    ruc: str
    razon_social: str
    estado: str

@app.get("/")
def inicio():
    return {"mensaje": "API de RUC funcionando correctamente"}

@app.get("/api/ruc/{numero}", response_model=Contribuyente)
def consultar_ruc(numero: str):
    # 1. Validar que solo sean números
    if not numero.isdigit():
        raise HTTPException(status_code=400, detail="El documento debe contener solo números.")
    
    # 2. Si tiene 10 dígitos (Cédula), le agregamos '001' para buscar en la base de datos
    if len(numero) == 10:
        numero = numero + "001"
    # 3. Si no tiene 10 ni 13 dígitos, rechazamos la petición
    elif len(numero) != 13:
        raise HTTPException(status_code=400, detail="Debe ingresar una cédula (10 dígitos) o un RUC (13 dígitos).")

    # 4. Conectar a Turso y buscar
    try:
        conn = libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)
        cur = conn.execute("SELECT ruc, razon_social, estado FROM contribuyentes WHERE ruc = ?", (numero,))
        row = cur.fetchone()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {type(e).__name__}: {e}")

    # 5. Si no se encontró
    if row is None:
        raise HTTPException(status_code=404, detail="Cédula o RUC no encontrado en el catastro.")
    
    # 6. Devolver los datos
    return Contribuyente(ruc=row[0], razon_social=row[1], estado=row[2])