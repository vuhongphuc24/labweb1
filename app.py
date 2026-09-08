import streamlit as st
import requests
from datetime import datetime
import pytz

st.set_page_config(page_title="Nhật Ký Chúng Mình", page_icon="💌", layout="wide")

# --- 1. CẤU HÌNH API GOOGLE SHEET ---
API_URL = "https://script.google.com/macros/library/d/1sde1cOlXiGwlJl-W4wTfs3Q26KET5tCsURSLrMxyKZJ6au04SelHsZYp/1"  # <-- Dán link Apps Script vào đây
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')

def load_data():
    try:
        res = requests.get(API_URL, timeout=10)
        return res.json()
    except Exception:
        return {"diaries": [], "views": {}}

def post_data(payload):
    try:
        requests.post(API_URL, json=payload, timeout=10)
    except Exception:
        pass

# --- 2. TỰ NHẬN DIỆN MẬT KHẨU ---
PASSWORDS = {
    "pass_cua_a_123": "User A",
    "pass_cua_b_456": "User B"
}

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# Màn hình đăng nhập
if not st.session_state.logged_in_user:
    st.title("🔒 Cánh Cửa Nhật Ký")
    st.caption("Nhập mật khẩu bí mật:")
    pwd = st.text_input("Mật khẩu:", type="password")
    
    if st.button("Mở cửa", use_container_width=True):
        if pwd in PASSWORDS:
            user = PASSWORDS[pwd]
            st.session_state.logged_in_user = user
            
            # Ghi nhận thời gian xem qua Google Apps Script
            now_vn = datetime.now(vn_tz).strftime("%H:%M:%S, %d/%m/%Y")
            post_data({
                "action": "update_view",
                "user": user,
                "time": now_vn
            })
            st.rerun()
        else:
            st.error("Mật khẩu không chính xác!")
    st.stop()

# --- 3. GIAO DIỆN CHÍNH ---
current_user = st.session_state.logged_in_user
partner = "User B" if current_user == "User A" else "User A"

db_data = load_data()
views_dict = db_data.get("views", {})

h_col1, h_col2 = st.columns([4, 1])
with h_col1:
    st.title(f"📖 Góc nhỏ của {current_user}")
with h_col2:
    if st.button("Đăng xuất"):
        st.session_state.logged_in_user = None
        st.rerun()

last_seen = views_dict.get(partner, "Chưa vào lần nào")
st.info(f"👀 **{partner}** đã vào đọc lần cuối lúc: **{last_seen}**")

# --- 4. FORM VIẾT NHẬT KÝ ---
with st.expander("✍️ Viết trang nhật ký hôm nay", expanded=True):
    with st.form("diary_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            entry_date = st.date_input("Ngày:", datetime.now(vn_tz).date())
        with col2:
            mood = st.selectbox("Tâm trạng:", ["🥰 Hạnh phúc", "😊 Bình yên", "🥺 Nhớ bạn", "😴 Mệt mỏi", "😤 Dỗi"])
            
        entry_title = st.text_input("Tiêu đề hôm nay:")
        entry_content = st.text_area("Hôm nay của bạn thế nào?", height=120)
        
        if st.form_submit_button("Lưu trang nhật ký", use_container_width=True):
            if entry_content.strip():
                now_str = datetime.now(vn_tz).strftime("%H:%M:%S, %d/%m/%Y")
                post_data({
                    "action": "add_diary",
                    "date": str(entry_date),
                    "author": current_user,
                    "mood": mood,
                    "title": entry_title,
                    "content": entry_content,
                    "created_at": now_str
                })
                st.success("Đã lưu vào Google Sheet!")
                st.rerun()
            else:
                st.warning("Nội dung không được để trống!")

st.divider()

# --- 5. HIỂN THỊ 2 CỘT NHẬT KÝ ---
st.subheader("📚 Nhật ký của chúng mình")
col_a, col_b = st.columns(2)

diaries = db_data.get("diaries", [])

def render_column(user_name, target_col):
    with target_col:
        st.markdown(f"### 💌 Nhật ký của {user_name}")
        user_entries = [d for d in diaries if d.get("author") == user_name]
        if user_entries:
            # Bài mới nhất hiển thị trên cùng
            for item in reversed(user_entries):
                with st.chat_message("user" if user_name == "User A" else "assistant"):
                    st.markdown(f"**🗓️ Ngày: {item.get('date')}** — {item.get('mood')}")
                    if item.get("title"):
                        st.markdown(f"**📌 {item.get('title')}**")
                    st.write(item.get("content"))
                    st.caption(f"Đã lưu lúc: {item.get('created_at')}")
        else:
            st.caption("Chưa có bài viết nào.")

render_column("User A", col_a)
render_column("User B", col_b)
