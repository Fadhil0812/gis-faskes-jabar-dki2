import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# =============================
# 1. AMBIL DATA OSM
# =============================
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

query = """
[out:json][timeout:300];

area["name"="Jawa Barat"]["admin_level"="4"]->.jabar;
area["name"="Daerah Khusus Ibukota Jakarta"]["admin_level"="4"]->.dki;

(
  node["amenity"="hospital"](area.jabar);
  node["amenity"="clinic"](area.jabar);
  node["amenity"="doctors"](area.jabar);
  node["amenity"="dentist"](area.jabar);
  node["amenity"="pharmacy"](area.jabar);
  node["healthcare"="therapy"](area.jabar);

  node["amenity"="hospital"](area.dki);
  node["amenity"="clinic"](area.dki);
  node["amenity"="doctors"](area.dki);
  node["amenity"="dentist"](area.dki);
  node["amenity"="pharmacy"](area.dki);
  node["healthcare"="therapy"](area.dki);
);

out tags center;
"""

print("📡 Mengambil data dari OpenStreetMap...")
response = requests.post(OVERPASS_URL, data=query)
data = response.json()

rows = []

for el in data["elements"]:
    tags = el.get("tags", {})

    rows.append({
        "nama_fasilitas": tags.get("name", "Tidak bernama"),
        "jenis_fasilitas": tags.get("amenity", tags.get("healthcare")),
        "latitude": el["lat"],
        "longitude": el["lon"]
    })

df = pd.DataFrame(rows)
print(f"✅ Jumlah data OSM: {len(df)}")

# =============================
# 2. JADI GEO DATA
# =============================
gdf_faskes = gpd.GeoDataFrame(
    df,
    geometry=[Point(xy) for xy in zip(df.longitude, df.latitude)],
    crs="EPSG:4326"
)

# =============================
# 3. LOAD BOUNDARY KAB/KOTA
# =============================
print("🗺️ Membaca boundary kabupaten/kota...")
gdf_admin = gpd.read_file("gadm/gadm41_IDN_2.shp")

gdf_admin = gdf_admin[
    gdf_admin["NAME_1"].isin([
        "Jawa Barat",
        "Daerah Khusus Ibukota Jakarta"
    ])
][["NAME_1", "NAME_2", "geometry"]]

gdf_admin = gdf_admin.to_crs("EPSG:4326")

# =============================
# 4. SPATIAL JOIN
# =============================
print("🔗 Menggabungkan titik dengan kab/kota...")
gdf_join = gpd.sjoin(
    gdf_faskes,
    gdf_admin,
    how="left",
    predicate="within"
)

gdf_join = gdf_join.rename(columns={
    "NAME_1": "provinsi",
    "NAME_2": "kota_kabupaten"
})

gdf_join = gdf_join.drop(columns=["index_right"])

# =============================
# 5. FIX JAKARTA (SOLUSI NO 2)
# =============================
# Semua kota administrasi Jakarta digabung jadi "DKI Jakarta"
gdf_join.loc[
    gdf_join["provinsi"] == "Daerah Khusus Ibukota Jakarta",
    "kota_kabupaten"
] = "DKI Jakarta"

# =============================
# 6. FIX DATA KOSONG (POINT DI JAKARTA TAPI GAGAL JOIN)
# =============================

mask_kosong = (
    gdf_join["provinsi"].isna() &
    gdf_join["kota_kabupaten"].isna() &
    (gdf_join["latitude"].between(-6.4, -5.9)) &
    (gdf_join["longitude"].between(106.6, 107.1))
)

gdf_join.loc[mask_kosong, "provinsi"] = "Daerah Khusus Ibukota Jakarta"
gdf_join.loc[mask_kosong, "kota_kabupaten"] = "DKI Jakarta"


# =============================
# 7. SIMPAN HASIL FINAL
# =============================
output = gdf_join.drop(columns="geometry")

output.to_csv(
    "fasilitas_kesehatan_jabar_dki_final.csv",
    index=False,
    encoding="utf-8-sig"
)

print("🎉 SELESAI")
print("📁 File: fasilitas_kesehatan_jabar_dki_final.csv")
print("📊 Total data:", len(output))
print("🏙️ Kab/Kota unik:", output["kota_kabupaten"].nunique())
