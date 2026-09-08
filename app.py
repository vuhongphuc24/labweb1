import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import pandas as pd

st.set_page_config(page_title="Nhật Ký Chúng Mình", page_icon="💌", layout="wide")

# --- 1. CẤU HÌNH LIÊN KẾT GOOGLE SHEET ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1f_0zYHTG-k3Gac_1ZZJ0ZAsl-mqKChCYYbnn4I772No/edit?usp=drive_link"  # <-- Dán link Sheet vào đây
vn_tz = pytz.timezone('Asia/Ha_Noi')

@st.cache_resource
def get_spreadsheet():
    # Sử dụng Google API thông qua tài khoản dịch vụ của gspread
    gc = gspread.public_sheet(SHEET_URL) if hasattr(gspread, "public_sheet") else gspread.Client(None)
    # Lưu ý: Nếu dùng gspread chuẩn mở công khai với link chia sẻ:
    return gspread.open_by_url(SHEET_URL)

try:
    sh = gspread.open_by_url(SHEET_URL)
    sheet_diaries = sh.worksheet("diaries")
    sheet_views = sh.worksheet("views_log")
except Exception:
    # Trường hợp kết nối qua gspread trực tiếp
    import gspread
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"]) if "gcp_service_account" in st.secrets else None
    if gc:
        sh = gc.open_by_url(SHEET_URL)
        sheet_diaries = sh.worksheet("diaries")
        sheet_views = sh.worksheet("views_log")

# --- 2. TÀI KHOẢN VÀ MẬT KHẨU ---
USERS = {
    "User A": "pass_a_123",
    "User B": "pass_b_123"
}

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# --- 3. MÀN HÌNH ĐĂNG NHẬP ---
if not st.session_state.logged_in_user:
    st.title("🔒 Cánh Cửa Nhật Ký")
    user_choice = st.selectbox("Bạn là ai?", list(USERS.keys()))
    pwd = st.text_input("Mật khẩu riêng tư:", type="password")
    
    if st.button("Vào đọc và viết"):
        if pwd == USERS.get(user_choice):
            st.session_state.logged_in_user = user_choice
            
            # Ghi lại thời gian vào xem
            now_vn = datetime.now(vn_tz).strftime("%H:%M:%S, %d/%m/%Y")
            try:
                cell = sheet_views.find(user_choice)
                sheet_views.update_cell(cell.row, 2, now_vn)
            except Exception as e:
                pass
            st.rerun()
        else:
            st.error("Sai mật khẩu rồi bạn ơi!")
    st.stop()

# --- 4. GIAO DIỆN CHÍNH ---
current_user = st.session_state.logged_in_user
partner = "User B" if current_user == "User A" else "User A"

header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.title(f"📖 Góc nhỏ của {current_user}")
with header_col2:
    if st.button("Đăng xuất"):
        st.session_state.logged_in_user = None
        st.rerun()

# Hiển thị thời gian đối phương xem lần cuối
try:
    cell_partner = sheet_views.find(partner)
    last_view = sheet_views.cell(cell_partner.row, 2).value or "Chưa vào lần nào"
except Exception:
    last_view = "Chưa có dữ liệu"

st.info(f"👀 **{partner}** đã vào đọc lần cuối lúc: **{last_view}**")

# --- 5. FORM VIẾT NHẬT KÝ HÀNG NGÀY ---
with st.expander("✍️ Viết nhật ký hôm nay", expanded=True):
    with st.form("diary_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns([2, 1])
        with f_col1:
            entry_date = st.date_input("Ngày:", datetime.now(vn_tz).date())
        with f_col2:
            mood = st.selectbox("Tâm trạng:", ["🥰 Hạnh phúc", "😊 Bình yên", "🥺 Nhớ bạn", "😴 Mệt mỏi", "😤 Dỗi"])
            
        entry_title = st.text_input("Tiêu đề ngày hôm nay:")
        entry_content = st.text_area("Kể chi tiết cho người kia nghe nhé:", height=130)
        
        btn_save = st.form_submit_button("Lưu trang nhật ký", use_container_width=True)
        if btn_save:
            if entry_content.strip():
                now_stamp = datetime.now(vn_tz).strftime("%H:%M:%S, %d/%m/%Y")
                # Thêm dòng mới vào Google Sheet: date, author, mood, title, content, created_at
                sheet_diaries.append_row([
                    str(entry_date),
                    current_user,
                    mood,
                    entry_title,
                    entry_content,
                    now_stamp
                ])
                st.success("Đã lưu vào trang tính thành công!")
                st.rerun()
            else:
                st.warning("Bạn chưa viết nội dung kìa!")

st.divider()

# --- 6. HIỂN THỊ 2 CỘT NHẬT KÝ ---
st.subheader("📚 Nhật ký song song")
col_a, col_b = st.columns(2)

# Đọc toàn bộ dữ liệu từ Sheet
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
                # Đảo ngược để bài mới nhất lên trên
                for _, row in user_entries.iloc[::-1].iterrows():
                    with st.chat_message("user" if user_name == "User A" else "assistant"):
                        st.markdown(f"**🗓️ Ngày: {row.get('date', '')}** — {row.get('mood', '')}")
                        if row.get('title'):
                            st.markdown(f"**📌 {row.get('title')}**")
                        st.write(row.get('content', ''))
                        st.caption(f"Đã lưu lúc: {row.get('created_at', '')}")
            else:
                st.caption("Chưa có trang nhật ký nào.")
        else:
            st.caption("Chưa có trang nhật ký nào.")

render_column("User A", col_a)
render_column("User B", col_b)
