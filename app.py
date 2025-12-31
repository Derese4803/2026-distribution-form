import streamlit as st
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from sqlalchemy import text
import os

from database import SessionLocal, engine
from models import Farmer, Woreda, Kebele, BackCheck, Base

# --- CONFIGURATION ---
st.set_page_config(page_title="Amhara 2026 Register", layout="wide", page_icon="🌳")

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()

# --- GOOGLE DRIVE UPLOAD ---
def upload_to_drive(file, farmer_name):
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json(creds_info, ['https://www.googleapis.com/auth/drive'])
        service = build('drive', 'v3', credentials=creds)
        file_name = f"{farmer_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.mp3"
        media = MediaIoBaseUpload(file, mimetype='audio/mpeg', resumable=True)
        g_file = service.files().create(body={'name': file_name}, media_body=media, fields='id').execute()
        fid = g_file.get('id')
        service.permissions().create(fileId=fid, body={'type': 'anyone', 'role': 'viewer'}).execute()
        return f"https://drive.google.com/uc?id={fid}"
    except Exception as e:
        st.error(f"Cloud Error: {e}")
        return None

# --- NAVIGATION ---
if "page" not in st.session_state: st.session_state["page"] = "Home"
def nav(p):
    st.session_state["page"] = p
    st.rerun()

# --- UI LOGIC ---
def main():
    page = st.session_state["page"]
    st.sidebar.title("🌳 Amhara 2026")

    if page == "Home":
        st.title("🚜 Amhara 2026 Distribution System")
        cols = st.columns(2)
        with cols[0]:
            if st.button("📝 NEW REGISTRATION", use_container_width=True, type="primary"): nav("Reg")
            if st.button("📍 MANAGE LOCATIONS", use_container_width=True): nav("Loc")
        with cols[1]:
            if st.button("🔍 BACK CHECK FORM", use_container_width=True): nav("BackCheck")
            if st.button("📊 VIEW DATA", use_container_width=True): nav("Data")

    elif page == "Reg":
        if st.button("⬅️ Back"): nav("Home")
        st.header("Farmer Registration")
        db = SessionLocal()
        woredas = db.query(Woreda).all()
        with st.form("reg"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Farmer Name")
            phone = c1.text_input("Phone")
            officer = c1.text_input("Officer (TNO)")
            sel_woreda = c2.selectbox("Woreda", [w.name for w in woredas] if woredas else ["None"])
            # Simplified Kebele Fetching
            keb_list = []
            if woredas and sel_woreda != "None":
                w_obj = db.query(Woreda).filter(Woreda.name == sel_woreda).first()
                keb_list = [k.name for k in w_obj.kebeles]
            sel_kebele = c2.selectbox("Kebele", keb_list if keb_list else ["None"])
            
            st.subheader("Seedlings")
            sc1, sc2, sc3 = st.columns(3)
            gesho = sc1.number_input("Gesho", 0); wanza = sc1.number_input("Wanza", 0)
            lemon = sc2.number_input("Lemon", 0); papaya = sc2.number_input("Papaya", 0)
            guava = sc3.number_input("Guava", 0); moringa = sc3.number_input("Moringa", 0)
            
            audio = st.file_uploader("Audio", type=['mp3','wav'])
            if st.form_submit_button("Save"):
                url = upload_to_drive(audio, name) if audio else None
                new_f = Farmer(name=name, phone=phone, woreda=sel_woreda, kebele=sel_kebele, 
                               officer_name=officer, audio_url=url, gesho=gesho, wanza=wanza, 
                               lemon=lemon, papaya=papaya, guava=guava, moringa=moringa)
                db.add(new_f); db.commit(); st.success("Saved!")
        db.close()

    elif page == "BackCheck":
        if st.button("⬅️ Back"): nav("Home")
        st.header("🔍 Nursery Back Check")
        with st.form("bc"):
            checker = st.text_input("Checker Name")
            fenced = st.radio("Fenced?", ["Yes", "No"])
            
            def bed_sec(label, exp):
                st.markdown(f"**{label}** (Expect {exp})")
                bc1, bc2, bc3 = st.columns(3)
                n = bc1.number_input(f"Beds #", 0, key=f"n_{label}")
                l = bc2.number_input(f"Length (m)", 0.0, key=f"l_{label}")
                s = bc3.number_input(f"Socket Width", 0, key=f"s_{label}")
                return n, l, s

            g_n, g_l, g_s = bed_sec("Guava", 13)
            l_n, l_l, l_s = bed_sec("Lemon", 13)
            ge_n, ge_l, ge_s = bed_sec("Gesho", 16)
            
            if st.form_submit_button("Submit"):
                db = SessionLocal()
                db.add(BackCheck(checker_name=checker, fenced=fenced, guava_beds=g_n, guava_length=g_l, guava_sockets=g_s,
                                 lemon_beds=l_n, lemon_length=l_l, lemon_sockets=l_s, gesho_beds=ge_n, gesho_length=ge_l, gesho_sockets=ge_s))
                db.commit(); db.close(); st.success("Back check saved!")

    elif page == "Data":
        if st.button("⬅️ Back"): nav("Home")
        db = SessionLocal()
        t1, t2 = st.tabs(["Distributions", "Back Checks"])
        with t1:
            data = db.query(Farmer).all()
            if data: st.dataframe(pd.DataFrame([d.__dict__ for d in data]).drop('_sa_instance_state', axis=1))
        with t2:
            data = db.query(BackCheck).all()
            if data: st.dataframe(pd.DataFrame([d.__dict__ for d in data]).drop('_sa_instance_state', axis=1))
        db.close()

    elif page == "Loc":
        if st.button("⬅️ Back"): nav("Home")
        db = SessionLocal()
        w_name = st.text_input("New Woreda")
        if st.button("Add"): db.add(Woreda(name=w_name)); db.commit(); st.rerun()
        for w in db.query(Woreda).all():
            with st.expander(w.name):
                k_name = st.text_input("Add Kebele", key=w.id)
                if st.button("Add K", key=f"btn_{w.id}"): db.add(Kebele(name=k_name, woreda_id=w.id)); db.commit(); st.rerun()
        db.close()

if __name__ == "__main__": main()
