import streamlit as st
import pandas as pd
import base64
import zipfile
from io import BytesIO
from sqlalchemy import inspect, text
from database import SessionLocal, engine
from models import BackCheck, Base
from auth import check_password

# --- INITIALIZATION ---
st.set_page_config(page_title="OAF Nursery", layout="wide", page_icon="🌳")

def init_db():
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    cols = [c['name'] for c in inspector.get_columns('oaf_back_checks')]
    with engine.connect() as conn:
        for c_name in ['cbe_acc', 'auto_remark', 'general_remark', 'photo']:
            if c_name not in cols:
                conn.execute(text(f"ALTER TABLE oaf_back_checks ADD COLUMN {c_name} TEXT"))
        conn.commit()

init_db()

def process_photo(file):
    return base64.b64encode(file.getvalue()).decode() if file else None

if "page" not in st.session_state: st.session_state["page"] = "Form"
def nav(p):
    st.session_state["page"] = p
    st.rerun()

def main():
    # --- SIDEBAR / የጎን አሞሌ ---
    st.sidebar.title("OAF Nursery 🌳")
    if st.sidebar.button("📝 Registration Form / መመዝገቢያ ፎርም", use_container_width=True): nav("Form")
    if st.sidebar.button("📊 View Data / መረጃዎችን ይመልከቱ", use_container_width=True): nav("Data")

    # --- PAGE 1: FORM ---
    if st.session_state["page"] == "Form":
        st.title("🚜 Nursery Back Check / የችግኝ ጣቢያ ቁጥጥር")
        db = SessionLocal()
        with st.form("main_form", clear_on_submit=True):
            st.subheader("📍 Location & Personnel / ቦታ እና ሰራተኛ")
            c1, c2, c3, c4 = st.columns(4)
            w = c1.text_input("Woreda / ወረዳ")
            cl = c2.text_input("Cluster / ክላስተር")
            k = c3.text_input("Kebele / ቀበሌ")
            t = c4.text_input("TNO Name / የTNO ስም")
            
            p1, p2, p3, p4 = st.columns(4)
            fa = p1.text_input("FA Name / የFA ስም")
            acc = p2.text_input("CBE Account / የCBE ሂሳብ ቁጥር")
            ph = p3.text_input("Phone Number / ስልክ ቁጥር")
            fn = p4.radio("Is it Fenced? / አጥር አለው?", ["Yes / አዎ", "No / የለም"], horizontal=True)

            def section(name, amharic, exp):
                st.markdown(f"--- \n### 🌿 {name} ({amharic})")
                st.info(f"💡 Expected width: **{exp}** sockets / የሚጠበቀው የጎን ስፋት: **{exp}** ሶኬቶች")
                sc1, sc2, sc3 = st.columns(3)
                nb = sc1.number_input(f"Number of Beds / የ{amharic} አልጋዎች ብዛት", 0, key=f"n_{name}")
                ln = sc2.number_input(f"Bed Length (m) / የአልጋው ርዝመት (ሜትር)", 0.0, key=f"l_{name}")
                sk = sc3.number_input(f"Sockets Wide / በጎን ያሉት ሶኬቶች ብዛት", 0, key=f"s_{name}")
                return nb, ln, sk

            g_n, g_l, g_s = section("Guava", "ዘይቶን", 13)
            ge_n, ge_l, ge_s = section("Gesho", "ጌሾ", 16)
            l_n, l_l, l_s = section("Lemon", "ሎሚ", 13)
            gr_n, gr_l, gr_s = section("Grevillea", "ግራቪሊያ", 16)

            st.markdown("---")
            st.subheader("📸 Photo & Remarks / ፎቶ እና ማስታወሻ")
            up_img = st.file_uploader("Upload Nursery Photo / የችግኝ ጣቢያውን ፎቶ ይጫኑ", type=['jpg', 'png', 'jpeg'])
            rem = st.text_area("General Remarks / አጠቃላይ አስተያየት")

            if st.form_submit_button("Submit Data / መረጃውን መዝግብ"):
                def get_r(v, e, n): return f"{n}: {v-e:+}" if v != 0 and v != e else ""
                auto = " | ".join(filter(None, [get_r(g_s, 13, "Guava"), get_r(ge_s, 16, "Gesho"), get_r(l_s, 13, "Lemon"), get_r(gr_s, 16, "Grev")]))
                
                try:
                    new_rec = BackCheck(woreda=w, cluster=cl, kebele=k, tno_name=t, checker_fa_name=fa, 
                                       cbe_acc=acc, checker_phone=ph, fenced=fn, guava_beds=g_n, guava_length=g_l,
                                       guava_sockets=g_s, total_guava_sockets=g_n*g_s, gesho_beds=ge_n, 
                                       gesho_length=ge_l, gesho_sockets=ge_s, total_gesho_sockets=ge_n*ge_s,
                                       lemon_beds=l_n, lemon_length=l_l, lemon_sockets=l_s, total_lemon_sockets=l_n*l_s,
                                       grevillea_beds=gr_n, grevillea_length=gr_l, grevillea_sockets=gr_s, 
                                       total_grevillea_sockets=gr_n*gr_s, auto_remark=auto, general_remark=rem, 
                                       photo=process_photo(up_img))
                    db.add(new_rec); db.commit()
                    st.success("✅ Saved Successfully! / መረጃው በተሳካ ሁኔታ ተመዝግቧል!")
                except Exception as e:
                    st.error(f"Error / ስህተት: {e}")
        db.close()

    # --- PAGE 2: DATA VIEW ---
    elif st.session_state["page"] == "Data":
        if check_password():
            st.title("📊 Recorded Data / የተመዘገቡ መረጃዎች")
            db = SessionLocal()
            query = db.query(BackCheck)
            
            # Search Bar
            search = st.text_input("🔍 Search Kebele or FA / ቀበሌ ወይም FA ስም በመጠቀም ይፈልጉ")
            if search:
                query = query.filter((BackCheck.kebele.contains(search)) | (BackCheck.checker_fa_name.contains(search)))
            
            recs = query.all()
            if recs:
                # ZIP and CSV Buttons
                buf = BytesIO()
                with zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
                    for r in recs:
                        if r.photo: zf.writestr(f"ID_{r.id}_{r.kebele}.jpg", base64.b64decode(r.photo))
                
                c1, c2 = st.columns(2)
                c1.download_button("🖼️ Photo ZIP / ፎቶዎችን አውርድ", buf.getvalue(), "photos.zip", use_container_width=True)
                df = pd.DataFrame([r.__dict__ for r in recs])
                if 'photo' in df.columns: df.drop(columns=['_sa_instance_state', 'photo'], inplace=True)
                c2.download_button("📥 Excel Data / መረጃውን አውርድ (CSV)", df.to_csv(index=False), "data.csv", use_container_width=True)

                st.markdown("---")
                for r in recs:
                    with st.container(border=True):
                        col_t, col_i = st.columns([3, 1])
                        col_t.subheader(f"📍 {r.kebele} (ID: {r.id})")
                        col_t.write(f"**FA:** {r.checker_fa_name} | **Status / ሁኔታ:** {r.auto_remark}")
                        col_t.info(f"**Notes / ማስታወሻ:** {r.general_remark}")
                        if r.photo: col_i.image(base64.b64decode(r.photo), caption="Nursery Photo")
                        if st.button(f"🗑️ Delete Record {r.id} / መረጃውን አጥፋ", key=f"d_{r.id}"):
                            db.delete(r); db.commit(); st.rerun()
            else:
                st.info("No records found. / ምንም መረጃ አልተገኘም።")
            db.close()

if __name__ == "__main__": main()
