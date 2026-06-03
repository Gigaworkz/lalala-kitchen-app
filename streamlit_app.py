import streamlit as st
import datetime
import pandas as pd

# --- CUSTOM CSS: COLOR PALETTE ---
st.markdown("""
<style>
    /* Button Colors */
    div.stButton > button[key="btn_add_cart"] { background-color: #FFB74D !important; color: black !important; }
    div.stButton > button[key="btn_gen_bill"] { background-color: #E1BEE7 !important; color: black !important; }
    div.stButton > button[key="btn_print"] { background-color: #81D4FA !important; color: black !important; }
    div.stButton > button[key="btn_whatsapp"] { background-color: #A5D6A7 !important; color: black !important; }
    div.stButton > button[key="btn_clear"] { background-color: #FFF59D !important; color: black !important; }
</style>
""", unsafe_allow_html=True)

# Session States
if "billing_cart" not in st.session_state: st.session_state.billing_cart = []
if "show_bill" not in st.session_state: st.session_state.show_bill = False

# --- HEADER SECTION ---
col_logo, col_text = st.columns([1, 4])
with col_logo:
    st.image("logo.png", width=120) # Path to your logo
with col_text:
    st.markdown("<h2 style='margin:0; color:#F5F5F5;'>LALALA</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin:0; color:#E0E0E0;'>Cloud Kitchen</h3>", unsafe_allow_html=True)
    st.markdown("<p style='margin:0; color:#BDBDBD; font-style:italic;'>Good Food | Sig-Nature Feel</p>", unsafe_allow_html=True)
    st.markdown("<p style='margin:0; color:#81C784; font-weight:bold;'>Pure Veg 🥦</p>", unsafe_allow_html=True)

st.divider()

# --- BILLING UI ---
col_1, col_2 = st.columns([1, 1])
with col_1:
    st.subheader("Billing Section")
    # Date logic: Default current date
    bill_date = st.date_input("Billing Date", datetime.date.today())
    
    # Adding items
    dish = st.selectbox("Select Dish", ["Veg Biryani", "Paneer Tikka", "Gobi 65"])
    if st.button("Add to Cart", key="btn_add_cart"):
        st.session_state.billing_cart.append({"dish": dish, "qty": 1, "price": 100})
        st.session_state.show_bill = False
        st.rerun()

with col_2:
    st.subheader("Order Summary")
    if st.session_state.billing_cart:
        df = pd.DataFrame(st.session_state.billing_cart)
        st.table(df)
        
        # Lavender Generate Bill Button (Placed above Total)
        if st.button("Generate Bill", key="btn_gen_bill"):
            st.session_state.show_bill = True
            
        if st.session_state.show_bill:
            total = df['price'].sum()
            st.markdown(f"### Total: ₹{total}")
            
            # Action Buttons
            c1, c2, c3 = st.columns(3)
            with c1: st.button("Print", key="btn_print")
            with c2: st.button("WhatsApp", key="btn_whatsapp")
            with c3: st.button("Clear", key="btn_clear")
