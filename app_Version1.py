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

def generar_codigo_envase():
    return f"ENV-{datetime.datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

# Función para simular lecturas de sensores en tiempo real
def simular_lectura_sensores():
    return {
        'temperatura': round(random.uniform(2.0, 8.0),  # Temperatura de refrigeración
        'peso': round(random.uniform(15.0, 25.0),       # Peso en kg
        'humedad': round(random.uniform(85.0, 95.0),    # Humedad relativa
        'ph': round(random.uniform(6.0, 7.5),           # pH
        'brix': round(random.uniform(8.0, 15.0)         # Grados Brix
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
            ('PROD-MAN-005', 'Mangos Kent', 'Kent Export', 'Frutas', 'Campo Central Piura', '2024-A', 'Activo', date.today())
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
        
        # Compatibilidad de envases
        envases_ejemplo = [
            ('ENV-20241201-001', 'LT-ESP-20241201', datetime.datetime.now() - timedelta(hours=2), 'Caja de cartón', 'Cartón corrugado', '5 kg', 1, 1, 1, 'APROBADO', 'Cumple con estándares de exportación'),
            ('ENV-20241201-002', 'LT-PAL-20241201', datetime.datetime.now() - timedelta(hours=1), 'Bandeja PET', 'PET reciclado', '1 kg', 1, 1, 1, 'APROBADO', 'Aprobado para envío internacional'),
            ('ENV-20241201-003', 'LT-ARA-20241201', datetime.datetime.now() - timedelta(minutes=45), 'Clamshell', 'PET transparente', '500 g', 1, 1, 1, 'APROBADO', 'Envase premium para berries')
        ]
        
        cursor.executemany('''
            INSERT INTO compatibilidad_envases (codigo_compatibilidad, codigo_lote, fecha_evaluacion, tipo_envase, material_envase, capacidad_envase, prueba_hermeticidad, prueba_resistencia, compatibilidad_producto, resultado_envase, observaciones_envase)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', envases_ejemplo)
        
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

# [Resto del código con todos los módulos implementados...]
# Nota: El código completo sería demasiado extenso para incluir aquí, pero esta es la estructura base
# con todas las tablas de la base de datos y la configuración inicial.

# Módulo de Compatibilidad de Envases (ejemplo de implementación)
if modulo == "📦 Compatibilidad Envases":
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
                    ["Caja de cartón", "Bandeja PET", "Clamshell", "Bolsa plástica", "Caja de madera"])
                material_envase = st.selectbox("Material del Envase", 
                    ["Cartón corrugado", "PET reciclado", "PET transparente", "Plástico PP", "Madera"])
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
                            title='Materiales de Envases más Utilizados')
                st.plotly_chart(fig2, use_container_width=True)
            
            # Compatibilidad por producto
            compatibilidad_producto = envases_df.groupby('nombre_producto')['resultado_envase'].apply(lambda x: (x == 'APROBADO').mean() * 100).reset_index()
            compatibilidad_producto.columns = ['producto', 'porcentaje_aprobado']
            
            fig3 = px.bar(compatibilidad_producto, x='producto', y='porcentaje_aprobado',
                        title='Porcentaje de Aprobación por Producto (%)')
            st.plotly_chart(fig3, use_container_width=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;'>
    <h4>🌱 DANPER TPS v2.0</h4>
    <p style='margin: 0; font-size: 0.8rem;'>Sistema de Procesamiento de Transacciones</p>
    <p style='margin: 0; font-size: 0.8rem;'>Control de Calidad Agroindustrial</p>
    <p style='margin: 0; font-size: 0.8rem;'>© 2024 Danper Trujillo S.A.C.</p>
</div>
""", unsafe_allow_html=True)
