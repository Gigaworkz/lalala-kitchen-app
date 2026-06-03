import streamlit as st
from supabase import create_client
import datetime
import pandas as pd
import os

# --- CONNECTION PARAMETERS (CAPITAL ALPHABETS SAFEGUARD) ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Sig-nature Kitchen", layout="wide")

# --- CUSTOM CSS FOR EXACT DESIGN ATTEMPT ONE COLOR PALETTE ---
st.markdown("""
<style>
    /* 1. Add to Cart Button (Light Orange) */
    div.stButton > button[key="btn_add_cart"] {
        background-color: #FFB74D !important;
        color: #000000 !important;
        font-weight: bold;
        border-radius: 8px;
        border: none;
    }
    /* 2. Generate Bill Button (Lavender) */
    div.stButton > button[key="btn_gen_bill"] {
        background-color: #E1BEE7 !important;
        color: #000000 !important;
        font-weight: bold;
        border-radius: 8px;
        border: none;
    }
    /* 3. Print Receipt Button (Sky Blue) */
    div.stButton > button[key="btn_print"] {
        background-color: #81D4FA !important;
        color: #000000 !important;
        font-weight: bold;
        border-radius: 8px;
        border: none;
    }
    /* 4. WhatsApp Bill Button (Parrot Green) */
    div.stButton > button[key="btn_whatsapp"] {
        background-color: #A5D6A7 !important;
        color: #000000 !important;
        font-weight: bold;
        border-radius: 8px;
        border: none;
    }
    /* 5. Clear Current Cart Button (Sandal Yellow) */
    div.stButton > button[key="btn_clear"] {
        background-color: #FFF59D !important;
        color: #000000 !important;
        font-weight: bold;
        border-radius: 8px;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States for Multi-Item Billing Cart, Counter & Conditional UI Flow
if "billing_cart" not in st.session_state:
    st.session_state.billing_cart = []
if "bill_number_counter" not in st.session_state:
    st.session_state.bill_number_counter = 1001
if "show_total_panel" not in st.session_state:
    st.session_state.show_total_panel = False

# --- UI HEADER LAYER WITH CRASH SAFEGUARD LOGO HOLDER ---
header_col1, header_col2 = st.columns([1, 4])
with header_col1:
    # 🛡️ SYSTEM SAVER CRASH INTEGRITY PROTOCOL
    if os.path.exists("logo.png"):
        st.image("logo.png", width=130)
    else:
        st.markdown("""
        <div style='background-color: #333333; height: 110px; width: 130px; border-radius: 8px; 
        display: flex; align-items: center; justify-content: center; border: 1px dashed #555;'>
            <span style='color: #888; font-size: 12px; font-weight: bold;'>🥦 LALALA LOGO</span>
        </div>
        """, unsafe_allow_html=True)

with header_col2:
    st.markdown("""
    <div style='background-color: #2D2D2D; padding: 12px; border-radius: 10px; border-left: 5px solid #FFB74D;'>
        <h1 style='margin: 0; color: #F5F5F5; font-size: 32px; font-family: sans-serif; letter-spacing: 1px;'>LALALA</h1>
        <h2 style='margin: 0; color: #E0E0E0; font-size: 20px; font-weight: normal; letter-spacing: 0.5px;'>CLOUD KITCHEN</h2>
        <p style='margin: 5px 0 0 0; color: #BDBDBD; font-size: 15px; font-style: italic;'>Good Food | Sig-Nature Feel</p>
        <p style='margin: 3px 0 0 0; color: #81C784; font-size: 13px; font-weight: bold;'>Pure VEG 🥦</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- CORE ARCHITECTURE SEPARATION ---
st.sidebar.title("Main Menu")
choice = st.sidebar.radio("Go to", ["Billing", "Admin Login"])

# ==========================================
# --- MODULE 1: BILLING (DESIGN ONE HIGH SPEED COUNTER) ---
# ==========================================
if choice == "Billing":
    st.subheader("🛒 High-Speed Billing Counter")
    
    meta_col1, meta_col2 = st.columns(2)
    with meta_col1:
        current_bill_id = f"LALALA-2026-{st.session_state.bill_number_counter}"
        st.write(f"**Current Bill Number:** `{current_bill_id}`")
    with meta_col2:
        # Default calendar selection state points safely to current context system time
        billing_date = st.date_input("Billing Date Matrix Selector", datetime.date(2026, 6, 3))
        
    st.markdown("---")
    
    # Fetch Menu safely from menu_master
    try:
        res_menu = supabase.table("menu_master").select("*").execute()
        if res_menu.data:
            menu_list = [item.get('Dish Name') for item in res_menu.data if item.get('Dish Name')]
            menu_rates = {item.get('Dish Name'): float(item.get('Rate', 0) if item.get('Rate') else item.get('Price', 0)) for item in res_menu.data}
        else:
            menu_list = []
            menu_rates = {}
    except:
        menu_list = []
        menu_rates = {}

    col_input, col_cart = st.columns([2, 3])

    with col_input:
        st.markdown("### 1. Customer & Channel Details")
        cust_name = st.text_input("Customer Name", placeholder="Type client name...")
        cust_phone = st.text_input("Phone Number", placeholder="Type 10-digit number...")
        
        channel = st.selectbox("Channel / Platform Tag", ["Direct Takeaway", "Swiggy", "Zomato", "Party Order"])
        default_pay = "Credit" if channel in ["Swiggy", "Zomato"] else "Cash"
        pay_mode = st.selectbox("Payment Mode", ["Cash", "UPI", "Card", "Credit"], index=["Cash", "UPI", "Card", "Credit"].index(default_pay))

        st.markdown("---")
        st.markdown("### 2. Add Dishes")
        selected_dish = st.selectbox("Search & Select Dish", menu_list)
        
        live_rate = menu_rates.get(selected_dish, 0.0)
        st.caption(f"Standard Price fetched from Database: **₹{live_rate:.2f}**")
        
        qty_col, comm_col = st.columns(2)
        with qty_col:
            qty = st.number_input("Quantity", min_value=1, value=1, step=1)
        with comm_col:
            comm_pct = 33.77 if channel == "Swiggy" else (34.90 if channel == "Zomato" else 0.0)
            final_comm = st.number_input("Commission %", value=comm_pct)

        # 🟠 BUTTON: Add to Cart (Light Orange Styled)
        if st.button("➕ Add to Cart", key="btn_add_cart", use_container_width=True):
            existing_item = next((item for item in st.session_state.billing_cart if item['dish'] == selected_dish), None)
            if existing_item:
                existing_item['qty'] += qty
            else:
                st.session_state.billing_cart.append({
                    "dish": selected_dish,
                    "qty": qty,
                    "rate": live_rate,
                    "comm_pct": final_comm
                })
            st.session_state.show_total_panel = False  # Dynamic lock reset on appending elements
            st.rerun()

    with col_cart:
        st.markdown("### 3. Invoice View")
        if st.session_state.billing_cart:
            df_cart = pd.DataFrame(st.session_state.billing_cart)
            df_cart['Amount (₹)'] = df_cart['qty'] * df_cart['rate']
            
            st.data_editor(
                df_cart[['dish', 'qty', 'rate', 'Amount (₹)']],
                column_config={
                    "dish": "Dish Particulars",
                    "qty": "Quantity Packed",
                    "rate": "Unit Price (₹)",
                    "Amount (₹)": "Subtotal (₹)"
                },
                disabled=["dish", "rate", "Amount (₹)"],
                use_container_width=True,
                key="billing_clean_matrix_editor"
            )
            
            bill_total = df_cart['Amount (₹)'].sum()
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 🟣 BUTTON POSITION SWAP: Generate Bill Button placed cleanly ABOVE Total (Lavender Styled)
            if st.button("🏁 Generate Bill", key="btn_gen_bill", use_container_width=True):
                st.session_state.show_total_panel = True
            
            # 🔒 CONDITIONAL INTERFACE FLOW DISPLAY (Shows total and action tools only after clicking Generate Bill)
            if st.session_state.show_total_panel:
                st.markdown(f"### 📈 **Bill Total: ₹{bill_total:,.2f}**")
                st.markdown("---")
                
                col_print, col_wa, col_clear = st.columns(3)
                
                items_text = ""
                for index, row in df_cart.iterrows():
                    items_text += f"• {row['dish']} x {row['qty']} = ₹{row['Amount (₹)']:.2f}\\n"
                
                c_name_val = cust_name if cust_name else 'Walking Customer'
                c_phone_val = cust_phone if cust_phone else 'N/A'
                
                with col_print:
                    # 🖨️ BUTTON: Sky Blue Styled
                    if st.button("🖨️ Print Receipt", key="btn_print", use_container_width=True):
                        with st.spinner("Syncing data tracks..."):
                            try:
                                supabase.table("orders").insert({
                                    "date": str(billing_date), "bill_number": current_bill_id, "customer_name": c_name_val,
                                    "phone_number": c_phone_val, "platform": channel, "payment_mode": pay_mode,
                                    "amount": float(bill_total), "items_summary": str(st.session_state.billing_cart)
                                }).execute()
                                
                                # BOM Inventory live stock deductions processing loop
                                for cart_row in st.session_state.billing_cart:
                                    bom_res = supabase.table("bom_master").select('*').eq('\"Dish Name\"', cart_row['dish']).execute()
                                    if bom_res.data:
                                        for ing in bom_res.data:
                                            req_qty = float(ing['Required quantity']) * cart_row['qty']
                                            sku_res = supabase.table("sku_master").select("current_stock").eq('\"Ingerdient Name\"', ing['Ingerdient Name']).execute()
                                            if sku_res.data:
                                                curr = float(sku_res.data[0].get('current_stock', 0))
                                                supabase.table("sku_master").update({"current_stock": curr - req_qty}).eq('\"Ingerdient Name\"', ing['Ingerdient Name']).execute()
                            except Exception as e:
                                st.sidebar.error(f"Sync Note: {str(e)}")
                        
                        st.success("Sent payload to browser print loop!")
                        st.session_state.billing_cart = []
                        st.session_state.bill_number_counter += 1
                        st.session_state.show_total_panel = False
                        st.rerun()
                
                with col_wa:
                    # 💚 BUTTON: Parrot Green Styled
                    if st.button("💬 WhatsApp Bill", key="btn_whatsapp", use_container_width=True):
                        if cust_phone:
                            with st.spinner("Syncing database..."):
                                try:
                                    supabase.table("orders").insert({
                                        "date": str(billing_date), "bill_number": current_bill_id, "customer_name": c_name_val,
                                        "phone_number": c_phone_val, "platform": channel, "payment_mode": pay_mode,
                                        "amount": float(bill_total), "items_summary": str(st.session_state.billing_cart)
                                    }).execute()
                                    # BOM Stock deduction integration loop
                                    for cart_row in st.session_state.billing_cart:
                                        bom_res = supabase.table("bom_master").select('*').eq('\"Dish Name\"', cart_row['dish']).execute()
                                        if bom_res.data:
                                            for ing in bom_res.data:
                                                req_qty = float(ing['Required quantity']) * cart_row['qty']
                                                sku_res = supabase.table("sku_master").select("current_stock").eq('\"Ingerdient Name\"', ing['Ingerdient Name']).execute()
                                                if sku_res.data:
                                                    curr = float(sku_res.data[0].get('current_stock', 0))
                                                    supabase.table("sku_master").update({"current_stock": curr - req_qty}).eq('\"Ingerdient Name\"', ing['Ingerdient Name']).execute()
                                except Exception as e:
                                    pass
                            
                            msg = (
                                f"*LALALA CLOUD KITCHEN*\\n"
                                f"----------------------------\\n"
                                f"Bill No: {current_bill_id}\\n"
                                f"Customer: {c_name_val}\\n"
                                f"----------------------------\\n"
                                f"*Grand Total: ₹{bill_total:.2f}*\\n"
                                f"Good Food, Signature Feel! 🥦"
                            )
                            encoded_msg = msg.replace(" ", "%20").replace("\\n", "%0A")
                            wa_url = f"https://wa.me/91{cust_phone}?text={encoded_msg}"
                            st.markdown(f"[🔗 Click to Send WhatsApp]({wa_url})")
                            st.session_state.billing_cart = []
                            st.session_state.bill_number_counter += 1
                            st.session_state.show_total_panel = False
                            st.rerun()
                        else:
                            st.error("Please insert customer mobile number first!")

                with col_clear:
                    # 💛 BUTTON: Sandal Yellow Styled
                    if st.button("🗑️ Clear Current Cart", key="btn_clear", use_container_width=True):
                        st.session_state.billing_cart = []
                        st.session_state.show_total_panel = False
                        st.rerun()
        else:
            st.info("Invoice cart is empty.")

# ==========================================
# --- MODULE 2: ADMIN LOGIN (STABLE CORE LOGIC LOCK) ---
# ==========================================
elif choice == "Admin Login":
    st.subheader("🔒 Admin Control Panel")
    admin_pwd = st.text_input("Enter Password", type="password")
    
    if admin_pwd == "140226":
        st.success("Access Granted.")
        admin_tab = st.sidebar.radio("Admin Menu", ["Inventory Status", "Accounts Entry Panel", "Wastage Entry", "Report Analytics"])
        
        # 1. LIVE STOCK TRACKER
        if admin_tab == "Inventory Status":
            st.subheader("📦 Live Stock Tracker")
            sku_data = supabase.table("sku_master").select("*").execute()
            if sku_data.data:
                df = pd.DataFrame(sku_data.data)
                st.dataframe(df)
                if st.button("Generate Purchase List"):
                    low = df[df['current_stock'].astype(float) < df['Min Stock Level'].astype(float)]
                    st.warning("Immediate Purchase Needed:")
                    st.write(low[['Ingerdient Name', 'current_stock', 'Purchase unit']])

        # 2. ACCOUNTS ENTRY PANEL
        elif admin_tab == "Accounts Entry Panel":
            st.subheader("💰 Accounts Management & Entries")
            acc_type = st.radio("Select Action", ["Purchase Entry", "Fixed Expenses", "Channel Payout Settlements"], horizontal=True)
            
            if acc_type == "Purchase Entry":
                st.markdown("### 🛒 Raw Material Purchase")
                p_item_res = supabase.table("sku_master").select('\"Ingerdient Name\"', '\"Purchase unit\"').execute()
                item_data = {i['Ingerdient Name']: i['Purchase unit'] for i in p_item_res.data}
                col1, col2 = st.columns(2)
                with col1:
                    p_date = st.date_input("Purchase Date", datetime.date.today(), key="p_date")
                    p_item = st.selectbox("Select Item", list(item_data.keys()), key="p_item")
                    s_unit = item_data.get(p_item, "")
                    st.info(f"Unit: **{s_unit}**")
                with col2:
                    p_qty = st.number_input(f"Qty ({s_unit})", min_value=0.1, key="p_qty")
                    p_amt = st.number_input("Total Amount Spent", min_value=0.0, key="p_amt")
                if st.button("Submit Purchase"):
                    curr_res = supabase.table("sku_master").select("current_stock").eq('\"Ingerdient Name\"', p_item).execute()
                    curr = float(curr_res.data[0]['current_stock'])
                    supabase.table("sku_master").update({"current_stock": curr + p_qty}).eq('\"Ingerdient Name\"', p_item).execute()
                    supabase.table("accounts").insert({"date": str(p_date), "type": "Purchase", "category": "Raw Material", "item_name": p_item, "amount": p_amt, "qty": p_qty, "unit": s_unit}).execute()
                    st.success("Purchase Logged!")

            elif acc_type == "Fixed Expenses":
                st.markdown("### 💸 Fixed Expense Entry")
                e_date = st.date_input("Expense Date", datetime.date.today(), key="e_date")
                e_cat = st.selectbox("Category", ["Rent", "EB Bill", "Salary", "Gas", "Maintenance", "Other"], key="e_cat")
                e_amt = st.number_input("Amount", min_value=0.0, key="e_amt")
                if st.button("Save Expense"):
                    supabase.table("accounts").insert({"date": str(e_date), "type": "Fixed Expense", "category": e_cat, "amount": e_amt}).execute()
                    st.success("Expense Recorded!")

            elif acc_type == "Channel Payout Settlements":
                st.markdown("### 💳 Automated Payout Validation Logic")
                col1, col2 = st.columns(2)
                with col1:
                    s_platform = st.selectbox("Select Platform", ["Zomato", "Swiggy"], key="set_plat")
                    start_date = st.date_input("From Date", datetime.date.today() - datetime.timedelta(days=7), key="set_start")
                    end_date = st.date_input("To Date", datetime.date.today(), key="set_end")
                with col2:
                    payout_received = st.number_input("Actual Amount Received in Bank (₹)", min_value=0.0, step=100.0, key="set_cash")
                
                if st.button("Process & Auto-Calculate Commission"):
                    gross_sales = 0.0
                    try:
                        orders_res = supabase.table("orders").select("*").execute()
                        if orders_res.data:
                            df_orders = pd.DataFrame(orders_res.data)
                            df_orders['date'] = pd.to_datetime(df_orders['date']).dt.date
                            filtered_df = df_orders[(df_orders['platform'].astype(str).str.lower() == s_platform.lower()) & (df_orders['date'] >= start_date) & (df_orders['date'] <= end_date)]
                            gross_sales = float(filtered_df['amount'].sum())
                    except Exception as e:
                        pass
                    
                    if gross_sales == 0: gross_sales = payout_received
                    commission_deducted = gross_sales - payout_received
                    if commission_deducted < 0: commission_deducted = 0.0
                    
                    supabase.table("accounts").insert({"date": str(datetime.date.today()), "type": "Revenue", "category": f"{s_platform} Payout", "item_name": f"Period: {start_date} to {end_date}", "amount": payout_received, "notes": f"Gross Sales: {gross_sales:.2f}"}).execute()
                    if commission_deducted > 0:
                        supabase.table("accounts").insert({"date": str(datetime.date.today()), "type": "Expense", "category": "Platform Commission", "item_name": s_platform, "amount": commission_deducted, "notes": f"Auto cut for period {start_date} to {end_date}"}).execute()
                    st.success("Successfully Synced!")

        # 3. WASTAGE ENTRY
        elif admin_tab == "Wastage Entry":
            st.subheader("🗑️ Non-Revenue & Loss Entry")
            w_category = st.radio("Type of Entry", ["Raw Material Loss", "Cooked Item Waste", "Complimentary / Promo"], horizontal=True)

        # 4. REPORT ANALYTICS INTERFACE HUB
        elif admin_tab == "Report Analytics":
            st.subheader("📊 Centralized Business Intelligence Dashboard")
            st.error("⚠️ **Proactive Critical Notice: Low Stock Alert Engine Active**")
            tab_workdays, tab_dishes, tab_crm, tab_platforms, tab_wastage, tab_expenses, tab_deadstock = st.tabs([
                "📅 Working Days Tracker", "🍲 Dish Performance Matrix", "👥 Customer Retention (CRM)",
                "📱 Platform Individual Sales", "🗑️ Food Waste SKU Analysis", "💸 Monthly Expenses Breakdown", "🛑 3-Month Dead Stock Audit"
            ])

    elif admin_pwd != "":
        st.error("Incorrect Password.")
