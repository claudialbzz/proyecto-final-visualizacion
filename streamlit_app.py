# Importación de librerías necesarias
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import warnings
import os
warnings.filterwarnings('ignore')

# Configuración inicial de la página de Streamlit
st.set_page_config(
    page_title="Dashboard de Ventas - Empresa Alimentación",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# DISCLAIMER GLOBAL - Visible en todas las páginas
st.sidebar.markdown("---")
st.sidebar.warning("""
**⚠️ DISCLAIMER - DATOS DE MUESTRA**

Este dashboard utiliza una **muestra de registros** para demostración.

**Valores reales aproximados:**
- Registros totales: ~2,000,000
- Ventas totales: ~$150M - $200M
- Tiendas únicas: ~54
- Período: 2013-2017
- Estados: ~16

Los gráficos muestran tendencias correctas pero valores reducidos.
""")

# Función para cargar los datos locales
@st.cache_data
def load_local_data():
    try:
        # RUTAS CORREGIDAS - Los archivos están en la raíz
        ruta_parte_1 = "parte_1_muestra.csv"
        ruta_parte_2 = "parte_2_muestra.csv"
        
        st.sidebar.write("🔍 Buscando archivos CSV en la raíz...")
        
        # Verificar qué archivos CSV hay en la raíz
        archivos_csv = [f for f in os.listdir() if f.lower().endswith('.csv')]
        st.sidebar.write(f"Archivos CSV encontrados: {archivos_csv}")
        
        # Verificar si existen los archivos específicos
        archivos_necesarios = ["parte_1_muestra.csv", "parte_2_muestra.csv"]
        archivos_faltantes = [f for f in archivos_necesarios if not os.path.exists(f)]
        
        if archivos_faltantes:
            st.sidebar.error(f"❌ Archivos faltantes: {archivos_faltantes}")
            st.sidebar.info("Sugerencias de nombres encontrados:")
            for archivo in archivos_faltantes:
                similares = [f for f in archivos_csv if 'parte' in f.lower() or 'muestra' in f.lower()]
                if similares:
                    st.sidebar.write(f"  - Posibles coincidencias para '{archivo}': {similares}")
        
        # Cargar los archivos
        if os.path.exists(ruta_parte_1) and os.path.exists(ruta_parte_2):
            st.sidebar.write(f"📥 Cargando {ruta_parte_1}...")
            df1 = pd.read_csv(ruta_parte_1)
            
            st.sidebar.write(f"📥 Cargando {ruta_parte_2}...")
            df2 = pd.read_csv(ruta_parte_2)
        else:
            # Intentar con nombres alternativos
            st.sidebar.warning("Buscando nombres alternativos...")
            
            # Buscar cualquier archivo que contenga 'parte' o 'muestra'
            posibles_archivos = [f for f in archivos_csv if any(x in f.lower() for x in ['parte', 'muestra', 'sample', 'test'])]
            
            if len(posibles_archivos) >= 2:
                ruta_parte_1 = posibles_archivos[0]
                ruta_parte_2 = posibles_archivos[1]
                st.sidebar.info(f"Usando archivos: {ruta_parte_1} y {ruta_parte_2}")
                
                df1 = pd.read_csv(ruta_parte_1)
                df2 = pd.read_csv(ruta_parte_2)
            else:
                st.sidebar.error("No se encontraron archivos de muestra adecuados")
                return pd.DataFrame()
        
        # Mostrar información básica de los datos cargados
        st.sidebar.success(f"✅ {ruta_parte_1}: {len(df1)} filas, {df1.shape[1]} columnas")
        st.sidebar.success(f"✅ {ruta_parte_2}: {len(df2)} filas, {df2.shape[1]} columnas")
        
        # Concatenar
        df = pd.concat([df1, df2], ignore_index=True)
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip().str.lower()
        
        # Mostrar primeras filas para debug
        st.sidebar.write("📋 Primeras filas del dataframe combinado:")
        st.sidebar.write(df.head(3))
        
        # Mostrar columnas disponibles
        st.sidebar.write(f"📊 Columnas disponibles: {list(df.columns)}")
        
        # Verificar columnas esenciales
        columnas_requeridas = ['date', 'sales', 'store_nbr', 'family', 'state']
        columnas_presentes = [col for col in columnas_requeridas if col in df.columns]
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        
        st.sidebar.write(f"✅ Columnas presentes: {columnas_presentes}")
        
        if columnas_faltantes:
            st.sidebar.error(f"❌ Columnas faltantes: {columnas_faltantes}")
            # Mostrar columnas similares
            for col_faltante in columnas_faltantes:
                similares = [col for col in df.columns if col_faltante in col or col_faltante[:3] in col]
                if similares:
                    st.sidebar.info(f"  Posibles columnas para '{col_faltante}': {similares}")
        
        # Procesar fecha si existe
        if 'date' in df.columns:
            try:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                
                # Crear columnas temporales
                df['year'] = df['date'].dt.year
                df['month'] = df['date'].dt.month
                df['week'] = df['date'].dt.isocalendar().week
                df['quarter'] = df['date'].dt.quarter
                df['day_of_week'] = df['date'].dt.day_name()
                
                # Mostrar información de fechas
                fechas_validas = df['date'].notna().sum()
                st.sidebar.info(f"📅 Fechas válidas: {fechas_validas}/{len(df)}")
                st.sidebar.info(f"📅 Rango: {df['date'].min().date()} a {df['date'].max().date()}")
            except Exception as e:
                st.sidebar.error(f"Error procesando fechas: {e}")
        else:
            # Si no hay columna 'date', buscar alternativas
            date_cols = [col for col in df.columns if 'date' in col.lower() or 'fecha' in col.lower()]
            if date_cols:
                st.sidebar.info(f"Usando columna '{date_cols[0]}' como fecha")
                df['date'] = pd.to_datetime(df[date_cols[0]], errors='coerce')
                df['year'] = df['date'].dt.year
                df['month'] = df['date'].dt.month
                df['day_of_week'] = df['date'].dt.day_name()
        
        # Procesar columnas numéricas
        numeric_cols = ['sales', 'onpromotion', 'transactions', 'dcoilwtico']
        for col in numeric_cols:
            if col in df.columns:
                original_type = df[col].dtype
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].fillna(0)
                st.sidebar.write(f"  {col}: {original_type} → {df[col].dtype}")
            else:
                st.sidebar.warning(f"  Columna '{col}' no encontrada")
        
        # Mostrar estadísticas finales
        st.sidebar.success(f"🎉 Carga completada: {len(df)} registros totales")
        st.sidebar.success(f"💰 Ventas totales en muestra: ${df['sales'].sum():,.2f}")
        
        return df
        
    except Exception as e:
        st.sidebar.error(f"❌ Error al cargar los datos: {e}")
        import traceback
        st.sidebar.error(traceback.format_exc())
        return pd.DataFrame()

# Título principal
st.title("📊 Dashboard de Ventas - Empresa Alimentación")
st.markdown("---")

# Cargar datos con un botón
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.df = None

if not st.session_state.data_loaded:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Cargar Datos de Muestra", type="primary", use_container_width=True):
            with st.spinner("Cargando datos de muestra..."):
                df = load_local_data()
                
                if df is not None and not df.empty:
                    st.session_state.df = df
                    st.session_state.data_loaded = True
                    st.success("✅ Datos cargados exitosamente!")
                    st.rerun()
                else:
                    st.error("No se pudieron cargar los datos. Revisa los archivos CSV.")
    
    # Mostrar instrucciones
    with st.expander("📋 Instrucciones para cargar datos", expanded=True):
        st.markdown("""
        **Requisitos:**
        1. Asegúrate de tener los siguientes archivos en la raíz del proyecto:
           - `parte_1_muestra.csv`
           - `parte_2_muestra.csv`
        
        2. Los archivos deben tener las columnas requeridas:
           - `date` (fecha)
           - `sales` (ventas)
           - `store_nbr` (número de tienda)
           - `family` (familia de producto)
           - `state` (estado)
        
        **Si tienes problemas:**
        - Verifica los nombres de los archivos
        - Revisa que tengan extensión .csv
        - Comprueba el sidebar para mensajes de debug
        """)
    
    st.info("""
    ### Dashboard de Ventas - Versión de Muestra
    
    Este dashboard analiza datos de ventas de una empresa de alimentación.
    
    **Para comenzar, haz clic en 'Cargar Datos de Muestra' arriba.**
    
    *Nota: Se usan datos de muestra para demostración.*
    """)
    
    st.stop()

# Si los datos están cargados, continuar con la aplicación
df = st.session_state.df

# ===========================================
# SIDEBAR - NAVEGACIÓN PRINCIPAL
# ===========================================
st.sidebar.title("📊 Navegación")

# Selección de pestaña principal
pagina_seleccionada = st.sidebar.radio(
    "Selecciona una pestaña:",
    ["🏠 Visión Global", "🏪 Información por Tienda", "🗺️ Información por Estado", "🚀 Análisis Avanzado"]
)

# Información del dataset en el sidebar
st.sidebar.markdown("---")
st.sidebar.header("📈 Información de la Muestra")
st.sidebar.write(f"**Registros:** {len(df):,}")
if 'date' in df.columns:
    st.sidebar.write(f"**Período:** {df['date'].min().date()} al {df['date'].max().date()}")
if 'store_nbr' in df.columns:
    st.sidebar.write(f"**Tiendas:** {df['store_nbr'].nunique()}")
if 'state' in df.columns:
    st.sidebar.write(f"**Estados:** {df['state'].nunique()}")
if 'family' in df.columns:
    st.sidebar.write(f"**Familias:** {df['family'].nunique()}")
if 'sales' in df.columns:
    st.sidebar.write(f"**Ventas:** ${df['sales'].sum():,.2f}")

# ===========================================
# PÁGINA 1: VISIÓN GLOBAL
# ===========================================
if pagina_seleccionada == "🏠 Visión Global":
    st.title("📈 Visión Global de Ventas")
    
    with st.expander("⚠️ IMPORTANTE: Información sobre los datos de muestra", expanded=True):
        st.warning("""
        **DATOS DE DEMOSTRACIÓN (MUESTRA DE REGISTROS)**
        
        | Métrica | En muestra | Valor real aproximado |
        |---------|------------|----------------------|
        | Registros totales | ~2,000 | ~2,000,000 |
        | Ventas totales | ~$10K | ~$150M - $200M |
        | Tiendas | ~10-15 | 54 |
        
        **Los gráficos muestran patrones correctos, valores absolutos reducidos.**
        """)
    
    st.markdown("---")
    
    # Crear pestañas
    tab_global1, tab_global2, tab_global3 = st.tabs([
        "📊 Conteo General", 
        "📋 Análisis Productos", 
        "📅 Estacionalidad"
    ])
    
    with tab_global1:
        st.subheader("Conteo General")
        st.info("🔍 **Nota:** Conteos basados en muestra disponible")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'store_nbr' in df.columns:
                total_tiendas = df['store_nbr'].nunique()
                st.metric("Tiendas (muestra)", total_tiendas, help="Valor real: ~54 tiendas")
        
        with col2:
            if 'family' in df.columns:
                total_productos = df['family'].nunique()
                st.metric("Familias", total_productos)
        
        with col3:
            if 'state' in df.columns:
                total_estados = df['state'].nunique()
                st.metric("Estados", total_estados, help="Valor real: ~16 estados")
        
        with col4:
            if 'month' in df.columns:
                meses_unicos = df['month'].nunique()
                st.metric("Meses", meses_unicos)
        
        # Gráfico de distribución por estado
        if 'state' in df.columns and 'store_nbr' in df.columns:
            st.subheader("Distribución de Tiendas por Estado")
            
            tiendas_por_estado = df.groupby('state')['store_nbr'].nunique().reset_index()
            tiendas_por_estado = tiendas_por_estado.sort_values('store_nbr', ascending=False)
            
            if not tiendas_por_estado.empty:
                fig = px.bar(
                    tiendas_por_estado, 
                    x='state', 
                    y='store_nbr',
                    title="Tiendas por Estado (Muestra)",
                    labels={'store_nbr': 'Número de Tiendas', 'state': 'Estado'},
                    color='store_nbr'
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
    
    with tab_global2:
        st.subheader("Análisis de Productos")
        
        if 'family' in df.columns and 'sales' in df.columns:
            st.subheader("Top Familias de Productos")
            
            ventas_por_familia = df.groupby('family')['sales'].sum().reset_index()
            ventas_por_familia = ventas_por_familia.sort_values('sales', ascending=False).head(10)
            
            if not ventas_por_familia.empty:
                fig = px.bar(
                    ventas_por_familia, 
                    y='family', 
                    x='sales',
                    orientation='h',
                    title="Top Familias por Ventas",
                    labels={'sales': 'Ventas ($)', 'family': 'Familia'},
                    color='sales'
                )
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
    
    with tab_global3:
        st.subheader("Estacionalidad")
        
        if 'day_of_week' in df.columns and 'sales' in df.columns:
            st.subheader("Ventas por Día de la Semana")
            
            ventas_por_dia = df.groupby('day_of_week')['sales'].mean().reset_index()
            
            if not ventas_por_dia.empty:
                # Ordenar días
                dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                ventas_por_dia['day_of_week'] = pd.Categorical(ventas_por_dia['day_of_week'], 
                                                              categories=dias_orden, ordered=True)
                ventas_por_dia = ventas_por_dia.sort_values('day_of_week')
                
                fig = px.bar(
                    ventas_por_dia, 
                    x='day_of_week', 
                    y='sales',
                    title="Ventas Promedio por Día",
                    labels={'sales': 'Ventas Promedio ($)', 'day_of_week': 'Día'}
                )
                st.plotly_chart(fig, use_container_width=True)

# ===========================================
# PÁGINA 2: INFORMACIÓN POR TIENDA
# ===========================================
elif pagina_seleccionada == "🏪 Información por Tienda":
    st.title("🏪 Información por Tienda")
    
    if 'store_nbr' in df.columns:
        tiendas_disponibles = sorted(df['store_nbr'].unique())
        
        if len(tiendas_disponibles) > 0:
            st.subheader("Selecciona una tienda:")
            tienda_seleccionada = st.selectbox(
                "Tienda:",
                tiendas_disponibles
            )
            
            df_tienda = df[df['store_nbr'] == tienda_seleccionada]
            
            if not df_tienda.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Registros", len(df_tienda))
                    if 'sales' in df_tienda.columns:
                        st.metric("Ventas Totales", f"${df_tienda['sales'].sum():,.2f}")
                
                with col2:
                    if 'city' in df_tienda.columns:
                        st.metric("Ciudad", df_tienda['city'].iloc[0])
                    if 'state' in df_tienda.columns:
                        st.metric("Estado", df_tienda['state'].iloc[0])
            else:
                st.info("No hay datos para esta tienda en la muestra")
        else:
            st.warning("No hay datos de tiendas en la muestra")
    else:
        st.error("No se encontró la columna 'store_nbr' en los datos")

# ===========================================
# PÁGINA 3: INFORMACIÓN POR ESTADO
# ===========================================
elif pagina_seleccionada == "🗺️ Información por Estado":
    st.title("🗺️ Información por Estado")
    
    if 'state' in df.columns:
        estados_disponibles = sorted(df['state'].unique())
        
        if len(estados_disponibles) > 0:
            st.subheader("Selecciona un estado:")
            estado_seleccionado = st.selectbox(
                "Estado:",
                estados_disponibles
            )
            
            df_estado = df[df['state'] == estado_seleccionado]
            
            if not df_estado.empty:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Registros", len(df_estado))
                
                with col2:
                    if 'store_nbr' in df_estado.columns:
                        st.metric("Tiendas", df_estado['store_nbr'].nunique())
                
                with col3:
                    if 'sales' in df_estado.columns:
                        st.metric("Ventas", f"${df_estado['sales'].sum():,.2f}")
            else:
                st.info("No hay datos para este estado en la muestra")
        else:
            st.warning("No hay datos de estados en la muestra")
    else:
        st.error("No se encontró la columna 'state' en los datos")

# ===========================================
# PÁGINA 4: ANÁLISIS AVANZADO
# ===========================================
else:  # "🚀 Análisis Avanzado"
    st.title("🚀 Análisis Avanzado")
    
    st.info("""
    **Con datos completos se podrían realizar análisis como:**
    - Modelado predictivo de ventas
    - Análisis de correlaciones
    - Segmentación de clientes
    - Optimización de inventario
    """)
    
    # Ejemplo simple con datos disponibles
    if 'sales' in df.columns and 'date' in df.columns:
        st.subheader("Tendencia de Ventas (Muestra)")
        
        # Agrupar por mes
        df_tendencia = df.copy()
        df_tendencia['mes'] = df_tendencia['date'].dt.to_period('M').astype(str)
        ventas_mensuales = df_tendencia.groupby('mes')['sales'].sum().reset_index()
        
        if len(ventas_mensuales) > 1:
            fig = px.line(
                ventas_mensuales,
                x='mes',
                y='sales',
                title="Ventas Mensuales",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)

# ===========================================
# PIE DE PÁGINA
# ===========================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 📝 Desarrollado por Claudia Maria Lopez Bombin")
st.sidebar.markdown("**Dashboard de Muestra**")

st.markdown("---")
st.caption("Dashboard desarrollado para análisis de datos de ventas - Versión con datos de muestra")
