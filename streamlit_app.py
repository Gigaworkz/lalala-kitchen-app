import streamlit as st
from supabase import create_client
import datetime
import pandas as pd
 
# --- CONNECTION ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)
 
st.set_page_config(page_title="Sig-nature Kitchen", layout="wide")
 
ADMIN_PASSWORD_KEY = st.secrets.get("ADMIN_PASSWORD", "140226")
 
# --- BILL COUNTER INIT ---
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
            st.session_state.bill_number_counter = max(ext_numbers) + 1 if ext_numbers else 1
        else:
            st.session_state.bill_number_counter = 1
    except:
        st.session_state.bill_number_counter = 1
 
# --- SESSION STATE INIT ---
if "billing_cart" not in st.session_state:
    st.session_state.billing_cart = []
if "last_bill_data" not in st.session_state:
    st.session_state.last_bill_data = None
if "input_phone_cache" not in st.session_state:
    st.session_state.input_phone_cache = ""
if "input_name_cache" not in st.session_state:
    st.session_state.input_name_cache = ""
 
# ==============================================================================
# HELPER: BOM-BASED STOCK DEDUCTION (FIX 5, 6, 7, 8)
# Case-insensitive dish name match + fixed column name query
# ==============================================================================
def deduct_stock_via_bom(dish_name, ordered_qty):
    try:
        bom_all = supabase.table("bom_master").select("*").execute()
        if not bom_all.data:
            return
 
        # FIX 5: Case-insensitive + strip matching
        matched_rows = [
            row for row in bom_all.data
            if row.get("dish_name", "").strip().upper() == dish_name.strip().upper()
        ]
 
        for recipe_row in matched_rows:
            ingredient_name = recipe_row.get("item_name", "").strip()
            recipe_unit_qty = float(recipe_row.get("qty", 0))
            total_deduction = recipe_unit_qty * float(ordered_qty)
 
            # FIX 6: Correct column name without escaped quotes
            sku_lookup = supabase.table("sku_master").select("current_stock").eq("Ingerdient Name", ingredient_name).execute()
            if sku_lookup.data:
                current_stock = float(sku_lookup.data[0]["current_stock"])
                new_stock = current_stock - total_deduction
                supabase.table("sku_master").update({"current_stock": new_stock}).eq("Ingerdient Name", ingredient_name).execute()
    except Exception as e:
        st.warning(f"Stock deduction note: {str(e)}")
 
 
# --- HEADER ---
st.markdown('<h1 style="text-align:center;color:#1B5E20;">👨‍🍳 LALALA CLOUD KITCHEN 👨‍🍳</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:#388E3C;font-size:20px;">🍟🍔🥟 Good Food | 🌾 Sig-Nature Feel | 🟩 Pure VEG 🌱</p>', unsafe_allow_html=True)
 
st.sidebar.title("Main Menu")
choice = st.sidebar.radio("Go to", ["Billing", "Admin Login"])
 
# ==============================================================================
# MODULE 1: BILLING
# ==============================================================================
if choice == "Billing":
    st.subheader("🛒 Billing Counter")
 
    current_bill_id = f"LALALA-2026-{st.session_state.bill_number_counter:03d}"
    st.write(f"**Current Bill Number:** `{current_bill_id}`")
    st.markdown("---")
 
    try:
        res_menu = supabase.table("menu_master").select("*").execute()
        menu_list = [item.get("Dish Name") for item in res_menu.data if item.get("Dish Name")] if res_menu.data else []
        menu_rates = {item.get("Dish Name"): float(item.get("Rate", 0) or item.get("Price", 0)) for item in res_menu.data} if res_menu.data else {}
    except Exception as e:
        st.error(f"Menu load error: {e}")
        menu_list, menu_rates = [], {}
 
    col_input, col_cart = st.columns([2, 3])
 
    with col_input:
        st.markdown("### 1. Customer Details")
 
        # FIX 1: Phone — 10 digits only or blank = N/A
        cust_phone = st.text_input(
            "Phone Number (10 digits or leave blank for walk-in)",
            value=st.session_state.input_phone_cache,
            placeholder="10-digit number or leave blank"
        )
 
        phone_valid = False
        phone_for_db = "N/A"
 
        if cust_phone == "" or cust_phone.upper() == "N/A":
            phone_valid = True
            phone_for_db = "N/A"
        elif len(cust_phone) == 10 and cust_phone.isdigit():
            phone_valid = True
            phone_for_db = cust_phone
        elif len(cust_phone) == 9:
            st.error("❌ Phone number is too short — must be 10 digits.")
        elif len(cust_phone) == 11:
            st.error("❌ Phone number is too long — must be 10 digits.")
        elif not cust_phone.isdigit():
            st.error("❌ Only numbers allowed.")
        else:
            st.error("❌ Phone must be exactly 10 digits.")
 
        # FIX 2: Auto-fill name from phone
        if cust_phone != st.session_state.input_phone_cache:
            st.session_state.input_phone_cache = cust_phone
            if len(cust_phone) == 10 and cust_phone.isdigit():
                try:
                    profile_check = supabase.table("orders").select("customer_name").eq("phone_number", cust_phone).order("id", desc=True).limit(1).execute()
                    if profile_check.data and profile_check.data[0].get("customer_name"):
                        st.session_state.input_name_cache = profile_check.data[0]["customer_name"]
                        st.rerun()
                except:
                    pass
 
        # FIX 2: Auto-fill phone from name
        cust_name = st.text_input(
            "Customer Name",
            value=st.session_state.input_name_cache,
            placeholder="Walking Customer"
        )
        if cust_name != st.session_state.input_name_cache:
            st.session_state.input_name_cache = cust_name
            if len(cust_name) >= 3 and st.session_state.input_phone_cache == "":
                try:
                    name_check = supabase.table("orders").select("phone_number").eq("customer_name", cust_name).order("id", desc=True).limit(1).execute()
                    if name_check.data and name_check.data[0].get("phone_number"):
                        fetched_phone = name_check.data[0]["phone_number"]
                        if fetched_phone and fetched_phone != "N/A":
                            st.session_state.input_phone_cache = fetched_phone
                            st.rerun()
                except:
                    pass
 
        bill_date = st.date_input("Bill Date", datetime.date.today())
        channel = st.selectbox("Channel", ["Direct Takeaway", "Swiggy", "Zomato", "Party Order"])
        pay_mode = st.selectbox("Payment Mode", ["Cash", "UPI", "Card", "Credit"])
 
        st.markdown("---")
        st.markdown("### 2. Add Dishes")
        selected_dish = st.selectbox("Search Dish", menu_list)
        qty = st.number_input("Quantity", min_value=1, value=1, step=1)
 
        if st.button("➕ Add to Cart", use_container_width=True):
            if selected_dish:
                st.session_state.billing_cart.append({
                    "dish": selected_dish,
                    "qty": int(qty),
                    "rate": menu_rates.get(selected_dish, 0.0),
                    "amount": int(qty) * menu_rates.get(selected_dish, 0.0)
                })
                st.session_state.last_bill_data = None
                st.rerun()
 
    with col_cart:
        st.markdown("### 3. Invoice View")
 
        if st.session_state.billing_cart:
            st.markdown("#### Items in Cart:")
 
            # FIX 4: Individual remove button per item
            temp_cart = st.session_state.billing_cart.copy()
            for index, item in enumerate(temp_cart):
                row_cols = st.columns([3, 1, 1, 1])
                with row_cols[0]:
                    st.write(f"**{item['dish']}**")
                with row_cols[1]:
                    st.write(f"Qty: {item['qty']}")
                with row_cols[2]:
                    st.write(f"₹{item['amount']:.2f}")
                with row_cols[3]:
                    if st.button("❌", key=f"remove_{index}_{item['dish']}"):
                        st.session_state.billing_cart.pop(index)
                        st.rerun()
 
            st.markdown("---")
            df_cart = pd.DataFrame(st.session_state.billing_cart)
            bill_total = df_cart["amount"].sum()
            st.metric("Total Amount", f"₹{bill_total:,.2f}")
 
            if st.button("🏁 Generate Bill", type="primary", use_container_width=True):
                if not phone_valid:
                    st.error("❌ Fix phone number before generating bill.")
                else:
                    items_text = ""
                    for i, r in df_cart.iterrows():
                        items_text += f"• {r['dish']} x {r['qty']} = ₹{r['amount']:.2f}\n"
 
                    st.session_state.last_bill_data = {
                        "id": current_bill_id,
                        "total": bill_total,
                        "phone": phone_for_db,
                        "name": cust_name or "Walking Customer",
                        "items": items_text,
                        "raw_items": st.session_state.billing_cart.copy()
                    }
 
                    try:
                        supabase.table("orders").insert({
                            "date": str(bill_date),
                            "bill_number": current_bill_id,
                            "customer_name": st.session_state.last_bill_data["name"],
                            "phone_number": phone_for_db,
                            "platform": channel,
                            "payment_mode": pay_mode,
                            "amount": float(bill_total),
                            "items_summary": str(st.session_state.billing_cart)
                        }).execute()
 
                        # FIX 6: Stock deduction via BOM with fixed query
                        for cart_item in st.session_state.billing_cart:
                            deduct_stock_via_bom(cart_item["dish"], cart_item["qty"])
 
                        st.success(f"✅ Bill {current_bill_id} saved!")
 
                        # FIX 3: Complete cart reset
                        st.session_state.billing_cart = []
                        st.session_state.bill_number_counter += 1
                        st.rerun()
 
                    except Exception as e:
                        st.error(f"DB Error: {str(e)}")
 
        else:
            st.info("Cart is empty. Add dishes to start billing.")
 
        # --- PERSISTENT INVOICE SHARE ---
        if st.session_state.last_bill_data:
            lb = st.session_state.last_bill_data
            st.markdown("---")
            st.info(f"✨ **Invoice Ready: {lb['id']}** | Total: ₹{lb['total']:.2f}")
 
            sh_col1, sh_col2 = st.columns(2)
            with sh_col1:
                if st.button("🖨️ Print / Save PDF", use_container_width=True):
                    html_items = "".join([
                        f"<tr><td>{item['dish']} x {item['qty']}</td><td>₹{item['amount']:.2f}</td></tr>"
                        for item in lb["raw_items"]
                    ])
                    print_html = f"""
                    <div style="font-family:monospace;width:280px;padding:10px;">
                        <h3 style="text-align:center;">LALALA CLOUD KITCHEN</h3>
                        <p>Bill: {lb['id']}<br>Date: {datetime.date.today()}</p>
                        <hr><table>{html_items}</table><hr>
                        <h4>Total: ₹{lb['total']:.2f}</h4>
                    </div>
                    <script>window.print();</script>
                    """
                    st.components.v1.html(print_html, height=0, width=0)
 
            with sh_col2:
                if lb["phone"] and lb["phone"] != "N/A":
                    wa_msg = f"*LALALA KITCHEN*\nBill: {lb['id']}\nTotal: ₹{lb['total']:.2f}\nItems:\n{lb['items']}"
                    wa_url = f"https://wa.me/91{lb['phone']}?text={wa_msg.replace(' ', '%20').replace(chr(10), '%0A')}"
                    st.link_button("💬 Share on WhatsApp", wa_url, use_container_width=True)
                else:
                    st.warning("No phone — WhatsApp not available for walk-in.")
 
            # FIX 3: Full reset on New Bill
            if st.button("🆕 Start New Bill", use_container_width=True, type="secondary"):
                st.session_state.last_bill_data = None
                st.session_state.billing_cart = []
                st.session_state.input_phone_cache = ""
                st.session_state.input_name_cache = ""
                st.rerun()
 
# ==============================================================================
# MODULE 2: ADMIN
# ==============================================================================
elif choice == "Admin Login":
    st.subheader("🔒 Admin Control Panel")
    admin_pwd = st.text_input("Enter Password", type="password")
 
    if admin_pwd == ADMIN_PASSWORD_KEY:
        st.success("Access Granted.")
 
        admin_tab = st.sidebar.radio("Admin Menu",
            ["Inventory Status", "Accounts Entry Panel", "Wastage Entry", "Report Analytics"])
 
        # ==========================================
        # 1. INVENTORY STATUS
        # ==========================================
        if admin_tab == "Inventory Status":
            st.subheader("📦 Live Stock Tracker")
            try:
                sku_data = supabase.table("sku_master").select("*").execute()
                if sku_data.data:
                    df = pd.DataFrame(sku_data.data)
                    st.dataframe(df, use_container_width=True)
                    if st.button("Generate Purchase List"):
                        try:
                            low = df[df["current_stock"].astype(float) < df["Min Stock Level"].astype(float)]
                            if not low.empty:
                                st.warning("⚠️ Items below minimum stock:")
                                st.dataframe(low[["Ingerdient Name", "current_stock", "Purchase unit", "Min Stock Level"]], use_container_width=True)
                            else:
                                st.success("All stock levels within safe limits!")
                        except Exception as e:
                            st.error(f"Error: {e}")
            except Exception as e:
                st.error(f"Inventory load error: {e}")
 
        # ==========================================
        # 2. ACCOUNTS ENTRY PANEL
        # ==========================================
        elif admin_tab == "Accounts Entry Panel":
            st.subheader("💰 Accounts Management")
            acc_type = st.radio("Select Action",
                ["Purchase Entry", "Fixed Expenses", "Pending Credit Dashboard", "Channel Payout Settlements"],
                horizontal=True)
            st.markdown("---")
 
            if acc_type == "Purchase Entry":
                st.markdown("### 🛒 Raw Material Purchase")
                try:
                    p_item_res = supabase.table("sku_master").select("*").execute()
                    item_data = {i["Ingerdient Name"]: i["Purchase unit"] for i in p_item_res.data} if p_item_res.data else {}
                    col1, col2 = st.columns(2)
                    with col1:
                        p_date = st.date_input("Purchase Date", datetime.date.today(), key="p_date")
                        p_item = st.selectbox("Select Item", list(item_data.keys()), key="p_item")
                        s_unit = item_data.get(p_item, "")
                        st.info(f"Unit: **{s_unit}**")
                    with col2:
                        p_qty = st.number_input(f"Qty ({s_unit})", min_value=0.1, key="p_qty")
                        p_amt = st.number_input("Total Amount Spent (₹)", min_value=0.0, key="p_amt")
                    if st.button("Submit Purchase"):
                        curr_res = supabase.table("sku_master").select("current_stock").eq("Ingerdient Name", p_item).execute()
                        curr = float(curr_res.data[0]["current_stock"])
                        supabase.table("sku_master").update({"current_stock": curr + p_qty}).eq("Ingerdient Name", p_item).execute()
                        supabase.table("accounts").insert({
                            "date": str(p_date), "type": "Purchase", "category": "Raw Material",
                            "item_name": p_item, "amount": p_amt, "qty": p_qty, "unit": s_unit
                        }).execute()
                        st.success("✅ Purchase logged and stock updated!")
                except Exception as e:
                    st.error(f"Error: {e}")
 
            elif acc_type == "Fixed Expenses":
                st.markdown("### 💸 Fixed Expense Entry")
                e_date = st.date_input("Expense Date", datetime.date.today(), key="e_date")
                e_cat = st.selectbox("Category", ["Rent", "EB Bill", "Salary", "Gas", "Maintenance", "Other"], key="e_cat")
                e_amt = st.number_input("Amount (₹)", min_value=0.0, key="e_amt")
                if st.button("Save Expense"):
                    supabase.table("accounts").insert({
                        "date": str(e_date), "type": "Fixed Expense", "category": e_cat, "amount": e_amt
                    }).execute()
                    st.success("✅ Expense recorded!")
 
            elif acc_type == "Pending Credit Dashboard":
                st.markdown("### 👥 Credit Monitoring")
                try:
                    credit_res = supabase.table("orders").select("*").eq("payment_mode", "Credit").execute()
                    if credit_res.data:
                        df_credit = pd.DataFrame(credit_res.data)
                        if "platform" in df_credit.columns:
                            df_credit = df_credit[~df_credit["platform"].isin(["Swiggy", "Zomato"])]
                        if not df_credit.empty:
                            df_grp = df_credit.groupby(["customer_name", "phone_number"])["amount"].sum().reset_index()
                            df_grp.columns = ["Client", "Phone", "Total Credit (₹)"]
                            recovery_res = supabase.table("accounts").select("*").eq("category", "Credit Recovery").execute()
                            recovery_dict = {}
                            if recovery_res.data:
                                for rec in recovery_res.data:
                                    ph = rec.get("notes", "").replace("Phone Recovery: ", "").strip()
                                    recovery_dict[ph] = recovery_dict.get(ph, 0.0) + float(rec.get("amount", 0))
                            verified = []
                            for _, row in df_grp.iterrows():
                                ph = str(row["Phone"])
                                billed = float(row["Total Credit (₹)"])
                                recovered = float(recovery_dict.get(ph, 0.0))
                                due = billed - recovered
                                if due > 0:
                                    verified.append({
                                        "Customer": row["Client"], "Phone": ph,
                                        "Total Billed (₹)": billed,
                                        "Recovered (₹)": recovered,
                                        "Net Due (₹)": due
                                    })
                            if verified:
                                df_dues = pd.DataFrame(verified)
                                st.error(f"⚠️ {len(df_dues)} clients pending — Total: ₹{df_dues['Net Due (₹)'].sum():,.2f}")
                                st.dataframe(df_dues, use_container_width=True)
                                st.markdown("#### Log Recovery")
                                rc1, rc2 = st.columns(2)
                                with rc1:
                                    r_date = st.date_input("Recovery Date", datetime.date.today(), key="rec_date")
                                    target = st.selectbox("Select Client", [f"{r['Customer']} ({r['Phone']})" for r in verified], key="rec_client")
                                with rc2:
                                    r_amt = st.number_input("Amount Recovered (₹)", min_value=0.0, step=50.0, key="rec_amt")
                                if st.button("Process Recovery"):
                                    if r_amt > 0:
                                        ext_phone = target.split("(")[-1].replace(")", "").strip()
                                        ext_name = target.split(" (")[0].strip()
                                        supabase.table("accounts").insert({
                                            "date": str(r_date), "type": "Income", "category": "Credit Recovery",
                                            "item_name": f"Recovery from {ext_name}", "qty": 1,
                                            "amount": float(r_amt), "notes": f"Phone Recovery: {ext_phone}"
                                        }).execute()
                                        st.success(f"✅ ₹{r_amt} recovered from {ext_name}.")
                                        st.rerun()
                            else:
                                st.success("🎉 All credit dues cleared!")
                        else:
                            st.info("No direct client credit orders.")
                    else:
                        st.info("No credit orders found.")
                except Exception as e:
                    st.error(f"Error: {e}")
 
            elif acc_type == "Channel Payout Settlements":
                st.markdown("### 💳 Platform Payout Settlement")
                p_cols = st.columns(2)
                for idx, plat in enumerate(["Zomato", "Swiggy"]):
                    try:
                        sq = supabase.table("orders").select("amount").eq("platform", plat).execute()
                        gross = sum(float(r["amount"]) for r in sq.data) if sq.data else 0.0
                        pq = supabase.table("accounts").select("amount").eq("category", f"{plat} Payout").execute()
                        paid = sum(float(r["amount"]) for r in pq.data) if pq.data else 0.0
                        with p_cols[idx]:
                            st.metric(f"{plat} Outstanding", f"₹{gross - paid:,.2f}", delta=f"Total Sales: ₹{gross:,.2f}", delta_color="off")
                    except Exception as e:
                        st.caption(f"{plat} error: {e}")
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    s_platform = st.selectbox("Platform", ["Zomato", "Swiggy"], key="set_plat")
                    start_date = st.date_input("From", datetime.date.today() - datetime.timedelta(days=7), key="set_start")
                    end_date = st.date_input("To", datetime.date.today(), key="set_end")
                with c2:
                    payout_received = st.number_input("Amount Received in Bank (₹)", min_value=0.0, step=100.0, key="set_cash")
                if st.button("Process & Calculate Commission"):
                    try:
                        ores = supabase.table("orders").select("*").execute()
                        gross_sales = 0.0
                        if ores.data:
                            df_o = pd.DataFrame(ores.data)
                            df_o["date"] = pd.to_datetime(df_o["date"]).dt.date
                            filtered = df_o[
                                (df_o["platform"].str.lower() == s_platform.lower()) &
                                (df_o["date"] >= start_date) &
                                (df_o["date"] <= end_date)
                            ]
                            gross_sales = float(filtered["amount"].sum())
                        if gross_sales == 0:
                            gross_sales = payout_received
                        commission = max(0.0, gross_sales - payout_received)
                        supabase.table("accounts").insert({
                            "date": str(datetime.date.today()), "type": "Revenue",
                            "category": f"{s_platform} Payout",
                            "item_name": f"Period: {start_date} to {end_date}",
                            "amount": payout_received, "notes": f"Gross: {gross_sales:.2f}"
                        }).execute()
                        if commission > 0:
                            supabase.table("accounts").insert({
                                "date": str(datetime.date.today()), "type": "Expense",
                                "category": "Platform Commission", "item_name": s_platform,
                                "amount": commission, "notes": f"Period {start_date} to {end_date}"
                            }).execute()
                        st.success(f"Synced! Gross: ₹{gross_sales:,.2f} | Payout: ₹{payout_received:,.2f}")
                        st.metric(f"{s_platform} Commission Deducted", f"₹{commission:,.2f}")
                        chart_data = pd.DataFrame({
                            "Category": ["Bank Payout", "Commission"],
                            "Amount (₹)": [payout_received, commission]
                        })
                        st.bar_chart(data=chart_data, x="Category", y="Amount (₹)")
                    except Exception as e:
                        st.error(f"Error: {e}")
 
        # ==========================================
        # 3. WASTAGE ENTRY
        # ==========================================
        elif admin_tab == "Wastage Entry":
            st.subheader("🗑️ Wastage & Loss Entry")
            w_category = st.radio("Type", ["Raw Material Loss", "Cooked Item Waste", "Complimentary / Promo"], horizontal=True)
 
            try:
                m_res = supabase.table("menu_master").select("*").execute()
                first_row = m_res.data[0] if m_res.data else {}
                actual_col = next((c for c in ["Dish Name", "item_name", "Item Name"] if c in first_row), None)
                dish_list = [m[actual_col] for m in m_res.data if actual_col] if actual_col else []
            except:
                dish_list = []
 
            if w_category == "Raw Material Loss":
                try:
                    w_res = supabase.table("sku_master").select("*").execute()
                    w_data = {
                        i["Ingerdient Name"]: {"unit": i["Purchase unit"], "stock": i["current_stock"]}
                        for i in w_res.data
                    } if w_res.data else {}
                    col1, col2 = st.columns(2)
                    with col1:
                        w_date = st.date_input("Date", datetime.date.today(), key="w_raw_date")
                        w_item = st.selectbox("Select Ingredient", list(w_data.keys()), key="w_raw_item")
                        s_unit = w_data[w_item]["unit"]
                        s_stock = float(w_data[w_item]["stock"])
                        st.warning(f"Live Stock: **{s_stock} {s_unit}**")
                    with col2:
                        w_qty = st.number_input(f"Quantity ({s_unit})", min_value=0.01, key="w_raw_qty")
                        w_reason = st.selectbox("Reason", ["Spoilage", "Expired", "Preparation Error"], key="w_raw_res")
                    if st.button("Record Raw Loss"):
                        if w_qty <= s_stock:
                            new_s = s_stock - float(w_qty)
                            supabase.table("sku_master").update({"current_stock": new_s}).eq("Ingerdient Name", w_item).execute()
                            supabase.table("accounts").insert({
                                "date": str(w_date), "type": "Wastage", "category": "Raw Loss",
                                "item_name": w_item, "qty": w_qty, "amount": 0, "notes": w_reason
                            }).execute()
                            st.success("✅ Stock adjusted successfully!")
                        else:
                            st.error("❌ Wastage quantity exceeds current stock!")
                except Exception as e:
                    st.error(f"Error: {e}")
 
            elif w_category == "Cooked Item Waste":
                # FIX 7: Auto BOM-based stock deduction
                col1, col2 = st.columns(2)
                with col1:
                    w_date = st.date_input("Date", datetime.date.today(), key="w_cook_date")
                    w_dish = st.selectbox("Select Dish", dish_list, key="w_cook_select")
                with col2:
                    w_qty_c = st.number_input("Portions Wasted", min_value=1, key="w_cook_qty")
                    w_loss = st.number_input("Estimated Cost (₹)", min_value=0.0, key="w_cook_val")
                if st.button("Record Cooked Waste"):
                    try:
                        supabase.table("accounts").insert({
                            "date": str(w_date), "type": "Wastage", "category": "Cooked Loss",
                            "item_name": w_dish, "qty": w_qty_c, "amount": w_loss, "notes": "Cooked Waste"
                        }).execute()
                        deduct_stock_via_bom(w_dish, w_qty_c)
                        st.error(f"⚠️ Loss of ₹{w_loss} recorded. Inventory auto-adjusted for {w_dish}.")
                    except Exception as e:
                        st.error(f"Error: {e}")
 
            elif w_category == "Complimentary / Promo":
                # FIX 8: Auto BOM-based stock deduction
                col1, col2 = st.columns(2)
                with col1:
                    c_date = st.date_input("Date", datetime.date.today(), key="c_date")
                    c_item = st.selectbox("Select Dish", dish_list, key="c_name_select")
                with col2:
                    c_qty = st.number_input("Portions Given", min_value=1, key="c_qty")
                    c_cost = st.number_input("Marketing Cost (₹)", min_value=0.0, key="c_val")
                if st.button("Record Promo Entry"):
                    try:
                        supabase.table("accounts").insert({
                            "date": str(c_date), "type": "Expense", "category": "Marketing",
                            "item_name": c_item, "qty": c_qty, "amount": c_cost, "notes": "Promo Offer"
                        }).execute()
                        deduct_stock_via_bom(c_item, c_qty)
                        st.success(f"✅ Promo entry added. Inventory auto-adjusted for {c_item}.")
                    except Exception as e:
                        st.error(f"Error: {e}")
 
        # ==========================================
        # 4. REPORT ANALYTICS
        # ==========================================
        elif admin_tab == "Report Analytics":
            st.subheader("📊 Business Intelligence Dashboard")
 
            st.markdown("### 🔍 Past Bill Search")
            s_col1, s_col2 = st.columns([3, 1])
            with s_col1:
                search_query = st.text_input("Bill Number or Phone Number", placeholder="LALALA-2026- or 10-digit phone", key="search_input")
            with s_col2:
                st.write("##")
                search_trigger = st.button("🔍 Search", use_container_width=True, type="primary")
 
            if search_trigger and search_query:
                try:
                    if search_query.strip().startswith("LALALA"):
                        res = supabase.table("orders").select("*").eq("bill_number", search_query.strip()).execute()
                    else:
                        res = supabase.table("orders").select("*").eq("phone_number", search_query.strip()).execute()
                    if res.data:
                        for bill in res.data:
                            st.markdown("---")
                            st.success(f"Found: **{bill['bill_number']}**")
                            v1, v2 = st.columns(2)
                            with v1:
                                st.write(f"📅 Date: {bill.get('date', 'N/A')}")
                                st.write(f"👤 Customer: {bill.get('customer_name', 'Walking Customer')}")
                                st.write(f"📱 Phone: {bill.get('phone_number', 'N/A')}")
                            with v2:
                                st.write(f"🌐 Channel: {bill.get('platform', 'Counter')}")
                                st.write(f"💳 Payment: {bill.get('payment_mode', 'Cash')}")
                                st.write(f"💰 Amount: ₹{float(bill.get('amount', 0)):,.2f}")
                            st.code(bill.get("items_summary", "[]"))
                    else:
                        st.warning("No records found.")
                except Exception as e:
                    st.error(f"Search error: {e}")
 
            st.markdown("---")
            st.markdown("### 📅 Report Date Range")
            cf, ct = st.columns(2)
            with cf:
                from_date = st.date_input("From", datetime.date.today().replace(day=1), key="from_date")
            with ct:
                to_date = st.date_input("To", datetime.date.today(), key="to_date")
 
            try:
                res_orders = supabase.table("orders").select("*").gte("date", str(from_date)).lte("date", str(to_date)).execute()
                orders_data = res_orders.data or []
            except:
                orders_data = []
 
            try:
                res_acc = supabase.table("accounts").select("*").gte("date", str(from_date)).lte("date", str(to_date)).execute()
                accounts_data = res_acc.data or []
            except:
                accounts_data = []
 
            df_orders = pd.DataFrame(orders_data)
            df_accounts = pd.DataFrame(accounts_data)
 
            try:
                sku_res = supabase.table("sku_master").select("*").execute()
                if sku_res.data:
                    low_items = [r for r in sku_res.data if float(r.get("current_stock", 0)) < float(r.get("Min Stock Level", 5))]
                    if low_items:
                        st.error(f"⚠️ {len(low_items)} ingredients below minimum stock!")
                        with st.expander("View Low Stock Items"):
                            for item in low_items:
                                st.write(f"• **{item.get('Ingerdient Name')}**: {item.get('current_stock')} (Min: {item.get('Min Stock Level')})")
            except:
                pass
 
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "📅 Working Days", "🍲 Dish Performance", "👥 CRM",
                "📱 Platforms", "🗑️ Wastage", "💸 Expenses", "🛑 Dead Stock"
            ])
 
            with tab1:
                st.markdown("### Working Days Summary")
                if not df_orders.empty:
                    st.metric("Active Days", df_orders["date"].nunique())
                    day_sum = df_orders.groupby("date").agg(
                        Bills=("bill_number", "count"), Revenue=("amount", "sum")
                    ).reset_index().sort_values("date", ascending=False)
                    st.dataframe(day_sum, use_container_width=True)
                else:
                    st.info("No data in selected range.")
 
            with tab2:
                st.markdown("### Dish Performance")
                if not df_orders.empty and "items_summary" in df_orders.columns:
                    import ast
                    all_items = []
                    for _, row in df_orders.iterrows():
                        try:
                            items = ast.literal_eval(row["items_summary"])
                            for item in items:
                                all_items.append({
                                    "Dish": item.get("dish"),
                                    "Qty": int(item.get("qty", 0)),
                                    "Revenue (₹)": float(item.get("amount", 0))
                                })
                        except:
                            pass
                    if all_items:
                        df_d = pd.DataFrame(all_items).groupby("Dish").sum().reset_index().sort_values("Qty", ascending=False)
                        st.dataframe(df_d, use_container_width=True)
                        st.bar_chart(df_d, x="Dish", y="Qty")
                else:
                    st.info("No dish data available.")
 
            with tab3:
                st.markdown("### Customer Retention (CRM)")
                if not df_orders.empty and "phone_number" in df_orders.columns:
                    df_crm = df_orders.copy()
                    df_crm["phone_number"] = df_crm["phone_number"].fillna("N/A")
                    df_c = df_crm.groupby(["customer_name", "phone_number"]).agg(
                        Orders=("bill_number", "count"), Spent=("amount", "sum")
                    ).reset_index().sort_values("Orders", ascending=False)
                    st.dataframe(df_c, use_container_width=True)
                else:
                    st.info("No CRM data.")
 
            with tab4:
                st.markdown("### Platform Sales")
                if not df_orders.empty and "platform" in df_orders.columns:
                    df_p = df_orders.groupby("platform")["amount"].agg(["count", "sum"]).reset_index()
                    df_p.columns = ["Platform", "Orders", "Revenue (₹)"]
                    st.dataframe(df_p, use_container_width=True)
                    st.bar_chart(df_p, x="Platform", y="Revenue (₹)")
                else:
                    st.info("No platform data.")
 
            with tab5:
                st.markdown("### Wastage Analysis")
                if not df_accounts.empty:
                    df_w = df_accounts[df_accounts["type"].str.contains("Wastage", case=False, na=False)]
                    if not df_w.empty:
                        st.dataframe(df_w[["date", "category", "item_name", "qty", "amount", "notes"]], use_container_width=True)
                        st.metric("Total Loss", f"₹{df_w['amount'].sum():,.2f}")
                    else:
                        st.success("Zero wastage recorded!")
                else:
                    st.info("No data.")
 
            with tab6:
                st.markdown("### Expenses Breakdown")
                if not df_accounts.empty:
                    df_e = df_accounts[df_accounts["type"].str.contains("Expense|Fixed", case=False, na=False)]
                    if not df_e.empty:
                        df_es = df_e.groupby("category")["amount"].sum().reset_index()
                        df_es.columns = ["Category", "Amount (₹)"]
                        st.dataframe(df_es, use_container_width=True)
                        st.metric("Total Expenses", f"₹{df_e['amount'].sum():,.2f}")
                        st.bar_chart(df_es, x="Category", y="Amount (₹)")
                    else:
                        st.info("No expenses recorded.")
                else:
                    st.info("No data.")
 
            with tab7:
                st.markdown("### Dead Stock Audit")
                try:
                    bom_res = supabase.table("bom_master").select("item_name").execute()
                    active_ingredients = set(r["item_name"].strip().upper() for r in bom_res.data) if bom_res.data else set()
                    sku_res = supabase.table("sku_master").select("*").execute()
                    if sku_res.data:
                        dead = [r for r in sku_res.data if r.get("Ingerdient Name", "").strip().upper() not in active_ingredients]
                        if dead:
                            st.warning(f"⚠️ {len(dead)} ingredients not linked to any recipe!")
                            st.dataframe(pd.DataFrame(dead)[["Ingerdient Name", "current_stock", "Purchase unit"]], use_container_width=True)
                        else:
                            st.success("✅ All ingredients linked to recipes!")
                except Exception as e:
                    st.error(f"Error: {e}")
 
    elif admin_pwd != "":
        st.error("❌ Incorrect Password.")
