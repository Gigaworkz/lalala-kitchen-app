import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import urllib.parse
import json

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
# --- CONNECTION ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Sig-nature Kitchen", layout="wide")

# FIX 1: ADMIN TOGGLE
# False = No password, direct access
# True  = Password required
ADMIN_ENABLED      = False
ADMIN_PASSWORD_KEY = st.secrets.get("ADMIN_PASSWORD", "140226")

# ==========================================
# 2. HELPER DATA FETCHERS & DATA PIPELINES
# ==========================================
def fetch_table(table_name: str) -> pd.DataFrame:
    try:
        res = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()

def generate_bill_number():
    df = fetch_table("orders")
    current_year = "2026"
    prefix = f"LALALA-{current_year}-"
    if df.empty or "bill_number" not in df.columns:
        return f"{prefix}001"
    
    # Filter for current year bills
    year_bills = df[df["bill_number"].str.startswith(prefix, na=False)]
    if year_bills.empty:
        return f"{prefix}001"
    
    try:
        # Extract serial strings and compute highest increment
        serials = year_bills["bill_number"].str.replace(prefix, "").astype(int)
        next_serial = serials.max() + 1
        return f"{prefix}{next_serial:03d}"
    except:
        return f"{prefix}{len(df)+1:03d}"

def convert_units(qty, from_unit, to_unit):
    """
    Standardize metrics gracefully: gm <-> kg, ml <-> L, nos <-> nos.
    Always helps cross-map purchase entities with system units safely.
    """
    f = from_unit.lower().strip()
    t = to_unit.lower().strip()
    if f == t:
        return qty
    # Weight conversions
    if f == "kg" and t in ["gm", "g"]: return qty * 1000
    if f in ["gm", "g"] and t == "kg": return qty / 1000
    # Liquid conversions
    if f in ["l", "litre", "liter"] and t == "ml": return qty * 1000
    if f == "ml" and t in ["l", "litre", "liter"]: return qty / 1000
    return qty

# ==========================================
# 3. CORE LOGIC ENGINE FUNCTIONS
# ==========================================
def get_bom_cost(dish_name, bom_df, sku_df):
    """Calculates making cost for a dish based on raw master price maps."""
    if bom_df.empty or sku_df.empty:
        return 0.0
    dish_bom = bom_df[bom_df["Dish Name"] == dish_name]
    if dish_bom.empty:
        return 0.0
    
    total_cost = 0.0
    for _, row in dish_bom.iterrows():
        ing_name = row["Ingerdient Name"]
        req_qty = float(row["Required quantity"])
        bom_unit = str(row["Unit"]).lower()
        
        sku_row = sku_df[sku_df["Ingerdient Name"] == ing_name]
        if not sku_row.empty:
            mkt_price = float(sku_row.iloc[0]["Market Price"])
            sku_unit = str(sku_row.iloc[0]["Purchase unit"]).lower()
            
            # Map cost to standard equivalents
            converted_qty = convert_units(req_qty, bom_unit, sku_unit)
            total_cost += converted_qty * mkt_price
            
    return round(total_cost, 2)

def deduct_stock_via_bom(dish_name, ordered_qty):
    """Automatically reduces raw materials from SKU Master on sale checkout."""
    bom_df = fetch_table("bom_master")
    sku_df = fetch_table("sku_master")
    if bom_df.empty or sku_df.empty:
        return
        
    dish_bom = bom_df[bom_df["Dish Name"] == dish_name]
    for _, row in dish_bom.iterrows():
        ing_name = row["Ingerdient Name"]
        req_qty = float(row["Required quantity"]) * ordered_qty
        bom_unit = str(row["Unit"])
        
        sku_row = sku_df[sku_df["Ingerdient Name"] == ing_name]
        if not sku_row.empty:
            current_stock = float(sku_row.iloc[0]["current_stock"])
            sku_unit = str(sku_row.iloc[0]["Purchase unit"])
            
            converted_deduction = convert_units(req_qty, bom_unit, sku_unit)
            new_stock = current_stock - converted_deduction
            
            supabase.table("sku_master").update({"current_stock": new_stock}).eq("Ingerdient Name", ing_name).execute()

# ==========================================
# 4. STREAMLIT APPLICATION ROUTING
# ==========================================
st.title("🍳 LALALA CLOUD KITCHEN (Signature Kitchen)")
st.write("---")

# Navigation Tabs
tab_billing, tab_admin = st.tabs(["🛒 BILLING COUNTER", "🔐 ADMIN CONTROL PANEL"])

# ==========================================
# MODULE A: BILLING COUNTER
# ==========================================
with tab_billing:
    st.header("⚡ Instant Orders Settlement Desk")
    
    # Init Session Cart items
    if "cart" not in st.session_state:
        st.session_state.cart = []
    
    # Live cache loads
    orders_df = fetch_table("orders")
    menu_df = fetch_table("menu_master")
    
    col_cust, col_dish = st.columns([1, 1])
    
    with col_cust:
        st.subheader("1. Customer Profile Information")
        
        # Smart Search Trigger UI setup
        phone_lookup = st.text_input("Phone Number Lookup (10 Digits / N/A)", max_chars=12)
        cust_name_lookup = st.text_input("Customer Name Reference")
        
        # Real-time Autofill engine
        autofilled_name = ""
        autofilled_phone = ""
        
        if phone_lookup and phone_lookup != "N/A" and not orders_df.empty:
            match = orders_df[orders_df["phone_number"] == phone_lookup]
            if not match.empty:
                autofilled_name = match.iloc[-1]["customer_name"]
                st.info(f"💡 Found past Record! Match Name: {autofilled_name}")
                
        if cust_name_lookup and not orders_df.empty:
            match = orders_df[orders_df["customer_name"].str.lower() == cust_name_lookup.lower()]
            if not match.empty:
                autofilled_phone = match.iloc[-1]["phone_number"]
                st.info(f"💡 Found past Record! Match Phone: {autofilled_phone}")

        final_name = cust_name_lookup if not autofilled_name else autofilled_name
        final_phone = phone_lookup if not autofilled_phone else autofilled_phone
        
        # Phone validation parameters
        if final_phone and final_phone != "N/A" and len(final_phone) != 10:
            st.warning("⚠️ Warning: Phone number precise limit is exactly 10 digits!")
            
        bill_date = st.date_input("Bill Date", value=date.today())
        platform = st.selectbox("Order Routing Channel", ["Takeaway", "Swiggy", "Zomato", "Party Order"])
        payment_mode = st.selectbox("Payment Handling", ["Cash", "UPI", "Credit"])
        
        # Enforce automated rule: Aggregators act implicitly via Channel credits
        if platform in ["Swiggy", "Zomato"]:
            payment_mode = "Credit"
            st.caption("ℹ️ Third-party Aggregators default cleanly to System Account Credits.")

    with col_dish:
        st.subheader("2. Add Menu items into Cart")
        if not menu_df.empty:
            dish_options = menu_df["Dish Name"].tolist()
            selected_dish = st.selectbox("Search & Pick Dish", dish_options)
            dish_price = float(menu_df[menu_df["Dish Name"] == selected_dish].iloc[0]["Price"])
            
            st.write(f"🏷️ Standard Unit Rate: ₹{dish_price}")
            order_qty = st.number_input("Count Quantity Units", min_value=1, value=1, step=1)
            
            if st.button("➕ Append to Kitchen Cart"):
                # Handle duplicated list indexes cleanly
                existing = [i for i, item in enumerate(st.session_state.cart) if item["dish"] == selected_dish]
                if existing:
                    st.session_state.cart[existing[0]]["qty"] += order_qty
                else:
                    st.session_state.cart.append({
                        "dish": selected_dish,
                        "qty": order_qty,
                        "price": dish_price
                    })
                st.toast(f"Added {selected_dish} successfully!")
        else:
            st.error("Menu Master requires entry list configurations inside database first!")

    st.write("---")
    st.subheader("3. Live Invoice View & Validation")
    
    if st.session_state.cart:
        invoice_data = []
        total_amount = 0.0
        
        for index, item in enumerate(st.session_state.cart):
            subtotal = item["qty"] * item["price"]
            total_amount += subtotal
            invoice_data.append({
                "Serial": index + 1,
                "Dish Name": item["dish"],
                "Quantity Ordered": item["qty"],
                "Rate Unit (₹)": item["price"],
                "Subtotal (₹)": subtotal
            })
            
        inv_df = pd.DataFrame(invoice_data)
        st.table(inv_df.set_index("Serial"))
        
        # Display dynamic row cleaning triggers
        del_cols = st.columns(len(st.session_state.cart))
        for idx, item in enumerate(st.session_state.cart):
            with del_cols[idx]:
                if st.button(f"❌ Remove Item #{idx+1}", key=f"del_{idx}"):
                    st.session_state.cart.pop(idx)
                    st.rerun()
                    
        st.markdown(f"### 💵 **Total Cumulative Order Value: ₹{total_amount}**")
        
        generated_bill_no = generate_bill_number()
        st.write(f"**Assigned Reference Sequence:** {generated_bill_no}")
        
        if st.button("🚀 EXECUTE GENERATE CHECKOUT BILL"):
            # Prepare descriptions summary
            summary_list = [f"{i['dish']} (x{i['qty']})" for i in st.session_state.cart]
            summary_str = ", ".join(summary_list)
            
            # 1. Post to core Orders DB table
            order_payload = {
                "date": str(bill_date),
                "bill_number": generated_bill_no,
                "customer_name": final_name if final_name else "Walk-In Guest",
                "phone_number": final_phone if final_phone else "N/A",
                "platform": platform,
                "payment_mode": payment_mode,
                "amount": total_amount,
                "items_summary": summary_str
            }
            supabase.table("orders").insert(order_payload).execute()
            
            # 2. Financial Accounts Logging Route
            if payment_mode != "Credit":
                acc_payload = {
                    "date": str(bill_date),
                    "type": "Revenue",
                    "category": "Sales",
                    "item_name": f"Bill Receipt {generated_bill_no}",
                    "amount": total_amount,
                    "qty": 1,
                    "unit": "nos",
                    "notes": f"Settled seamlessly via {payment_mode}"
                }
                supabase.table("accounts").insert(acc_payload).execute()
                
            # 3. Deduct active stocks based on underlying recipes
            for item in st.session_state.cart:
                deduct_stock_via_bom(item["dish"], item["qty"])
                
            st.success(f"Transaction Complete! {generated_bill_no} successfully saved.")
            
            # Formulate text links for digital receipts distribution channels
            whatsapp_msg = f"Vanakkam {final_name}! Your bill {generated_bill_no} from LALALA Cloud Kitchen for ₹{total_amount} is ready. Items: {summary_str}. Thanks!"
            encoded_msg = urllib.parse.quote(whatsapp_msg)
            wa_link = f"https://api.whatsapp.com/send?phone=91{final_phone}&text={encoded_msg}" if (final_phone and final_phone != "N/A") else "#"
            
            st.markdown(f"[📲 Share Bill direct to WhatsApp]({wa_link})")
            
            # Reset Cart state cleanly
            st.session_state.cart = []
    else:
        st.info("Current operational cart registry remains empty.")

# ==========================================
# MODULE B: ADMIN CONTROL PANEL
# ==========================================
with tab_admin:
    # Optional Password Verification system
    access_allowed = True
    if PASSWORD_PROTECTED:
        pwd_input = st.text_input("Enter secure Management Credentials passphrase", type="password")
        if pwd_input != ADMIN_PASSWORD:
            access_allowed = False
            st.warning("🔒 Enter correct administrative password to view financial tools.")
            
    if access_allowed:
        st.header("🛠️ Production Control & Financial Dashboard")
        
        # Sub-panels Router
        admin_mode = st.radio("Select Domain Desk Context", [
            "📦 Inventory Status (Stock Tracker)",
            "💸 Accounts Entry Panel (Kanakku Valakku)",
            "🗑️ Wastage Entry Manager",
            "📊 Analytical Reporting Performance Summaries"
        ], horizontal=True)
        
        # Load real-time infrastructure states
        sku_df = fetch_table("sku_master")
        bom_df = fetch_table("bom_master")
        acc_df = fetch_table("accounts")
        orders_df = fetch_table("orders")
        
        # ----------------------------------
        # SUB-PANEL 1: INVENTORY TRACKER
        # ----------------------------------
        if admin_mode == "📦 Inventory Status (Stock Tracker)":
            st.subheader("Live Raw Materials Master Monitor")
            if not sku_df.empty:
                # Dynamic warning threshold check flags
                sku_df["Status Alert"] = sku_df.apply(
                    lambda r: "🚨 REORDER RUNNING LOW" if float(r["current_stock"]) <= float(r["Min Stock Level"]) else "✅ Stable", axis=1
                )
                st.dataframe(sku_df, use_container_width=True)
                
                # Compute total holdings capitalization
                sku_df["Worth"] = sku_df["current_stock"].astype(float) * sku_df["Market Price"].astype(float)
                total_worth = sku_df["Worth"].sum()
                st.metric("📦 Total Live Holding Inventory Asset Worth", f"₹{total_worth:,.2f}")
                
                if st.button("Generate Pending Purchase Run Sheet"):
                    low_stock_df = sku_df[sku_df["Status Alert"] == "🚨 REORDER RUNNING LOW"]
                    if not low_stock_df.empty:
                        st.subheader("📋 Procurement Recommendation Reorder Matrix")
                        st.table(low_stock_df[["Ingerdient Name", "current_stock", "Min Stock Level", "Purchase unit"]])
                        
                        p_list_str = "LALALA Reorder Sheet:\n" + "\n".join([f"- {r['Ingerdient Name']}: Stock {r['current_stock']} {r['Purchase unit']} (Min: {r['Min Stock Level']})" for _, r in low_stock_df.iterrows()])
                        wa_procure = f"https://api.whatsapp.com/send?text={urllib.parse.quote(p_list_str)}"
                        st.markdown(f"[📲 Send Procurement Run Sheet on WhatsApp]({wa_procure})")
                    else:
                        st.success("All raw stock indices report healthy status margins.")
            else:
                st.info("No active components listed in SKU Master registry.")
                
        # ----------------------------------
        # SUB-PANEL 2: ACCOUNTS PANEL
        # ----------------------------------
        elif admin_mode == "💸 Accounts Entry Panel (Kanakku Valakku)":
            acc_type = st.radio("Transaction Flow Form Selection", [
                "Raw Purchase Entry", "Fixed Expenses Registry", "Pending Credit Settlement", "Aggregator Payout Reconciliations"
            ])
            
            if acc_type == "Raw Purchase Entry":
                st.write("### Log Incoming Procurement Receipts")
                p_date = st.date_input("Procurement Date", value=date.today())
                if not sku_df.empty:
                    p_item = st.selectbox("Select Target Raw Material SKU", sku_df["Ingerdient Name"].tolist())
                    p_price = st.number_input("Purchase Price Unit Cost (₹)", min_value=0.0, step=1.0)
                    p_qty = st.number_input("Inward Volume Quantity Count", min_value=0.0, step=0.1)
                    p_unit = st.selectbox("Measurement Unit Matrix", ["gm", "ml", "nos"])
                    
                    if st.button("Submit Purchase Entry Records"):
                        # Match current unit conversions dynamically to system states
                        match_sku = sku_df[sku_df["Ingerdient Name"] == p_item].iloc[0]
                        sys_unit = match_sku["Purchase unit"]
                        converted_inward = convert_units(p_qty, p_unit, sys_unit)
                        
                        new_stock = float(match_sku["current_stock"]) + converted_inward
                        total_cost = p_price * p_qty
                        
                        # Update master matrix metrics concurrently
                        supabase.table("sku_master").update({
                            "current_stock": new_stock,
                            "Market Price": p_price,
                            "price note": f"Last bought on {p_date} in {p_unit} configuration"
                        }).eq("Ingerdient Name", p_item).execute()
                        
                        # Log onto Expense records matrix
                        supabase.table("accounts").insert({
                            "date": str(p_date),
                            "type": "Expense",
                            "category": "Purchase",
                            "item_name": f"Procured: {p_item}",
                            "amount": total_cost,
                            "qty": p_qty,
                            "unit": p_unit,
                            "notes": f"Dynamic Unit Conversion multiplier scaled onto {sys_unit}"
                        }).execute()
                        
                        st.success("Purchase registered successfully! Inventory metrics recalibrated.")
                else:
                    st.error("Setup your target Ingredient list records inside database sheets first.")
                    
            elif acc_type == "Fixed Expenses Registry":
                st.write("### Log Operations Overhead Bills")
                e_date = st.date_input("Expense Billing Window", value=date.today())
                e_cat = st.selectbox("Category Classification", ["Rent", "EB Bill", "Salary", "Transport", "Other"])
                e_amt = st.number_input("Outflow Cash Quantum Value (₹)", min_value=0.0, step=50.0)
                e_notes = st.text_area("Contextual Explanatory Notes")
                
                if st.button("Commit Expense Row Entry"):
                    supabase.table("accounts").insert({
                        "date": str(e_date),
                        "type": "Expense",
                        "category": e_cat,
                        "item_name": e_cat,
                        "amount": e_amt,
                        "qty": 1,
                        "unit": "nos",
                        "notes": e_notes
                    }).execute()
                    st.success(f"Logged overhead record entry mapping out ₹{e_amt} to operational bills.")
                    
            elif acc_type == "Pending Credit Settlement":
                st.write("### Customer Outstanding Recoveries Panel")
                # Deduce structural calculations via outstanding pipelines
                credit_bills = orders_df[orders_df["payment_mode"] == "Credit"] if not orders_df.empty else pd.DataFrame()
                
                if not credit_bills.empty:
                    # Gather recovery balances aggregated historically
                    recovery_df = acc_df[(acc_df["type"] == "Revenue") & (acc_df["category"] == "Settlement")] if not acc_df.empty else pd.DataFrame()
                    
                    clients = credit_bills["customer_name"].unique().tolist()
                    selected_client = st.selectbox("Select Target Client Account", clients)
                    
                    client_total_due = credit_bills[credit_bills["customer_name"] == selected_client]["amount"].sum()
                    client_recovered = recovery_df[recovery_df["item_name"] == f"Recovery: {selected_client}"]["amount"].sum() if not recovery_df.empty else 0.0
                    
                    net_outstanding = client_total_due - client_recovered
                    st.metric(f"Current Outstanding Liability Balance Due for [{selected_client}]", f"₹{net_outstanding:,.2f}")
                    
                    c_date = st.date_input("Settlement Event Date", value=date.today())
                    recv_amt = st.number_input("Inward Liquidation Quantum (₹)", min_value=0.0, max_value=float(net_outstanding) if net_outstanding > 0 else 1000000.0, step=10.0)
                    
                    if st.button("Submit Inward Ledger Balance Recovery"):
                        if recv_amt > 0:
                            supabase.table("accounts").insert({
                                "date": str(c_date),
                                "type": "Revenue",
                                "category": "Settlement",
                                "item_name": f"Recovery: {selected_client}",
                                "amount": recv_amt,
                                "qty": 1,
                                "unit": "nos",
                                "notes": "Credit recovery ledger settlement processing"
                            }).execute()
                            st.success(f"Account credit recovery logged for ₹{recv_amt}.")
                            st.rerun()
                else:
                    st.info("No recorded pending system credit transactions exist on active lines.")
                    
            elif acc_type == "Aggregator Payout Reconciliations":
                st.write("### Channel Commission Settlement Pipeline")
                st.write("#### Live Pending Channel Balances Tracking Dashboard")
                
                # Fetch data structures safely
                orders_data = fetch_table("orders")
                accounts_data = fetch_table("accounts")
                
                # Swiggy/Zomato Total Sales Calculations
                agg_sales_swiggy = orders_data[(orders_data["platform"] == "Swiggy")]["amount"].sum() if not orders_data.empty else 0
                agg_sales_zomato = orders_data[(orders_data["platform"] == "Zomato")]["amount"].sum() if not orders_data.empty else 0
                
                # Calculated Received Channel Payouts Metrics
                if not accounts_data.empty:
                    settled_swiggy = accounts_data[(accounts_data["category"] == "Settlement") & (accounts_data["item_name"] == "Swiggy Settlement Bank Inward")]["amount"].sum()
                    settled_zomato = accounts_data[(accounts_data["category"] == "Settlement") & (accounts_data["item_name"] == "Zomato Settlement Bank Inward")]["amount"].sum()
                    comm_swiggy = accounts_data[(accounts_data["category"] == "Platform Charge") & (accounts_data["item_name"] == "Swiggy Commission Writeoff")]["amount"].sum()
                    comm_zomato = accounts_data[(accounts_data["category"] == "Platform Charge") & (accounts_data["item_name"] == "Zomato Commission Writeoff")]["amount"].sum()
                else:
                    settled_swiggy = settled_zomato = comm_swiggy = comm_zomato = 0
                
                live_swiggy_outstanding = agg_sales_swiggy - (settled_swiggy + comm_swiggy)
                live_zomato_outstanding = agg_sales_zomato - (settled_zomato + comm_zomato)
                
                c1, c2 = st.columns(2)
                c1.metric("🏍️ Swiggy Live Outstanding Balance", f"₹{live_swiggy_outstanding:,.2f}")
                c2.metric("🛵 Zomato Live Outstanding Balance", f"₹{live_zomato_outstanding:,.2f}")
                
                st.write("---")
                st.write("#### Reconcile New Payout Batch File")
                
                f_date = st.date_input("Settlement Range Horizon From", value=date.today() - timedelta(days=7))
                t_date = st.date_input("Settlement Range Horizon To", value=date.today())
                
                target_platform = st.selectbox("Target Aggregator Stream Channel", ["Swiggy", "Zomato"])
                inward_bank_cash = st.number_input("Net Bank Deposited Amount received (₹)", min_value=0.0)
                total_gross_dispatched = st.number_input("Gross Platform Order Valuation dispatched (₹)", min_value=0.0)
                
                implied_commission_losses = total_gross_dispatched - inward_bank_cash
                st.caption(f"Calculated Marketplace Commission Burn Write-off Margin: ₹{implied_commission_losses}")
                
                if st.button("Execute Double-Entry Reconciliation Ledger"):
                    if inward_bank_cash > 0 and total_gross_dispatched >= inward_bank_cash:
                        # 1. Book clean liquid financial ledger inputs mapping revenue
                        supabase.table("accounts").insert({
                            "date": str(t_date),
                            "type": "Revenue",
                            "category": "Settlement",
                            "item_name": f"{target_platform} Settlement Bank Inward",
                            "amount": inward_bank_cash,
                            "qty": 1,
                            "unit": "nos",
                            "notes": f"Bank Settlement Range: {f_date} to {t_date}"
                        }).execute()
                        
                        # 2. Book Platform Commission burns into Expense ledgers concurrently
                        if implied_commission_losses > 0:
                            supabase.table("accounts").insert({
                                "date": str(t_date),
                                "type": "Expense",
                                "category": "Platform Charge",
                                "item_name": f"{target_platform} Commission Writeoff",
                                "amount": implied_commission_losses,
                                "qty": 1,
                                "unit": "nos",
                                "notes": f"Aggregator operational cuts for {target_platform}"
                            }).execute()
                            
                        st.success("Reconciliation records adjusted successfully.")
                        st.rerun()
                    else:
                        st.error("Invalid entry: Gross sales value must exceed net bank cash inputs.")

        # ----------------------------------
        # SUB-PANEL 3: WASTAGE ENTRY MANAGER
        # ----------------------------------
        elif admin_mode == "🗑️ Wastage Entry Manager":
            st.subheader("Inventory Stock Audits & Wastage Correction Desk")
            w_mode = st.radio("Select Leakage Target Type Context", ["Raw Material Loss", "Cooked Item Waste", "Complimentary / Promo"])
            
            w_date = st.date_input("Audit Ledger Date", value=date.today())
            
            if w_mode == "Raw Material Loss":
                if not sku_df.empty:
                    w_sku = st.selectbox("Select Damaged Ingredient SKU", sku_df["Ingerdient Name"].tolist())
                    w_qty = st.number_input("Wastage Quantity Volume Count", min_value=0.0, step=0.1)
                    
                    sku_row = sku_df[sku_df["Ingerdient Name"] == w_sku].iloc[0]
                    s_unit = sku_row["Purchase unit"]
                    st.write(f"Standard operational tracking packaging layout: **{s_unit}**")
                    
                    if st.button("Log Material Loss & Deduct Stock"):
                        cur_stock = float(sku_row["current_stock"])
                        mkt_prc = float(sku_row["Market Price"])
                        calculated_loss_value = w_qty * mkt_prc
                        
                        # Deduct from SKU database table
                        supabase.table("sku_master").update({"current_stock": cur_stock - w_qty}).eq("Ingerdient Name", w_sku).execute()
                        
                        # Post to Accounts as explicit operational loss expense row
                        supabase.table("accounts").insert({
                            "date": str(w_date),
                            "type": "Expense",
                            "category": "Wastage",
                            "item_name": f"Raw Loss: {w_sku}",
                            "amount": calculated_loss_value,
                            "qty": w_qty,
                            "unit": s_unit,
                            "notes": f"Wastage recorded via Raw Material Loss workflow"
                        }).execute()
                        st.success(f"Stock adjusted! Registered ₹{calculated_loss_value} operational deficit loss.")
                else:
                    st.info("Initialize raw elements configuration states first.")
                    
            elif w_mode in ["Cooked Item Waste", "Complimentary / Promo"]:
                menu_master_df = fetch_table("menu_master")
                if not menu_master_df.empty and not bom_df.empty:
                    w_dish = st.selectbox("Select Target Menu Dish Item", menu_master_df["Dish Name"].tolist())
                    w_qty = st.number_input("Dispatched Item Units Count Volume", min_value=1, step=1)
                    
                    if st.button("Log Operational Recipe Leakage Adjustments"):
                        # Calculate dynamic standard loss value maps via raw recipes
                        bom_making_cost = get_bom_cost(w_dish, bom_df, sku_df)
                        total_loss_footprint = bom_making_cost * w_qty
                        
                        # 1. Deduct component stocks sequentially using BOM recipe
                        deduct_stock_via_bom(w_dish, w_qty)
                        
                        # 2. Log expenses into Accounts registry ledger matrix sheets
                        supabase.table("accounts").insert({
                            "date": str(w_date),
                            "type": "Expense",
                            "category": "Wastage",
                            "item_name": f"{w_mode}: {w_dish}",
                            "amount": total_loss_footprint,
                            "qty": w_qty,
                            "unit": "nos",
                            "notes": f"BOM Calculated recipe write-off for {w_dish}"
                        }).execute()
                        
                        st.success(f"Recipe leakage logged. Traced and deducted raw assets worth ₹{total_loss_footprint:,.2f}.")
                else:
                    st.error("BOM Structure map metrics configurations missing from system layers.")

        # ----------------------------------
        # SUB-PANEL 4: ANALYTICAL REPORTING
        # ----------------------------------
        elif admin_mode == "📊 Analytical Reporting Performance Summaries":
            st.subheader("Data Intelligence & Strategic Operations Analytics Matrix")
            
            f_date = st.date_input("Report Window Horizon From", value=date.today() - timedelta(days=30))
            t_date = st.date_input("Report Window Horizon To", value=date.today())
            
            # Global historical dataframe filtering workflows
            if not acc_df.empty:
                acc_df["date"] = pd.to_datetime(acc_df["date"]).dt.date
                f_acc = acc_df[(acc_df["date"] >= f_date) & (acc_df["date"] <= t_date)]
            else: f_acc = pd.DataFrame()
                
            if not orders_df.empty:
                orders_df["date"] = pd.to_datetime(orders_df["date"]).dt.date
                f_orders = orders_df[(orders_df["date"] >= f_date) & (orders_df["date"] <= t_date)]
            else: f_orders = pd.DataFrame()

            # --- SUB REPORT A: P&L ---
            st.markdown("### 📊 Consolidated Profit & Loss Summary")
            rev_sum = f_acc[f_acc["type"] == "Revenue"]["amount"].sum() if not f_acc.empty else 0.0
            exp_sum = f_acc[f_acc["type"] == "Expense"]["amount"].sum() if not f_acc.empty else 0.0
            net_margin = rev_sum - exp_sum
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Gross Attributed Revenue Receipts", f"₹{rev_sum:,.2f}")
            c2.metric("Total Consolidated Cost Overhead Outflows", f"₹{exp_sum:,.2f}")
            c3.metric("Net Dispatched Profit Extraction Margin", f"₹{net_margin:,.2f}", delta=float(net_margin))
            
            # --- SUB REPORT B: WORKING DAYS ---
            st.markdown("### 📅 Operational Dispatch Working Days Analysis")
            if not f_orders.empty:
                unique_days = f_orders["date"].nunique()
                avg_sales_day = f_orders["amount"].sum() / unique_days if unique_days > 0 else 0
                st.write(f"Active Service Delivery Days logged inside the given scope window: **{unique_days} Days**")
                st.write(f"Calculated Mean Sales Density Run-Rate per Active Day: **₹{avg_sales_day:,.2f} / Day**")
            else: st.info("No sales records logged in the specified date range.")

            # --- SUB REPORT C: DISH PERFORMANCE ---
            st.markdown("### 🍲 Menu Performance Volume Density Metrics")
            if not f_orders.empty:
                dish_counts = {}
                for _, row in f_orders.iterrows():
                    # Parse item summary texts
                    summary = str(row["items_summary"])
                    parts = summary.split(", ")
                    for p in parts:
                        if "(" in p:
                            try:
                                d_name = p.split(" (")[0]
                                d_qty = int(p.split("(x")[1].replace(")", ""))
                                dish_counts[d_name] = dish_counts.get(d_name, 0) + d_qty
                            except: pass
                if dish_counts:
                    perf_df = pd.DataFrame(list(dish_counts.items()), columns=["Dish Item Formulation Name", "Volume Units Sold Ordered"]).sort_values(by="Volume Units Sold Ordered", ascending=False)
                    st.bar_chart(perf_df.set_index("Dish Item Formulation Name"))
                    st.table(perf_df)
                else: st.caption("Inconclusive transaction metrics structure data signatures.")
            
            # --- SUB REPORT D: CRM CUSTOMER RETENTION ---
            st.markdown("### 👥 CRM Retention Loyalty Vectors")
            if not f_orders.empty:
                cust_freq = f_orders["customer_name"].value_value_counts() if "customer_name" in f_orders.columns else pd.DataFrame()
                if not cust_freq.empty:
                    st.write("#### Top Loyal Ordering Customer Personas Accounts Profile List")
                    st.dataframe(cust_freq.head(10))
                    
            # --- SUB REPORT E: PLATFORMS SALES ---
            st.markdown("### 📱 Platform Channels Valuation Market Splits")
            if not f_orders.empty:
                p_splits = f_orders.groupby("platform")["amount"].sum().reset_index()
                st.dataframe(p_splits)
                
            # --- SUB REPORT F: WASTAGE ANALYSIS ---
            st.markdown("### 🗑️ Operational Wastage Footprint Tracking Deficit")
            if not f_acc.empty:
                waste_rows = f_acc[f_acc["category"] == "Wastage"]
                if not waste_rows.empty:
                    st.table(waste_rows[["date", "item_name", "amount", "notes"]])
                    st.metric("Total Asset Value Dissipated via Leakage Waste", f"₹{waste_rows['amount'].sum():,.2f}")
                else: st.info("No recorded product leakage adjustments verified within this range window.")

            # --- SUB REPORT G: EXPENSES BREAKDOWN ---
            st.markdown("### 💸 Fixed Capital Expenditure Overheads Breakdown")
            if not f_acc.empty:
                exp_rows = f_acc[f_acc["type"] == "Expense"]
                if not exp_rows.empty:
                    exp_breakdown = exp_rows.groupby("category")["amount"].sum().reset_index()
                    st.dataframe(exp_breakdown)

            # --- SUB REPORT H: DEAD STOCK AUDIT ---
            st.markdown("### 🛑 Dead Stock Audit Monitoring Panel (60-Day Inactivity Matrix)")
            if not sku_df.empty:
                sixty_days_ago = date.today() - timedelta(days=60)
                # Filter out raw products showing zero purchase velocity spikes
                st.caption("Cross-verifying materials lacking incoming procurement activity indexes for more than 60 days.")
                if not f_acc.empty:
                    recent_purchases = f_acc[(f_acc["category"] == "Purchase") & (f_acc["date"] >= sixty_days_ago)]["item_name"].tolist()
                    dead_materials = []
                    for _, r in sku_df.iterrows():
                        p_string = f"Procured: {r['Ingerdient Name']}"
                        if p_string not in recent_purchases:
                            dead_materials.append(r["Ingerdient Name"])
                    if dead_materials:
                        st.warning(f"⚠️ Traced {len(dead_materials)} slow-moving ingredient profiles showing low activity velocity:")
                        st.write(dead_materials)
                    else: st.success("All listed ingredients have shown fresh inbound procurement movement recently.")
                else: st.info("Data logging tracks are currently insufficient to map inventory velocity metrics safely.")
                
            # --- HISTORICAL SEARCH ARCHIVE ENGINE ---
            st.write("---")
            st.markdown("### 🔍 Historical Archive Deep-Search Core Engine")
            search_query = st.text_input("Deep-Query Lookup Match (Provide Target Reference Bill Sequence / Contact Phone Number)")
            if search_query and not orders_df.empty:
                archive_match = orders_df[(orders_df["bill_number"].str.contains(search_query, case=False, na=False)) | 
                                          (orders_df["phone_number"].str.contains(search_query, na=False))]
                if not archive_match.empty:
                    st.subheader("🎯 Verified Document Match Found")
                    st.dataframe(archive_match)
                else:
                    st.error("No historical receipts trace returned matches against provided credentials parameters.")
