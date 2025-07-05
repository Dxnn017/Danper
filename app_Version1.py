import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import uuid
import random

# Configuración de la página
st.set_page_config(
    page_title="TPS Danper - Control de Calidad",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado estilo Danper
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #e53e3e 0%, #c53030 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .danper-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #e53e3e;
        margin-bottom: 1rem;
    }
    .sensor-reading {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .status-aprobado {
        background-color: #10b981;
        color: white;
        padding: 0.5rem;
        border-radius: 8px;
        text-align: center;
    }
    .status-rechazado {
        background-color: #ef4444;
        color: white;
        padding: 0.5rem;
        border-radius: 8px;
        text-align: center;
    }
    .status-pendiente {
        background-color: #f59e0b;
        color: white;
        padding: 0.5rem;
        border-radius: 8px;
        text-align: center;
    }
    .alert-box {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar base de datos TPS
@st.cache_resource
def init_tps_database():
    conn = sqlite3.connect('danper_tps_calidad.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Tabla de Productos Agroindustriales
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos_agro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_producto TEXT UNIQUE,
            nombre_producto TEXT,
            variedad TEXT,
            categoria TEXT,
            origen_campo TEXT,
            temporada TEXT,
            estado TEXT,
            fecha_registro DATE
        )
    ''')
    
    # Tabla de Lotes de Producción
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lotes_produccion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_lote TEXT UNIQUE,
            codigo_producto TEXT,
            fecha_cosecha DATE,
            cantidad_kg REAL,
            campo_origen TEXT,
            responsable_campo TEXT,
            estado_lote TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (codigo_producto) REFERENCES productos_agro (codigo_producto)
        )
    ''')
    
    # Tabla de Inspecciones Visuales (TPS Core)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inspecciones_visuales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_inspeccion TEXT UNIQUE,
            codigo_lote TEXT,
            fecha_inspeccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            inspector TEXT,
            color_evaluacion TEXT,
            forma_evaluacion TEXT,
            tamano_evaluacion TEXT,
            defectos_visuales TEXT,
            porcentaje_conformidad REAL,
            resultado_visual TEXT,
            observaciones TEXT,
            tiempo_procesamiento REAL,
            FOREIGN KEY (codigo_lote) REFERENCES lotes_produccion (codigo_lote)
        )
    ''')
    
    # Tabla de Lecturas de Sensores (TPS Core)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lecturas_sensores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_lectura TEXT UNIQUE,
            codigo_lote TEXT,
            timestamp_lectura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sensor_temperatura REAL,
            sensor_peso REAL,
            sensor_humedad REAL,
            sensor_ph REAL,
            sensor_brix REAL,
            estado_sensores TEXT,
            alerta_generada BOOLEAN DEFAULT 0,
            FOREIGN KEY (codigo_lote) REFERENCES lotes_produccion (codigo_lote)
        )
    ''')
    
    # Tabla de Pruebas Fisicoquímicas (TPS Core)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pruebas_fisicoquimicas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_prueba TEXT UNIQUE,
            codigo_lote TEXT,
            fecha_prueba TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            laboratorista TEXT,
            acidez_titulable REAL,
            solidos_solubles REAL,
            firmeza REAL,
            contenido_humedad REAL,
            residuos_pesticidas TEXT,
            microbiologia_resultado TEXT,
            resultado_fisicoquimico TEXT,
            certificacion_organica BOOLEAN DEFAULT 0,
            FOREIGN KEY (codigo_lote) REFERENCES lotes_produccion (codigo_lote)
        )
    ''')
    
    # Tabla de Compatibilidad de Envases (TPS Core)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compatibilidad_envases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_compatibilidad TEXT UNIQUE,
            codigo_lote TEXT,
            fecha_evaluacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tipo_envase TEXT,
            material_envase TEXT,
            capacidad_envase TEXT,
            prueba_hermeticidad BOOLEAN,
            prueba_resistencia BOOLEAN,
            compatibilidad_producto BOOLEAN,
            resultado_envase TEXT,
            observaciones_envase TEXT,
            FOREIGN KEY (codigo_lote) REFERENCES lotes_produccion (codigo_lote)
        )
    ''')
    
    # Tabla de Alertas Automáticas (TPS Core)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alertas_automaticas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_alerta TEXT UNIQUE,
            codigo_lote TEXT,
            tipo_alerta TEXT,
            nivel_criticidad TEXT,
            mensaje_alerta TEXT,
            parametro_afectado TEXT,
            valor_detectado REAL,
            valor_limite REAL,
            fecha_alerta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            estado_alerta TEXT,
            accion_tomada TEXT,
            FOREIGN KEY (codigo_lote) REFERENCES lotes_produccion (codigo_lote)
        )
    ''')
    
    # Tabla de Informes de Calidad Consolidados (TPS Core)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS informes_calidad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_informe TEXT UNIQUE,
            codigo_lote TEXT,
            fecha_informe TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resultado_inspeccion_visual TEXT,
            resultado_sensores TEXT,
            resultado_fisicoquimico TEXT,
            resultado_envases TEXT,
            decision_final TEXT,
            porcentaje_calidad_total REAL,
            certificaciones_obtenidas TEXT,
            destino_comercial TEXT,
            responsable_aprobacion TEXT,
            fecha_aprobacion TIMESTAMP,
            FOREIGN KEY (codigo_lote) REFERENCES lotes_produccion (codigo_lote)
        )
    ''')
    
    # Tabla de Trazabilidad Internacional
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trazabilidad_internacional (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_trazabilidad TEXT UNIQUE,
            codigo_lote TEXT,
            pais_destino TEXT,
            cliente_internacional TEXT,
            certificacion_requerida TEXT,
            numero_contenedor TEXT,
            fecha_embarque DATE,
            puerto_destino TEXT,
            documentos_exportacion TEXT,
            estado_envio TEXT,
            FOREIGN KEY (codigo_lote) REFERENCES lotes_produccion (codigo_lote)
        )
    ''')
    
    conn.commit()
    return conn

# Función para obtener conexión
def get_connection():
    return sqlite3.connect('danper_tps_calidad.db', check_same_thread=False)

# Funciones para generar códigos únicos
def generar_codigo_producto():
    return f"PROD-{datetime.datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

def generar_codigo_lote():
    return f"LT-{datetime.datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

def generar_codigo_inspeccion():
    return f"INS-{datetime.datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

def generar_codigo_sensor():
    return f"SEN-{datetime.datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

def generar_codigo_prueba():
    return f"LAB-{datetime.datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

# Función para simular lecturas de sensores en tiempo real
def simular_lectura_sensores():
    return {
        'temperatura': round(random.uniform(2.0, 8.0), 1),  # Temperatura de refrigeración
        'peso': round(random.uniform(15.0, 25.0), 2),       # Peso en kg
        'humedad': round(random.uniform(85.0, 95.0), 1),    # Humedad relativa
        'ph': round(random.uniform(6.0, 7.5), 2),           # pH
        'brix': round(random.uniform(8.0, 15.0), 1)         # Grados Brix
    }

# Función para insertar datos de ejemplo realistas
@st.cache_data
def insertar_datos_danper():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si ya hay datos
    cursor.execute("SELECT COUNT(*) FROM productos_agro")
    if cursor.fetchone()[0] == 0:
        
        # Productos agroindustriales de Danper
        productos_ejemplo = [
            ('PROD-ESP-001', 'Espárragos Verdes', 'UC-157', 'Hortalizas', 'Campo Norte Virú', '2024-A', 'Activo', date.today()),
            ('PROD-PAL-002', 'Paltas Hass', 'Hass Premium', 'Frutas', 'Campo Sur Chincha', '2024-A', 'Activo', date.today()),
            ('PROD-ARA-003', 'Arándanos Frescos', 'Biloxi', 'Berries', 'Campo Este Trujillo', '2024-A', 'Activo', date.today()),
            ('PROD-UVA-004', 'Uvas Red Globe', 'Red Globe Premium', 'Frutas', 'Campo Oeste Ica', '2024-A', 'Activo', date.today()),
            ('PROD-MAN-005', 'Mangos Kent', 'Kent Export', 'Frutas', 'Campo Central Piura', '2024-A', 'Activo', date.today()),
            ('PROD-ALC-006', 'Alcachofas', 'Imperial Star', 'Hortalizas', 'Campo Sur Chincha', '2024-A', 'Activo', date.today()),
            ('PROD-BRO-007', 'Brócoli', 'Marathon', 'Hortalizas', 'Campo Este Trujillo', '2024-A', 'Activo', date.today()),
            ('PROD-QUI-008', 'Quinua', 'Blanca Real', 'Granos', 'Campo Andino', '2024-A', 'Activo', date.today()),
            ('PROD-MAR-009', 'Maracuyá', 'Gigante Amarillo', 'Frutas', 'Campo Selva Central', '2024-A', 'Activo', date.today()),
            ('PROD-GRA-010', 'Granada', 'Wonderful', 'Frutas', 'Campo Sur Ica', '2024-A', 'Activo', date.today())
        ]
        cursor.executemany('''
            INSERT INTO productos_agro (codigo_producto, nombre_producto, variedad, categoria, origen_campo, temporada, estado, fecha_registro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', productos_ejemplo)
        
        # Lotes de producción
        lotes_ejemplo = [
            ('LT-ESP-20241201', 'PROD-ESP-001', date.today() - timedelta(days=3), 1500.0, 'Campo Norte Virú', 'Carlos Mendoza', 'EN_PROCESO'),
            ('LT-PAL-20241201', 'PROD-PAL-002', date.today() - timedelta(days=2), 2200.0, 'Campo Sur Chincha', 'Ana García', 'EN_PROCESO'),
            ('LT-ARA-20241201', 'PROD-ARA-003', date.today() - timedelta(days=1), 800.0, 'Campo Este Trujillo', 'Luis Rodríguez', 'EN_PROCESO'),
            ('LT-UVA-20241201', 'PROD-UVA-004', date.today(), 1800.0, 'Campo Oeste Ica', 'María López', 'NUEVO'),
            ('LT-MAN-20241201', 'PROD-MAN-005', date.today(), 2500.0, 'Campo Central Piura', 'José Fernández', 'NUEVO')
        ]
        
        cursor.executemany('''
            INSERT INTO lotes_produccion (codigo_lote, codigo_producto, fecha_cosecha, cantidad_kg, campo_origen, responsable_campo, estado_lote)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', lotes_ejemplo)
        
        # Inspecciones visuales
        inspecciones_ejemplo = [
            ('INS-20241201-001', 'LT-ESP-20241201', datetime.datetime.now() - timedelta(hours=2), 'Juan Pérez', 'Verde intenso', 'Recta uniforme', '18-22 cm', 'Ninguno significativo', 95.5, 'APROBADO', 'Excelente calidad visual', 2.5),
            ('INS-20241201-002', 'LT-PAL-20241201', datetime.datetime.now() - timedelta(hours=1), 'María García', 'Verde oscuro', 'Ovalada perfecta', '180-220g', 'Leves manchas <5%', 92.0, 'APROBADO', 'Calidad exportación', 3.2),
            ('INS-20241201-003', 'LT-ARA-20241201', datetime.datetime.now() - timedelta(minutes=30), 'Carlos López', 'Azul intenso', 'Redonda uniforme', '16-18mm', 'Ninguno', 98.0, 'APROBADO', 'Premium quality', 1.8)
        ]
        
        cursor.executemany('''
            INSERT INTO inspecciones_visuales (codigo_inspeccion, codigo_lote, fecha_inspeccion, inspector, color_evaluacion, forma_evaluacion, tamano_evaluacion, defectos_visuales, porcentaje_conformidad, resultado_visual, observaciones, tiempo_procesamiento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', inspecciones_ejemplo)
        
        # Lecturas de sensores
        for i, lote in enumerate(['LT-ESP-20241201', 'LT-PAL-20241201', 'LT-ARA-20241201']):
            for j in range(5):  # 5 lecturas por lote
                lectura = simular_lectura_sensores()
                cursor.execute('''
                    INSERT INTO lecturas_sensores (codigo_lectura, codigo_lote, sensor_temperatura, sensor_peso, sensor_humedad, sensor_ph, sensor_brix, estado_sensores, alerta_generada)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (f"SEN-{i+1}-{j+1}", lote, lectura['temperatura'], lectura['peso'], lectura['humedad'], lectura['ph'], lectura['brix'], 'OPERATIVO', 0))
        
        # Pruebas fisicoquímicas
        pruebas_ejemplo = [
            ('LAB-20241201-001', 'LT-ESP-20241201', datetime.datetime.now() - timedelta(hours=1), 'Dr. Ana Martín', 0.15, 6.2, 180.5, 92.3, 'No detectados', 'Negativo', 'APROBADO', 1),
            ('LAB-20241201-002', 'LT-PAL-20241201', datetime.datetime.now() - timedelta(minutes=45), 'Dr. Carlos Ruiz', 0.12, 23.8, 165.2, 78.5, 'Dentro límites', 'Negativo', 'APROBADO', 1),
            ('LAB-20241201-003', 'LT-ARA-20241201', datetime.datetime.now() - timedelta(minutes=30), 'Dra. Laura Vega', 0.08, 12.5, 195.8, 88.2, 'No detectados', 'Negativo', 'APROBADO', 1)
        ]
        
        cursor.executemany('''
            INSERT INTO pruebas_fisicoquimicas (codigo_prueba, codigo_lote, fecha_prueba, laboratorista, acidez_titulable, solidos_solubles, firmeza, contenido_humedad, residuos_pesticidas, microbiologia_resultado, resultado_fisicoquimico, certificacion_organica)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', pruebas_ejemplo)
        
        # Alertas automáticas (algunas de ejemplo)
        alertas_ejemplo = [
            ('ALT-20241201-001', 'LT-UVA-20241201', 'TEMPERATURA', 'MEDIA', 'Temperatura ligeramente elevada detectada', 'Temperatura', 8.5, 8.0, 'ACTIVA', 'Ajuste de refrigeración'),
            ('ALT-20241201-002', 'LT-MAN-20241201', 'HUMEDAD', 'BAJA', 'Humedad por debajo del rango óptimo', 'Humedad', 82.0, 85.0, 'RESUELTA', 'Incremento de humidificación')
        ]
        
        cursor.executemany('''
            INSERT INTO alertas_automaticas (codigo_alerta, codigo_lote, tipo_alerta, nivel_criticidad, mensaje_alerta, parametro_afectado, valor_detectado, valor_limite, estado_alerta, accion_tomada)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', alertas_ejemplo)
        
        # Informes de calidad consolidados
        informes_ejemplo = [
            ('INF-20241201-001', 'LT-ESP-20241201', datetime.datetime.now() - timedelta(minutes=15), 'APROBADO', 'NORMAL', 'APROBADO', 'APROBADO', 'APROBADO', 95.5, 'Global GAP, HACCP', 'Exportación USA', 'Ing. Roberto Silva', datetime.datetime.now()),
            ('INF-20241201-002', 'LT-PAL-20241201', datetime.datetime.now() - timedelta(minutes=10), 'APROBADO', 'NORMAL', 'APROBADO', 'APROBADO', 'APROBADO', 92.0, 'Organic, Fair Trade', 'Exportación Europa', 'Ing. Roberto Silva', datetime.datetime.now())
        ]
        
        cursor.executemany('''
            INSERT INTO informes_calidad (codigo_informe, codigo_lote, fecha_informe, resultado_inspeccion_visual, resultado_sensores, resultado_fisicoquimico, resultado_envases, decision_final, porcentaje_calidad_total, certificaciones_obtenidas, destino_comercial, responsable_aprobacion, fecha_aprobacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', informes_ejemplo)
    
    conn.commit()
    conn.close()

# Inicializar sistema
conn = init_tps_database()
insertar_datos_danper()

# Header principal estilo Danper
st.markdown("""
<div class="main-header">
    <h1>🌱 DANPER TRUJILLO S.A.C.</h1>
    <h2>Sistema TPS - Control de Calidad Agroindustrial</h2>
    <p><strong>Odoo 17 | PostgreSQL | Python + XML | Sensores IoT</strong></p>
    <p>Automatización de Inspecciones • Trazabilidad Internacional • Estándares de Exportación</p>
</div>
""", unsafe_allow_html=True)

# Sidebar para navegación
st.sidebar.markdown("""
<div style='background: linear-gradient(90deg, #e53e3e 0%, #c53030 100%); padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 1rem;'>
    <h2 style='color: white; margin: 0;'>🌱 DANPER</h2>
    <p style='color: white; margin: 0; font-size: 0.9rem;'>TPS Control de Calidad</p>
</div>
""", unsafe_allow_html=True)

modulo = st.sidebar.selectbox(
    "🎯 Módulos TPS:",
    ["🏠 Dashboard TPS", "📦 Gestión de Productos", "👁️ Inspecciones Visuales", 
     "📡 Lecturas de Sensores", "🧪 Pruebas Fisicoquímicas", "📦 Compatibilidad Envases",
     "🚨 Alertas Automáticas", "📊 Informes Consolidados", "🌍 Trazabilidad Internacional"]
)

# DASHBOARD TPS PRINCIPAL
if modulo == "🏠 Dashboard TPS":
    st.title("🏠 Dashboard TPS - Control de Calidad en Tiempo Real")
    
    # Métricas TPS en tiempo real
    col1, col2, col3, col4 = st.columns(4)
    
    conn = get_connection()
    
    # Lotes en proceso
    lotes_proceso = pd.read_sql_query("SELECT COUNT(*) as total FROM lotes_produccion WHERE estado_lote = 'EN_PROCESO'", conn)
    
    # Inspecciones hoy
    inspecciones_hoy = pd.read_sql_query("SELECT COUNT(*) as total FROM inspecciones_visuales WHERE DATE(fecha_inspeccion) = DATE('now')", conn)
    
    # Alertas activas
    alertas_activas = pd.read_sql_query("SELECT COUNT(*) as total FROM alertas_automaticas WHERE estado_alerta = 'ACTIVA'", conn)
    
    # Lotes aprobados hoy
    aprobados_hoy = pd.read_sql_query("SELECT COUNT(*) as total FROM informes_calidad WHERE DATE(fecha_informe) = DATE('now') AND decision_final = 'APROBADO'", conn)
    
    with col1:
        st.metric("🔄 Lotes en Proceso", lotes_proceso['total'].iloc[0])
    
    with col2:
        st.metric("👁️ Inspecciones Hoy", inspecciones_hoy['total'].iloc[0])
    
    with col3:
        alertas_valor = alertas_activas['total'].iloc[0]
        st.metric("🚨 Alertas Activas", alertas_valor, delta="Crítico" if alertas_valor > 0 else "Normal")
    
    with col4:
        st.metric("✅ Lotes Aprobados Hoy", aprobados_hoy['total'].iloc[0])
    
    # Lecturas de sensores en tiempo real
    st.markdown("---")
    st.subheader("📡 Lecturas de Sensores en Tiempo Real")
    
    col1, col2, col3 = st.columns(3)
    
    # Simular lecturas actuales
    lectura_actual = simular_lectura_sensores()
    
    with col1:
        st.markdown(f"""
        <div class="sensor-reading">
            <h3>🌡️ Temperatura</h3>
            <h2>{lectura_actual['temperatura']}°C</h2>
            <p>Rango óptimo: 2-8°C</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="sensor-reading">
            <h3>⚖️ Peso Promedio</h3>
            <h2>{lectura_actual['peso']} kg</h2>
            <p>Estándar exportación</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="sensor-reading">
            <h3>💧 Humedad</h3>
            <h2>{lectura_actual['humedad']}%</h2>
            <p>Rango óptimo: 85-95%</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Gráficos del TPS
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Resultados de Calidad por Producto")
        calidad_producto = pd.read_sql_query("""
            SELECT pa.nombre_producto, 
                   COUNT(CASE WHEN ic.decision_final = 'APROBADO' THEN 1 END) as aprobados,
                   COUNT(CASE WHEN ic.decision_final = 'RECHAZADO' THEN 1 END) as rechazados
            FROM informes_calidad ic
            JOIN lotes_produccion lp ON ic.codigo_lote = lp.codigo_lote
            JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
            GROUP BY pa.nombre_producto
        """, conn)
        
        if not calidad_producto.empty:
            fig = px.bar(calidad_producto, x='nombre_producto', y=['aprobados', 'rechazados'],
                        title='Resultados de Calidad por Producto',
                        color_discrete_map={'aprobados': '#10b981', 'rechazados': '#ef4444'})
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("⏱️ Tiempo de Procesamiento TPS")
        tiempo_procesamiento = pd.read_sql_query("""
            SELECT inspector, AVG(tiempo_procesamiento) as tiempo_promedio
            FROM inspecciones_visuales
            GROUP BY inspector
        """, conn)
        
        if not tiempo_procesamiento.empty:
            fig2 = px.bar(tiempo_procesamiento, x='inspector', y='tiempo_promedio',
                         title='Tiempo Promedio de Inspección (minutos)')
            st.plotly_chart(fig2, use_container_width=True)
    
    conn.close()
    
# Módulo de Gestión de Productos
elif modulo == "📦 Gestión de Productos":
    st.title("📦 Gestión de Productos Agroindustriales")
    
    tab1, tab2, tab3 = st.tabs(["➕ Nuevo Producto", "📋 Lista de Productos", "📊 Análisis"])
    
    with tab1:
        st.subheader("➕ Registrar Nuevo Producto")
        
        with st.form("form_producto"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre_producto = st.text_input("Nombre del Producto", placeholder="Ej: Espárragos Verdes")
                variedad = st.text_input("Variedad", placeholder="Ej: UC-157")
                categoria = st.selectbox("Categoría", ["Hortalizas", "Frutas", "Berries", "Legumbres", "Granos"])
            
            with col2:
                origen_campo = st.selectbox("Origen/Campo", ["Virú", "Chincha", "Trujillo", "Ica", "Piura", "Lambayeque"])
                temporada = st.text_input("Temporada", placeholder="Ej: 2024-A")
                estado = st.selectbox("Estado", ["Activo", "Inactivo", "En desarrollo"])
            
            submitted = st.form_submit_button("💾 Guardar Producto", use_container_width=True)
            
            if submitted:
                if nombre_producto and variedad:
                    codigo_producto = generar_codigo_producto()
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute('''
                            INSERT INTO productos_agro (codigo_producto, nombre_producto, variedad, categoria, origen_campo, temporada, estado, fecha_registro)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (codigo_producto, nombre_producto, variedad, categoria, origen_campo, temporada, estado, date.today()))
                        conn.commit()
                        st.success(f"✅ Producto registrado: {codigo_producto}")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("❌ Complete los campos obligatorios")
    
    with tab2:
        st.subheader("📋 Lista de Productos Agroindustriales")
        
        conn = get_connection()
        productos_df = pd.read_sql_query("SELECT * FROM productos_agro ORDER BY fecha_registro DESC", conn)
        conn.close()
        
        if not productos_df.empty:
            # Función para editar producto
            def editar_producto(row):
                with st.form(f"form_editar_{row['id']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        nuevo_nombre = st.text_input("Nombre", value=row['nombre_producto'])
                        nueva_variedad = st.text_input("Variedad", value=row['variedad'])
                        nueva_categoria = st.selectbox("Categoría", 
                            ["Hortalizas", "Frutas", "Berries", "Legumbres", "Granos"],
                            index=["Hortalizas", "Frutas", "Berries", "Legumbres", "Granos"].index(row['categoria']))
                    
                    with col2:
                        nuevo_origen = st.selectbox("Origen", 
                            ["Virú", "Chincha", "Trujillo", "Ica", "Piura", "Lambayeque"],
                            index=["Virú", "Chincha", "Trujillo", "Ica", "Piura", "Lambayeque"].index(row['origen_campo']))
                        nueva_temporada = st.text_input("Temporada", value=row['temporada'])
                        nuevo_estado = st.selectbox("Estado", 
                            ["Activo", "Inactivo", "En desarrollo"],
                            index=["Activo", "Inactivo", "En desarrollo"].index(row['estado']))
                    
                    if st.form_submit_button("💾 Guardar Cambios"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        try:
                            cursor.execute('''
                                UPDATE productos_agro 
                                SET nombre_producto=?, variedad=?, categoria=?, origen_campo=?, temporada=?, estado=?
                                WHERE id=?
                            ''', (nuevo_nombre, nueva_variedad, nueva_categoria, nuevo_origen, nueva_temporada, nuevo_estado, row['id']))
                            conn.commit()
                            st.success("✅ Producto actualizado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                        finally:
                            conn.close()
            
            # Mostrar tabla con opciones de edición/eliminación
            for _, row in productos_df.iterrows():
                with st.expander(f"{row['nombre_producto']} ({row['codigo_producto']})"):
                    editar_producto(row)
                    
                    if st.button(f"❌ Eliminar {row['codigo_producto']}", key=f"eliminar_{row['id']}"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        try:
                            # Verificar si hay lotes asociados
                            cursor.execute("SELECT COUNT(*) FROM lotes_produccion WHERE codigo_producto=?", (row['codigo_producto'],))
                            if cursor.fetchone()[0] == 0:
                                cursor.execute("DELETE FROM productos_agro WHERE id=?", (row['id'],))
                                conn.commit()
                                st.success("✅ Producto eliminado")
                                st.rerun()
                            else:
                                st.error("❌ No se puede eliminar: Hay lotes asociados a este producto")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                        finally:
                            conn.close()
        else:
            st.info("📦 No hay productos registrados")
    
    with tab3:
        st.subheader("📊 Análisis de Productos")
        
        conn = get_connection()
        productos_df = pd.read_sql_query("SELECT * FROM productos_agro", conn)
        lotes_df = pd.read_sql_query("SELECT * FROM lotes_produccion", conn)
        conn.close()
        
        if not productos_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribución por categoría
                categoria_dist = productos_df['categoria'].value_counts().reset_index()
                categoria_dist.columns = ['categoria', 'cantidad']
                
                fig = px.pie(categoria_dist, values='cantidad', names='categoria',
                           title='Distribución de Productos por Categoría',
                           color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Estado de productos
                estado_dist = productos_df['estado'].value_counts().reset_index()
                estado_dist.columns = ['estado', 'cantidad']
                
                fig2 = px.bar(estado_dist, x='estado', y='cantidad',
                            title='Estado de los Productos',
                            color='estado',
                            color_discrete_map={'Activo': '#10b981', 'Inactivo': '#ef4444', 'En desarrollo': '#f59e0b'})
                st.plotly_chart(fig2, use_container_width=True)
            
            # Relación productos-lotes (si hay datos)
            if not lotes_df.empty:
                productos_lotes = pd.merge(productos_df, lotes_df, left_on='codigo_producto', right_on='codigo_producto', how='left')
                productos_lotes_count = productos_lotes.groupby('nombre_producto')['codigo_lote'].count().reset_index()
                
                fig3 = px.bar(productos_lotes_count, x='nombre_producto', y='codigo_lote',
                            title='Número de Lotes por Producto',
                            labels={'codigo_lote': 'N° de Lotes', 'nombre_producto': 'Producto'})
                st.plotly_chart(fig3, use_container_width=True)
                
# MÓDULO DE INSPECCIONES VISUALES
elif modulo == "👁️ Inspecciones Visuales":
    st.title("👁️ Inspecciones Visuales - TPS en Tiempo Real")
    
    tab1, tab2, tab3 = st.tabs(["📝 Nueva Inspección", "📋 Historial", "📊 Análisis"])
    
    with tab1:
        st.subheader("📝 Registrar Inspección Visual")
        
        with st.form("form_inspeccion"):
            col1, col2 = st.columns(2)
            
            with col1:
                conn = get_connection()
                lotes = pd.read_sql_query("""
                    SELECT lp.codigo_lote, pa.nombre_producto, lp.cantidad_kg
                    FROM lotes_produccion lp
                    JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
                    WHERE lp.estado_lote IN ('NUEVO', 'EN_PROCESO')
                """, conn)
                conn.close()
                
                if not lotes.empty:
                    lote_seleccionado = st.selectbox("Lote a Inspeccionar", 
                        options=lotes['codigo_lote'].tolist(),
                        format_func=lambda x: f"{x} - {lotes[lotes['codigo_lote']==x]['nombre_producto'].iloc[0]}")
                
                inspector = st.text_input("Inspector", placeholder="Nombre del inspector")
                color_evaluacion = st.selectbox("Evaluación de Color", 
                    ["Excelente", "Bueno", "Regular", "Deficiente"])
                forma_evaluacion = st.selectbox("Evaluación de Forma", 
                    ["Uniforme", "Ligeramente irregular", "Irregular", "Deforme"])
            
            with col2:
                tamano_evaluacion = st.text_input("Evaluación de Tamaño", placeholder="Ej: 18-22 cm")
                defectos_visuales = st.text_area("Defectos Visuales Detectados", 
                    placeholder="Describir defectos encontrados...")
                porcentaje_conformidad = st.slider("Porcentaje de Conformidad", 0.0, 100.0, 95.0, 0.1)
                observaciones = st.text_area("Observaciones", 
                    placeholder="Comentarios adicionales...")
            
            # Simulación de tiempo de procesamiento
            tiempo_procesamiento = st.number_input("Tiempo de Procesamiento (minutos)", 
                min_value=0.1, value=2.5, step=0.1)
            
            submitted = st.form_submit_button("👁️ Registrar Inspección", use_container_width=True)
            
            if submitted:
                if lote_seleccionado and inspector:
                    codigo_inspeccion = generar_codigo_inspeccion()
                    resultado_visual = "APROBADO" if porcentaje_conformidad >= 90 else "RECHAZADO" if porcentaje_conformidad < 70 else "OBSERVADO"
                    
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute('''
                            INSERT INTO inspecciones_visuales (codigo_inspeccion, codigo_lote, inspector, color_evaluacion, forma_evaluacion, tamano_evaluacion, defectos_visuales, porcentaje_conformidad, resultado_visual, observaciones, tiempo_procesamiento)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (codigo_inspeccion, lote_seleccionado, inspector, color_evaluacion, forma_evaluacion, tamano_evaluacion, defectos_visuales, porcentaje_conformidad, resultado_visual, observaciones, tiempo_procesamiento))
                        conn.commit()
                        st.success(f"✅ Inspección registrada: {codigo_inspeccion}")
                        st.balloons()
                        
                        # Mostrar resultado
                        if resultado_visual == "APROBADO":
                            st.markdown(f'<div class="status-aprobado">✅ LOTE APROBADO - {porcentaje_conformidad}% conformidad</div>', unsafe_allow_html=True)
                        elif resultado_visual == "RECHAZADO":
                            st.markdown(f'<div class="status-rechazado">❌ LOTE RECHAZADO - {porcentaje_conformidad}% conformidad</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="status-pendiente">⚠️ LOTE EN OBSERVACIÓN - {porcentaje_conformidad}% conformidad</div>', unsafe_allow_html=True)
                            
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("❌ Complete los campos obligatorios")
    
    with tab2:
        st.subheader("📋 Historial de Inspecciones")
        
        conn = get_connection()
        inspecciones_df = pd.read_sql_query("""
            SELECT iv.*, pa.nombre_producto, lp.cantidad_kg
            FROM inspecciones_visuales iv
            JOIN lotes_produccion lp ON iv.codigo_lote = lp.codigo_lote
            JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
            ORDER BY iv.fecha_inspeccion DESC
        """, conn)
        conn.close()
        
        if not inspecciones_df.empty:
            st.dataframe(inspecciones_df, use_container_width=True, height=400)
            
            # Métricas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📋 Total Inspecciones", len(inspecciones_df))
            with col2:
                aprobadas = len(inspecciones_df[inspecciones_df['resultado_visual'] == 'APROBADO'])
                st.metric("✅ Aprobadas", aprobadas)
            with col3:
                tiempo_promedio = inspecciones_df['tiempo_procesamiento'].mean()
                st.metric("⏱️ Tiempo Promedio", f"{tiempo_promedio:.1f} min")
            with col4:
                conformidad_promedio = inspecciones_df['porcentaje_conformidad'].mean()
                st.metric("📊 Conformidad Promedio", f"{conformidad_promedio:.1f}%")
        else:
            st.info("👁️ No hay inspecciones registradas")
    
    with tab3:
        st.subheader("📊 Análisis de Inspecciones Visuales")
        
        conn = get_connection()
        inspecciones_df = pd.read_sql_query("""
            SELECT iv.*, pa.nombre_producto, pa.categoria
            FROM inspecciones_visuales iv
            JOIN lotes_produccion lp ON iv.codigo_lote = lp.codigo_lote
            JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
        """, conn)
        conn.close()
        
        if not inspecciones_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribución de resultados
                resultado_dist = inspecciones_df['resultado_visual'].value_counts().reset_index()
                resultado_dist.columns = ['resultado', 'cantidad']
                
                fig = px.pie(resultado_dist, values='cantidad', names='resultado',
                           title='Distribución de Resultados de Inspección',
                           color_discrete_map={'APROBADO': '#10b981', 'RECHAZADO': '#ef4444', 'OBSERVADO': '#f59e0b'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Conformidad por producto
                conformidad_producto = inspecciones_df.groupby('nombre_producto')['porcentaje_conformidad'].mean().reset_index()
                
                fig2 = px.bar(conformidad_producto, x='nombre_producto', y='porcentaje_conformidad',
                            title='Conformidad Promedio por Producto (%)')
                st.plotly_chart(fig2, use_container_width=True)

# MÓDULO DE LECTURAS DE SENSORES
elif modulo == "📡 Lecturas de Sensores":
    st.title("📡 Lecturas de Sensores IoT - TPS en Tiempo Real")
    
    tab1, tab2, tab3 = st.tabs(["📊 Monitoreo Actual", "📈 Histórico", "⚙️ Configuración"])
    
    with tab1:
        st.subheader("📊 Monitoreo de Sensores en Tiempo Real")
        
        # Botón para simular nueva lectura
        if st.button("🔄 Actualizar Lecturas de Sensores"):
            st.rerun()
        
        # Lecturas actuales simuladas
        col1, col2, col3 = st.columns(3)
        
        lectura_actual = simular_lectura_sensores()
        
        with col1:
            st.markdown("### 🌡️ Sensor de Temperatura")
            temp_status = "Normal" if 2.0 <= lectura_actual['temperatura'] <= 8.0 else "Alerta"
            st.metric("Temperatura Actual", f"{lectura_actual['temperatura']}°C", 
                     delta=f"Estado: {temp_status}")
            
            st.markdown("### ⚖️ Sensor de Peso")
            st.metric("Peso Promedio", f"{lectura_actual['peso']} kg")
        
        with col2:
            st.markdown("### 💧 Sensor de Humedad")
            hum_status = "Normal" if 85.0 <= lectura_actual['humedad'] <= 95.0 else "Alerta"
            st.metric("Humedad Relativa", f"{lectura_actual['humedad']}%", 
                     delta=f"Estado: {hum_status}")
            
            st.markdown("### 🧪 Sensor de pH")
            ph_status = "Normal" if 6.0 <= lectura_actual['ph'] <= 7.5 else "Alerta"
            st.metric("Nivel de pH", f"{lectura_actual['ph']}", 
                     delta=f"Estado: {ph_status}")
        
        with col3:
            st.markdown("### 🍯 Sensor de Brix")
            st.metric("Grados Brix", f"{lectura_actual['brix']}°")
            
            # Registrar nueva lectura
            with st.form("form_sensor"):
                conn = get_connection()
                lotes = pd.read_sql_query("SELECT codigo_lote FROM lotes_produccion WHERE estado_lote IN ('NUEVO', 'EN_PROCESO')", conn)
                conn.close()
                
                if not lotes.empty:
                    lote_sensor = st.selectbox("Lote para Registro", lotes['codigo_lote'].tolist())
                    
                    if st.form_submit_button("📡 Registrar Lectura"):
                        codigo_lectura = generar_codigo_sensor()
                        conn = get_connection()
                        cursor = conn.cursor()
                        try:
                            cursor.execute('''
                                INSERT INTO lecturas_sensores (codigo_lectura, codigo_lote, sensor_temperatura, sensor_peso, sensor_humedad, sensor_ph, sensor_brix, estado_sensores, alerta_generada)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (codigo_lectura, lote_sensor, lectura_actual['temperatura'], lectura_actual['peso'], lectura_actual['humedad'], lectura_actual['ph'], lectura_actual['brix'], 'OPERATIVO', 0))
                            conn.commit()
                            st.success(f"✅ Lectura registrada: {codigo_lectura}")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                        finally:
                            conn.close()
    
    with tab2:
        st.subheader("📈 Histórico de Sensores")
        
        conn = get_connection()
        sensores_df = pd.read_sql_query("""
            SELECT ls.*, pa.nombre_producto
            FROM lecturas_sensores ls
            JOIN lotes_produccion lp ON ls.codigo_lote = lp.codigo_lote
            JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
            ORDER BY ls.timestamp_lectura DESC
        """, conn)
        conn.close()
        
        if not sensores_df.empty:
            st.dataframe(sensores_df, use_container_width=True, height=400)
            
            # Gráficos de tendencias
            col1, col2 = st.columns(2)
            
            with col1:
                # Tendencia de temperatura
                sensores_df['timestamp_lectura'] = pd.to_datetime(sensores_df['timestamp_lectura'])
                fig = px.line(sensores_df.tail(20), x='timestamp_lectura', y='sensor_temperatura',
                            title='Tendencia de Temperatura (Últimas 20 lecturas)')
                fig.add_hline(y=2.0, line_dash="dash", line_color="blue", annotation_text="Mín")
                fig.add_hline(y=8.0, line_dash="dash", line_color="red", annotation_text="Máx")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Tendencia de humedad
                fig2 = px.line(sensores_df.tail(20), x='timestamp_lectura', y='sensor_humedad',
                             title='Tendencia de Humedad (Últimas 20 lecturas)')
                fig2.add_hline(y=85.0, line_dash="dash", line_color="blue", annotation_text="Mín")
                fig2.add_hline(y=95.0, line_dash="dash", line_color="red", annotation_text="Máx")
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("📡 No hay lecturas de sensores registradas")
    
    with tab3:
        st.subheader("⚙️ Configuración de Sensores")
        
        st.markdown("### 🎛️ Parámetros de Sensores")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🌡️ Sensor de Temperatura**")
            temp_min = st.number_input("Temperatura Mínima (°C)", value=2.0)
            temp_max = st.number_input("Temperatura Máxima (°C)", value=8.0)
            
            st.markdown("**💧 Sensor de Humedad**")
            hum_min = st.number_input("Humedad Mínima (%)", value=85.0)
            hum_max = st.number_input("Humedad Máxima (%)", value=95.0)
        
        with col2:
            st.markdown("**🧪 Sensor de pH**")
            ph_min = st.number_input("pH Mínimo", value=6.0)
            ph_max = st.number_input("pH Máximo", value=7.5)
            
            st.markdown("**⚖️ Sensor de Peso**")
            peso_tolerancia = st.number_input("Tolerancia de Peso (%)", value=5.0)
        
        if st.button("💾 Guardar Configuración"):
            st.success("✅ Configuración de sensores actualizada")

# MÓDULO DE PRUEBAS FISICOQUÍMICAS
elif modulo == "🧪 Pruebas Fisicoquímicas":
    st.title("🧪 Pruebas Fisicoquímicas - Laboratorio TPS")
    
    tab1, tab2, tab3 = st.tabs(["🔬 Nueva Prueba", "📋 Resultados", "📊 Análisis"])
    
    with tab1:
        st.subheader("🔬 Registrar Prueba Fisicoquímica")
        
        with st.form("form_prueba"):
            col1, col2 = st.columns(2)
            
            with col1:
                conn = get_connection()
                lotes = pd.read_sql_query("""
                    SELECT lp.codigo_lote, pa.nombre_producto
                    FROM lotes_produccion lp
                    JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
                    WHERE lp.estado_lote IN ('NUEVO', 'EN_PROCESO')
                """, conn)
                conn.close()
                
                if not lotes.empty:
                    lote_seleccionado = st.selectbox("Lote para Análisis", 
                        options=lotes['codigo_lote'].tolist(),
                        format_func=lambda x: f"{x} - {lotes[lotes['codigo_lote']==x]['nombre_producto'].iloc[0]}")
                
                laboratorista = st.text_input("Laboratorista", placeholder="Dr./Dra. Nombre")
                acidez_titulable = st.number_input("Acidez Titulable (%)", min_value=0.0, value=0.15, step=0.01)
                solidos_solubles = st.number_input("Sólidos Solubles (°Brix)", min_value=0.0, value=12.0, step=0.1)
            
            with col2:
                firmeza = st.number_input("Firmeza (g/mm)", min_value=0.0, value=180.0, step=0.1)
                contenido_humedad = st.number_input("Contenido de Humedad (%)", min_value=0.0, value=85.0, step=0.1)
                residuos_pesticidas = st.selectbox("Residuos de Pesticidas", 
                    ["No detectados", "Dentro de límites", "Excede límites"])
                microbiologia_resultado = st.selectbox("Resultado Microbiológico", 
                    ["Negativo", "Positivo", "En proceso"])
                certificacion_organica = st.checkbox("Certificación Orgánica")
            
            submitted = st.form_submit_button("🧪 Registrar Prueba", use_container_width=True)
            
            if submitted:
                if lote_seleccionado and laboratorista:
                    codigo_prueba = generar_codigo_prueba()
                    
                    # Determinar resultado basado en parámetros
                    resultado_fisicoquimico = "APROBADO"
                    if residuos_pesticidas == "Excede límites" or microbiologia_resultado == "Positivo":
                        resultado_fisicoquimico = "RECHAZADO"
                    elif microbiologia_resultado == "En proceso":
                        resultado_fisicoquimico = "PENDIENTE"
                    
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute('''
                            INSERT INTO pruebas_fisicoquimicas (codigo_prueba, codigo_lote, laboratorista, acidez_titulable, solidos_solubles, firmeza, contenido_humedad, residuos_pesticidas, microbiologia_resultado, resultado_fisicoquimico, certificacion_organica)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (codigo_prueba, lote_seleccionado, laboratorista, acidez_titulable, solidos_solubles, firmeza, contenido_humedad, residuos_pesticidas, microbiologia_resultado, resultado_fisicoquimico, certificacion_organica))
                        conn.commit()
                        st.success(f"✅ Prueba registrada: {codigo_prueba}")
                        
                        # Mostrar resultado
                        if resultado_fisicoquimico == "APROBADO":
                            st.markdown('<div class="status-aprobado">✅ PRUEBA APROBADA</div>', unsafe_allow_html=True)
                        elif resultado_fisicoquimico == "RECHAZADO":
                            st.markdown('<div class="status-rechazado">❌ PRUEBA RECHAZADA</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="status-pendiente">⏳ PRUEBA PENDIENTE</div>', unsafe_allow_html=True)
                            
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("❌ Complete los campos obligatorios")
    
    with tab2:
        st.subheader("📋 Resultados de Laboratorio")
        
        conn = get_connection()
        pruebas_df = pd.read_sql_query("""
            SELECT pf.*, pa.nombre_producto, lp.cantidad_kg
            FROM pruebas_fisicoquimicas pf
            JOIN lotes_produccion lp ON pf.codigo_lote = lp.codigo_lote
            JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
            ORDER BY pf.fecha_prueba DESC
        """, conn)
        conn.close()
        
        if not pruebas_df.empty:
            st.dataframe(pruebas_df, use_container_width=True, height=400)
            
            # Métricas de laboratorio
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🧪 Total Pruebas", len(pruebas_df))
            with col2:
                aprobadas = len(pruebas_df[pruebas_df['resultado_fisicoquimico'] == 'APROBADO'])
                st.metric("✅ Aprobadas", aprobadas)
            with col3:
                organicas = len(pruebas_df[pruebas_df['certificacion_organica'] == 1])
                st.metric("🌱 Certificación Orgánica", organicas)
            with col4:
                brix_promedio = pruebas_df['solidos_solubles'].mean()
                st.metric("📊 Brix Promedio", f"{brix_promedio:.1f}°")
        else:
            st.info("🧪 No hay pruebas fisicoquímicas registradas")
    
    with tab3:
        st.subheader("📊 Análisis de Laboratorio")
        
        conn = get_connection()
        pruebas_df = pd.read_sql_query("""
            SELECT pf.*, pa.nombre_producto, pa.categoria
            FROM pruebas_fisicoquimicas pf
            JOIN lotes_produccion lp ON pf.codigo_lote = lp.codigo_lote
            JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
        """, conn)
        conn.close()
        
        if not pruebas_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribución de resultados
                resultado_dist = pruebas_df['resultado_fisicoquimico'].value_counts().reset_index()
                resultado_dist.columns = ['resultado', 'cantidad']
                
                fig = px.pie(resultado_dist, values='cantidad', names='resultado',
                           title='Distribución de Resultados Fisicoquímicos',
                           color_discrete_map={'APROBADO': '#10b981', 'RECHAZADO': '#ef4444', 'PENDIENTE': '#f59e0b'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Análisis de Brix por producto
                brix_producto = pruebas_df.groupby('nombre_producto')['solidos_solubles'].mean().reset_index()
                
                fig2 = px.bar(brix_producto, x='nombre_producto', y='solidos_solubles',
                            title='Grados Brix Promedio por Producto')
                st.plotly_chart(fig2, use_container_width=True)

# MÓDULO DE COMPATIBILIDAD DE ENVASES
elif modulo == "📦 Compatibilidad Envases":
    st.title("📦 Compatibilidad de Envases - TPS")
    
    tab1, tab2, tab3 = st.tabs(["🧪 Nueva Prueba", "📋 Historial", "📊 Análisis"])
    
    with tab1:
        st.subheader("🧪 Evaluar Compatibilidad de Envases")
        
        with st.form("form_envase"):
            col1, col2 = st.columns(2)
            
            with col1:
                conn = get_connection()
                lotes = pd.read_sql_query("""
                    SELECT lp.codigo_lote, pa.nombre_producto
                    FROM lotes_produccion lp
                    JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
                    WHERE lp.estado_lote IN ('NUEVO', 'EN_PROCESO')
                """, conn)
                conn.close()
                
                if not lotes.empty:
                    lote_seleccionado = st.selectbox("Lote para Evaluación", 
                        options=lotes['codigo_lote'].tolist(),
                        format_func=lambda x: f"{x} - {lotes[lotes['codigo_lote']==x]['nombre_producto'].iloc[0]}")
                
                tipo_envase = st.selectbox("Tipo de Envase", 
                    ["Caja de cartón", "Bandeja PET", "Clamshell", "Bolsa plástica", "Caja de madera", "Envase al vacío"])
                material_envase = st.selectbox("Material del Envase", 
                    ["Cartón corrugado", "PET reciclado", "PET transparente", "Plástico PP", "Madera", "Vidrio"])
                capacidad_envase = st.text_input("Capacidad del Envase", placeholder="Ej: 5 kg, 500 g")
            
            with col2:
                prueba_hermeticidad = st.checkbox("Prueba de Hermeticidad Aprobada")
                prueba_resistencia = st.checkbox("Prueba de Resistencia Aprobada")
                compatibilidad_producto = st.checkbox("Compatibilidad con Producto Verificada")
                observaciones = st.text_area("Observaciones", 
                    placeholder="Detalles sobre la compatibilidad...")
            
            submitted = st.form_submit_button("📦 Registrar Evaluación", use_container_width=True)
            
            if submitted:
                if lote_seleccionado and tipo_envase:
                    codigo_compatibilidad = generar_codigo_envase()
                    
                    # Determinar resultado basado en pruebas
                    resultado_envase = "APROBADO" if prueba_hermeticidad and prueba_resistencia and compatibilidad_producto else "RECHAZADO"
                    
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute('''
                            INSERT INTO compatibilidad_envases (codigo_compatibilidad, codigo_lote, tipo_envase, material_envase, capacidad_envase, prueba_hermeticidad, prueba_resistencia, compatibilidad_producto, resultado_envase, observaciones_envase)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (codigo_compatibilidad, lote_seleccionado, tipo_envase, material_envase, capacidad_envase, prueba_hermeticidad, prueba_resistencia, compatibilidad_producto, resultado_envase, observaciones))
                        conn.commit()
                        st.success(f"✅ Evaluación registrada: {codigo_compatibilidad}")
                        
                        # Mostrar resultado
                        if resultado_envase == "APROBADO":
                            st.markdown('<div class="status-aprobado">✅ ENVASE APROBADO</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="status-rechazado">❌ ENVASE RECHAZADO</div>', unsafe_allow_html=True)
                            
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("❌ Complete los campos obligatorios")
    
    with tab2:
        st.subheader("📋 Historial de Evaluaciones")
        
        conn = get_connection()
        envases_df = pd.read_sql_query("""
            SELECT ce.*, pa.nombre_producto, lp.cantidad_kg
            FROM compatibilidad_envases ce
            JOIN lotes_produccion lp ON ce.codigo_lote = lp.codigo_lote
            JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
            ORDER BY ce.fecha_evaluacion DESC
        """, conn)
        conn.close()
        
        if not envases_df.empty:
            st.dataframe(envases_df, use_container_width=True, height=400)
            
            # Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📦 Total Evaluaciones", len(envases_df))
            with col2:
                aprobados = len(envases_df[envases_df['resultado_envase'] == 'APROBADO'])
                st.metric("✅ Envases Aprobados", aprobados)
            with col3:
                materiales_unicos = envases_df['material_envase'].nunique()
                st.metric("🔄 Materiales Diferentes", materiales_unicos)
        else:
            st.info("📦 No hay evaluaciones de envases registradas")
    
    with tab3:
        st.subheader("📊 Análisis de Compatibilidad")
        
        conn = get_connection()
        envases_df = pd.read_sql_query("""
            SELECT ce.*, pa.nombre_producto, pa.categoria
            FROM compatibilidad_envases ce
            JOIN lotes_produccion lp ON ce.codigo_lote = lp.codigo_lote
            JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
        """, conn)
        conn.close()
        
        if not envases_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribución de resultados
                resultado_dist = envases_df['resultado_envase'].value_counts().reset_index()
                resultado_dist.columns = ['resultado', 'cantidad']
                
                fig = px.pie(resultado_dist, values='cantidad', names='resultado',
                           title='Distribución de Resultados de Envases',
                           color_discrete_map={'APROBADO': '#10b981', 'RECHAZADO': '#ef4444'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Materiales más utilizados
                material_dist = envases_df['material_envase'].value_counts().reset_index()
                material_dist.columns = ['material', 'cantidad']
                
                fig2 = px.bar(material_dist, x='material', y='cantidad',
                            title='Materiales de Envases más Utilizados',
                            color='material')
                st.plotly_chart(fig2, use_container_width=True)
            
            # Compatibilidad por producto
            compatibilidad_producto = envases_df.groupby('nombre_producto')['resultado_envase'].apply(lambda x: (x == 'APROBADO').mean() * 100).reset_index()
            compatibilidad_producto.columns = ['producto', 'porcentaje_aprobado']
            
            fig3 = px.bar(compatibilidad_producto, x='producto', y='porcentaje_aprobado',
                        title='Porcentaje de Aprobación por Producto (%)',
                        labels={'porcentaje_aprobado': '% Aprobación', 'producto': 'Producto'})
            st.plotly_chart(fig3, use_container_width=True)
            
# MÓDULO DE ALERTAS AUTOMÁTICAS
elif modulo == "🚨 Alertas Automáticas":
    st.title("🚨 Sistema de Alertas Automáticas TPS")
    
    tab1, tab2, tab3 = st.tabs(["⚡ Alertas Activas", "📊 Historial", "⚙️ Configuración"])
    
    with tab1:
        st.subheader("⚡ Alertas Activas del Sistema")
        
        conn = get_connection()
        alertas_activas = pd.read_sql_query("""
            SELECT aa.*, pa.nombre_producto, lp.cantidad_kg
            FROM alertas_automaticas aa
            JOIN lotes_produccion lp ON aa.codigo_lote = lp.codigo_lote
            JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
            WHERE aa.estado_alerta = 'ACTIVA'
            ORDER BY aa.fecha_alerta DESC
        """, conn)
        conn.close()
        
        if not alertas_activas.empty:
            for _, alerta in alertas_activas.iterrows():
                criticidad_color = {
                    'ALTA': '#ef4444',
                    'MEDIA': '#f59e0b', 
                    'BAJA': '#10b981'
                }
                
                st.markdown(f"""
                <div class="alert-box" style="border-left: 4px solid {criticidad_color.get(alerta['nivel_criticidad'], '#6b7280')}">
                    <h4>🚨 {alerta['tipo_alerta']} - {alerta['nivel_criticidad']}</h4>
                    <p><strong>Lote:</strong> {alerta['codigo_lote']} ({alerta['nombre_producto']})</p>
                    <p><strong>Mensaje:</strong> {alerta['mensaje_alerta']}</p>
                    <p><strong>Parámetro:</strong> {alerta['parametro_afectado']} - Valor: {alerta['valor_detectado']} (Límite: {alerta['valor_limite']})</p>
                    <p><strong>Fecha:</strong> {alerta['fecha_alerta']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Resolver Alerta {alerta['codigo_alerta']}", key=f"resolver_{alerta['id']}"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE alertas_automaticas SET estado_alerta = 'RESUELTA' WHERE id = ?", (alerta['id'],))
                        conn.commit()
                        conn.close()
                        st.success("Alerta marcada como resuelta")
                        st.rerun()
                
                with col2:
                    accion = st.text_input(f"Acción tomada para {alerta['codigo_alerta']}", key=f"accion_{alerta['id']}")
                    if st.button(f"💾 Guardar Acción", key=f"guardar_{alerta['id']}"):
                        if accion:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("UPDATE alertas_automaticas SET accion_tomada = ? WHERE id = ?", (accion, alerta['id']))
                            conn.commit()
                            conn.close()
                            st.success("Acción guardada")
        else:
            st.success("✅ No hay alertas activas en el sistema")
        
        # Generar nueva alerta de ejemplo
        st.markdown("---")
        st.subheader("🔧 Simular Nueva Alerta")
        
        with st.form("form_alerta"):
            col1, col2 = st.columns(2)
            
            with col1:
                conn = get_connection()
                lotes = pd.read_sql_query("SELECT codigo_lote FROM lotes_produccion WHERE estado_lote IN ('NUEVO', 'EN_PROCESO')", conn)
                conn.close()
                
                if not lotes.empty:
                    lote_alerta = st.selectbox("Lote", lotes['codigo_lote'].tolist())
                
                tipo_alerta = st.selectbox("Tipo de Alerta", 
                    ["TEMPERATURA", "HUMEDAD", "PH", "PESO", "CALIDAD", "SENSOR"])
                nivel_criticidad = st.selectbox("Nivel de Criticidad", ["BAJA", "MEDIA", "ALTA"])
            
            with col2:
                mensaje_alerta = st.text_input("Mensaje de Alerta", 
                    placeholder="Descripción del problema detectado")
                parametro_afectado = st.text_input("Parámetro Afectado", placeholder="Ej: Temperatura")
                valor_detectado = st.number_input("Valor Detectado", value=0.0)
                valor_limite = st.number_input("Valor Límite", value=0.0)
            
            if st.form_submit_button("🚨 Generar Alerta"):
                if lote_alerta and mensaje_alerta:
                    codigo_alerta = f"ALT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute('''
                            INSERT INTO alertas_automaticas (codigo_alerta, codigo_lote, tipo_alerta, nivel_criticidad, mensaje_alerta, parametro_afectado, valor_detectado, valor_limite, estado_alerta)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (codigo_alerta, lote_alerta, tipo_alerta, nivel_criticidad, mensaje_alerta, parametro_afectado, valor_detectado, valor_limite, 'ACTIVA'))
                        conn.commit()
                        st.success(f"🚨 Alerta generada: {codigo_alerta}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                    finally:
                        conn.close()
    
    with tab2:
        st.subheader("📊 Historial de Alertas")
        
        conn = get_connection()
        alertas_df = pd.read_sql_query("""
            SELECT aa.*, pa.nombre_producto
            FROM alertas_automaticas aa
            JOIN lotes_produccion lp ON aa.codigo_lote = lp.codigo_lote
            JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
            ORDER BY aa.fecha_alerta DESC
        """, conn)
        conn.close()
        
        if not alertas_df.empty:
            st.dataframe(alertas_df, use_container_width=True, height=400)
            
            # Métricas de alertas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🚨 Total Alertas", len(alertas_df))
            with col2:
                activas = len(alertas_df[alertas_df['estado_alerta'] == 'ACTIVA'])
                st.metric("⚡ Activas", activas)
            with col3:
                resueltas = len(alertas_df[alertas_df['estado_alerta'] == 'RESUELTA'])
                st.metric("✅ Resueltas", resueltas)
            with col4:
                criticas = len(alertas_df[alertas_df['nivel_criticidad'] == 'ALTA'])
                st.metric("🔴 Críticas", criticas)
        else:
            st.info("🚨 No hay alertas en el historial")
    
    with tab3:
        st.subheader("⚙️ Configuración de Alertas")
        
        st.markdown("### 🎛️ Parámetros de Alertas Automáticas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🌡️ Alertas de Temperatura**")
            temp_alerta_min = st.number_input("Temperatura Mínima Alerta (°C)", value=1.0)
            temp_alerta_max = st.number_input("Temperatura Máxima Alerta (°C)", value=9.0)
            
            st.markdown("**💧 Alertas de Humedad**")
            hum_alerta_min = st.number_input("Humedad Mínima Alerta (%)", value=80.0)
            hum_alerta_max = st.number_input("Humedad Máxima Alerta (%)", value=98.0)
        
        with col2:
            st.markdown("**🧪 Alertas de pH**")
            ph_alerta_min = st.number_input("pH Mínimo Alerta", value=5.5)
            ph_alerta_max = st.number_input("pH Máximo Alerta", value=8.0)
            
            st.markdown("**⚖️ Alertas de Peso**")
            peso_variacion_max = st.number_input("Variación Máxima Peso (%)", value=10.0)
        
        if st.button("💾 Guardar Configuración de Alertas"):
            st.success("✅ Configuración de alertas actualizada")

# MÓDULO DE INFORMES CONSOLIDADOS
elif modulo == "📊 Informes Consolidados":
    st.title("📊 Informes Consolidados de Calidad")
    
    tab1, tab2, tab3 = st.tabs(["📋 Generar Informe", "📊 Informes Existentes", "📈 Análisis Ejecutivo"])
    
    with tab1:
        st.subheader("📋 Generar Informe Consolidado")
        
        with st.form("form_informe"):
            conn = get_connection()
            lotes_disponibles = pd.read_sql_query("""
                SELECT DISTINCT lp.codigo_lote, pa.nombre_producto, lp.cantidad_kg
                FROM lotes_produccion lp
                JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
                LEFT JOIN informes_calidad ic ON lp.codigo_lote = ic.codigo_lote
                WHERE ic.codigo_lote IS NULL AND lp.estado_lote = 'EN_PROCESO'
            """, conn)
            conn.close()
            
            if not lotes_disponibles.empty:
                lote_informe = st.selectbox("Lote para Informe", 
                    options=lotes_disponibles['codigo_lote'].tolist(),
                    format_func=lambda x: f"{x} - {lotes_disponibles[lotes_disponibles['codigo_lote']==x]['nombre_producto'].iloc[0]}")
                
                responsable_aprobacion = st.text_input("Responsable de Aprobación", 
                    placeholder="Ing. Nombre Apellido")
                
                # Obtener resultados automáticamente
                conn = get_connection()
                
                # Resultado inspección visual
                inspeccion = pd.read_sql_query(
                    "SELECT resultado_visual FROM inspecciones_visuales WHERE codigo_lote = ? ORDER BY fecha_inspeccion DESC LIMIT 1", 
                    conn, params=[lote_informe])
                resultado_inspeccion = inspeccion['resultado_visual'].iloc[0] if not inspeccion.empty else "PENDIENTE"
                
                # Resultado sensores
                sensores = pd.read_sql_query(
                    "SELECT estado_sensores FROM lecturas_sensores WHERE codigo_lote = ? ORDER BY timestamp_lectura DESC LIMIT 1", 
                    conn, params=[lote_informe])
                resultado_sensores = "NORMAL" if not sensores.empty and sensores['estado_sensores'].iloc[0] == 'OPERATIVO' else "ALERTA"
                
                # Resultado fisicoquímico
                fisicoquimico = pd.read_sql_query(
                    "SELECT resultado_fisicoquimico FROM pruebas_fisicoquimicas WHERE codigo_lote = ? ORDER BY fecha_prueba DESC LIMIT 1", 
                    conn, params=[lote_informe])
                resultado_fisicoquimico = fisicoquimico['resultado_fisicoquimico'].iloc[0] if not fisicoquimico.empty else "PENDIENTE"
                
                conn.close()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Inspección Visual:** {resultado_inspeccion}")
                    st.write(f"**Estado Sensores:** {resultado_sensores}")
                    st.write(f"**Resultado Fisicoquímico:** {resultado_fisicoquimico}")
                
                with col2:
                    resultado_envases = st.selectbox("Resultado Envases", ["APROBADO", "RECHAZADO", "PENDIENTE"])
                    certificaciones = st.multiselect("Certificaciones Obtenidas", 
                        ["Global GAP", "HACCP", "Organic", "Fair Trade", "BRC", "SQF"])
                    destino_comercial = st.selectbox("Destino Comercial", 
                        ["Exportación USA", "Exportación Europa", "Exportación Asia", "Mercado Nacional"])
                
                # Calcular decisión final automática
                resultados = [resultado_inspeccion, resultado_fisicoquimico, resultado_envases]
                if all(r == "APROBADO" for r in resultados) and resultado_sensores == "NORMAL":
                    decision_final = "APROBADO"
                    porcentaje_calidad = 95.0
                elif any(r == "RECHAZADO" for r in resultados):
                    decision_final = "RECHAZADO"
                    porcentaje_calidad = 60.0
                else:
                    decision_final = "PENDIENTE"
                    porcentaje_calidad = 75.0
                
                st.write(f"**Decisión Final Automática:** {decision_final}")
                st.write(f"**Porcentaje de Calidad:** {porcentaje_calidad}%")
                
                submitted = st.form_submit_button("📊 Generar Informe Consolidado", use_container_width=True)
                
                if submitted:
                    if responsable_aprobacion:
                        codigo_informe = f"INF-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                        conn = get_connection()
                        cursor = conn.cursor()
                        try:
                            cursor.execute('''
                                INSERT INTO informes_calidad (codigo_informe, codigo_lote, resultado_inspeccion_visual, resultado_sensores, resultado_fisicoquimico, resultado_envases, decision_final, porcentaje_calidad_total, certificaciones_obtenidas, destino_comercial, responsable_aprobacion, fecha_aprobacion)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (codigo_informe, lote_informe, resultado_inspeccion, resultado_sensores, resultado_fisicoquimico, resultado_envases, decision_final, porcentaje_calidad, ', '.join(certificaciones), destino_comercial, responsable_aprobacion, datetime.datetime.now()))
                            
                            # Actualizar estado del lote
                            nuevo_estado = "APROBADO" if decision_final == "APROBADO" else "RECHAZADO" if decision_final == "RECHAZADO" else "EN_REVISION"
                            cursor.execute("UPDATE lotes_produccion SET estado_lote = ? WHERE codigo_lote = ?", (nuevo_estado, lote_informe))
                            
                            conn.commit()
                            st.success(f"✅ Informe consolidado generado: {codigo_informe}")
                            
                            # Mostrar resultado final
                            if decision_final == "APROBADO":
                                st.markdown('<div class="status-aprobado">✅ LOTE APROBADO PARA COMERCIALIZACIÓN</div>', unsafe_allow_html=True)
                            elif decision_final == "RECHAZADO":
                                st.markdown('<div class="status-rechazado">❌ LOTE RECHAZADO</div>', unsafe_allow_html=True)
                            else:
                                st.markdown('<div class="status-pendiente">⏳ LOTE EN REVISIÓN</div>', unsafe_allow_html=True)
                                
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                        finally:
                            conn.close()
                    else:
                        st.error("❌ Ingrese el responsable de aprobación")
            else:
                st.info("📋 No hay lotes disponibles para generar informes")
    
    with tab2:
        st.subheader("📊 Informes Existentes")
        
        conn = get_connection()
        informes_df = pd.read_sql_query("""
            SELECT ic.*, pa.nombre_producto, lp.cantidad_kg, lp.campo_origen
            FROM informes_calidad ic
            JOIN lotes_produccion lp ON ic.codigo_lote = lp.codigo_lote
            JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
            ORDER BY ic.fecha_informe DESC
        """, conn)
        conn.close()
        
        if not informes_df.empty:
            st.dataframe(informes_df, use_container_width=True, height=400)
            
            # Métricas de informes
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Informes", len(informes_df))
            with col2:
                aprobados = len(informes_df[informes_df['decision_final'] == 'APROBADO'])
                st.metric("✅ Lotes Aprobados", aprobados)
            with col3:
                calidad_promedio = informes_df['porcentaje_calidad_total'].mean()
                st.metric("📈 Calidad Promedio", f"{calidad_promedio:.1f}%")
            with col4:
                exportacion = len(informes_df[informes_df['destino_comercial'].str.contains('Exportación', na=False)])
                st.metric("🌍 Para Exportación", exportacion)
        else:
            st.info("📊 No hay informes consolidados generados")
    
    with tab3:
    st.subheader("📈 Análisis Ejecutivo Avanzado")
    
    conn = get_connection()
    informes_df = pd.read_sql_query("""
        SELECT ic.*, pa.nombre_producto, pa.categoria, lp.campo_origen
        FROM informes_calidad ic
        JOIN lotes_produccion lp ON ic.codigo_lote = lp.codigo_lote
        JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
    """, conn)
    conn.close()
    
    if not informes_df.empty:
        # Filtros para análisis
        st.subheader("🔍 Filtros para Análisis")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            producto_filtro = st.selectbox("Filtrar por Producto", 
                ["Todos"] + list(informes_df['nombre_producto'].unique()))
        
        with col2:
            destino_filtro = st.selectbox("Filtrar por Destino", 
                ["Todos"] + list(informes_df['destino_comercial'].unique()))
        
        with col3:
            fecha_inicio = st.date_input("Fecha inicio", value=date.today() - timedelta(days=30))
            fecha_fin = st.date_input("Fecha fin", value=date.today())
        
        # Aplicar filtros
        if producto_filtro != "Todos":
            informes_df = informes_df[informes_df['nombre_producto'] == producto_filtro]
        
        if destino_filtro != "Todos":
            informes_df = informes_df[informes_df['destino_comercial'] == destino_filtro]
        
        informes_df['fecha_informe'] = pd.to_datetime(informes_df['fecha_informe']).dt.date
        informes_df = informes_df[(informes_df['fecha_informe'] >= fecha_inicio) & 
                                (informes_df['fecha_informe'] <= fecha_fin)]
        
        # Mostrar métricas filtradas
        st.subheader("📊 Métricas Clave")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📦 Lotes Analizados", len(informes_df))
        with col2:
            calidad_promedio = informes_df['porcentaje_calidad_total'].mean()
            st.metric("📈 Calidad Promedio", f"{calidad_promedio:.1f}%")
        with col3:
            aprobados = len(informes_df[informes_df['decision_final'] == 'APROBADO'])
            st.metric("✅ Lotes Aprobados", aprobados)
        with col4:
            rechazados = len(informes_df[informes_df['decision_final'] == 'RECHAZADO'])
            st.metric("❌ Lotes Rechazados", rechazados)
        
        # Gráficos avanzados
        st.subheader("📈 Tendencias de Calidad")
        
        # Tendencia semanal de calidad
        informes_df['semana'] = pd.to_datetime(informes_df['fecha_informe']).dt.to_period('W').astype(str)
        tendencia_semanal = informes_df.groupby('semana')['porcentaje_calidad_total'].mean().reset_index()
        
        fig = px.line(tendencia_semanal, x='semana', y='porcentaje_calidad_total',
                     title='Tendencia Semanal de Calidad (%)',
                     markers=True)
        st.plotly_chart(fig, use_container_width=True)
        
        # Calidad por producto y destino
        if len(informes_df) > 1:
            calidad_producto_destino = informes_df.groupby(['nombre_producto', 'destino_comercial'])['porcentaje_calidad_total'].mean().unstack().reset_index()
            
            fig2 = px.bar(calidad_producto_destino, 
                         x='nombre_producto',
                         y=calidad_producto_destino.columns[1:],
                         title='Calidad Promedio por Producto y Destino',
                         barmode='group',
                         labels={'value': 'Calidad (%)', 'nombre_producto': 'Producto'})
            st.plotly_chart(fig2, use_container_width=True)
        
        # Exportar reporte
        st.subheader("📤 Exportar Reporte")
        
        if st.button("💾 Generar Reporte PDF"):
            # Aquí iría la lógica para generar un PDF con los análisis
            st.success("✅ Reporte generado (simulación)")
        
        if st.button("📊 Exportar Datos a Excel"):
            # Crear un archivo Excel en memoria
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                informes_df.to_excel(writer, sheet_name='Informes', index=False)
                
                # Crear hoja de resumen
                resumen = pd.DataFrame({
                    'Métrica': ['Lotes Analizados', 'Calidad Promedio', 'Lotes Aprobados', 'Lotes Rechazados'],
                    'Valor': [len(informes_df), f"{calidad_promedio:.1f}%", aprobados, rechazados]
                })
                resumen.to_excel(writer, sheet_name='Resumen', index=False)
            
            output.seek(0)
            st.download_button(
                label="⬇️ Descargar Excel",
                data=output,
                file_name=f"reporte_calidad_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
# MÓDULO DE TRAZABILIDAD INTERNACIONAL
elif modulo == "🌍 Trazabilidad Internacional":
    st.title("🌍 Trazabilidad Internacional - Exportaciones")
    
    tab1, tab2, tab3 = st.tabs(["🚢 Nuevo Envío", "📦 Seguimiento", "📊 Reportes"])
    
    with tab1:
        st.subheader("🚢 Registrar Envío Internacional")
        
        with st.form("form_trazabilidad"):
            col1, col2 = st.columns(2)
            
            with col1:
                conn = get_connection()
                lotes_aprobados = pd.read_sql_query("""
                    SELECT lp.codigo_lote, pa.nombre_producto, ic.destino_comercial
                    FROM lotes_produccion lp
                    JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
                    JOIN informes_calidad ic ON lp.codigo_lote = ic.codigo_lote
                    WHERE ic.decision_final = 'APROBADO' AND lp.estado_lote = 'APROBADO'
                """, conn)
                conn.close()
                
                if not lotes_aprobados.empty:
                    lote_envio = st.selectbox("Lote Aprobado", 
                        options=lotes_aprobados['codigo_lote'].tolist(),
                        format_func=lambda x: f"{x} - {lotes_aprobados[lotes_aprobados['codigo_lote']==x]['nombre_producto'].iloc[0]}")
                
                pais_destino = st.selectbox("País de Destino", 
                    ["Estados Unidos", "Países Bajos", "Reino Unido", "Alemania", "Francia", "Canadá", "Japón"])
                cliente_internacional = st.text_input("Cliente Internacional", 
                    placeholder="Nombre del importador")
                certificacion_requerida = st.multiselect("Certificaciones Requeridas", 
                    ["Global GAP", "HACCP", "Organic", "Fair Trade", "BRC", "SQF", "FDA"])
            
            with col2:
                numero_contenedor = st.text_input("Número de Contenedor", 
                    placeholder="ABCD1234567")
                fecha_embarque = st.date_input("Fecha de Embarque", value=date.today() + timedelta(days=7))
                puerto_destino = st.text_input("Puerto de Destino", 
                    placeholder="Puerto de destino")
                documentos_exportacion = st.text_area("Documentos de Exportación", 
                    placeholder="Lista de documentos requeridos...")
                estado_envio = st.selectbox("Estado del Envío", 
                    ["PREPARACION", "EMBARCADO", "EN_TRANSITO", "LLEGADA", "ENTREGADO"])
            
            submitted = st.form_submit_button("🌍 Registrar Trazabilidad", use_container_width=True)
            
            if submitted:
                if lote_envio and cliente_internacional:
                    codigo_trazabilidad = f"TRZ-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute('''
                            INSERT INTO trazabilidad_internacional (codigo_trazabilidad, codigo_lote, pais_destino, cliente_internacional, certificacion_requerida, numero_contenedor, fecha_embarque, puerto_destino, documentos_exportacion, estado_envio)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (codigo_trazabilidad, lote_envio, pais_destino, cliente_internacional, ', '.join(certificacion_requerida), numero_contenedor, fecha_embarque, puerto_destino, documentos_exportacion, estado_envio))
                        
                        # Actualizar estado del lote
                        cursor.execute("UPDATE lotes_produccion SET estado_lote = 'EXPORTADO' WHERE codigo_lote = ?", (lote_envio,))
                        
                        conn.commit()
                        st.success(f"✅ Trazabilidad registrada: {codigo_trazabilidad}")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("❌ Complete los campos obligatorios")
    
    with tab2:
        st.subheader("📦 Seguimiento de Envíos")
        
        conn = get_connection()
        trazabilidad_df = pd.read_sql_query("""
            SELECT ti.*, pa.nombre_producto, lp.cantidad_kg
            FROM trazabilidad_internacional ti
            JOIN lotes_produccion lp ON ti.codigo_lote = lp.codigo_lote
            JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
            ORDER BY ti.fecha_embarque DESC
        """, conn)
        conn.close()
        
        if not trazabilidad_df.empty:
            # Filtro por estado
            estado_filtro = st.selectbox("Filtrar por Estado", 
                ["Todos"] + list(trazabilidad_df['estado_envio'].unique()))
            
            if estado_filtro != "Todos":
                df_filtrado = trazabilidad_df[trazabilidad_df['estado_envio'] == estado_filtro]
            else:
                df_filtrado = trazabilidad_df
            
            st.dataframe(df_filtrado, use_container_width=True, height=400)
            
            # Métricas de exportación
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🚢 Total Envíos", len(df_filtrado))
            with col2:
                en_transito = len(df_filtrado[df_filtrado['estado_envio'] == 'EN_TRANSITO'])
                st.metric("🌊 En Tránsito", en_transito)
            with col3:
                entregados = len(df_filtrado[df_filtrado['estado_envio'] == 'ENTREGADO'])
                st.metric("✅ Entregados", entregados)
            with col4:
                paises_unicos = df_filtrado['pais_destino'].nunique()
                st.metric("🌍 Países Destino", paises_unicos)
        else:
            st.info("🌍 No hay envíos internacionales registrados")
    
    with tab3:
        st.subheader("📊 Reportes de Exportación")
        
        conn = get_connection()
        trazabilidad_df = pd.read_sql_query("""
            SELECT ti.*, pa.nombre_producto, pa.categoria, lp.cantidad_kg
            FROM trazabilidad_internacional ti
            JOIN lotes_produccion lp ON ti.codigo_lote = lp.codigo_lote
            JOIN productos_agro pa ON lp.codigo_producto = pa.codigo_producto
        """, conn)
        conn.close()
        
        if not trazabilidad_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Exportaciones por país
                pais_dist = trazabilidad_df['pais_destino'].value_counts().reset_index()
                pais_dist.columns = ['pais', 'cantidad']
                
                fig = px.bar(pais_dist, x='pais', y='cantidad',
                           title='Exportaciones por País de Destino')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Estados de envío
                estado_dist = trazabilidad_df['estado_envio'].value_counts().reset_index()
                estado_dist.columns = ['estado', 'cantidad']
                
                fig2 = px.pie(estado_dist, values='cantidad', names='estado',
                            title='Distribución por Estado de Envío')
                st.plotly_chart(fig2, use_container_width=True)
            
            # Volumen exportado por producto
            volumen_producto = trazabilidad_df.groupby('nombre_producto')['cantidad_kg'].sum().reset_index()
            
            fig3 = px.bar(volumen_producto, x='nombre_producto', y='cantidad_kg',
                        title='Volumen Exportado por Producto (kg)')
            st.plotly_chart(fig3, use_container_width=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;'>
    <h4>🌱 DANPER TPS v1.0</h4>
    <p style='margin: 0; font-size: 0.8rem;'>Sistema de Procesamiento de Transacciones</p>
    <p style='margin: 0; font-size: 0.8rem;'>Control de Calidad Agroindustrial</p>
    <p style='margin: 0; font-size: 0.8rem;'>Odoo 17 | PostgreSQL | Python + XML</p>
</div>
""", unsafe_allow_html=True)

# Información del TPS
with st.sidebar.expander("ℹ️ Información del TPS"):
    st.markdown("""
    **Tipo de TPS:** Control de Calidad Agroindustrial
    
    **Funciones Principales:**
    - 👁️ Inspecciones visuales automatizadas
    - 📡 Lecturas de sensores IoT
    - 🧪 Pruebas fisicoquímicas
    - 📦 Compatibilidad de envases
    - 🚨 Alertas automáticas
    - 📊 Informes consolidados
    - 🌍 Trazabilidad internacional
    
    **Tecnologías:**
    - Odoo 17 (ERP)
    - PostgreSQL (Base de datos)
    - Python + XML (Desarrollo)
    - Sensores IoT (Hardware)
    
    **Estado:** Operativo ✅
    """)

with st.sidebar.expander("📊 Estadísticas del TPS"):
    conn = get_connection()
    
    total_lotes = pd.read_sql_query("SELECT COUNT(*) as total FROM lotes_produccion", conn)
    total_inspecciones = pd.read_sql_query("SELECT COUNT(*) as total FROM inspecciones_visuales", conn)
    total_sensores = pd.read_sql_query("SELECT COUNT(*) as total FROM lecturas_sensores", conn)
    total_pruebas = pd.read_sql_query("SELECT COUNT(*) as total FROM pruebas_fisicoquimicas", conn)
    total_alertas = pd.read_sql_query("SELECT COUNT(*) as total FROM alertas_automaticas", conn)
    total_informes = pd.read_sql_query("SELECT COUNT(*) as total FROM informes_calidad", conn)
    
    st.metric("📦 Lotes", total_lotes['total'].iloc[0])
    st.metric("👁️ Inspecciones", total_inspecciones['total'].iloc[0])
    st.metric("📡 Lecturas Sensores", total_sensores['total'].iloc[0])
    st.metric("🧪 Pruebas Lab", total_pruebas['total'].iloc[0])
    st.metric("🚨 Alertas", total_alertas['total'].iloc[0])
    st.metric("📊 Informes", total_informes['total'].iloc[0])
    
    conn.close()
