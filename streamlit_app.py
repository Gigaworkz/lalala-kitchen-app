import streamlit as st
from supabase import create_client

# Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Sig-nature Kitchen", layout="wide")
st.title("👨‍🍳 Sig-nature Cloud Kitchen")

# Sidebar
page = st.sidebar.radio("Go to", ["Dashboard", "Inventory", "Billing"])

if page == "Inventory":
    st.subheader("📦 Current Stock (SKU Master)")
    res = supabase.table("sku_master").select("*").execute()
    st.dataframe(res.data)

elif page == "Billing":
    st.subheader("🧾 New Bill")
    # Menu items example (Ithai namma pinnaadi Supabase kooda inaikkalam)
    menu_item = st.selectbox("Select Dish", ["Chicken Rice", "Onion Pakoda", "Egg Fried Rice"])
    qty = st.number_input("Quantity", min_value=1, value=1)
    
    if st.button("Generate Bill"):
        st.success(f"Bill Generated for {qty} {menu_item}!")
        st.info("Next Step: Intha order-ku thevayana ingredients-ai stock-la irundhu namma auto-deduct panna porom.")

elif page == "Dashboard":
    st.subheader("📈 Business Overview")
    st.write("Today's Total Sales: ₹0 (Coming Soon)")
