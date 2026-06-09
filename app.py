import streamlit as st

st.set_page_config(page_title="FIPE Tracker", page_icon="📉", layout="wide")

pg = st.navigation([
    st.Page("pages/home.py",      title="Home",      icon="📉"),
    st.Page("pages/detalhes.py", title="Registrar", icon="💾"),
    st.Page("pages/comparar.py",  title="Comparar",  icon="⚖️"),
])
pg.run()