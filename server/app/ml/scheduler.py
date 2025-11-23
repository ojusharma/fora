"""
Background scheduler for ML training tasks.

This service runs ML training and update tasks in the background
using APScheduler (Advanced Python Scheduler).
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import asyncio

from app.ml.training import MLTrainingService

logger = logging.getLogger(__name__)


class MLSchedulerService:
    """Background scheduler for ML training tasks."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.training_service = MLTrainingService()
        self.is_running = False
    
    def _run_daily_tasks(self):
        """Wrapper to run daily training tasks."""
        try:
            logger.info("=== Starting scheduled daily ML training ===")
            asyncio.run(self.training_service.compute_user_similarity_matrix())
            asyncio.run(self.training_service.update_user_feature_vectors())
            logger.info("=== Daily ML training complete ===")
        except Exception as e:
            logger.error(f"Error in daily training: {e}", exc_info=True)
    
    def _run_hourly_tasks(self):
        """Wrapper to run hourly update tasks."""
        try:
            logger.info("=== Starting scheduled hourly updates ===")
            asyncio.run(self.training_service.update_engagement_scores())
            logger.info("=== Hourly updates complete ===")
        except Exception as e:
            logger.error(f"Error in hourly updates: {e}", exc_info=True)
    
    def _run_frequent_tasks(self):
        """Wrapper to run frequent update tasks."""
        try:
            logger.info("=== Starting scheduled frequent updates ===")
            asyncio.run(self.training_service.refresh_trending_listings_view())
            logger.info("=== Frequent updates complete ===")
        except Exception as e:
            logger.error(f"Error in frequent updates: {e}", exc_info=True)
    
    def start(self):
        """Start the background scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting ML background scheduler...")
        
        # Daily training at 2 AM
        self.scheduler.add_job(
            self._run_daily_tasks,
            CronTrigger(hour=2, minute=0),
            id='daily_training',
            name='Daily ML Training',
            replace_existing=True
        )
        
        # Hourly updates
        self.scheduler.add_job(
            self._run_hourly_tasks,
            IntervalTrigger(hours=1),
            id='hourly_updates',
            name='Hourly ML Updates',
            replace_existing=True
        )
        
        # Frequent updates every 15 minutes
        self.scheduler.add_job(
            self._run_frequent_tasks,
            IntervalTrigger(minutes=15),
            id='frequent_updates',
            name='Frequent ML Updates',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info("ML Scheduler started successfully")
        logger.info(f"Next daily training: {self.scheduler.get_job('daily_training').next_run_time}")
        logger.info(f"Next hourly update: {self.scheduler.get_job('hourly_updates').next_run_time}")
        logger.info(f"Next frequent update: {self.scheduler.get_job('frequent_updates').next_run_time}")
    
    def stop(self):
        """Stop the background scheduler."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        logger.info("Stopping ML background scheduler...")
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("ML Scheduler stopped")
    
    def get_status(self):
        """Get scheduler status and job information."""
        if not self.is_running:
            return {
                "status": "stopped",
                "jobs": []
            }
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "status": "running",
            "jobs": jobs
        }


# Global scheduler instance
_ml_scheduler = None


def get_ml_scheduler() -> MLSchedulerService:
    """Get or create the global ML scheduler instance."""
    global _ml_scheduler
    if _ml_scheduler is None:
        _ml_scheduler = MLSchedulerService()
    return _ml_scheduler


def start_ml_scheduler():
    """Start the ML scheduler (called on app startup)."""
    scheduler = get_ml_scheduler()
    scheduler.start()


def stop_ml_scheduler():
    """Stop the ML scheduler (called on app shutdown)."""
    scheduler = get_ml_scheduler()
    scheduler.stop()
