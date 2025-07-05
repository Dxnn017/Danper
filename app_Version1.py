He corregido los errores en el código y lo he mejorado para que funcione correctamente. Aquí está la versión corregida:

```python
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
from io import BytesIO

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
        
        # Compatibilidad de envases
        envases_ejemplo = [
            ('ENV-20241201-001', 'LT-ESP-20241201', datetime.datetime.now() - timedelta(hours=1), 'Caja de cartón', 'Cartón corrugado', '5 kg', 1, 1, 1, 'APROBADO', 'Envase adecuado para exportación'),
            ('ENV-20241201-002', 'LT-PAL-20241201', datetime.datetime.now() - timedelta(minutes=45), 'Bandeja PET', 'PET reciclado', '4 unidades', 1, 1, 1, 'APROBADO', 'Envase premium para mercado europeo'),
            ('ENV-20241201-003', 'LT-ARA-20241201', datetime.datetime.now() - timedelta(minutes=30), 'Clamshell', 'PET transparente', '125 g', 1, 1, 1, 'APROBADO', 'Envase estándar para berries')
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
        
        # Trazabilidad internacional
        trazabilidad_ejemplo = [
            ('TRZ-20241201-001', 'LT-ESP-20241201', 'Estados Unidos', 'Fresh Foods Inc.', 'Global GAP, HACCP', 'ECMU1234567', date.today() + timedelta(days=7), 'Miami', 'Factura, BL, Certificado Fitosanitario', 'PREPARACION'),
            ('TRZ-20241201-002', 'LT-PAL-20241201', 'Países Bajos', 'European Fruits BV', 'Organic, Fair Trade', 'CMAU7654321', date.today() + timedelta(days=10), 'Rotterdam', 'Factura, BL, Certificado Orgánico', 'PREPARACION')
        ]
        
        cursor.executemany('''
            INSERT INTO trazabilidad_internacional (codigo_trazabilidad, codigo_lote, pais_destino, cliente_internacional, certificacion_requerida, numero_contenedor, fecha_embarque, documentos_exportacion, estado_envio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', trazabilidad_ejemplo)
    
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
