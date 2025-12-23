import streamlit as st
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from sqlalchemy import text
import os

# --- SYSTEM IMPORTS ---
try:
    from database import SessionLocal
    from models import Farmer, Woreda, Kebele, create_tables
except ImportError:
    st.error("⚠️ models.py or database.py missing!")
    st.stop()

# --- INITIALIZATION & MIGRATIONS ---
st.set_page_config(page_title="2025 Amhara Survey", layout="wide", page_icon="🌳")
create_tables()

def run_migrations():
    db = SessionLocal()
    # List of all possible columns to ensure DB is up to date
    trees = ["gesho", "giravila", "diceres", "wanza", "papaya", "moringa", "lemon", "arzelibanos", "guava"]
    base_cols = ["f_type", "audio_url", "phone", "registered_by"]
    
    for col in base_cols + trees:
        try:
            ctype = "INTEGER DEFAULT 0" if col in trees else "TEXT"
            db.execute(text(f"ALTER TABLE farmers ADD COLUMN {col} {ctype}"))
            db.commit()
        except Exception:
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
        st.error(f"Upload Error: {e}")
        return None

# --- NAVIGATION ---
if "page" not in st.session_state: st.session_state["page"] = "Home"
def nav(p):
    st.session_state["page"] = p
    st.rerun()

# --- PAGE: HOME ---
def home_page():
    st.title("🌾 2025 Amhara Planting Survey")
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📝 NEW REGISTRATION", use_container_width=True, type="primary"): nav("Reg")
    with c2:
        if st.button("📍 MANAGE LOCATIONS", use_container_width=True): nav("Loc")
    with c3:
        if st.button("📊 DATA & DOWNLOAD", use_container_width=True): nav("Data")

# --- PAGE: REGISTRATION ---
def registration_page():
    if st.button("⬅️ Home"): nav("Home")
    st.header("📝 Farmer Registration")
    db = SessionLocal()
    woredas = db.query(Woreda).all()
    
    with st.form("reg_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            name = st.text_input("Farmer Full Name")
            f_type = st.selectbox("Farmer Type", ["Smallholder", "Commercial", "Large Scale", "Subsistence"])
            phone = st.text_input("Phone Number")
        with col_b:
            w_names = [w.name for w in woredas] if woredas else ["Add Woredas First"]
            sel_woreda = st.selectbox("Woreda", w_names)
            kebeles = []
            if woredas and sel_woreda != "Add Woredas First":
                w_obj = db.query(Woreda).filter(Woreda.name == sel_woreda).first()
                kebeles = [k.name for k in w_obj.kebeles]
            sel_kebele = st.selectbox("Kebele", kebeles if kebeles else ["No Kebeles Found"])

        st.subheader("🌲 Tree Seedlings Distributed")
        t1, t2, t3 = st.columns(3)
        with t1:
            gesho = st.number_input("Gesho", min_value=0, step=1)
            wanza = st.number_input("Wanza", min_value=0, step=1)
            lemon = st.number_input("Lemon", min_value=0, step=1)
        with t2:
            giravila = st.number_input("Giravila", min_value=0, step=1)
            papaya = st.number_input("Papaya", min_value=0, step=1)
            arzelibanos = st.number_input("Arzelibanos", min_value=0, step=1)
        with t3:
            diceres = st.number_input("Diceres", min_value=0, step=1)
            moringa = st.number_input("Moringa", min_value=0, step=1)
            guava = st.number_input("Guava", min_value=0, step=1)

        audio = st.file_uploader("🎤 Audio Note", type=['mp3', 'wav', 'm4a'])
        
        if st.form_submit_button("Save Record"):
            if not name or not kebeles:
                st.error("Missing name or location!")
            else:
                url = upload_to_drive(audio, name) if audio else None
                new_f = Farmer(
                    name=name, f_type=f_type, woreda=sel_woreda, kebele=sel_kebele, 
                    phone=phone, audio_url=url, registered_by=st.session_state.get('user'),
                    gesho=gesho, giravila=giravila, diceres=diceres, wanza=wanza,
                    papaya=papaya, moringa=moringa, lemon=lemon, arzelibanos=arzelibanos, guava=guava
                )
                db.add(new_f)
                db.commit()
                st.success("✅ Saved Successfully!")
    db.close()

# --- PAGE: LOCATIONS ---
def location_page():
    if st.button("⬅️ Home"): nav("Home")
    db = SessionLocal()
    st.header("📍 Manage Locations")
    nw = st.text_input("New Woreda")
    if st.button("Add Woreda"):
        if nw: db.add(Woreda(name=nw)); db.commit(); st.rerun()
    for w in db.query(Woreda).all():
        with st.expander(f"📌 {w.name}"):
            nk = st.text_input(f"New Kebele for {w.name}", key=f"in{w.id}")
            if st.button("Add", key=f"bn{w.id}"):
                db.add(Kebele(name=nk, woreda_id=w.id)); db.commit(); st.rerun()
            for k in w.kebeles:
                st.text(f"• {k.name}")
    db.close()

# --- PAGE: DATA ---
def data_page():
    if st.button("⬅️ Home"): nav("Home")
    st.header("📊 Survey Records")
    db = SessionLocal()
    farmers = db.query(Farmer).all()
    if farmers:
        df = pd.DataFrame([{
            "Name": f.name, "Woreda": f.woreda, "Kebele": f.kebele,
            "Gesho": f.gesho, "Wanza": f.wanza, "Papaya": f.papaya,
            "Lemon": f.lemon, "Moringa": f.moringa, "Guava": f.guava,
            "Total Trees": (f.gesho + f.wanza + f.papaya + f.lemon + f.moringa + f.guava + f.giravila + f.diceres + f.arzelibanos),
            "Audio": f.audio_url
        } for f in farmers])
        st.download_button("📥 Download CSV", df.to_csv(index=False).encode('utf-8'), "Survey_Data.csv")
        st.dataframe(df)
    else: st.info("No records yet.")
    db.close()

# --- MAIN ---
def main():
    if "user" not in st.session_state:
        st.title("🚜 Survey Login")
        u = st.text_input("User")
        if st.button("Login"):
            st.session_state["user"] = u
            st.rerun()
    else:
        p = st.session_state["page"]
        if p == "Home": home_page()
        elif p == "Reg": registration_page()
        elif p == "Loc": location_page()
        elif p == "Data": data_page()

if __name__ == "__main__": main()
