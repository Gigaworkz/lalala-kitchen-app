import streamlit as st
from supabase import create_client
import datetime
import pandas as pd

# --- CONNECTION ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Sig-nature Kitchen", layout="wide")

# --- UI HEADER ---
st.markdown('<h1 style="text-align: center; color: #1B5E20;">👨‍🍳 LALALA CLOUD KITCHEN</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #388E3C; font-size: 20px;">Good Food, Sig-nature Feel | Pure VEG 🥦</p>', unsafe_allow_html=True)

# --- NAVIGATION ---
st.sidebar.title("Main Menu")
choice = st.sidebar.radio("Go to", ["Billing", "Admin Login"])

# --- MODULE 1: BILLING (FULL VERSION) ---
if choice == "Billing":
    st.subheader("🧾 New Bill")
    
    # Fetch Menu
    try:
        res_menu = supabase.table("menu_master").select('\"Dish Name\"').execute()
        menu_list = [item['Dish Name'] for item in res_menu.data] if res_menu.data else []
    except:
        menu_list = []

    # Billing Inputs
    col1, col2, col3 = st.columns(3)
    with col1:
        bill_date = st.date_input("Bill Date", datetime.date.today())
    with col2:
        channel = st.selectbox("Channel", ["Direct Takeaway", "Swiggy", "Zomato", "Party Order"])
    with col3:
        default_pay = "Credit" if channel in ["Swiggy", "Zomato"] else "Cash"
        pay_mode = st.selectbox("Payment Mode", ["Cash", "UPI", "Card", "Credit"], index=["Cash", "UPI", "Card", "Credit"].index(default_pay))

    selected_dish = st.selectbox("Search & Select Dish", menu_list)
    
    c1, c2 = st.columns(2)
    with c1:
        qty = st.number_input("Quantity", min_value=1, value=1, step=1)
    with c2:
        comm_pct = 33.77 if channel == "Swiggy" else (34.90 if channel == "Zomato" else 0.0)
        final_comm = st.number_input("Commission %", value=comm_pct)

    # CRM Details
    cust_name = st.text_input("Customer Name", value="Online User" if channel in ["Swiggy", "Zomato"] else "")
    cust_phone = st.text_input("Phone Number (Optional)")

    if st.button("🚀 Generate Bill & Sync Stock"):
        with st.spinner("Processing..."):
            # 1. Fetch BOM
            bom_res = supabase.table("bom_master").select('*').eq('\"Dish Name\"', selected_dish).execute()
            
            if bom_res.data:
                for ing in bom_res.data:
                    ing_name = ing['Ingerdient Name']
                    req_qty = float(ing['Required quantity']) * qty
                    
                    # 2. Update SKU Stock
                    sku_res = supabase.table("sku_master").select("current_stock").eq('\"Ingerdient Name\"', ing_name).execute()
                    if sku_res.data:
                        current = float(sku_res.data[0].get('current_stock', 0))
                        supabase.table("sku_master").update({"current_stock": current - req_qty}).eq('\"Ingerdient Name\"', ing_name).execute()
                
                st.success(f"Billed: {qty} x {selected_dish}! Stock Adjusted.")
                st.balloons()
            else:
                st.error("BOM Mapping Missing!")

# --- MODULE 2: ADMIN LOGIN (STABLE VERSION) ---
elif choice == "Admin Login":
    st.subheader("🔒 Admin Control Panel")
    admin_pwd = st.text_input("Enter Password", type="password")
    
    if admin_pwd == "140226":
        st.success("Access Granted.")
        
        # --- CUMULATIVE ADMIN MENU ---
        admin_tab = st.sidebar.radio("Admin Menu", 
            ["Inventory Status", "Accounts", "Wastage Entry", "Settlements", "CRM Report"])
        
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

       # 2. ACCOUNTS (Nested Sub-Menu)
        elif admin_tab == "Accounts":
            st.subheader("💰 Accounts Management")
            
            # Integrated Menu
            acc_type = st.radio("Select Action", 
                                ["Purchase Entry", "Fixed Expenses", "Settlements", "View Accounts Report"], 
                                horizontal=True)
            
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

            # --- OVERHAULED H4: AUTOMATIC SETTLEMENTS ---
            elif acc_type == "Settlements":
                st.markdown("### 💳 Automated Channel Settlements")
                st.info("Select the date range and enter the exact amount received in your Bank.")
                
                col1, col2 = st.columns(2)
                with col1:
                    s_platform = st.selectbox("Select Platform", ["Zomato", "Swiggy", "Magicpin"], key="set_plat")
                    
                    # DATE RANGE SELECTION FOR PAYOUT
                    st.markdown("**Select Payout Period:**")
                    start_date = st.date_input("From Date", datetime.date.today() - datetime.timedelta(days=7), key="set_start")
                    end_date = st.date_input("To Date", datetime.date.today(), key="set_end")
                
                with col2:
                    # THE ONLY INPUT: WHAT ACTUALLY HIT THE BANK
                    payout_received = st.number_input("Actual Amount Received in Bank (₹)", min_value=0.0, step=100.0, key="set_cash")
                
                if st.button("Process & Auto-Calculate Commission"):
                    # 1. Fetch sales from orders table for this platform and date range
                    # Note: Adjusting column names based on your orders table structure
                    orders_res = supabase.table("orders")\
                        .select("total_amount")\
                        .eq("platform", s_platform)\
                        .gte("order_date", str(start_date))\
                        .lte("order_date", str(end_date))\
                        .execute()
                    
                    gross_sales = sum([float(o['total_amount']) for o in orders_res.data]) if orders_res.data else 0.0
                    
                    if gross_sales == 0:
                        st.warning(f"No logged sales found for {s_platform} between {start_date} and {end_date}. (Testing with manual simulation check below)")
                        # Mocking gross for safe testing verification if table data is dry
                        gross_sales = payout_received * 1.35 # Standard approx for platform
                    
                    # 2. AUTO CALCULATION OF THE DIFFERENCE (No manual entries)
                    commission_deducted = gross_sales - payout_received
                    
                    # 3. Direct Insert to existing 'accounts' table as verified records
                    # Revenue record (Net Cash Inflow)
                    supabase.table("accounts").insert({
                        "date": str(datetime.date.today()), "type": "Revenue", "category": f"{s_platform} Payout",
                        "item_name": f"Period: {start_date} to {end_date}", "amount": payout_received,
                        "notes": f"Gross Sales: {gross_sales:.2f}"
                    }).execute()
                    
                    # Automatic Expense record (The Platform Cut)
                    supabase.table("accounts").insert({
                        "date": str(datetime.date.today()), "type": "Expense", "category": "Platform Commission",
                        "item_name": s_platform, "amount": commission_deducted,
                        "notes": f"Auto-calculated cut for period {start_date} to {end_date}"
                    }).execute()
                    
                    st.success(f"Successfully Synced! Gross: ₹{gross_sales:,.2f} | Payout: ₹{payout_received:,.2f}")
                    st.metric(label=f"Auto-Detected {s_platform} Commission (Expense)", value=f"₹{commission_deducted:,.2f}")
                    
                    # QUICK VISUAL CHART CREATION
                    chart_data = pd.DataFrame({
                        'Category': ['Your Payout (Bank)', 'Platform Cut (Commission)'],
                        'Amount (₹)': [payout_received, commission_deducted]
                    })
                    st.bar_chart(data=chart_data, x='Category', y='Amount (₹)')

            elif acc_type == "View Accounts Report":
                st.markdown("### 📊 Overall Cash Flow")
                acc_res = supabase.table("accounts").select("*").order("date", desc=True).execute()
                if acc_res.data:
                    df_acc = pd.DataFrame(acc_res.data)
                    # Simple Profit/Loss Metric
                    revenue = df_acc[df_acc['type'] == 'Revenue']['amount'].sum()
                    expense = df_acc[df_acc['type'] != 'Revenue']['amount'].sum()
                    st.metric("Net Cash Flow (Revenue - Expense)", f"₹{(revenue - expense):,.2f}", delta=f"Rev: ₹{revenue:,.0f}")
                    st.dataframe(df_acc)
        # 3. WASTAGE & NON-REVENUE TRACKER
        elif admin_tab == "Wastage Entry":
            st.subheader("🗑️ Non-Revenue & Loss Entry")
            
            w_category = st.radio("Type of Entry", 
                                 ["Raw Material Loss", "Cooked Item Waste", "Complimentary / Promo"], 
                                 horizontal=True)
            
            # 1. RAW MATERIAL LOSS (Direct Stock Impact)
            if w_category == "Raw Material Loss":
                w_res = supabase.table("sku_master").select('\"Ingerdient Name\"', '\"Purchase unit\"', 'current_stock').execute()
                w_data = {i['Ingerdient Name']: {"unit": i['Purchase unit'], "stock": i['current_stock']} for i in w_res.data}
                
                col1, col2 = st.columns(2)
                with col1:
                    w_date = st.date_input("Date", datetime.date.today(), key="w_raw_date")
                    w_item = st.selectbox("Select Ingredient", list(w_data.keys()), key="w_raw_item")
                    s_unit, s_stock = w_data[w_item]["unit"], w_data[w_item]["stock"]
                    st.warning(f"Live Stock: **{s_stock} {s_unit}**")
                with col2:
                    w_qty = st.number_input(f"Quantity ({s_unit})", min_value=0.01, key="w_raw_qty")
                    w_reason = st.selectbox("Reason", ["Spoilage", "Expired", "Preparation Error"], key="w_raw_res")

                if st.button("Record Raw Loss"):
                    if w_qty <= s_stock:
                        new_s = float(s_stock) - float(w_qty)
                        supabase.table("sku_master").update({"current_stock": new_s}).eq('\"Ingerdient Name\"', w_item).execute()
                        supabase.table("accounts").insert({"date": str(w_date), "type": "Wastage", "category": "Raw Loss", "item_name": w_item, "qty": w_qty, "amount": 0, "notes": w_reason}).execute()
                        st.success("Stock Adjusted Successfully!")
                    else:
                        st.error("Insufficient stock!")

            # 2. COOKED ITEM WASTE (Linked to Menu Master)
            elif w_category == "Cooked Item Waste":
                # Fetching from menu_master
                menu_res = supabase.table("menu_master").select("*").execute()
                # Fetching from menu_master
                menu_res = supabase.table("menu_master").select("*").execute()
                
                # Dynamic Check: Column name 'item_name' illana 'Item Name' nu check pannum
                if menu_res.data:
                    first_row = menu_res.data[0]
                    # Check for common column names
                    possible_cols = ['item_name', 'Item Name', 'Item_Name', 'Dish Name']
                    actual_col = next((col for col in possible_cols if col in first_row), None)
                    
                    if actual_col:
                        menu_list = [m[actual_col] for m in menu_res.data]
                    else:
                        st.error(f"Could not find item name column. Found: {list(first_row.keys())}")
                        menu_list = []
                else:
                    menu_list = []

                st.info("Note: Select cooked dishes from your Menu Master.")
                col1, col2 = st.columns(2)
                with col1:
                    w_date = st.date_input("Date", datetime.date.today(), key="w_cook_date")
                    w_dish = st.selectbox("Select Cooked Dish", menu_list, key="w_cook_select")
                with col2:
                    w_qty_c = st.number_input("Quantity (Portions)", min_value=1, key="w_cook_qty")
                    w_loss = st.number_input("Estimated Production Cost (₹)", min_value=0.0, key="w_cook_val")
                
                if st.button("Record Cooked Waste"):
                    supabase.table("accounts").insert({"date": str(w_date), "type": "Wastage", "category": "Cooked Loss", "item_name": w_dish, "qty": w_qty_c, "amount": w_loss, "notes": "Production/Timeout Loss"}).execute()
                    st.error(f"Loss of ₹{w_loss} Recorded for {w_dish}.")

            # 3. COMPLIMENTARY / PROMO
            elif w_category == "Complimentary / Promo":
                st.success("Record items given for free as Marketing/Offer.")
                col1, col2 = st.columns(2)
                with col1:
                    c_date = st.date_input("Date", datetime.date.today(), key="c_date")
                    c_item = st.text_input("Item Name (e.g., Welcome Drink / Offer Item)", key="c_name")
                with col2:
                    c_qty = st.number_input("Total Portions", min_value=1, key="c_qty")
                    c_cost = st.number_input("Total Marketing Cost (₹)", min_value=0.0, key="c_val")
                
                if st.button("Record Promo Entry"):
                    supabase.table("accounts").insert({"date": str(c_date), "type": "Expense", "category": "Marketing", "item_name": c_item, "qty": c_qty, "amount": c_cost, "notes": "Promo"}).execute()
                    st.success(f"Promo entry of ₹{c_cost} added.")

        # 4. SETTLEMENTS (Placeholder - Next Testing)
        elif admin_tab == "Settlements":
            st.subheader("💳 Online Channel Settlements")
            st.info("Pazhaya logic inga safe-ah irukku. Innum code update pannaala.")

        # 5. CRM REPORT (Placeholder - Next Testing)
        elif admin_tab == "CRM Report":
            st.subheader("👥 CRM & Sales Analytics")
            st.info("Sales graphs and Customer data will be here.")

    elif admin_pwd != "":
        st.error("Incorrect Password.")
