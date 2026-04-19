import streamlit as st
from supabase import create_client

# Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Lalala Kitchen", layout="wide")
st.title("👨‍🍳 Lalala Cloud Kitchen")

# Sidebar for Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Inventory", "Billing"])

if page == "Dashboard":
    st.subheader("Welcome Gaju! Dashboard is coming soon...")
    
elif page == "Inventory":
    st.subheader("Live SKU Stock")
    res = supabase.table("sku_master").select("*").execute()
    st.dataframe(res.data)
