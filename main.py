import os
import time
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import libsql

app = FastAPI(title="API Catastro RUC SRI - Ecuador Completo")

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
    return {"mensaje": "API de RUC funcionando", "url1": TURSO_URL[:25] if TURSO_URL else "vacía", "url2": TURSO_URL_2[:25] if TURSO_URL_2 else "vacía"}

@app.get("/api/ruc/{numero}", response_model=List[Contribuyente])
def consultar_ruc(numero: str):
    if not numero.isdigit():
        raise HTTPException(status_code=400, detail="El documento debe contener solo números.")
    
    if len(numero) == 10:
        numero = numero + "001" 
    elif len(numero) != 13:
        raise HTTPException(status_code=400, detail="Debe ingresar una cédula (10 dígitos) o un RUC (13 dígitos).")

    query = "SELECT * FROM contribuyentes WHERE ruc LIKE ? LIMIT 10"
    inicio_total = time.time()

    if TURSO_URL and TURSO_TOKEN:
        t0 = time.time()
        try:
            conn1 = libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)
            t1 = time.time()
            print(f"⏱️ DB1 Conexión: {t1-t0:.2f}s (URL: {TURSO_URL[:30]})")
            
            cur1 = conn1.execute(query, (numero + '%',)) 
            t2 = time.time()
            print(f"⏱️ DB1 Query: {t2-t1:.2f}s")
            
            columnas = [col[0] for col in cur1.description]
            rows = cur1.fetchall()
            conn1.close()
            if rows:
                print(f"⏱️ DB1 TOTAL: {time.time()-inicio_total:.2f}s")
                return [Contribuyente(**dict(zip(columnas, row))) for row in rows]
        except Exception as e:
            print(f"❌ Error en DB1 (después de {time.time()-t0:.2f}s): {e}")

    if TURSO_URL_2 and TURSO_TOKEN_2:
        t0 = time.time()
        try:
            conn2 = libsql.connect(database=TURSO_URL_2, auth_token=TURSO_TOKEN_2)
            t1 = time.time()
            print(f"⏱️ DB2 Conexión: {t1-t0:.2f}s (URL: {TURSO_URL_2[:30]})")
            
            cur2 = conn2.execute(query, (numero + '%',))
            t2 = time.time()
            print(f"⏱️ DB2 Query: {t2-t1:.2f}s")
            
            columnas = [col[0] for col in cur2.description]
            rows = cur2.fetchall()
            conn2.close()
            if rows:
                print(f"⏱️ DB2 TOTAL: {time.time()-inicio_total:.2f}s")
                return [Contribuyente(**dict(zip(columnas, row))) for row in rows]
        except Exception as e:
            print(f"❌ Error en DB2 (después de {time.time()-t0:.2f}s): {e}")

    print(f"⏱️ Búsqueda no encontrada. Total: {time.time()-inicio_total:.2f}s")
    raise HTTPException(status_code=404, detail="Cédula o RUC no encontrado en el catastro.")
