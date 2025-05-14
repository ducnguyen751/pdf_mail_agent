import streamlit as st
import tempfile
import os
from rag_processor import process_pdf
from db_client import find_users_by_roles
from mailer import send_email_sync

st.set_page_config(page_title="Automated PDF Email Sender", layout="wide")

st.title("📄 Automated PDF Email Sender")
st.write("Upload a PDF, xem tóm tắt, danh sách roles, và kết quả gửi mail.")

file = st.file_uploader("Choose a PDF file", type=["pdf"])

if file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.read())
        pdf_path = tmp.name

    # RAG + display
    summary, roles = process_pdf(pdf_path)
    st.subheader("Tóm tắt nội dung PDF")
    st.markdown(summary)
    st.subheader("Vai trò/Phòng ban được xác định")
    st.write(roles)

    # Lookup & send
    users = find_users_by_roles(roles)
    if not users:
        st.warning("Không tìm thấy user phù hợp roles.")
    else:
        results = []
        for u in users:
            to = u['email']
            subject = f"[Notification] New Document: {os.path.basename(pdf_path)}"
            body = f"Hello {u.get('name', to)},\n\n{summary}\n\nPlease see attached PDF."
            try:
                send_email_sync(to, subject, body, pdf_path)
                status = "Success"
            except Exception as e:
                status = f"Failed: {e}"
            results.append({
                "email": to,
                "role": u['role'],
                "status": status,
                "preview": body[:100] + '...'
            })
        st.subheader("Kết quả gửi mail")
        st.table(results)

    os.remove(pdf_path)