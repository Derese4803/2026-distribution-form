import streamlit as st
import pandas as pd
import base64
from database import SessionLocal, engine
from models import BackCheck, Base
from io import BytesIO

# --- INITIALIZATION ---
st.set_page_config(page_title="OAF Nursery Back Check", layout="wide", page_icon="🌳")

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()

# Helper to convert uploaded photo to string
def process_photo(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        return base64.b64encode(bytes_data).decode()
    return None

if "page" not in st.session_state:
    st.session_state["page"] = "Form"

def nav(p):
    st.session_state["page"] = p
    st.rerun()

def main():
    page = st.session_state["page"]
    
    # --- SIDEBAR ---
    st.sidebar.title("OAF Nursery 🌳")
    if st.sidebar.button("📝 Registration Form / መመዝገቢያ ፎርም", use_container_width=True): nav("Form")
    if st.sidebar.button("📊 View & Delete / መረጃዎችን ይመልከቱ", use_container_width=True): nav("Data")

    if page == "Form":
        st.title("🚜 Nursery Back Check Form / የችግኝ ጣቢያ ቁጥጥር ፎርም")
        db = SessionLocal()

        with st.form("oaf_form", clear_on_submit=True):
            st.subheader("📍 Location & Personnel / ቦታ እና ሰራተኛ")
            c1, c2, c3, c4 = st.columns(4)
            w_val = c1.text_input("Woreda / ወረዳ")
            cl_val = c2.text_input("Cluster / ክላስተር")
            k_val = c3.text_input("Kebele / ቀበሌ")
            t_val = c4.text_input("TNO Name / የTNO ስም")

            p1, p2, p3, p4 = st.columns(4)
            f_val = p1.text_input("FA Name / የFA ስም")
            acc_val = p2.text_input("CBE ACC / የCBE ሂሳብ ቁጥር")
            ph_val = p3.text_input("Phone / ስልክ ቁጥር")
            fn_val = p4.radio("Is Nursery Fenced? / አጥር አለው?", ["Yes / አዎ", "No / የለም"], horizontal=True)

            def bed_section(species, amharic, expected):
                st.markdown(f"--- \n### 🌿 {species} ({amharic})")
                st.info(f"💡 Expected: **{expected}** sockets. / የሚጠበቀው፡ **{expected}** ሶኬቶች።")
                bc1, bc2, bc3 = st.columns(3)
                n = bc1.number_input(f"{amharic} beds #", min_value=0, step=1, key=f"n_{species}")
                l = bc2.number_input(f"{amharic} Length (m)", min_value=0.0, step=0.1, key=f"l_{species}")
                s = bc3.number_input(f"{amharic} Sockets width", min_value=0, step=1, key=f"s_{species}")
                return n, l, s

            g_n, g_l, g_s = bed_section("Guava", "ዘይቶን", 13)
            ge_n, ge_l, ge_s = bed_section("Gesho", "ጌሾ", 16)
            l_n, l_l, l_s = bed_section("Lemon", "ሎሚ", 13)
            gr_n, gr_l, gr_s = bed_section("Grevillea", "ግራቪሊያ", 16)

            st.markdown("---")
            st.subheader("📸 Upload Photo & Remarks / ፎቶ እና ማስታወሻ")
            
            # Photo Upload field
            uploaded_photo = st.file_uploader("Upload Nursery Photo / የችግኝ ጣቢያውን ፎርም ይጫኑ", type=['jpg', 'png', 'jpeg'])
            gen_remark = st.text_area("General Remarks / አጠቃላይ አስተያየት")

            if st.form_submit_button("Submit Data / መረጃውን መዝግብ"):
                photo_str = process_photo(uploaded_photo)
                
                # Simple Logic for auto-remark
                def get_rem(val, exp, name):
                    if val == 0: return ""
                    return f"{name}: Correct" if val == exp else f"{name}: Error"

                auto_rem = f"{get_rem(g_s, 13, 'Guava')} | {get_rem(ge_s, 16, 'Gesho')}"

                try:
                    new_rec = BackCheck(
                        woreda=w_val, cluster=cl_val, kebele=k_val, tno_name=t_val,
                        checker_fa_name=f_val, cbe_acc=acc_val, checker_phone=ph_val, fenced=fn_val,
                        guava_beds=g_n, guava_length=g_l, guava_sockets=g_s, total_guava_sockets=g_n*g_s,
                        gesho_beds=ge_n, gesho_length=ge_l, gesho_sockets=ge_s, total_gesho_sockets=ge_n*ge_s,
                        lemon_beds=l_n, lemon_length=l_l, lemon_sockets=l_s, total_lemon_sockets=l_n*l_s,
                        grevillea_beds=gr_n, grevillea_length=gr_l, grevillea_sockets=gr_s, total_grevillea_sockets=gr_n*gr_s,
                        auto_remark=auto_rem, general_remark=gen_remark,
                        photo=photo_str
                    )
                    db.add(new_rec); db.commit()
                    st.success("✅ Saved Successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")
        db.close()

    elif page == "Data":
        st.title("📊 Recorded Data")
        db = SessionLocal()
        
        recs = db.query(BackCheck).all()
        if recs:
            for r in recs:
                with st.container(border=True):
                    col_text, col_img = st.columns([3, 1])
                    with col_text:
                        st.write(f"**ID:** {r.id} | **Kebele:** {r.kebele} | **FA:** {r.checker_fa_name}")
                        st.write(f"**Remark:** {r.general_remark}")
                    with col_img:
                        if r.photo:
                            st.image(base64.b64decode(r.photo), width=150)
                        else:
                            st.write("No Photo")
                    if st.button(f"Delete ID {r.id}", key=f"del_{r.id}"):
                        db.delete(r); db.commit()
                        st.rerun()
        db.close()

if __name__ == "__main__":
    main()
