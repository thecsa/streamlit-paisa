import streamlit as st
import modules.styles as styles
import modules.data_manager as dm
import modules.utils as utils
import pandas as pd
import plotly.express as px
import datetime
from streamlit_option_menu import option_menu

# Page Config
st.set_page_config(
    page_title="Finans Asistanı",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom CSS
st.markdown(styles.global_css, unsafe_allow_html=True)

# Initialize Database
dm.init_db()

# Initialize Database
dm.init_db()

# Top Navigation (Horizontal)
# User requested menu at the top, horizontal, like the image (Red active color).
page = option_menu(
    menu_title=None,  # required, but None for horizontal to hide title
    options=["Özet", "Gelir/Gider Ekle", "Yatırımlarım", "Faiz Hesapla", "Ayarlar"],  # required
    icons=["speedometer2", "wallet2", "graph-up-arrow", "calculator", "gear"],  # optional
    menu_icon="cast",  # optional
    default_index=0,  # optional
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#f8f9fa"},
        "icon": {"color": "#333", "font-size": "16px"}, 
        "nav-link": {
            "font-family": "'Segoe UI', Roboto, Helvetica, Arial, sans-serif", 
            "font-size": "16px", 
            "text-align": "center", 
            "margin":"0px", 
            "--hover-color": "#eee", 
            "color": "#333"
        },
        "nav-link-selected": {"background-color": "#ff4b4b", "color": "white", "font-weight": "normal"}, # Red color like the image, no bold
    }
)

# --- Main Content Routing ---

if page == "Özet":
    st.title("📊 Finansal Özet")
    
    # --- Calculate Metrics ---
    transactions = dm.get_transactions()
    portfolio = dm.get_portfolio()
    
    total_income = 0
    total_expense = 0
    
    if not transactions.empty:
        total_income = transactions[transactions['type'] == 'Gelir']['amount'].sum()
        total_expense = transactions[transactions['type'] == 'Gider']['amount'].sum()
        
    cash_balance = total_income - total_expense
    
    # Portfolio Value & Data for Chart
    total_portfolio_value = 0
    portfolio_chart_data = []
    
    if not portfolio.empty:
        # Fallback to cost basis if live fetch fails or for speed
        # For now, let's just use cost basis + simple logic to keep it fast
        # In a real app, we'd cache this.
        import modules.market_data as md
        
        for _, row in portfolio.iterrows():
            current_val = 0
            try:
                price = 0
                if "Fon" in row['asset_type']:
                    price = md.get_tefas_data(row['symbol'])
                else:
                    price = md.get_market_price(row['symbol'])
                    if "USD" in row['symbol']:
                        usd = md.get_usd_try_rate()
                        price = price * usd if price and usd else 0
                
                if price:
                    current_val = row['quantity'] * price
                else:
                    current_val = row['quantity'] * row['avg_cost']
            except:
                current_val = row['quantity'] * row['avg_cost']
            
            total_portfolio_value += current_val
            portfolio_chart_data.append({
                "symbol": row['symbol'],
                "current_value": current_val
            })
    
    net_worth = cash_balance + total_portfolio_value
    
    # --- Save Daily Snapshot ---
    # Automatically save today's net worth when visiting the dashboard
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    dm.save_daily_snapshot(today_str, net_worth, cash_balance, total_portfolio_value)
    
    # --- Display Metrics ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("TOPLAM VARLIK (NET)", f"{net_worth:,.2f} ₺")
    # User requested to remove the green indicator (delta)
    col2.metric("NAKİT DURUMU", f"{cash_balance:,.2f} ₺") 
    col3.metric("PORTFÖY DEĞERİ", f"{total_portfolio_value:,.2f} ₺")
    col4.metric("TOPLAM GELİR", f"{total_income:,.2f} ₺")
    
    # --- Net Worth Trend Chart (New) ---
    st.subheader("VARLIK GELİŞİMİ")
    history_df = dm.get_history()
    if not history_df.empty:
        # Line chart for Net Worth
        fig_trend = px.line(history_df, x='date', y='net_worth', markers=True)
        # Turkish formatting for numbers (decimal=, thousands=.) and Date format (dd-mm-yyyy)
        fig_trend.update_layout(
            margin=dict(t=30, b=0, l=0, r=0), 
            height=300, 
            xaxis_title=None, 
            yaxis_title=None,
            separators=",." 
        )
        fig_trend.update_xaxes(tickformat="%d-%m-%Y")
        fig_trend.update_yaxes(tickformat=",.") # Use the separators format
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Henüz geçmiş veri yok.")

    # --- Charts ---
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("GELİR / GİDER DAĞILIMI")
        if not transactions.empty:
            fig = px.pie(transactions, values='amount', names='category', color='category', hole=0.4)
            fig.update_layout(
                margin=dict(t=30, b=0, l=0, r=0), 
                height=300,
                separators=",."
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Veri yok.")
            
    with col_chart2:
        st.subheader("VARLIK DAĞILIMI")
        if portfolio_chart_data:
            chart_df = pd.DataFrame(portfolio_chart_data)
            fig2 = px.pie(chart_df, values='current_value', names='symbol', hole=0.4)
            fig2.update_layout(
                margin=dict(t=30, b=0, l=0, r=0), 
                height=300,
                separators=",."
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Portföy boş.")
            
    # --- Recent Transactions ---
    st.subheader("SON İŞLEMLER")
    if not transactions.empty:
        # Rename columns for display
        display_df = transactions.head(5).copy()
        
        # Format Date for Display
        display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%d-%m-%Y')
        
        display_df.columns = [col.upper() for col in display_df.columns]
        
        # Turkish Currency Formatting Helper
        def tr_fmt(x):
            return "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", ".") + " ₺"
            
        st.dataframe(display_df.style.format({
            "AMOUNT": tr_fmt
        }), use_container_width=True)
    else:
        st.info("Henüz işlem kaydı yok.")

elif page == "Gelir/Gider Ekle":
    st.title("💸 Gelir & Gider Yönetimi")
    
    tab1, tab2 = st.tabs(["Yeni Ekle", "Düzenle / Sil"])
    
    with tab1:
        st.subheader("Yeni İşlem Ekle")
        with st.form("transaction_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Tarih", datetime.date.today(), format="DD-MM-YYYY")
                t_type = st.selectbox("Tür", ["Gelir", "Gider"])
                category = st.text_input("Kategori (Örn: Market, Maaş, Kira)")
            
            with col2:
                amount = st.number_input("Tutar", min_value=0.0, step=0.01, format="%.2f")
                currency = st.selectbox("Para Birimi", ["TRY", "USD", "EUR"])
                description = st.text_input("Açıklama")
                
            submitted = st.form_submit_button("Kaydet")
            
            if submitted:
                if amount > 0:
                    dm.add_transaction(date, t_type, category, amount, currency, description)
                    st.success("İşlem başarıyla kaydedildi!")
                else:
                    st.error("Lütfen geçerli bir tutar giriniz.")

    with tab2:
        st.subheader("İşlem Düzenle / Sil")
        df = dm.get_transactions()
        if not df.empty:
            # Create a selection list
            df['label'] = df.apply(lambda x: f"{x['id']} | {x['date']} | {x['type']} | {x['amount']} {x['currency']} | {x['category']}", axis=1)
            selected_trans_label = st.selectbox("İşlem Seçiniz", df['label'])
            
            if selected_trans_label:
                selected_id = int(selected_trans_label.split(" | ")[0])
                selected_row = df[df['id'] == selected_id].iloc[0]
                
                with st.form("edit_transaction_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_date = st.date_input("Tarih", datetime.datetime.strptime(selected_row['date'], '%Y-%m-%d').date(), format="DD-MM-YYYY")
                        new_type = st.selectbox("Tür", ["Gelir", "Gider"], index=0 if selected_row['type'] == "Gelir" else 1)
                        new_category = st.text_input("Kategori", value=selected_row['category'])
                    with col2:
                        new_amount = st.number_input("Tutar", min_value=0.0, step=0.01, format="%.2f", value=float(selected_row['amount']))
                        new_currency = st.selectbox("Para Birimi", ["TRY", "USD", "EUR"], index=["TRY", "USD", "EUR"].index(selected_row['currency']))
                        new_description = st.text_input("Açıklama", value=selected_row['description'])
                        
                    c1, c2 = st.columns(2)
                    with c1:
                        update_submitted = st.form_submit_button("Güncelle")
                    with c2:
                        delete_submitted = st.form_submit_button("Sil", type="primary")
                        
                    if update_submitted:
                        dm.update_transaction(selected_id, new_date, new_type, new_category, new_amount, new_currency, new_description)
                        st.success("İşlem güncellendi!")
                        st.rerun()
                        
                    if delete_submitted:
                        dm.delete_transaction(selected_id)
                        st.warning("İşlem silindi!")
                        st.rerun()
        else:
            st.info("Düzenlenecek işlem bulunamadı.")

    st.markdown("---")
    st.subheader("SON İŞLEMLER")
    # Refresh data
    df = dm.get_transactions()
    if not df.empty:
        if 'label' in df.columns:
            df = df.drop(columns=['label'])
        # Rename columns for display
        display_df = df.copy()
        
        # Format Date for Display
        display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%d-%m-%Y')
        
        display_df.columns = [col.upper() for col in display_df.columns]
        
        # Turkish Currency Formatting Helper
        def tr_fmt(x):
            return "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", ".") + " ₺"

        st.dataframe(display_df.style.format({
            "AMOUNT": tr_fmt
        }), use_container_width=True)
    else:
        st.info("Henüz işlem kaydı yok.")

elif page == "Yatırımlarım":
    st.title("📈 Portföy ve Yatırımlar")
    
    # --- Investment Actions ---
    with st.expander("Yatırım İşlemi Yap (Al/Sat)", expanded=False):
        st.markdown("##### 1. Varlık Seçimi ve Fiyat")
        # Inputs outside form to allow interaction (Price Fetch)
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            asset_type = st.selectbox("Varlık Tipi", ["Fon (TEFAS)", "Kripto/Borsa", "Döviz/Altın"])
        with c2:
            symbol = st.text_input("Sembol (Örn: TCD, BTC-USD, TRY=X)")
        with c3:
            st.write("") # Spacer for alignment
            st.write("") 
            if st.button("Fiyat Getir", use_container_width=True):
                if symbol:
                    import modules.market_data as md
                    try:
                        fetched_price = 0
                        with st.spinner('Fiyat çekiliyor...'):
                            if "Fon" in asset_type:
                                fetched_price = md.get_tefas_data(symbol)
                            else:
                                fetched_price = md.get_market_price(symbol)
                                if "USD" in symbol:
                                    usd_rate = md.get_usd_try_rate()
                                    fetched_price = fetched_price * usd_rate if fetched_price and usd_rate else 0
                        
                        if fetched_price:
                            st.session_state['last_price'] = fetched_price
                            st.success(f"Fiyat: {fetched_price:,.2f} TL")
                        else:
                            st.error("Bulunamadı")
                    except Exception as e:
                        st.error(f"Hata: {e}")
                else:
                    st.warning("Sembol giriniz")

        st.markdown("##### 2. İşlem Detayları")
        with st.form("invest_form"):
            f1, f2, f3, f4 = st.columns(4)
            with f1:
                action = st.selectbox("İşlem", ["Alış", "Satış"])
            with f2:
                date = st.date_input("Tarih", datetime.date.today(), format="DD-MM-YYYY")
            with f3:
                quantity = st.number_input("Adet", min_value=0.0, step=0.01)
            with f4:
                # Use session state for price value
                default_price = st.session_state.get('last_price', 0.0)
                price = st.number_input("Birim Fiyat (TL)", min_value=0.0, step=0.01, value=float(default_price), format="%.2f")
                
            submitted = st.form_submit_button("İşlemi Onayla", type="primary", use_container_width=True)
            
            if submitted:
                if quantity > 0 and price > 0 and symbol:
                    total_amount = quantity * price
                    
                    if action == "Alış":
                        dm.update_portfolio(asset_type, symbol, quantity, price, "Buy")
                        dm.add_transaction(date, "Gider", "Yatırım", total_amount, "TRY", f"{symbol} Alış")
                        st.success(f"{symbol} alındı ve portföye eklendi.")
                        
                    elif action == "Satış":
                        dm.update_portfolio(asset_type, symbol, quantity, price, "Sell")
                        dm.add_transaction(date, "Gelir", "Yatırım", total_amount, "TRY", f"{symbol} Satış")
                        st.success(f"{symbol} satıldı ve gelir kaydedildi.")
                else:
                    st.error("Lütfen miktar, fiyat ve sembol bilgilerini kontrol ediniz.")

    # --- Edit/Delete Assets ---
    with st.expander("Varlık Düzenle / Sil (Hata Düzeltme)", expanded=False):
        p_df = dm.get_portfolio()
        if not p_df.empty:
            p_df['label'] = p_df.apply(lambda x: f"{x['id']} | {x['symbol']} | Adet: {x['quantity']} | Ort.Mal: {x['avg_cost']}", axis=1)
            selected_asset_label = st.selectbox("Varlık Seçiniz", p_df['label'])
            
            if selected_asset_label:
                sel_id = int(selected_asset_label.split(" | ")[0])
                sel_row = p_df[p_df['id'] == sel_id].iloc[0]
                
                with st.form("edit_asset_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_qty = st.number_input("Adet", min_value=0.0, step=0.01, value=float(sel_row['quantity']))
                    with c2:
                        new_avg = st.number_input("Ortalama Maliyet (TL)", min_value=0.0, step=0.01, value=float(sel_row['avg_cost']))
                        
                    col_up, col_del = st.columns(2)
                    with col_up:
                        up_sub = st.form_submit_button("Güncelle")
                    with col_del:
                        del_sub = st.form_submit_button("Sil", type="primary")
                        
                    if up_sub:
                        dm.edit_portfolio_asset(sel_id, new_qty, new_avg)
                        st.success("Varlık güncellendi!")
                        st.rerun()
                        
                    if del_sub:
                        dm.delete_portfolio_asset(sel_id)
                        st.warning("Varlık silindi!")
                        st.rerun()
        else:
            st.info("Düzenlenecek varlık yok.")

    # --- Portfolio View ---
    st.subheader("Mevcut Portföy")
    portfolio_df = dm.get_portfolio()
    
    if not portfolio_df.empty:
        import modules.market_data as md
        
        portfolio_data = []
        total_portfolio_value = 0
        
        progress_bar = st.progress(0)
        total_assets = len(portfolio_df)
        
        for idx, row in portfolio_df.iterrows():
            symbol = row['symbol']
            qty = row['quantity']
            avg_cost = row['avg_cost']
            asset_type = row['asset_type']
            
            # Fetch Price
            current_price = 0
            try:
                if "Fon" in asset_type:
                    price = md.get_tefas_data(symbol)
                    current_price = price if price else avg_cost
                else:
                    price = md.get_market_price(symbol)
                    if "USD" in symbol:
                        usd_rate = md.get_usd_try_rate()
                        current_price = price * usd_rate if price and usd_rate else avg_cost
                    else:
                        current_price = price if price else avg_cost
            except:
                current_price = avg_cost
            
            current_value = qty * current_price
            total_portfolio_value += current_value
            
            profit_loss = current_value - (qty * avg_cost)
            profit_loss_pct = (profit_loss / (qty * avg_cost)) * 100 if avg_cost > 0 else 0
            
            portfolio_data.append({
                "Sembol": symbol,
                "Adet": qty,
                "Ort. Maliyet": avg_cost,
                "Anlık Fiyat": current_price,
                "Toplam Değer": current_value,
                "K/Z (TL)": profit_loss,
                "K/Z (%)": profit_loss_pct
            })
            progress_bar.progress((idx + 1) / total_assets)
            
        progress_bar.empty()
        
        # Create DataFrame
        res_df = pd.DataFrame(portfolio_data)
        
        # Calculate Totals for Summary (Moved above table)
        total_value = res_df["Toplam Değer"].sum()
        total_pl = res_df["K/Z (TL)"].sum()
        total_pl_pct = (total_pl / (total_value - total_pl)) * 100 if (total_value - total_pl) != 0 else 0

        # Display Summary Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Portföy Değeri", f"{total_value:,.2f} ₺")
        col2.metric("Toplam Kar/Zarar (TL)", f"{total_pl:,.2f} ₺")
        col3.metric("Toplam Kar/Zarar (%)", f"%{total_pl_pct:.2f}")

        # Rename columns to UPPERCASE as requested
        res_df.columns = [col.upper() for col in res_df.columns]
        
        # Turkish Currency Formatting Helper
        def tr_fmt(x):
            return "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", ".") + " ₺"
        
        # Formatting
        st.dataframe(res_df.style.format({
            "ADET": "{:,.2f}",
            "ORT. MALIYET": tr_fmt,
            "ANLIK FIYAT": tr_fmt,
            "TOPLAM DEĞER": tr_fmt,
            "K/Z (TL)": tr_fmt,
            "K/Z (%)": "{:+.2f}%"
        }), use_container_width=True)
        
    else:
        st.info("Portföyünüz boş.")

elif page == "Faiz Hesapla":
    st.title("🧮 Faiz Getirisi Hesapla")
    
    # Calculate current cash balance for default value
    transactions = dm.get_transactions()
    current_cash = 0.0
    if not transactions.empty:
        inc = transactions[transactions['type'] == 'Gelir']['amount'].sum()
        exp = transactions[transactions['type'] == 'Gider']['amount'].sum()
        current_cash = inc - exp
        
    col1, col2, col3 = st.columns(3)
    with col1:
        # User requested: "ana para her zaman kullanıcının elinde olan kalan toplam para olacak"
        cash = st.number_input("ANA PARA (TL)", min_value=0.0, step=1000.0, value=float(current_cash))
    with col2:
        annual_rate = st.number_input("YILLIK FAİZ ORANI (%)", min_value=0.0, max_value=100.0, value=50.0)
    with col3:
        tax_rate = st.number_input("STOPAJ ORANI (%)", min_value=0.0, max_value=100.0, value=5.0)
    
    rate_decimal = annual_rate / 100.0
    tax_decimal = tax_rate / 100.0
    
    daily_return = ((pow((1 + rate_decimal), (1/365)) - 1) * (1 - tax_decimal)) * cash
    
    st.metric(label="Günlük Net Getiri", value=f"{daily_return:,.2f} ₺")
    
    if st.button("📅 Günlük Getiriyi Gelir Olarak Ekle"):
        today = datetime.date.today()
        dm.add_transaction(
            date=today,
            type="Gelir",
            category="Faiz",
            amount=daily_return,
            currency="TRY",
            description=f"Günlük Faiz Getirisi (%{annual_rate})"
        )
        st.success(f"{today} tarihine {daily_return:,.2f} TL faiz geliri eklendi!")

elif page == "Ayarlar":
    st.title("⚙️ Ayarlar")
    st.write("Veritabanı ve uygulama ayarları.")
    
    st.markdown("### ⚠️ Tehlikeli Bölge")
    st.warning("Veritabanını sıfırlamak tüm verilerinizi (işlemler ve portföy) kalıcı olarak silecektir.")
    
    confirm_reset = st.checkbox("Tüm verileri silmek istediğime eminim.")
    
    if st.button("Veritabanını Sıfırla", type="primary", disabled=not confirm_reset):
        dm.reset_db()
        st.success("Veritabanı başarıyla sıfırlandı! Sayfa yenileniyor...")
        st.rerun()

# Footer
st.markdown("---")
st.caption("v1.0.0 | Kişisel Finans Asistanı")
