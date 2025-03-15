import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
import warnings
warnings.filterwarnings('ignore')

# Konfigurasi halaman
st.set_page_config(page_title="Olist E-commerce Dashboard", 
                   page_icon="📊", 
                   layout="wide",
                   initial_sidebar_state="expanded")

# Fungsi untuk memuat data hasil analisis dari notebook.ipynb
@st.cache_data
def load_processed_data():
    try:
        # Dalam aplikasi nyata, file-file ini akan dihasilkan dari notebook.ipynb
        # Untuk demo, kita akan mencoba memuat langsung dari path data mentah
        import os
        
        # Check if processed_data directory exists, create if it doesn't
        if not os.path.exists('processed_data'):
            os.makedirs('processed_data')
            st.info("Created 'processed_data' directory. Run the notebook.ipynb first to generate processed datasets.")
        
        is_cloud = os.getenv('STREAMLIT_SHARING') == 'true' or os.getenv('STREAMLIT_RUN_ON_SAVE') == 'true'
        
        if is_cloud:
            base_path = 'data'  
        else:
            base_path = '../data'  

        def get_file_path(filename):
            possible_paths = [
                os.path.join('processed_data', filename),  # Check processed data first
                os.path.join(base_path, filename),
                os.path.join('data', filename),  
                os.path.join('../data', filename)
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            return os.path.join(base_path, filename)
        
        # Memuat semua dataset
        # Umumnya kita memuat data hasil proses, tapi karena belum dibuat, kita memuat data mentah
        df_customers = pd.read_csv(get_file_path('customers_dataset.csv'))
        df_order_items = pd.read_csv(get_file_path('order_items_dataset.csv'))
        df_order_payments = pd.read_csv(get_file_path('order_payments_dataset.csv'))
        df_order_reviews = pd.read_csv(get_file_path('order_reviews_dataset.csv'))
        df_orders = pd.read_csv(get_file_path('orders_dataset.csv'))
        df_product_category = pd.read_csv(get_file_path('product_category_name_translation.csv'))
        df_products = pd.read_csv(get_file_path('products_dataset.csv'))
        df_sellers = pd.read_csv(get_file_path('sellers_dataset.csv'))
        
        # Mengkonversi kolom tanggal ke format datetime
        orders_col = ['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date',
                      'order_delivered_customer_date', 'order_estimated_delivery_date']
        for col in orders_col:
            df_orders[col] = pd.to_datetime(df_orders[col])
        
        # Menggabungkan kategori produk dengan nama bahasa Inggris
        df_products = pd.merge(
            df_products, 
            df_product_category, 
            on='product_category_name', 
            how='left'
        )
        
        return {
            'customers': df_customers,
            'order_items': df_order_items,
            'order_payments': df_order_payments,
            'order_reviews': df_order_reviews,
            'orders': df_orders,
            'products': df_products,
            'sellers': df_sellers
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Memuat data dengan tampilan loading spinner
with st.spinner('Memuat data... Mohon tunggu.'):
    data = load_processed_data()

# Memeriksa apakah data berhasil dimuat
if not data:
    st.error("Gagal memuat data. Silakan periksa jalur file.")
    st.stop()

# ---------------------- Dashboard ----------------------

st.title("🛍️ Olist E-commerce Analytics Dashboard")

# Penjelasan dashboard
with st.expander("ℹ️ About this Dashboard"):
    st.markdown("""
    Dashboard ini menampilkan hasil analisis data e-commerce Brasil dari Olist Store yang telah diolah 
    melalui notebook.ipynb. Dashboard ini menyediakan wawasan tentang:
    
    1. **Tren Penjualan**: Analisis tren penjualan dari waktu ke waktu dan berdasarkan kategori produk.
    2. **Perilaku Pelanggan**: Analisis RFM dan segmentasi pelanggan.
    3. **Metode Pembayaran**: Distribusi metode pembayaran yang digunakan pelanggan.
    4. **Performa Pengiriman**: Analisis ketepatan waktu pengiriman pesanan.
    5. **Analisis Geografis**: Distribusi pelanggan berdasarkan lokasi geografis.
    
    Analisis lengkap tersedia dalam notebook.ipynb yang menyertai dashboard ini.
    """)

# --------- Sidebar untuk filter ---------
st.sidebar.title("📊 Filter Dashboard")

# Setup for date filters
min_date = data['orders']['order_purchase_timestamp'].min()
max_date = data['orders']['order_purchase_timestamp'].max()

# Filter date range
with st.sidebar.expander("🗓️ Tanggal", expanded=True):
    # Option to choose preset periods or custom
    date_option = st.radio(
        "Pilih Rentang Waktu:",
        ["Semua Data", "Tahun Terakhir", "6 Bulan Terakhir", "3 Bulan Terakhir", "Kustom"]
    )
    
    if date_option == "Semua Data":
        start_date = min_date
        end_date = max_date
    elif date_option == "Tahun Terakhir":
        start_date = max_date - timedelta(days=365)
        end_date = max_date
    elif date_option == "6 Bulan Terakhir":
        start_date = max_date - timedelta(days=180)
        end_date = max_date
    elif date_option == "3 Bulan Terakhir":
        start_date = max_date - timedelta(days=90)
        end_date = max_date
    else:  # Custom
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Tanggal Mulai", min_date)
        with col2:
            end_date = st.date_input("Tanggal Akhir", max_date)
        
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

# Filter kategori produk
with st.sidebar.expander("🏷️ Kategori Produk", expanded=True):
    # Check if translated categories are available
    if 'product_category_name_english' in data['products'].columns:
        categories = ['All Categories'] + sorted(data['products']['product_category_name_english'].dropna().unique().tolist())
    else:
        categories = ['All Categories'] + sorted(data['products']['product_category_name'].dropna().unique().tolist())
    
    selected_category = st.selectbox("Pilih Kategori Produk:", categories)
    
    if selected_category == 'All Categories':
        selected_category = None

# Filter negara bagian untuk analisis geografis
with st.sidebar.expander("🌎 Lokasi Geografis", expanded=True):
    states = ['All States'] + sorted(data['customers']['customer_state'].unique().tolist())
    selected_state = st.selectbox("Pilih Negara Bagian:", states)
    
    if selected_state == 'All States':
        selected_state = None

# ---- Tab layout untuk berbagai analisis ----
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Tren Penjualan", 
    "👥 Analisis Pelanggan", 
    "💳 Metode Pembayaran", 
    "🚚 Performa Pengiriman",
    "🌎 Analisis Geografis"
])

# ----- Tab 1: Tren Penjualan -----
with tab1:
    st.header("📊 Analisis Tren Penjualan")
    
    # Filter orders berdasarkan tanggal
    filtered_orders = data['orders'][(data['orders']['order_purchase_timestamp'] >= start_date) & 
                                (data['orders']['order_purchase_timestamp'] <= end_date)]
    
    # Gabungkan dengan items
    filtered_items = pd.merge(
        filtered_orders[['order_id']],
        data['order_items'],
        on='order_id',
        how='inner'
    )
    
    # Filter berdasarkan kategori jika ditentukan
    if selected_category:
        product_ids = data['products'][data['products']['product_category_name_english'] == selected_category]['product_id'].unique()
        filtered_items = filtered_items[filtered_items['product_id'].isin(product_ids)]
    
    # Metrik utama dalam 3 kolom
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_orders = filtered_items['order_id'].nunique()
        st.metric("Total Pesanan", f"{total_orders:,}")
    
    with col2:
        total_sales = filtered_items['price'].sum()
        st.metric("Total Penjualan", f"R$ {total_sales:,.2f}")
    
    with col3:
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        st.metric("Rata-rata Nilai Pesanan", f"R$ {avg_order_value:,.2f}")
    
    # Grafik tren penjualan dari waktu ke waktu
    st.subheader("Tren Penjualan dari Waktu ke Waktu")
    
    # Menggabungkan data pesanan dengan waktu
    sales_over_time = pd.merge(
        filtered_orders[['order_id', 'order_purchase_timestamp']],
        filtered_items[['order_id', 'price']],
        on='order_id',
        how='inner'
    )
    
    # Agregasi penjualan per bulan
    sales_over_time['month'] = sales_over_time['order_purchase_timestamp'].dt.to_period('M')
    monthly_sales = sales_over_time.groupby(sales_over_time['month'].astype(str))['price'].sum().reset_index()
    
    # Plotting
    fig = px.line(
        monthly_sales, 
        x='month', 
        y='price',
        title='Tren Penjualan Bulanan',
        labels={'month': 'Bulan', 'price': 'Total Penjualan (R$)'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Top kategori berdasarkan penjualan
    st.subheader("Top Kategori Produk Berdasarkan Penjualan")
    
    # Menggabungkan data item dengan produk
    items_with_categories = pd.merge(
        filtered_items,
        data['products'][['product_id', 'product_category_name', 'product_category_name_english']],
        on='product_id',
        how='inner'
    )
    
    # Agregasi berdasarkan kategori
    cat_column = 'product_category_name_english' if 'product_category_name_english' in items_with_categories.columns else 'product_category_name'
    category_sales = items_with_categories.groupby(cat_column).agg({
        'price': 'sum',
        'order_id': 'nunique'
    }).reset_index()
    
    # Sorting dan mengambil top 10
    top_categories = category_sales.sort_values('price', ascending=False).head(10)
    
    # Plotting
    fig = px.bar(
        top_categories,
        x=cat_column,
        y='price',
        title='Top 10 Kategori Berdasarkan Penjualan',
        labels={cat_column: 'Kategori', 'price': 'Total Penjualan (R$)'}
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ----- Tab 2: Analisis Pelanggan -----
with tab2:
    st.header("👥 Analisis Segmentasi Pelanggan")
    
    st.info("""
    **RFM Analysis** adalah teknik segmentasi pelanggan berdasarkan perilaku pembelian:
    - **Recency**: Berapa hari sejak pembelian terakhir
    - **Frequency**: Berapa kali pelanggan melakukan pembelian
    - **Monetary**: Berapa total nilai pembelian pelanggan
    
    Analisis lengkap tersedia di notebook.ipynb.
    """)
    
    # Filter orders berdasarkan tanggal untuk RFM
    filtered_orders_rfm = data['orders'][
        (data['orders']['order_purchase_timestamp'] >= start_date) & 
        (data['orders']['order_purchase_timestamp'] <= end_date) &
        (data['orders']['order_status'] == 'delivered')
    ]
    
    # Gabungkan dengan pembayaran
    orders_with_payments = pd.merge(
        filtered_orders_rfm[['order_id', 'customer_id', 'order_purchase_timestamp']],
        data['order_payments'][['order_id', 'payment_value']],
        on='order_id',
        how='inner'
    )
    
    if len(orders_with_payments) > 0:
        # Hitung RFM metrics
        # Recency
        recency_df = orders_with_payments.groupby('customer_id')['order_purchase_timestamp'].max().reset_index()
        recency_df['recency'] = (end_date - recency_df['order_purchase_timestamp']).dt.days
        
        # Frequency
        frequency_df = orders_with_payments.groupby('customer_id')['order_id'].nunique().reset_index()
        frequency_df.columns = ['customer_id', 'frequency']
        
        # Monetary
        monetary_df = orders_with_payments.groupby('customer_id')['payment_value'].sum().reset_index()
        monetary_df.columns = ['customer_id', 'monetary']
        
        # Combine
        rfm = pd.merge(recency_df[['customer_id', 'recency']], frequency_df, on='customer_id')
        rfm = pd.merge(rfm, monetary_df, on='customer_id')
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_recency = rfm['recency'].mean()
            st.metric("Rata-rata Recency", f"{avg_recency:.1f} hari")
        
        with col2:
            avg_frequency = rfm['frequency'].mean()
            st.metric("Rata-rata Frequency", f"{avg_frequency:.1f} pesanan")
        
        with col3:
            avg_monetary = rfm['monetary'].mean()
            st.metric("Rata-rata Monetary", f"R$ {avg_monetary:.2f}")
        
        # Create segments - Penanganan khusus untuk recency
        if rfm['recency'].nunique() < 5:
            # Jika tidak cukup variasi, tetapkan nilai tengah
            rfm['r_score'] = 3
        else:
            try:
                rfm['r_score'] = pd.qcut(rfm['recency'], q=5, labels=[5, 4, 3, 2, 1], duplicates='drop')
            except ValueError:
                rfm['r_score'] = pd.cut(rfm['recency'], bins=5, labels=[5, 4, 3, 2, 1], duplicates='drop')
        
        # Penanganan untuk frequency
        if rfm['frequency'].nunique() < 5:
            rfm['f_score'] = 3
        else:
            try:
                rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
            except ValueError:
                rfm['f_score'] = pd.cut(rfm['frequency'], bins=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
        
        # Penanganan untuk monetary
        if rfm['monetary'].nunique() < 5:
            rfm['m_score'] = 3
        else:
            try:
                rfm['m_score'] = pd.qcut(rfm['monetary'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
            except ValueError:
                rfm['m_score'] = pd.cut(rfm['monetary'], bins=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
        
        # Convert score columns to numeric
        for col in ['r_score', 'f_score', 'm_score']:
            rfm[col] = pd.to_numeric(rfm[col], errors='coerce')
        
        # Calculate overall RFM score
        rfm['rfm_score'] = rfm['r_score'] + rfm['f_score'] + rfm['m_score']
        
        # Create segment labels
        rfm['segment'] = pd.cut(
            rfm['rfm_score'],
            bins=[0, 4, 8, 12, 15],
            labels=['Bronze', 'Silver', 'Gold', 'Platinum'],
            include_lowest=True
        )
        
        # Visualize segment distribution
        segment_dist = rfm['segment'].value_counts().reset_index()
        segment_dist.columns = ['segment', 'count']
        
        fig = px.pie(
            segment_dist, 
            values='count', 
            names='segment',
            title='Distribusi Segmen Pelanggan',
            color='segment',
            color_discrete_map={
                'Bronze': '#CD7F32',
                'Silver': '#C0C0C0',
                'Gold': '#FFD700',
                'Platinum': '#E5E4E2'
            }
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add explanation of segments
        st.subheader("Interpretasi Segmen Pelanggan")
        
        segments_table = pd.DataFrame({
            'Segmen': ['Platinum', 'Gold', 'Silver', 'Bronze'],
            'Deskripsi': [
                'Pelanggan dengan nilai tertinggi yang sering berbelanja dan baru-baru ini melakukan pembelian.',
                'Pelanggan bernilai tinggi yang cenderung berbelanja secara teratur.',
                'Pelanggan menengah yang berbelanja sesekali atau pelanggan baru dengan nilai pembelian tinggi.',
                'Pelanggan yang jarang berbelanja dan sudah lama tidak melakukan pembelian.'
            ],
            'Strategi Marketing': [
                'Program loyalitas VIP, akses awal ke produk baru, personalisasi layanan.',
                'Cross-selling dan up-selling, program rewards, insentif untuk meningkatkan frekuensi.',
                'Promosi produk terkait, program engagement, insentif untuk meningkatkan frekuensi.',
                'Program reaktivasi, diskon khusus untuk pembelian berikutnya, penawaran win-back.'
            ]
        })
        
        st.table(segments_table)
    else:
        st.warning("Tidak ada data yang cukup untuk analisis RFM dalam rentang waktu yang dipilih.")

# ----- Tab 3: Metode Pembayaran -----
with tab3:
    st.header("💳 Analisis Metode Pembayaran")
    
    # Filter orders berdasarkan rentang tanggal
    filtered_orders_payment = data['orders'][(data['orders']['order_purchase_timestamp'] >= start_date) & 
                                         (data['orders']['order_purchase_timestamp'] <= end_date)]
    
    # Gabungkan dengan data pembayaran
    payment_data = pd.merge(
        filtered_orders_payment[['order_id']],
        data['order_payments'],
        on='order_id',
        how='inner'
    )
    
    # Agregasi berdasarkan jenis pembayaran
    payment_summary = payment_data.groupby('payment_type').agg({
        'payment_value': 'sum',
        'order_id': 'nunique'
    }).reset_index()
    
    payment_summary.columns = ['payment_type', 'total_value', 'order_count']
    payment_summary['percentage'] = payment_summary['total_value'] / payment_summary['total_value'].sum() * 100
    
    # Visualisasi distribusi metode pembayaran
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = px.pie(
            payment_summary, 
            values='total_value', 
            names='payment_type',
            title='Distribusi Metode Pembayaran',
            hole=0.4
        )
        
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Value: R$%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Statistik pembayaran
        st.subheader("Statistik Metode Pembayaran")
        
        # Format untuk tampilan
        display_stats = payment_summary.copy()
        display_stats['avg_value'] = display_stats['total_value'] / display_stats['order_count']
        display_stats = display_stats[['payment_type', 'order_count', 'avg_value']]
        display_stats.columns = ['Metode Pembayaran', 'Jumlah Pesanan', 'Rata-rata Nilai']
        display_stats['Rata-rata Nilai'] = display_stats['Rata-rata Nilai'].map('R$ {:.2f}'.format)
        
        st.table(display_stats)
    
    # Analisis cicilan pembayaran kartu kredit
    st.subheader("Analisis Pembayaran Cicilan")
    
    # Filter hanya metode pembayaran credit_card
    credit_data = payment_data[payment_data['payment_type'] == 'credit_card']
    
    if len(credit_data) > 0:
        # Distribusi jumlah cicilan
        installment_counts = credit_data['payment_installments'].value_counts().reset_index()
        installment_counts.columns = ['installments', 'count']
        installment_counts = installment_counts.sort_values('installments')
        
        fig = px.bar(
            installment_counts,
            x='installments',
            y='count',
            title='Distribusi Jumlah Cicilan (Kartu Kredit)',
            labels={'installments': 'Jumlah Cicilan', 'count': 'Jumlah Transaksi'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Rata-rata nilai pembelian berdasarkan jumlah cicilan
        installment_values = credit_data.groupby('payment_installments')['payment_value'].mean().reset_index()
        installment_values.columns = ['installments', 'avg_value']
        
        fig = px.line(
            installment_values,
            x='installments',
            y='avg_value',
            title='Rata-rata Nilai Pembelian Berdasarkan Jumlah Cicilan',
            labels={'installments': 'Jumlah Cicilan', 'avg_value': 'Rata-rata Nilai (R$)'},
            markers=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Tidak ada data pembayaran kartu kredit dalam periode yang dipilih.")

# ----- Tab 4: Performa Pengiriman -----
with tab4:
    st.header("🚚 Analisis Performa Pengiriman")
    
    # Filter orders berdasarkan rentang tanggal dan status terkirim
    delivery_data = data['orders'][
        (data['orders']['order_purchase_timestamp'] >= start_date) & 
        (data['orders']['order_purchase_timestamp'] <= end_date) &
        (data['orders']['order_status'] == 'delivered')
    ].copy()
    
    # Filter out rows with missing delivery dates
    delivery_data = delivery_data.dropna(subset=['order_delivered_customer_date', 'order_estimated_delivery_date'])
    
    if len(delivery_data) > 0:
        # Hitung selisih waktu antara estimasi dan aktual pengiriman
        delivery_data['delivery_difference'] = (delivery_data['order_delivered_customer_date'] - 
                                               delivery_data['order_estimated_delivery_date']).dt.days
        
        # Definisi kategori ketepatan waktu
        delivery_data['delivery_status'] = pd.cut(
            delivery_data['delivery_difference'],
            bins=[-float('inf'), -3, -1, 0, 2, float('inf')],
            labels=['Very Early', 'Early', 'On Time', 'Late', 'Very Late']
        )
        
        # Agregasi berdasarkan status pengiriman
        delivery_summary = delivery_data['delivery_status'].value_counts().reset_index()
        delivery_summary.columns = ['delivery_status', 'count']
        
        # Urutkan berdasarkan kategori
        status_order = ['Very Early', 'Early', 'On Time', 'Late', 'Very Late']
        delivery_summary['delivery_status'] = pd.Categorical(
            delivery_summary['delivery_status'], 
            categories=status_order, 
            ordered=True
        )
        delivery_summary = delivery_summary.sort_values('delivery_status')
        
        # Warna untuk setiap kategori
        color_map = {
            'Very Early': 'darkgreen',
            'Early': 'green',
            'On Time': 'lightgreen',
            'Late': 'orange',
            'Very Late': 'red'
        }
        
        # Visualisasi distribusi status pengiriman
        fig = px.bar(
            delivery_summary, 
            x='delivery_status', 
            y='count',
            title='Analisis Performa Pengiriman',
            color='delivery_status',
            color_discrete_map=color_map,
            labels={'delivery_status': 'Status Pengiriman', 'count': 'Jumlah Pesanan'}
        )
        
        fig.update_layout(
            xaxis_title='Status Pengiriman',
            yaxis_title='Jumlah Pesanan'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Metrik pengiriman
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Hitung waktu pengiriman actual
            delivery_data['actual_delivery_days'] = (delivery_data['order_delivered_customer_date'] - 
                                                   delivery_data['order_purchase_timestamp']).dt.days
            avg_delivery_time = delivery_data['actual_delivery_days'].mean()
            st.metric("Rata-rata Waktu Pengiriman", f"{avg_delivery_time:.1f} hari")
        
        with col2:
            # Hitung waktu pengiriman estimasi
            delivery_data['estimated_delivery_days'] = (delivery_data['order_estimated_delivery_date'] - 
                                                      delivery_data['order_purchase_timestamp']).dt.days
            avg_estimated_time = delivery_data['estimated_delivery_days'].mean()
            st.metric("Rata-rata Estimasi Pengiriman", f"{avg_estimated_time:.1f} hari")
        
        with col3:
            # Hitung persentase tepat waktu
            on_time_percentage = (delivery_data['delivery_difference'] <= 0).mean() * 100
            st.metric("Persentase Tepat Waktu", f"{on_time_percentage:.1f}%")
        
        # Distribusi waktu pengiriman
        st.subheader("Distribusi Waktu Pengiriman")
        
        fig = px.histogram(
            delivery_data,
            x='actual_delivery_days',
            nbins=20,
            title='Distribusi Waktu Pengiriman (Hari)',
            labels={'actual_delivery_days': 'Waktu Pengiriman (Hari)'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Tidak ada data pengiriman yang cukup untuk analisis dalam periode yang dipilih.")

# ----- Tab 5: Analisis Geografis -----
with tab5:
    st.header("🌎 Analisis Geografis")
    
    # Distribusi pelanggan berdasarkan negara bagian
    customer_states = data['customers']['customer_state'].value_counts().reset_index()
    customer_states.columns = ['state', 'customer_count']
    
    # Filter berdasarkan state jika dipilih
    if selected_state:
        customer_states = customer_states[customer_states['state'] == selected_state]
    
    # Buat peta Brazil
    brazil_map = folium.Map(location=[-14.235, -51.9253], zoom_start=4, tiles="CartoDB positron")
    
    # Tambahkan GeoJson dari Brazil
    folium.Choropleth(
        geo_data='https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson',
        name='choropleth',
        data=customer_states,
        columns=['state', 'customer_count'],
        key_on='feature.properties.sigla',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Customer Count'
    ).add_to(brazil_map)
    
    folium.LayerControl().add_to(brazil_map)
    
    # Tampilkan peta
    st.subheader("Distribusi Pelanggan berdasarkan Negara Bagian")
    folium_static(brazil_map)
    
    # Visualisasi jumlah pelanggan per negara bagian dengan grafik batang
    st.subheader("Jumlah Pelanggan per Negara Bagian")
    
    if not selected_state:
        # Sorting state berdasarkan jumlah pelanggan
        sorted_states = customer_states.sort_values('customer_count', ascending=False)
        
        fig = px.bar(
            sorted_states,
            x='state',
            y='customer_count',
            title='Distribusi Pelanggan berdasarkan Negara Bagian',
            labels={'state': 'Negara Bagian', 'customer_count': 'Jumlah Pelanggan'},
            color='customer_count'
        )
        
        fig.update_layout(xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Jika state dipilih, tampilkan distribusi kota
        city_counts = data['customers'][data['customers']['customer_state'] == selected_state]['customer_city'].value_counts().reset_index()
        city_counts.columns = ['city', 'count']
        top_cities = city_counts.head(10)
        
        fig = px.bar(
            top_cities,
            x='city',
            y='count',
            title=f'Top 10 Kota di {selected_state} berdasarkan Jumlah Pelanggan',
            labels={'city': 'Kota', 'count': 'Jumlah Pelanggan'},
            color='count'
        )
        
        fig.update_layout(xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig, use_container_width=True)

# Tampilkan informasi tentang notebook analisis
st.markdown("---")
st.info("""
**Catatan:** Dashboard ini hanya menampilkan sebagian hasil analisis yang telah dilakukan dalam notebook.ipynb. 
Untuk melihat analisis lengkap termasuk RFM analysis, clustering, visualisasi lanjutan, dan insight bisnis, 
silakan buka dan jalankan notebook.ipynb.

Notebook berisi analisis mendalam tentang:
- Segmentasi pelanggan dengan RFM analysis
- Analisis geografis penjualan
- Pola pembelian berdasarkan waktu
- Analisis review dan rating produk
- Performa pengiriman
""")

st.markdown("""
<div style="text-align: center">
    <p>Olist E-commerce Analytics Dashboard | Dibuat dengan Streamlit</p>
</div>
""", unsafe_allow_html=True)