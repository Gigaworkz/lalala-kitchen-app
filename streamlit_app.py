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
st.markdown("""
    <style>
    .main-title { font-size: 34px; font-weight: bold; color: #1B5E20; text-align: center; }
    .tagline { font-size: 18px; color: #388E3C; text-align: center; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">👨‍🍳 LALALA CLOUD KITCHEN</div>', unsafe_allow_html=True)
st.markdown('<div class="tagline">Sig-nature taste | Pure VEG 🥦</div>', unsafe_allow_html=True)

# --- NAVIGATION ---
menu = ["Billing", "Admin Login"]
choice = st.sidebar.selectbox("Navigation", menu)

# --- MODULE 1: BILLING (PUBLIC) ---
if choice == "Billing":
    st.subheader("🧾 New Bill")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        bill_date = st.date_input("Date", datetime.date.today())
    with col2:
        channel = st.selectbox("Channel", ["Direct Takeaway", "Swiggy", "Zomato", "Party Order"])
    with col3:
        # Auto-Credit for Online Orders
        default_pay = "Credit" if channel in ["Swiggy", "Zomato"] else "Cash"
        pay_mode = st.selectbox("Payment", ["Cash", "UPI", "Card", "Credit"], index=["Cash", "UPI", "Card", "Credit"].index(default_pay))

    # Fetch Menu from menu_master
    res_menu = supabase.table("menu_master").select("Dish Name").execute()
    menu_list = [item['Dish Name'] for item in res_menu.data] if res_menu.data else []
    
    selected_dish = st.selectbox("Select Dish", menu_list)
    qty = st.number_input("Quantity", min_value=1, value=1)
    
    # Dynamic Commission
    comm_pct = 33.77 if channel == "Swiggy" else (34.90 if channel == "Zomato" else 0.0)
    final_comm = st.number_input("Commission %", value=comm_pct)

    if st.button("🚀 Confirm Order & Update Stock"):
        with st.spinner("Processing..."):
            # 1. Get Recipe from BOM
            bom_res = supabase.table("bom_master").select("*").eq("Dish Name", selected_dish).execute()
            
            if bom_res.data:
                for ing in bom_res.data:
                    ing_name = ing['Ingerdient Name']
                    req_qty = float(ing['Required quantity']) * qty
                    
                    # 2. Update SKU Stock
                    sku_res = supabase.table("sku_master").select("current_stock").eq("Ingerdient Name", ing_name).execute()
                    if sku_res.data:
                        current = float(sku_res.data[0].get('current_stock', 0))
                        # Deduction Logic
                        supabase.table("sku_master").update({"current_stock": current - req_qty}).eq("Ingerdient Name", ing_name).execute()
                
                st.success(f"Order Placed: {qty} x {selected_dish}. Stock Synced!")
                st.balloons()
            else:
                st.error("BOM Mapping not found for this dish.")

# --- MODULE 2: ADMIN (PRIVATE) ---
elif choice == "Admin Login":
    pwd = st.text_input("Admin Password", type="password")
    if pwd == "140226":
        admin_page = st.sidebar.radio("Menu", ["Inventory", "Purchase & Expenses", "CRM", "Settlement"])
        
        if admin_page == "Inventory":
            st.subheader("📦 Live Stock Status")
            sku_data = supabase.table("sku_master").select("*").execute()
            df = pd.DataFrame(sku_data.data)
            st.dataframe(df)
            
            if st.button("Generate Purchase List"):
                # Alert if stock is below Min Stock Level
                low_stock = df[df['current_stock'].astype(float) < df['Min Stock Level'].astype(float)]
                st.warning("Low Stock Items:")
                st.write(low_stock[['Ingerdient Name', 'current_stock', 'Purchase unit']])

        elif admin_page == "Purchase & Expenses":
            st.subheader("🛒 Add Purchase / Expense")
            tab1, tab2 = st.tabs(["Purchase", "Fixed Expense"])
            with tab1:
                p_item = st.selectbox("Select Item", [i['Ingerdient Name'] for i in supabase.table("sku_master").select("Ingerdient Name").execute().data])
                p_qty = st.number_input("Added Quantity", min_value=0.1)
                if st.button("Add to Stock"):
                    curr = float(supabase.table("sku_master").select("current_stock").eq("Ingerdient Name", p_item).execute().data[0]['current_stock'])
                    supabase.table("sku_master").update({"current_stock": curr + p_qty}).eq("Ingerdient Name", p_item).execute()
                    st.success("Stock updated successfully!")
            with tab2:
                st.date_input("Expense Date")
                st.selectbox("Type", ["Rent", "Electricity", "Salary", "Other"])
                st.number_input("Amount")
                st.button("Record Expense")
    
    elif pwd != "":
        st.error("Wrong Password!")
