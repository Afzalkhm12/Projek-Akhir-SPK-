import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. KONFIGURASI HALAMAN (LAYOUT)
# ==========================================
st.set_page_config(
    page_title="Jabar Bansos Analytics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk mempercantik tampilan metric
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #00CC96;
    }
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI LOAD DATA
# ==========================================
@st.cache_data
def load_data():
    """
    Memuat data dari file CSV hasil olahan Jupyter Notebook.
    Pastikan file berada di satu folder dengan script ini.
    """
    try:
        # Load Data Time Series (2018-2024)
        df_ts = pd.read_csv('data_timeseries_bansos_jabar.csv')
        
        # Load Hasil SPK (Ranking TOPSIS)
        df_spk = pd.read_csv('hasil_spk_topsis.csv')
        
        return df_ts, df_spk
    except FileNotFoundError:
        st.error("❌ File CSV tidak ditemukan! Pastikan 'data_timeseries_bansos_jabar.csv' dan 'hasil_spk_topsis.csv' ada di folder yang sama.")
        return None, None

# Load Data
df_ts, df_spk = load_data()

# Jika data gagal dimuat, hentikan eksekusi
if df_ts is None or df_spk is None:
    st.stop()

# ==========================================
# 3. SIDEBAR (NAVIGASI & FILTER)
# ==========================================
with st.sidebar:
    st.title("🛡️ Jabar Bansos Analytics")
    st.markdown("Dashboard Evaluasi Kinerja Penyaluran Bansos (2018-2024)")
    st.markdown("---")
    
    # Filter 1: Pilih Wilayah
    all_regions = sorted(df_ts['Wilayah'].unique())
    selected_regions = st.multiselect(
        "Pilih Wilayah untuk Analisis Tren:",
        options=all_regions,
        default=df_spk.sort_values('Ranking')['Wilayah'].head(5).tolist() # Default Top 5
    )
    
    # Filter 2: Rentang Tahun
    min_year = int(df_ts['Tahun'].min())
    max_year = int(df_ts['Tahun'].max())
    selected_years = st.slider("Rentang Tahun:", min_year, max_year, (min_year, max_year))
    
    st.markdown("---")
    st.info("""
    **Metodologi:**
    - **CRITIC:** Pembobotan Objektif berdasarkan deviasi data.
    - **TOPSIS:** Perankingan berdasarkan jarak solusi ideal.
    """)
    st.caption("Developed for UAS SPK")

# Filter Data Berdasarkan Sidebar
df_ts_filtered = df_ts[
    (df_ts['Wilayah'].isin(selected_regions)) & 
    (df_ts['Tahun'] >= selected_years[0]) & 
    (df_ts['Tahun'] <= selected_years[1])
]

# ==========================================
# 4. HEADER & KPI (KEY PERFORMANCE INDICATORS)
# ==========================================
st.title("📊 Executive Summary: Stabilitas Bansos Jabar")
st.markdown("Analisis Efektivitas dan Stabilitas Kinerja Wilayah Menggunakan Metode **Hybrid CRITIC-TOPSIS**")

# Hitung KPI untuk Baris Atas
col1, col2, col3, col4 = st.columns(4)

# KPI 1: Total Realisasi Tahun Terakhir (2024)
total_realisasi_2024 = df_ts[df_ts['Tahun'] == max_year]['Realisasi'].sum()
col1.metric("Total Penerima (2024)", f"{total_realisasi_2024:,.0f}", "KPM")

# KPI 2: Rata-rata Efektivitas (Seluruh Wilayah)
avg_eff = df_spk['C2_Efektivitas'].mean()
col2.metric("Rata-rata Efektivitas", f"{avg_eff:.2f}%", "Target Realisasi")

# KPI 3: Wilayah Terbaik (Ranking 1)
top_region = df_spk.loc[df_spk['Ranking'] == 1, 'Wilayah'].values[0]
top_score = df_spk.loc[df_spk['Ranking'] == 1, 'Skor_TOPSIS'].values[0]
col3.metric("Wilayah Terbaik", top_region, f"Skor: {top_score:.3f}")

# KPI 4: Wilayah Paling Stabil (Deviasi Terkecil - C4)
# Ingat C4 adalah Stabilitas (Cost), makin kecil makin stabil
stable_region = df_spk.loc[df_spk['C4_Stabilitas'].idxmin(), 'Wilayah']
stable_value = df_spk['C4_Stabilitas'].min()
col4.metric("Paling Stabil (Deviasi Terendah)", stable_region, f"±{stable_value:,.0f}")

st.markdown("---")

# ==========================================
# 5. VISUALISASI UTAMA (BARIS TENGAH)
# ==========================================
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader(f"📈 Tren Penyaluran Bansos ({selected_years[0]}-{selected_years[1]})")
    
    if not df_ts_filtered.empty:
        fig_line = px.line(
            df_ts_filtered, 
            x='Tahun', 
            y='Realisasi', 
            color='Wilayah',
            markers=True,
            title='Dinamika Jumlah Penerima Manfaat per Tahun',
            labels={'Realisasi': 'Jumlah Penerima (Jiwa)', 'Tahun': 'Tahun Anggaran'},
            template='plotly_white'
        )
        fig_line.update_layout(hovermode="x unified", height=400)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("Silakan pilih wilayah di sidebar untuk melihat grafik.")

with col_right:
    st.subheader("🏆 Top 10 Prioritas Wilayah")
    
    # Ambil Top 10 dari hasil SPK
    top_10 = df_spk.sort_values('Ranking').head(10)
    
    fig_bar = px.bar(
        top_10,
        x='Skor_TOPSIS',
        y='Wilayah',
        orientation='h',
        color='Skor_TOPSIS',
        title='Ranking Hasil TOPSIS',
        labels={'Skor_TOPSIS': 'Skor Preferensi', 'Wilayah': ''},
        color_continuous_scale='Viridis',
        template='plotly_white'
    )
    # Balik urutan biar Ranking 1 di atas
    fig_bar.update_layout(yaxis=dict(autorange="reversed"), height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# 6. ANALISIS MENDALAM (KUADRAN)
# ==========================================
st.markdown("---")
st.subheader("🧩 Analisis Kuadran: Efektivitas vs Stabilitas")
st.markdown("""
Grafik ini memetakan posisi setiap wilayah berdasarkan dua indikator kunci:
* **Sumbu X (Efektivitas):** Seberapa konsisten mencapai target? (Makin kanan makin bagus).
* **Sumbu Y (Ketidakstabilan/Deviasi):** Seberapa fluktuatif datanya? (Makin bawah makin stabil).
""")

# Buat Scatter Plot Kuadran
mean_eff = df_spk['C2_Efektivitas'].mean()
mean_stab = df_spk['C4_Stabilitas'].mean()

fig_scatter = px.scatter(
    df_spk,
    x='C2_Efektivitas',
    y='C4_Stabilitas',
    color='Ranking',
    size='C1_Volume', # Ukuran bubble = Volume Bansos
    hover_name='Wilayah',
    text='Wilayah',
    title='Peta Posisi Kinerja Wilayah (Bubble Size = Volume Penyaluran)',
    labels={'C2_Efektivitas': 'Rata-rata Efektivitas (%)', 'C4_Stabilitas': 'Ketidakstabilan (Standar Deviasi)'},
    template='plotly_white',
    color_continuous_scale='RdYlGn_r' # Merah = Ranking jelek, Hijau = Ranking bagus
)

# Tambahkan Garis Rata-rata (Garis Kuadran)
fig_scatter.add_hline(y=mean_stab, line_dash="dash", line_color="grey", annotation_text="Rata-rata Stabilitas")
fig_scatter.add_vline(x=mean_eff, line_dash="dash", line_color="grey", annotation_text="Rata-rata Efektivitas")
fig_scatter.update_traces(textposition='top center')
fig_scatter.update_layout(height=600)

st.plotly_chart(fig_scatter, use_container_width=True)

# ==========================================
# 7. TABEL DATA DETAIL
# ==========================================
with st.expander("📋 Lihat Data Detail Perhitungan"):
    st.markdown("Berikut adalah hasil perhitungan lengkap matriks keputusan.")
    
    # Format tabel biar cantik
    st.dataframe(
        df_spk.style.format({
            "Skor_TOPSIS": "{:.4f}",
            "C1_Volume": "{:,.0f}",
            "C2_Efektivitas": "{:.2f}%",
            "C3_Tren_Pertumbuhan": "{:.2f}%",
            "C4_Stabilitas": "{:,.2f}"
        }).background_gradient(subset=['Skor_TOPSIS'], cmap='Greens'),
        use_container_width=True
    )
    
    # Tombol Download CSV
    csv = df_spk.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Hasil Analisis (CSV)",
        data=csv,
        file_name='Laporan_SPK_Bansos_Jabar.csv',
        mime='text/csv',
    )

# ==========================================
# 8. FOOTER
# ==========================================
st.markdown("---")
st.caption("© 2025 Jabar Bansos Analytics | Dashboard created for Decision Support System Final Project")