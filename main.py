from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
from datetime import datetime

app = FastAPI()

def safe_int_conversion(value, default=0):
    if pd.isna(value) or str(value).strip() == '':
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

@app.post("/generate-sql/")
async def generate_sql(file: UploadFile = File(...)):
    try:
        df = pd.read_excel(file.file, header=5)
        if df.empty:
            return JSONResponse(status_code=400, content={"error": "A planilha está vazia"})

        sql_scripts = []

        for index, row in df.iterrows():
            if pd.isna(row.get('resumoSolicitacao')) or str(row.get('resumoSolicitacao')).strip() == "":
                continue

            script = f"""
-- Script gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Dados da loja: {row.get('storeNome', '').strip()}

gestorEntityId := {safe_int_conversion(row.get('gestorEntityId'))};
gestorNome := '{str(row.get('gestorName', '')).strip()}';
storeNome := '{str(row.get('storeNome', '')).strip()}';
numeroRegistroJunta := '{str(row.get('numeroRegistroJunta', '')).strip()}';
SELECT NVL(MAX(GESTOR_ID), 0) + 1 INTO gestorId FROM GESTOR;
gestorLogo := '{str(row.get('gestorLogo', '')).strip()}';
store_uri = '{str(row.get('storeUri', '')).strip()}';
gestorContactEmail := '{str(row.get('gestorContactEmail', '')).strip()}';
gestorTabela := {safe_int_conversion(row.get('gestorTabela'))};
leiloeiroEntityId := {safe_int_conversion(row.get('leiloeiroEntityId'))};

-- Fim do script
"""
            sql_scripts.append(script.strip())

        return {"scripts": sql_scripts}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})