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
    # Asegurar que los saltos de línea de la llave privada se lean correctamente
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
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

# --- ENVIAR ALERTA DE STOCK BAJO ---
def enviar_alerta_stock_bajo(material, cantidad_actual, limite_minimo):
    remitente = "calidadalmacen4@gmail.com"
    password = "ogfz prpu bzzh ggnj"
    destinatario = ["calidadalmacen4@gmail.com"]

    asunto = f"⚠️ ALERTA DE STOCK BAJO: {material}"
    cuerpo = f"""Atención,

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
    ["📊 Ver Inventario", "➕ Registrar Movimiento", "📁 Historial"],
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
        st.info("Aún no hay productos registrados. Ve a la pestaña de movimientos o añade registros.")
    else:
        st.dataframe(df_inv, use_container_width=True)

# --- 2. REGISTRAR MOVIMIENTO ---
elif menu == "➕ Registrar Movimiento":
    st.header("Registrar Entrada o Salida de Insumo")
    
    df_inv = obtener_datos(ws_inventario)
    if df_inv.empty:
        st.warning("No hay productos en el inventario para registrar movimientos.")
    else:
        productos = df_inv["Producto"].tolist() if "Producto" in df_inv.columns else []
        
        with st.form("form_movimiento"):
            tipo = st.selectbox("Tipo de Movimiento", ["Entrada", "Salida"])
            producto_sel = st.selectbox("Selecciona el Insumo", productos)
            cantidad_mov = st.number_input("Cantidad", min_value=1, step=1)
            usuario = st.text_input("Responsable / Usuario")
            
            submitted = st.form_submit_button("Guardar Movimiento")
            
            if submitted:
                if not usuario.strip():
                    st.error("Por favor, ingresa el nombre del responsable.")
                else:
                    cell = ws_inventario.find(producto_sel)
                    if cell:
                        fila = cell.row
                        val_actual = int(ws_inventario.cell(fila, 2).value or 0)
                        stock_min = int(ws_inventario.cell(fila, 3).value or 0)
                        
                        if tipo == "Entrada":
                            nuevo_stock = val_actual + cantidad_mov
                        else:
                            nuevo_stock = val_actual - cantidad_mov
                            if nuevo_stock < 0:
                                nuevo_stock = 0
                        
                        ws_inventario.update_cell(fila, 2, nuevo_stock)
                        
                        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ws_movimientos.append_row([fecha_actual, tipo, producto_sel, cantidad_mov, usuario])
                        
                        st.success(f"¡Movimiento registrado con éxito! Stock actualizado a: {nuevo_stock}")
                        
                        if tipo == "Salida" and nuevo_stock <= stock_min:
                            enviar_alerta_stock_bajo(producto_sel, nuevo_stock, stock_min)
                            st.warning(f"⚠️ ¡Atención! El insumo {producto_sel} ha quedado por debajo del stock mínimo. Se ha enviado una alerta por correo.")
                    else:
                        st.error("No se encontró el producto en la hoja de inventario.")

# --- 3. HISTORIAL ---
elif menu == "📁 Historial":
    st.header("Historial de Movimientos")
    if st.button("🔄 Actualizar Historial"):
        st.rerun()
        
    df_mov = obtener_datos(ws_movimientos)
    if df_mov.empty:
        st.info("Aún no hay movimientos registrados.")
    else:
        st.dataframe(df_mov, use_container_width=True)
