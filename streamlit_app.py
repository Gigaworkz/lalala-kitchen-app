import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import urllib.parse
import json
import ast

# ==========================================
# 1. LIVE DATABASE CONNECTION (Unga Secrets Line)
# ==========================================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Sig-nature Kitchen", layout="wide")

# ADMIN ACCESSIBILITY TOGGLE
# False = Direct access (No password while testing)
# True  = Password prompt mandatory
ADMIN_ENABLED      = False
ADMIN_PASSWORD_KEY = st.secrets.get("ADMIN_PASSWORD", "140226")

# ==========================================
# 2. AUTOMATED BILL COUNTER INITIALIZATION
# ==========================================
if "bill_number_counter" not in st.session_state:
    try:
        res_counter = supabase.table("orders").select("bill_number").execute()
        if res_counter.data:
            ext_numbers = []
            for row in res_counter.data:
                b_num = row.get("bill_number", "")
                if b_num and "-" in b_num:
                    try:
                        num_part = int(b_num.split("-")[-1])
                        ext_numbers.append(num_part)
                    except:
                        pass
            st.session_state.bill_number_counter = max(ext_numbers) + 1 if ext_numbers else 1
        else:
            st.session_state.bill_number_counter = 1
    except:
        st.session_state.bill_number_counter = 1

# Session Caches
if "billing_cart"      not in st.session_state: st.session_state.billing_cart      = []
if "last_bill_data"    not in st.session_state: st.session_state.last_bill_data    = None
if "input_phone_cache" not in st.session_state: st.session_state.input_phone_cache = ""
if "input_name_cache"  not in st.session_state: st.session_state.input_name_cache  = ""

# Dynamic Unit Converter
def convert_units(qty, from_unit, to_unit):
    f = str(from_unit).lower().strip()
    t = str(to_unit).lower().strip()
    if f == t:
        return qty
    if f == "kg" and t in ["gm", "g"]: return qty * 1000
    if f in ["gm", "g"] and t == "kg": return qty / 1000
    if f in ["l", "litre", "liter"] and t == "ml": return qty * 1000
    if f == "ml" and t in ["l", "litre", "liter"]: return qty / 1000
    return qty

# Fetch Tables Utility
def fetch_table(table_name: str) -> pd.DataFrame:
    try:
        res = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()

# ==========================================
# 3. CORE CORE BUSINESS FUNCTIONS
# ==========================================
def get_bom_cost(dish_name, bom_data, sku_df):
    total_cost = 0.0
    if not bom_data or sku_df.empty:
        return total_cost
    matched = [r for r in bom_data if str(r.get("Dish Name", "")).strip().upper() == dish_name.strip().upper()]
    for row in matched:
        ing      = str(row.get("Ingerdient Name", "")).strip()
        req_qty  = float(row.get("Required quantity") or 0)
        bom_unit = str(row.get("Unit", "gm"))
        
        sku_row = sku_df[sku_df["Ingerdient Name"] == ing]
        if not sku_row.empty:
            mkt_price = float(sku_row.iloc[0].get("Market Price") or 0)
            sku_unit  = str(sku_row.iloc[0].get("Purchase unit") or "gm")
            
            converted_qty = convert_units(req_qty, bom_unit, sku_unit)
            total_cost += converted_qty * mkt_price
    return round(total_cost, 2)

def deduct_stock_via_bom(dish_name, ordered_qty):
    try:
        bom_all = supabase.table("bom_master").select("*").execute()
        if not bom_all.data: return
        matched_rows = [row for row in bom_all.data if str(row.get("Dish Name", "")).strip().upper() == str(dish_name).strip().upper()]
        for recipe_row in matched_rows:
            ingredient_name = str(recipe_row.get("Ingerdient Name", "")).strip()
            required_qty    = float(recipe_row.get("Required quantity") or 0)
            bom_unit        = str(recipe_row.get("Unit", "gm"))
            
            sku_lookup = supabase.table("sku_master").select("*").eq("Ingerdient Name", ingredient_name).execute()
            if sku_lookup.data:
                current_stock = float(sku_lookup.data[0].get("current_stock") or 0)
                sku_unit      = str(sku_lookup.data[0].get("Purchase unit", "gm"))
                
                converted_deduction = convert_units(required_qty * float(ordered_qty), bom_unit, sku_unit)
                supabase.table("sku_master").update({"current_stock": current_stock - converted_deduction}).eq("Ingerdient Name", ingredient_name).execute()
    except Exception as e:
        st.warning(f"Stock deduction warning: {str(e)}")

# ==========================================
# 4. HEADER LAYOUT DESIGN
# ==========================================
st.markdown('<h1 style="text-align:center;color:#1B5E20;">👨‍🍳 LALALA CLOUD KITCHEN 👨‍🍳</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:#388E3C;font-size:20px;">🍟🍔🥟 Good Food | 🌾 Sig-Nature Feel | 🟩 Pure VEG 🌱</p>', unsafe_allow_html=True)

st.sidebar.title("Main Menu")
choice = st.sidebar.radio("Go to", ["Billing", "Admin Control Panel"])

# ==========================================
# MODULE A: BILLING COUNTER
# ==========================================
if choice == "Billing":
    st.subheader("🛒 Billing Counter")
    current_bill_id = f"LALALA-2026-{st.session_state.bill_number_counter:03d}"
    st.write(f"**Current Bill Number:** `{current_bill_id}`")
    st.markdown("---")

    orders_df = fetch_table("orders")
    menu_df = fetch_table("menu_master")

    col_input, col_cart = st.columns([2, 3])

    with col_input:
        st.markdown("### 1. Customer Details")
        
        phone_lookup = st.text_input("Phone Number Lookup (10 digits / N/A)", value=st.session_state.input_phone_cache)
        cust_name_lookup = st.text_input("Customer Name Reference", value=st.session_state.input_name_cache)
        
        autofilled_name = ""
        autofilled_phone = ""

        if phone_lookup and phone_lookup != "N/A" and not orders_df.empty:
            match = orders_df[orders_df["phone_number"] == phone_lookup]
            if not match.empty:
                autofilled_name = match.iloc[-1]["customer_name"]
                st.info(f"💡 Old Customer Found! Name: {autofilled_name}")

        if cust_name_lookup and not orders_df.empty:
            match = orders_df[orders_df["customer_name"].str.lower() == cust_name_lookup.lower()]
            if not match.empty:
                autofilled_phone = match.iloc[-1]["phone_number"]
                st.info(f"💡 Old Customer Found! Phone: {autofilled_phone}")

        final_name = cust_name_lookup if not autofilled_name else autofilled_name
        final_phone = phone_lookup if not autofilled_phone else autofilled_phone

        if final_phone and final_phone != "N/A" and len(final_phone) != 10:
            st.warning("⚠️ Alert: Phone number should be exactly 10 digits!")

        bill_date = st.date_input("Bill Date", value=date.today())
        platform = st.selectbox("Platform Routing", ["Takeaway", "Swiggy", "Zomato", "Party Order"])
        payment_mode = st.selectbox("Payment Mode", ["Cash", "UPI", "Credit"])

        if platform in ["Swiggy", "Zomato"]:
            payment_mode = "Credit"
            st.caption("ℹ️ Swiggy/Zomato orders are handled via System Credit automatically.")

        st.markdown("### 2. Add Dishes")
        if not menu_df.empty:
            dish_options = menu_df["Dish Name"].tolist()
            selected_dish = st.selectbox("Search Dish Item", dish_options)
            dish_price = float(menu_df[menu_df["Dish Name"] == selected_dish].iloc[0]["Price"])
            
            st.write(f"🏷️ Price: ₹{dish_price}")
            order_qty = st.number_input("Quantity", min_value=1, value=1, step=1)
            
            if st.button("➕ Add to Cart"):
                existing = [i for i, item in enumerate(st.session_state.billing_cart) if item["dish"] == selected_dish]
                if existing:
                    st.session_state.billing_cart[existing[0]]["qty"] += order_qty
                else:
                    st.session_state.billing_cart.append({"dish": selected_dish, "qty": order_qty, "price": dish_price})
                st.toast("Item added to cart!")
        else:
            st.error("No dishes found in menu_master!")

    with col_cart:
        st.markdown("### 3. Invoice Cart View")
        if st.session_state.billing_cart:
            cart_data = []
            total_amount = 0.0
            for idx, item in enumerate(st.session_state.billing_cart):
                subtotal = item["qty"] * item["price"]
                total_amount += subtotal
                cart_data.append({"Index": idx + 1, "Dish Name": item["dish"], "Qty": item["qty"], "Rate (₹)": item["price"], "Subtotal (₹)": subtotal})
            
            st.table(pd.DataFrame(cart_data).set_index("Index"))
            
            # Individual Remove buttons
            for idx, item in enumerate(st.session_state.billing_cart):
                if st.button(f"🗑️ Remove Item #{idx+1} ({item['dish']})", key=f"del_{idx}"):
                    st.session_state.billing_cart.pop(idx)
                    st.rerun()

            st.markdown(f"### 💵 **Total Amount: ₹{total_amount}**")
            
            if st.button("🚀 GENERATE BILL & CHECKOUT"):
                items_summary = ", ".join([f"{i['dish']} (x{i['qty']})" for i in st.session_state.billing_cart])
                
                # Insert Order row
                order_payload = {
                    "date": str(bill_date),
                    "bill_number": current_bill_id,
                    "customer_name": final_name if final_name else "Walk-In",
                    "phone_number": final_phone if final_phone else "N/A",
                    "platform": platform,
                    "payment_mode": payment_mode,
                    "amount": total_amount,
                    "items_summary": items_summary
                }
                supabase.table("orders").insert(order_payload).execute()
                
                # Account Flow Logic
                if payment_mode != "Credit":
                    supabase.table("accounts").insert({
                        "date": str(bill_date), "type": "Revenue", "category": "Sales",
                        "item_name": f"Bill {current_bill_id}", "amount": total_amount, "qty": 1, "unit": "nos", "notes": f"Paid via {payment_mode}"
                    }).execute()
                
                # Stock Deduction Route
                for item in st.session_state.billing_cart:
                    deduct_stock_via_bom(item["dish"], item["qty"])
                    
                st.success(f"Bill Generated Successfully: {current_bill_id}")
                
                # Reset operations
                st.session_state.bill_number_counter += 1
                st.session_state.billing_cart = []
                st.rerun()
        else:
            st.info("Cart is empty.")

# ==========================================
# MODULE B: ADMIN CONTROL PANEL
# ==========================================
if choice == "Admin Control Panel":
    access_granted = True
    if ADMIN_ENABLED:
        passwd = st.text_input("Enter Admin Passcode", type="password")
        if passwd != ADMIN_PASSWORD_KEY:
            access_granted = False
            st.warning("🔒 Restricted access area.")
            
    if access_granted:
        sku_df = fetch_table("sku_master")
        bom_df = fetch_table("bom_master")
        acc_df = fetch_table("accounts")
        orders_df = fetch_table("orders")

        admin_tab = st.radio("Management Desks", [
            "📦 Inventory Status", "💸 Accounts Entry Panel", "🗑️ Wastage Entry", "📊 Report Analytics"
        ], horizontal=True)

        # 1. STOCK TRACKER
        if admin_tab == "📦 Inventory Status":
            st.subheader("Live Stock Status & Worth Tracker")
            if not sku_df.empty:
                sku_df["Status Warning"] = sku_df.apply(lambda r: "🚨 LOW STOCK" if float(r["current_stock"]) <= float(r["Min Stock Level"]) else "✅ OK", axis=1)
                st.dataframe(sku_df, use_container_width=True)
                
                sku_df["Worth"] = sku_df["current_stock"].astype(float) * sku_df["Market Price"].astype(float)
                st.metric("Total Inventory Asset Worth", f"₹{sku_df['Worth'].sum():,.2f}")
            else:
                st.info("SKU master sheet is empty.")

        # 2. ACCOUNTS ENTRY PANEL
        elif admin_tab == "💸 Accounts Entry Panel":
            acc_mode = st.radio("Form Mode", ["Purchase Entry", "Fixed Expenses", "Credit Dashboard", "Channel Payouts"])
            
            if acc_mode == "Purchase Entry" and not sku_df.empty:
                p_date = st.date_input("Purchase Date")
                p_item = st.selectbox("Raw SKU", sku_df["Ingerdient Name"].tolist())
                p_price = st.number_input("Market Unit Price (₹)", min_value=0.0)
                p_qty = st.number_input("Purchased Quantity", min_value=0.0)
                p_unit = st.selectbox("Unit Type", ["gm", "ml", "nos"])
                
                if st.button("Submit Purchase"):
                    match = sku_df[sku_df["Ingerdient Name"] == p_item].iloc[0]
                    sys_unit = match["Purchase unit"]
                    converted = convert_units(p_qty, p_unit, sys_unit)
                    new_stk = float(match["current_stock"]) + converted
                    
                    supabase.table("sku_master").update({"current_stock": new_stk, "Market Price": p_price}).eq("Ingerdient Name", p_item).execute()
                    supabase.table("accounts").insert({
                        "date": str(p_date), "type": "Expense", "category": "Purchase",
                        "item_name": f"Procured: {p_item}", "amount": (p_price * p_qty), "qty": p_qty, "unit": p_unit, "notes": "Inward entry"
                    }).execute()
                    st.success("Purchase added & stock incremented!")
                    st.rerun()

            elif acc_mode == "Fixed Expenses":
                e_date = st.date_input("Overhead Date")
                e_cat = st.selectbox("Category", ["Rent", "EB Bill", "Salary", "Transport", "Other"])
                e_amt = st.number_input("Amount (₹)", min_value=0.0)
                if st.button("Save Expense"):
                    supabase.table("accounts").insert({
                        "date": str(e_date), "type": "Expense", "category": e_cat, "item_name": e_cat, "amount": e_amt, "qty": 1, "unit": "nos", "notes": ""
                    }).execute()
                    st.success("Expense logged to Accounts sheet.")

            elif acc_mode == "Credit Dashboard" and not orders_df.empty:
                st.write("#### Pending Outstanding Recoveries")
                credits = orders_df[orders_df["payment_mode"] == "Credit"]
                if not credits.empty:
                    clients = credits["customer_name"].unique().tolist()
                    sel_client = st.selectbox("Select Client", clients)
                    total_due = credits[credits["customer_name"] == sel_client]["amount"].sum()
                    
                    recovered = acc_df[(acc_df["category"] == "Settlement") & (acc_df["item_name"] == f"Recovery: {sel_client}")]["amount"].sum() if not acc_df.empty else 0.0
                    net_due = total_due - recovered
                    st.metric(f"Net Balance Due for {sel_client}", f"₹{net_due:,.2f}")
                    
                    rec_amt = st.number_input("Recovered Amount (₹)", min_value=0.0)
                    if st.button("Submit Inward Settlement"):
                        supabase.table("accounts").insert({
                            "date": str(date.today()), "type": "Revenue", "category": "Settlement", "item_name": f"Recovery: {sel_client}", "amount": rec_amt, "qty": 1, "unit": "nos", "notes": ""
                        }).execute()
                        st.success("Credit status updated!"); st.rerun()

            elif acc_mode == "Channel Payouts":
                st.write("#### Aggregator Financial Settlements")
                s_sales = orders_df[orders_df["platform"] == "Swiggy"]["amount"].sum() if not orders_df.empty else 0
                z_sales = orders_df[orders_df["platform"] == "Zomato"]["amount"].sum() if not orders_df.empty else 0
                
                st.write(f"**Gross Swiggy Booked Revenue Tracker:** ₹{s_sales}")
                st.write(f"**Gross Zomato Booked Revenue Tracker:** ₹{z_sales}")
                
                target_p = st.selectbox("Channel", ["Swiggy", "Zomato"])
                inward_cash = st.number_input("Net Bank Deposited Amount (₹)", min_value=0.0)
                gross_disp = st.number_input("Gross Platform Order Value Dispatched (₹)", min_value=0.0)
                
                if st.button("Execute Settlement Entry"):
                    comm_loss = gross_disp - inward_cash
                    supabase.table("accounts").insert({"date": str(date.today()), "type": "Revenue", "category": "Settlement", "item_name": f"{target_p} Settlement Bank Inward", "amount": inward_cash, "qty": 1, "unit": "nos", "notes": ""}).execute()
                    if comm_loss > 0:
                        supabase.table("accounts").insert({"date": str(date.today()), "type": "Expense", "category": "Platform Charge", "item_name": f"{target_p} Commission Writeoff", "amount": comm_loss, "qty": 1, "unit": "nos", "notes": ""}).execute()
                    st.success("Payout reconciliation entries recorded successfully.")

        # 3. WASTAGE ENTRY
        elif admin_tab == "🗑️ Wastage Entry":
            w_type = st.radio("Leakage Category", ["Raw Material Loss", "Cooked Item Waste", "Complimentary / Promo"])
            w_date = st.date_input("Audit Event Date")
            
            if w_type == "Raw Material Loss" and not sku_df.empty:
                w_sku = st.selectbox("Select Ingredient", sku_df["Ingerdient Name"].tolist())
                w_qty = st.number_input("Loss Volume", min_value=0.0)
                if st.button("Log Raw Loss"):
                    row = sku_df[sku_df["Ingerdient Name"] == w_sku].iloc[0]
                    supabase.table("sku_master").update({"current_stock": float(row["current_stock"]) - w_qty}).eq("Ingerdient Name", w_sku).execute()
                    supabase.table("accounts").insert({"date": str(w_date), "type": "Expense", "category": "Wastage", "item_name": f"Raw Loss: {w_sku}", "amount": (w_qty * float(row["Market Price"])), "qty": w_qty, "unit": row["Purchase unit"], "notes": ""}).execute()
                    st.success("Wastage updated on SKU table.")
                    
            elif w_type in ["Cooked Item Waste", "Complimentary / Promo"] and not bom_df.empty:
                menu_master_df = fetch_table("menu_master")
                w_dish = st.selectbox("Select Menu Dish", menu_master_df["Dish Name"].tolist() if not menu_master_df.empty else [])
                w_qty = st.number_input("Units Count Volume", min_value=1, step=1)
                if st.button("Log Cooked Waste Adjustments"):
                    cost_per_dish = get_bom_cost(w_dish, bom_df.to_dict('records'), sku_df)
                    deduct_stock_via_bom(w_dish, w_qty)
                    supabase.table("accounts").insert({"date": str(w_date), "type": "Expense", "category": "Wastage", "item_name": f"{w_type}: {w_dish}", "amount": (cost_per_dish * w_qty), "qty": w_qty, "unit": "nos", "notes": ""}).execute()
                    st.success("BOM materials adjusted safely.")

        # 4. REPORTS
        elif admin_tab == "📊 Report Analytics":
            f_d = st.date_input("From Horizon Date", value=date.today()-timedelta(days=30))
            t_d = st.date_input("To Horizon Date", value=date.today())
            
            if not acc_df.empty:
                acc_df["date"] = pd.to_datetime(acc_df["date"]).dt.date
                f_acc = acc_df[(acc_df["date"] >= f_d) & (acc_df["date"] <= t_d)]
                
                rev_sum = f_acc[f_acc["type"] == "Revenue"]["amount"].sum()
                exp_sum = f_acc[f_acc["type"] == "Expense"]["amount"].sum()
                
                st.markdown("### 📊 Profit & Loss Metric Frame")
                c1, c2, c3 = st.columns(3)
                c1.metric("Gross Revenue Receipts", f"₹{rev_sum:,.2f}")
                c2.metric("Total Expenses Cost Outflows", f"₹{exp_sum:,.2f}")
                c3.metric("Net Operational Margin Profit", f"₹{(rev_sum - exp_sum):,.2f}")
                
                st.markdown("### 💸 Fixed Expenditure Overheads Splits")
                st.dataframe(f_acc[f_acc["type"] == "Expense"].groupby("category")["amount"].sum().reset_index())
            else:
                st.info("Accounts pipeline reports empty.")
                
            st.write("---")
            st.markdown("### 🔍 Historical Bill Deep Search Archive")
            query = st.text_input("Look up Reference (Bill No / Phone)")
            if query and not orders_df.empty:
                res = orders_df[(orders_df["bill_number"].str.contains(query, case=False, na=False)) | (orders_df["phone_number"].str.contains(query, na=False))]
                st.dataframe(res)
