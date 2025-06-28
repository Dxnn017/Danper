import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="TPS - Seguimiento de Producción y Servicios", layout='wide')

# Datos simulados en memoria
if 'ordenes' not in st.session_state:
    st.session_state['ordenes'] = []
if 'inventario' not in st.session_state:
    st.session_state['inventario'] = [
        {'material': 'Materia Prima A', 'stock': 100, 'minimo': 20},
        {'material': 'Producto Terminado B', 'stock': 50, 'minimo': 10},
    ]
if 'incidencias' not in st.session_state:
    st.session_state['incidencias'] = []

# Dashboard principal
st.title("TPS - Seguimiento de Producción y Servicios")
tabs = st.tabs(["Dashboard", "Órdenes de Producción", "Inventario", "Incidencias", "Reportes"])

# Dashboard KPIs
with tabs[0]:
    st.header("Indicadores principales")
    total_ordenes = len(st.session_state['ordenes'])
    ordenes_proceso = sum(1 for o in st.session_state['ordenes'] if o['estado'] == "En proceso")
    ordenes_terminadas = sum(1 for o in st.session_state['ordenes'] if o['estado'] == "Finalizada")
    incidencias = len(st.session_state['incidencias'])
    stock_bajo = sum(1 for item in st.session_state['inventario'] if item['stock'] <= item['minimo'])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Órdenes totales", total_ordenes)
    col2.metric("En proceso", ordenes_proceso)
    col3.metric("Finalizadas", ordenes_terminadas)
    col4.metric("Incidencias", incidencias)
    col5.metric("Stock bajo", stock_bajo)

# Órdenes de Producción
with tabs[1]:
    st.header("Órdenes de Producción")
    with st.form("Nueva orden"):
        producto = st.text_input("Producto")
        cantidad = st.number_input("Cantidad", min_value=1, step=1)
        responsable = st.text_input("Responsable")
        submitted = st.form_submit_button("Registrar Orden")
        if submitted and producto and responsable:
            st.session_state['ordenes'].append({
                'producto': producto,
                'cantidad': cantidad,
                'responsable': responsable,
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'estado': "En proceso"
            })
            st.success("Orden registrada")

    df_ordenes = pd.DataFrame(st.session_state['ordenes'])
    if not df_ordenes.empty:
        st.dataframe(df_ordenes)
        idx = st.selectbox("Selecciona orden para finalizar", df_ordenes.index, format_func=lambda i: f"{df_ordenes.loc[i,'producto']} ({df_ordenes.loc[i,'estado']})")
        if st.button("Finalizar orden"):
            st.session_state['ordenes'][idx]['estado'] = "Finalizada"
            st.success("Orden finalizada")

# Inventario
with tabs[2]:
    st.header("Inventario")
    df_inv = pd.DataFrame(st.session_state['inventario'])
    st.dataframe(df_inv)

    with st.form("Actualizar inventario"):
        material = st.selectbox("Material", [item['material'] for item in st.session_state['inventario']])
        movimiento = st.selectbox("Movimiento", ["Entrada", "Salida"])
        cantidad = st.number_input("Cantidad", min_value=1, step=1)
        submit_inv = st.form_submit_button("Actualizar stock")
        if submit_inv:
            for item in st.session_state['inventario']:
                if item['material'] == material:
                    if movimiento == "Entrada":
                        item['stock'] += cantidad
                    else:
                        item['stock'] = max(0, item['stock'] - cantidad)
                    st.success(f"Stock de {material} actualizado")

# Incidencias
with tabs[3]:
    st.header("Incidencias y Paros de Línea")
    with st.form("Nueva incidencia"):
        orden = st.selectbox("Orden relacionada", [f"{i}-{o['producto']}" for i,o in enumerate(st.session_state['ordenes'])])
        descripcion = st.text_area("Descripción de la incidencia")
        responsable = st.text_input("Responsable de solución")
        submitted_inc = st.form_submit_button("Registrar Incidencia")
        if submitted_inc and descripcion and responsable:
            st.session_state['incidencias'].append({
                'orden': orden,
                'descripcion': descripcion,
                'responsable': responsable,
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'estado': "Abierta"
            })
            st.success("Incidencia registrada")

    df_inc = pd.DataFrame(st.session_state['incidencias'])
    if not df_inc.empty:
        st.dataframe(df_inc)
        idx = st.selectbox("Selecciona incidencia para cerrar", df_inc.index, format_func=lambda i: f"{df_inc.loc[i,'descripcion'][:30]} ({df_inc.loc[i,'estado']})")
        if st.button("Cerrar incidencia"):
            st.session_state['incidencias'][idx]['estado'] = "Cerrada"
            st.success("Incidencia cerrada")

# Reportes y Dashboard
with tabs[4]:
    st.header("Reportes e Indicadores")
    st.subheader("Órdenes por estado")
    df_ordenes = pd.DataFrame(st.session_state['ordenes'])
    if not df_ordenes.empty:
        st.bar_chart(df_ordenes['estado'].value_counts())
        st.subheader("Órdenes por responsable")
        st.bar_chart(df_ordenes['responsable'].value_counts())
    st.subheader("Stock de Inventario")
    df_inv = pd.DataFrame(st.session_state['inventario'])
    st.bar_chart(df_inv.set_index('material')['stock'])
    st.subheader("Incidencias abiertas/cerradas")
    df_inc = pd.DataFrame(st.session_state['incidencias'])
    if not df_inc.empty:
        st.bar_chart(df_inc['estado'].value_counts())