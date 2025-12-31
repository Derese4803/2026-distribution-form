import streamlit as st
import pandas as pd
from database import SessionLocal, engine
from models import BackCheck, Base

# --- INITIALIZATION ---
st.set_page_config(page_title="Amhara 2026 Back Check", layout="wide", page_icon="🔍")

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()

# --- NAVIGATION ---
if "page" not in st.session_state:
    st.session_state["page"] = "Form"

def nav(p):
    st.session_state["page"] = p
    st.rerun()

# --- MAIN UI ---
def main():
    page = st.session_state["page"]
    
    st.sidebar.title("🔍 Back Check System")
    if st.sidebar.button("📝 Form"): nav("Form")
    if st.sidebar.button("📊 View Data"): nav("Data")

    # --- PAGE: FORM ---
    if page == "Form":
        st.title("🚜 Amhara 2026 Nursery Back Check")
        db = SessionLocal()

        with st.form("back_check_form", clear_on_submit=True):
            # Identification Section
            st.subheader("📍 Location & Personnel")
            c1, c2 = st.columns(2)
            with c1:
                woreda = st.text_input("Woreda")
                fa_name = st.text_input("Name of Back checker (FAs)")
                phone = st.text_input("Back checker phone #")
            with c2:
                kebele = st.text_input("Kebele")
                cbe_name = st.text_input("Back checker (CBE)")
                fenced = st.radio("Does the Nursery have Fenced?", ["Yes", "No"], horizontal=True)

            st.markdown("---")

            # Seedling Metrics Section
            
            
            def bed_input_row(species, expected_width):
                st.markdown(f"#### 🌿 {species} Beds")
                st.info(f"💡 Note: We expect **{expected_width}** sockets in the width of the {species} beds.")
                bc1, bc2, bc3 = st.columns(3)
                n = bc1.number_input(f"{species} beds number", min_value=0, key=f"n_{species}")
                l = bc2.number_input(f"Length of {species} beds (meters)", min_value=0.0, step=0.1, key=f"l_{species}")
                s = bc3.number_input(f"Sockets in width", min_value=0, key=f"s_{species}")
                return n, l, s

            # Capture Inputs
            g_n, g_l, g_s = bed_input_row("Guava", 13)
            l_n, l_l, l_s = bed_input_row("Lemon", 13)
            ge_n, ge_l, ge_s = bed_input_row("Gesho", 16)
            gr_n, gr_l, gr_s = bed_input_row("Grevillea", 16)

            # Automatic Calculation
            total_l_sockets = l_n * l_s
            st.write(f"**Total Lemon Sockets (Auto-calculated):** {total_l_sockets}")

            # Submission Logic
            if st.form_submit_button("Submit Back Check Record"):
                if not woreda or not kebele or not fa_name:
                    st.error("Please fill in Woreda, Kebele, and FAs Name!")
                else:
                    new_record = BackCheck(
                        woreda=woreda,
                        kebele=kebele,
                        checker_fa_name=fa_name,
                        checker_cbe_name=cbe_name,
                        checker_phone=phone,
                        fenced=fenced,
                        guava_beds=g_n, guava_length=g_l, guava_sockets=g_s,
                        lemon_beds=l_n, lemon_length=l_l, lemon_sockets=l_s,
                        total_lemon_sockets=total_l_sockets,
                        gesho_beds=ge_n, gesho_length=ge_l, gesho_sockets=ge_s,
                        grevillea_beds=gr_n, grevillea_length=gr_l, grevillea_sockets=gr_s
                    )
                    db.add(new_record)
                    db.commit()
                    st.success(f"✅ Record for {kebele} saved successfully!")
        db.close()

    # --- PAGE: DATA VIEW ---
    elif page == "Data":
        st.title("📊 Recorded Back Check Data")
        db = SessionLocal()
        records = db.query(BackCheck).all()
        if records:
            df = pd.DataFrame([r.__dict__ for r in records]).drop('_sa_instance_state', axis=1, errors='ignore')
            st.dataframe(df)
            
            # CSV Download Button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download as CSV", data=csv, file_name="BackCheck_Data.csv", mime="text/csv")
        else:
            st.info("No records found yet.")
        db.close()

if __name__ == "__main__":
    main()
