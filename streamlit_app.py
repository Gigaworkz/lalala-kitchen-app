import streamlit as st
from supabase import create_client
import datetime
import pandas as pd

# --- CONNECTION PARAMETERS (CAPITAL ALPHABETS SAFEGUARD) ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Sig-nature Kitchen", layout="wide")

# --- TASK 1: DYNAMIC DB COUNTER INITIALIZATION ENGINE ---
if "bill_number_counter" not in st.session_state:
    try:
        # DB orders table-la irundhu absolute last counter trace query fetch panrom
        res_counter = supabase.table("orders").select("bill_number").execute()
        if res_counter.data:
            # LALALA-2026-XXXX format-la irundhu numeric tail parameter extraction strings parsing
            ext_numbers = []
            for row in res_counter.data:
                b_num = row.get("bill_number", "")
                if b_num and "-" in b_num:
                    try:
                        parts = b_num.split("-")
                        num_part = int(parts[-1]) # Extracting last numeric sequence
                        ext_numbers.append(num_part)
                    except:
                        pass
            if ext_numbers:
                st.session_state.bill_number_counter = max(ext_numbers) + 1
            else:
                st.session_state.bill_number_counter = 1 # Start at index 1 standard integer integer boundaries matrix
        else:
            st.session_state.bill_number_counter = 1
    except Exception as ec:
        st.sidebar.warning(f"Counter Sync Delay Note: {str(ec)}")
        st.session_state.bill_number_counter = 1

if "billing_cart" not in st.session_state:
    st.session_state.billing_cart = []
# --- UI HEADER ---
st.markdown('<h1 style="text-align: center; color: #1B5E20;">👨‍🍳 LALALA CLOUD KITCHEN 👨‍🍳</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #388E3C; font-size: 20px;">🍟🍔🥟Good Food 🌯🥙🥪| 🌾Sig-Nature Feel 🧀| 🟩 Pure VEG 🌱</p>', unsafe_allow_html=True)

# --- CORE ARCHITECTURE SEPARATION ---
st.sidebar.title("Main Menu")
choice = st.sidebar.radio("Go to", ["Billing", "Admin Login"])

# ==========================================
# --- MODULE 1: BILLING (PERSISTENT SHARE & PRINT LOGIC) ---
# ==========================================
if choice == "Billing":
    st.subheader("🛒 Billing Counter")
    
    # Initialize Persistent Storage for Success State
    if 'last_bill_data' not in st.session_state:
        st.session_state.last_bill_data = None

    # {:03d} logic automatically formats numerical integer values like 1 into string '001', 2 into '002', 12 into '012', 105 into '105' parameters cleanly
    current_bill_id = f"LALALA-2026-{st.session_state.bill_number_counter:03d}"
    st.write(f"**Current Bill Number:** `{current_bill_id}`")
    st.markdown("---")
    
    # Menu Fetching (Standard Stable Loop)
    try:
        res_menu = supabase.table("menu_master").select("*").execute()
        menu_list = [item.get('Dish Name') for item in res_menu.data if item.get('Dish Name')] if res_menu.data else []
        menu_rates = {item.get('Dish Name'): float(item.get('Rate', 0) or item.get('Price', 0)) for item in res_menu.data} if res_menu.data else {}
    except:
        menu_list, menu_rates = [], {}

    col_input, col_cart = st.columns([2, 3])

    with col_input:
        st.markdown("### 1. Customer Details")
        cust_name = st.text_input("Customer Name", placeholder="Walking Customer")
        cust_phone = st.text_input("Phone Number", placeholder="10-digit number")
        bill_date = st.date_input("Bill Date", datetime.date.today())
        channel = st.selectbox("Channel", ["Direct Takeaway", "Swiggy", "Zomato", "Party Order"])
        pay_mode = st.selectbox("Payment Mode", ["Cash", "UPI", "Card", "Credit"])

        st.markdown("---")
        st.markdown("### 2. Add Dishes")
        selected_dish = st.selectbox("Search Dish", menu_list)
        qty = st.number_input("Quantity", min_value=1, value=1)

        if st.button("➕ Add to Cart", use_container_width=True):
            st.session_state.billing_cart.append({
                "dish": selected_dish, "qty": qty, 
                "rate": menu_rates.get(selected_dish, 0.0),
                "amount": qty * menu_rates.get(selected_dish, 0.0)
            })
            st.session_state.last_bill_data = None # Clear old bill display when adding new items
            st.rerun()

    with col_cart:
        st.markdown("### 3. Invoice View")
        if st.session_state.billing_cart:
            df_cart = pd.DataFrame(st.session_state.billing_cart)
            st.dataframe(df_cart, use_container_width=True)
            bill_total = df_cart['amount'].sum()
            
            if st.button("🏁 Generate Bill", type="primary", use_container_width=True):
                # 1. Store data for sharing before clearing cart
                items_text = ""
                for i, r in df_cart.iterrows():
                    items_text += f"• {r['dish']} x {r['qty']} = ₹{r['amount']:.2f}\\n"
                
                st.session_state.last_bill_data = {
                    "id": current_bill_id,
                    "total": bill_total,
                    "phone": cust_phone,
                    "name": cust_name or "Walking Customer",
                    "items": items_text,
                    "raw_items": st.session_state.billing_cart.copy()
                }

                # 2. Database Orders Table Insertion
                try:
                    supabase.table("orders").insert({
                        "date": str(bill_date), "bill_number": current_bill_id,
                        "customer_name": st.session_state.last_bill_data['name'],
                        "phone_number": cust_phone, "platform": channel,
                        "payment_mode": pay_mode, "amount": float(bill_total),
                        "items_summary": str(st.session_state.billing_cart)
                    }).execute()
                    
                    st.success(f"✅ Bill {current_bill_id} Saved to Database!")
                    
                    # === 🚀 NEW CRITICAL LOGIC: SALES INTERMEDIATE BOM DECOUPLING ENGINE ===
                    for cart_item in st.session_state.billing_cart:
                        dish_name_token = cart_item.get('dish')
                        ordered_qty = float(cart_item.get('qty', 1))
                        
                        # Fetch recipe items matching selected cooked dish from BOM master
                        bom_query = supabase.table("bom_master").select("*").eq("dish_name", dish_name_token).execute()
                        
                        if bom_query.data:
                            for recipe_row in bom_query.data:
                                ingredient_name = recipe_row.get("item_name")
                                recipe_unit_qty = float(recipe_row.get("qty", 0)) # Qty needed for 1 portion
                                
                                # Total weight deduction calculation rule
                                total_deduction = recipe_unit_qty * ordered_qty
                                
                                # Fetch current stock configuration parameters safely
                                sku_lookup = supabase.table("sku_master").select("current_stock").eq('\"Ingerdient Name\"', ingredient_name).execute()
                                if sku_lookup.data:
                                    current_live_stock = float(sku_lookup.data[0]['current_stock'])
                                    new_calculated_stock = current_live_stock - total_deduction
                                    
                                    # Update live warehouse index counters
                                    supabase.table("sku_master").update({"current_stock": new_calculated_stock}).eq('\"Ingerdient Name\"', ingredient_name).execute()
                    
                    st.caption("✨ Dynamic Inventory Calibration: Component metrics successfully adjusted based on recipe matrix specifications.")
                    st.session_state.billing_cart = [] # Now safe to clear cart
                    st.session_state.bill_number_counter += 1
                except Exception as e:
                    st.error(f"DB Error: {str(e)}")

        # --- PERSISTENT SHARE SECTION ---
        # This section stays visible even after cart is cleared
        if st.session_state.last_bill_data:
            lb = st.session_state.last_bill_data
            st.markdown("---")
            st.info(f"✨ **Active Invoice Ready: {lb['id']}** | Total: ₹{lb['total']:.2f}")
            
            sh_col1, sh_col2 = st.columns(2)
            
            with sh_col1:
                # 🖨️ PDF / Print Hook
                if st.button("🖨️ Print / Save PDF", use_container_width=True):
                    html_items = "".join([f"<tr><td>{item['dish']} x {item['qty']}</td><td>₹{item['amount']:.2f}</td></tr>" for item in lb['raw_items']])
                    print_html = f"""
                    <div style="font-family:monospace; width:280px; padding:10px;">
                        <h3 style="text-align:center;">LALALA CLOUD KITCHEN</h3>
                        <p>ID: {lb['id']}<br>Date: {datetime.date.today()}</p>
                        <hr><table>{html_items}</table><hr>
                        <h4>Total: ₹{lb['total']:.2f}</h4>
                    </div>
                    <script>window.print();</script>
                    """
                    st.components.v1.html(print_html, height=0, width=0)

            with sh_col2:
                # 💬 WhatsApp Hook
                if lb['phone']:
                    wa_msg = f"*LALALA KITCHEN*\\nBill: {lb['id']}\\nTotal: ₹{lb['total']:.2f}\\nItems:\\n{lb['items']}"
                    wa_url = f"https://wa.me/91{lb['phone']}?text={wa_msg.replace(' ', '%20').replace('\\n', '%0A')}"
                    st.link_button("💬 Share WhatsApp", wa_url, use_container_width=True)
                else:
                    st.warning("No phone number for WhatsApp")

            if st.button("🆕 Start New Bill", use_container_width=True, type="secondary"):
                st.session_state.last_bill_data = None
                st.rerun()

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
                            
                            if p_col and d_col and a_col:
                                df_orders[d_col] = pd.to_datetime(df_orders[d_col]).dt.date
                                filtered_df = df_orders[
                                    (df_orders[p_col].astype(str).str.lower() == s_platform.lower()) & 
                                    (df_orders[d_col] >= start_date) & 
                                    (df_orders[d_col] <= end_date)
                                ]
                                gross_sales = float(filtered_df[a_col].sum())
                    except Exception as e:
                        st.error(f"Sync Note: {str(e)}")
                    
                    if gross_sales == 0:
                        st.warning(f"No transactions found for {s_platform}. Using Payout as base index value.")
                        gross_sales = payout_received
                    
                    commission_deducted = gross_sales - payout_received
                    if commission_deducted < 0: commission_deducted = 0.0
                    
                    supabase.table("accounts").insert({
                        "date": str(datetime.date.today()), "type": "Revenue", "category": f"{s_platform} Payout",
                        "item_name": f"Period: {start_date} to {end_date}", "amount": payout_received,
                        "notes": f"Gross Sales: {gross_sales:.2f}"
                    }).execute()
                    
                    if commission_deducted > 0:
                        supabase.table("accounts").insert({
                            "date": str(datetime.date.today()), "type": "Expense", "category": "Platform Commission",
                            "item_name": s_platform, "amount": commission_deducted,
                            "notes": f"Auto cut for period {start_date} to {end_date}"
                        }).execute()
                    
                    st.success(f"Successfully Synced! Gross: ₹{gross_sales:,.2f} | Payout: ₹{payout_received:,.2f}")
                    st.metric(label=f"{s_platform} Commission Deducted", value=f"₹{commission_deducted:,.2f}")
                    
                    chart_data = pd.DataFrame({
                        'Category': ['Bank Payout', 'Platform Cut (Commission)'],
                        'Amount (₹)': [payout_received, commission_deducted]
                    })
                    st.bar_chart(data=chart_data, x='Category', y='Amount (₹)')

        # 3. WASTAGE & NON-REVENUE TRACKER
        elif admin_tab == "Wastage Entry":
            st.subheader("🗑️ Non-Revenue & Loss Entry")
            w_category = st.radio("Type of Entry", ["Raw Material Loss", "Cooked Item Waste", "Complimentary / Promo"], horizontal=True)
            
            try:
                m_res = supabase.table("menu_master").select("*").execute()
                possible_cols = ['item_name', 'Item Name', 'Item_Name', 'Dish Name']
                first_row = m_res.data[0] if m_res.data else {}
                actual_col = next((col for col in possible_cols if col in first_row), None)
                system_dish_list = [m[actual_col] for m in m_res.data] if actual_col else []
            except:
                system_dish_list = []

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

            elif w_category == "Cooked Item Waste":
                st.info("Note: Select cooked dishes from your Menu Master.")
                col1, col2 = st.columns(2)
                with col1:
                    w_date = st.date_input("Date", datetime.date.today(), key="w_cook_date")
                    w_dish = st.selectbox("Select Cooked Dish", system_dish_list, key="w_cook_select")
                with col2:
                    w_qty_c = st.number_input("Quantity (Portions)", min_value=1, key="w_cook_qty")
                    w_loss = st.number_input("Estimated Production Cost (₹)", min_value=0.0, key="w_cook_val")
                
                if st.button("Record Cooked Waste"):
                    supabase.table("accounts").insert({"date": str(w_date), "type": "Wastage", "category": "Cooked Loss", "item_name": w_dish, "qty": w_qty_c, "amount": w_loss, "notes": "Production/Timeout Loss"}).execute()
                    st.error(f"Loss of ₹{w_loss} Recorded for {w_dish}.")

            elif w_category == "Complimentary / Promo":
                st.success("Record items given for free as Marketing/Offer.")
                col1, col2 = st.columns(2)
                with col1:
                    c_date = st.date_input("Date", datetime.date.today(), key="c_date")
                    c_item = st.selectbox("Select Dish (From Menu Master)", system_dish_list, key="c_name_select")
                with col2:
                    c_qty = st.number_input("Total Portions", min_value=1, key="c_qty")
                    c_cost = st.number_input("Total Marketing Cost (₹)", min_value=0.0, key="c_val")
                
                if st.button("Record Promo Entry"):
                    supabase.table("accounts").insert({"date": str(c_date), "type": "Expense", "category": "Marketing", "item_name": c_item, "qty": c_qty, "amount": c_cost, "notes": "Promo Offer Allocation"}).execute()
                    st.success(f"Promo entry of ₹{c_cost} added safely for {c_item}.")

        # 4. REPORT ANALYTICS & PAST BILL SEARCH ENGINE (TASK 3 MERGED)
        elif admin_tab == "Report Analytics":
            st.subheader("📊 Centralized Business Intelligence Dashboard")
            
            # --- TASK 3: PAST BILL LOOKUP INTERFACE HOOK ---
            st.markdown("### 🔍 Central Invoice Retrieval Engine")
            st.info("Type complete text token identifiers (e.g., LALALA-2026-1001) or customer parameters to scan repository logs.")
            
            search_col1, search_col2 = st.columns([3, 1])
            with search_col1:
                search_query = st.text_input("Enter Bill Number or Phone Number Token Key", placeholder="LALALA-2026-", key="central_search_input")
            with search_col2:
                st.write("##") # Layout alignment padding
                search_trigger = st.button("📡 Execute Database Scan", use_container_width=True, type="primary", key="central_search_btn")
                
            if search_trigger and search_query:
                with st.spinner("Executing relational filter scans across cloud server databases..."):
                    try:
                        if search_query.strip().startswith("LALALA"):
                            fetch_res = supabase.table("orders").select("*").eq("bill_number", search_query.strip()).execute()
                        else:
                            fetch_res = supabase.table("orders").select("*").eq("phone_number", search_query.strip()).execute()
                            
                        if fetch_res.data:
                            for matched_bill in fetch_res.data:
                                st.markdown("---")
                                st.success(f"Record Matching Verified! Target Invoice Document: **{matched_bill['bill_number']}**")
                                
                                v_col1, v_col2 = st.columns(2)
                                with v_col1:
                                    st.write(f"📅 **Transaction Date:** {matched_bill.get('date', 'N/A')}")
                                    st.write(f"👤 **Customer Particulars:** {matched_bill.get('customer_name', 'Walking Customer')}")
                                    st.write(f"📱 **Contact Registry:** {matched_bill.get('phone_number', 'N/A')}")
                                with v_col2:
                                    st.write(f"🌐 **Channel Tag:** {matched_bill.get('platform', 'Counter')}")
                                    st.write(f"💳 **Settlement Mode:** {matched_bill.get('payment_mode', 'Cash')}")
                                    st.write(f"💰 **Gross Amount Total:** ₹{float(matched_bill.get('amount', 0)):,.2f}")
                                    
                                st.markdown("**Billed Element Details Checklist:**")
                                st.code(matched_bill.get('items_summary', '[]'), language='json')
                                st.button(f"🖨️ Re-Send Document to Printer ({matched_bill['bill_number']})", key=f"reprint_{matched_bill['bill_number']}")
                        else:
                            st.warning("Query Trace Completed. Absolute zero records discovered matching specifications inside Supabase.")
                    except Exception as e_fetch:
                        st.error(f"Search Execution Fault: {str(e_fetch)}")

            st.markdown("---")
            
            # --- GLOBAL DYNAMIC DATE RANGE FILTER WIDGETS ---
            st.markdown("### 📅 Select Reporting Timeframe Window")
            col_f_date, col_t_date = st.columns(2)
            
            with col_f_date:
                default_from = datetime.date.today().replace(day=1) # Default to 1st of current month
                from_date = st.date_input("From Date Boundary", default_from, key="report_from_date_widget")
            
            with col_t_date:
                to_date = st.date_input("To Date Boundary", datetime.date.today(), key="report_to_date_widget")
                
            st.caption(f"💡 Visualizing system metrics and database records execution lines from **{from_date}** to **{to_date}**.")
            st.markdown("---")

            # --- FETCH REAL-TIME DATA BASED ON DATE FILTERS ---
            orders_data = []
            accounts_data = []
            
            try:
                res_orders = supabase.table("orders").select("*").gte("date", str(from_date)).lte("date", str(to_date)).execute()
                orders_data = res_orders.data if res_orders.data else []
            except Exception as ex:
                st.warning(f"Orders Query Execution Boundary Note: {str(ex)}")
                
            try:
                res_accounts = supabase.table("accounts").select("*").gte("date", str(from_date)).lte("date", str(to_date)).execute()
                accounts_data = res_accounts.data if res_accounts.data else []
            except Exception as ex:
                st.warning(f"Accounts Query Execution Boundary Note: {str(ex)}")

            df_orders = pd.DataFrame(orders_data)
            df_accounts = pd.DataFrame(accounts_data)

            # --- LOW STOCK SAFETY ENGINE ALERT LAYER ---
            try:
                sku_res = supabase.table("sku_master").select("*").execute()
                if sku_res.data:
                    # Column parsing safe handling (checking fallback keys)
                    low_stock_items = [row for row in sku_res.data if float(row.get('current_stock', 0)) < float(row.get('Min Stock Level', row.get('Minimum stock required', 5)))]
                    if low_stock_items:
                        st.error(f"⚠️ **Low Stock Alert Engine:** {len(low_stock_items)} raw materials dropped below standard security threshold settings boundaries!")
                        with st.expander("🔍 View Missing SKU Inventory Allocation List"):
                            for item in low_stock_items:
                                st.write(f"• **{item.get('Ingerdient Name')}**: Stock is `{item.get('current_stock')}` (Min Req: `{item.get('Min Stock Level', item.get('Minimum stock required'))}`)")
            except Exception as e:
                st.caption(f"SKU Alert Engine Link Note: {str(e)}")

            # --- STRUCTURAL TABS RENDER WITH REAL MATHEMATICAL CORES ---
            tab_workdays, tab_dishes, tab_crm, tab_platforms, tab_wastage, tab_expenses, tab_deadstock = st.tabs([
                "📅 Working Days Tracker", "🍲 Dish Performance Matrix", "👥 Customer Retention (CRM)",
                "📱 Platform Individual Sales", "🗑️ Food Waste SKU Analysis", "💸 Monthly Expenses Breakdown", 
                "🛑 3-Month Dead Stock Audit"
            ])
            
            # 1. Working Days Tab
            with tab_workdays:
                st.markdown("### 📅 Operational Days Summary Matrix")
                if not df_orders.empty:
                    total_active_days = df_orders['date'].nunique()
                    st.metric(label="Active Counter Invoicing Days", value=f"{total_active_days} Days")
                    
                    df_day_summary = df_orders.groupby("date").agg(
                        Bills_Processed=('bill_number', 'count'),
                        Total_Collection=('amount', 'sum')
                    ).reset_index().sort_values(by="date", ascending=False)
                    
                    st.dataframe(df_day_summary, use_container_width=True)
                else:
                    st.info("Zero active counter transactions trace logs found inside selected calendar boundaries.")

            # 2. Dish Performance Tab
            with tab_dishes:
                st.markdown("### 🍲 Top Performing Dishes & Volume Analytics")
                if not df_orders.empty and 'items_summary' in df_orders.columns:
                    all_items = []
                    for idx, row in df_orders.iterrows():
                        try:
                            import ast
                            # Parse array representation string cleanly
                            items_list = ast.literal_eval(row['items_summary'])
                            for item in items_list:
                                all_items.append({
                                    "Dish Particulars": item.get('dish'),
                                    "Quantity Volume": int(item.get('qty', 0)),
                                    "Revenue Generated (₹)": float(item.get('amount', 0))
                                })
                        except:
                            pass
                    if all_items:
                        df_dishes = pd.DataFrame(all_items)
                        df_summary = df_dishes.groupby("Dish Particulars").sum().reset_index().sort_values(by="Quantity Volume", ascending=False)
                        
                        st.dataframe(df_summary, use_container_width=True)
                        st.bar_chart(data=df_summary, x="Dish Particulars", y="Quantity Volume")
                    else:
                        st.info("Item summaries parser array layout lines empty.")
                else:
                    st.info("No active production sales logs captured to map dish volume distribution trends.")

            # 3. Customer CRM Tab
            with tab_crm:
                st.markdown("### 👥 Customer Base Retention Ledger")
                if not df_orders.empty and 'phone_number' in df_orders.columns:
                    df_crm = df_orders.copy()
                    df_crm['phone_number'] = df_crm['phone_number'].replace('', 'N/A').fillna('N/A')
                    df_cust = df_crm.groupby(['customer_name', 'phone_number']).agg(
                        Total_Orders=('bill_number', 'count'),
                        Total_Spent=('amount', 'sum')
                    ).reset_index().sort_values(by="Total_Orders", ascending=False)
                    
                    st.dataframe(df_cust, use_container_width=True)
                else:
                    st.info("CRM baseline analytics empty inside selected date brackets.")

            # 4. Platform Performance Tab
            with tab_platforms:
                st.markdown("### 📱 Platform Channel Performance Statistics")
                if not df_orders.empty and 'platform' in df_orders.columns:
                    df_plat = df_orders.groupby("platform")["amount"].agg(['count', 'sum']).reset_index()
                    df_plat.columns = ["Platform Channel", "Order Velocity", "Gross Sales Total (₹)"]
                    
                    st.dataframe(df_plat, use_container_width=True)
                    st.bar_chart(data=df_plat, x="Platform Channel", y="Gross Sales Total (₹)")
                else:
                    st.info("No platform tagged transaction matrix data trace found.")

            # 5. Food Waste SKU Tab
            with tab_wastage:
                st.markdown("### 🗑️ Raw Stock Food Waste & Loss Volatility Matrix")
                if not df_accounts.empty:
                    df_waste = df_accounts[df_accounts['type'].str.contains('Wastage|Loss', case=False, na=False)]
                    if not df_waste.empty:
                        st.dataframe(df_waste[['date', 'category', 'item_name', 'qty', 'amount', 'notes']], use_container_width=True)
                        st.metric("Consolidated Cost Incurred on Loss Modules", f"₹{df_waste['amount'].sum():,.2f}")
                    else:
                        st.success("Perfect Execution! Zero recorded waste allocation rows logs matched.")
                else:
                    st.info("Accounts matrix log lines empty for selected timeframe evaluation parameters.")

            # 6. Monthly Expenses Tab
            with tab_expenses:
                st.markdown("### 💸 Monthly Consolidated Expenditures Breakdown")
                if not df_accounts.empty:
                    df_exp = df_accounts[df_accounts['type'].str.contains('Expense|Fixed Expense', case=False, na=False)]
                    if not df_exp.empty:
                        df_exp_sum = df_exp.groupby("category")["amount"].sum().reset_index()
                        df_exp_sum.columns = ["Expenditure Category", "Amount Spent (₹)"]
                        
                        st.dataframe(df_exp_sum, use_container_width=True)
                        st.metric("Total Operating Expenditure (OPEX)", f"₹{df_exp['amount'].sum():,.2f}")
                        st.bar_chart(data=df_exp_sum, x="Expenditure Category", y="Amount Spent (₹)")
                    else:
                        st.info("Zero operational debit records entered inside this calendar block.")
                else:
                    st.info("No expense ledger entries synchronized.")

            # 7. Dead Stock Tab
            with tab_deadstock:
                st.markdown("### 🛑 Dead Stock Audit Panel (Zero Activity Threshold)")
                try:
                    # Extract active components from recipe templates systematically
                    bom_res = supabase.table("bom_master").select("item_name").execute()
                    active_ingredients = set([row['item_name'] for row in bom_res.data]) if bom_res.data else set()
                    
                    sku_res = supabase.table("sku_master").select("*").execute()
                    if sku_res.data:
                        dead_stock = [r for r in sku_res.data if r.get('Ingerdient Name') not in active_ingredients]
                        if dead_stock:
                            st.warning("Dormant materials discovered inside system cluster storage records matrix (Not bound to any recipe):")
                            df_dead = pd.DataFrame(dead_stock)
                            st.dataframe(df_dead[['Ingerdient Name', 'current_stock', 'Purchase unit']], use_container_width=True)
                        else:
                            st.success("All raw stock variants tightly bound to active production items matrices!")
                except Exception as es:
                    st.caption(f"Inventory Audit Structural Mapping Log Notice: {str(es)}")
                    
    elif admin_pwd != "":
        st.error("Incorrect Password.")
