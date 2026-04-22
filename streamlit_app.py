import streamlit as st
from supabase import create_client
import datetime
import pandas as pd

# --- CONNECTION ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Sig-Nature Kitchen", layout="wide")

# --- UI HEADER ---
st.markdown('<h1 style="text-align: center; color: #1B5E20;">👨‍🍳 LALALA CLOUD KITCHEN</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #388E3C; font-size: 20px;">Good Food, Sig-Nature Feel | Pure VEG 🥦</p>', unsafe_allow_html=True)

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
        # Inga namma puthu tabs-ai insert panniduvom
        admin_tab = st.sidebar.radio("Admin Menu", ["Inventory Status", "Purchase Entry (Accounts)", "Fixed Expenses", "Wastage Entry"])
        
        # --- 1. PURCHASE ENTRY (Inventory + Accounts Impact) ---
        if admin_tab == "Purchase Entry (Accounts)":
            st.subheader("🛒 Raw Material Purchase")
            col1, col2 = st.columns(2)
            with col1:
                p_date = st.date_input("Purchase Date", datetime.date.today())
                # Table fetch with space-safe column name
                p_item_res = supabase.table("sku_master").select('\"Ingerdient Name\"').execute()
                p_item = st.selectbox("Select Item", [i['Ingerdient Name'] for i in p_item_res.data])
            with col2:
                p_qty = st.number_input("Quantity Added", min_value=0.1)
                p_amt = st.number_input("Total Amount Spent", min_value=0.0)
            
            if st.button("Submit Purchase"):
                # A. Update Stock (PLUS)
                curr_res = supabase.table("sku_master").select("current_stock").eq('\"Ingerdient Name\"', p_item).execute()
                curr = float(curr_res.data[0]['current_stock'])
                supabase.table("sku_master").update({"current_stock": curr + p_qty}).eq('\"Ingerdient Name\"', p_item).execute()
                
                # B. Add to Accounts
                supabase.table("accounts").insert({
                    "date": str(p_date), "type": "Purchase", "category": "Raw Material",
                    "item_name": p_item, "amount": p_amt, "qty": p_qty
                }).execute()
                st.success(f"{p_item} Stock Updated & Expense Recorded!")

        # --- 2. FIXED EXPENSES (Accounts Impact Only) ---
        elif admin_tab == "Fixed Expenses":
            st.subheader("💸 Fixed Expense Entry")
            e_date = st.date_input("Expense Date", datetime.date.today())
            e_cat = st.selectbox("Category", ["Rent", "EB Bill", "Salary", "Gas", "Maintenance", "Other"])
            e_amt = st.number_input("Amount", min_value=0.0)
            e_note = st.text_area("Notes")
            
            if st.button("Save Expense"):
                supabase.table("accounts").insert({
                    "date": str(e_date), "type": "Fixed Expense", "category": e_cat,
                    "amount": e_amt, "notes": e_note
                }).execute()
                st.success("Expense added to Accounts!")

        # --- 3. WASTAGE ENTRY (Inventory Impact Only) ---
        elif admin_tab == "Wastage Entry":
            st.subheader("🗑️ Daily Wastage Record")
            w_date = st.date_input("Wastage Date", datetime.date.today())
            # Fetch for selection
            w_item_res = supabase.table("sku_master").select('\"Ingerdient Name\"').execute()
            w_item = st.selectbox("Item Wasted", [i['Ingerdient Name'] for i in w_item_res.data])
            w_qty = st.number_input("Wasted Quantity", min_value=0.1)
            
            if st.button("Record Wastage"):
                # A. Update Stock (MINUS)
                curr_res = supabase.table("sku_master").select("current_stock").eq('\"Ingerdient Name\"', w_item).execute()
                curr = float(curr_res.data[0]['current_stock'])
                supabase.table("sku_master").update({"current_stock": curr - w_qty}).eq('\"Ingerdient Name\"', w_item).execute()
                
                # B. Add to Accounts (Type: Wastage, Amount: 0)
                supabase.table("accounts").insert({
                    "date": str(w_date), "type": "Wastage", "category": "Loss",
                    "item_name": w_item, "qty": w_qty, "amount": 0
                }).execute()
                st.error(f"Stock reduced due to Wastage: {w_item}")
        
        # --- 4. INVENTORY STATUS (View Only) ---
        elif admin_tab == "Inventory Status":
            st.subheader("📦 Live Stock Tracker")
            sku_data = supabase.table("sku_master").select("*").execute()
            if sku_data.data:
                df = pd.DataFrame(sku_data.data)
                st.dataframe(df)
                if st.button("Generate Purchase List"):
                    low = df[df['current_stock'].astype(float) < df['Min Stock Level'].astype(float)]
                    st.warning("Immediate Purchase Needed:")
                    st.write(low[['Ingerdient Name', 'current_stock', 'Purchase unit']])

    elif admin_pwd != "":
        st.error("Incorrect Password.")
