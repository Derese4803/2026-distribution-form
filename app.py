import streamlit as st
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from sqlalchemy import text

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
        st.error(f"Cloud Storage Error: {e}")
        return None

# --- NAVIGATION ---
if "page" not in st.session_state: st.session_state["page"] = "Home"
def nav(p):
    st.session_state["page"] = p
    st.rerun()

# --- MAIN UI ---
def main():
    page = st.session_state["page"]
    st.sidebar.title("🌳 Amhara 2026")

    if page == "Home":
        st.title("🌳 Amhara 2026 Distribution & Back Check")
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📝 NEW REGISTRATION", use_container_width=True, type="primary"): nav("Reg")
            if st.button("📍 MANAGE LOCATIONS", use_container_width=True): nav("Loc")
        with c2:
            if st.button("🔍 NURSERY BACK CHECK", use_container_width=True): nav("BackCheck")
            if st.button("📊 VIEW SURVEY DATA", use_container_width=True): nav("Data")

    elif page == "Reg":
        if st.button("⬅️ Back"): nav("Home")
        st.header("New Farmer Registration")
        db = SessionLocal()
        woredas = db.query(Woreda).all()
        
        with st.form("reg_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Farmer Full Name")
                phone = st.text_input("Phone Number")
                officer = st.text_input("Distribution Officer (TNO)")
            with col2:
                w_list = [w.name for w in woredas] if woredas else ["Add Woredas First"]
                sel_woreda = st.selectbox("Woreda", w_list)
                keb_list = []
                if woredas and sel_woreda != "Add Woredas First":
                    w_obj = db.query(Woreda).filter(Woreda.name == sel_woreda).first()
                    keb_list = [k.name for k in w_obj.kebeles]
                sel_kebele = st.selectbox("Kebele", keb_list if keb_list else ["No Kebeles Found"])

            st.markdown("---")
            st.subheader("🌲 Seedlings Distributed")
            t1, t2, t3 = st.columns(3)
            with t1:
                gesho = st.number_input("Gesho", 0); wanza = st.number_input("Wanza", 0); lemon = st.number_input("Lemon", 0)
            with t2:
                giravila = st.number_input("Giravila", 0); papaya = st.number_input("Papaya", 0); arzelibanos = st.number_input("Arzelibanos", 0)
            with t3:
                diceres = st.number_input("Diceres", 0); moringa = st.number_input("Moringa", 0); guava = st.number_input("Guava", 0)

            audio = st.file_uploader("🎤 Audio Confirmation", type=['mp3', 'wav', 'm4a'])
            
            if st.form_submit_button("Submit Distribution"):
                if not name or not officer: st.error("Name and Officer required!")
                else:
                    url = upload_to_drive(audio, name) if audio else None
                    new_f = Farmer(name=name, phone=phone, woreda=sel_woreda, kebele=sel_kebele, 
                                   officer_name=officer, audio_url=url, gesho=gesho, giravila=giravila, 
                                   diceres=diceres, wanza=wanza, papaya=papaya, moringa=moringa, 
                                   lemon=lemon, arzelibanos=arzelibanos, guava=guava)
                    db.add(new_f); db.commit(); st.success("Saved!")
        db.close()

    elif page == "BackCheck":
        if st.button("⬅️ Back"): nav("Home")
        st.header("🔍 Nursery Back Check Form")
        db = SessionLocal()
        woredas = db.query(Woreda).all()

        with st.form("bc_form"):
            c1, c2 = st.columns(2)
            with c1:
                checker = st.text_input("Back Checker Name")
                w_list = [w.name for w in woredas] if woredas else ["Add Woredas First"]
                sel_woreda = st.selectbox("Woreda", w_list)
            with c2:
                fenced = st.radio("Does Nursery have Fenced?", ["Yes", "No"])
                keb_list = []
                if woredas and sel_woreda != "Add Woredas First":
                    w_obj = db.query(Woreda).filter(Woreda.name == sel_woreda).first()
                    keb_list = [k.name for k in w_obj.kebeles]
                sel_kebele = st.selectbox("Kebele", keb_list if keb_list else ["No Kebeles Found"])

            st.markdown("---")

            def bed_row(species, expected):
                st.markdown(f"#### {species} (Expect {expected} sockets)")
                col1, col2, col3 = st.columns(3)
                n = col1.number_input(f"{species} beds #", 0, key=f"n_{species}")
                l = col2.number_input(f"Length (m)", 0.0, step=0.1, key=f"l_{species}")
                s = col3.number_input(f"Socket Width", 0, key=f"s_{species}")
                return n, l, s

            g_n, g_l, g_s = bed_row("Guava", 13)
            l_n, l_l, l_s = bed_row("Lemon", 13)
            ge_n, ge_l, ge_s = bed_row("Gesho", 16)
            gr_n, gr_l, gr_s = bed_row("Grevillea", 16)

            # Calculation for Lemon
            total_l_sockets = l_n * l_s
            st.info(f"💡 Calculated Total Lemon Sockets: {total_l_sockets}")

            if st.form_submit_button("Submit Back Check"):
                new_bc = BackCheck(checker_name=checker, woreda=sel_woreda, kebele=sel_kebele, fenced=fenced,
                                  guava_beds=g_n, guava_length=g_l, guava_sockets=g_s,
                                  lemon_beds=l_n, lemon_length=l_l, lemon_sockets=l_s,
                                  total_lemon_sockets=total_l_sockets,
                                  gesho_beds=ge_n, gesho_length=ge_l, gesho_sockets=ge_s,
                                  grevillea_beds=gr_n, grevillea_length=gr_l, grevillea_sockets=gr_s)
                db.add(new_bc); db.commit(); st.success("Back Check Saved!")
        db.close()

    elif page == "Data":
        if st.button("⬅️ Back"): nav("Home")
        db = SessionLocal()
        t1, t2 = st.tabs(["Farmer Distribution", "Nursery Back Checks"])
        with t1:
            df1 = pd.DataFrame([f.__dict__ for f in db.query(Farmer).all()]).drop('_sa_instance_state', axis=1, errors='ignore')
            st.dataframe(df1)
        with t2:
            df2 = pd.DataFrame([b.__dict__ for b in db.query(BackCheck).all()]).drop('_sa_instance_state', axis=1, errors='ignore')
            st.dataframe(df2)
        db.close()

    elif page == "Loc":
        if st.button("⬅️ Back"): nav("Home")
        db = SessionLocal()
        st.header("📍 Manage Areas")
        nw = st.text_input("New Woreda")
        if st.button("Add Woreda"):
            if nw: db.add(Woreda(name=nw)); db.commit(); st.rerun()
        for w in db.query(Woreda).all():
            with st.expander(f"📌 {w.name}"):
                nk = st.text_input(f"Add Kebele to {w.name}", key=w.id)
                if st.button("Add Kebele", key=f"btn_{w.id}"):
                    if nk: db.add(Kebele(name=nk, woreda_id=w.id)); db.commit(); st.rerun()
        db.close()

if __name__ == "__main__": main()
