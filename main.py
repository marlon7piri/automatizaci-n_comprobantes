from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
from email.message import EmailMessage
import smtplib
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from weasyprint import HTML
from io import BytesIO
from dotenv import load_dotenv

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # O usa tu frontend URL exacta por seguridad
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

# Directorio para guardar los PDF generados
PDF_DIR = "comprobantes"
os.makedirs(PDF_DIR, exist_ok=True)
EMAIL_USER=os.getenv("EMAIL_USER")
EMAIL_PASS=os.getenv("EMAIL_PASS")


# Cargar plantilla HTML
env = Environment(loader=FileSystemLoader("templates"))
template = env.get_template("comprobante.html")

def generar_pdf(datos):
    html = template.render(datos)
    output_path = os.path.join(PDF_DIR, f"{datos['nombre']}.pdf")
    HTML(string=html).write_pdf(output_path)
    return output_path

def enviar_email(correo_destino, pdf_path):
    msg = EmailMessage()
    msg["Subject"] = "Tu comprobante de pago"
    msg["From"] = EMAIL_USER
    msg["To"] = correo_destino
    msg.set_content("Adjunto encontrarás tu comprobante de pago.")

    with open(pdf_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=os.path.basename(pdf_path))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

@app.post("/subir-excel")
def procesar_excel(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        df = pd.read_excel(file.file)
        df.columns = df.columns.str.strip()

        # Verifica que las columnas clave existan
        columnas_requeridas = ["Nombre", "Salario base", "Propina", "Días trabajados", "Total a pagar", "Fecha de pago", "Correo"]
        for col in columnas_requeridas:
            if col not in df.columns:
                return JSONResponse(status_code=400, content={"error": f"Columna faltante: '{col}'"})
            
        for _, row in df.iterrows():
            
            fecha_str = row['Fecha de pago']

            # Intentar parsear la fecha en formato 'dd/mm/yyyy'
            try:
                
                fecha_obj = pd.to_datetime(fecha_str)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Formato de fecha no válido: '{fecha_str}'. Debe ser DD/MM/YYYY"}
                )

            # Formatear la fecha como 'DD/MM/YYYY' para mostrar en el PDF
            fecha_formateada = fecha_obj.strftime("%d/%m/%Y")
            
            datos = {
                "nombre": row["Nombre"],
                "salario": row["Salario base"],
                "propina": row["Propina"],
                "dias": row["Días trabajados"],
                "total": row["Total a pagar"],
                "fecha": fecha_formateada,
                "correo":row["Correo"]
            }
            pdf_path = generar_pdf(datos)
            background_tasks.add_task(enviar_email, row["Correo"], pdf_path)

        return JSONResponse(content={"mensaje": "Comprobantes en proceso de envío."})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
