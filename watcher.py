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
INPUT_DIR = os.getenv("INPUT_DIR")
ARCHIVE_DIR = os.getenv("ARCHIVE_DIR")

class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.lower().endswith('.pdf'):
            pdf_path = event.src_path
            logger.info(f"Detected new PDF: {pdf_path}")

            # RAG processing
            summary, roles = process_pdf(pdf_path)
            logger.info(f"Roles identified: {roles}")

            # MongoDB lookup
            users = find_users_by_roles(roles)
            logger.info(f"Found {len(users)} users to notify.")

            # Send email to each
            for user in users:
                to = user['email']
                try:
                    send_email_sync(
                        to=to,
                        subject=f"[Notification] New Document: {os.path.basename(pdf_path)}",
                        body=summary,
                        attachment_path=pdf_path
                    )
                    logger.info(f"Email sent to {to}")
                except Exception as e:
                    logger.error(f"Failed to send to {to}: {e}")

            # Archive processed PDF
            os.makedirs(ARCHIVE_DIR, exist_ok=True)
            dest = os.path.join(ARCHIVE_DIR, os.path.basename(pdf_path))
            os.rename(pdf_path, dest)
            logger.info(f"Archived PDF to {dest}")

if __name__ == '__main__':
    observer = Observer()
    handler = PDFHandler()
    observer.schedule(handler, INPUT_DIR, recursive=False)
    observer.start()
    logger.info("Watcher started.")
    observer.join()