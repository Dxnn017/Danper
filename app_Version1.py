import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


st.set_page_config(
    page_title="TPS Calidad - DANPER",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #e53e3e 0%, #c53030 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #e53e3e;
    }
    .quality-status-ok {
        background-color: #48bb78;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    .quality-status-warning {
        background-color: #ed8936;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    .quality-status-critical {
        background-color: #e53e3e;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_database():
    conn = sqlite3.connect('danper_quality.db', check_same_thread=False)
    cursor = conn.cursor()
    
 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS control_calidad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_control DATE,
            lote_producto TEXT,
            tipo_producto TEXT,
            variedad TEXT,
            parametros_fisicos TEXT,
            parametros_quimicos TEXT,
            parametros_microbiologicos TEXT,
            resultado_general TEXT,
            inspector TEXT,
            observaciones TEXT,
            estado_aprobacion TEXT,
            fecha_vencimiento DATE
        )
    ''')
    

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trazabilidad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_trazabilidad TEXT UNIQUE,
            lote_producto TEXT,
            origen_campo TEXT,
            fecha_siembra DATE,
            fecha_cosecha DATE,
            tratamientos_aplicados TEXT,
            certificaciones TEXT,
            destino_exportacion TEXT,
            cliente_final TEXT,
            estado_seguimiento TEXT,
            documentos_adjuntos TEXT
        )
    ''')
    

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auditorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_auditoria DATE,
            tipo_auditoria TEXT,
            area_auditada TEXT,
            auditor_responsable TEXT,
            norma_aplicada TEXT,
            hallazgos_criticos INTEGER,
            hallazgos_mayores INTEGER,
            hallazgos_menores INTEGER,
            puntuacion_total REAL,
            estado_auditoria TEXT,
            fecha_seguimiento DATE,
            plan_accion TEXT
        )
    ''')
    

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS no_conformidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_deteccion DATE,
            codigo_nc TEXT UNIQUE,
            tipo_nc TEXT,
            area_afectada TEXT,
            descripcion_nc TEXT,
            causa_raiz TEXT,
            accion_inmediata TEXT,
            accion_correctiva TEXT,
            responsable TEXT,
            fecha_cierre_programada DATE,
            fecha_cierre_real DATE,
            estado_nc TEXT,
            eficacia_verificada TEXT
        )
    ''')
    
    conn.commit()
    return conn


def get_connection():
    return sqlite3.connect('danper_quality.db', check_same_thread=False)

@st.cache_data
def insert_sample_data():
    conn = get_connection()
    cursor = conn.cursor()
    

    cursor.execute("SELECT COUNT(*) FROM control_calidad")
    if cursor.fetchone()[0] == 0:

        sample_quality_data = [
            (date.today() - timedelta(days=1), 'LT-ESP-001', 'Espárragos', 'UC-157', 
             'Longitud: 18cm, Diámetro: 12mm', 'Brix: 6.2, pH: 6.8', 'Coliformes: <10 UFC/g',
             'APROBADO', 'Juan Pérez', 'Producto conforme', 'APROBADO', date.today() + timedelta(days=30)),
            (date.today(), 'LT-PAL-002', 'Paltas', 'Hass', 
             'Peso: 180g, Firmeza: 8kg', 'Materia seca: 23%', 'Salmonella: Ausente',
             'APROBADO', 'María García', 'Calidad exportación', 'APROBADO', date.today() + timedelta(days=45)),
            (date.today() - timedelta(days=2), 'LT-ARA-003', 'Arándanos', 'Biloxi', 
             'Calibre: 16-18mm, Firmeza: 180g/mm', 'Brix: 12.5, Acidez: 0.8%', 'Mohos: <100 UFC/g',
             'APROBADO', 'Carlos López', 'Excelente calidad', 'APROBADO', date.today() + timedelta(days=21)),
            (date.today() - timedelta(days=3), 'LT-UVA-004', 'Uvas', 'Red Globe', 
             'Peso racimo: 450g, Bayas: 18mm', 'Brix: 16.8, pH: 3.9', 'Levaduras: <1000 UFC/g',
             'OBSERVADO', 'Ana Martín', 'Revisar calibre', 'PENDIENTE', date.today() + timedelta(days=14))
        ]
        
        cursor.executemany('''
            INSERT INTO control_calidad 
            (fecha_control, lote_producto, tipo_producto, variedad, parametros_fisicos, 
             parametros_quimicos, parametros_microbiologicos, resultado_general, inspector, 
             observaciones, estado_aprobacion, fecha_vencimiento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_quality_data)
        

        sample_trace_data = [
            ('TRZ-ESP-001', 'LT-ESP-001', 'Campo Norte - Sector A', 
             date.today() - timedelta(days=120), date.today() - timedelta(days=30),
             'Fertilización orgánica, Control biológico', 'Global GAP, HACCP', 
             'Estados Unidos', 'Walmart USA', 'ENTREGADO', 'Certificado_GlobalGAP.pdf'),
            ('TRZ-PAL-002', 'LT-PAL-002', 'Campo Sur - Sector B',
             date.today() - timedelta(days=365), date.today() - timedelta(days=15),
             'Riego tecnificado, Poda selectiva', 'Organic, Fair Trade',
             'Europa', 'Carrefour Francia', 'EN_TRANSITO', 'Certificado_Organico.pdf'),
            ('TRZ-ARA-003', 'LT-ARA-003', 'Campo Este - Sector C',
             date.today() - timedelta(days=180), date.today() - timedelta(days=45),
             'Manejo integrado de plagas', 'Global GAP, BRC',
             'Canadá', 'Loblaws Canada', 'ENTREGADO', 'Certificado_BRC.pdf')
        ]
        
        cursor.executemany('''
            INSERT INTO trazabilidad 
            (codigo_trazabilidad, lote_producto, origen_campo, fecha_siembra, fecha_cosecha,
             tratamientos_aplicados, certificaciones, destino_exportacion, cliente_final,
             estado_seguimiento, documentos_adjuntos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_trace_data)
        

        sample_audit_data = [
            (date.today() - timedelta(days=30), 'Externa', 'Producción', 'SGS Perú', 'Global GAP',
             0, 2, 5, 92.5, 'COMPLETADA', date.today() + timedelta(days=30), 'Mejorar documentación de registros'),
            (date.today() - timedelta(days=15), 'Interna', 'Laboratorio', 'Equipo Interno', 'HACCP',
             1, 1, 3, 88.0, 'COMPLETADA', date.today() + timedelta(days=15), 'Calibración de equipos'),
            (date.today() - timedelta(days=7), 'Cliente', 'Empaque', 'Walmart Auditor', 'BRC',
             0, 0, 2, 95.5, 'COMPLETADA', date.today() + timedelta(days=60), 'Mantener estándares')
        ]
        
        cursor.executemany('''
            INSERT INTO auditorias 
            (fecha_auditoria, tipo_auditoria, area_auditada, auditor_responsable, norma_aplicada,
             hallazgos_criticos, hallazgos_mayores, hallazgos_menores, puntuacion_total,
             estado_auditoria, fecha_seguimiento, plan_accion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_audit_data)
        

        sample_nc_data = [
            (date.today() - timedelta(days=10), 'NC-001', 'Producto', 'Laboratorio', 
             'Resultado microbiológico fuera de especificación', 'Contaminación cruzada en muestreo',
             'Repetir análisis con nueva muestra', 'Implementar protocolo de muestreo aséptico',
             'Jefe de Laboratorio', date.today() + timedelta(days=5), None, 'CERRADA', 'SI'),
            (date.today() - timedelta(days=5), 'NC-002', 'Proceso', 'Empaque',
             'Temperatura de cámara fuera de rango', 'Falla en sensor de temperatura',
             'Ajuste manual de temperatura', 'Reemplazo de sensor y calibración',
             'Supervisor de Empaque', date.today() + timedelta(days=3), None, 'EN_PROCESO', None)
        ]
        
        cursor.executemany('''
            INSERT INTO no_conformidades 
            (fecha_deteccion, codigo_nc, tipo_nc, area_afectada, descripcion_nc, causa_raiz,
             accion_inmediata, accion_correctiva, responsable, fecha_cierre_programada,
             fecha_cierre_real, estado_nc, eficacia_verificada)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_nc_data)
    
    conn.commit()
    conn.close()

conn = init_database()
insert_sample_data()

st.markdown("""
<div class="main-header">
    <h1>🌱 SISTEMA TPS CALIDAD - DANPER</h1>
    <p>Sistema de Procesamiento de Transacciones para Control de Calidad Agroindustrial</p>
    <p><strong>ISIA-103 - Sistemas Empresariales | Proyecto Semestral 2025</strong></p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style='background: linear-gradient(90deg, #e53e3e 0%, #c53030 100%); padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 1rem;'>
    <h2 style='color: white; margin: 0;'>🌱 DANPER</h2>
    <p style='color: white; margin: 0; font-size: 0.9rem;'>Control de Calidad</p>
</div>
""", unsafe_allow_html=True)

modulo = st.sidebar.selectbox(
    "🎯 Seleccionar Módulo de Calidad:",
    ["🏠 Dashboard de Calidad", "🔬 Control de Calidad", "📋 Trazabilidad", 
     "🔍 Auditorías", "⚠️ No Conformidades"]
)

if modulo == "🏠 Dashboard de Calidad":
    st.title("🏠 Dashboard de Calidad - DANPER")
    
    col1, col2, col3, col4 = st.columns(4)
    
    conn = get_connection()
    
    productos_aprobados = pd.read_sql_query(
        "SELECT COUNT(*) as total FROM control_calidad WHERE fecha_control = ? AND estado_aprobacion = 'APROBADO'", 
        conn, params=[date.today()]
    )

    auditorias_pendientes = pd.read_sql_query(
        "SELECT COUNT(*) as total FROM auditorias WHERE estado_auditoria = 'PENDIENTE'", 
        conn
    )
    
    nc_abiertas = pd.read_sql_query(
        "SELECT COUNT(*) as total FROM no_conformidades WHERE estado_nc IN ('ABIERTA', 'EN_PROCESO')", 
        conn
    )
    
    lotes_seguimiento = pd.read_sql_query(
        "SELECT COUNT(*) as total FROM trazabilidad WHERE estado_seguimiento = 'EN_TRANSITO'", 
        conn
    )
    
    with col1:
        st.metric("🟢 Productos Aprobados Hoy", productos_aprobados['total'].iloc[0])
    
    with col2:
        st.metric("📋 Auditorías Pendientes", auditorias_pendientes['total'].iloc[0])
    
    with col3:
        st.metric("⚠️ No Conformidades Abiertas", nc_abiertas['total'].iloc[0])
    
    with col4:
        st.metric("📦 Lotes en Seguimiento", lotes_seguimiento['total'].iloc[0])
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Resultados de Control de Calidad")
        calidad_df = pd.read_sql_query("SELECT resultado_general, COUNT(*) as cantidad FROM control_calidad GROUP BY resultado_general", conn)
        if not calidad_df.empty:
            fig = px.pie(calidad_df, values='cantidad', names='resultado_general', 
                        title='Distribución de Resultados de Calidad',
                        color_discrete_map={'APROBADO': '#48bb78', 'RECHAZADO': '#e53e3e', 'OBSERVADO': '#ed8936'})
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Puntuaciones de Auditorías")
        audit_df = pd.read_sql_query("SELECT area_auditada, AVG(puntuacion_total) as promedio FROM auditorias GROUP BY area_auditada", conn)
        if not audit_df.empty:
            fig2 = px.bar(audit_df, x='area_auditada', y='promedio', 
                         title='Puntuación Promedio por Área',
                         color='promedio', color_continuous_scale='RdYlGn')
            st.plotly_chart(fig2, use_container_width=True)
    
    conn.close()
    
    st.markdown("---")
    st.markdown("### 📋 Información del Sistema TPS de Calidad")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🎯 Tipo de TPS:** Sistema de Procesamiento de Transacciones para Control de Calidad Agroindustrial
        
        **📈 Importancia:**
        - ✅ Garantizar la calidad de productos agrícolas de exportación
        - ✅ Cumplimiento de normativas internacionales (Global GAP, HACCP, Organic)
        - ✅ Trazabilidad completa desde campo hasta cliente final
        - ✅ Gestión proactiva de riesgos de calidad
        - ✅ Optimización de procesos de certificación
        """)
    
    with col2:
        st.markdown("""
        **🔧 Tecnologías Utilizadas:**
        - 🐍 Python + Streamlit (Interfaz de usuario)
        - 🗄️ SQLite (Base de datos transaccional)
        - 📊 Pandas (Análisis de datos de calidad)
        - 📈 Plotly (Visualización de métricas)
        
        **🏢 Áreas Impactadas:**
        - 🔬 Control de Calidad
        - 🌱 Producción Agrícola
        - 📦 Exportaciones
        - 📜 Certificaciones
        """)

elif modulo == "🔬 Control de Calidad":
    st.title("🔬 Módulo de Control de Calidad")
    
    tab1, tab2, tab3 = st.tabs(["📝 Registrar Control", "🔍 Consultar Controles", "📊 Reportes de Calidad"])
    
    with tab1:
        st.subheader("📝 Registrar Nuevo Control de Calidad")
        
        with st.form("form_control_calidad"):
            col1, col2 = st.columns(2)
            
            with col1:
                lote_producto = st.text_input("Código de Lote *", placeholder="LT-ESP-001")
                tipo_producto = st.selectbox("Tipo de Producto *", 
                    ["Espárragos", "Paltas", "Arándanos", "Uvas", "Mangos", "Alcachofas"])
                variedad = st.text_input("Variedad", placeholder="UC-157, Hass, Biloxi...")
                parametros_fisicos = st.text_area("Parámetros Físicos", 
                    placeholder="Ej: Longitud: 18cm, Peso: 180g, Firmeza: 8kg")
            
            with col2:
                parametros_quimicos = st.text_area("Parámetros Químicos",
                    placeholder="Ej: Brix: 6.2, pH: 6.8, Materia seca: 23%")
                parametros_microbiologicos = st.text_area("Parámetros Microbiológicos",
                    placeholder="Ej: Coliformes: <10 UFC/g, Salmonella: Ausente")
                resultado_general = st.selectbox("Resultado General *", 
                    ["APROBADO", "RECHAZADO", "OBSERVADO"])
                inspector = st.text_input("Inspector Responsable *", placeholder="Nombre del inspector")
            
            observaciones = st.text_area("Observaciones", placeholder="Comentarios adicionales...")
            estado_aprobacion = st.selectbox("Estado de Aprobación", 
                ["APROBADO", "PENDIENTE", "RECHAZADO"])
            fecha_vencimiento = st.date_input("Fecha de Vencimiento", 
                value=date.today() + timedelta(days=30))
            
            submitted = st.form_submit_button("🔬 Registrar Control de Calidad", use_container_width=True)
            
            if submitted:
                if lote_producto and tipo_producto and inspector:
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute('''
                            INSERT INTO control_calidad 
                            (fecha_control, lote_producto, tipo_producto, variedad, parametros_fisicos,
                             parametros_quimicos, parametros_microbiologicos, resultado_general, inspector,
                             observaciones, estado_aprobacion, fecha_vencimiento)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (date.today(), lote_producto, tipo_producto, variedad, parametros_fisicos,
                              parametros_quimicos, parametros_microbiologicos, resultado_general, inspector,
                              observaciones, estado_aprobacion, fecha_vencimiento))
                        conn.commit()
                        st.success("✅ Control de calidad registrado exitosamente!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error al registrar: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("❌ Por favor complete todos los campos obligatorios (*)")
    
    with tab2:
        st.subheader("🔍 Consultar Controles de Calidad")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_producto = st.selectbox("Filtrar por Producto", 
                ["Todos", "Espárragos", "Paltas", "Arándanos", "Uvas", "Mangos", "Alcachofas"])
        with col2:
            filtro_resultado = st.selectbox("Filtrar por Resultado", 
                ["Todos", "APROBADO", "RECHAZADO", "OBSERVADO"])
        with col3:
            filtro_fecha = st.date_input("Desde fecha", value=date.today() - timedelta(days=30))
        
        conn = get_connection()
        query = "SELECT * FROM control_calidad WHERE fecha_control >= ?"
        params = [filtro_fecha]
        
        if filtro_producto != "Todos":
            query += " AND tipo_producto = ?"
            params.append(filtro_producto)
        
        if filtro_resultado != "Todos":
            query += " AND resultado_general = ?"
            params.append(filtro_resultado)
        
        query += " ORDER BY fecha_control DESC"
        
        controles_df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not controles_df.empty:
            st.dataframe(controles_df, use_container_width=True, height=400)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📋 Total Controles", len(controles_df))
            with col2:
                aprobados = len(controles_df[controles_df['resultado_general'] == 'APROBADO'])
                st.metric("✅ Aprobados", aprobados)
            with col3:
                rechazados = len(controles_df[controles_df['resultado_general'] == 'RECHAZADO'])
                st.metric("❌ Rechazados", rechazados)
            with col4:
                tasa_aprobacion = (aprobados / len(controles_df) * 100) if len(controles_df) > 0 else 0
                st.metric("📊 Tasa Aprobación", f"{tasa_aprobacion:.1f}%")
        else:
            st.info("📋 No se encontraron controles con los filtros aplicados")
    
    with tab3:
        st.subheader("📊 Reportes de Calidad")
        
        conn = get_connection()
        controles_df = pd.read_sql_query("SELECT * FROM control_calidad", conn)
        conn.close()
        
        if not controles_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                calidad_producto = controles_df.groupby(['tipo_producto', 'resultado_general']).size().unstack(fill_value=0)
                fig = px.bar(calidad_producto, title='📊 Resultados de Calidad por Producto',
                           color_discrete_map={'APROBADO': '#48bb78', 'RECHAZADO': '#e53e3e', 'OBSERVADO': '#ed8936'})
                st.plotly_chart(fig, use_container_width=True)
                
                inspector_stats = controles_df.groupby('inspector').agg({
                    'resultado_general': lambda x: (x == 'APROBADO').mean() * 100
                }).round(1).reset_index()
                inspector_stats.columns = ['Inspector', 'Tasa_Aprobacion']
                
                fig3 = px.bar(inspector_stats, x='Inspector', y='Tasa_Aprobacion',
                            title='👨‍🔬 Performance por Inspector (%)',
                            color='Tasa_Aprobacion', color_continuous_scale='RdYlGn')
                st.plotly_chart(fig3, use_container_width=True)
            
            with col2:
                controles_df['fecha_control'] = pd.to_datetime(controles_df['fecha_control'])
                controles_df['mes'] = controles_df['fecha_control'].dt.to_period('M')
                tendencia = controles_df.groupby(['mes', 'resultado_general']).size().unstack(fill_value=0)
                tendencia.index = tendencia.index.astype(str)
                
                fig2 = px.line(tendencia, title='📈 Tendencia de Calidad en el Tiempo')
                st.plotly_chart(fig2, use_container_width=True)
                
                # Distribución por estado de aprobación
                estado_dist = controles_df['estado_aprobacion'].value_counts()
                fig4 = px.pie(values=estado_dist.values, names=estado_dist.index,
                            title='🔄 Estados de Aprobación')
                st.plotly_chart(fig4, use_container_width=True)

elif modulo == "📋 Trazabilidad":
    st.title("📋 Módulo de Trazabilidad y Certificaciones")
    
    tab1, tab2, tab3 = st.tabs(["📝 Registrar Trazabilidad", "🗺️ Seguimiento", "📜 Certificaciones"])
    
    with tab1:
        st.subheader("📝 Registrar Nueva Trazabilidad")
        
        with st.form("form_trazabilidad"):
            col1, col2 = st.columns(2)
            
            with col1:
                codigo_trazabilidad = st.text_input("Código de Trazabilidad *", placeholder="TRZ-ESP-001")
                lote_producto = st.text_input("Lote de Producto *", placeholder="LT-ESP-001")
                origen_campo = st.text_input("Origen - Campo *", placeholder="Campo Norte - Sector A")
                fecha_siembra = st.date_input("Fecha de Siembra")
                fecha_cosecha = st.date_input("Fecha de Cosecha")
            
            with col2:
                tratamientos_aplicados = st.text_area("Tratamientos Aplicados", 
                    placeholder="Fertilización orgánica, Control biológico...")
                certificaciones = st.multiselect("Certificaciones", 
                    ["Global GAP", "HACCP", "Organic", "Fair Trade", "BRC", "SQF"])
                destino_exportacion = st.text_input("Destino de Exportación", placeholder="Estados Unidos")
                cliente_final = st.text_input("Cliente Final", placeholder="Walmart USA")
                estado_seguimiento = st.selectbox("Estado de Seguimiento", 
                    ["PREPARACION", "EN_TRANSITO", "ENTREGADO", "DEVUELTO"])
            
            documentos_adjuntos = st.text_input("Documentos Adjuntos", 
                placeholder="Certificado_GlobalGAP.pdf")
            
            submitted = st.form_submit_button("📋 Registrar Trazabilidad", use_container_width=True)
            
            if submitted:
                if codigo_trazabilidad and lote_producto and origen_campo:
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute('''
                            INSERT INTO trazabilidad 
                            (codigo_trazabilidad, lote_producto, origen_campo, fecha_siembra, fecha_cosecha,
                             tratamientos_aplicados, certificaciones, destino_exportacion, cliente_final,
                             estado_seguimiento, documentos_adjuntos)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (codigo_trazabilidad, lote_producto, origen_campo, fecha_siembra, fecha_cosecha,
                              tratamientos_aplicados, ', '.join(certificaciones), destino_exportacion, 
                              cliente_final, estado_seguimiento, documentos_adjuntos))
                        conn.commit()
                        st.success("✅ Trazabilidad registrada exitosamente!")
                        st.balloons()
                    except sqlite3.IntegrityError:
                        st.error("❌ El código de trazabilidad ya existe")
                    except Exception as e:
                        st.error(f"❌ Error al registrar: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("❌ Por favor complete todos los campos obligatorios (*)")
    
    with tab2:
    st.subheader("🗺️ Seguimiento de Lotes")

    conn = get_connection()
    trazabilidad_df = pd.read_sql_query("SELECT * FROM trazabilidad ORDER BY fecha_cosecha DESC", conn)
    conn.close()

    if not trazabilidad_df.empty:

        estado_filtro = st.selectbox("🔍 Filtrar por Estado", ["Todos"] + list(trazabilidad_df['estado_seguimiento'].unique()))
        if estado_filtro != "Todos":
            df_filtrado = trazabilidad_df[trazabilidad_df['estado_seguimiento'] == estado_filtro]
        else:
            df_filtrado = trazabilidad_df


        st.dataframe(df_filtrado, use_container_width=True, height=400)


        st.subheader("✏️ Editar o Eliminar Registro")
        selected_row = st.selectbox("Selecciona un Código de Trazabilidad", df_filtrado['codigo_trazabilidad'].unique())

        registro = trazabilidad_df[trazabilidad_df['codigo_trazabilidad'] == selected_row].iloc[0]

        with st.form("form_editar_trazabilidad"):
            col1, col2 = st.columns(2)

            with col1:
                lote_producto = st.text_input("Lote de Producto", value=registro['lote_producto'])
                origen_campo = st.text_input("Origen - Campo", value=registro['origen_campo'])
                fecha_siembra = st.date_input("Fecha de Siembra", value=pd.to_datetime(registro['fecha_siembra']))
                fecha_cosecha = st.date_input("Fecha de Cosecha", value=pd.to_datetime(registro['fecha_cosecha']))

            with col2:
                tratamientos = st.text_area("Tratamientos Aplicados", value=registro['tratamientos_aplicados'])
                certificaciones = st.multiselect("Certificaciones", 
                    ["Global GAP", "HACCP", "Organic", "Fair Trade", "BRC", "SQF"],
                    default=registro['certificaciones'].split(', ') if registro['certificaciones'] else [])
                destino = st.text_input("Destino Exportación", value=registro['destino_exportacion'])
                cliente = st.text_input("Cliente Final", value=registro['cliente_final'])
                estado = st.selectbox("Estado de Seguimiento", 
                    ["PREPARACION", "EN_TRANSITO", "ENTREGADO", "DEVUELTO"],
                    index=["PREPARACION", "EN_TRANSITO", "ENTREGADO", "DEVUELTO"].index(registro['estado_seguimiento']))

            documentos = st.text_input("Documentos Adjuntos", value=registro['documentos_adjuntos'])

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                actualizar = st.form_submit_button("💾 Actualizar")
            with col_btn2:
                eliminar = st.form_submit_button("🗑️ Eliminar")

            if actualizar:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE trazabilidad SET
                            lote_producto=?, origen_campo=?, fecha_siembra=?, fecha_cosecha=?,
                            tratamientos_aplicados=?, certificaciones=?, destino_exportacion=?,
                            cliente_final=?, estado_seguimiento=?, documentos_adjuntos=?
                        WHERE codigo_trazabilidad=?
                    ''', (lote_producto, origen_campo, fecha_siembra, fecha_cosecha,
                          tratamientos, ', '.join(certificaciones), destino, cliente,
                          estado, documentos, selected_row))
                    conn.commit()
                    st.success("✅ Registro actualizado correctamente.")
                except Exception as e:
                    st.error(f"❌ Error al actualizar: {e}")
                finally:
                    conn.close()

            if eliminar:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM trazabilidad WHERE codigo_trazabilidad = ?", (selected_row,))
                    conn.commit()
                    st.success("🗑️ Registro eliminado correctamente.")
                except Exception as e:
                    st.error(f"❌ Error al eliminar: {e}")
                finally:
                    conn.close()


        st.subheader("📈 Resumen de Estados de Lotes")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔄 En Preparación", len(df_filtrado[df_filtrado['estado_seguimiento'] == 'PREPARACION']))
        with col2:
            st.metric("🚛 En Tránsito", len(df_filtrado[df_filtrado['estado_seguimiento'] == 'EN_TRANSITO']))
        with col3:
            st.metric("✅ Entregado", len(df_filtrado[df_filtrado['estado_seguimiento'] == 'ENTREGADO']))
        with col4:
            st.metric("↩️ Devuelto", len(df_filtrado[df_filtrado['estado_seguimiento'] == 'DEVUELTO']))

    else:
        st.info("📋 No hay registros de trazabilidad aún.")


    
    with tab3:
        st.subheader("📜 Gestión de Certificaciones")
        
        conn = get_connection()
        trazabilidad_df = pd.read_sql_query("SELECT * FROM trazabilidad", conn)
        conn.close()
        
        if not trazabilidad_df.empty:
            cert_data = []
            for _, row in trazabilidad_df.iterrows():
                if row['certificaciones']:
                    certs = row['certificaciones'].split(', ')
                    for cert in certs:
                        cert_data.append({'certificacion': cert, 'lote': row['lote_producto']})
            
            if cert_data:
                cert_df = pd.DataFrame(cert_data)
                cert_count = cert_df.groupby('certificacion').size().reset_index(name='cantidad')
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(cert_count, x='certificacion', y='cantidad', 
                               title='📊 Distribución de Certificaciones por Lote',
                               color='cantidad', color_continuous_scale='Greens')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig2 = px.pie(cert_count, values='cantidad', names='certificacion',
                                title='📜 Proporción de Certificaciones')
                    st.plotly_chart(fig2, use_container_width=True)
                
       
                st.subheader("📊 Resumen de Certificaciones")
                st.dataframe(cert_count, use_container_width=True)

elif modulo == "🔍 Auditorías":
    st.title("🔍 Módulo de Auditorías e Inspecciones")
    
    tab1, tab2, tab3 = st.tabs(["📝 Registrar Auditoría", "🔍 Consultar Auditorías", "📊 Análisis de Hallazgos"])
    
    with tab1:
        st.subheader("📝 Registrar Nueva Auditoría")
        
        with st.form("form_auditoria"):
            col1, col2 = st.columns(2)
            
            with col1:
                tipo_auditoria = st.selectbox("Tipo de Auditoría *", 
                    ["Interna", "Externa", "Certificación", "Cliente", "Regulatoria"])
                area_auditada = st.selectbox("Área Auditada *", 
                    ["Producción", "Almacén", "Laboratorio", "Campo", "Empaque", "Administración"])
                auditor_responsable = st.text_input("Auditor Responsable *", placeholder="Nombre del auditor")
                norma_aplicada = st.selectbox("Norma Aplicada *", 
                    ["Global GAP", "HACCP", "BRC", "SQF", "Organic", "ISO 22000"])
            
            with col2:
                hallazgos_criticos = st.number_input("Hallazgos Críticos", min_value=0, value=0)
                hallazgos_mayores = st.number_input("Hallazgos Mayores", min_value=0, value=0)
                hallazgos_menores = st.number_input("Hallazgos Menores", min_value=0, value=0)
                puntuacion_total = st.number_input("Puntuación Total (%)", min_value=0.0, max_value=100.0, value=85.0)
            
            estado_auditoria = st.selectbox("Estado de Auditoría", 
                ["PROGRAMADA", "EN_PROCESO", "COMPLETADA", "PENDIENTE"])
            fecha_seguimiento = st.date_input("Fecha de Seguimiento")
            plan_accion = st.text_area("Plan de Acción", placeholder="Descripción del plan de acción...")
            
            submitted = st.form_submit_button("🔍 Registrar Auditoría", use_container_width=True)
            
            if submitted:
                if tipo_auditoria and area_auditada and auditor_responsable and norma_aplicada:
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute('''
                            INSERT INTO auditorias 
                            (fecha_auditoria, tipo_auditoria, area_auditada, auditor_responsable, norma_aplicada,
                             hallazgos_criticos, hallazgos_mayores, hallazgos_menores, puntuacion_total,
                             estado_auditoria, fecha_seguimiento, plan_accion)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (date.today(), tipo_auditoria, area_auditada, auditor_responsable, norma_aplicada,
                              hallazgos_criticos, hallazgos_mayores, hallazgos_menores, puntuacion_total,
                              estado_auditoria, fecha_seguimiento, plan_accion))
                        conn.commit()
                        st.success("✅ Auditoría registrada exitosamente!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error al registrar: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("❌ Por favor complete todos los campos obligatorios (*)")
    
    with tab2:
        st.subheader("🔍 Consultar Auditorías")
        
        conn = get_connection()
        auditorias_df = pd.read_sql_query("SELECT * FROM auditorias ORDER BY fecha_auditoria DESC", conn)
        conn.close()
        
        if not auditorias_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                filtro_tipo = st.selectbox("Filtrar por Tipo", 
                    ["Todos"] + list(auditorias_df['tipo_auditoria'].unique()))
            with col2:
                filtro_area = st.selectbox("Filtrar por Área", 
                    ["Todas"] + list(auditorias_df['area_auditada'].unique()))
            
            df_filtrado = auditorias_df.copy()
            if filtro_tipo != "Todos":
                df_filtrado = df_filtrado[df_filtrado['tipo_auditoria'] == filtro_tipo]
            if filtro_area != "Todas":
                df_filtrado = df_filtrado[df_filtrado['area_auditada'] == filtro_area]
            
            st.dataframe(df_filtrado, use_container_width=True, height=400)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📋 Total Auditorías", len(df_filtrado))
            with col2:
                puntuacion_promedio = df_filtrado['puntuacion_total'].mean()
                st.metric("📊 Puntuación Promedio", f"{puntuacion_promedio:.1f}%")
            with col3:
                hallazgos_totales = (df_filtrado['hallazgos_criticos'] + 
                                   df_filtrado['hallazgos_mayores'] + 
                                   df_filtrado['hallazgos_menores']).sum()
                st.metric("⚠️ Total Hallazgos", hallazgos_totales)
            with col4:
                completadas = len(df_filtrado[df_filtrado['estado_auditoria'] == 'COMPLETADA'])
                st.metric("✅ Completadas", completadas)
        else:
            st.info("🔍 No hay auditorías registradas")
    
    with tab3:
        st.subheader("📊 Análisis de Hallazgos")
        
        conn = get_connection()
        auditorias_df = pd.read_sql_query("SELECT * FROM auditorias", conn)
        conn.close()
        
        if not auditorias_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                hallazgos_data = {
                    'Tipo': ['Críticos', 'Mayores', 'Menores'],
                    'Cantidad': [
                        auditorias_df['hallazgos_criticos'].sum(),
                        auditorias_df['hallazgos_mayores'].sum(),
                        auditorias_df['hallazgos_menores'].sum()
                    ]
                }
                fig = px.bar(hallazgos_data, x='Tipo', y='Cantidad', 
                           title='⚠️ Distribución de Hallazgos',
                           color='Tipo', color_discrete_map={
                               'Críticos': '#e53e3e', 'Mayores': '#ed8936', 'Menores': '#48bb78'
                           })
                st.plotly_chart(fig, use_container_width=True)
                
                hallazgos_norma = auditorias_df.groupby('norma_aplicada').agg({
                    'hallazgos_criticos': 'sum',
                    'hallazgos_mayores': 'sum', 
                    'hallazgos_menores': 'sum'
                }).reset_index()
                
                fig3 = px.bar(hallazgos_norma, x='norma_aplicada', 
                            y=['hallazgos_criticos', 'hallazgos_mayores', 'hallazgos_menores'],
                            title='📋 Hallazgos por Norma')
                st.plotly_chart(fig3, use_container_width=True)
            
            with col2:
                puntuacion_area = auditorias_df.groupby('area_auditada')['puntuacion_total'].mean().reset_index()
                fig2 = px.bar(puntuacion_area, x='area_auditada', y='puntuacion_total',
                            title='🎯 Puntuación Promedio por Área',
                            color='puntuacion_total', color_continuous_scale='RdYlGn')
                st.plotly_chart(fig2, use_container_width=True)
                
                auditorias_df['fecha_auditoria'] = pd.to_datetime(auditorias_df['fecha_auditoria'])
                auditorias_df['mes'] = auditorias_df['fecha_auditoria'].dt.to_period('M')
                tendencia_punt = auditorias_df.groupby('mes')['puntuacion_total'].mean().reset_index()
                tendencia_punt['mes'] = tendencia_punt['mes'].astype(str)
                
                fig4 = px.line(tendencia_punt, x='mes', y='puntuacion_total',
                             title='📈 Tendencia de Puntuaciones', markers=True)
                st.plotly_chart(fig4, use_container_width=True)

elif modulo == "⚠️ No Conformidades":
    st.title("⚠️ Módulo de No Conformidades y Acciones Correctivas")
    
    tab1, tab2, tab3 = st.tabs(["📝 Registrar NC", "🔧 Gestión de NC", "📊 Análisis de Eficacia"])
    
    with tab1:
        st.subheader("📝 Registrar Nueva No Conformidad")
        
        with st.form("form_nc"):
            col1, col2 = st.columns(2)
            
            with col1:
                codigo_nc = st.text_input("Código de No Conformidad *", placeholder="NC-001")
                tipo_nc = st.selectbox("Tipo de No Conformidad *", 
                    ["Producto", "Proceso", "Sistema", "Documentación", "Personal"])
                area_afectada = st.selectbox("Área Afectada *", 
                    ["Producción", "Calidad", "Almacén", "Campo", "Laboratorio", "Administración"])
                descripcion_nc = st.text_area("Descripción de la No Conformidad *", 
                    placeholder="Descripción detallada del problema...")
            
            with col2:
                causa_raiz = st.text_area("Análisis de Causa Raíz", 
                    placeholder="Análisis de las causas que originaron la NC...")
                accion_inmediata = st.text_area("Acción Inmediata", 
                    placeholder="Acciones tomadas de forma inmediata...")
                accion_correctiva = st.text_area("Acción Correctiva", 
                    placeholder="Acciones para prevenir recurrencia...")
                responsable = st.text_input("Responsable *", placeholder="Nombre del responsable")
            
            fecha_cierre_programada = st.date_input("Fecha de Cierre Programada", 
                value=date.today() + timedelta(days=15))
            estado_nc = st.selectbox("Estado", ["ABIERTA", "EN_PROCESO", "CERRADA", "VERIFICADA"])
            
            submitted = st.form_submit_button("⚠️ Registrar No Conformidad", use_container_width=True)
            
            if submitted:
                if codigo_nc and tipo_nc and area_afectada and descripcion_nc and responsable:
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute('''
                            INSERT INTO no_conformidades 
                            (fecha_deteccion, codigo_nc, tipo_nc, area_afectada, descripcion_nc,
                             causa_raiz, accion_inmediata, accion_correctiva, responsable,
                             fecha_cierre_programada, estado_nc)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (date.today(), codigo_nc, tipo_nc, area_afectada, descripcion_nc,
                              causa_raiz, accion_inmediata, accion_correctiva, responsable,
                              fecha_cierre_programada, estado_nc))
                        conn.commit()
                        st.success("✅ No Conformidad registrada exitosamente!")
                        st.balloons()
                    except sqlite3.IntegrityError:
                        st.error("❌ El código de NC ya existe")
                    except Exception as e:
                        st.error(f"❌ Error al registrar: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("❌ Por favor complete todos los campos obligatorios (*)")
    
    with tab2:
        st.subheader("🔧 Gestión de No Conformidades")
        
        conn = get_connection()
        nc_df = pd.read_sql_query("SELECT * FROM no_conformidades ORDER BY fecha_deteccion DESC", conn)
        conn.close()
        
        if not nc_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                nc_abiertas = len(nc_df[nc_df['estado_nc'] == 'ABIERTA'])
                st.metric("🔴 NC Abiertas", nc_abiertas)
            
            with col2:
                nc_proceso = len(nc_df[nc_df['estado_nc'] == 'EN_PROCESO'])
                st.metric("🟡 NC en Proceso", nc_proceso)
            
            with col3:
                nc_cerradas = len(nc_df[nc_df['estado_nc'] == 'CERRADA'])
                st.metric("🟢 NC Cerradas", nc_cerradas)
            
            with col4:
                # Calcular NC vencidas
                nc_df['fecha_cierre_programada'] = pd.to_datetime(nc_df['fecha_cierre_programada'])
                nc_vencidas = len(nc_df[(nc_df['estado_nc'].isin(['ABIERTA', 'EN_PROCESO'])) & 
                                       (nc_df['fecha_cierre_programada'] < pd.Timestamp.now())])
                st.metric("⏰ NC Vencidas", nc_vencidas)
            
            st.subheader("📋 Lista de No Conformidades")
            
            filtro_estado = st.selectbox("Filtrar por Estado", 
                ["Todos", "ABIERTA", "EN_PROCESO", "CERRADA", "VERIFICADA"])
            
            if filtro_estado != "Todos":
                df_filtrado = nc_df[nc_df['estado_nc'] == filtro_estado]
            else:
                df_filtrado = nc_df
            
            st.dataframe(df_filtrado, use_container_width=True, height=400)
        else:
            st.info("⚠️ No hay no conformidades registradas")
    
    with tab3:
        st.subheader("📊 Análisis de Eficacia")
        
        conn = get_connection()
        nc_df = pd.read_sql_query("SELECT * FROM no_conformidades", conn)
        conn.close()
        
        if not nc_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                nc_tipo = nc_df.groupby('tipo_nc').size().reset_index(name='cantidad')
                fig = px.pie(nc_tipo, values='cantidad', names='tipo_nc', 
                           title='📊 Distribución de NC por Tipo')
                st.plotly_chart(fig, use_container_width=True)
                
                nc_estado = nc_df.groupby('estado_nc').size().reset_index(name='cantidad')
                fig3 = px.bar(nc_estado, x='estado_nc', y='cantidad',
                            title='🔄 NC por Estado',
                            color='estado_nc', color_discrete_map={
                                'ABIERTA': '#e53e3e', 'EN_PROCESO': '#ed8936', 
                                'CERRADA': '#48bb78', 'VERIFICADA': '#3182ce'
                            })
                st.plotly_chart(fig3, use_container_width=True)
            
            with col2:
                nc_area = nc_df.groupby('area_afectada').size().reset_index(name='cantidad')
                fig2 = px.bar(nc_area, x='area_afectada', y='cantidad',
                            title='🏢 NC por Área Afectada')
                st.plotly_chart(fig2, use_container_width=True)
                
                nc_cerradas = nc_df[nc_df['estado_nc'] == 'CERRADA'].copy()
                if not nc_cerradas.empty and 'fecha_cierre_real' in nc_cerradas.columns:
                    nc_cerradas['fecha_deteccion'] = pd.to_datetime(nc_cerradas['fecha_deteccion'])
                    nc_cerradas['fecha_cierre_real'] = pd.to_datetime(nc_cerradas['fecha_cierre_real'])
                    nc_cerradas['dias_cierre'] = (nc_cerradas['fecha_cierre_real'] - nc_cerradas['fecha_deteccion']).dt.days
                    
                    tiempo_area = nc_cerradas.groupby('area_afectada')['dias_cierre'].mean().reset_index()
                    fig4 = px.bar(tiempo_area, x='area_afectada', y='dias_cierre',
                                title='⏱️ Tiempo Promedio de Cierre (días)')
                    st.plotly_chart(fig4, use_container_width=True)
            
            st.subheader("📈 Tendencia de No Conformidades")
            nc_df['fecha_deteccion'] = pd.to_datetime(nc_df['fecha_deteccion'])
            nc_df['mes'] = nc_df['fecha_deteccion'].dt.to_period('M')
            tendencia_nc = nc_df.groupby('mes').size().reset_index(name='cantidad')
            tendencia_nc['mes'] = tendencia_nc['mes'].astype(str)
            
            fig5 = px.line(tendencia_nc, x='mes', y='cantidad',
                          title='📈 Tendencia Mensual de No Conformidades', markers=True)
            st.plotly_chart(fig5, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;'>
    <h4>🌱 TPS CALIDAD DANPER v1.0</h4>
    <p style='margin: 0; font-size: 0.8rem;'>Sistema de Procesamiento de Transacciones</p>
    <p style='margin: 0; font-size: 0.8rem;'>Control de Calidad Agroindustrial</p>
    <p style='margin: 0; font-size: 0.8rem;'>ISIA-103 - Sistemas Empresariales</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar.expander("ℹ️ Información del Sistema"):
    st.markdown("""
    **Módulos Implementados:**
    - 🔬 Control de Calidad
    - 📋 Trazabilidad
    - 🔍 Auditorías
    - ⚠️ No Conformidades
    
    **Certificaciones Soportadas:**
    - Global GAP
    - HACCP
    - Organic
    - Fair Trade
    - BRC
    - SQF
    
    **Estado:** Operativo ✅
    """)

with st.sidebar.expander("📊 Estadísticas del Sistema"):
    conn = get_connection()
    
    total_controles = pd.read_sql_query("SELECT COUNT(*) as total FROM control_calidad", conn)
    total_trazabilidad = pd.read_sql_query("SELECT COUNT(*) as total FROM trazabilidad", conn)
    total_auditorias = pd.read_sql_query("SELECT COUNT(*) as total FROM auditorias", conn)
    total_nc = pd.read_sql_query("SELECT COUNT(*) as total FROM no_conformidades", conn)
    
    st.metric("🔬 Controles", total_controles['total'].iloc[0])
    st.metric("📋 Trazabilidad", total_trazabilidad['total'].iloc[0])
    st.metric("🔍 Auditorías", total_auditorias['total'].iloc[0])
    st.metric("⚠️ No Conformidades", total_nc['total'].iloc[0])
    
    conn.close()
