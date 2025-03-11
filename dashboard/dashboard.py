import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import datetime as dt
from datetime import datetime
import folium
from folium.plugins import HeatMap
import warnings
import squarify
from streamlit_folium import folium_static

# Mengabaikan peringatan untuk tampilan yang lebih bersih
warnings.filterwarnings('ignore')

# Konfigurasi halaman
st.set_page_config(page_title="Olist E-commerce Dashboard", 
                   page_icon="📊", 
                   layout="wide",
                   initial_sidebar_state="expanded")

# Judul dan Pengantar
st.title("Olist E-commerce Analytics Dashboard")
st.markdown("""
Dashboard ini menganalisis data e-commerce Brasil dari Olist, mengeksplorasi pola geografis,
kinerja penjual, metode pembayaran, dan segmentasi pelanggan.
""")

# Fungsi untuk memuat data
@st.cache_data  # Menggunakan cache agar data tidak perlu dimuat ulang setiap kali refresh
def load_data():
    try:
        # Memuat semua dataset
        df_customers = pd.read_csv('../data/customers_dataset.csv')
        df_geolocation = pd.read_csv('../data/geolocation_dataset.csv')
        df_order_items = pd.read_csv('../data/order_items_dataset.csv')
        df_order_payments = pd.read_csv('../data/order_payments_dataset.csv')
        df_order_reviews = pd.read_csv('../data/order_reviews_dataset.csv')
        df_orders = pd.read_csv('../data/orders_dataset.csv')
        df_product_category = pd.read_csv('../data/product_category_name_translation.csv')
        df_products = pd.read_csv('../data/products_dataset.csv')
        df_sellers = pd.read_csv('../data/sellers_dataset.csv')
        
        # Mengkonversi kolom tanggal ke format datetime
        order_items_col = ['shipping_limit_date']
        for col in order_items_col:
            df_order_items[col] = pd.to_datetime(df_order_items[col])
            
        order_reviews_col = ['review_creation_date', 'review_answer_timestamp']
        for col in order_reviews_col:
            df_order_reviews[col] = pd.to_datetime(df_order_reviews[col])
            
        orders_col = ['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date',
                    'order_delivered_customer_date', 'order_estimated_delivery_date']
        for col in orders_col:
            df_orders[col] = pd.to_datetime(df_orders[col])
        
        # Membersihkan data duplikat pada geolocation
        df_geolocation.drop_duplicates(inplace=True)
        
        # Mengisi nilai yang kosong (NA) pada ulasan
        df_order_reviews["review_comment_title"] = df_order_reviews["review_comment_title"].fillna("Not Available")
        df_order_reviews["review_comment_message"] = df_order_reviews["review_comment_message"].fillna("Not Available")
        
        # Mengisi nilai yang kosong (NA) pada data produk dengan nilai median
        df_products['product_name_lenght'] = df_products['product_name_lenght'].fillna(df_products['product_name_lenght'].median())
        df_products['product_description_lenght'] = df_products['product_description_lenght'].fillna(df_products['product_description_lenght'].median())
        df_products['product_photos_qty'] = df_products['product_photos_qty'].fillna(df_products['product_photos_qty'].median())
        df_products['product_weight_g'] = df_products['product_weight_g'].fillna(df_products['product_weight_g'].median())
        df_products['product_length_cm'] = df_products['product_length_cm'].fillna(df_products['product_length_cm'].median())
        df_products['product_height_cm'] = df_products['product_height_cm'].fillna(df_products['product_height_cm'].median())
        df_products['product_width_cm'] = df_products['product_width_cm'].fillna(df_products['product_width_cm'].median())
        
        # Mengembalikan semua dataset dalam bentuk dictionary
        return {
            'customers': df_customers,
            'geolocation': df_geolocation,
            'order_items': df_order_items,
            'order_payments': df_order_payments,
            'order_reviews': df_order_reviews,
            'orders': df_orders,
            'product_category': df_product_category,
            'products': df_products,
            'sellers': df_sellers
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Memuat data dengan tampilan loading spinner
with st.spinner('Memuat data... Mohon tunggu.'):
    data = load_data()

# Memeriksa apakah data berhasil dimuat
if not data:
    st.error("Gagal memuat data. Silakan periksa jalur file.")
    st.stop()

# Menu sidebar untuk navigasi
st.sidebar.title("Navigasi")
analysis_option = st.sidebar.selectbox(
    "Pilih Analisis",
    ["Overview", 
     "Geographical Purchase Patterns", 
     "Seller Performance Analysis", 
     "Payment Method Analysis", 
     "RFM & Customer Segmentation"]
)

# Halaman Overview - Ikhtisar dataset
if analysis_option == "Overview":
    st.header("Ikhtisar Dataset")
    
    # Menampilkan informasi dataset dalam bentuk tab
    datasets = ["customers", "orders", "order_items", "order_payments", "sellers", "products"]
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(datasets)
    
    with tab1:
        st.subheader("Dataset Pelanggan")
        st.write(f"Ukuran: {data['customers'].shape}")
        st.dataframe(data['customers'].head())
        
    with tab2:
        st.subheader("Dataset Pesanan")
        st.write(f"Ukuran: {data['orders'].shape}")
        st.dataframe(data['orders'].head())
        
    with tab3:
        st.subheader("Dataset Item Pesanan")
        st.write(f"Ukuran: {data['order_items'].shape}")
        st.dataframe(data['order_items'].head())
        
    with tab4:
        st.subheader("Dataset Pembayaran Pesanan")
        st.write(f"Ukuran: {data['order_payments'].shape}")
        st.dataframe(data['order_payments'].head())
        
    with tab5:
        st.subheader("Dataset Penjual")
        st.write(f"Ukuran: {data['sellers'].shape}")
        st.dataframe(data['sellers'].head())
        
    with tab6:
        st.subheader("Dataset Produk")
        st.write(f"Ukuran: {data['products'].shape}")
        st.dataframe(data['products'].head())
    
    # Menampilkan informasi nilai null dan duplikat
    st.subheader("Pemeriksaan Kualitas Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Ringkasan Nilai Null (Kosong)")
        null_data = {
            'Pelanggan': data['customers'].isna().sum().sum(),
            'Pesanan': data['orders'].isna().sum().sum(),
            'Item Pesanan': data['order_items'].isna().sum().sum(),
            'Pembayaran': data['order_payments'].isna().sum().sum(),
            'Penjual': data['sellers'].isna().sum().sum(),
            'Produk': data['products'].isna().sum().sum()
        }
        st.bar_chart(null_data)
        
    with col2:
        st.write("Ringkasan Data Duplikat")
        duplicate_data = {
            'Pelanggan': data['customers'].duplicated().sum(),
            'Pesanan': data['orders'].duplicated().sum(),
            'Item Pesanan': data['order_items'].duplicated().sum(), 
            'Pembayaran': data['order_payments'].duplicated().sum(),
            'Penjual': data['sellers'].duplicated().sum(),
            'Produk': data['products'].duplicated().sum()
        }
        st.bar_chart(duplicate_data)

# Analisis Pola Pembelian Geografis
elif analysis_option == "Geographical Purchase Patterns":
    st.header("Analisis Pola Pembelian Berdasarkan Lokasi Geografis")
    
    # Memproses data untuk analisis geografis
    @st.cache_data
    def prepare_geo_data():
        # Menggabungkan data untuk mendapatkan pesanan pelanggan dengan lokasi
        customer_orders = pd.merge(data['orders'], data['customers'], on='customer_id')
        
        # Menghitung nilai pesanan
        order_values = data['order_items'].groupby('order_id').agg({'price': 'sum', 'freight_value': 'sum'}).reset_index()
        order_values['total_value'] = order_values['price'] + order_values['freight_value']
        
        # Menggabungkan dengan customer_orders
        geo_orders = pd.merge(customer_orders, order_values, on='order_id')
        
        # Analisis berdasarkan negara bagian (state)
        state_orders = geo_orders.groupby('customer_state').agg({
            'order_id': 'count',
            'total_value': 'sum'
        }).reset_index()
        state_orders.columns = ['State', 'Order Count', 'Total Value']
        state_orders = state_orders.sort_values('Total Value', ascending=False)
        
        # Analisis berdasarkan waktu
        geo_orders['order_month'] = geo_orders['order_purchase_timestamp'].dt.to_period('M')
        monthly_state_orders = geo_orders.groupby(['order_month', 'customer_state']).agg({
            'order_id': 'count',
            'total_value': 'sum'
        }).reset_index()
        
        # Mengkonversi Period ke string untuk Plotly
        monthly_state_orders['order_month'] = monthly_state_orders['order_month'].astype(str)
        
        # Analisis berdasarkan kota
        city_orders = geo_orders.groupby(['customer_state', 'customer_city']).agg({
            'order_id': 'count',
            'total_value': 'sum'
        }).reset_index()
        city_orders = city_orders.sort_values('total_value', ascending=False)
        
        return {
            'geo_orders': geo_orders,
            'state_orders': state_orders,
            'monthly_state_orders': monthly_state_orders,
            'city_orders': city_orders
        }
    
    geo_data = prepare_geo_data()
    
    # Menampilkan analisis level negara bagian
    st.subheader("Analisis Pembelian berdasarkan Negara Bagian")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.bar(
            geo_data['state_orders'].head(10),
            x='State',
            y='Total Value',
            title="10 Negara Bagian Teratas berdasarkan Nilai Pesanan Total",
            color='Total Value',
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig1, use_container_width=True, key="geo_state_value")
        
    with col2:
        fig2 = px.bar(
            geo_data['state_orders'].head(10),
            x='State',
            y='Order Count',
            title="10 Negara Bagian Teratas berdasarkan Jumlah Pesanan",
            color='Order Count',
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig2, use_container_width=True, key="geo_state_count")
    
    # Tren bulanan untuk negara bagian teratas
    st.subheader("Tren Pembelian Bulanan untuk Negara Bagian Teratas")
    
    # Mendapatkan 5 negara bagian teratas
    top_states = geo_data['state_orders']['State'].head(5).tolist()
    
    filtered_monthly_data = geo_data['monthly_state_orders'][
        geo_data['monthly_state_orders']['customer_state'].isin(top_states)
    ]
    
    fig3 = px.line(
        filtered_monthly_data,
        x='order_month',
        y='total_value',
        color='customer_state',
        title="Tren Pembelian Bulanan untuk 5 Negara Bagian Teratas",
        labels={'order_month': 'Bulan', 'total_value': 'Nilai Pesanan Total', 'customer_state': 'Negara Bagian'}
    )
    st.plotly_chart(fig3, use_container_width=True, key="geo_monthly_trend")
    
    # Analisis kota
    st.subheader("Kota Teratas berdasarkan Nilai Pesanan")
    
    top_cities = geo_data['city_orders'].head(10)
    fig4 = px.bar(
        top_cities,
        x='customer_city',
        y='total_value',
        color='customer_state',
        title="10 Kota Teratas berdasarkan Nilai Pesanan Total",
        labels={'customer_city': 'Kota', 'total_value': 'Nilai Pesanan Total', 'customer_state': 'Negara Bagian'}
    )
    fig4.update_layout(xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig4, use_container_width=True, key="geo_cities")
    
    # Menampilkan tabel data
    with st.expander("Lihat Tabel Data"):
        st.write("Data Level Negara Bagian")
        st.dataframe(geo_data['state_orders'])
        
        st.write("Data Level Kota")
        st.dataframe(geo_data['city_orders'].head(20))

# Analisis Performa Penjual
elif analysis_option == "Seller Performance Analysis":
    st.header("Analisis Performa Penjual")
    
    # Memproses data untuk analisis performa penjual
    @st.cache_data
    def prepare_seller_data():
        # Menggabungkan data
        seller_orders = pd.merge(data['order_items'], data['sellers'], on='seller_id')
        seller_reviews = pd.merge(data['orders'][['order_id']], data['order_reviews'][['order_id', 'review_score']], on='order_id')
        seller_performance = pd.merge(seller_orders, seller_reviews, on='order_id', how='left')
        
        # Performa level negara bagian
        seller_state_performance = seller_performance.groupby('seller_state').agg({
            'order_id': 'count',
            'price': 'sum',
            'review_score': ['mean', 'count']
        })
        
        # Meratakan kolom MultiIndex
        seller_state_performance.columns = ['_'.join(col).strip('_') for col in seller_state_performance.columns.values]
        seller_state_performance = seller_state_performance.reset_index()
        seller_state_performance = seller_state_performance.sort_values('price_sum', ascending=False)
        
        # Performa penjual individu
        individual_seller_performance = seller_performance.groupby('seller_id').agg({
            'order_id': 'count',
            'price': 'sum',
            'review_score': ['mean', 'count']
        })
        
        # Meratakan kolom MultiIndex
        individual_seller_performance.columns = ['_'.join(col).strip('_') for col in individual_seller_performance.columns.values]
        individual_seller_performance = individual_seller_performance.reset_index()
        
        # Menambahkan info lokasi
        individual_seller_performance = pd.merge(
            individual_seller_performance,
            data['sellers'][['seller_id', 'seller_city', 'seller_state']],
            on='seller_id'
        )
        
        # Membuat kategori rating
        individual_seller_performance['rating_category'] = pd.cut(
            individual_seller_performance['review_score_mean'],
            bins=[0, 2, 3, 4, 5],
            labels=['1-2', '2-3', '3-4', '4-5']
        )
        
        # Analisis kelompok rating
        rating_groups = individual_seller_performance.groupby('rating_category').agg({
            'seller_id': 'count',
            'price_sum': 'mean',
            'order_id_count': 'mean'
        }).reset_index()
        
        return {
            'seller_performance': seller_performance,
            'seller_state_performance': seller_state_performance,
            'individual_seller_performance': individual_seller_performance,
            'rating_groups': rating_groups
        }
    
    seller_data = prepare_seller_data()
    
    # Menampilkan performa penjual level negara bagian
    st.subheader("Performa Penjual berdasarkan Negara Bagian")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig5 = px.bar(
            seller_data['seller_state_performance'],
            x='seller_state',
            y='price_sum',
            title="Total Penjualan berdasarkan Negara Bagian Penjual",
            color='price_sum',
            color_continuous_scale="Viridis"
        )
        fig5.update_layout(xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig5, use_container_width=True, key="seller_state_sales")
        
    with col2:
        fig6 = px.bar(
            seller_data['seller_state_performance'],
            x='seller_state',
            y='review_score_mean',
            title="Rata-rata Skor Ulasan berdasarkan Negara Bagian Penjual",
            color='review_score_mean',
            color_continuous_scale="RdYlGn"
        )
        fig6.update_layout(xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig6, use_container_width=True, key="seller_state_reviews")
    
    # Penjual teratas
    st.subheader("Penjual dengan Performa Terbaik")
    
    top_sellers = seller_data['individual_seller_performance'].sort_values('price_sum', ascending=False).head(10)
    fig7 = px.bar(
        top_sellers,
        x='seller_id',
        y='price_sum',
        color='review_score_mean',
        title="10 Penjual Teratas berdasarkan Total Penjualan",
        color_continuous_scale="RdYlGn",
        hover_data=['seller_city', 'seller_state', 'order_id_count']
    )
    st.plotly_chart(fig7, use_container_width=True, key="top_sellers")
    
    # Analisis rating
    st.subheader("Performa berdasarkan Kategori Rating")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig8 = px.bar(
            seller_data['rating_groups'],
            x='rating_category',
            y='seller_id',
            title="Jumlah Penjual berdasarkan Kategori Rating",
            labels={'seller_id': 'Jumlah Penjual', 'rating_category': 'Kategori Rating'}
        )
        st.plotly_chart(fig8, use_container_width=True, key="seller_rating_count")
        
    with col2:
        fig9 = px.bar(
            seller_data['rating_groups'],
            x='rating_category',
            y='price_sum',
            title="Rata-rata Penjualan berdasarkan Kategori Rating",
            labels={'price_sum': 'Rata-rata Penjualan (R$)', 'rating_category': 'Kategori Rating'}
        )
        st.plotly_chart(fig9, use_container_width=True, key="seller_rating_sales")
    
    # Analisis korelasi
    st.subheader("Korelasi: Skor Ulasan vs Penjualan")
    
    fig10 = px.scatter(
        seller_data['individual_seller_performance'],
        x='review_score_mean',
        y='price_sum',
        color='order_id_count',
        size='order_id_count',
        title="Korelasi antara Skor Ulasan dan Penjualan",
        labels={
            'review_score_mean': 'Rata-rata Skor Ulasan',
            'price_sum': 'Total Penjualan (R$)',
            'order_id_count': 'Jumlah Pesanan'
        }
    )
    st.plotly_chart(fig10, use_container_width=True, key="seller_correlation")
    
    correlation = seller_data['individual_seller_performance']['review_score_mean'].corr(
        seller_data['individual_seller_performance']['price_sum']
    )
    st.write(f"Koefisien korelasi antara skor ulasan dan penjualan: **{correlation:.4f}**")
    
    # Menampilkan tabel data
    with st.expander("Lihat Tabel Data"):
        st.write("Performa Level Negara Bagian")
        st.dataframe(seller_data['seller_state_performance'])
        
        st.write("Penjual Teratas")
        st.dataframe(top_sellers)
        
        st.write("Analisis Kelompok Rating")
        st.dataframe(seller_data['rating_groups'])

# Analisis Metode Pembayaran
elif analysis_option == "Payment Method Analysis":
    st.header("Analisis Metode Pembayaran")
    
    # Memproses data untuk analisis pembayaran
    @st.cache_data
    def prepare_payment_data():
        # Menggabungkan data
        payment_with_orders = pd.merge(data['order_payments'], data['orders'][['order_id', 'customer_id']], on='order_id')
        payment_with_customers = pd.merge(payment_with_orders, data['customers'][['customer_id', 'customer_state']], on='customer_id')
        
        # Statistik pembayaran berdasarkan jenis pembayaran
        payment_stats = data['order_payments'].groupby('payment_type').agg({
            'order_id': 'count',
            'payment_value': ['mean', 'median', 'min', 'max'],
            'payment_installments': ['mean', 'median', 'max']
        })
        
        # Meratakan kolom MultiIndex
        payment_stats.columns = ['_'.join(col).strip('_') for col in payment_stats.columns.values]
        payment_stats = payment_stats.reset_index()
        
        # Metode pembayaran berdasarkan negara bagian
        payment_by_state = payment_with_customers.groupby(['customer_state', 'payment_type']).size().reset_index(name='count')
        payment_by_state_pivot = payment_by_state.pivot_table(
            index='customer_state',
            columns='payment_type',
            values='count',
            fill_value=0
        )
        
        # Menghitung persentase
        payment_by_state_pct = payment_by_state_pivot.div(payment_by_state_pivot.sum(axis=1), axis=0) * 100
        payment_by_state_pct = payment_by_state_pct.reset_index()
        
        # Metode pembayaran paling populer berdasarkan negara bagian
        most_popular_payment = payment_by_state_pivot.idxmax(axis=1).reset_index()
        most_popular_payment.columns = ['customer_state', 'most_popular_payment']
        
        # Analisis cicilan kartu kredit
        credit_card_payments = data['order_payments'][data['order_payments']['payment_type'] == 'credit_card']
        avg_by_installment = credit_card_payments.groupby('payment_installments').agg({
            'payment_value': 'mean',
            'order_id': 'count'
        }).reset_index()
        
        return {
            'payment_with_customers': payment_with_customers,
            'payment_stats': payment_stats,
            'payment_by_state': payment_by_state,
            'payment_by_state_pivot': payment_by_state_pivot,
            'payment_by_state_pct': payment_by_state_pct,
            'most_popular_payment': most_popular_payment,
            'credit_card_payments': credit_card_payments,
            'avg_by_installment': avg_by_installment
        }
    
    payment_data = prepare_payment_data()
    
    # Distribusi metode pembayaran secara keseluruhan
    st.subheader("Distribusi Metode Pembayaran")
    
    payment_count = payment_data['payment_stats'][['payment_type', 'order_id_count']]
    fig11 = px.pie(
        payment_count,
        values='order_id_count',
        names='payment_type',
        title="Distribusi Metode Pembayaran",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig11, use_container_width=True, key="payment_distribution")
    
    # Statistik pembayaran
    st.subheader("Statistik Pembayaran berdasarkan Metode")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig12 = px.bar(
            payment_data['payment_stats'],
            x='payment_type',
            y='payment_value_mean',
            title="Nilai Transaksi Rata-rata berdasarkan Metode Pembayaran",
            color='payment_type'
        )
        st.plotly_chart(fig12, use_container_width=True, key="payment_value_by_type")
        
    with col2:
        fig13 = px.bar(
            payment_data['payment_stats'],
            x='payment_type',
            y='order_id_count',
            title="Jumlah Transaksi berdasarkan Metode Pembayaran",
            color='payment_type'
        )
        st.plotly_chart(fig13, use_container_width=True, key="payment_count_by_type")
    
    # Metode pembayaran berdasarkan negara bagian
    st.subheader("Metode Pembayaran berdasarkan Negara Bagian")
    
    # Mengkonversi tabel pivot ke format panjang untuk Plotly
    payment_by_state_long = pd.melt(
        payment_data['payment_by_state_pivot'].reset_index(),
        id_vars=['customer_state'],
        var_name='payment_type',
        value_name='count'
    )
    
    fig14 = px.bar(
        payment_by_state_long,
        x='customer_state',
        y='count',
        color='payment_type',
        title="Distribusi Metode Pembayaran berdasarkan Negara Bagian",
        barmode='stack'
    )
    fig14.update_layout(xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig14, use_container_width=True, key="payment_by_state")
    
    # Analisis cicilan kartu kredit
    st.subheader("Analisis Cicilan Kartu Kredit")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig15 = px.bar(
            payment_data['avg_by_installment'],
            x='payment_installments',
            y='payment_value',
            title="Nilai Transaksi Rata-rata berdasarkan Jumlah Cicilan",
            color='payment_installments'
        )
        st.plotly_chart(fig15, use_container_width=True, key="installment_value")
        
    with col2:
        fig16 = px.bar(
            payment_data['avg_by_installment'],
            x='payment_installments',
            y='order_id',
            title="Jumlah Transaksi berdasarkan Jumlah Cicilan",
            color='payment_installments'
        )
        st.plotly_chart(fig16, use_container_width=True, key="installment_count")
    
    # Grafik scatter plot jumlah cicilan vs nilai transaksi
    fig17 = px.scatter(
        payment_data['credit_card_payments'],
        x='payment_installments',
        y='payment_value',
        title="Korelasi antara Jumlah Cicilan dan Nilai Transaksi",
        opacity=0.6,
        color_discrete_sequence=['#1f77b4']
    )
    
    # Menambahkan garis tren
    fig17.update_layout(
        shapes=[
            dict(
                type='line',
                yref='y',
                xref='x',
                y0=payment_data['credit_card_payments']['payment_value'].min(),
                y1=payment_data['credit_card_payments']['payment_value'].max(),
                x0=payment_data['credit_card_payments']['payment_installments'].min(),
                x1=payment_data['credit_card_payments']['payment_installments'].max(),
                line=dict(
                    color='red',
                    width=2,
                    dash='dash'
                )
            )
        ]
    )
    
    st.plotly_chart(fig17, use_container_width=True, key="installment_correlation")
    
    # Menghitung korelasi
    installment_corr = payment_data['credit_card_payments']['payment_installments'].corr(
        payment_data['credit_card_payments']['payment_value']
    )
    st.write(f"Koefisien korelasi antara jumlah cicilan dan nilai transaksi: **{installment_corr:.4f}**")
    
    # Menampilkan tabel data
    with st.expander("Lihat Tabel Data"):
        st.write("Statistik Metode Pembayaran")
        st.dataframe(payment_data['payment_stats'])
        
        st.write("Metode Pembayaran Paling Populer berdasarkan Negara Bagian")
        st.dataframe(payment_data['most_popular_payment'])
        
        st.write("Analisis Cicilan Kartu Kredit")
        st.dataframe(payment_data['avg_by_installment'])

# Analisis RFM dan Segmentasi Pelanggan
else:  # RFM & Customer Segmentation
    st.header("Analisis RFM & Segmentasi Pelanggan")
    
    # Memproses data untuk analisis RFM
    @st.cache_data
    def prepare_rfm_data():
        # Menggabungkan pesanan dengan pembayaran untuk nilai transaksi
        order_payments = data['order_payments'].groupby('order_id')['payment_value'].sum().reset_index()
        orders_with_payments = pd.merge(data['orders'], order_payments, on='order_id')
        
        # Mendapatkan tanggal maksimum untuk perhitungan recency
        max_date = data['orders']['order_purchase_timestamp'].max()
        
        # Menghitung RFM
        rfm = orders_with_payments.groupby('customer_id').agg({
            'order_purchase_timestamp': lambda x: (max_date - x.max()).days,  # Recency
            'order_id': 'count',  # Frequency
            'payment_value': 'sum'  # Monetary
        }).reset_index()
        
        rfm.columns = ['customer_id', 'recency', 'frequency', 'monetary']
        
        # Membuat kuintil
        rfm['r_score'] = pd.qcut(rfm['recency'], q=5, labels=[5, 4, 3, 2, 1])  # 5 adalah yang terbaru
        rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5])  # 5 adalah yang paling sering
        rfm['m_score'] = pd.qcut(rfm['monetary'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5])  # 5 adalah nilai tertinggi
        
        # Menggabungkan skor
        rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
        
        # Membuat segmen
        def get_segment(rfm_score):
            r = int(rfm_score[0])
            f = int(rfm_score[1])
            m = int(rfm_score[2])

            if r >= 4 and f >= 4 and m >= 4:
                return 'Champions'
            elif r >= 3 and f >= 3 and m >= 3:
                return 'Loyal Customers'
            elif r >= 3 and f >= 1 and m >= 2:
                return 'Potential Loyalists'
            elif r >= 4 and f <= 2 and m <= 2:
                return 'New Customers'
            elif r < 2 and f > 2 and m > 2:
                return 'At Risk'
            elif r < 2 and f <= 2 and m <= 2:
                return 'Hibernating'
            elif r >= 2 and f <= 2 and m <= 2:
                return 'Needs Attention'
            else:
                return 'Others'
        
        rfm['segment'] = rfm['rfm_score'].apply(get_segment)
        
        # Ringkasan segmen
        segment_summary = rfm.groupby('segment').agg({
            'customer_id': 'count',
            'recency': 'mean',
            'frequency': 'mean',
            'monetary': 'mean'
        }).reset_index()
        
        segment_summary = segment_summary.sort_values('monetary', ascending=False)
        
        # Menambahkan data lokasi
        rfm_with_location = pd.merge(rfm, data['customers'][['customer_id', 'customer_state', 'customer_city']], on='customer_id')
        
        # Distribusi segmen berdasarkan negara bagian
        segment_by_state = rfm_with_location.groupby(['customer_state', 'segment']).size().reset_index(name='count')
        
        return {
            'rfm': rfm,
            'segment_summary': segment_summary,
            'rfm_with_location': rfm_with_location,
            'segment_by_state': segment_by_state,
            'max_date': max_date
        }
    
    rfm_data = prepare_rfm_data()
    
    # Menampilkan ikhtisar RFM
    st.subheader("Ikhtisar Analisis RFM")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Pelanggan", f"{len(rfm_data['rfm']):,}")
        
    with col2:
        st.metric("Tanggal Transaksi Terakhir", rfm_data['max_date'].strftime('%Y-%m-%d'))
        
    with col3:
        st.metric("Total Pendapatan", f"R$ {rfm_data['rfm']['monetary'].sum():,.2f}")
    
    # Segmen pelanggan
    st.subheader("Segmentasi Pelanggan")
    
    # Distribusi segmen
    segment_counts = rfm_data['rfm']['segment'].value_counts().reset_index()
    segment_counts.columns = ['Segment', 'Count']
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig18 = px.pie(
            segment_counts,
            values='Count',
            names='Segment',
            title="Distribusi Segmen Pelanggan",
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.4
        )
        st.plotly_chart(fig18, use_container_width=True, key="segment_distribution")
        
    with col2:
        fig19 = px.bar(
            rfm_data['segment_summary'],
            x='segment',
            y='customer_id',
            title="Jumlah Pelanggan berdasarkan Segmen",
            color='segment',
            labels={'customer_id': 'Jumlah Pelanggan', 'segment': 'Segmen'}
        )
        st.plotly_chart(fig19, use_container_width=True, key="segment_counts")
    
    # Karakteristik segmen
    st.subheader("Karakteristik Segmen")
    
    # Metrik rata-rata berdasarkan segmen
    fig20 = px.bar(
        rfm_data['segment_summary'],
        x='segment',
        y=['recency', 'frequency', 'monetary'],
        barmode='group',
        title="Metrik RFM Rata-rata berdasarkan Segmen",
        labels={'value': 'Nilai Rata-rata', 'segment': 'Segmen', 'variable': 'Metrik'}
    )
    st.plotly_chart(fig20, use_container_width=True, key="segment_metrics")
    
    # Fokus pada segmen bernilai tinggi
    st.subheader("Fokus pada Segmen Bernilai Tinggi")
    
    high_value_segments = ['Champions', 'Loyal Customers']
    high_value_data = rfm_data['rfm'][rfm_data['rfm']['segment'].isin(high_value_segments)]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Pelanggan Champion", 
            f"{len(rfm_data['rfm'][rfm_data['rfm']['segment'] == 'Champions']):,}",
            f"{len(rfm_data['rfm'][rfm_data['rfm']['segment'] == 'Champions']) / len(rfm_data['rfm']) * 100:.1f}%"
        )
        
    with col2:
        st.metric(
            "Pendapatan dari Champion",
            f"R$ {rfm_data['rfm'][rfm_data['rfm']['segment'] == 'Champions']['monetary'].sum():,.2f}",
            f"{rfm_data['rfm'][rfm_data['rfm']['segment'] == 'Champions']['monetary'].sum() / rfm_data['rfm']['monetary'].sum() * 100:.1f}%"
        )
    
    # Distribusi geografis segmen
    st.subheader("Distribusi Geografis Segmen")
    
    # Negara bagian teratas untuk Champions
    champions_by_state = rfm_data['segment_by_state'][rfm_data['segment_by_state']['segment'] == 'Champions']
    champions_by_state = champions_by_state.sort_values('count', ascending=False)
    
    fig21 = px.bar(
        champions_by_state.head(10),
        x='customer_state',
        y='count',
        title="10 Negara Bagian dengan Pelanggan Champion Terbanyak",
        color='count',
        labels={'customer_state': 'Negara Bagian', 'count': 'Jumlah Pelanggan Champion'}
    )
    st.plotly_chart(fig21, use_container_width=True, key="champions_by_state")
    
    # Menampilkan tabel data
    with st.expander("Lihat Tabel Data"):
        st.write("Ringkasan Segmen")
        st.dataframe(rfm_data['segment_summary'])
        
        st.write("Karakteristik Pelanggan Champion")
        st.dataframe(rfm_data['rfm'][rfm_data['rfm']['segment'] == 'Champions'].describe())
        
        st.write("Distribusi Champion berdasarkan Negara Bagian")
        st.dataframe(champions_by_state.head(10))

# Fungsi utama untuk menjalankan aplikasi
if __name__ == "__main__":
    st.sidebar.info("Dibuat dengan ❤️ menggunakan Streamlit")
    st.sidebar.markdown("---")
    st.sidebar.write("### Tentang Dashboard Ini")
    st.sidebar.write("""
    Dashboard ini menyediakan analisis komprehensif untuk data e-commerce Brasil dari Olist, 
    menampilkan pola geografis, kinerja penjual, metode pembayaran, dan segmentasi pelanggan.
    """)