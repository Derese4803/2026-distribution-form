import streamlit as st
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from sqlalchemy import text
import os

from database import SessionLocal
from models import Farmer, Woreda, Kebele, create_tables

# --- INITIALIZATION ---
st.set_page_config(page_title="Amhara distributio register form 2025", layout="wide", page_icon="🌳")
create_tables()

def run_migrations():
    db = SessionLocal()
    cols = ["gesho", "giravila", "diceres", "wanza", "papaya", "moringa", "lemon", "arzelibanos", "guava", "phone", "registered_by", "audio_url"]
    for c in cols:
        try:
            dtype = "INTEGER DEFAULT 0" if c not in ["phone", "registered_by", "audio_url"] else "TEXT"
            db.execute(text(f"ALTER TABLE farmers ADD COLUMN {c} {dtype}"))
            db.commit()
        except:
            db.rollback() 
    db.close()

run_migrations()

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
        st.error(f"Drive Error: {e}")
        return None

# --- NAVIGATION ---
if "page" not in st.session_state: st.session_state["page"] = "Home"
def nav(p):
    st.session_state["page"] = p
    st.rerun()

# --- APP PAGES ---
def main():
    st.sidebar.title("🚜 2025 Survey")
    p = st.session_state["page"]

    if p == "Home":
        st.title("🌾 Amhara 2025 Planting Survey")
        st.info("Public Access Mode - No Login Required")
        c1, c2, c3 = st.columns(3)
        if c1.button("📝 NEW REGISTRATION", use_container_width=True, type="primary"): nav("Reg")
        if c2.button("📍 LOCATIONS", use_container_width=True): nav("Loc")
        if c3.button("📊 VIEW DATA", use_container_width=True): nav("Data")

    elif p == "Reg":
        if st.button("⬅️ Back"): nav("Home")
        st.header("Farmer Registration")
        db = SessionLocal()
        woredas = db.query(Woreda).all()
        
        with st.form("reg_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                name = st.text_input("Farmer Full Name")
                phone = st.text_input("Phone Number")
                surveyor = st.text_input("Your Name (Surveyor)")
            with col_b:
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

            audio = st.file_uploader("🎤 Audio Note", type=['mp3', 'wav', 'm4a'])
            
            if st.form_submit_button("Save Registration"):
                if not name or not kebeles:
                    st.error("Missing Name or Location!")
                else:
                    url = upload_to_drive(audio, name) if audio else None
                    new_f = Farmer(
                        name=name, phone=phone, woreda=sel_woreda, kebele=sel_kebele,
                        registered_by=surveyor, audio_url=url,
                        gesho=gesho, giravila=giravila, diceres=diceres, wanza=wanza,
                        papaya=papaya, moringa=moringa, lemon=lemon, 
                        arzelibanos=arzelibanos, guava=guava
                    )
                    db.add(new_f)
                    db.commit()
                    st.success("✅ Saved Successfully!")
        db.close()

    elif p == "Loc":
        if st.button("⬅️ Back"): nav("Home")
        db = SessionLocal()
        st.header("📍 Location Management")
        nw = st.text_input("New Woreda Name")
        if st.button("Save Woreda"):
            if nw: db.add(Woreda(name=nw)); db.commit(); st.rerun()

        for w in db.query(Woreda).all():
            with st.expander(f"📌 {w.name}"):
                nk = st.text_input(f"New Kebele for {w.name}", key=f"k_{w.id}")
                if st.button("Add Kebele", key=f"b_{w.id}"):
                    if nk: db.add(Kebele(name=nk, woreda_id=w.id)); db.commit(); st.rerun()
                for k in w.kebeles: st.write(f"- {k.name}")
        db.close()

    elif p == "Data":
        if st.button("⬅️ Back"): nav("Home")
        st.header("📊 Survey Records")
        db = SessionLocal()
        farmers = db.query(Farmer).all()
        if farmers:
            df = pd.DataFrame([f.__dict__ for f in farmers]).drop('_sa_instance_state', axis=1)
            st.download_button("📥 Download CSV", df.to_csv(index=False).encode('utf-8'), "Survey_Data.csv")
            st.dataframe(df)
        else: st.info("No records yet.")
        db.close()

if __name__ == "__main__": main()
