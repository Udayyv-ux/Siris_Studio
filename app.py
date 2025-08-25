import streamlit as st
from PIL import Image
import os
import json
import urllib.parse
from datetime import datetime
import uuid
# ------------------ SETTINGS ------------------
UPLOAD_DIR = "uploaded_clothes"
DATA_FILE = "clothes_data.json"
USERS_FILE = "users_data.json"
ORDERS_FILE = "orders_data.json"

ADMIN_USERNAME = "Udayyv"
ADMIN_PASSWORD = "Rohith"
WHATSAPP_NUMBER = "+918919349836"  # change to your number

os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="Siri's Studio", layout="wide")

# Hide Streamlit UI (no toolbar, menu, footer)
st.markdown(
    """
    <style>
      #MainMenu{visibility:hidden;}
      footer{visibility:hidden;}
      header{visibility:hidden;}
      [data-testid="stToolbar"]{visibility:hidden;}
      .stDeployButton{display:none;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("👗 Welcome to Siri's Studio")

# ------------------ UTILS ------------------
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def save_image_unique(uploaded_file) -> str:
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    unique = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, unique)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return unique

clothes = load_json(DATA_FILE, {})
users = load_json(USERS_FILE, {})
orders = load_json(ORDERS_FILE, {})

# ------------------ SESSION ------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.is_admin = False
    st.session_state.username = None
    st.session_state.phone = None

# ------------------ AUTH ------------------
if not st.session_state.logged_in:
    role = st.radio("Login as", ["User", "Admin"], index=0)

    if role == "Admin":
        with st.form("admin_login"):
            st.subheader("🔑 Admin Login")
            u = st.text_input("Admin ID")
            p = st.text_input("Password", type="password")
            ok = st.form_submit_button("Login")
            if ok:
                if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
                    st.session_state.logged_in = True
                    st.session_state.is_admin = True
                    st.session_state.username = ADMIN_USERNAME
                    st.success("✅ Logged in as Admin")
                    st.rerun()
                else:
                    st.error("❌ Invalid Admin credentials")
    else:
        with st.form("user_login"):
            st.subheader("👤 User Login")
            name = st.text_input("Your Name")
            phone = st.text_input("Mobile Number")
            ok = st.form_submit_button("Enter Store")
            if ok:
                if name.strip() and phone.strip():
                    st.session_state.logged_in = True
                    st.session_state.is_admin = False
                    st.session_state.username = name.strip()
                    st.session_state.phone = phone.strip()
                    users[str(datetime.now())] = {"name": name.strip(), "phone": phone.strip()}
                    save_json(USERS_FILE, users)
                    st.success(f"✅ Welcome, {name}!")
                    st.rerun()
                else:
                    st.error("❌ Please enter both name and mobile number")

else:
    # ------------------ AFTER LOGIN ------------------
    if st.button("🚪 Logout"):
        for k in ["logged_in", "is_admin", "username", "phone"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

    # ---------- ADMIN PANEL ----------
    if st.session_state.is_admin:
        with st.expander("🛠️ Admin Panel", expanded=False):
            st.subheader("➕ Add New Dress")
            with st.form("add_dress"):
                up = st.file_uploader("Upload dress image", type=["jpg", "jpeg", "png"])
                name = st.text_input("Dress Name")
                price = st.text_input("Price (e.g., ₹1499)")
                desc = st.text_area("Description")
                add_ok = st.form_submit_button("Add Dress")
                if add_ok:
                    if up and name.strip() and price.strip():
                        filename = save_image_unique(up)
                        clothes[filename] = {
                            "name": name.strip(),
                            "price": price.strip(),
                            "description": desc.strip(),
                        }
                        save_json(DATA_FILE, clothes)
                        st.success("✅ Dress added!")
                        st.rerun()
                    else:
                        st.error("❌ Please provide image, name, and price.")

            if clothes:
                st.markdown("---")
                del_choice = st.selectbox("Select a dress to delete", list(clothes.keys()), format_func=lambda f: clothes[f]["name"])
                if st.button("🗑️ Delete Selected Dress"):
                    try:
                        os.remove(os.path.join(UPLOAD_DIR, del_choice))
                    except FileNotFoundError:
                        pass
                    clothes.pop(del_choice, None)
                    save_json(DATA_FILE, clothes)
                    st.success("Deleted.")
                    st.rerun()

            st.subheader("📋 Users who viewed the store")
            if users:
                for t, info in sorted(users.items()):
                    st.markdown(f"- **{info.get('name','(unknown)')}** ({info.get('phone','n/a')}) at `{t}`")
            else:
                st.info("No viewers yet.")

    # ---------- STORE GRID ----------
    st.subheader("🛍️ Store Collection")

    if clothes:
        num_cols = 3
        cols = st.columns(num_cols)

        for i, (fname, meta) in enumerate(clothes.items()):
            with cols[i % num_cols]:
                img_path = os.path.join(UPLOAD_DIR, fname)
                if os.path.exists(img_path):
                    img = Image.open(img_path)
                    st.image(img, caption=meta["name"], use_container_width=True)

                st.markdown(f"**💰 Price:** {meta['price']}")
                if meta.get("description"):
                    st.markdown(f"**📝 Description:** {meta['description']}")

                msg = f"Hi, I want to order {meta['name']}.\\nPrice: {meta['price']}"
                if meta.get("description"):
                    msg += f"\\nDescription: {meta['description']}"
                encoded = urllib.parse.quote(msg)
                wa = f"https://wa.me/{WHATSAPP_NUMBER}?text={encoded}"
                st.markdown(f"[🛒 Order on WhatsApp]({wa})", unsafe_allow_html=True)
    else:
        st.info("No clothes uploaded yet.")
