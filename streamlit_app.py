import streamlit as st
from supabase import create_client
import datetime
import pandas as pd

# ==============================================================================
# 0. CORE CONNECTION PARAMETERS & STATE INITIALIZATION ENGINE
# ==============================================================================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Sig-nature Kitchen", layout="wide")

# Static Password definition for Admin validation protocols
ADMIN_PASSWORD_KEY = "140226"

# Dynamic DB Counter Initialization Engine Block
if "bill_number_counter" not in st.session_state:
    try:
        res_counter = supabase.table("orders").select("bill_number").execute()
        if res_counter.data:
            ext_numbers = []
            for row in res_counter.data:
                b_num = row.get("bill_number", "")
                if b_num and "-" in b_num:
                    try:
                        parts = b_num.split("-")
                        num_part = int(parts[-1])
                        ext_numbers.append(num_part)
                    except:
                        pass
            if ext_numbers:
                st.session_state.bill_number_counter = max(ext_numbers) + 1
            else:
                st.session_state.bill_number_counter = 1
        else:
            st.session_state.bill_number_counter = 1
    except Exception as ec:
        st.sidebar.warning(f"Counter Sync Delay Note: {str(ec)}")
        st.session_state.bill_number_counter = 1

# Initialize Session Memory Cache Arrays Parameters Settings Configuration
if "billing_cart" not in st.session_state:
    st.session_state.billing_cart = []
if "last_bill_data" not in st.session_state:
    st.session_state.last_bill_data = None
if "input_phone_cache" not in st.session_state:
    st.session_state.input_phone_cache = ""
if "input_name_cache" not in st.session_state:
    st.session_state.input_name_cache = ""

# --- UI VISUAL DESIGN STYLE SHEETS HEADER ROW COMPONENT LAYOUT ---
st.markdown('<h1 style="text-align: center; color: #1B5E20;">👨‍🍳 LALALA CLOUD KITCHEN 👨‍🍳</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #388E3C; font-size: 20px;">🍟🍔🥟Good Food 🌯🥙🥪| 🌾Sig-Nature Feel 🧀| 🟩 Pure VEG 🌱</p>', unsafe_allow_html=True)

# Navigation panel setup
st.sidebar.title("Main Menu")
choice = st.sidebar.radio("Go to", ["Billing", "Admin Login"])

# ==============================================================================
# MODULE 1: COMPREHENSIVE INTEGRATED BILLING COUNTER ENGINE WORKSPACE
# ==============================================================================
if choice == "Billing":
    st.subheader("🛒 Billing Counter Workspace")
    
    current_bill_id = f"LALALA-2026-{st.session_state.bill_number_counter:03d}"
    st.write(f"**Current Bill Reference Token:** `{current_bill_id}`")
    st.markdown("---")
    
    # Live Menu Fetch Sequence Execution Pipeline 
    try:
        res_menu = supabase.table("menu_master").select("*").execute()
        menu_list = [item.get('Dish Name') for item in res_menu.data if item.get('Dish Name')] if res_menu.data else []
        menu_rates = {item.get('Dish Name'): float(item.get('Rate', 0) or item.get('Price', 0)) for item in res_menu.data} if res_menu.data else {}
    except:
        menu_list, menu_rates = [], {}

    col_input, col_cart = st.columns([2, 3])

    with col_input:
        st.markdown("### 1. Customer Profiles Validation")
        
        # UI Action Auto-Mapping Hook Processing Form
        cust_phone = st.text_input("Phone Number (Exactly 10 Digits)", value=st.session_state.input_phone_cache, placeholder="Enter 10-digit mobile line")
        
        # Trigger Auto Retrieval Logic Sequence mapping parameters when 10 digit matches metrics
        if cust_phone != st.session_state.input_phone_cache:
            st.session_state.input_phone_cache = cust_phone
            if len(cust_phone) == 10 and cust_phone.isdigit():
                try:
                    profile_check = supabase.table("orders").select("customer_name").eq("phone_number", cust_phone).order("id", descending=True).limit(1).execute()
                    if profile_check.data and profile_check.data[0].get("customer_name"):
                        st.session_state.input_name_cache = profile_check.data[0]["customer_name"]
                        st.rerun()
                except:
                    pass

        cust_name = st.text_input("Customer Name", value=st.session_state.input_name_cache, placeholder="Walking Customer")
        if cust_name != st.session_state.input_name_cache:
            st.session_state.input_name_cache = cust_name

        bill_date = st.date_input("Bill Date", datetime.date.today())
        channel = st.selectbox("Channel Route Distribution", ["Direct Takeaway", "Swiggy", "Zomato", "Party Order"])
        pay_mode = st.selectbox("Payment Mode Integration Method", ["Cash", "UPI", "Credit"])

        st.markdown("---")
        st.markdown("### 2. Dish Selection Line Mapping")
        selected_dish = st.selectbox("Search Dish Item Menu", menu_list)
        qty = st.number_input("Portion Selection (Quantity)", min_value=1, value=1, step=1)

        if st.button("➕ Append Item to Transaction Cart", use_container_width=True):
            if selected_dish:
                st.session_state.billing_cart.append({
                    "dish": selected_dish, 
                    "qty": int(qty), 
                    "rate": menu_rates.get(selected_dish, 0.0),
                    "amount": int(qty) * menu_rates.get(selected_dish, 0.0)
                })
                st.session_state.last_bill_data = None 
                st.rerun()
            else:
                st.error("Invalid choice sequence framework pointer target error.")

    with col_cart:
        st.markdown("### 3. Current Live Invoice View Layout")
        if st.session_state.billing_cart:
            
            # --- GRANULAR STEP-BY-STEP CUSTOM COMPONENT REMOVAL IMPLEMENTATION WORKSPACE ---
            st.markdown("#### Item Allocation List Tracker Matrix:")
            temp_cart = st.session_state.billing_cart.copy()
            
            for index, item_dictionary_element in enumerate(temp_cart):
                row_cols = st.columns([3, 1, 1, 1])
                with row_cols[0]:
                    st.write(f"**{item_dictionary_element['dish']}**")
                with row_cols[1]:
                    st.write(f"Qty: {item_dictionary_element['qty']}")
                with row_cols[2]:
                    st.write(f"₹{item_dictionary_element['amount']:.2f}")
                with row_cols[3]:
                    if st.button("❌ Remove", key=f"del_btn_idx_{index}_{item_dictionary_element['dish']}"):
                        st.session_state.billing_cart.pop(index)
                        st.rerun()
            
            st.markdown("---")
            df_cart = pd.DataFrame(st.session_state.billing_cart)
            bill_total = df_cart['amount'].sum()
            st.metric(label="Total Transaction Ledger Accumulation Value", value=f"₹{bill_total:,.2f}")
            
            # Form Fields Pre-Submission Verification Checks Engine Boundary Rules
            phone_valid_flag = len(cust_phone) == 10 and cust_phone.isdigit()
            
            if not phone_valid_flag and cust_phone != "":
                st.sidebar.error("❌ Phone line format validation boundary rejected: Must be exactly 10 digits numeric sequence rules.")

            if st.button("🏁 Generate & Commit Final Bill Invoice", type="primary", use_container_width=True):
                if cust_phone != "" and not phone_valid_flag:
                    st.error("Execution Interrupted Sequence Framework Flag: Cannot commit data records using improper 10-digit parameter metrics formatting.")
                else:
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

                    try:
                        # 1. Base DB Insertion Sequence Logic Commit 
                        supabase.table("orders").insert({
                            "date": str(bill_date), 
                            "bill_number": current_bill_id,
                            "customer_name": st.session_state.last_bill_data['name'],
                            "phone_number": cust_phone, 
                            "platform": channel,
                            "payment_mode": pay_mode, 
                            "amount": float(bill_total),
                            "items_summary": str(st.session_state.billing_cart)
                        }).execute()
                        
                        # 2. Automated Warehousing Dynamic Subtraction Loop 
                        for cart_item in st.session_state.billing_cart:
                            dish_name_token = cart_item.get('dish')
                            ordered_qty = float(cart_item.get('qty', 1))
                            
                            bom_query = supabase.table("bom_master").select("*").eq("dish_name", dish_name_token).execute()
                            if bom_query.data:
                                for recipe_row in bom_query.data:
                                    ingredient_name = recipe_row.get("item_name")
                                    recipe_unit_qty = float(recipe_row.get("qty", 0))
                                    total_deduction = recipe_unit_qty * ordered_qty
                                    
                                    sku_lookup = supabase.table("sku_master").select("current_stock").eq("Ingerdient Name", ingredient_name).execute()
                                    if sku_lookup.data:
                                        current_live_stock = float(sku_lookup.data[0]['current_stock'])
                                        new_calculated_stock = current_live_stock - total_deduction
                                        
                                        supabase.table("sku_master").update({"current_stock": new_calculated_stock}).eq("Ingerdient Name", ingredient_name).execute()
                        
                        st.success(f"✅ Success Log: Bill Invoice Reference {current_bill_id} Commited to Cloud Repositories!")
                        st.session_state.billing_cart = []
                        st.session_state.bill_number_counter += 1
                        st.rerun()
                    except Exception as e:
                        st.error(f"Central Database Storage Pipeline Interruption Notice: {str(e)}")
        else:
            st.info("Invoice assembly empty status tracker. Ready to accept items lists entries rules loops.")

        # --- PERSISTENT SHARE & HARD PRINT ANCHORS LOGIC PANEL ---
        if st.session_state.last_bill_data:
            lb = st.session_state.last_bill_data
            st.markdown("---")
            st.info(f"✨ **Active Document Buffered Line: {lb['id']}** | Balance Due: ₹{lb['total']:.2f}")
            
            sh_col1, sh_col2 = st.columns(2)
            with sh_col1:
                if st.button("🖨️ Launch Direct Thermal Print Component Layout", use_container_width=True):
                    html_items = "".join([f"<tr><td>{item['dish']} x {item['qty']}</td><td>₹{item['amount']:.2f}</td></tr>" for item in lb['raw_items']])
                    print_html = f"""
                    <div style="font-family:monospace; width:280px; padding:10px;">
                        <h3 style="text-align:center;">LALALA CLOUD KITCHEN</h3>
                        <p>Invoice Token: {lb['id']}<br>Execution Timestamp: {datetime.date.today()}</p>
                        <hr><table>{html_items}</table><hr>
                        <h4>Total: ₹{lb['total']:.2f}</h4>
                    </div>
                    <script>window.print();</script>
                    """
                    st.components.v1.html(print_html, height=0, width=0)

            with sh_col2:
                if lb['phone']:
                    wa_msg = f"*LALALA KITCHEN*\\nBill Reference: {lb['id']}\\nTotal Bill: ₹{lb['total']:.2f}\\nOrdered Items Log:\\n{lb['items']}"
                    wa_url = f"https://wa.me/91{lb['phone']}?text={wa_msg.replace(' ', '%20').replace('\\n', '%0A')}"
                    st.link_button("💬 Dispatch via Cloud WhatsApp API Gateway", wa_url, use_container_width=True)
                else:
                    st.warning("Communication line omitted parameter step: Verification phone value missing mapping indices.")

            if st.button("🆕 Initialize & Trigger Start New Bill Interface Sequence", use_container_width=True, type="secondary"):
                st.session_state.last_bill_data = None
                st.session_state.billing_cart = []
                st.session_state.input_phone_cache = ""
                st.session_state.input_name_cache = ""
                st.rerun()

# ==============================================================================
# MODULE 2: SECURED ADMIN HUB DASHBOARDS AND LOGISTICS ARCHITECTURE
# ==============================================================================
elif choice == "Admin Login":
    st.subheader("🔒 Administrator Operational Credentials Panel")
    admin_pwd = st.text_input("Security Encryption Password Key Validation Gate", type="password")
    
    if admin_pwd == ADMIN_PASSWORD_KEY:
        st.success("Authorization confirmed status. Administrative structural layout controls unlocked.")
        
        admin_tab = st.sidebar.radio("Admin Workspace Options Menu", 
            ["Inventory Status Tracking Grid", "Accounts Financial Entry Ledger", "Wastage Records Handling", "Business Report Intelligence"])
        
        # 1. LIVE INVENTORY MANAGEMENT TRACKER MODULE 
        if admin_tab == "Inventory Status Tracking Grid":
            st.subheader("📦 Real-Time Warehouse Stock Tracker Engine")
            sku_data = supabase.table("sku_master").select("*").execute()
            if sku_data.data:
                df = pd.DataFrame(sku_data.data)
                st.dataframe(df, use_container_width=True)
                
                if st.button("Generate Replenishment Order Recommendation List Matrix"):
                    low = df[df['current_stock'].astype(float) < df['Min Stock Level'].astype(float)]
                    if not low.empty:
                        st.warning("⚠️ High Supply Vulnerability Alert Notice: Below Threshold Baseline Rules Counters:")
                        st.write(low[['Ingerdient Name', 'current_stock', 'Purchase unit', 'Min Stock Level']])
                    else:
                        st.success("Logistics safety clearance check complete: All tracking ingredient volumes conform safely within optimal ranges.")

        # 2. ACCOUNTS FINANCIAL MANAGEMENT WORKSPACE PORTAL 
        elif admin_tab == "Accounts Financial Entry Ledger":
            st.subheader("💰 Accounting Ledger Records Validation Interface")
            acc_type = st.radio("Navigation Subcategory Options Matrix", 
                ["Raw Materials Procurement Entry", "Fixed Operational Overheads Expenses", "Direct Customer Outstanding Credit Tracker Ledger", "Aggregator Channels Verification Settlements Pipeline"], horizontal=True)
            st.markdown("---")
            
            # PROCUREMENT BALANCING AND LEDGER ENTRIES RULES LOGIC COMPONENT FORM
            if acc_type == "Raw Materials Procurement Entry":
                st.markdown("### 🛒 Materials Procurement Input Forms Integration")
                p_item_res = supabase.table("sku_master").select("Ingerdient Name", "Purchase unit").execute()
                item_data = {i['Ingerdient Name']: i['Purchase unit'] for i in p_item_res.data} if p_item_res.data else {}
                
                col1, col2 = st.columns(2)
                with col1:
                    p_date = st.date_input("Procurement Log Date", datetime.date.today(), key="p_date")
                    p_item = st.selectbox("Select Target Raw Material Ingredient Line", list(item_data.keys()), key="p_item")
                    s_unit = item_data.get(p_item, "")
                    st.info(f"Operational Metrics Target Baseline Unit Category: **{s_unit}**")
                with col2:
                    p_qty = st.number_input(f"Procured Supply Volume Quantity ({s_unit})", min_value=0.1, key="p_qty")
                    p_amt = st.number_input("Gross Invoiced Operational Currency Spent (₹)", min_value=0.0, key="p_amt")
                
                if st.button("Commit Procurement Records Ledger Write Query"):
                    curr_res = supabase.table("sku_master").select("current_stock").eq("Ingerdient Name", p_item).execute()
                    curr = float(curr_res.data[0]['current_stock'])
                    
                    supabase.table("sku_master").update({"current_stock": curr + p_qty}).eq("Ingerdient Name", p_item).execute()
                    supabase.table("accounts").insert({
                        "date": str(p_date), "type": "Purchase", "category": "Raw Material", 
                        "item_name": p_item, "amount": p_amt, "qty": p_qty, "unit": s_unit
                    }).execute()
                    st.success("✅ Log committed: Raw stock indicators metrics increments successfully applied parameters updates!")

            # OVERHEAD EXPENSES CAPTURING INTERFACE MODULE COMPONENT FORM
            elif acc_type == "Fixed Operational Overheads Expenses":
                st.markdown("### 💸 Fixed Business Expenditure Processing Registry")
                e_date = st.date_input("Expense Ledger Log Date", datetime.date.today(), key="e_date")
                e_cat = st.selectbox("Expenditure Structural Framework Type Category", ["Rent", "EB Bill", "Salary", "Gas", "Maintenance", "Other"], key="e_cat")
                e_amt = st.number_input("Currency Outflow Amount Matrix Metric (₹)", min_value=0.0, key="e_amt")
                
                if st.button("Save Overhead Outflow Expense Line Item Entry"):
                    supabase.table("accounts").insert({"date": str(e_date), "type": "Fixed Expense", "category": e_cat, "amount": e_amt}).execute()
                    st.success("✅ Operational expense tracking row committed to financial analytics database indices!")

            # DIRECT INDIVIDUAL PARTY OUTSTANDING CREDIT DATA MATRIX HUB MANAGEMENT PANEL 
            elif acc_type == "Direct Customer Outstanding Credit Tracker Ledger":
                st.markdown("### 👥 Personal Non-Platform Client Credit Monitoring Facility Ledger")
                try:
                    credit_res = supabase.table("orders").select("*").eq("payment_mode", "Credit").execute()
                    if credit_res.data:
                        df_credit_orders = pd.DataFrame(credit_res.data)
                        
                        if 'platform' in df_credit_orders.columns:
                            df_credit_orders = df_credit_orders[~df_credit_orders['platform'].isin(['Swiggy', 'Zomato'])]
                        if 'customer_name' in df_credit_orders.columns:
                            df_credit_orders = df_credit_orders[~df_credit_orders['customer_name'].isin(['Swiggy', 'Zomato'])]
                        
                        if not df_credit_orders.empty:
                            df_cust_credit = df_credit_orders.groupby(['customer_name', 'phone_number'])['amount'].sum().reset_index()
                            df_cust_credit.columns = ["Client Name", "Contact Token", "Total Credit Accumulated (₹)"]
                            
                            recovery_res = supabase.table("accounts").select("*").eq("category", "Credit Recovery").execute()
                            recovery_dict = {}
                            if recovery_res.data:
                                for rec_row in recovery_res.data:
                                    phone_tag = rec_row.get("notes", "").replace("Phone Recovery: ", "").strip()
                                    recovery_dict[phone_tag] = recovery_dict.get(phone_tag, 0.0) + float(rec_row.get("amount", 0))
                            
                            verified_credit_list = []
                            for _, row in df_cust_credit.iterrows():
                                ph = str(row["Contact Token"])
                                total_sales_debited = float(row["Total Credit Accumulated (₹)"])
                                total_recovered = float(recovery_dict.get(ph, 0.0))
                                net_outstanding = total_sales_debited - total_recovered
                                
                                if net_outstanding > 0:
                                    verified_credit_list.append({
                                        "Customer Name": row["Client Name"], "Phone Number": ph,
                                        "Total Bill Credit (₹)": total_sales_debited, "Total Cleared (₹)": total_recovered,
                                        "Net Outstanding Due (₹)": net_outstanding
                                    })
                            
                            if verified_credit_list:
                                df_final_dues = pd.DataFrame(verified_credit_list)
                                st.error(f"⚠️ **Direct Client Debts Allocation Alert Checklist Indicators:** Net Collection Backlog Liability: ₹{df_final_dues['Net Outstanding Due (₹)'].sum():,.2f}")
                                st.dataframe(df_final_dues, use_container_width=True)
                                
                                st.markdown("#### 📥 Log Client Credit Recovery Reduction Installment Outflow Receipt Form")
                                rec_col1, rec_col2 = st.columns(2)
                                with rec_col1:
                                    r_date = st.date_input("Recovery Transaction Settlement Date Timestamp", datetime.date.today(), key="rec_cl_dt")
                                    target_client = st.selectbox("Select Target Active Outstanding Profile Reference Key", [f"{r['Customer Name']} ({r['Phone Number']})" for r in verified_credit_list], key="rec_cl_sl")
                                with rec_col2:
                                    r_amount = st.number_input("Liquid Cash Received Reduction Face Value Balance (₹)", min_value=0.0, step=50.0, key="rec_cl_am")
                                
                                if st.button("📡 Finalize and Write Credit Balance Reduction Processing Line"):
                                    if r_amount > 0:
                                        ext_phone = target_client.split("(")[-1].replace(")", "").strip()
                                        ext_name = target_client.split(" (")[0].strip()
                                        supabase.table("accounts").insert({
                                            "date": str(r_date), "type": "Income", "category": "Credit Recovery",
                                            "item_name": f"Credit Recovery from {ext_name}", "qty": 1, "amount": float(r_amount), "notes": f"Phone Recovery: {ext_phone}"
                                        }).execute()
                                        st.success(f"✅ Recovery balance applied adjustments loop metrics! Clear ₹{r_amount} out of debtor balance ledger.")
                                        st.rerun()
                            else:
                                st.success("🎉 Financial health parameters balanced baseline clear check: Customer outstandings metrics equal zero values arrays.")
                        else:
                            st.info("Zero direct customer credit terms identified inside central tracking lists loops structures.")
                    else:
                        st.info("Database table logs collections profiles empty on client ledger entries models checks.")
                except Exception as ex_cr:
                    st.caption(f"Evaluation Exception on Client Tracking Systems Routine Execution Logic: {str(ex_cr)}")

            # THIRD PARTY FOOD DELIVERY SERVICES AGGREGATOR RECONCILIATION GATEWAY COMPONENT CONTROL FORM
            elif acc_type == "Aggregator Channels Verification Settlements Pipeline":
                st.markdown("### 💳 Automated Third Party Channel Settlements Reconciliation Modules Engine")
                st.markdown("#### 📊 Aggregators Channels Net Revenue Liability Discrepancies Matrix")
                p_metrics_cols = st.columns(2)
                platforms_list = ["Zomato", "Swiggy"]
                
                for idx, plat_tag in enumerate(platforms_list):
                    try:
                        s_query = supabase.table("orders").select("amount").eq("platform", plat_tag).execute()
                        gross_calc_total = sum(float(r['amount']) for r in s_query.data) if s_query.data else 0.0
                        
                        p_query = supabase.table("accounts").select("amount").eq("category", f"{plat_tag} Payout").execute()
                        payout_calc_total = sum(float(r['amount']) for r in p_query.data) if p_query.data else 0.0
                        
                        live_outstanding_payout_index = gross_calc_total - payout_calc_total
                        
                        with p_metrics_cols[idx]:
                            st.metric(label=f"Net Open Unsettled Balance Platform Target Flow ({plat_tag})", 
                                value=f"₹{live_outstanding_payout_index:,.2f}", 
                                delta=f"Gross Aggregated Historical Sales: ₹{gross_calc_total:,.2f}", delta_color="off")
                    except Exception as e_metric:
                        st.caption(f"Reconciliation Metric Matrix Dynamic Computation Pipeline Stalled Loop Parameter Issue: {str(e_metric)}")
                        
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    s_platform = st.selectbox("Select Target Channels Platform Operator Identifier", ["Zomato", "Swiggy"], key="set_plat")
                    start_date = st.date_input("Settlement Evaluation Frame Window Start Date", datetime.date.today() - datetime.timedelta(days=7), key="set_start")
                    end_date = st.date_input("Settlement Evaluation Frame Window End Date", datetime.date.today(), key="set_end")
                with col2:
                    payout_received = st.number_input("Net Actual Liquidity Received inside Corporate Bank Accounts (₹)", min_value=0.0, step=100.0, key="set_cash")
                
                if st.button("Execute Settlement Matching & Automate Commission Variance Expense Entry"):
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
                                    (df_orders[d_col] >= start_date) & (df_orders[d_col] <= end_date)
                                ]
                                gross_sales = float(filtered_df[a_col].sum())
                    except Exception as e:
                        st.error(f"Channel Pipeline Analysis Scan Execution Latency Notice: {str(e)}")
                    
                    if gross_sales == 0:
                        st.warning(f"No transactions traced within specific date metrics brackets targets for {s_platform}. Using inputs cash base values baseline coordinates variables lines.")
                        gross_sales = payout_received
                    
                    commission_deducted = gross_sales - payout_received
                    if commission_deducted < 0: 
                        commission_deducted = 0.0
                    
                    supabase.table("accounts").insert({
                        "date": str(datetime.date.today()), "type": "Revenue", "category": f"{s_platform} Payout",
                        "item_name": f"Period Frame Settlement: {start_date} to {end_date}", "amount": payout_received,
                        "notes": f"Gross Platform Value Target: {gross_sales:.2f}"
                    }).execute()
                    
                    if commission_deducted > 0:
                        supabase.table("accounts").insert({
                            "date": str(datetime.date.today()), "type": "Expense", "category": "Platform Commission",
                            "item_name": s_platform, "amount": commission_deducted,
                            "notes": f"Automated commission calculation log cutoff reference for period: {start_date} to {end_date}"
                        }).execute()
                    
                    st.success(f"🎉 Reconciliation Process Complete: Channels Pipeline Balances Synced! Base Value: ₹{gross_sales:,.2f} | Dispatched Balance Bank Account Transfer Clear: ₹{payout_received:,.2f}")
                    st.metric(label="Calculated Automated Platform Retention Fee (Commission Expense)", value=f"₹{commission_deducted:,.2f}")

        # 3. COMPREHENSIVE REVENUE LEAKAGE, WASTAGE, AND INVENTORY REDUCTION LOSS LOG MODULE CONTROL COMPONENT FORM
        elif admin_tab == "Wastage Records Handling":
            st.subheader("🗑️ Inventory Degradation, Spoilage, Waste & Complimentary Promotion Allocation Systems")
            w_category = st.radio("Select Loss Configuration Type Allocation", ["Raw Material Loss", "Cooked Item Waste", "Complimentary / Promo"], horizontal=True)
            
            try:
                m_res = supabase.table("menu_master").select("*").execute()
                possible_cols = ['item_name', 'Item Name', 'Item_Name', 'Dish Name']
                first_row = m_res.data[0] if m_res.data else {}
                actual_col = next((col for col in possible_cols if col in first_row), None)
                system_dish_list = [m[actual_col] for m in m_res.data] if actual_col else []
            except:
                system_dish_list = []

            # A. RAW MATERIAL LOSS PROCESSING AND INVENTORY REDUCTION ENGINE ROUTINES CORRECTIONS BLOCK CRITICAL LAYOUT
            if w_category == "Raw Material Loss":
                w_res = supabase.table("sku_master").select("Ingerdient Name", "Purchase unit", "current_stock").execute()
                w_data = {i['Ingerdient Name']: {"unit": i['Purchase unit'], "stock": i['current_stock']} for i in w_res.data} if w_res.data else {}
                
                col1, col2 = st.columns(2)
                with col1:
                    w_date = st.date_input("Loss Record Incident Date", datetime.date.today(), key="w_raw_date")
                    w_item = st.selectbox("Select Impacted Raw Material Ingredient Base", list(w_data.keys()), key="w_raw_item")
                    s_unit, s_stock = w_data[w_item]["unit"], float(w_data[w_item]["stock"])
                    st.warning(f"Live Vault Warehouse Quantities Content: **{s_stock} {s_unit}**")
                with col2:
                    w_qty = st.number_input(f"Identified Ruined Weight/Volume Loss Entry ({s_unit})", min_value=0.01, key="w_raw_qty")
                    w_reason = st.selectbox("Spoilage Direct Specific Attribution Category Reason", ["Spoilage", "Expired", "Preparation Error"], key="w_raw_res")

                if st.button("Process & Apply Immediate Inventory Stock Downward Adjustment"):
                    if w_qty <= s_stock:
                        new_s = s_stock - float(w_qty)
                        supabase.table("sku_master").update({"current_stock": new_s}).eq("Ingerdient Name", w_item).execute()
                        supabase.table("accounts").insert({
                            "date": str(w_date), "type": "Wastage", "category": "Raw Loss", 
                            "item_name": w_item, "qty": w_qty, "amount": 0, "notes": w_reason
                        }).execute()
                        st.success("✅ Warehouse storage ledger scales balances recalculated. Decrements applied safely down mapping index coordinates lines!")
                    else:
                        st.error("Operation sequence rejected: Requested reduction quantity value metrics exceeds limits parameters storage availability counters fields.")

            # B. COOKED LOSS AND AUTOMATIC WAREHOUSE INVENTORY BALANCING MATRIX DECOUPLING TRIGGER BLOCK CORRECTIONS
            elif w_category == "Cooked Item Waste":
                st.info("Menu Production Wastage Management Panel: Processing calculated background breakdown logic down towards raw item configurations matrices rules.")
                col1, col2 = st.columns(2)
                with col1:
                    w_date = st.date_input("Kitchen Waste Production Date Log", datetime.date.today(), key="w_cook_date")
                    w_dish = st.selectbox("Select Ruined Produced Cooked Dish Entity Template", system_dish_list, key="w_cook_select")
                with col2:
                    w_qty_c = st.number_input("Total Discarded Volumes Portions (Quantity)", min_value=1, step=1, key="w_cook_qty")
                    w_loss = st.number_input("Estimated Production Cost Financial Valuation Penalty (₹)", min_value=0.0, key="w_cook_val")
                
                if st.button("Process Cooked Waste Outflow Ledger Entry & Calibrate Inventory Warehouse Levels"):
                    try:
                        # 1. Financial Ledger Entry Insertion
                        supabase.table("accounts").insert({
                            "date": str(w_date), "type": "Wastage", "category": "Cooked Loss", 
                            "item_name": w_dish, "qty": int(w_qty_c), "amount": w_loss, "notes": "Production/Timeout Kitchen Loss Spoilage Allocation"
                        }).execute()
                        
                        # 2. Dynamic BOM Extraction and Ingredient Reduction Execution Loop
                        bom_query = supabase.table("bom_master").select("*").eq("dish_name", w_dish).execute()
                        if bom_query.data:
                            for recipe_row in bom_query.data:
                                ingredient_name = recipe_row.get("item_name")
                                recipe_unit_qty = float(recipe_row.get("qty", 0))
                                total_deduction = recipe_unit_qty * float(w_qty_c)
                                
                                sku_lookup = supabase.table("sku_master").select("current_stock").eq("Ingerdient Name", ingredient_name).execute()
                                if sku_lookup.data:
                                    current_live_stock = float(sku_lookup.data[0]['current_stock'])
                                    new_calculated_stock = current_live_stock - total_deduction
                                    
                                    supabase.table("sku_master").update({"current_stock": new_calculated_stock}).eq("Ingerdient Name", ingredient_name).execute()
                        
                        st.error(f"🛑 Waste Event Recorded: ₹{w_loss} allocation registered. Warehouse sub-component ingredient balances matching recipe constraints matrix levels automatically decremented safely!")
                    except Exception as e_waste:
                        st.error(f"Cooked Waste Inventory Mitigation Trigger Process Fail Failure Flag Notification: {str(e_waste)}")

            # C. COMPLIMENTARY/PROMO MARKETING DEDUCTION ENGINE ROUTINES IMPLEMENTATION REFACTORING CORRECTIONS 
            elif w_category == "Complimentary / Promo":
                st.success("Marketing Allotment and Free Tasting Protocols Systems Control Interface.")
                col1, col2 = st.columns(2)
                with col1:
                    c_date = st.date_input("Promo Event Operational Execution Date", datetime.date.today(), key="c_date")
                    c_item = st.selectbox("Select Distributed Cooked Menu Item Line Entity", system_dish_list, key="c_name_select")
                with col2:
                    c_qty = st.number_input("Total Gifted Distribution Portions Volume (Quantity)", min_value=1, step=1, key="c_qty")
                    c_cost = st.number_input("Total Cost Evaluation Attributed Towards Marketing Expenditures (₹)", min_value=0.0, key="c_val")
                
                if st.button("Commit Marketing Event Entry & Deduct Supporting Sub-Component Inventory Quantities"):
                    try:
                        # 1. Accounts Database Mappings Insertion
                        supabase.table("accounts").insert({
                            "date": str(c_date), "type": "Expense", "category": "Marketing", 
                            "item_name": c_item, "qty": int(c_qty), "amount": c_cost, "notes": "Promo Free Sample Allocation Distribution Campaign Operations"
                        }).execute()
                        
                        # 2. Dynamic BOM Deconstruction down loop pipelines updating ingredients counts stock scales
                        bom_query = supabase.table("bom_master").select("*").eq("dish_name", c_item).execute()
                        if bom_query.data:
                            for recipe_row in bom_query.data:
                                ingredient_name = recipe_row.get("item_name")
                                recipe_unit_qty = float(recipe_row.get("qty", 0))
                                total_deduction = recipe_unit_qty * float(c_qty)
                                
                                sku_lookup = supabase.table("sku_master").select("current_stock").eq("Ingerdient Name", ingredient_name).execute()
                                if sku_lookup.data:
                                    current_live_stock = float(sku_lookup.data[0]['current_stock'])
                                    new_calculated_stock = current_live_stock - total_deduction
                                    
                                    supabase.table("sku_master").update({"current_stock": new_calculated_stock}).eq("Ingerdient Name", ingredient_name).execute()
                        
                        st.success(f"✅ Marketing event logged. Cost value line entry of ₹{c_cost} registered. Supporting recipe index stock variables values update complete indices calibration matches!")
                    except Exception as e_promo:
                        st.error(f"Promo Logistics Calibration Error Flag Pipeline Trigger Interrupted Status Notice: {str(e_promo)}")

        # 4. BUSINESS INTEL AND HISTORICAL DATABASE ARCHIVAL SCAN ENGINE SEARCH FACILITY 
        elif admin_tab == "Business Report Intelligence":
            st.subheader("📊 Analytical Reports & Intelligence Data Framework Systems")
            st.markdown("### 🔍 Central Archive Invoice Records Retrieval Portal")
            st.info("Input tracking markers tokens patterns parameter values identifiers strings to trigger dynamic system records recall sequences.")
            
            search_col1, search_col2 = st.columns([3, 1])
            with search_col1:
                search_query = st.text_input("Enter Key Unique Target Bill Document Reference ID Number or Phone Value Sequence Token", placeholder="LALALA-2026-", key="central_search_input")
            with search_col2:
                st.write("##")
                search_trigger = st.button("📡 Execute Database Repository Deep Verification Scan", use_container_width=True, type="primary", key="central_search_btn")
            
            if search_trigger and search_query:
                try:
                    search_res = supabase.table("orders").select("*").or_(f"bill_number.ilike.%{search_query}%,phone_number.ilike.%{search_query}%").execute()
                    if search_res.data:
                        st.success(f"🎉 Sequence execution match complete! Traced {len(search_res.data)} matching rows inside logging system fields database files storage grids.")
                        df_search_results = pd.DataFrame(search_res.data)
                        st.dataframe(df_search_results, use_container_width=True)
                    else:
                        st.warning("Query execution zero indices matching state: Criteria pattern input search parameter values matches zero entries profiles inside repository rows logs data arrays.")
                except Exception as e_search:
                    st.error(f"Deep Scan Retrieval Processing Matrix Encountered Interrupted Failure Code State: {str(e_search)}")
    else:
        st.sidebar.error("❌ Invalid Administrative Access Credentials Token: Core operation locked system boundary logic.")
