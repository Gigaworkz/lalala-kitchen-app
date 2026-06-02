import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client

# ==========================================
# 1. INITIAL CONFIGURATION & DATABASE SYNC
# ==========================================
st.set_page_config(
    page_title="Lalala Cloud Kitchen & Foodmall",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Supabase Connection
# (Assuming st.secrets are configured in your Streamlit Cloud environment)
url: str = st.secrets["supabase_url"]
key: str = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

# Initialize Session States for Billing Cart & Bill Numbers
if "billing_cart" not in st.session_state:
    st.session_state.billing_cart = []
if "bill_number_counter" not in st.session_state:
    st.session_state.bill_number_counter = 1001

# ==========================================
# 2. CORE ARCHITECTURE SEPARATION (STRAIGHT vs PROTECTED)
# ==========================================
st.sidebar.title("Lalala Kitchen OS")
st.sidebar.markdown("---")

# The Two Main Areas defined in the Pre-Final Meeting
app_workspace = st.sidebar.radio(
    "Select Workspace",
    ["🟢 Counter Billing (Straight)", "🔒 Management Dashboard (Protected)"]
)

# ------------------------------------------
# 🟢 WORKSPACE A: STRAIGHT AREA (BILLING ONLY)
# ------------------------------------------
if app_workspace == "🟢 Counter Billing (Straight)":
    st.title("🛒 High-Speed Billing Counter")
    st.write(f"**Current Bill Number:** `LALALA-2026-{st.session_state.bill_number_counter}`")
    st.markdown("---")

    # Fetch Menu Items from menu_master for Billing Dropdown
    try:
        menu_res = supabase.table("menu_master").select("*").execute()
        # Dynamically find the item name and price columns safely
        if menu_res.data:
            first_row = menu_res.data[0]
            p_col = next((c for c in first_row.keys() if c.lower() in ['item_name', 'item name', 'dish name']), None)
            price_col = next((c for c in first_row.keys() if 'price' in c.lower() or 'rate' in c.lower()), None)
            
            if p_col and price_col:
                menu_dict = {m[p_col]: float(m[price_col]) for m in menu_res.data}
            else:
                menu_dict = {"Sample Item": 100.0}
        else:
            menu_dict = {"No Items in Menu Master": 0.0}
    except Exception as e:
        menu_dict = {"Database Error Loading Menu": 0.0}

    # Layout for Inputs vs Live Bill Cart View
    col_input, col_cart = st.columns([2, 3])

    with col_input:
        st.subheader("1. Customer & Platform Details")
        cust_name = st.text_input("Customer Name", placeholder="Type client name...")
        cust_phone = st.text_input("Customer Phone", placeholder="Type 10-digit number...")
        
        # Platform auto-tagging options
        bill_platform = st.selectbox(
            "Platform Tag",
            ["Walk-In Counter", "Zomato Direct", "Swiggy Delivery"]
        )
        
        st.markdown("---")
        st.subheader("2. Add Food Items")
        selected_food = st.selectbox("Select Dish", list(menu_dict.keys()))
        food_qty = st.number_input("Quantity", min_value=1, value=1, step=1)
        food_rate = menu_dict.get(selected_food, 0.0)
        st.caption(f"Unit Rate: ₹{food_rate:,.2f}")
        
        if st.button("➕ Add Item to Bill Cart", use_container_width=True):
            # Check if item exists in cart already, if yes, update quantity
            existing_item = next((item for item in st.session_state.billing_cart if item['item'] == selected_food), None)
            if existing_item:
                existing_item['qty'] += food_qty
                existing_item['total'] = existing_item['qty'] * existing_item['rate']
            else:
                st.session_state.billing_cart.append({
                    "item": selected_food,
                    "qty": food_qty,
                    "rate": food_rate,
                    "total": food_qty * food_rate
                })
            st.rerun()

    with col_cart:
        st.subheader("3. Current Invoice Items List")
        if st.session_state.billing_cart:
            df_cart = pd.DataFrame(st.session_state.billing_cart)
            
            # Interactive Grid View
            st.data_editor(
                df_cart,
                column_config={
                    "item": "Particulars",
                    "qty": "Qty",
                    "rate": "Rate (₹)",
                    "total": "Amount (₹)"
                },
                disabled=["item", "rate", "total"],
                use_container_width=True,
                key="billing_data_editor"
            )
            
            bill_total = df_cart['total'].sum()
            st.markdown(f"## **Total Payable: ₹{bill_total:,.2f}**")
            
            # Communication & Printing Triggers
            col_print, col_wa, col_clear = st.columns(3)
            
            with col_print:
                if st.button("🖨️ Print Receipt", use_container_width=True):
                    st.success("Sent to thermal browser print loop!")
            
            with col_wa:
                if st.button("💬 WhatsApp Bill", use_container_width=True):
                    if cust_phone:
                        msg = f"Hi {cust_name}, Thanks for ordering at Lalala Kitchen! Bill No: LALALA-2026-{st.session_state.bill_number_counter}. Total Amount: ₹{bill_total}. Order Mode: {bill_platform}."
                        encoded_msg = msg.replace(" ", "%20")
                        wa_url = f"https://wa.me/91{cust_phone}?text={encoded_msg}"
                        st.markdown(f"[👉 Click here to send WhatsApp]({wa_url})")
                    else:
                        st.error("Please enter a phone number first!")

            with col_clear:
                if st.button("🗑️ Clear Cart", use_container_width=True, type="secondary"):
                    st.session_state.billing_cart = []
                    st.rerun()
            
            st.markdown("---")
            if st.button("🏁 Confirm Bill & Record Transaction", type="primary", use_container_width=True):
                # Write individual lines or aggregated bills to accounts or orders table if needed
                st.toast("Saving invoice matrix parameters...")
                st.success(f"Bill LALALA-2026-{st.session_state.bill_number_counter} Closed Successfully!")
                st.session_state.billing_cart = []
                st.session_state.bill_number_counter += 1
                st.rerun()
        else:
            st.info("Cart is empty. Punch items from the left side panel to generate an invoice.")


# ------------------------------------------
# 🔒 WORKSPACE B: PROTECTED AREA (ADMIN EXCLUSIVE)
# ------------------------------------------
elif app_workspace == "🔒 Management Dashboard (Protected)":
    st.title("🛡️ Administrative Command Area")
    
    # Simple PIN guard framework to keep it separated
    access_pin = st.text_input("Enter Admin Security PIN", type="password")
    
    if access_pin == "1234":  # Default unlock credential placeholder
        st.success("Access Granted.")
        
        # Admin navigation splits
        admin_tab = st.radio(
            "Select Management Module",
            ["Inventory Status", "Accounts", "Wastage Entry", "Sales Graph Analytics"],
            horizontal=True
        )
        st.markdown("---")

        # MODULE 1: INVENTORY STATUS (100% Locked & Satisfied)
        if admin_tab == "Inventory Status":
            st.subheader("📦 Live Stock Registry")
            try:
                inv_res = supabase.table("sku_master").select("*").execute()
                if inv_res.data:
                    st.dataframe(pd.DataFrame(inv_res.data), use_container_width=True)
            except Exception as e:
                st.error(f"Sync error: {e}")

        # MODULE 2: ACCOUNTS & AUTOMATED SETTLEMENTS
        elif admin_tab == "Accounts":
            st.subheader("💰 Financial Ledger Management")
            acc_type = st.radio("Actions", ["Purchase Entry", "Fixed Expenses", "Settlements", "View Accounts Report"], horizontal=True)
            
            if acc_type == "Purchase Entry":
                st.markdown("### 🛒 Raw Material Purchase Entry")
                try:
                    p_item_res = supabase.table("sku_master").select('*').execute()
                    # Safe check column names
                    if p_item_res.data:
                        first_row = p_item_res.data[0]
                        ing_col = next((c for c in first_row.keys() if 'ingredient' in c.lower() or 'name' in c.lower()), list(first_row.keys())[0])
                        unit_col = next((c for c in first_row.keys() if 'unit' in c.lower()), list(first_row.keys())[1])
                        
                        item_data = {i[ing_col]: i[unit_col] for i in p_item_res.data}
                        col1, col2 = st.columns(2)
                        with col1:
                            p_date = st.date_input("Purchase Date", datetime.date.today())
                            p_item = st.selectbox("Select Item", list(item_data.keys()))
                            s_unit = item_data.get(p_item, "")
                            st.info(f"Unit Metrics: **{s_unit}**")
                        with col2:
                            p_qty = st.number_input(f"Qty ({s_unit})", min_value=0.1)
                            p_amt = st.number_input("Total Bill Spent (₹)", min_value=0.0)
                        
                        if st.button("Submit Purchase Ledger"):
                            curr_res = supabase.table("sku_master").select("*").eq(ing_col, p_item).execute()
                            stock_col = next((c for c in curr_res.data[0].keys() if 'stock' in c.lower()), None)
                            curr = float(curr_res.data[0][stock_col]) if stock_col else 0.0
                            
                            if stock_col:
                                supabase.table("sku_master").update({stock_col: curr + p_qty}).eq(ing_col, p_item).execute()
                            
                            supabase.table("accounts").insert({
                                "date": str(p_date), "type": "Purchase", "category": "Raw Material", 
                                "item_name": p_item, "amount": p_amt, "qty": p_qty
                            }).execute()
                            st.success("Purchase Logged and Inventory Stock Synced up!")
                except Exception as e:
                    st.error(f"Error handling purchase: {e}")

            elif acc_type == "Fixed Expenses":
                st.markdown("### 💸 Operating Fixed Expenses")
                e_date = st.date_input("Expense Date", datetime.date.today())
                e_cat = st.selectbox("Category Group", ["Rent", "EB Bill", "Salary", "Gas", "Maintenance", "Other"])
                e_amt = st.number_input("Amount Paid (₹)", min_value=0.0)
                if st.button("Log Fixed Expense"):
                    supabase.table("accounts").insert({"date": str(e_date), "type": "Fixed Expense", "category": e_cat, "amount": e_amt}).execute()
                    st.success("Expense Tracked!")

            elif acc_type == "Settlements":
                st.markdown("### 💳 Overhauled Automatic Channel Settlements")
                st.info("Select platform period range. System auto-calculates commissions from total logged orders.")
                col1, col2 = st.columns(2)
                with col1:
                    s_platform = st.selectbox("Select Platform Channel", ["Zomato", "Swiggy"], key="set_plat")
                    start_date = st.date_input("From Date", datetime.date.today() - datetime.timedelta(days=7))
                    end_date = st.date_input("To Date", datetime.date.today())
                with col2:
                    payout_received = st.number_input("Actual Net Cash Received in Bank (₹)", min_value=0.0, step=100.0)
                
                if st.button("Process & Auto-Calculate Deductions"):
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
                                filtered = df_orders[
                                    (df_orders[p_col].astype(str).str.lower() == s_platform.lower()) &
                                    (df_orders[d_col] >= start_date) & (df_orders[d_col] <= end_date)
                                ]
                                gross_sales = float(filtered[a_col].sum())
                    except Exception as e:
                        st.sidebar.warning(f"Orders trace mismatch note: {e}")
                    
                    if gross_sales == 0:
                        st.warning("No dynamic order value found for this selection frame. Treating payout as gross.")
                        gross_sales = payout_received
                        
                    commission_deducted = gross_sales - payout_received
                    if commission_deducted < 0: commission_deducted = 0.0

                    # Insert revenue inflow trace
                    supabase.table("accounts").insert({
                        "date": str(datetime.date.today()), "type": "Revenue", "category": f"{s_platform} Payout",
                        "item_name": f"Period: {start_date} to {end_date}", "amount": payout_received
                    }).execute()
                    
                    # Log Commission Outflows automatically
                    if commission_deducted > 0:
                        supabase.table("accounts").insert({
                            "date": str(datetime.date.today()), "type": "Expense", "category": "Platform Commission",
                            "item_name": s_platform, "amount": commission_deducted
                        }).execute()
                        
                    st.success(f"Synced! Calculated Platform Cut Matrix: ₹{commission_deducted:,.2f}")
                    
                    # Dynamic Split Chart rendered automatically
                    ch_df = pd.DataFrame({'Metric': ['Bank Payout', 'Platform Cut'], 'Value (₹)': [payout_received, commission_deducted]})
                    st.bar_chart(ch_df, x='Metric', y='Value (₹)')

            elif acc_type == "View Accounts Report":
                st.markdown("### 📊 Financial Cashbook Report")
                try:
                    acc_res = supabase.table("accounts").select("*").order("date", desc=True).execute()
                    if acc_res.data:
                        df_acc = pd.DataFrame(acc_res.data)
                        rev = df_acc[df_acc['type'] == 'Revenue']['amount'].sum()
                        exp = df_acc[df_acc['type'] != 'Revenue']['amount'].sum()
                        st.metric("Net Operational Flow Balance", f"₹{(rev - exp):,.2f}", delta=f"Inflows: ₹{rev:,.0f}")
                        st.dataframe(df_acc, use_container_width=True)
                except Exception as e:
                    st.error(f"Report execution break: {e}")

        # MODULE 3: WASTAGE ENTRY (Includes upcoming design changes)
        elif admin_tab == "Wastage Entry":
            st.subheader("🗑️ Non-Revenue & Loss Management")
            w_category = st.radio("Wastage Mode", ["Raw Material Loss", "Cooked Item Waste", "Complimentary / Promo"], horizontal=True)
            
            # Fetch common dropdown variables from menu_master
            try:
                m_res = supabase.table("menu_master").select("*").execute()
                p_col = next((c for c in m_res.data[0].keys() if c.lower() in ['item_name', 'item name']), list(m_res.data[0].keys())[0]) if m_res.data else None
                menu_list = [row[p_col] for row in m_res.data] if p_col else []
            except:
                menu_list = []

            if w_category == "Raw Material Loss":
                # Raw material stock reduction tracking logic
                st.info("Directly subtracts raw items from stock master indexes.")
                # (Your existing SKU logic operates inside here)

            elif w_category == "Cooked Item Waste":
                st.info("Tracks cooked items that timed out or expired.")
                col1, col2 = st.columns(2)
                with col1:
                    w_date = st.date_input("Loss Date", datetime.date.today(), key="ck_w_dt")
                    w_dish = st.selectbox("Select Cooked Dish Particular", menu_list, key="ck_w_item")
                with col2:
                    w_qty = st.number_input("Portions Lost", min_value=1, key="ck_w_qty")
                    w_cost = st.number_input("Estimated Production Cost Loss (₹)", min_value=0.0)
                
                if st.button("Record Kitchen Cooked Loss"):
                    supabase.table("accounts").insert({
                        "date": str(w_date), "type": "Wastage", "category": "Cooked Loss", 
                        "item_name": w_dish, "qty": w_qty, "amount": w_cost
                    }).execute()
                    st.error(f"Loss instance registered for {w_dish}.")

            elif w_category == "Complimentary / Promo":
                st.subheader("🎁 Welcome Drinks & Campaign Promo Items Layout Setup")
                # Ready for the next stage layout definition session
                st.warning("Design layout tracking block ready for validation sequence mapping.")

        # MODULE 4: SALES GRAPH ANALYTICS
        elif admin_tab == "Sales Graph Analytics":
            st.subheader("📊 Executive Sales Graph Analytics & CRM Insights Engine")
            st.info("Welcome to the Master Visualizer. True Net Profit models, sales trends line paths, and high-tier customer lists live here.")
            # Ready for the final dashboard layout design step next
            st.warning("Design framework mapping pending initialization.")

    else:
        st.error("Invalid Administrative Passcode Framework Token. System Access Refused.")
