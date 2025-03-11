# Dashboard Analitik E-commerce Olist

Dashboard ini menyediakan analisis komprehensif untuk data e-commerce Brasil dari Olist, yang mencakup berbagai aspek bisnis:

- **Analisis Pola Pembelian Geografis**: Mengeksplorasi tren pembelian berdasarkan lokasi pelanggan
- **Analisis Performa Penjual**: Evaluasi kinerja penjual berdasarkan penjualan dan ulasan
- **Analisis Metode Pembayaran**: Analisis preferensi metode pembayaran dan pola cicilan
- **Segmentasi Pelanggan (RFM)**: Pengelompokan pelanggan berdasarkan Recency, Frequency, dan Monetary value

## Demo

Dashboard ini tersedia secara online pada Streamlit Cloud: [Olist E-commerce Dashboard](https://submission-dashboard-e-commerce.streamlit.app/)

## Struktur Repositori

```
├── dashboard/
│   └── dashboard.py          # File utama aplikasi Streamlit
│
├── data/                     # Direktori data
│   ├── customers_dataset.csv
│   ├── geolocation_dataset.csv
│   ├── order_items_dataset.csv
│   ├── order_payments_dataset.csv
│   ├── order_reviews_dataset.csv
│   ├── orders_dataset.csv
│   ├── product_category_name_translation.csv
│   ├── products_dataset.csv
│   └── sellers_dataset.csv
│
├── README.md                 # Dokumentasi proyek
├── requirements.txt          # Daftar dependensi
└── url.txt                   # URL repository
```

## Petunjuk Penggunaan

### Prasyarat
- Python 3.7 atau lebih tinggi
- Pip package manager

### Instalasi

1. Clone repositori ini:
```
git clone git@github.com:Koerentji/submission-dashboard-e-commerce.git
```

2. Pindah ke direktori proyek:
```
cd submission-dashboard-e-commerce
```

3. Buat virtual environment (direkomendasikan):
```
python -m venv venv
```

4. Aktifkan virtual environment:
   - Windows:
   ```
   venv\Scripts\activate
   ```
   - macOS/Linux:
   ```
   source venv/bin/activate
   ```

5. Pasang paket yang diperlukan:
```
pip install -r requirements.txt
```

### Menjalankan Aplikasi

Untuk menjalankan dashboard:
```
cd dashboard
streamlit run dashboard.py
```

Aplikasi akan terbuka di browser Anda secara otomatis, biasanya di `http://localhost:8501`.

## Fitur

### Overview
- Tampilan dataset dan informasi kualitas data
- Visualisasi nilai null dan duplikat

### Analisis Geografis
- Analisis penjualan berdasarkan negara bagian
- Tren pembelian bulanan untuk negara bagian teratas
- Analisis kota dengan nilai transaksi tertinggi

### Performa Penjual
- Performa penjual berdasarkan negara bagian
- Penjual dengan performa terbaik
- Korelasi antara ulasan dan penjualan

### Metode Pembayaran
- Distribusi metode pembayaran
- Pola pembayaran berdasarkan negara bagian
- Analisis cicilan kartu kredit

### Segmentasi Pelanggan
- Segmentasi berdasarkan RFM (Recency, Frequency, Monetary)
- Analisis kelompok pelanggan Champion
- Distribusi geografis segmen pelanggan

## Sumber Data

Dataset yang digunakan adalah data publik dari Olist, marketplace e-commerce Brasil. Dataset berisi informasi tentang 100.000 pesanan dari 2016 hingga 2018. Data ini mencakup berbagai aspek operasional e-commerce seperti informasi pesanan, pembayaran, produk, pelanggan, dan penjual.

## Teknologi yang Digunakan

- **Streamlit**: Kerangka kerja untuk membangun aplikasi web interaktif
- **Pandas**: Manipulasi dan analisis data
- **Plotly**: Visualisasi data interaktif
- **Matplotlib & Seaborn**: Visualisasi data tambahan
- **Folium**: Visualisasi peta

## Tentang Proyek

Proyek ini dibuat sebagai bagian dari tugas akhir kursus Data Science. Tujuannya adalah untuk menunjukkan kemampuan dalam menganalisis data e-commerce dan menghasilkan dashboard yang interaktif dan informatif untuk pengambilan keputusan bisnis.