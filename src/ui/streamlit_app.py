import streamlit as st
import requests
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="Trợ Lý Phân Tích Số Liệu",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Trợ Lý Phân Tích Số Liệu Kinh Doanh")
st.caption("Tải file Excel/CSV lên và đặt câu hỏi bằng tiếng Việt tự nhiên.")

API_URL = "http://localhost:8000/api"

if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.header("📁 Tải dữ liệu")
    uploaded_file = st.file_uploader(
        "Chọn file Excel hoặc CSV",
        type=["xlsx", "xls", "csv", "tsv"],
        help="Hỗ trợ file Excel (.xlsx, .xls) và CSV/TSV",
    )

    if uploaded_file and st.button("📤 Tải lên & Phân tích"):
        with st.spinner("Đang đọc dữ liệu..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                resp = requests.post(f"{API_URL}/upload", files=files)
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.session_id = data["session_id"]
                    st.success(f"✅ Đã tải: {data['file_name']}")
                    st.json(data["schemas"])
                else:
                    st.error(resp.json().get("detail", "Lỗi tải file"))
            except Exception as e:
                st.error(f"Không kết nối được API: {e}")

st.header("💬 Đặt câu hỏi")
question = st.text_input(
    "Bạn muốn biết điều gì?",
    placeholder="VD: Tháng vừa rồi mặt hàng nào bán chạy nhất?",
)

col1, col2 = st.columns([1, 5])
with col1:
    ask_button = st.button("🔍 Phân tích", type="primary")

if ask_button and question and st.session_state.session_id:
    with st.spinner("Đang phân tích..."):
        try:
            resp = requests.post(
                f"{API_URL}/analyze",
                json={"session_id": st.session_state.session_id, "question": question},
            )
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.chat_history.append({
                    "question": question,
                    "response": data,
                })

                if data.get("chart_html"):
                    st.components.v1.html(data["chart_html"], height=400)
                if data.get("narrative"):
                    st.markdown(f"### 📝 Phân tích\n{data['narrative']}")
                if data.get("recommendation"):
                    st.info(data["recommendation"])
                if data.get("error"):
                    st.warning(f"⚠️ {data['error']}")
            else:
                st.error(resp.json().get("detail", "Lỗi phân tích"))
        except Exception as e:
            st.error(f"Không kết nối được API: {e}")

if st.session_state.chat_history:
    st.header("📜 Lịch sử")
    for i, chat in enumerate(reversed(st.session_state.chat_history)):
        with st.expander(f"Q: {chat['question'][:80]}..."):
            st.json(chat["response"])

st.divider()
st.caption("NonTech Data Analyst Agent — v0.1.0")
