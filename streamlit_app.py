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
st.markdown('<p style="text-align: center; color: #388E3C; font-size: 20px;">Sig-nature taste | Pure VEG 🥦</p>', unsafe_allow_html=True)

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
    
    # Password logic in a clean way
    admin_pwd = st.text_input("Enter Password", type="password")
    
    if admin_pwd == "140226":
        st.success("Access Granted.")
        admin_tab = st.sidebar.radio("Admin Menu", ["Inventory Status", "Purchase Entry", "Expenses", "Settlements", "CRM Report"])
        
        if admin_tab == "Inventory Status":
            st.subheader("📦 Live Stock Tracker")
            sku_data = supabase.table("sku_master").select("*").execute()
            if sku_data.data:
                df = pd.DataFrame(sku_data.data)
                st.dataframe(df)
                if st.button("Low Stock Alert"):
                    # Min Stock Level check
                    low = df[df['current_stock'].astype(float) < df['Min Stock Level'].astype(float)]
                    st.warning("Immediate Purchase Needed:")
                    st.write(low[['Ingerdient Name', 'current_stock', 'Purchase unit']])
        
        elif admin_tab == "Purchase Entry":
            st.subheader("🛒 Update Stock")
            p_item = st.selectbox("Select Item", [i['Ingerdient Name'] for i in supabase.table("sku_master").select('\"Ingerdient Name\"').execute().data])
            p_qty = st.number_input("Added Qty", min_value=0.1)
            if st.button("Add to Inventory"):
                curr = float(supabase.table("sku_master").select("current_stock").eq('\"Ingerdient Name\"', p_item).execute().data[0]['current_stock'])
                supabase.table("sku_master").update({"current_stock": curr + p_qty}).eq('\"Ingerdient Name\"', p_item).execute()
                st.success("Stock Updated!")

    elif admin_pwd != "":
        st.error("Incorrect Password.")
