import streamlit as st

st.set_page_config(page_title="My App", page_icon="📱")

st.title("📱 Xin chào từ Android App!")

# Ô nhập tên
name = st.text_input("Nhập tên của bạn:")

# Nút bấm gửi
if st.button("Gửi"):
    if name:
        st.success(f"Chào bạn, {name}!")
    else:
        st.warning("Vui lòng nhập tên trước khi gửi.")
