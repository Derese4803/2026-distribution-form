import streamlit as st
import pandas as pd
from database import SessionLocal, engine
from models import BackCheck, Base

# --- INITIALIZATION ---
st.set_page_config(page_title="OAF Nursery Back Check", layout="wide", page_icon="🌳")

def init_db():
    # This creates the table. Remember: delete your old .db file first!
    Base.metadata.create_all(bind=engine)

init_db()

if "page" not in st.session_state:
    st.session_state["page"] = "Form"

def nav(p):
    st.session_state["page"] = p
    st.rerun()

def main():
    page = st.session_state["page"]
    
    # --- SIDEBAR ---
    st.sidebar.title("OAF Nursery 🌳")
    st.sidebar.markdown("---")
    if st.sidebar.button("📝 Registration Form / መመዝገቢያ ፎርም", use_container_width=True): nav("Form")
    if st.sidebar.button("📊 View Records / መረጃዎችን ይመልከቱ", use_container_width=True): nav("Data")

    # --- PAGE 1: REGISTRATION FORM ---
    if page == "Form":
        st.title("🚜 Nursery Back Check / የችግኝ ጣቢያ ቁጥጥር")
        db = SessionLocal()

        with st.form("oaf_form", clear_on_submit=True):
            st.subheader("📍 Location & Personnel / ቦታ እና ሰራተኛ")
            
            c1, c2, c3, c4 = st.columns(4)
            w_val = c1.text_input("Woreda (ወረዳ)")
            cl_val = c2.text_input("Cluster (ክላስተር)")
            k_val = c3.text_input("Kebele (ቀበሌ)")
            t_val = c4.text_input("TNO Name (የTNO ስም)")

            p1, p2, p3, p4 = st.columns(4)
            f_val = p1.text_input("FA Name (የFA ስም)")
            acc_val = p2.text_input("CBE ACC (የCBE ሂሳብ ቁጥር)")
            ph_val = p3.text_input("Phone (ስልክ ቁጥር)")
            fn_val = p4.radio("Fenced? (አጥር አለው?)", ["Yes (አዎ)", "No (የለም)"], horizontal=True)

            st.markdown("---")

            def bed_section(species, amharic):
                st.markdown(f"### 🌿 {species} ({amharic})")
                bc1, bc2, bc3 = st.columns(3)
                n = bc1.number_input(f"{amharic} beds #", min_value=0, step=1, key=f"n_{species}")
                l = bc2.number_input(f"{amharic} length (m)", min_value=0.0, step=0.1, key=f"l_{species}")
                s = bc3.number_input(f"{amharic} sockets", min_value=0, step=1, key=f"s_{species}")
                return n, l, s

            g_n, g_l, g_s = bed_section("Guava", "ዘይቶን")
            ge_n, ge_l, ge_s = bed_section("Gesho", "ጌሾ")
            l_n, l_l, l_s = bed_section("Lemon", "ሎሚ")
            gr_n, gr_l, gr_s = bed_section("Grevillea", "ግራቪሊያ")

            if st.form_submit_button("Submit Data / መረጃውን መዝግብ"):
                if not w_val or not k_val:
                    st.error("Woreda and Kebele are required! / ወረዳ እና ቀበሌ አልተሞላም!")
                else:
                    try:
                        new_record = BackCheck(
                            woreda=w_val, cluster=cl_val, kebele=k_val, tno_name=t_val,
                            checker_fa_name=f_val, cbe_acc=acc_val,
                            checker_phone=ph_val, fenced=fn_val,
                            guava_beds=g_n, guava_length=g_l, guava_sockets=g_s, total_guava_sockets=g_n*g_s,
                            gesho_beds=ge_n, gesho_length=ge_l, gesho_sockets=ge_s, total_gesho_sockets=ge_n*ge_s,
                            lemon_beds=l_n, lemon_length=l_l, lemon_sockets=l_s, total_lemon_sockets=l_n*l_s,
                            grevillea_beds=gr_n, grevillea_length=gr_l, grevillea_sockets=gr_s, total_grevillea_sockets=gr_n*gr_s
                        )
                        db.add(new_record)
                        db.commit()
                        st.success("✅ Saved Successfully! / መረጃው ተመዝግቧል!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error: {e}. Please delete your .db file and try again.")
        db.close()

    # --- PAGE 2: DATA VIEW ---
    elif page == "Data":
        st.title("📊 Recorded Data / የተመዘገቡ መረጃዎች")
        db = SessionLocal()
        records = db.query(BackCheck).all()
        if records:
            df = pd.DataFrame([r.__dict__ for r in records])
            
            # --- CUSTOM ORDERED COLUMNS (BED -> LENGTH -> SOCKET) ---
            ordered_cols = [
                'id', 'woreda', 'cluster', 'kebele', 'tno_name', 'checker_fa_name', 'cbe_acc', 'checker_phone',
                'guava_beds', 'guava_length', 'guava_sockets',   # Guava Group
                'gesho_beds', 'gesho_length', 'gesho_sockets',   # Gesho Group
                'lemon_beds', 'lemon_length', 'lemon_sockets',   # Lemon Group
                'grevillea_beds', 'grevillea_length', 'grevillea_sockets', # Grevillea Group
                'fenced', 'timestamp'
            ]
            
            # Filter and order safely
            final_df = df[[c for c in ordered_cols if c in df.columns]]
            
            # Amharic Headers for Display
            rename_map = {
                'woreda': 'ወረዳ', 'cluster': 'ክላስተር', 'kebele': 'ቀበሌ', 'tno_name': 'TNO ስም',
                'checker_fa_name': 'FA ስም', 'cbe_acc': 'CBE ACC', 'checker_phone': 'ስልክ',
                'guava_beds': 'ዘይቶን አልጋ', 'guava_length': 'ዘይቶን ርዝመት', 'guava_sockets': 'ዘይቶን ሶኬት',
                'gesho_beds': 'ጌሾ አልጋ', 'gesho_length': 'ጌሾ ርዝመት', 'gesho_sockets': 'ጌሾ ሶኬት',
                'lemon_beds': 'ሎሚ አልጋ', 'lemon_length': 'ሎሚ ርዝመት', 'lemon_sockets': 'ሎሚ ሶኬት',
                'grevillea_beds': 'ግራቪሊያ አልጋ', 'grevillea_length': 'ግራቪሊያ ርዝመት', 'grevillea_sockets': 'ግራቪሊያ ሶኬት',
                'fenced': 'አጥር', 'timestamp': 'ጊዜ'
            }
            
            st.dataframe(final_df.rename(columns=rename_map), use_container_width=True)
            st.download_button("📥 Export CSV", data=final_df.to_csv(index=False), file_name="nursery_data.csv")
        else:
            st.info("No records found.")
        db.close()

if __name__ == "__main__":
    main()
