import streamlit as st
import gspread
from datetime import datetime
import pytz
import pandas as pd

st.set_page_config(page_title="Nhật Ký Chúng Mình", page_icon="💌", layout="wide")

# --- 1. CẤU HÌNH LIÊN KẾT GOOGLE SHEET ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit"  # <-- Dán link Google Sheet của bạn vào đây
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')

try:
    sh = gspread.open_by_url(SHEET_URL)
    sheet_diaries = sh.worksheet("diaries")
    sheet_views = sh.worksheet("views_log")
except Exception:
    # Hỗ trợ trường hợp kết nối qua Streamlit Secrets (nếu có cấu hình service account)
    if "gcp_service_account" in st.secrets:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_url(SHEET_URL)
        sheet_diaries = sh.worksheet("diaries")
        sheet_views = sh.worksheet("views_log")

# --- 2. TỰ ĐỘNG NHẬN DIỆN DANH TÍNH QUA MẬT KHẨU ---
# Đổi mật khẩu mong muốn ở đây (Mật khẩu: Tên người dùng tương ứng)
PASSWORDS = {
    "pass_cua_a_123": "User A",
    "pass_cua_b_456": "User B"
}

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# --- 3. MÀN HÌNH ĐĂNG NHẬP (KHÔNG HỎI TÊN, CHỈ NHẬP PASS) ---
if not st.session_state.logged_in_user:
    st.title("🔒 Cánh Cửa Nhật Ký")
    st.caption("Nhập mật khẩu bí mật của bạn để vào góc riêng:")
    
    pwd = st.text_input("Mật khẩu:", type="password")
    
    if st.button("Mở cửa", use_container_width=True):
        if pwd in PASSWORDS:
            identified_user = PASSWORDS[pwd]
            st.session_state.logged_in_user = identified_user
            
            # Tự động ghi nhận thời gian vừa mở xem
            now_vn = datetime.now(vn_tz).strftime("%H:%M:%S, %d/%m/%Y")
            try:
                cell = sheet_views.find(identified_user)
                sheet_views.update_cell(cell.row, 2, now_vn)
            except Exception:
                pass
            st.rerun()
        else:
            st.error("Mật khẩu không đúng rồi bạn ơi!")
    st.stop()

# --- 4. GIAO DIỆN CHÍNH KHI ĐÃ ĐĂNG NHẬP ---
current_user = st.session_state.logged_in_user
partner = "User B" if current_user == "User A" else "User A"

header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.title(f"📖 Góc nhỏ của {current_user}")
with header_col2:
    if st.button("Đăng xuất"):
        st.session_state.logged_in_user = None
        st.rerun()

# Lấy thời gian đối phương xem lần cuối từ tab views_log
try:
    cell_partner = sheet_views.find(partner)
    last_view = sheet_views.cell(cell_partner.row, 2).value or "Chưa vào lần nào"
except Exception:
    last_view = "Chưa có dữ liệu"

st.info(f"👀 **{partner}** đã vào đọc lần cuối lúc: **{last_view}**")

# --- 5. FORM VIẾT NHẬT KÝ HÀNG NGÀY ---
with st.expander("✍️ Viết trang nhật ký hôm nay", expanded=True):
    with st.form("diary_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns([2, 1])
        with f_col1:
            entry_date = st.date_input("Ngày:", datetime.now(vn_tz).date())
        with f_col2:
            mood = st.selectbox("Tâm trạng:", ["🥰 Hạnh phúc", "😊 Bình yên", "🥺 Nhớ bạn", "😴 Mệt mỏi", "😤 Dỗi"])
            
        entry_title = st.text_input("Tiêu đề hôm nay:")
        entry_content = st.text_area("Kể chi tiết ngày hôm nay nhé:", height=130)
        
        btn_save = st.form_submit_button("Lưu trang nhật ký", use_container_width=True)
        if btn_save:
            if entry_content.strip():
                now_stamp = datetime.now(vn_tz).strftime("%H:%M:%S, %d/%m/%Y")
                sheet_diaries.append_row([
                    str(entry_date),
                    current_user,
                    mood,
                    entry_title,
                    entry_content,
                    now_stamp
                ])
                st.success("Đã lưu trang nhật ký thành công!")
                st.rerun()
            else:
                st.warning("Nội dung nhật ký không được để trống!")

st.divider()

# --- 6. HIỂN THỊ 2 CỘT NHẬT KÝ SONG SONG ---
st.subheader("📚 Nhật ký của chúng mình")
col_a, col_b = st.columns(2)

try:
    records = sheet_diaries.get_all_records()
    df = pd.DataFrame(records)
except Exception:
    df = pd.DataFrame()

def render_column(user_name, placeholder):
    with placeholder:
        st.markdown(f"### 💌 Nhật ký của {user_name}")
        if not df.empty and 'author' in df.columns:
            user_entries = df[df['author'] == user_name]
            if not user_entries.empty:
                # Sắp xếp bài viết mới nhất lên trên
                for _, row in user_entries.iloc[::-1].iterrows():
                    with st.chat_message("user" if user_name == "User A" else "assistant"):
                        st.markdown(f"**🗓️ Ngày: {row.get('date', '')}** — {row.get('mood', '')}")
                        if row.get('title'):
                            st.markdown(f"**📌 {row.get('title')}**")
                        st.write(row.get('content', ''))
                        st.caption(f"Đã ghi lúc: {row.get('created_at', '')}")
            else:
                st.caption("Chưa có bài viết nào.")
        else:
            st.caption("Chưa có bài viết nào.")

render_column("User A", col_a)
render_column("User B", col_b)
