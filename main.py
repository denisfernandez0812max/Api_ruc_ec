from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import libsql_client as libsql
import os

app = FastAPI(title="API Catastro RUC SRI")

TURSO_URL = os.getenv("TURSO_URL", "libsql://rucec-denisfer2000.aws-sa-east-1.turso.io")
TURSO_TOKEN = os.getenv("TURSO_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9") 

class Contribuyente(BaseModel):
    ruc: str
    razon_social: str
    estado: str

@app.get("/")
def inicio():
    return {"mensaje": "API de RUC funcionando correctamente"}

@app.get("/api/ruc/{ruc}", response_model=Contribuyente)
def consultar_ruc(ruc: str):
    if len(ruc) != 13 or not ruc.isdigit():
        raise HTTPException(status_code=400, detail="El RUC debe tener 13 dígitos numéricos.")
    
    conn = libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)
    cursor = conn.cursor()
    
    cursor.execute("SELECT ruc, razon_social, estado FROM contribuyentes WHERE ruc = ?", (ruc,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        raise HTTPException(status_code=404, detail="RUC no encontrado en el catastro.")
    
    return Contribuyente(ruc=row[0], razon_social=row[1], estado=row[2])