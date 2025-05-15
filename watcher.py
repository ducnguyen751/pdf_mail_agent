import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
from rag_processor import process_pdf
from db_client import find_users_by_roles
from mailer import send_email_sync
from utils.logger import get_logger

load_dotenv()
logger = get_logger('watcher')
INPUT_DIR = os.getenv('INPUT_DIR')
ARCHIVE_DIR = os.getenv('ARCHIVE_DIR')

class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.lower().endswith('.pdf'):
            pdf_path = event.src_path
            logger.info(f"New PDF: {pdf_path}")
            summary, roles = process_pdf(pdf_path)
            users = find_users_by_roles(roles)
            for u in users:
                try:
                    send_email_sync(
                        to=u['email'],
                        subject=f"New Doc: {os.path.basename(pdf_path)}",
                        body=summary,
                        attachment_path=pdf_path
                    )
                    logger.info(f"Email sent to {u['email']}")
                except Exception as e:
                    logger.error(f"Fail to {u['email']}: {e}")
            os.makedirs(ARCHIVE_DIR, exist_ok=True)
            os.rename(pdf_path, os.path.join(ARCHIVE_DIR, os.path.basename(pdf_path)))
            logger.info(f"Archived {pdf_path}")

if __name__=='__main__':
    obs = Observer()
    obs.schedule(PDFHandler(), INPUT_DIR, False)
    obs.start()
    obs.join()