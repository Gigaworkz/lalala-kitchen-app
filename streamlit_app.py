import streamlit as st
from supabase import create_client
import datetime
import pandas as pd

# --- CONNECTION ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Sig-nature Kitchen", layout="wide")

st.markdown('<h1 style="text-align: center; color: #1B5E20;">👨‍🍳 LALALA CLOUD KITCHEN</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #388E3C; font-size: 20px;">Sig-nature taste | Pure VEG 🥦</p>', unsafe_allow_html=True)

# --- NAVIGATION ---
st.sidebar.title("Main Menu")
choice = st.sidebar.radio("Go to", ["Billing", "Admin Login"])

# --- MODULE 1: BILLING ---
if choice == "Billing":
    st.subheader("🧾 New Bill")
    try:
        res_menu = supabase.table("menu_master").select('\"Dish Name\"').execute()
        menu_list = [item['Dish Name'] for item in res_menu.data] if res_menu.data else []
    except:
        menu_list = []

    if menu_list:
        selected_dish = st.selectbox("Select Dish", menu_list)
        qty = st.number_input("Quantity", min_value=1, value=1)
        if st.button("🚀 Confirm Order"):
            st.success("Billed!")
    else:
        st.warning("Menu items load aagala. Supabase connect check pannunga.")

# --- MODULE 2: ADMIN LOGIN (Fixed) ---
elif choice == "Admin Login":
    st.subheader("🔒 Admin Authentication")
    
    # Inga password box theriyaanum
    pwd = st.text_input("Enter Admin Password", type="password", placeholder="Type here...")
    
    if pwd == "140226":
        st.success("Login Successful! Welcome Gaju.")
        
        # Admin Sub-Menu
        admin_opt = st.radio("Select Action", ["View Inventory", "Purchase Entry", "Sales Report"])
        
        if admin_opt == "View Inventory":
            sku_res = supabase.table("sku_master").select("*").execute()
            if sku_res.data:
                st.dataframe(pd.DataFrame(sku_res.data))
        
        elif admin_opt == "Purchase Entry":
            st.write("New stock entry option coming here.")
            
    elif pwd != "":
        st.error("Wrong Password! Try again.")
    else:
        st.info("Please enter the password to access Admin features.")
