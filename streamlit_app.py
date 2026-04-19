import streamlit as st
from supabase import create_client

# Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Sig-nature Kitchen", layout="wide")
st.title("🥦 Sig-nature Pure Veg Kitchen")

# Sidebar
page = st.sidebar.radio("Go to", ["Dashboard", "Inventory", "Billing"])

if page == "Inventory":
    st.subheader("📦 Stock Status (SKU Master)")
    res = supabase.table("sku_master").select("*").execute()
    st.dataframe(res.data)

elif page == "Billing":
    st.subheader("🧾 New Billing")
    
    # Pure Veg Menu - Intha list-ai unga actual menu-kku mathikalam
    menu_items = ["Veg Biryani", "Paneer Butter Masala", "Mushroom Fry", "Gobi 65", "Dal Tadka"]
    
    col1, col2 = st.columns(2)
    with col1:
        selected_dish = st.selectbox("Select Dish", menu_items)
    with col2:
        qty = st.number_input("Quantity", min_value=1, value=1)
    
    if st.button("Generate Bill & Deduct Stock"):
        st.success(f"Bill Generated: {qty} x {selected_dish}")
        st.warning("Next: Intha dish-oda Recipe (BOM) padi, Supabase-la stock-ai auto-reduce panna porom.")

elif page == "Dashboard":
    st.subheader("📈 Today's Summary")
    st.metric("Total Sales", "₹0", delta="0%")
    st.write("Live data reporting coming soon.")
