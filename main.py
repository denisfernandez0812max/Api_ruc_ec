import os
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware  # 🆕 IMPORTANTE
import libsql

app = FastAPI(title="API Catastro RUC SRI - Ecuador Completo")

# 🆕 CONFIGURACIÓN DE CORS (Permite llamadas directas desde el POS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TURSO_URL = os.environ.get("TURSO_URL")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN")
TURSO_URL_2 = os.environ.get("TURSO_URL_2")
TURSO_TOKEN_2 = os.environ.get("TURSO_TOKEN_2")

class Contribuyente(BaseModel):
    ruc: str
    razon_social: str
    codigo_jurisdiccion: str
    estado: str
    clase_contribuyente: str
    fecha_inicio_actividades: str
    fecha_actualizacion: str
    fecha_suspension_definitiva: str
    fecha_reinicio_actividades: str
    obligado: str
    tipo_contribuyente: str
    numero_establecimiento: str
    nombre_fantasia_comercial: str
    estado_establecimiento: str
    provincia: str
    canton: str
    parroquia: str
    codigo_ciiu: str
    actividad_economica: str
    agente_retencion: str
    especial: str

@app.get("/")
def inicio():
    return {"mensaje": "API de RUC funcionando. Use /api/ruc/{numero}"}

@app.get("/api/ruc/{numero}", response_model=List[Contribuyente])
def consultar_ruc(numero: str):
    if not numero.isdigit():
        raise HTTPException(status_code=400, detail="El documento debe contener solo números.")
    
    if len(numero) == 10:
        numero = numero + "001" 
    elif len(numero) != 13:
        raise HTTPException(status_code=400, detail="Debe ingresar una cédula (10 dígitos) o un RUC (13 dígitos).")

    # ✅ AGREGADO LIMIT 10 PARA EVITAR QUE SE CUELGUE SI HAY MUCHAS SUCURSALES
    query = "SELECT * FROM contribuyentes WHERE ruc LIKE ? LIMIT 10"

    try:
        if TURSO_URL and TURSO_TOKEN:
            conn1 = libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)
            cur1 = conn1.execute(query, (numero + '%',)) 
            columnas = [col[0] for col in cur1.description]
            rows = cur1.fetchall()
            conn1.close()
            if rows:
                return [Contribuyente(**dict(zip(columnas, row))) for row in rows]
    except Exception as e:
        print(f"Error en DB1: {e}")

    try:
        if TURSO_URL_2 and TURSO_TOKEN_2:
            conn2 = libsql.connect(database=TURSO_URL_2, auth_token=TURSO_TOKEN_2)
            cur2 = conn2.execute(query, (numero + '%',))
            columnas = [col[0] for col in cur2.description]
            rows = cur2.fetchall()
            conn2.close()
            if rows:
                return [Contribuyente(**dict(zip(columnas, row))) for row in rows]
    except Exception as e:
        print(f"Error en DB2: {e}")

    raise HTTPException(status_code=404, detail="Cédula o RUC no encontrado en el catastro.")
