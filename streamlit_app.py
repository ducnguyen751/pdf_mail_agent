import os, tempfile
import streamlit as st
from rag_processor import process_pdf
from db_client import find_users_by_roles
from mailer import send_email_sync

st.set_page_config(page_title='PDF Email Sender', layout='wide')
if 'history' not in st.session_state:
    st.session_state['history'] = []

st.title('📄 Automated PDF Email Sender')
file = st.file_uploader('Upload PDF', type=['pdf'])

if file:
    with tempfile.NamedTemporaryFile(delete=False,suffix='.pdf') as tmp:
        tmp.write(file.read())
        pdf_path = tmp.name

    st.info('Processing PDF...')
    summary, roles = process_pdf(pdf_path)

    st.subheader('📑 Summary')
    st.markdown(summary)
    st.subheader('👥 Identified Roles')
    st.write(roles)

    users = find_users_by_roles(roles)
    if not users:
        st.warning('No matching users found.')
    else:
        st.subheader('✉️ Sending Emails')
        for u in users:
            subject = f"[Notification] New Doc: {os.path.basename(pdf_path)}"
            body = f"Hello {u.get('name',u['email'])},\n\n{summary}\n\n-- End --"
            try:
                #send_email_sync(u['email'], subject, body, pdf_path)
                status = 'Success'
            except Exception as e:
                status = f'Failed: {e}'
            rec = {'email':u['email'],'role':u['role'],'status':status,'subject':subject,'body':body}
            st.session_state['history'].append(rec)

    # Cleanup
    os.remove(pdf_path)

# Display history
if st.session_state['history']:
    st.subheader('🕘 Email Send History')
    df = []
    for rec in st.session_state['history']:
        df.append({'Email':rec['email'],'Role':rec['role'],'Status':rec['status'],'Subject':rec['subject']})
    st.table(df)
    for rec in st.session_state['history']:
        with st.expander(f"{rec['email']} - {rec['status']}"):
            st.markdown(f"**Subject:** {rec['subject']}\n\n**Body:**\n{rec['body']}")