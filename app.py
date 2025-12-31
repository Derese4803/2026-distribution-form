import streamlit as st
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from sqlalchemy import text
import os

# --- 1. IMPORT LOCAL MODULES ---
# Ensure BackCheck is imported from your models
from database import SessionLocal, engine
from models import Farmer, Woreda, Kebele, BackCheck, Base

# --- 2. CONFIGURATION ---
st.set_page_config(
    page_title="Amhara 2026 Distribution & Back Check", 
    layout="wide", 
    page_icon="🌳"
)

def create_tables():
    Base.metadata.create_all(bind=engine)

create_tables()

# --- 3. GOOGLE DRIVE UPLOAD ---
def upload_to_drive(file, farmer_name):
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json(creds_info, ['https://www.googleapis.com/auth/drive'])
        service = build('drive', 'v3', credentials=creds)
        
        file_name = f"{farmer_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.mp3"
        media = MediaIoBaseUpload(file, mimetype='audio/mpeg', resumable=True)
        
        g_file = service.files().create(
            body={'name': file_name}, 
            media_body=media, 
            fields='id'
        ).execute()
        
        fid = g_file.get('id')
        service.permissions().create(fileId=fid, body={'type': 'anyone', 'role': 'viewer'}).execute()
        return f"https://drive.google.com/uc?id={fid}"
    except Exception as e:
        st.error(f"Cloud Storage Error: {e}")
        return None

# --- 4. NAVIGATION ---
if "page" not in st.session_state:
    st.session_state["page"] = "Home"

def nav(p):
    st.session_state["page"] = p
    st.rerun()

# --- 5. MAIN UI ---
def main():
    st.sidebar.title("🌳 Amhara 2026")
    st.sidebar.info("Nursery & Distribution Management")
    
    page = st.session_state["page"]

    # --- PAGE: HOME ---
    if page == "Home":
        st.title("🚜 Amhara 2026 Management System")
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📝 NEW DISTRIBUTION REGISTRATION", use_container_width=True, type="primary"): nav("Reg")
            if st.button("📍 MANAGE LOCATIONS", use_container_width=True): nav("Loc")
        with c2:
            if st.button("🔍 NURSERY BACK CHECK", use_container_width=True, type="secondary"): nav("BackCheck")
            if st.button("📊 VIEW ALL DATA", use_container_width=True): nav("Data")

    # --- PAGE: REGISTRATION ---
    elif page == "Reg":
        if st.button("⬅️ Back"): nav("Home")
        st.header("New Farmer Registration")
        db = SessionLocal()
        woredas = db.query(Woreda).all()
        
        with st.form("reg_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Farmer Full Name")
                phone = st.text_input("Phone Number")
                officer = st.text_input("Distribution Officer Name (TNO)")
            with col2:
                w_list = [w.name for w in woredas] if woredas else ["Add Woredas First"]
                sel_woreda = st.selectbox("Woreda", w_list)
                
                kebeles = []
                if woredas and sel_woreda != "Add Woredas First":
                    w_obj = db.query(Woreda).filter(Woreda.name == sel_woreda).first()
                    kebeles = [k.name for k in w_obj.kebeles]
                sel_kebele = st.selectbox("Kebele", kebeles if kebeles else ["No Kebeles Found"])
            
            st.markdown("---")
            st.subheader("🌲 Seedlings Distributed")
            t1, t2, t3 = st.columns(3)
            with t1:
                gesho = st.number_input("Gesho", 0)
                wanza = st.number_input("Wanza", 0)
                lemon = st.number_input("Lemon", 0)
            with t2:
                giravila = st.number_input("Giravila", 0)
                papaya = st.number_input("Papaya", 0)
                arzelibanos = st.number_input("Arzelibanos", 0)
            with t3:
                diceres = st.number_input("Diceres", 0)
                moringa = st.number_input("Moringa", 0)
                guava = st.number_input("Guava", 0)

            audio = st.file_uploader("🎤 Audio Confirmation", type=['mp3', 'wav', 'm4a'])
            
            if st.form_submit_button("Submit Distribution Record"):
                if not name or not officer:
                    st.error("Please fill in Name and Officer!")
                else:
                    with st.spinner("Saving..."):
                        url = upload_to_drive(audio, name) if audio else None
                        new_f = Farmer(
                            name=name, phone=phone, woreda=sel_woreda, 
                            kebele=sel_kebele, officer_name=officer,
                            audio_url=url, gesho=gesho, giravila=giravila, 
                            diceres=diceres, wanza=wanza, papaya=papaya, 
                            moringa=moringa, lemon=lemon, 
                            arzelibanos=arzelibanos, guava=guava
                        )
                        db.add(new_f)
                        db.commit()
                        st.success(f"✅ Record for {name} saved!")
        db.close()

    # --- PAGE: BACK CHECK ---
    elif page == "BackCheck":
        if st.button("⬅️ Back"): nav("Home")
        st.header("🔍 Nursery Back Check Form")
        st.info("Verify nursery bed dimensions and counts.")

        with st.form("back_check_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            checker = c1.text_input("Back Checker Name")
            fenced = c2.selectbox("Does the Nursery have Fenced?", ["Yes", "No"])

            def bed_row(species, expected):
                st.markdown(f"#### {species} (Expected Width: {expected} sockets)")
                col1, col2, col3 = st.columns(3)
                b_num = col1.number_input(f"{species} beds number", min_value=0, key=f"{species}_n")
                b_len = col2.number_input(f"Length of {species} beds (m)", min_value=0.0, step=0.1, key=f"{species}_l")
                b_sock = col3.number_input(f"Number of sockets in width", min_value=0, key=f"{species}_s", help=f"We expect {expected}")
                return b_num, b_len, b_sock

            g_num, g_len, g_sock = bed_row("Guava", 13)
            l_num, l_len, l_sock = bed_row("Lemon", 13)
            ge_num, ge_len, ge_sock = bed_row("Gesho", 16)
            gr_num, gr_len, gr_sock = bed_row("Grevillea", 16)

            if st.form_submit_button("Submit Back Check"):
                if not checker:
                    st.error("Checker name is required!")
                else:
                    db = SessionLocal()
                    new_bc = BackCheck(
                        checker_name=checker, fenced=fenced,
                        guava_beds=g_num, guava_length=g_len, guava_sockets=g_sock,
                        lemon_beds=l_num, lemon_length=l_len, lemon_sockets=l_sock,
                        gesho_beds=ge_num, gesho_length=ge_len, gesho_sockets=ge_sock,
                        grevillea_beds=gr_num, grevillea_length=gr_len, grevillea_sockets=gr_sock
                    )
                    db.add(new_bc)
                    db.commit()
                    db.close()
                    st.success("✅ Back Check record saved successfully!")

    # --- PAGE: DATA VIEW ---
    elif page == "Data":
        if st.button("⬅️ Back"): nav("Home")
        db = SessionLocal()
        
        tab1, tab2 = st.tabs(["Farmer Distribution", "Nursery Back Checks"])
        
        with tab1:
            farmers = db.query(Farmer).all()
            if farmers:
                df1 = pd.DataFrame([f.__dict__ for f in farmers]).drop('_sa_instance_state', axis=1, errors='ignore')
                st.dataframe(df1)
            else: st.info("No distribution data.")

        with tab2:
            checks = db.query(BackCheck).all()
            if checks:
                df2 = pd.DataFrame([c.__dict__ for c in checks]).drop('_sa_instance_state', axis=1, errors='ignore')
                st.dataframe(df2)
            else: st.info("No back check data.")
        db.close()

    # --- PAGE: LOCATIONS ---
    elif page == "Loc":
        if st.button("⬅️ Back"): nav("Home")
        db = SessionLocal()
        st.header("📍 Manage Areas")
        nw = st.text_input("Add Woreda Name")
        if st.button("Add Woreda"):
            if nw: db.add(Woreda(name=nw)); db.commit(); st.rerun()

        for w in db.query(Woreda).all():
            with st.expander(f"📌 {w.name}"):
                nk = st.text_input(f"Add Kebele to {w.name}", key=f"k_{w.id}")
                if st.button("Add Kebele", key=f"b_{w.id}"):
                    if nk: db.add(Kebele(name=nk, woreda_id=w.id)); db.commit(); st.rerun()
        db.close()

if __name__ == "__main__":
    main()
