import streamlit as st
from supabase import create_client
import datetime
import pandas as pd

# --- CONNECTION PARAMETERS (CAPITAL ALPHABETS SAFEGUARD) ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Sig-nature Kitchen", layout="wide")

# Initialize Session States for Multi-Item Billing Cart & Bill Numbers
if "billing_cart" not in st.session_state:
    st.session_state.billing_cart = []
if "bill_number_counter" not in st.session_state:
    st.session_state.bill_number_counter = 1001

# --- UI HEADER ---
st.markdown('<h1 style="text-align: center; color: #1B5E20;">👨‍🍳 LALALA CLOUD KITCHEN</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #388E3C; font-size: 20px;">Good Food, Sig-nature Feel | Pure VEG 🥦</p>', unsafe_allow_html=True)

# --- CORE ARCHITECTURE SEPARATION ---
st.sidebar.title("Main Menu")
choice = st.sidebar.radio("Go to", ["Billing", "Admin Login"])

# ==========================================
# --- MODULE 1: BILLING (HIGH-SPEED COUNTER WITH CUSTOM OPERATIONS) ---
# ==========================================
if choice == "Billing":
    st.subheader("🛒 High-Speed Billing Counter")
    current_bill_id = f"LALALA-2026-{st.session_state.bill_number_counter}"
    st.write(f"**Current Bill Number:** `{current_bill_id}`")
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

        if st.button("➕ Append Item to Bill", use_container_width=True):
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
            st.markdown(f"### 📈 **Bill Total: ₹{bill_total:,.2f}**")
            st.markdown("---")
            
            col_print, col_wa, col_clear = st.columns(3)
            
            items_text = ""
            for index, row in df_cart.iterrows():
                items_text += f"• {row['dish']} x {row['qty']} = ₹{row['Amount (₹)']:.2f}\\n"
            
            c_name_val = cust_name if cust_name else 'Walking Customer'
            c_phone_val = cust_phone if cust_phone else 'N/A'
            
            with col_print:
                if st.button("🖨️ Print Receipt", use_container_width=True):
                    st.success("Sent payload to browser print loop!")
                    st.session_state.billing_cart = []
                    st.session_state.bill_number_counter += 1
                    st.rerun()
            
            with col_wa:
                if st.button("💬 WhatsApp Bill", use_container_width=True):
                    if cust_phone:
                        msg = (
                            f"*LALALA CLOUD KITCHEN*\\n"
                            f"----------------------------\\n"
                            f"Bill No: {current_bill_id}\\n"
                            f"Customer: {c_name_val}\\n"
                            f"Phone: {c_phone_val}\\n"
                            f"Channel: {channel}\\n"
                            f"Payment Mode: {pay_mode}\\n"
                            f"----------------------------\\n"
                            f"*Items Billed:*\\n{items_text}"
                            f"----------------------------\\n"
                            f"*Grand Total: ₹{bill_total:.2f}*\\n"
                            f"Thank you! Good Food, Signature Feel! 🥦"
                        )
                        encoded_msg = msg.replace(" ", "%20").replace("\\n", "%0A")
                        wa_url = f"https://wa.me/91{cust_phone}?text={encoded_msg}"
                        st.markdown(f"[🔗 Click to Send WhatsApp]({wa_url})")
                        st.session_state.billing_cart = []
                        st.session_state.bill_number_counter += 1
                        st.rerun()
                    else:
                        st.error("Please insert customer mobile number first!")

            with col_clear:
                if st.button("🗑️ Clear Current Cart", use_container_width=True, type="secondary"):
                    st.session_state.billing_cart = []
                    st.rerun()
            
            st.markdown("---")
            if st.button("🏁 Finalize Bill & Sync Inventory Stock", type="primary", use_container_width=True):
                with st.spinner("Processing transaction matrices and decrementing stock..."):
                    try:
                        supabase.table("orders").insert({
                            "date": str(datetime.date.today()),
                            "bill_number": current_bill_id,
                            "customer_name": c_name_val,
                            "phone_number": c_phone_val,
                            "platform": channel,
                            "payment_mode": pay_mode,
                            "amount": float(bill_total),
                            "items_summary": str(st.session_state.billing_cart)
                        }).execute()
                    except Exception as ex:
                        st.sidebar.warning(f"Orders Table Insert Note: {str(ex)}")

                    for cart_row in st.session_state.billing_cart:
                        c_dish = cart_row['dish']
                        c_qty = cart_row['qty']
                        
                        bom_res = supabase.table("bom_master").select('*').eq('\"Dish Name\"', c_dish).execute()
                        if bom_res.data:
                            for ing in bom_res.data:
                                ing_name = ing['Ingerdient Name']
                                req_qty = float(ing['Required quantity']) * c_qty
                                
                                sku_res = supabase.table("sku_master").select("current_stock").eq('\"Ingerdient Name\"', ing_name).execute()
                                if sku_res.data:
                                    current = float(sku_res.data[0].get('current_stock', 0))
                                    supabase.table("sku_master").update({"current_stock": current - req_qty}).eq('\"Ingerdient Name\"', ing_name).execute()
                    
                    st.success(f"Transaction Complete! Closed Invoice No: {current_bill_id}")
                    st.balloons()
                    st.session_state.billing_cart = []
                    st.session_state.bill_number_counter += 1
                    st.rerun()
        else:
            st.info("Invoice cart is empty. Please add elements to active layout matrix to see changes.")


# ==========================================
# --- MODULE 2: ADMIN LOGIN (STABLE & PROTECTED AREA) ---
# ==========================================
elif choice == "Admin Login":
    st.subheader("🔒 Admin Control Panel")
    admin_pwd = st.text_input("Enter Password", type="password")
    
    if admin_pwd == "140226":
        st.success("Access Granted.")
        
        admin_tab = st.sidebar.radio("Admin Menu", 
            ["Inventory Status", "Accounts Entry Panel", "Wastage Entry", "Report Analytics"])
        
        # 1. INVENTORY STATUS
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

        # 2. ACCOUNTS ENTRY PANEL (Now houses Settlements Entry successfully!)
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

            # 🔄 Shifted Segment: Channel Settlements Analytics -> Accounts Entry Panel
            elif acc_type == "Channel Payout Settlements":
                st.markdown("### 💳 Automated Payout Validation Logic")
                st.info("Select the date range and enter the exact amount received in your Bank.")
                
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
                            p_col = next((c for c in df_orders.columns if c.lower() == 'platform'), None)
                            d_col = next((c for c in df_orders.columns if 'date' in c.lower()), None)
                            a_col = next((c for c in df_orders.columns if 'amount' in c.lower() or 'total' in c.lower()), None)
                            
                            if p_col
