import sys
import os

# 1. Configuramos una carpeta local 'packages' con permisos de escritura
packages_dir = os.path.join(os.path.dirname(__file__), "packages")
if packages_dir not in sys.path:
    sys.path.insert(0, packages_dir)

# 2. Intentamos importar gspread; si no está, lo instalamos localmente de inmediato
try:
    import gspread
except ImportError:
    import subprocess
    os.makedirs(packages_dir, exist_ok=True)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gspread", "--target", packages_dir])
    import gspread

# --- IMPORTACIONES DE LIBRERÍAS ---
import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
    st.success("¡Conexión exitosa con Google Sheets!")
except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    st.stop()
