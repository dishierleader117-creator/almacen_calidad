# --- IMPORTACIONES DE LIBRERÍAS ---
import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import gspread

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Control de Inventario y Calidad", page_icon="📦", layout="wide"
)

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def conectar_google_sheets():
    creds_dict = dict(st.secrets["gspread_json"])
    client = gspread.service_account_from_dict(creds_dict)
    sheet = client.open("Inventario_Calidad_Almacen")
    return sheet

try:
    sh = conectar_google_sheets()
    ws_inventario = sh.worksheet("Inventario")
    ws_movimientos = sh.worksheet("Movimientos")
except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    st.stop()
