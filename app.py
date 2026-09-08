import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pytz

st.set_page_config(page_title="Nhật Ký Chúng Mình", page_icon="💌", layout="wide")

# --- 1. KẾT NỐI SUPABASE ---
SUPABASE_URL = "https://vexrprlxrudebjrwpsex.supabase.co/rest/v1/"    # Thay URL của bạn
SUPABASE_KEY = "sb_secret_VYZAz3JsQMWCaj3L2qtaGw_4FCxsKgv"                     # Thay anon public key của bạn
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')

@st.cache_resource
def get_db() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_db()

# --- 2. TỰ NHẬN DIỆN QUA MẬT KHẨU ---
PASSWORDS = {
    "pass_cua_a_123": "User A",
    "pass_cua_b_456": "User B"
}

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# Màn hình đăng nhập
if not st.session_state.logged_in_user:
    st.title("🔒 Cánh Cửa Nhật Ký")
    st.caption("Nhập mật khẩu bí mật của bạn:")
    pwd = st.text_input("Mật khẩu:", type="password")
    
    if st.button("Mở cửa", use_container_width=True):
        if pwd in PASSWORDS:
            identified_user = PASSWORDS[pwd]
            st.session_state.logged_in_user = identified_user
            
            # Cập nhật thời gian vào xem
            now_vn = datetime.now(vn_tz).strftime("%H:%M:%S, %d/%m/%Y")
            supabase.table("views_log").upsert({
                "user_name": identified_user,
                "last_viewed": now_vn
            }).execute()
            
            st.rerun()
        else:
            st.error("Mật khẩu không đúng!")
    st.stop()

# --- 3. GIAO DIỆN CHÍNH ---
current_user = st.session_state.logged_in_user
partner = "User B" if current_user == "User A" else "User A"

h_left, h_right = st.columns([4, 1])
with h_left:
    st.title(f"📖 Góc nhỏ của {current_user}")
with h_right:
    if st.button("Đăng xuất"):
        st.session_state.logged_in_user = None
        st.rerun()

# Lấy thời gian đối phương xem lần cuối
res_view = supabase.table("views_log").select("last_viewed").eq("user_name", partner).execute()
last_view = res_view.data[0]["last_viewed"] if res_view.data else "Chưa có dữ liệu"
st.info(f"👀 **{partner}** đã vào đọc lần cuối lúc: **{last_view}**")

# --- 4. FORM VIẾT BÀI HÀNG NGÀY ---
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
                supabase.table("diaries").insert({
                    "date": str(entry_date),
                    "author": current_user,
                    "mood": mood,
                    "title": entry_title,
                    "content": entry_content
                }).execute()
                st.success("Đã lưu trang nhật ký thành công!")
                st.rerun()
            else:
                st.warning("Nội dung không được để trống!")

st.divider()

# --- 5. HIỂN THỊ 2 CỘT NHẬT KÝ ---
st.subheader("📚 Nhật ký của chúng mình")
col_a, col_b = st.columns(2)

def render_column(user_name, target_col):
    with target_col:
        st.markdown(f"### 💌 Nhật ký của {user_name}")
        records = supabase.table("diaries").select("*").eq("author", user_name).order("id", desc=True).execute().data
        if records:
            for row in records:
                with st.chat_message("user" if user_name == "User A" else "assistant"):
                    st.markdown(f"**🗓️ Ngày: {row['date']}** — {row['mood']}")
                    if row.get('title'):
                        st.markdown(f"**📌 {row['title']}**")
                    st.write(row['content'])
        else:
            st.caption("Chưa có bài viết nào.")

render_column("User A", col_a)
render_column("User B", col_b)
