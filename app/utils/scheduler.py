import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app.services.notifications import run_all_notifications
from app.services.backup import auto_backup

logger = logging.getLogger("scheduler")

scheduler = BackgroundScheduler()


def _run_notifications():
    db = SessionLocal()
    try:
        run_all_notifications(db)
        logger.info("Notification check completed")
    except Exception as e:
        logger.error(f"Notification error: {e}")
    finally:
        db.close()


def _run_backup():
    try:
        auto_backup()
        logger.info("Auto backup completed")
    except Exception as e:
        logger.error(f"Backup error: {e}")


def start_scheduler():
    # Run notifications every day at 7:00 and 20:00
    scheduler.add_job(_run_notifications, "cron", hour=7, minute=0, id="notifications_morning")
    scheduler.add_job(_run_notifications, "cron", hour=20, minute=0, id="notifications_evening")

    # Run backup every day at midnight
    scheduler.add_job(_run_backup, "cron", hour=0, minute=0, id="auto_backup")

    scheduler.start()
    logger.info("Scheduler started: notifications at 07:00/20:00, backup at 00:00")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
