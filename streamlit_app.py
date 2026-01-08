# Importación de librerías necesarias
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import warnings
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

# Función para cargar los datos
@st.cache_data
def load_data():
    try:
        # CORRECCIÓN: Agregar extensión .csv a los nombres de archivo
        df1 = pd.read_csv('parte_1_muestra.csv')
        df2 = pd.read_csv('parte_2_muestra.csv')
        
        # Mostrar información de las columnas para debug
        st.sidebar.write("✅ Columnas en df1:", list(df1.columns))
        st.sidebar.write("✅ Columnas en df2:", list(df2.columns))

        df = pd.concat([df1, df2], ignore_index=True)

        # ELIMINAR LA COLUMNA VACÍA "Unnamed: 0" si existe
        if 'Unnamed: 0' in df.columns:
            df = df.drop(columns=['Unnamed: 0'])
        
        # Limpiar nombres de columnas (convertir a minúsculas y quitar espacios)
        df.columns = df.columns.str.strip().str.lower()
        
        # Mostrar columnas después de limpiar
        st.sidebar.write("📊 Columnas después de limpiar:", list(df.columns))

        # Verificar si la columna 'date' existe
        if 'date' not in df.columns:
            st.sidebar.warning(f"La columna 'date' no existe. Columnas disponibles: {list(df.columns)}")
            # Buscar columnas similares
            date_cols = [col for col in df.columns if 'date' in col.lower() or 'fecha' in col.lower()]
            if date_cols:
                st.sidebar.info(f"Columnas que podrían contener fechas: {date_cols}")
                # Usar la primera columna que parezca ser de fecha
                df.rename(columns={date_cols[0]: 'date'}, inplace=True)
            else:
                return pd.DataFrame()

        # Convertir date a datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Crear columnas de fecha si no existen
        if 'year' not in df.columns:
            df['year'] = df['date'].dt.year
        if 'month' not in df.columns:
            df['month'] = df['date'].dt.month
        if 'week' not in df.columns:
            df['week'] = df['date'].dt.isocalendar().week
        if 'quarter' not in df.columns:
            df['quarter'] = df['date'].dt.quarter
        if 'day_of_week' not in df.columns:
            df['day_of_week'] = df['date'].dt.day_name()

        # Columnas numéricas - con manejo mejorado de NaN
        numeric_cols = ['sales', 'onpromotion', 'transactions', 'dcoilwtico']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Rellenar NaN con 0 para evitar problemas en gráficos
                if col in ['sales', 'onpromotion', 'transactions']:
                    df[col] = df[col].fillna(0)
            else:
                st.sidebar.warning(f"Advertencia: La columna '{col}' no existe en los datos")

        # Verificar datos cargados
        st.sidebar.success(f"✅ Datos cargados exitosamente: {len(df)} registros")
        st.sidebar.info(f"📅 Rango de fechas: {df['date'].min().date()} a {df['date'].max().date()}")
        
        return df

    except FileNotFoundError as e:
        st.error(f"❌ Archivo no encontrado: {e}")
        st.info("""
        **Solución de problemas:**
        1. Verifica que los archivos estén en la misma carpeta
        2. Los nombres deben ser exactamente:
           - parte_1_muestra.csv
           - parte_2_muestra.csv
        3. Asegúrate de que tengan extensión .csv
        """)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame()

# Cargar los datos
df = load_data()

# Verificar que los datos se cargaron correctamente
if df.empty:
    st.error("No se pudieron cargar los datos. Por favor, verifica los archivos CSV.")
    st.stop()

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
st.sidebar.write(f"**Registros en muestra:** {len(df):,}")
if 'date' in df.columns and not df['date'].isna().all():
    st.sidebar.write(f"**Período:** {df['date'].min().date()} al {df['date'].max().date()}")
if 'store_nbr' in df.columns:
    st.sidebar.write(f"**Tiendas en muestra:** {df['store_nbr'].nunique()}")
if 'state' in df.columns:
    st.sidebar.write(f"**Estados en muestra:** {df['state'].nunique()}")
if 'family' in df.columns:
    st.sidebar.write(f"**Familias en muestra:** {df['family'].nunique()}")
if 'sales' in df.columns:
    st.sidebar.write(f"**Ventas en muestra:** ${df['sales'].sum():,.2f}")

# ===========================================
# PÁGINA 1: VISIÓN GLOBAL
# ===========================================
if pagina_seleccionada == "🏠 Visión Global":
    st.title("📈 Visión Global de Ventas")
    st.markdown("---")
    
    # Crear pestañas dentro de la primera sección
    tab_global1, tab_global2, tab_global3 = st.tabs([
        "📊 Conteo General", 
        "📋 Análisis en Términos Medios", 
        "📅 Estacionalidad"
    ])
    
    # ===========================================
    # 1a. CONTEO GENERAL
    # ===========================================
    with tab_global1:
        st.subheader("Conteo General de Métricas Clave")
        
        # Crear 4 columnas para mostrar las métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'store_nbr' in df.columns:
                total_tiendas = df['store_nbr'].nunique()
                st.metric("Número Total de Tiendas", total_tiendas, help="Valor real: ~54 tiendas")
        
        with col2:
            if 'family' in df.columns:
                total_productos = df['family'].nunique()
                st.metric("Familias de Productos", total_productos)
        
        with col3:
            if 'state' in df.columns:
                total_estados = df['state'].nunique()
                st.metric("Estados Operativos", total_estados, help="Valor real: ~16 estados")
        
        with col4:
            if 'month' in df.columns:
                meses_unicos = df['month'].nunique()
                st.metric("Meses con Datos", meses_unicos)
        
        # Gráfico adicional: Distribución de tiendas por estado
        st.subheader("Distribución de Tiendas por Estado")
        
        if 'state' in df.columns and 'store_nbr' in df.columns:
            tiendas_por_estado = df.groupby('state')['store_nbr'].nunique().reset_index()
            tiendas_por_estado = tiendas_por_estado.sort_values('store_nbr', ascending=False)
            
            if not tiendas_por_estado.empty:
                fig = px.bar(
                    tiendas_por_estado, 
                    x='state', 
                    y='store_nbr',
                    title="Número de Tiendas por Estado (Muestra)",
                    labels={'store_nbr': 'Número de Tiendas', 'state': 'Estado'},
                    color='store_nbr',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
    
    # ===========================================
    # 1b. ANÁLISIS EN TÉRMINOS MEDIOS
    # ===========================================
    with tab_global2:
        st.subheader("Análisis en Términos Medios")
        
        # Crear pestañas para los diferentes análisis
        analisis_tab1, analisis_tab2, analisis_tab3 = st.tabs([
            "📈 Top 10 Productos Más Vendidos", 
            "🏪 Distribución de Ventas por Tienda", 
            "🏆 Top 10 Tiendas con Promociones"
        ])
        
        with analisis_tab1:
            st.subheader("Top 10 Productos Más Vendidos (por familia)")
            
            if 'family' in df.columns and 'sales' in df.columns:
                ventas_por_familia = df.groupby('family')['sales'].sum().reset_index()
                ventas_por_familia = ventas_por_familia.sort_values('sales', ascending=False).head(10)
                
                if not ventas_por_familia.empty:
                    fig = px.bar(
                        ventas_por_familia, 
                        y='family', 
                        x='sales',
                        orientation='h',
                        title="Top 10 Familias de Productos por Ventas Totales (Muestra)",
                        labels={'sales': 'Ventas Totales ($)', 'family': 'Familia de Producto'},
                        color='sales',
                        color_continuous_scale='Viridis'
                    )
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
        
        with analisis_tab2:
            st.subheader("Distribución de Ventas por Tienda")
            
            if 'store_nbr' in df.columns and 'sales' in df.columns:
                ventas_por_tienda = df.groupby('store_nbr')['sales'].sum().reset_index()
                
                if not ventas_por_tienda.empty:
                    fig = px.histogram(
                        ventas_por_tienda, 
                        x='sales',
                        nbins=20,  # Reducido para muestra
                        title="Distribución de Ventas Totales por Tienda (Muestra)",
                        labels={'sales': 'Ventas Totales ($)', 'count': 'Número de Tiendas'},
                        color_discrete_sequence=['#636EFA']
                    )
                    if ventas_por_tienda['sales'].mean() > 0:
                        fig.add_vline(x=ventas_por_tienda['sales'].mean(), line_dash="dash", 
                                     line_color="red", annotation_text="Media")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if ventas_por_tienda['sales'].mean() > 0:
                            st.metric("Media", f"${ventas_por_tienda['sales'].mean():,.2f}")
                    with col2:
                        if ventas_por_tienda['sales'].median() > 0:
                            st.metric("Mediana", f"${ventas_por_tienda['sales'].median():,.2f}")
                    with col3:
                        if ventas_por_tienda['sales'].max() > 0:
                            st.metric("Máximo", f"${ventas_por_tienda['sales'].max():,.2f}")
                    with col4:
                        st.metric("Mínimo", f"${ventas_por_tienda['sales'].min():,.2f}")
        
        with analisis_tab3:
            st.subheader("Top 10 Tiendas con Ventas en Promoción")
            
            if 'onpromotion' in df.columns and 'sales' in df.columns and 'store_nbr' in df.columns:
                ventas_promocion = df[df['onpromotion'] > 0]
                
                if not ventas_promocion.empty:
                    promocion_por_tienda = ventas_promocion.groupby('store_nbr')['sales'].sum().reset_index()
                    promocion_por_tienda = promocion_por_tienda.sort_values('sales', ascending=False).head(10)
                    
                    if not promocion_por_tienda.empty:
                        fig = px.bar(
                            promocion_por_tienda, 
                            x='store_nbr', 
                            y='sales',
                            title="Top 10 Tiendas por Ventas en Promoción (Muestra)",
                            labels={'sales': 'Ventas en Promoción ($)', 'store_nbr': 'Número de Tienda'},
                            color='sales',
                            color_continuous_scale='Reds'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        if df['sales'].sum() > 0:
                            ventas_totales = df['sales'].sum()
                            ventas_promocion_total = ventas_promocion['sales'].sum()
                            porcentaje_promocion = (ventas_promocion_total / ventas_totales) * 100
                            
                            st.metric("Porcentaje de Ventas en Promoción", f"{porcentaje_promocion:.2f}%")
                    else:
                        st.info("No hay suficientes datos de promoción para mostrar el top 10")
                else:
                    st.info("No hay ventas en promoción registradas en la muestra")
    
    # ===========================================
    # 1c. ANÁLISIS DE ESTACIONALIDAD
    # ===========================================
    with tab_global3:
        st.subheader("Análisis de Estacionalidad de Ventas")
        
        # Crear pestañas para los diferentes análisis de estacionalidad
        estacionalidad_tab1, estacionalidad_tab2, estacionalidad_tab3 = st.tabs([
            "📅 Día de la Semana", 
            "📈 Volumen Semanal", 
            "📊 Volumen Mensual"
        ])
        
        with estacionalidad_tab1:
            st.subheader("Ventas por Día de la Semana")
            
            if 'day_of_week' in df.columns and 'sales' in df.columns:
                dias_espanol = {
                    'Monday': 'Lunes',
                    'Tuesday': 'Martes',
                    'Wednesday': 'Miércoles',
                    'Thursday': 'Jueves',
                    'Friday': 'Viernes',
                    'Saturday': 'Sábado',
                    'Sunday': 'Domingo'
                }
                
                ventas_por_dia = df.groupby('day_of_week')['sales'].mean().reset_index()
                
                if not ventas_por_dia.empty:
                    orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    ventas_por_dia['day_of_week'] = pd.Categorical(ventas_por_dia['day_of_week'], categories=orden_dias, ordered=True)
                    ventas_por_dia = ventas_por_dia.sort_values('day_of_week')
                    ventas_por_dia['dia_espanol'] = ventas_por_dia['day_of_week'].map(dias_espanol)
                    
                    fig = px.bar(
                        ventas_por_dia, 
                        x='dia_espanol', 
                        y='sales',
                        title="Ventas Promedio por Día de la Semana (Muestra)",
                        labels={'sales': 'Ventas Promedio ($)', 'dia_espanol': 'Día de la Semana'},
                        color='sales',
                        color_continuous_scale='Greens'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if 'dia_espanol' in ventas_por_dia.columns:
                        dia_max_ventas = ventas_por_dia.loc[ventas_por_dia['sales'].idxmax(), 'dia_espanol']
                        st.info(f"**Día con más ventas en promedio:** {dia_max_ventas}")
        
        with estacionalidad_tab2:
            st.subheader("Volumen de Ventas Promedio por Semana del Año")
            
            if 'week' in df.columns and 'sales' in df.columns:
                ventas_por_semana = df.groupby('week')['sales'].mean().reset_index()
                
                if not ventas_por_semana.empty:
                    fig = px.line(
                        ventas_por_semana, 
                        x='week', 
                        y='sales',
                        title="Ventas Promedio por Semana del Año (Todos los Años) - Muestra",
                        labels={'sales': 'Ventas Promedio ($)', 'week': 'Semana del Año'},
                        markers=True
                    )
                    fig.update_traces(line=dict(color='blue', width=3))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if len(ventas_por_semana) > 1:
                        semana_max = ventas_por_semana.loc[ventas_por_semana['sales'].idxmax(), 'week']
                        semana_min = ventas_por_semana.loc[ventas_por_semana['sales'].idxmin(), 'week']
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Semana con Más Ventas", f"Semana {int(semana_max)}")
                        with col2:
                            st.metric("Semana con Menos Ventas", f"Semana {int(semana_min)}")
        
        with estacionalidad_tab3:
            st.subheader("Volumen de Ventas Promedio por Mes")
            
            if 'month' in df.columns and 'sales' in df.columns:
                meses_espanol = {
                    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
                }
                
                ventas_por_mes = df.groupby('month')['sales'].mean().reset_index()
                ventas_por_mes['mes_nombre'] = ventas_por_mes['month'].map(meses_espanol)
                ventas_por_mes = ventas_por_mes.sort_values('month')
                
                if not ventas_por_mes.empty:
                    fig = px.bar(
                        ventas_por_mes, 
                        x='mes_nombre', 
                        y='sales',
                        title="Ventas Promedio por Mes (Todos los Años) - Muestra",
                        labels={'sales': 'Ventas Promedio ($)', 'mes_nombre': 'Mes'},
                        color='sales',
                        color_continuous_scale='Purples'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if 'mes_nombre' in ventas_por_mes.columns:
                        mes_max_ventas = ventas_por_mes.loc[ventas_por_mes['sales'].idxmax(), 'mes_nombre']
                        st.info(f"**Mes con más ventas en promedio:** {mes_max_ventas}")

# ===========================================
# PÁGINA 2: INFORMACIÓN POR TIENDA
# ===========================================
elif pagina_seleccionada == "🏪 Información por Tienda":
    st.title("🏪 Información por Tienda")
    st.markdown("---")
    
    # Selector de tienda en la página principal (no en sidebar)
    if 'store_nbr' in df.columns:
        tiendas_unicas = sorted(df['store_nbr'].unique())
        
        if len(tiendas_unicas) > 0:
            st.subheader("Selecciona una tienda para visualizar sus datos:")
            
            tienda_seleccionada = st.selectbox(
                "Tienda:",
                tiendas_unicas,
                key="selector_tienda_pagina2"
            )
            
            # Filtrar datos para la tienda seleccionada
            df_tienda = df[df['store_nbr'] == tienda_seleccionada]
            
            if not df_tienda.empty:
                # Obtener información de la tienda (con verificación de columnas)
                estado_tienda = df_tienda['state'].iloc[0] if 'state' in df_tienda.columns else "N/A"
                ciudad_tienda = df_tienda['city'].iloc[0] if 'city' in df_tienda.columns else "N/A"
                tipo_tienda = df_tienda['store_type'].iloc[0] if 'store_type' in df_tienda.columns else "N/A"
                
                # Mostrar información de la tienda
                st.header(f"Tienda {tienda_seleccionada} (Muestra)")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Número de Tienda", tienda_seleccionada)
                with col2:
                    st.metric("Estado", estado_tienda)
                with col3:
                    st.metric("Ciudad", ciudad_tienda)
                with col4:
                    st.metric("Tipo de Tienda", tipo_tienda)
                
                st.markdown("---")
                
                # Crear gráficos para la tienda seleccionada
                col_chart1, col_chart2, col_chart3 = st.columns(3)
                
                with col_chart1:
                    if 'year' in df_tienda.columns and 'sales' in df_tienda.columns:
                        st.subheader("Ventas Totales por Año")
                        
                        ventas_por_anio = df_tienda.groupby('year')['sales'].sum().reset_index()
                        ventas_por_anio = ventas_por_anio.sort_values('year')
                        
                        if not ventas_por_anio.empty:
                            fig = px.bar(
                                ventas_por_anio, 
                                x='year', 
                                y='sales',
                                title=f"Ventas Totales por Año - Tienda {tienda_seleccionada}",
                                labels={'sales': 'Ventas Totales ($)', 'year': 'Año'},
                                color='sales',
                                color_continuous_scale='Blues'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                
                with col_chart2:
                    if 'year' in df_tienda.columns and 'transactions' in df_tienda.columns:
                        st.subheader("Transacciones por Año")
                        
                        transacciones_por_anio = df_tienda.groupby('year')['transactions'].sum().reset_index()
                        transacciones_por_anio = transacciones_por_anio.sort_values('year')
                        
                        if not transacciones_por_anio.empty:
                            fig = px.line(
                                transacciones_por_anio, 
                                x='year', 
                                y='transactions',
                                title=f"Transacciones por Año - Tienda {tienda_seleccionada}",
                                labels={'transactions': 'Número de Transacciones', 'year': 'Año'},
                                markers=True
                            )
                            fig.update_traces(line=dict(color='green', width=3))
                            st.plotly_chart(fig, use_container_width=True)
                
                with col_chart3:
                    if 'onpromotion' in df_tienda.columns and 'sales' in df_tienda.columns and 'year' in df_tienda.columns:
                        st.subheader("Ventas en Promoción por Año")
                        
                        ventas_promocion_tienda = df_tienda[df_tienda['onpromotion'] > 0]
                        
                        if not ventas_promocion_tienda.empty:
                            promocion_por_anio = ventas_promocion_tienda.groupby('year')['sales'].sum().reset_index()
                            promocion_por_anio = promocion_por_anio.sort_values('year')
                            
                            if not promocion_por_anio.empty:
                                fig = px.bar(
                                    promocion_por_anio, 
                                    x='year', 
                                    y='sales',
                                    title=f"Ventas en Promoción por Año - Tienda {tienda_seleccionada}",
                                    labels={'sales': 'Ventas en Promoción ($)', 'year': 'Año'},
                                    color='sales',
                                    color_continuous_scale='Reds'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("No hay ventas en promoción registradas por año.")
                        else:
                            st.info("No hay ventas en promoción registradas.")
                
                # Análisis adicional: Ventas por familia de producto en esta tienda
                if 'family' in df_tienda.columns and 'sales' in df_tienda.columns:
                    st.subheader(f"Distribución de Ventas por Familia de Producto - Tienda {tienda_seleccionada}")
                    
                    ventas_familia_tienda = df_tienda.groupby('family')['sales'].sum().reset_index()
                    ventas_familia_tienda = ventas_familia_tienda.sort_values('sales', ascending=False).head(10)
                    
                    if not ventas_familia_tienda.empty:
                        fig = px.pie(
                            ventas_familia_tienda, 
                            values='sales', 
                            names='family',
                            title=f"Top 10 Familias de Producto - Tienda {tienda_seleccionada}",
                            hole=0.4
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
            
            else:
                st.warning(f"No se encontraron datos para la tienda {tienda_seleccionada} en la muestra")
        else:
            st.warning("No hay datos de tiendas en la muestra")
    else:
        st.error("No se encontró la columna 'store_nbr' en los datos")

# ===========================================
# PÁGINA 3: INFORMACIÓN POR ESTADO
# ===========================================
elif pagina_seleccionada == "🗺️ Información por Estado":
    st.title("🗺️ Información por Estado")
    st.markdown("---")
    
    # Selector de estado en la página principal
    if 'state' in df.columns:
        estados_unicos = sorted(df['state'].unique())
        
        if len(estados_unicos) > 0:
            st.subheader("Selecciona un estado para visualizar sus datos:")
            
            estado_seleccionado = st.selectbox(
                "Estado:",
                estados_unicos,
                key="selector_estado_pagina3"
            )
            
            # Filtrar datos para el estado seleccionado
            df_estado = df[df['state'] == estado_seleccionado]
            
            if not df_estado.empty:
                # Mostrar información del estado
                num_tiendas_estado = df_estado['store_nbr'].nunique() if 'store_nbr' in df_estado.columns else 0
                num_ciudades_estado = df_estado['city'].nunique() if 'city' in df_estado.columns else 0
                ventas_totales_estado = df_estado['sales'].sum() if 'sales' in df_estado.columns else 0
                
                st.header(f"Estado: {estado_seleccionado} (Muestra)")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Número de Tiendas", num_tiendas_estado)
                with col2:
                    st.metric("Número de Ciudades", num_ciudades_estado)
                with col3:
                    st.metric("Ventas Totales", f"${ventas_totales_estado:,.2f}")
                
                st.markdown("---")
                
                # Crear gráficos para el estado seleccionado
                col_estado1, col_estado2, col_estado3 = st.columns(3)
                
                with col_estado1:
                    if 'year' in df_estado.columns and 'transactions' in df_estado.columns:
                        st.subheader("Transacciones por Año")
                        
                        transacciones_por_anio_estado = df_estado.groupby('year')['transactions'].sum().reset_index()
                        transacciones_por_anio_estado = transacciones_por_anio_estado.sort_values('year')
                        
                        if not transacciones_por_anio_estado.empty:
                            fig = px.bar(
                                transacciones_por_anio_estado, 
                                x='year', 
                                y='transactions',
                                title=f"Transacciones por Año - {estado_seleccionado}",
                                labels={'transactions': 'Número de Transacciones', 'year': 'Año'},
                                color='transactions',
                                color_continuous_scale='Greens'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                
                with col_estado2:
                    if 'store_nbr' in df_estado.columns and 'sales' in df_estado.columns:
                        st.subheader("Top 5 Tiendas por Ventas")
                        
                        ventas_por_tienda_estado = df_estado.groupby('store_nbr')['sales'].sum().reset_index()
                        ventas_por_tienda_estado = ventas_por_tienda_estado.sort_values('sales', ascending=False).head(5)
                        
                        if not ventas_por_tienda_estado.empty:
                            fig = px.bar(
                                ventas_por_tienda_estado, 
                                x='store_nbr', 
                                y='sales',
                                title=f"Top 5 Tiendas - {estado_seleccionado}",
                                labels={'sales': 'Ventas Totales ($)', 'store_nbr': 'Número de Tienda'},
                                color='sales',
                                color_continuous_scale='Oranges'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                
                with col_estado3:
                    if 'family' in df_estado.columns and 'sales' in df_estado.columns:
                        st.subheader("Producto Más Vendido en el Estado")
                        
                        # Encontrar la familia de producto más vendida en el estado
                        producto_mas_vendido = df_estado.groupby('family')['sales'].sum().reset_index()
                        producto_mas_vendido = producto_mas_vendido.sort_values('sales', ascending=False).head(1)
                        
                        if not producto_mas_vendido.empty:
                            familia_top = producto_mas_vendido['family'].iloc[0]
                            ventas_top = producto_mas_vendido['sales'].iloc[0]
                            
                            # Mostrar el producto más vendido en un formato claro
                            st.markdown(f"### 🏆 {familia_top}")
                            st.markdown(f"**Ventas totales:** ${ventas_top:,.2f}")
                            
                            # Gráfico de indicador
                            fig = go.Figure(go.Indicator(
                                mode="number",
                                value=ventas_top,
                                number={'prefix': "$", 'valueformat': ",.0f"},
                                title={"text": f"Ventas totales<br>{familia_top}"},
                                domain={'x': [0, 1], 'y': [0, 1]}
                            ))
                            
                            fig.update_layout(
                                height=250,
                                paper_bgcolor="lightgray"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("No hay datos suficientes para determinar el producto más vendido.")
                
                # Análisis adicional: Mapa de calor de ventas por mes y año
                if 'year' in df_estado.columns and 'month' in df_estado.columns and 'sales' in df_estado.columns:
                    st.subheader(f"Mapa de Calor de Ventas por Mes y Año")
                    
                    ventas_mes_anio = df_estado.groupby(['year', 'month'])['sales'].sum().reset_index()
                    
                    if not ventas_mes_anio.empty:
                        tabla_pivote = ventas_mes_anio.pivot(index='month', columns='year', values='sales')
                        
                        if not tabla_pivote.empty:
                            fig = px.imshow(
                                tabla_pivote,
                                labels=dict(x="Año", y="Mes", color="Ventas ($)"),
                                title=f"Ventas por Mes y Año - {estado_seleccionado}",
                                aspect="auto",
                                color_continuous_scale="YlOrRd"
                            )
                            st.plotly_chart(fig, use_container_width=True)
            
            else:
                st.warning(f"No se encontraron datos para el estado {estado_seleccionado} en la muestra")
        else:
            st.warning("No hay datos de estados en la muestra")
    else:
        st.error("No se encontró la columna 'state' en los datos")

# ===========================================
# PÁGINA 4: ANÁLISIS AVANZADO
# ===========================================
else:  # "🚀 Análisis Avanzado"
    st.title("🚀 Análisis Avanzado")
    st.markdown("---")
    
    st.markdown("""
    ### ¡Sorpresa para el CEO y el Jefe de Ventas!
    Esta sección incluye análisis avanzados y visualizaciones innovadoras para facilitar la toma de decisiones.
    
    **Nota:** Estos análisis se basan en datos de muestra. Con los datos completos, los insights serían más precisos.
    """)
    
    # Crear pestañas para diferentes análisis avanzados
    tab_avanzado1, tab_avanzado2, tab_avanzado3, tab_avanzado4 = st.tabs([
        "📈 Análisis de Tendencia", 
        "🏪 Comparativa de Tiendas", 
        "📊 Efectividad de Promociones",
        "💡 Insights y Recomendaciones"
    ])
    
    with tab_avanzado1:
        st.subheader("Análisis de Tendencia de Ventas")
        
        if 'year' in df.columns and 'month' in df.columns and 'sales' in df.columns:
            ventas_mensuales = df.groupby(['year', 'month'])['sales'].sum().reset_index()
            
            if not ventas_mensuales.empty:
                ventas_mensuales['fecha'] = pd.to_datetime(ventas_mensuales['year'].astype(str) + '-' + ventas_mensuales['month'].astype(str) + '-01')
                ventas_mensuales = ventas_mensuales.sort_values('fecha')
                
                fig = px.line(
                    ventas_mensuales, 
                    x='fecha', 
                    y='sales',
                    title="Tendencia de Ventas Mensuales (Muestra)",
                    labels={'sales': 'Ventas Totales ($)', 'fecha': 'Fecha'},
                    markers=True
                )
                
                # Calcular y añadir línea de tendencia
                if len(ventas_mensuales) > 1:
                    z = np.polyfit(range(len(ventas_mensuales)), ventas_mensuales['sales'], 1)
                    p = np.poly1d(z)
                    ventas_mensuales['tendencia'] = p(range(len(ventas_mensuales)))
                    
                    fig.add_scatter(
                        x=ventas_mensuales['fecha'], 
                        y=ventas_mensuales['tendencia'], 
                        mode='lines',
                        name='Tendencia',
                        line=dict(color='red', dash='dash')
                    )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Análisis de crecimiento
                if len(ventas_mensuales) >= 2:
                    ultimo_mes = ventas_mensuales['sales'].iloc[-1]
                    primer_mes = ventas_mensuales['sales'].iloc[0]
                    
                    if primer_mes > 0:
                        crecimiento_total = ((ultimo_mes - primer_mes) / primer_mes) * 100
                        
                        st.metric("Crecimiento Total del Período (Muestra)", f"{crecimiento_total:.2f}%")
    
    with tab_avanzado2:
        st.subheader("Comparativa de Rendimiento entre Tiendas")
        
        if 'store_nbr' in df.columns:
            tiendas_unicas = sorted(df['store_nbr'].unique())
            
            if len(tiendas_unicas) > 0:
                tiendas_comparar = st.multiselect(
                    "Selecciona hasta 5 tiendas para comparar:",
                    tiendas_unicas,
                    default=tiendas_unicas[:min(3, len(tiendas_unicas))],
                    max_selections=5
                )
                
                if tiendas_comparar:
                    df_comparacion = df[df['store_nbr'].isin(tiendas_comparar)]
                    
                    if 'year' in df_comparacion.columns and 'month' in df_comparacion.columns and 'sales' in df_comparacion.columns:
                        ventas_mensuales_tienda = df_comparacion.groupby(['year', 'month', 'store_nbr'])['sales'].sum().reset_index()
                        
                        if not ventas_mensuales_tienda.empty:
                            ventas_mensuales_tienda['fecha'] = pd.to_datetime(ventas_mensuales_tienda['year'].astype(str) + '-' + ventas_mensuales_tienda['month'].astype(str) + '-01')
                            
                            fig = px.line(
                                ventas_mensuales_tienda, 
                                x='fecha', 
                                y='sales',
                                color='store_nbr',
                                title="Comparativa de Ventas Mensuales por Tienda (Muestra)",
                                labels={'sales': 'Ventas ($)', 'fecha': 'Fecha', 'store_nbr': 'Número de Tienda'},
                                markers=True
                            )
                            st.plotly_chart(fig, use_container_width=True)
    
    with tab_avanzado3:
        st.subheader("Análisis de Efectividad de Promociones")
        
        if 'sales' in df.columns and 'onpromotion' in df.columns:
            ventas_totales = df['sales'].sum()
            ventas_promocion = df[df['onpromotion'] > 0]['sales'].sum()
            
            if ventas_totales > 0:
                porcentaje_promocion = (ventas_promocion / ventas_totales) * 100
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Ventas Totales", f"${ventas_totales:,.2f}")
                with col2:
                    st.metric("Ventas en Promoción", f"${ventas_promocion:,.2f}")
                with col3:
                    st.metric("% de Ventas en Promoción", f"{porcentaje_promocion:.2f}%")
                
                # Análisis de qué productos se benefician más de las promociones
                if 'family' in df.columns:
                    st.subheader("Productos con Mayor Impacto de Promoción")
                    
                    ventas_familia_total = df.groupby('family')['sales'].sum().reset_index()
                    ventas_familia_promocion = df[df['onpromotion'] > 0].groupby('family')['sales'].sum().reset_index()
                    
                    if not ventas_familia_total.empty and not ventas_familia_promocion.empty:
                        ventas_familia = pd.merge(
                            ventas_familia_total, 
                            ventas_familia_promocion, 
                            on='family', 
                            suffixes=('_total', '_promocion'),
                            how='left'
                        ).fillna(0)
                        
                        if not ventas_familia.empty:
                            ventas_familia['porcentaje_promocion'] = (ventas_familia['sales_promocion'] / ventas_familia['sales_total']) * 100
                            
                            # Filtrar familias con ventas significativas
                            if ventas_familia['sales_total'].quantile(0.25) > 0:
                                ventas_familia_significativas = ventas_familia[ventas_familia['sales_total'] > ventas_familia['sales_total'].quantile(0.25)]
                                top_promocion = ventas_familia_significativas.sort_values('porcentaje_promocion', ascending=False).head(10)
                                
                                if not top_promocion.empty:
                                    fig = px.bar(
                                        top_promocion, 
                                        x='family', 
                                        y='porcentaje_promocion',
                                        title="Top Familias con Mayor % de Ventas en Promoción (Muestra)",
                                        labels={'porcentaje_promocion': '% de Ventas en Promoción', 'family': 'Familia de Producto'},
                                        color='porcentaje_promocion',
                                        color_continuous_scale='RdYlGn'
                                    )
                                    fig.update_layout(xaxis_tickangle=-45)
                                    st.plotly_chart(fig, use_container_width=True)
    
    with tab_avanzado4:
        st.subheader("💡 Insights Automáticos y Recomendaciones")
        
        # Generar insights automáticos
        st.info("""
        ### 📋 Insights Generados Automáticamente (basados en muestra):
        """)
        
        # Insight 1: Día con más ventas
        if 'day_of_week' in df.columns and 'sales' in df.columns:
            ventas_por_dia = df.groupby('day_of_week')['sales'].mean().reset_index()
            if not ventas_por_dia.empty:
                dia_max = ventas_por_dia.loc[ventas_por_dia['sales'].idxmax(), 'day_of_week']
                dias_espanol = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 
                               'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
                
                st.success(f"1. **Optimizar inventario los {dias_espanol.get(dia_max, dia_max)}**: Este día tiene las ventas promedio más altas.")
        
        # Insight 2: Producto más vendido
        if 'family' in df.columns and 'sales' in df.columns:
            producto_mas_vendido = df.groupby('family')['sales'].sum().reset_index()
            if not producto_mas_vendido.empty:
                producto_mas_vendido = producto_mas_vendido.sort_values('sales', ascending=False).head(1)
                st.success(f"2. **Enfocar estrategias en {producto_mas_vendido['family'].iloc[0]}**: Es la familia de productos con mayores ventas totales.")
        
        # Insight 3: Estado con más ventas
        if 'state' in df.columns and 'sales' in df.columns:
            estado_mas_ventas = df.groupby('state')['sales'].sum().reset_index()
            if not estado_mas_ventas.empty:
                estado_mas_ventas = estado_mas_ventas.sort_values('sales', ascending=False).head(1)
                st.success(f"3. **Expandir presencia en {estado_mas_ventas['state'].iloc[0]}**: Es el estado con mayores ventas totales.")
        
        # Insight 4: Efectividad de promociones
        if 'sales' in df.columns and 'onpromotion' in df.columns:
            ventas_totales = df['sales'].sum()
            if ventas_totales > 0:
                porcentaje_promocion = (df[df['onpromotion'] > 0]['sales'].sum() / df['sales'].sum()) * 100
                if porcentaje_promocion < 20:
                    st.warning(f"4. **Aumentar estrategias promocionales**: Solo el {porcentaje_promocion:.1f}% de las ventas provienen de promociones.")
                else:
                    st.success(f"4. **Mantener estrategias promocionales**: El {porcentaje_promocion:.1f}% de las ventas provienen de promociones.")
        
        # Insight 5: Tendencia de crecimiento
        if 'year' in df.columns and 'month' in df.columns and 'sales' in df.columns:
            ventas_mensuales = df.groupby(['year', 'month'])['sales'].sum().reset_index()
            if len(ventas_mensuales) >= 2:
                primer_valor = ventas_mensuales['sales'].iloc[0]
                if primer_valor > 0:
                    crecimiento = ((ventas_mensuales['sales'].iloc[-1] - primer_valor) / primer_valor) * 100
                    if crecimiento > 0:
                        st.success(f"5. **Crecimiento positivo**: Las ventas han crecido un {crecimiento:.1f}% durante el período analizado.")
                    else:
                        st.error(f"5. **Atención: decrecimiento**: Las ventas han disminuido un {abs(crecimiento):.1f}% durante el período analizado.")
        
        # Recomendaciones estratégicas
        st.info("""
        ### 🎯 Recomendaciones Estratégicas:
        
        1. **Personalización por región**: Desarrollar estrategias específicas para cada estado basadas en sus patrones de ventas únicos.
        
        2. **Optimización de inventario**: Usar los patrones de estacionalidad para optimizar los niveles de inventario y reducir costos.
        
        3. **Programación de promociones**: Planificar promociones estratégicamente durante los períodos de menor ventas para estimular la demanda.
        
        4. **Benchmarking entre tiendas**: Identificar las mejores prácticas de las tiendas de alto rendimiento y replicarlas en otras ubicaciones.
        
        5. **Segmentación de clientes**: Utilizar los datos de transacciones para segmentar clientes y desarrollar programas de fidelización personalizados.
        """)

# ===========================================
# PIE DE PÁGINA
# ===========================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 📝 Desarrollado por Claudia Maria Lopez Bombin")
st.sidebar.markdown("**Área de Datos**")
st.sidebar.markdown("Empresa de Alimentación")

# Nota en la página principal de Visión Global
if pagina_seleccionada == "🏠 Visión Global":
    st.markdown("---")
    st.success("✅ Dashboard completado exitosamente. ¡Listo para presentar al CEO y al Jefe de Ventas!")
    st.caption("*Nota: Los análisis se basan en una muestra de datos. Los valores absolutos son proporcionalmente menores que en el dataset completo.*")
