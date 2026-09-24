# --- IMPORTACIONES DE LIBRERÍAS ---
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import gspread
import pandas as pd
import streamlit as st
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Control de Inventario y Calidad", page_icon="📦", layout="wide"
)

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def conectar_google_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    # Leemos las credenciales directamente desde los secretos de Streamlit
    creds_dict = dict(st.secrets["gspread_json"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    
    client = gspread.authorize(creds)
    sheet = client.open("Inventario_Calidad_Almacen")
    return sheet

try:
    sh = conectar_google_sheets()
    ws_inventario = sh.worksheet("Inventario")
    ws_movimientos = sh.worksheet("Movimientos")
except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    st.stop()

# --- ENVIAR ALERTA DE STOCK BAJO ---
def enviar_alerta_stock_bajo(material, cantidad_actual, limite_minimo):
    remitente = "calidadalmacen4@gmail.com"
    password = "ogfz prpu bzzh ggnj"
    destinatario = ["calidadalmacen4@gmail.com"]

    asunto = f"🚨 ALERTA DE STOCK BAJO: {material}"
    cuerpo = f"""
    Atención,
    
    El material **{material}** ha alcanzado un nivel crítico.
    - Cantidad actual: {cantidad_actual}
    - Límite mínimo permitido: {limite_minimo}
    
    Por favor, gestione el reabastecimiento lo antes posible.
    
    Atentamente,
    Sistema de Almacén y Calidad
    """
    
    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = ", ".join(destinatario)
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Error al enviar correo: {e}")
