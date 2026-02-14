import streamlit as st
import pandas as pd
from datetime import datetime
import database as db
from PIL import Image
import os

# Page Config
st.set_page_config(page_title="نظام إدارة مخبز الوفاء", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for RTL and Mobile
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        direction: rtl;
    }
    .main {
        direction: rtl;
        text-align: right;
    }
    div.stButton > button:first-child {
        width: 100%;
    }
    .metric-card {
        background: linear-gradient(135deg, #fff5e6 0%, #ffcc80 100%);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #ffb74d;
    }
    .metric-card h3 {
        color: #5d4037;
        font-size: 1.1rem;
        margin-bottom: 10px;
    }
    .metric-card h2 {
        color: #d84315;
        font-size: 1.8rem;
    }
    /* Fix for RTL text alignment in inputs */
    input {
        text-align: right;
        direction: rtl;
    }
    .stNumberInput label, .stTextInput label {
        text-align: right;
        display: block;
        width: 100%;
        color: #5d4037;
        font-weight: bold;
    }
    h1, h2, h3 {
        color: #5d4037;
        text-align: right;
    }
    .stButton button {
        background-color: #d84315 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar Navigation
if os.path.exists("/home/ubuntu/alwafaa_bakery/logo.png"):
    st.sidebar.image("/home/ubuntu/alwafaa_bakery/logo.png", width=150)
st.sidebar.title("مخبز الوفاء")
menu = st.sidebar.radio("القائمة الرئيسية", ["الإنتاج اليومي", "المبيعات والتوزيع", "مبيعات أخرى", "المصروفات", "إدارة الديون", "التقارير", "الإعدادات"])

selected_date = st.sidebar.date_input("اختر التاريخ", datetime.now()).strftime('%Y-%m-%d')

# 1. Production Logic
if menu == "الإنتاج اليومي":
    st.header("📦 الإنتاج اليومي")
    
    # Load existing data if any
    existing_prod = db.get_data("production", selected_date)
    default_bags = float(existing_prod['flour_bags'].iloc[0]) if not existing_prod.empty else 0.0
    
    flour_bags = st.number_input("عدد أكياس الدقيق", min_value=0.0, step=0.5, format="%.1f", value=default_bags)
    expected_production = int(flour_bags * 1600)
    
    st.info(f"الإنتاج المتوقع: {expected_production} قرص (روتي)")
    
    if st.button("حفظ بيانات الإنتاج"):
        db.save_production(selected_date, flour_bags, expected_production)
        st.success("تم حفظ بيانات الإنتاج بنجاح!")

# 2. Daily Sales & Distribution
elif menu == "المبيعات والتوزيع":
    st.header("🚚 المبيعات والتوزيع")
    distributors = ["هيثم", "وجيه", "المفرش", "علي", "درهم", "كاش"]
    
    # Load existing sales for the date
    existing_sales = db.get_data("sales", selected_date)
    
    sales_data = []
    cols = st.columns(2)
    
    for i, dist in enumerate(distributors):
        with cols[i % 2]:
            st.subheader(f"الموزع: {dist}")
            
            # Get existing values if available
            dist_row = existing_sales[existing_sales['distributor'] == dist]
            def_del = int(dist_row['delivered'].iloc[0]) if not dist_row.empty else 0
            def_ret = int(dist_row['returned'].iloc[0]) if not dist_row.empty else 0
            def_cash = float(dist_row['cash_paid'].iloc[0]) if not dist_row.empty else 0.0
            
            delivered = st.number_input(f"الكمية المسلمة ({dist})", min_value=0, key=f"del_{dist}", value=def_del)
            returned = st.number_input(f"الكمية المرتجعة ({dist})", min_value=0, key=f"ret_{dist}", value=def_ret)
            cash_paid = st.number_input(f"المبلغ المدفوع نقداً ({dist})", min_value=0.0, key=f"cash_{dist}", value=def_cash)
            
            net_sales = delivered - returned
            
            # Pricing logic from database (Individual prices for distributors)
            if dist == "كاش":
                price = db.get_setting('price_cash', 20)
            elif dist in ["هيثم", "وجيه", "المفرش", "علي", "درهم"]:
                price = db.get_distributor_price(dist, 16)
            else:
                price = db.get_setting('price_factory', 15)
                
            total_amount = net_sales * price
            sales_data.append({
                "distributor": dist,
                "delivered": delivered,
                "returned": returned,
                "net_sales": net_sales,
                "price": price,
                "total_amount": total_amount,
                "cash_paid": cash_paid
            })
            st.write(f"صافي المبيعات: {net_sales} | السعر: {price} | الإجمالي: {total_amount:,.0f} ريال")
            st.divider()

    if st.button("حفظ بيانات المبيعات"):
        for data in sales_data:
            db.save_sales(selected_date, data['distributor'], data['delivered'], data['returned'], 
                         data['net_sales'], data['price'], data['total_amount'], data['cash_paid'])
        st.success("تم حفظ بيانات المبيعات بنجاح!")

# 3. Other Sales
elif menu == "مبيعات أخرى":
    st.header("🥐 مبيعات أخرى")
    items = ["روتي طويل", "كيك", "خبز", "فحم"]
    
    existing_other = db.get_data("other_sales", selected_date)
    
    for item in items:
        item_row = existing_other[existing_other['item_name'] == item]
        def_val = float(item_row['amount'].iloc[0]) if not item_row.empty else 0.0
        
        amount = st.number_input(f"مبيعات {item} (ريال)", min_value=0.0, key=f"other_{item}", value=def_val)
        if st.button(f"حفظ {item}", key=f"btn_{item}"):
            db.save_other_sales(selected_date, item, amount)
            st.success(f"تم حفظ مبيعات {item}")

# 4. Expenses
elif menu == "المصروفات":
    st.header("💸 المصروفات")
    
    existing_exp = db.get_data("expenses", selected_date)
    
    # Get flour bags for misc calculation
    prod_df = db.get_data("production", selected_date)
    bags = prod_df['flour_bags'].iloc[0] if not prod_df.empty else 0
    misc_calc = bags * 1000
    
    def_labor = float(existing_exp['labor'].iloc[0]) if not existing_exp.empty else 53000.0
    def_wood = float(existing_exp['wood'].iloc[0]) if not existing_exp.empty else 20000.0
    def_misc = float(existing_exp['misc'].iloc[0]) if not existing_exp.empty else float(misc_calc)
    
    labor = st.number_input("أجور العمال", value=def_labor)
    wood = st.number_input("قيمة الحطب", value=def_wood)
    misc = st.number_input("مصاريف أخرى (1000 لكل كيس)", value=def_misc)
    
    total_exp = labor + wood + misc
    
    st.warning(f"إجمالي المصروفات: {total_exp:,.0f} ريال يمني")
    
    if st.button("حفظ المصروفات"):
        db.save_expenses(selected_date, labor, wood, misc, total_exp)
        st.success("تم حفظ المصروفات بنجاح!")

# 5. Debt Management (Dain & Madin)
elif menu == "إدارة الديون":
    st.header("📒 سجل الأستاذ (دائن ومدين)")
    
    tab1, tab2 = st.tabs(["📊 ملخص الحسابات", "➕ إضافة قيد يدوي"])
    
    with tab1:
        # Combine Sales data and Ledger data
        sales_df = db.get_data("sales")
        ledger_df = db.get_data("ledger")
        
        # Process Sales into Debit/Credit
        if not sales_df.empty:
            sales_ledger = sales_df.copy()
            sales_ledger = sales_ledger.rename(columns={'distributor': 'name', 'total_amount': 'debit', 'cash_paid': 'credit'})
            sales_ledger['description'] = "مبيعات يومية"
            sales_ledger = sales_ledger[['date', 'name', 'description', 'debit', 'credit']]
        else:
            sales_ledger = pd.DataFrame(columns=['date', 'name', 'description', 'debit', 'credit'])
            
        # Combine with manual ledger entries
        full_ledger = pd.concat([sales_ledger, ledger_df], ignore_index=True)
        
        if not full_ledger.empty:
            names = full_ledger['name'].unique()
            selected_name = st.selectbox("اختر الاسم لعرض كشف الحساب", ["الكل"] + list(names))
            
            if selected_name != "الكل":
                filtered_df = full_ledger[full_ledger['name'] == selected_name]
            else:
                filtered_df = full_ledger
                
            summary = filtered_df.groupby('name').agg({
                'debit': 'sum',
                'credit': 'sum'
            }).reset_index()
            summary['balance'] = summary['debit'] - summary['credit']
            
            # Display Summary Cards
            total_debit = summary['debit'].sum()
            total_credit = summary['credit'].sum()
            total_balance = total_debit - total_credit
            
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("إجمالي عليه (مدين)", f"{total_debit:,.0f} ريال")
            sc2.metric("إجمالي له (دائن)", f"{total_credit:,.0f} ريال")
            sc3.metric("الرصيد المتبقي", f"{total_balance:,.0f} ريال")
            
            st.divider()
            st.subheader("تفاصيل العمليات")
            
            # Formatting for display
            display_df = filtered_df.sort_values('date', ascending=False).rename(columns={
                'date': 'التاريخ',
                'name': 'الاسم',
                'description': 'البيان',
                'debit': 'عليه (مدين)',
                'credit': 'له (دائن)'
            })
            st.dataframe(display_df.style.format({
                'عليه (مدين)': '{:,.0f}',
                'له (دائن)': '{:,.0f}'
            }), use_container_width=True)
        else:
            st.info("لا توجد بيانات حسابات حالياً.")

    with tab2:
        st.subheader("إضافة قيد مالي جديد")
        with st.form("ledger_form"):
            l_date = st.date_input("تاريخ القيد", datetime.now()).strftime('%Y-%m-%d')
            l_name = st.selectbox("الاسم", ["هيثم", "وجيه", "المفرش", "علي", "درهم", "كاش", "أخرى"])
            if l_name == "أخرى":
                l_name = st.text_input("اكتب الاسم الجديد")
            
            l_desc = st.text_input("البيان (مثلاً: دفعة من الحساب، سلفة، إلخ)")
            l_type = st.radio("نوع العملية", ["عليه (مدين - دين جديد)", "له (دائن - تسديد مبلغ)"], horizontal=True)
            l_amount = st.number_input("المبلغ (ريال)", min_value=0.0)
            
            submit_l = st.form_submit_button("حفظ القيد")
            if submit_l:
                if l_type == "عليه (مدين - دين جديد)":
                    db.add_ledger_entry(l_date, l_name, l_desc, debit=l_amount, credit=0)
                else:
                    db.add_ledger_entry(l_date, l_name, l_desc, debit=0, credit=l_amount)
                st.success(f"تم حفظ القيد لـ {l_name} بنجاح!")
                st.rerun()

# 6. Reports & Dashboard
elif menu == "التقارير":
    st.header("📊 التقارير والنتائج")
    
    report_type = st.radio("نوع التقرير", ["تقرير يومي", "تقرير شهري"], horizontal=True)
    
    if report_type == "تقرير يومي":
        st.subheader(f"تقرير يوم {selected_date}")
        
        # Calculations
        prod_df = db.get_data("production", selected_date)
        sales_df = db.get_data("sales", selected_date)
        other_df = db.get_data("other_sales", selected_date)
        exp_df = db.get_data("expenses", selected_date)
        
        expected = prod_df['expected_production'].sum() if not prod_df.empty else 0
        total_net_sales = sales_df['net_sales'].sum() if not sales_df.empty else 0
        deficit = expected - total_net_sales
        price_dist = db.get_setting('price_distributor', 16)
        loss_value = deficit * price_dist
        
        rev_dist = sales_df['total_amount'].sum() if not sales_df.empty else 0
        rev_other = other_df['amount'].sum() if not other_df.empty else 0
        total_rev = rev_dist + rev_other
        
        total_exp = exp_df['total_expenses'].sum() if not exp_df.empty else 0
        net_profit = total_rev - total_exp - loss_value
        
        # Dashboard
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div class='metric-card'><h3>إجمالي الإيرادات</h3><h2>{total_rev:,.0f}</h2><p>ريال يمني</p></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><h3>إجمالي المصروفات</h3><h2>{total_exp:,.0f}</h2><p>ريال يمني</p></div>", unsafe_allow_html=True)
        with c3:
            color = "green" if net_profit >= 0 else "red"
            st.markdown(f"<div class='metric-card'><h3>صافي الربح</h3><h2 style='color:{color}'>{net_profit:,.0f}</h2><p>ريال يمني</p></div>", unsafe_allow_html=True)
        
        st.divider()
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"**الإنتاج المتوقع:** {expected} قرص")
            st.write(f"**المبيعات الفعلية:** {total_net_sales} قرص")
        with col_b:
            st.write(f"**العجز في الإنتاج:** {deficit} قرص")
            st.write(f"**قيمة الخسارة من العجز:** {loss_value:,.0f} ريال")
        
        st.divider()
        st.subheader("🚚 تفاصيل مبيعات الموزعين")
        if not sales_df.empty:
            # Filter only rows with actual sales to keep it clean
            active_sales = sales_df[sales_df['net_sales'] > 0].copy()
            if not active_sales.empty:
                display_sales = active_sales[['distributor', 'net_sales', 'total_amount', 'cash_paid']].rename(columns={
                    'distributor': 'الموزع',
                    'net_sales': 'الكمية المباعة',
                    'total_amount': 'المبلغ الإجمالي',
                    'cash_paid': 'المدفوع نقداً'
                })
                st.dataframe(display_sales.style.format({
                    'المبلغ الإجمالي': '{:,.0f}',
                    'المدفوع نقداً': '{:,.0f}'
                }), use_container_width=True)
            else:
                st.info("لا توجد مبيعات مسجلة لهذا اليوم حتى الآن.")
        else:
            st.info("يرجى إدخال بيانات المبيعات في قسم 'المبيعات والتوزيع' أولاً.")

    else:
        st.subheader("التقرير الشهري")
        col_m, col_y = st.columns(2)
        with col_m:
            month = st.selectbox("اختر الشهر", range(1, 13), index=datetime.now().month-1)
        with col_y:
            year = st.number_input("السنة", value=datetime.now().year)
        
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-31"
        
        sales_month = db.get_data("sales", start_date=start_date, end_date=end_date)
        exp_month = db.get_data("expenses", start_date=start_date, end_date=end_date)
        other_month = db.get_data("other_sales", start_date=start_date, end_date=end_date)
        
        if not sales_month.empty:
            total_m_rev = sales_month['total_amount'].sum() + other_month['amount'].sum()
            total_m_exp = exp_month['total_expenses'].sum()
            
            # Monthly Dashboard
            st.write(f"### 📅 ملخص شهر {month} / {year}")
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("إجمالي الإيرادات", f"{total_m_rev:,.0f} ريال")
            mc2.metric("إجمالي المصروفات", f"{total_m_exp:,.0f} ريال")
            mc3.metric("صافي الربح", f"{(total_m_rev - total_m_exp):,.0f} ريال")
            
            st.divider()
            
            # Charts
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.subheader("📈 منحنى المبيعات اليومي")
                daily_sales = sales_month.groupby('date')['total_amount'].sum().reset_index()
                st.line_chart(daily_sales.set_index('date'))
            
            with col_chart2:
                st.subheader("📊 توزيع المبيعات حسب الموزع")
                dist_sales = sales_month.groupby('distributor')['total_amount'].sum().reset_index()
                st.bar_chart(dist_sales.set_index('distributor'))
            
            st.divider()
            st.subheader("📑 تفاصيل الشهر")
            st.dataframe(sales_month[['date', 'distributor', 'net_sales', 'total_amount']].rename(columns={
                'date': 'التاريخ',
                'distributor': 'الموزع',
                'net_sales': 'الكمية',
                'total_amount': 'المبلغ'
            }), use_container_width=True)
        else:
            st.info("لا توجد بيانات لهذا الشهر.")

# 7. Settings
elif menu == "الإعدادات":
    st.header("⚙️ إعدادات النظام والأسعار")
    
    tab_gen, tab_dist = st.tabs(["⚙️ إعدادات عامة", "🚚 أسعار الموزعين"])
    
    with tab_gen:
        st.subheader("تعديل أسعار البيع العامة (ريال يمني)")
        curr_cash = db.get_setting('price_cash', 20)
        curr_factory = db.get_setting('price_factory', 15)
        
        with st.form("gen_settings_form"):
            new_cash = st.number_input("سعر البيع المباشر (كاش)", value=float(curr_cash), step=1.0)
            new_factory = st.number_input("سعر المصانع / أخرى", value=float(curr_factory), step=1.0)
            
            if st.form_submit_button("حفظ الإعدادات العامة"):
                db.update_setting('price_cash', new_cash)
                db.update_setting('price_factory', new_factory)
                st.success("تم تحديث الأسعار العامة بنجاح!")
                st.rerun()

    with tab_dist:
        st.subheader("تعديل أسعار الموزعين (كل موزع على حدة)")
        distributors_list = ["هيثم", "وجيه", "المفرش", "علي", "درهم"]
        
        with st.form("dist_settings_form"):
            new_prices = {}
            cols = st.columns(2)
            for i, d in enumerate(distributors_list):
                with cols[i % 2]:
                    curr_p = db.get_distributor_price(d, 16)
                    new_prices[d] = st.number_input(f"سعر الموزع: {d}", value=float(curr_p), step=0.5, key=f"set_p_{d}")
            
            if st.form_submit_button("حفظ أسعار الموزعين"):
                for d, p in new_prices.items():
                    db.update_distributor_price(d, p)
                st.success("تم تحديث أسعار الموزعين بنجاح!")
                st.rerun()
            
    st.divider()
    st.subheader("💾 النسخ الاحتياطي للبيانات")
    st.write("يمكنك تحميل نسخة من قاعدة البيانات لحفظها في OneDrive أو أي مكان آمن.")
    
    try:
        with open("bakery.db", "rb") as f:
            db_bytes = f.read()
            st.download_button(
                label="📥 تحميل نسخة احتياطية من قاعدة البيانات (bakery.db)",
                data=db_bytes,
                file_name=f"bakery_backup_{selected_date}.db",
                mime="application/x-sqlite3"
            )
    except Exception as e:
        st.error("فشل في الوصول إلى ملف قاعدة البيانات.")

    st.divider()
    st.info("ملاحظة: تغيير الأسعار سيؤثر على العمليات الجديدة التي يتم تسجيلها بعد التعديل.")
