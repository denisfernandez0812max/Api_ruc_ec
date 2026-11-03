import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import libsql

app = FastAPI(title="API Catastro RUC SRI")

# --- VARIABLES DE ENTORNO PARA LA BASE DE DATOS 1 (22 Provincias) ---
TURSO_URL = os.environ.get("TURSO_URL")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN")

# --- VARIABLES DE ENTORNO PARA LA BASE DE DATOS 2 (Pichincha y Guayas) ---
TURSO_URL_2 = os.environ.get("TURSO_URL_2")
TURSO_TOKEN_2 = os.environ.get("TURSO_TOKEN_2")

class Contribuyente(BaseModel):
    ruc: str
    razon_social: str
    estado: str

@app.get("/")
def inicio():
    return {"mensaje": "API de RUC funcionando correctamente con doble base de datos"}

@app.get("/api/ruc/{numero}", response_model=Contribuyente)
def consultar_ruc(numero: str):
    # 1. Validar que solo sean números
    if not numero.isdigit():
        raise HTTPException(status_code=400, detail="El documento debe contener solo números.")
    
    # 2. Si tiene 10 dígitos (Cédula), le agregamos '001'
    if len(numero) == 10:
        numero = numero + "001"
    # 3. Si no tiene 10 ni 13 dígitos, rechazamos
    elif len(numero) != 13:
        raise HTTPException(status_code=400, detail="Debe ingresar una cédula (10 dígitos) o un RUC (13 dígitos).")

    # 4. Buscar primero en la Base de Datos 1 (Provincias pequeñas)
    try:
        if TURSO_URL and TURSO_TOKEN:
            conn1 = libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)
            cur1 = conn1.execute("SELECT ruc, razon_social, estado FROM contribuyentes WHERE ruc = ?", (numero,))
            row = cur1.fetchone()
            conn1.close()
            
            if row is not None:
                print(f"RUC {numero} encontrado en DB1")
                return Contribuyente(ruc=row[0], razon_social=row[1], estado=row[2])
    except Exception as e:
        print(f"Error en DB1: {e}")

    # 5. Si no se encontró en DB1, buscar en la Base de Datos 2 (Pichincha/Guayas)
    try:
        if TURSO_URL_2 and TURSO_TOKEN_2:
            conn2 = libsql.connect(database=TURSO_URL_2, auth_token=TURSO_TOKEN_2)
            cur2 = conn2.execute("SELECT ruc, razon_social, estado FROM contribuyentes WHERE ruc = ?", (numero,))
            row = cur2.fetchone()
            conn2.close()
            
            if row is not None:
                print(f"RUC {numero} encontrado en DB2")
                return Contribuyente(ruc=row[0], razon_social=row[1], estado=row[2])
    except Exception as e:
        print(f"Error en DB2: {e}")

    # 6. Si no se encontró en ninguna de las dos
    raise HTTPException(status_code=404, detail="Cédula o RUC no encontrado en el catastro.")