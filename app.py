import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px

# =============================
# KONFIGURASI HALAMAN
# =============================
st.set_page_config(
    page_title="Analisis Persebaran Fasilitas Kesehatan Di Jawa Barat Dan DKI Jakarta",
    layout="wide"
)

st.title("🗺️ Analisis Persebaran Fasilitas Kesehatan Di Jawa Barat Dan DKI Jakarta")
st.caption("Provinsi Jawa Barat dan DKI Jakarta (Sumber: OpenStreetMap)")

# =============================
# LOAD DATA
# =============================
df = pd.read_csv("fasilitas_kesehatan_jabar_dki_final.csv")

# =============================
# FIX DATA KOSONG JAKARTA
# =============================
mask_jakarta = (
    df["provinsi"].isna() &
    df["latitude"].between(-6.4, -5.9) &
    df["longitude"].between(106.6, 107.1)
)

df.loc[mask_jakarta, "provinsi"] = "Daerah Khusus Ibukota Jakarta"
df.loc[mask_jakarta, "kota_kabupaten"] = "DKI Jakarta"

# =============================
# SIDEBAR FILTER
# =============================
st.sidebar.header("🔎 Filter Data")

# ---- FILTER PROVINSI
provinsi_opsi = st.sidebar.multiselect(
    "Pilih Provinsi",
    options=sorted(df["provinsi"].dropna().unique()),
    default=sorted(df["provinsi"].dropna().unique())
)

df = df[df["provinsi"].isin(provinsi_opsi)]

# ---- FILTER JENIS FASKES
jenis_opsi = st.sidebar.multiselect(
    "Pilih Jenis Fasilitas",
    options=sorted(df["jenis_fasilitas"].unique()),
    default=sorted(df["jenis_fasilitas"].unique())
)

df = df[df["jenis_fasilitas"].isin(jenis_opsi)]

# =============================
# INFO RINGKAS (DI ATAS MAP)
# =============================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📍 Total Fasilitas", len(df))

with col2:
    st.metric("🏙️ Jumlah Kab/Kota", df["kota_kabupaten"].nunique())

with col3:
    st.metric("🏥 Jenis Fasilitas", df["jenis_fasilitas"].nunique())

# =============================
# MAP GIS
# =============================
st.markdown("### 🗺️ Peta Persebaran Fasilitas Kesehatan")

m = folium.Map(
    location=[-6.6, 106.9],
    zoom_start=9,
    tiles="CartoDB positron"
)

for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=4,
        color="#1E88E5",
        fill=True,
        fill_opacity=0.8,
        popup=f"""
        <b>{row['nama_fasilitas']}</b><br>
        Jenis: {row['jenis_fasilitas']}<br>
        Wilayah: {row['kota_kabupaten']}<br>
        Provinsi: {row['provinsi']}
        """
    ).add_to(m)

st_folium(m, height=480, width=1200)

# =============================
# BAR CHART (DIPINDAH KE BAWAH)
# =============================
st.markdown("---")
st.markdown("## 📊 Visualisasi Statistik")

# ---- BAR JENIS FASILITAS
st.markdown("### Jumlah Fasilitas Berdasarkan Jenis")

jenis_df = (
    df["jenis_fasilitas"]
    .value_counts()
    .reset_index()
)
jenis_df.columns = ["Jenis Fasilitas", "Jumlah"]

fig1 = px.bar(
    jenis_df,
    x="Jenis Fasilitas",
    y="Jumlah",
    text="Jumlah"
)

fig1.update_layout(
    xaxis_tickangle=-30,
    showlegend=False
)

st.plotly_chart(fig1, use_container_width=True)

# ---- BAR KAB / KOTA
st.markdown("### Jumlah Fasilitas per Kabupaten / Kota")

kota_df = (
    df["kota_kabupaten"]
    .value_counts()
    .reset_index()
)
kota_df.columns = ["Kabupaten / Kota", "Jumlah"]

fig2 = px.bar(
    kota_df,
    x="Kabupaten / Kota",
    y="Jumlah",
    text="Jumlah"
)

fig2.update_layout(
    xaxis_tickangle=-45,
    showlegend=False
)

st.plotly_chart(fig2, use_container_width=True)