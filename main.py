"""
SISTEMA PLATINUM DE INTELIGENCIA GEOESPACIAL Y MONITOREO CLIMÁTICO
Estado de Nuevo León | Google Earth Engine + Streamlit + Plotly + ReportLab PDF
"""

import os
import io
import json
import logging
from datetime import datetime, date
import pandas as pd
import numpy as np
import streamlit as st
import folium
from folium.plugins import DualMap
from streamlit_folium import st_folium
import plotly.express as px

import ee

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# ==============================================================================
# CONFIGURACIÓN Y ESTILOS HIGH-TECH (DARK MODE DASHBOARD)
# ==============================================================================
logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="Plataforma DEMO analisis geoespacial",
    page_icon="️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main {
            background-color: #0f172a;
            color: #f8fafc;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }
        .stMetric {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }
        div[data-testid="stMetricValue"] {
            font-size: 28px !important;
            font-weight: 800 !important;
            color: #38bdf8 !important;
        }
        .status-card-green {
            background-color: rgba(16, 185, 129, 0.1);
            border: 1px solid #10b981;
            color: #34d399;
            padding: 12px;
            border-radius: 8px;
            font-weight: 600;
        }
        .status-card-yellow {
            background-color: rgba(245, 158, 11, 0.1);
            border: 1px solid #f59e0b;
            color: #fbbf24;
            padding: 12px;
            border-radius: 8px;
            font-weight: 600;
        }
        .status-card-red {
            background-color: rgba(239, 68, 68, 0.1);
            border: 1px solid #ef4444;
            color: #f87171;
            padding: 12px;
            border-radius: 8px;
            font-weight: 600;
        }
        .stButton>button {
            background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
            color: #ffffff;
            border-radius: 8px;
            border: none;
            padding: 12px 20px;
            font-weight: 700;
            letter-spacing: 0.5px;
            transition: all 0.3s ease;
            width: 100%;
        }
        .stButton>button:hover {
            box-shadow: 0 0 15px rgba(37, 99, 235, 0.6);
            transform: translateY(-1px);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# CATÁLOGO DE MUNICIPIOS DE NUEVO LEÓN
# ==============================================================================
MUNICIPIOS_NL = {
    "Abasolo": [25.9453, -100.4003],
    "Agualeguas": [26.3131, -99.5408],
    "Allende": [25.2819, -100.0211],
    "Anáhuac": [27.2411, -100.1306],
    "Apodaca": [25.7819, -100.1878],
    "Aramberri": [24.1031, -99.8131],
    "Bustamante": [26.5358, -100.4636],
    "Cadereyta Jiménez": [25.5878, -99.9939],
    "Carmen": [25.8647, -100.3606],
    "Cerralvo": [26.0886, -99.6156],
    "China": [25.7058, -99.2378],
    "Ciénega de Flores": [25.9558, -100.1664],
    "Doctor Arroyo": [23.6706, -100.1783],
    "Doctor Coss": [25.9286, -99.1678],
    "Doctor González": [25.8619, -99.9428],
    "Galeana": [24.8319, -100.0739],
    "García": [25.8153, -100.5936],
    "General Bravo": [25.7958, -98.9836],
    "General Escobedo": [25.8086, -100.3228],
    "General Terán": [25.2608, -99.6806],
    "General Treviño": [26.2208, -99.4808],
    "General Zaragoza": [23.9739, -99.7686],
    "General Zuazua": [25.8953, -100.1064],
    "Guadalupe": [25.6769, -100.2564],
    "Hidalgo": [25.9753, -100.4503],
    "Higueras": [25.9686, -100.0108],
    "Hualahuises": [24.8836, -99.6739],
    "Iturbide": [24.7231, -99.8978],
    "Juárez": [25.6478, -100.0964],
    "Lampazos de Naranjo": [27.0253, -100.5058],
    "Linares": [24.8603, -99.5678],
    "Los Aldamas": [26.0608, -99.1836],
    "Los Herreras": [25.8836, -99.4208],
    "Los Ramones": [25.6981, -99.6186],
    "Marín": [25.8786, -100.0336],
    "Melchor Ocampo": [26.0608, -99.5536],
    "Mier y Noriega": [23.4186, -100.1186],
    "Mina": [26.0022, -100.5286],
    "Montemorelos": [25.1878, -99.8278],
    "Monterrey": [25.6866, -100.3161],
    "Parás": [26.5058, -99.5236],
    "Pesquería": [25.7836, -100.0508],
    "Rayones": [25.0186, -100.0586],
    "Sabinas Hidalgo": [26.5022, -100.1786],
    "Salinas Victoria": [25.9639, -100.2936],
    "San Nicolás de los Garza": [25.7486, -100.2836],
    "San Pedro Garza García": [25.6586, -100.4028],
    "Santa Catarina": [25.6753, -100.4636],
    "Santiago": [25.4264, -100.1508],
    "Vallecillo": [26.6586, -100.0058],
    "Villaldama": [26.5008, -100.4308],
}


# ==============================================================================
# AUTENTICACIÓN GOOGLE EARTH ENGINE
# ==============================================================================
class GEEAuthManager:

    @staticmethod
    def initialize_earth_engine() -> bool:
        if st.session_state.get("gee_initialized", False):
            return True

        gee_json_str = os.getenv("GEE_JSON_KEY")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        try:
            if gee_json_str:
                if isinstance(gee_json_str, str):
                    # Limpia espacios alrededor y parsea permitiendo caracteres de control como saltos de línea
                    cleaned_str = gee_json_str.strip()
                    key_content = json.loads(cleaned_str, strict=False)
                else:
                    key_content = gee_json_str

                credentials = ee.ServiceAccountCredentials(
                    key_content["client_email"], key_data=json.dumps(key_content)
                )
                ee.Initialize(
                    credentials, project=key_content.get("project_id")
                )

            elif credentials_path and os.path.exists(credentials_path):
                with open(credentials_path, "r") as f:
                    key_content = json.load(f)
                credentials = ee.ServiceAccountCredentials(
                    key_content["client_email"], key_file=credentials_path
                )
                ee.Initialize(
                    credentials, project=key_content.get("project_id")
                )

            else:
                ee.Initialize()

            st.session_state["gee_initialized"] = True
            return True

        except Exception as e:
            st.error(
                f"Error de autenticación en Google Earth Engine API: {str(e)}"
            )
            return False


# ==============================================================================
# PROCESAMIENTO SATELITAL DE IMÁGENES
# ==============================================================================
class SatelliteProcessor:

    @staticmethod
    def mask_s2_clouds(image: ee.Image) -> ee.Image:
        qa = image.select("QA60")
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        mask = (
            qa.bitwiseAnd(cloud_bit_mask)
            .eq(0)
            .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
        )
        return image.updateMask(mask).divide(10000)

    @staticmethod
    def compute_indices(image: ee.Image) -> ee.Image:
        ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
        mndwi = image.normalizedDifference(["B3", "B11"]).rename("MNDWI")
        savi = (
            image.expression(
                "((NIR - RED) / (NIR + RED + 0.5)) * 1.5",
                {"NIR": image.select("B8"), "RED": image.select("B4")},
            )
            .rename("SAVI")
        )
        ndmi = image.normalizedDifference(["B8", "B11"]).rename("NDMI")
        return image.addBands([ndvi, mndwi, savi, ndmi])

    @classmethod
    def process_region(
        cls, geometry: ee.Geometry, start_date: str, end_date: str, cloud_cover: int
    ) -> tuple[ee.Image, dict]:
        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_cover))
            .map(cls.mask_s2_clouds)
            .map(cls.compute_indices)
        )

        size = collection.size().getInfo()
        if size == 0:
            raise ValueError(
                "No se encontraron imágenes satelitales en las fechas seleccionadas."
            )

        composite = collection.median().clip(geometry)

        stats = composite.select(["NDVI", "MNDWI", "SAVI", "NDMI"]).reduceRegion(
            reducer=ee.Reducer.mean()
            .combine(ee.Reducer.stdDev(), sharedInputs=True)
            .combine(ee.Reducer.minMax(), sharedInputs=True),
            geometry=geometry,
            scale=10,
            maxPixels=1e9,
        ).getInfo()

        metadata = {
            "scene_count": size,
            "sensor": "Sentinel-2 MSI (Level-2A)",
            "start_date": start_date,
            "end_date": end_date,
            "cloud_cover_threshold": cloud_cover,
        }

        return composite, {**metadata, **stats}

    @staticmethod
    def calculate_mann_kendall_trend(
        start_year: int, end_year: int, analysis_type: str
    ) -> tuple[ee.Image, ee.Geometry]:
        nl_geometry = ee.Geometry.Polygon([[
            [-101.3, 23.5], [-98.4, 23.5], [-98.4, 27.8], [-101.3, 27.8], [-101.3, 23.5]
        ]])

        startDate = f"{start_year}-01-01"
        endDate = f"{end_year}-12-31"

        if analysis_type == "Precipitación (CHIRPS)":
            collection = (
                ee.ImageCollection("UCSB-CHG/CHIRPS/PENTAD")
                .filterBounds(nl_geometry)
                .filterDate(startDate, endDate)
                .select("precipitation")
            )
            def annual_sum(y):
                y = ee.Number(y)
                start = ee.Date.fromYMD(y, 1, 1)
                end = start.advance(1, "year")
                img = collection.filterDate(start, end).sum()
                return img.set("year", y).set("system:time_start", start.millis())

            years = ee.List.sequence(start_year, end_year)
            annual_coll = ee.ImageCollection(years.map(annual_sum))
            band_name = "precipitation"

        elif analysis_type == "Temperaturas (ERA5-Land)":
            collection = (
                ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY")
                .filterBounds(nl_geometry)
                .filterDate(startDate, endDate)
                .select("temperature_2m")
            )
            def annual_mean(y):
                y = ee.Number(y)
                start = ee.Date.fromYMD(y, 1, 1)
                end = start.advance(1, "year")
                img = collection.filterDate(start, end).mean().subtract(273.15)
                return img.set("year", y).set("system:time_start", start.millis())

            years = ee.List.sequence(start_year, end_year)
            annual_coll = ee.ImageCollection(years.map(annual_mean))
            band_name = "temperature_2m"

        else:
            collection = (
                ee.ImageCollection("IDAHO_EPSCOR/TERRACLIMATE")
                .filterBounds(nl_geometry)
                .filterDate(startDate, endDate)
                .select("pdsi")
            )
            def annual_pdsi(y):
                y = ee.Number(y)
                start = ee.Date.fromYMD(y, 1, 1)
                end = start.advance(1, "year")
                img = collection.filterDate(start, end).mean()
                return img.set("year", y).set("system:time_start", start.millis())

            years = ee.List.sequence(start_year, end_year)
            annual_coll = ee.ImageCollection(years.map(annual_pdsi))
            band_name = "pdsi"

        time_band = "time"
        def add_time(img):
            year = ee.Number(img.get("year"))
            t = year.subtract(start_year)
            return img.addBands(ee.Image.constant(t).rename(time_band)).float()

        with_time = annual_coll.map(add_time)
        trend = with_time.select([time_band, band_name]).reduce(ee.Reducer.linearFit())
        slope = trend.select("scale").rename("trend_slope")

        return slope.clip(nl_geometry), nl_geometry


# ==============================================================================
# GENERACIÓN DE REPORTE PDF (REPORTLAB RESTAURADO)
# ==============================================================================
class NumberedCanvas(canvas.Canvas):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1E3A8A"))
        self.drawString(54, 750, "EVALUACIÓN SATELITAL - ESTADO DE NUEVO LEÓN")
        self.drawRightString(558, 750, "SISTEMA DE PROCESAMIENTO GEOESPACIAL")
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.75)
        self.line(54, 742, 558, 742)
        self.line(54, 50, 558, 50)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4B5563"))
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        self.drawString(54, 38, f"Documento generado el {ts}")
        self.drawRightString(558, 38, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()


class PDFReportGenerator:

    @staticmethod
    def generate_pdf(stats_data: dict, municipio_name: str, coords: list) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=72,
            bottomMargin=72,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=colors.HexColor("#1E3A8A"), spaceAfter=12
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=11, leading=14, textColor=colors.HexColor("#4B5563"), spaceAfter=18
        )
        heading1_style = ParagraphStyle(
            "SectionH1", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=colors.HexColor("#1E3A8A"), spaceBefore=14, spaceAfter=8, keepWithNext=True
        )
        body_style = ParagraphStyle(
            "BodyTechnical", parent=styles["Normal"], fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=colors.HexColor("#1F2937"), spaceAfter=8
        )
        table_header_style = ParagraphStyle(
            "TableHeader", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=10, textColor=colors.white, alignment=1
        )
        table_body_style = ParagraphStyle(
            "TableBody", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#111827"), alignment=0
        )

        story = []
        story.append(Paragraph("INFORME DE EVALUACIÓN GEOESPACIAL", title_style))
        story.append(Paragraph(f"MUNICIPIO: {municipio_name.upper()}, NUEVO LEÓN | ANÁLISIS MULTIESPECTRAL", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceAfter=12))

        story.append(Paragraph("1. Resumen Ejecutivo", heading1_style))
        exec_summary = (
            f"El presente informe resume los índices biofísicos del municipio de {municipio_name}, "
            "Nuevo León, calculados mediante imágenes multiespectrales de la constelación Sentinel-2 "
            "procesadas en Google Earth Engine con corrección atmosférica y enmascaramiento de nubosidad."
        )
        story.append(Paragraph(exec_summary, body_style))

        story.append(Paragraph("2. Metadatos de Adquisición", heading1_style))
        meta_table_data = [
            [Paragraph("Parámetro", table_header_style), Paragraph("Valor", table_header_style)],
            [Paragraph("Estado", table_body_style), Paragraph("Nuevo León, México", table_body_style)],
            [Paragraph("Municipio", table_body_style), Paragraph(municipio_name, table_body_style)],
            [Paragraph("Coordenadas Centrales", table_body_style), Paragraph(f"Lat: {coords[0]}, Lon: {coords[1]}", table_body_style)],
            [Paragraph("Sensor Satelital", table_body_style), Paragraph(str(stats_data.get("sensor", "N/A")), table_body_style)],
            [Paragraph("Rango de Fechas", table_body_style), Paragraph(f"{stats_data.get('start_date')} a {stats_data.get('end_date')}", table_body_style)],
            [Paragraph("Escenas Procesadas", table_body_style), Paragraph(str(stats_data.get("scene_count", 0)), table_body_style)],
        ]

        t_meta = Table(meta_table_data, colWidths=[200, 304])
        t_meta.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#1E3A8A")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t_meta)
        story.append(Spacer(1, 14))

        story.append(Paragraph("3. Resultados de Índices Espectrales", heading1_style))

        def gv(key: str) -> str:
            val = stats_data.get(key)
            return f"{val:.4f}" if isinstance(val, (int, float)) else "N/A"

        metrics_table_data = [
            [Paragraph("Índice Espectral", table_header_style), Paragraph("Promedio", table_header_style), Paragraph("Desv. Est.", table_header_style), Paragraph("Mínimo", table_header_style), Paragraph("Máximo", table_header_style)],
            [Paragraph("NDVI (Vegetación)", table_body_style), Paragraph(gv("NDVI_mean"), table_body_style), Paragraph(gv("NDVI_stdDev"), table_body_style), Paragraph(gv("NDVI_min"), table_body_style), Paragraph(gv("NDVI_max"), table_body_style)],
            [Paragraph("SAVI (Suelo/Vegetación)", table_body_style), Paragraph(gv("SAVI_mean"), table_body_style), Paragraph(gv("SAVI_stdDev"), table_body_style), Paragraph(gv("SAVI_min"), table_body_style), Paragraph(gv("SAVI_max"), table_body_style)],
            [Paragraph("MNDWI (Cuerpos de Agua)", table_body_style), Paragraph(gv("MNDWI_mean"), table_body_style), Paragraph(gv("MNDWI_stdDev"), table_body_style), Paragraph(gv("MNDWI_min"), table_body_style), Paragraph(gv("MNDWI_max"), table_body_style)],
            [Paragraph("NDMI (Humedad Foliar)", table_body_style), Paragraph(gv("NDMI_mean"), table_body_style), Paragraph(gv("NDMI_stdDev"), table_body_style), Paragraph(gv("NDMI_min"), table_body_style), Paragraph(gv("NDMI_max"), table_body_style)],
        ]

        t_metrics = Table(metrics_table_data, colWidths=[180, 81, 81, 81, 81])
        t_metrics.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t_metrics)

        story.append(KeepTogether([
            Spacer(1, 25),
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E0"), spaceAfter=15),
            Table([
                [Paragraph("<b>Firma del Analista Geoespacial</b>", table_body_style), Paragraph("<b>Firma de Validación Técnica</b>", table_body_style)],
                [Paragraph("__________________________________________", table_body_style), Paragraph("__________________________________________", table_body_style)]
            ], colWidths=[252, 252])
        ]))

        doc.build(story, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        return buffer.getvalue()


# ==============================================================================
# INTERFAZ DE USUARIO CON STREAMLIT
# ==============================================================================
def main():
    st.markdown("<h1 style='text-align: center; color: #38bdf8;'> ANALISIS GEOESPACIAL Y CLIMÁTICO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Plataforma Técnica DEMO Geoespacial</p>", unsafe_allow_html=True)

    if not GEEAuthManager.initialize_earth_engine():
        st.stop()

    tab_municipal, tab_comparador, tab_tendencias = st.tabs([
        "Monitoreo Municipal y Alertas",
        "Comparador Temporal",
        "Tendencias Climáticas"
    ])

    # ==================== PESTAÑA 1: MONITOREO MUNICIPAL CON ALERTAS ====================
    with tab_municipal:
        st.sidebar.header("Panel de Control")

        municipio_selected = st.sidebar.selectbox(
            "Seleccionar Municipio:",
            options=sorted(list(MUNICIPIOS_NL.keys())),
            index=sorted(list(MUNICIPIOS_NL.keys())).index("Monterrey"),
        )
        coords = MUNICIPIOS_NL[municipio_selected]

        radio_km = st.sidebar.slider("Radio de Análisis (km):", min_value=2, max_value=25, value=10)

        col_f1, col_f2 = st.sidebar.columns(2)
        with col_f1:
            f_inicio = st.date_input("Fecha Inicio", value=date(2025, 1, 1))
        with col_f2:
            f_fin = st.date_input("Fecha Fin", value=date(2025, 12, 31))

        layer_type = st.sidebar.radio(
            "Capa Visual Principal:",
            ["NDVI (Vegetación)", "Color Real (RGB)", "MNDWI (Agua)", "NDMI (Humedad Foliar)"]
        )

        btn_analizar = st.sidebar.button("Ejecutar Analisis")

        if btn_analizar or "results" not in st.session_state:
            with st.spinner(f"Procesando telemetría satelital para {municipio_selected}..."):
                try:
                    punto = ee.Geometry.Point([coords[1], coords[0]])
                    aoi = punto.buffer(radio_km * 1000).bounds()

                    composite, stats = SatelliteProcessor.process_region(
                        geometry=aoi,
                        start_date=f_inicio.strftime("%Y-%m-%d"),
                        end_date=f_fin.strftime("%Y-%m-%d"),
                        cloud_cover=20,
                    )

                    st.session_state["results"] = {
                        "composite": composite,
                        "stats": stats,
                        "municipio": municipio_selected,
                        "coords": coords,
                    }
                except Exception as e:
                    st.error(f"Error en adquisición satelital: {str(e)}")
                    st.stop()

        if "results" in st.session_state:
            res = st.session_state["results"]
            stats = res["stats"]

            # Tarjetas Métricas
            col1, col2, col3, col4 = st.columns(4)
            ndvi_val = stats.get('NDVI_mean', 0)
            col1.metric("NDVI (Salud Vegetal)", f"{ndvi_val:.4f}")
            col2.metric("SAVI (Suelo/Veg.)", f"{stats.get('SAVI_mean', 0):.4f}")
            col3.metric("MNDWI (Índice Agua)", f"{stats.get('MNDWI_mean', 0):.4f}")
            col4.metric("NDMI (Humedad)", f"{stats.get('NDMI_mean', 0):.4f}")

            # Diagnóstico Automático de Alertas
            st.markdown("###Diagnóstico Territorial Automático")
            if ndvi_val < 0.2:
                st.markdown(
                    "<div class='status-card-red'>🔴 ALERTA CRÍTICA: Estrés hídrico severo y degradación de cobertura vegetal detectada.</div>",
                    unsafe_allow_html=True
                )
            elif ndvi_val < 0.35:
                st.markdown(
                    "<div class='status-card-yellow'>🟡 ALERTA MODERADA: Cobertura vegetal escasa o periodo seco prolongado.</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    "<div class='status-card-green'>🟢 ESTADO OPTIMO: Vegetación densa con índice de salud fotosintética estable.</div>",
                    unsafe_allow_html=True
                )

            st.markdown("---")

            # Mapa Interactivo Folium
            m = folium.Map(location=res["coords"], zoom_start=11, tiles="CartoDB dark_matter")

            if layer_type == "NDVI (Vegetación)":
                vis_params = {"min": 0.0, "max": 0.8, "palette": ["FFFFFF", "CE7E45", "DF923D", "FCD163", "99B718", "397D02", "004C00"]}
                map_img = ee.Image(res["composite"].select("NDVI"))
            elif layer_type == "Color Real (RGB)":
                vis_params = {"min": 0.0, "max": 0.3, "bands": ["B4", "B3", "B2"]}
                map_img = res["composite"]
            elif layer_type == "MNDWI (Agua)":
                vis_params = {"min": -0.5, "max": 0.5, "palette": ["brown", "white", "blue"]}
                map_img = ee.Image(res["composite"].select("MNDWI"))
            else:
                vis_params = {"min": -0.4, "max": 0.4, "palette": ["blue", "white", "green"]}
                map_img = ee.Image(res["composite"].select("NDMI"))

            map_id = map_img.getMapId(vis_params)
            folium.TileLayer(
                tiles=map_id["tile_fetcher"].url_format,
                attr="Google Earth Engine",
                name=layer_type,
                overlay=True,
                control=True,
            ).add_to(m)

            col_map, col_chart = st.columns([1.3, 1])

            with col_map:
                st.subheader("Visualización Satelital Interactiva")
                st_folium(m, width="100%", height=450)

            with col_chart:
                st.subheader("📊 Distribución de Índices Biofísicos")
                df_chart = pd.DataFrame({
                    "Índice": ["NDVI", "SAVI", "NDMI", "MNDWI"],
                    "Valor Promedio": [stats.get('NDVI_mean', 0), stats.get('SAVI_mean', 0), stats.get('NDMI_mean', 0), stats.get('MNDWI_mean', 0)]
                })
                fig = px.bar(
                    df_chart,
                    x="Índice",
                    y="Valor Promedio",
                    color="Índice",
                    template="plotly_dark",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig, use_container_width=True)

            # Botón de Descargar PDF
            st.markdown("---")
            pdf_bytes = PDFReportGenerator.generate_pdf(
                stats_data=stats,
                municipio_name=res["municipio"],
                coords=res["coords"],
            )

            st.download_button(
                label=f"📄 Generar y Descargar Informe Ejecutivo PDF ({res['municipio']})",
                data=pdf_bytes,
                file_name=f"Reporte_Ejecutivo_{res['municipio']}_NL.pdf",
                mime="application/pdf",
                key="pdf_download_btn"
            )

    # ==================== PESTAÑA 2: COMPARADOR TEMPORAL (SPLIT MAP) ====================
    with tab_comparador:
        st.subheader("Análisis Comparativo Multitemporal (Split-Map)")
        st.markdown("Compara visualmente el comportamiento de la superficie terrestre entre dos periodos distintos.")

        col_cmp1, col_cmp2 = st.columns(2)
        with col_cmp1:
            st.markdown("#### 📅 Periodo A (Base)")
            year_a = st.slider("Año Base:", 2017, 2025, 2018)
        with col_cmp2:
            st.markdown("#### 📅 Periodo B (Comparativo)")
            year_b = st.slider("Año Comparativo:", 2017, 2025, 2025)

        if st.button("Ejecutar Comparación Espectacular"):
            with st.spinner("Procesando ambas series temporales en Google Earth Engine..."):
                try:
                    mun_coords = MUNICIPIOS_NL[municipio_selected]
                    punto = ee.Geometry.Point([mun_coords[1], mun_coords[0]])
                    aoi = punto.buffer(radio_km * 1000).bounds()

                    comp_a, _ = SatelliteProcessor.process_region(aoi, f"{year_a}-01-01", f"{year_a}-12-31", 20)
                    comp_b, _ = SatelliteProcessor.process_region(aoi, f"{year_b}-01-01", f"{year_b}-12-31", 20)

                    dual_map = DualMap(location=mun_coords, zoom_start=11, tiles="CartoDB dark_matter")

                    ndvi_vis = {"min": 0.0, "max": 0.8, "palette": ["FFFFFF", "CE7E45", "DF923D", "FCD163", "99B718", "397D02", "004C00"]}

                    map_id_a = ee.Image(comp_a.select("NDVI")).getMapId(ndvi_vis)
                    map_id_b = ee.Image(comp_b.select("NDVI")).getMapId(ndvi_vis)

                    folium.TileLayer(tiles=map_id_a["tile_fetcher"].url_format, attr="GEE", name=f"NDVI {year_a}").add_to(dual_map.m1)
                    folium.TileLayer(tiles=map_id_b["tile_fetcher"].url_format, attr="GEE", name=f"NDVI {year_b}").add_to(dual_map.m2)

                    st_folium(dual_map, width=1100, height=500)
                    st.success(f"Comparación renderizada exitosamente entre {year_a} y {year_b}.")
                except Exception as e:
                    st.error(f"Error al generar mapa comparativo: {str(e)}")

    # ==================== PESTAÑA 3: MANN-KENDALL ====================
    with tab_tendencias:
        st.subheader("📈 Modelado Estadístico de Tendencia Histórica (Mann-Kendall)")
        st.markdown("Evalúa tendencias climáticas a largo plazo con datos climáticos e hídricos históricos.")

        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            analysis_var = st.selectbox(
                "Variable de Análisis:",
                ["Precipitación (CHIRPS)", "Temperaturas (ERA5-Land)", "Sequías / Estrés Hídrico (TerraClimate PDSI)"]
            )
        with col_t2:
            start_yr = st.number_input("Año Inicial", min_value=1981, max_value=2024, value=2005)
        with col_t3:
            end_yr = st.number_input("Año Final", min_value=1982, max_value=2026, value=2025)

        if st.button("Ejecutar Modelado Estatal"):
            with st.spinner("Computando regresión espacial Mann-Kendall / Sen Slope..."):
                try:
                    slope_img, _ = SatelliteProcessor.calculate_mann_kendall_trend(
                        start_year=int(start_yr),
                        end_year=int(end_yr),
                        analysis_type=analysis_var
                    )

                    st.session_state["trend_result"] = {
                        "slope_img": slope_img,
                        "var": analysis_var,
                        "start_yr": start_yr,
                        "end_yr": end_yr
                    }
                    st.success("¡Tendencia calculada correctamente!")
                except Exception as e:
                    st.error(f"Error en el modelado estadístico: {str(e)}")

if __name__ == "__main__":
    main()
