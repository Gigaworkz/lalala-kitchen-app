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
menu = ["Billing", "Admin Login"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Billing":
    st.subheader("🧾 New Bill")
    
    try:
        # Quote panni space use pannuvom (Correct column name: "Dish Name")
        res_menu = supabase.table("menu_master").select('\"Dish Name\"').execute()
        if hasattr(res_menu, 'data'):
            menu_list = [item['Dish Name'] for item in res_menu.data]
        else:
            menu_list = []
    except Exception as e:
        st.error(f"Database Error: {str(e)}")
        menu_list = []

    if menu_list:
        col1, col2, col3 = st.columns(3)
        with col1:
            bill_date = st.date_input("Date", datetime.date.today())
        with col2:
            channel = st.selectbox("Channel", ["Direct Takeaway", "Swiggy", "Zomato", "Party Order"])
        with col3:
            default_pay = "Credit" if channel in ["Swiggy", "Zomato"] else "Cash"
            pay_mode = st.selectbox("Payment", ["Cash", "UPI", "Card", "Credit"], index=["Cash", "UPI", "Card", "Credit"].index(default_pay))

        selected_dish = st.selectbox("Select Dish", menu_list)
        qty = st.number_input("Quantity", min_value=1, value=1)
        
        if st.button("🚀 Confirm Order"):
            with st.spinner("Syncing Inventory..."):
                # Column names match unga Supabase: "Dish Name" and "Ingerdient Name"
                bom_res = supabase.table("bom_master").select('*').eq('\"Dish Name\"', selected_dish).execute()
                
                if bom_res.data:
                    for ing in bom_res.data:
                        ing_name = ing['Ingerdient Name']
                        req_qty = float(ing['Required quantity']) * qty
                        
                        try:
                            sku_res = supabase.table("sku_master").select("current_stock").eq('\"Ingerdient Name\"', ing_name).execute()
                            if sku_res.data:
                                current = float(sku_res.data[0].get('current_stock', 0))
                                supabase.table("sku_master").update({"current_stock": current - req_qty}).eq('\"Ingerdient Name\"', ing_name).execute()
                        except Exception as inner_e:
                            st.warning(f"Stock update failed for {ing_name}")
                    
                    st.success(f"Billed: {qty} x {selected_dish}")
                    st.balloons()
                else:
                    st.warning("BOM mapping not found.")
