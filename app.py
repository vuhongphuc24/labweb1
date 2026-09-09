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
API_URL = "https://script.google.com/macros/s/AKfycbxHhYwbsX0rztBik_Er6hVgy-VbUsh_qUSl1QS4c2gRaYDJvDEhIwgmLkTgTNenK2n2/exec"  # <-- Giữ nguyên link Apps Script của bạn
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

# Hàm làm sạch định dạng ngày hiển thị (chuẩn Việt Nam DD/MM/YYYY)
def format_display_date(date_raw):
    if not date_raw:
        return ""
    date_str = str(date_raw).strip()
    # Nếu bị dính format GMT dài từ Google Sheet
    if "GMT" in date_str:
        try:
            # Tách lấy phần ngày tháng năm
            dt = datetime.strptime(date_str[:15], "%a %b %d %Y")
            return dt.strftime("%d/%m/%Y")
        except Exception:
            pass
    # Nếu là dạng YYYY-MM-DD
    if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except Exception:
            pass
    return date_str

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
with st.expander(f"✍️ Viết trang nhật ký hôm nay ({current_user})", expanded=True):
    col_d, col_m = st.columns([1, 1])
    with col_d:
        entry_date = st.date_input("Ngày:", datetime.now(vn_tz).date(), format="DD/MM/YYYY")
    with col_m:
        mood_options = [
            "🥰 Hạnh phúc", 
            "😊 Vui", 
            "🥺 Buồn", 
            "❤️ Yêu", 
            "🙅‍♂️ Không cho dỗi", 
            "🙅‍♀️ Không cho ghét", 
            "✏️ Tự nhập..."
        ]
        selected_mood = st.selectbox("Tâm trạng hôm nay:", mood_options)
    
    final_mood = selected_mood
    if selected_mood == "✏️ Tự nhập...":
        custom_mood = st.text_input("Gõ tâm trạng của bạn vào đây:")
        if custom_mood.strip():
            final_mood = f"✨ {custom_mood.strip()}"
            
    entry_title = st.text_input("Tiêu đề hôm nay:", placeholder="Ví dụ: Một buổi tối thật dịu dàng...")
    entry_content = st.text_area("Hôm nay của bạn có gì đặc biệt không?", height=120)
    uploaded_img = st.file_uploader("📸 Ảnh kỷ niệm hôm nay:", type=["png", "jpg", "jpeg"])
    
    if st.button("Lưu trang nhật ký", use_container_width=True):
        if entry_content.strip() or uploaded_img:
            with st.spinner("Đang lưu bài viết vào Google Sheet..."):
                img_str = process_image(uploaded_img)
                # Lưu ngày chuẩn định dạng Việt Nam DD/MM/YYYY
                formatted_date_save = entry_date.strftime("%d/%m/%Y")
                now_str = datetime.now(vn_tz).strftime("%H:%M:%S, %d/%m/%Y")
                
                title_to_save = entry_title.strip() if entry_title.strip() else "Không có tiêu đề"
                
                ok = post_entry({
                    "action": "add_diary",
                    "author": current_user,
                    "date": formatted_date_save,
                    "mood": final_mood,
                    "title": title_to_save,
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

# Hàm hiển thị danh sách dạng hộp bấm sổ ra (expander)
def render_list(entries, is_mine):
    if not entries:
        st.caption("Chưa có bài viết nào.")
        return
    for item in reversed(entries):
        disp_date = format_display_date(item.get('date'))
        mood = item.get('mood', '')
        title = item.get('title', 'Không có tiêu đề')
        
        # Tiêu đề thanh bấm: Hiện Ngày - Tâm trạng - Tiêu đề
        expander_title = f"🗓️ {disp_date} | {mood} | 📌 {title}"
        
        with st.expander(expander_title, expanded=False):
            if item.get('content'):
                st.write(item.get('content'))
            im = item.get('image_data', '')
            if im and im.startswith("data:image"):
                st.image(im, use_container_width=True)
            st.caption(f"🕒 Đã lưu lúc: {item.get('created_at')}")

# Cột của mình
with col_my:
    st.markdown(f"### 🌸 Nhật ký của tôi ({current_user})")
    render_list(my_data.get("diaries", []), is_mine=True)

# Cột của đối phương
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
