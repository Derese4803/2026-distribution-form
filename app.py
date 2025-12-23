import streamlit as st
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from sqlalchemy import text
import os

# --- 1. IMPORT LOCAL MODULES ---
try:
    from database import SessionLocal
    from models import Farmer, Woreda, Kebele, create_tables
    # Note: We don't need check_auth anymore
except ImportError as e:
    st.error(f"❌ Critical Error: Missing files in repository! {e}")
    st.stop()

# --- 2. CONFIG & DATABASE INIT ---
st.set_page_config(page_title="Amhara Survey 2025", layout="wide", page_icon="🌳")

# Create tables if they don't exist
create_tables()

def run_migrations():
    """Ensures all columns exist in the database even if added later."""
    db = SessionLocal()
    cols = [
        "gesho", "giravila", "diceres", "wanza", "papaya", 
        "moringa", "lemon", "arzelibanos", "guava", 
        "phone", "f_type", "registered_by", "audio_url"
    ]
    for c in cols:
        try:
            dtype = "INTEGER DEFAULT 0" if c not in ["phone", "f_type", "registered_by", "audio_url"] else "TEXT"
            db.execute(text(f"ALTER TABLE farmers ADD COLUMN {c} {dtype}"))
            db.commit()
        except:
            db.rollback() 
    db.close()

run_migrations()

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
        st.error(f"Google Drive Upload Failed: {e}")
        return None

# --- 4. NAVIGATION LOGIC ---
def nav(p):
    st.session_state["page"] = p
    st.rerun()

# --- 5. MAIN APPLICATION FLOW ---
def main():
    # LOGIN REMOVED: The app starts directly here
    if "page" not in st.session_state: 
        st.session_state["page"] = "Home"
    
    # Sidebar only for navigation info now
    st.sidebar.title("🚜 2025 Survey")
    st.sidebar.info("Public Access Mode")

    page = st.session_state["page"]

    # --- PAGE: HOME ---
    if page == "Home":
        st.title("🌾 Amhara 2025 Planting Survey")
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("📝 NEW REGISTRATION", use_container_width=True, type="primary"): nav("Reg")
        with c2:
            if st.button("📍 MANAGE LOCATIONS", use_container_width=True): nav("Loc")
        with c3:
            if st.button("📊 VIEW DATA", use_container_width=True): nav("Data")

    # --- PAGE: REGISTRATION ---
    elif page == "Reg":
        if st.button("⬅️ Back"): nav("Home")
        st.header("Farmer Registration Form")
        db = SessionLocal()
        woredas = db.query(Woreda).all()
        
        with st.form("reg_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Farmer Full Name")
                phone = st.text_input("Phone Number")
                # Add a manual name for the surveyor since login is gone
                surveyor_name = st.text_input("Surveyor Name (Your Name)")
            with col2:
                w_list = [w.name for w in woredas] if woredas else ["No Woredas Found"]
                sel_woreda = st.selectbox("Woreda", w_list)
                
                kebeles = []
                if woredas and sel_woreda != "No Woredas Found":
                    w_obj = db.query(Woreda).filter(Woreda.name == sel_woreda).first()
                    kebeles = [k.name for k in w_obj.kebeles]
                sel_kebele = st.selectbox("Kebele", kebeles if kebeles else ["No Kebeles Found"])
            
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

            audio = st.file_uploader("🎤 Record Audio Note", type=['mp3', 'wav', 'm4a'])
            
            if st.form_submit_button("Save Registration"):
                if not name or not kebeles:
                    st.error("Missing Name or Location!")
                else:
                    with st.spinner("Saving..."):
                        url = upload_to_drive(audio, name) if audio else None
                        new_f = Farmer(
                            name=name, phone=phone, woreda=sel_woreda, 
                            kebele=sel_kebele, audio_url=url, 
                            registered_by=surveyor_name, # Saved from the text input
                            gesho=gesho, giravila=giravila, diceres=diceres, wanza=wanza,
                            papaya=papaya, moringa=moringa, lemon=lemon, 
                            arzelibanos=arzelibanos, guava=guava
                        )
                        db.add(new_f)
                        db.commit()
                        st.success(f"✅ Record for {name} saved!")
        db.close()

    # --- PAGE: LOCATIONS ---
    elif page == "Loc":
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
                for k in w.kebeles:
                    st.write(f"- {k.name}")
        db.close()

    # --- PAGE: DATA VIEW ---
    elif page == "Data":
        if st.button("⬅️ Back"): nav("Home")
        st.header("📊 Survey Records")
        db = SessionLocal()
        farmers = db.query(Farmer).all()
        if farmers:
            # Drop unnecessary internal column for display
            df = pd.DataFrame([f.__dict__ for f in farmers]).drop('_sa_instance_state', axis=1)
            st.download_button("📥 Download CSV", df.to_csv(index=False).encode('utf-8'), "Survey_Data.csv")
            st.dataframe(df)
        else:
            st.info("No records yet.")
        db.close()

if __name__ == "__main__":
    main()
