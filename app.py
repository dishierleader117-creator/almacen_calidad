import os 
os.system("pip install gspread oauth2client")

# --- IMPORTACIONES DE LIBRERÍAS ---
import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import gspread
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

