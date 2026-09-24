import subprocess
subprocess.run(["pip", "install", "gspread", "oauth2client"])

# --- IMPORTACIONES DE LIBRERIAS ---
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

  asunto = f"⚠️ ALERTA DE STOCK BAJO: {material}"
  cuerpo = f"""
    Atención,

    Se ha registrado una salida en el Almacén de Calidad y el siguiente insumo ha quedado por debajo del límite mínimo:

    • Material / Insumo: {material}
    • Stock Actual: {cantidad_actual}
    • Límite Mínimo Requerido: {limite_minimo}

    Por favor, gestionar el reabastecimiento correspondiente.

    ---
    Sistema Automático de Control de Inventario
    """

  msg = MIMEMultipart()
  msg["From"] = remitente
  msg["To"] = ", ".join(destinatario)
  msg["Subject"] = asunto
  msg.attach(MIMEText(cuerpo, "plain"))

  try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(remitente, password)
    server.send_message(msg)
    server.quit()
    return True
  except Exception as e:
    print(f"Error al enviar correo: {e}")
    return False

# --- INTERFAZ DE USUARIO ---
st.title("📦 Sistema de Control de Inventario y Calidad 🧠")
st.sidebar.title("Menú de Navegación")

menu = st.sidebar.radio(
    "Selecciona una opción:",
    ["📊 Ver Inventario", "➕ Registrar Movimiento", "📋 Historial"],
)

# --- FUNCIÓN PARA LEER DATOS ---
def obtener_datos(worksheet):
  data = worksheet.get_all_records()
  return pd.DataFrame(data)

# --- 1. VER INVENTARIO ---
if menu == "📊 Ver Inventario":
  st.header("Inventario Actual en la Nube")

  if st.button("🔄 Actualizar Datos"):
    st.rerun()

  df_inv = obtener_datos(ws_inventario)

  if df_inv.empty:
    st.info(
        "Aún no hay productos registrados. Ve a la pestaña de movimientos o"
        " añade registros."
    )
  else:
    st.dataframe(df_inv, use_container_width=True)

# --- 2. REGISTRAR MOVIMIENTO ---
elif menu == "➕ Registrar Movimiento":
  st.header("Registro de Entradas y Salidas")

  df_inv = obtener_datos(ws_inventario)
  lista_productos = (
      df_inv["Producto"].tolist() if not df_inv.empty else ["Ejemplo: Caja Corrugada"]
  )

  with st.form("form_movimiento"):
    tipo = st.selectbox("Tipo de Movimiento", ["Entrada", "Salida"])
    producto = st.selectbox("Producto", lista_productos)
    cantidad = st.number_input(
        "Cantidad", min_value=1, step=1, value=1
    )
    
    # Cambiado de Usuario a Responsable de entrega y agregado Quien recibe
    responsable = st.text_input("Responsable de entrega", value="Juan Diego")
    quien_recibe = st.text_input("Quien recibe", value="")

    submitted = st.form_submit_button("Guardar Movimiento")

    if submitted:
      fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

      # Guardar en la pestaña Movimientos incluyendo al responsable y a quien recibe
      ws_movimientos.append_row([fecha_hora, tipo, producto, cantidad, responsable, quien_recibe])
      st.success(
          f"¡Movimiento de {tipo} registrado exitosamente para {producto}!"
      )
      
      # --- EVALUACIÓN DE STOCK BAJO ---
      if tipo == "Salida":
            fila = df_inv[df_inv["Producto"] == producto]
            
            if not fila.empty:
                stock_actual = int(fila["Cantidad"].values[0]) - cantidad
                stock_minimo = int(fila["Stock Minimo"].values[0])
                
                if stock_actual <= stock_minimo:
                    alerta_enviada = enviar_alerta_stock_bajo(producto, stock_actual, stock_minimo)
                    
                    if alerta_enviada:
                        st.warning(f"⚠️ ¡Stock bajo detectado ({stock_actual} pzs)! Se ha enviado una alerta por correo.")
                    else:
                        st.error("El inventario se actualizó, pero no se pudo enviar el correo de alerta.")

# --- 3. HISTORIAL DE MOVIMIENTOS ---
elif menu == "📋 Historial":
  st.header("Historial de Movimientos")

  if st.button("🔄 Actualizar Historial"):
    st.rerun()

  df_mov = obtener_datos(ws_movimientos)

  if df_mov.empty:
    st.info("Aún no se han registrado movimientos.")
  else:
    st.dataframe(df_mov, use_container_width=True)
