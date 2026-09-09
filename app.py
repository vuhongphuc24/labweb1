import streamlit as st
import requests
import json
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime
import pytz

st.set_page_config(page_title="Nhật Ký Chúng Mình", page_icon="💌", layout="wide")

# --- 1. CẤU HÌNH API LINK ---
API_URL = "https://script.google.com/macros/s/AKfycbxHhYwbsX0rztBik_Er6hVgy-VbUsh_qUSl1QS4c2gRaYDJvDEhIwgmLkTgTNenK2n2/exec"  # <-- Dán link Apps Script vào đây
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')

@st.cache_data(ttl=3)
def fetch_data():
    try:
        res = requests.get(API_URL, timeout=15)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {"passwords": {}, "data_lan": {}, "data_phuc": {}}

def send_peek(viewer, target_user, time_str):
    try:
        requests.get(API_URL, params={
            "action": "peek_partner",
            "viewer": viewer,
            "target_user": target_user,
            "time": time_str
        }, timeout=15)
    except Exception:
        pass

def post_entry(payload):
    try:
        res = requests.post(
            API_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            allow_redirects=True,
            timeout=25
        )
        return res.status_code == 200
    except Exception as e:
        st.error(f"Lỗi gửi bài: {e}")
        return False

def process_image(uploaded_file):
    if not uploaded_file:
        return ""
    img = Image.open(uploaded_file).convert("RGB")
    img.thumbnail((750, 750))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

# --- 2. ĐĂNG NHẬP ---
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if "unlock_partner" not in st.session_state:
    st.session_state.unlock_partner = False

data = fetch_data()
passwords_dict = data.get("passwords", {})

if not st.session_state.logged_in_user:
    st.title("🔒 Cánh Cửa Nhật Ký")
    st.caption("Nhập mật khẩu cá nhân của bạn để mở cửa:")
    pwd_in = st.text_input("Mật khẩu:", type="password")
    
    if st.button("Mở cửa", use_container_width=True):
        if pwd_in in passwords_dict:
            st.session_state.logged_in_user = passwords_dict[pwd_in]
            st.session_state.unlock_partner = False
            st.rerun()
        else:
            st.error("Mật khẩu không trùng khớp với bất kỳ file nào!")
    st.stop()

# --- 3. MÀN HÌNH CHÍNH ---
current_user = st.session_state.logged_in_user
partner = "Phuc iu" if current_user == "Moc Lan iu" else "Moc Lan iu"

my_data = data.get("data_lan", {}) if current_user == "Moc Lan iu" else data.get("data_phuc", {})
partner_data = data.get("data_phuc", {}) if current_user == "Moc Lan iu" else data.get("data_lan", {})

h1, h2 = st.columns([4, 1])
with h1:
    st.title(f"📖 Góc riêng của {current_user} ✨")
with h2:
    if st.button("Đăng xuất"):
        st.session_state.logged_in_user = None
        st.session_state.unlock_partner = False
        st.rerun()

last_peek = my_data.get("last_peek", "Chưa xem lần nào")
st.info(f"👀 **{partner}** đã vào đọc nhật ký của bạn lần cuối lúc: **{last_peek}**")

# Form viết bài trực tiếp
with st.expander(f"✍️ Viết nhật ký hôm nay ({current_user})", expanded=True):
    with st.form("diary_form", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            entry_date = st.date_input("Ngày:", datetime.now(vn_tz).date())
        with c2:
            mood = st.selectbox("Tâm trạng:", ["🥰 Hạnh phúc", "😊 Bình yên", "🥺 Nhớ bạn", "😴 Mệt mỏi", "😤 Dỗi"])
            
        entry_title = st.text_input("Tiêu đề:")
        entry_content = st.text_area("Hôm nay của bạn có gì đặc biệt không?", height=120)
        uploaded_img = st.file_uploader("📸 Ảnh kỷ niệm hôm nay:", type=["png", "jpg", "jpeg"])
        
        if st.form_submit_button("Lưu trang nhật ký", use_container_width=True):
            if entry_content.strip() or uploaded_img:
                with st.spinner("Đang lưu bài viết..."):
                    img_str = process_image(uploaded_img)
                    now_str = datetime.now(vn_tz).strftime("%H:%M:%S, %d/%m/%Y")
                    ok = post_entry({
                        "action": "add_diary",
                        "author": current_user,
                        "date": str(entry_date),
                        "mood": mood,
                        "title": entry_title,
                        "content": entry_content,
                        "image_data": img_str,
                        "created_at": now_str
                    })
                    if ok:
                        st.cache_data.clear()
                        st.success("Đã ghi thành công vào file Sheet của bạn!")
                        st.rerun()
                    else:
                        st.error("Có lỗi khi ghi vào Google Sheet!")
            else:
                st.warning("Vui lòng nhập nội dung hoặc chọn ảnh!")

st.divider()

# --- 4. BỐ CỤC 2 CỘT HIỂN THỊ ---
col_my, col_other = st.columns(2)

def render_list(entries, is_mine):
    if not entries:
        st.caption("Chưa có bài viết nào.")
        return
    for item in reversed(entries):
        with st.chat_message("user" if is_mine else "assistant"):
            st.markdown(f"**🗓️ Ngày: {item.get('date')}** — {item.get('mood')}")
            if item.get('title'):
                st.markdown(f"**📌 {item.get('title')}**")
            if item.get('content'):
                st.write(item.get('content'))
            im = item.get('image_data', '')
            if im and im.startswith("data:image"):
                st.image(im, use_container_width=True)
            st.caption(f"Đã lưu lúc: {item.get('created_at')}")

# Cột của mình (luôn hiển thị bài trong file của mình)
with col_my:
    st.markdown(f"### 🌸 Nhật ký của tôi ({current_user})")
    render_list(my_data.get("diaries", []), is_mine=True)

# Cột của đối phương (bắt buộc nhập mật khẩu peek + ghi nhận log)
with col_other:
    st.markdown(f"### 🔐 Nhật ký của {partner}")
    if not st.session_state.unlock_partner:
        st.warning(f"File nhật ký của {partner} đang được khóa bảo vệ.")
        st.caption("⚠️ Bạn cần nhập đúng mật khẩu đọc của người ấy. Khi mở thành công, hệ thống sẽ ghi nhận mốc thời gian để báo cho đối phương!")
        
        peek_pwd_input = st.text_input(f"Nhập mật khẩu đọc nhật ký của {partner}:", type="password", key="peek_pwd_key")
        
        if st.button("🔓 Mở khóa đọc nhật ký", use_container_width=True):
            expected_peek_pwd = partner_data.get("peek_password", "")
            
            if not expected_peek_pwd:
                st.error("Đối phương chưa thiết lập mật khẩu đọc trong Sheet!")
            elif peek_pwd_input == expected_peek_pwd:
                now_str = datetime.now(vn_tz).strftime("%H:%M:%S, %d/%m/%Y")
                send_peek(viewer=current_user, target_user=partner, time_str=now_str)
                st.session_state.unlock_partner = True
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Mật khẩu đọc không chính xác!")
    else:
        if st.button("🔒 Đóng lại", use_container_width=True):
            st.session_state.unlock_partner = False
            st.rerun()
        render_list(partner_data.get("diaries", []), is_mine=False)
