"""
Scheduler for timed actions using APScheduler
Handles temporary bans, mutes, captcha timeouts, etc.
"""
import logging
from typing import Optional, Callable
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from utils.time_parser import now_utc

logger = logging.getLogger(__name__)


class SchedulerManager:
    """
    Manages scheduled jobs for timed actions
    """
    
    def __init__(self, database=None):
        """
        Initialize scheduler
        
        Args:
            database: Database instance for storing scheduled actions
        """
        self.db = database
        self.scheduler: Optional[AsyncIOScheduler] = None
        
        # Configure scheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
    
    async def start(self) -> None:
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✓ Scheduler started")
            
            # Load pending scheduled actions from database
            if self.db is not None:
                await self._load_scheduled_actions()
    
    async def shutdown(self) -> None:
        """Shutdown the scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("✓ Scheduler shut down")
    
    async def _load_scheduled_actions(self) -> None:
        """Load scheduled actions from database on startup"""
        try:
            if self.db is None:
                logger.debug("Database not configured, skipping scheduled actions load")
                return
            
            # Query database for pending actions
            pending_actions = await self.db.scheduled_actions.find({
                "execute_at": {"$gt": now_utc()}
            }).to_list(length=None)
            
            logger.info(f"Loading {len(pending_actions)} scheduled actions from database")
            
            # Import action handlers
            from core.scheduled_handlers import (
                execute_scheduled_unban,
                execute_scheduled_unmute,
                execute_scheduled_antiraid_disable
            )
            
            # Map action types to handler functions
            action_handlers = {
                'unban': execute_scheduled_unban,
                'unmute': execute_scheduled_unmute,
                'disable_antiraid': execute_scheduled_antiraid_disable
            }
            
            # Re-schedule each pending action
            scheduled_count = 0
            for action in pending_actions:
                action_type = action.get('action_type')
                execute_at = action.get('execute_at')
                chat_id = int(action.get('chat_id', 0))
                user_id = action.get('user_id')
                metadata = action.get('metadata', {})
                
                if action_type in action_handlers:
                    try:
                        # Create job ID
                        if user_id:
                            job_id = f"{action_type}_{chat_id}_{user_id}"
                        else:
                            job_id = f"{action_type}_{chat_id}"
                        
                        # Get handler function
                        handler = action_handlers[action_type]
                        
                        # Prepare kwargs for handler
                        handler_kwargs = {'chat_id': chat_id, 'db': self.db}
                        if user_id:
                            handler_kwargs['user_id'] = int(user_id)
                        if metadata:
                            handler_kwargs['metadata'] = metadata
                        
                        # Schedule the action
                        self.schedule_action(
                            job_id=job_id,
                            func=handler,
                            run_date=execute_at,
                            kwargs=handler_kwargs,
                            replace_existing=True
                        )
                        
                        scheduled_count += 1
                        logger.debug(f"Rescheduled {action_type} for chat {chat_id}" + 
                                   (f" user {user_id}" if user_id else ""))
                    
                    except Exception as e:
                        logger.error(f"Error rescheduling {action_type} action: {e}")
                else:
                    logger.warning(f"No handler found for action type: {action_type}")
            
            if scheduled_count > 0:
                logger.info(f"✓ Successfully rescheduled {scheduled_count} pending actions")
            
        except Exception as e:
            logger.error(f"Error loading scheduled actions: {e}")
    
    def schedule_action(
        self,
        job_id: str,
        func: Callable,
        run_date: datetime,
        args: tuple = (),
        kwargs: dict = None,
        replace_existing: bool = True
    ) -> bool:
        """
        Schedule a one-time action
        
        Args:
            job_id: Unique job identifier
            func: Function to execute
            run_date: When to execute
            args: Function positional arguments
            kwargs: Function keyword arguments
            replace_existing: Replace job if exists
            
        Returns:
            True if scheduled successfully
        """
        try:
            self.scheduler.add_job(
                func,
                'date',
                run_date=run_date,
                args=args,
                kwargs=kwargs or {},
                id=job_id,
                replace_existing=replace_existing
            )
            
            logger.debug(f"Scheduled job {job_id} for {run_date}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling job {job_id}: {e}")
            return False
    
    def cancel_action(self, job_id: str) -> bool:
        """
        Cancel a scheduled action
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancelled successfully
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.debug(f"Cancelled job {job_id}")
            return True
        except Exception as e:
            logger.debug(f"Could not cancel job {job_id}: {e}")
            return False
    
    def get_job(self, job_id: str):
        """Get job by ID"""
        return self.scheduler.get_job(job_id)
    
    def schedule_unban(
        self,
        chat_id: int,
        user_id: int,
        unban_func: Callable,
        duration: int
    ) -> str:
        """
        Schedule an unban action
        
        Args:
            chat_id: Chat ID
            user_id: User ID to unban
            unban_func: Function to call for unbanning
            duration: Duration in seconds
            
        Returns:
            Job ID
        """
        job_id = f"unban_{chat_id}_{user_id}"
        run_date = now_utc() + timedelta(seconds=duration)
        
        self.schedule_action(
            job_id=job_id,
            func=unban_func,
            run_date=run_date,
            args=(chat_id, user_id)
        )
        
        return job_id
    
    def schedule_unmute(
        self,
        chat_id: int,
        user_id: int,
        unmute_func: Callable,
        duration: int
    ) -> str:
        """
        Schedule an unmute action
        
        Args:
            chat_id: Chat ID
            user_id: User ID to unmute
            unmute_func: Function to call for unmuting
            duration: Duration in seconds
            
        Returns:
            Job ID
        """
        job_id = f"unmute_{chat_id}_{user_id}"
        run_date = now_utc() + timedelta(seconds=duration)
        
        self.schedule_action(
            job_id=job_id,
            func=unmute_func,
            run_date=run_date,
            args=(chat_id, user_id)
        )
        
        return job_id
    
    def schedule_captcha_timeout(
        self,
        chat_id: int,
        user_id: int,
        timeout_func: Callable,
        duration: int,
        context=None
    ) -> str:
        """
        Schedule a captcha timeout action
        
        Args:
            chat_id: Chat ID
            user_id: User ID
            timeout_func: Function to call on timeout
            duration: Duration in seconds
            context: Bot context (optional, passed to timeout_func)
            
        Returns:
            Job ID
        """
        job_id = f"captcha_timeout_{chat_id}_{user_id}"
        run_date = now_utc() + timedelta(seconds=duration)
        
        self.schedule_action(
            job_id=job_id,
            func=timeout_func,
            run_date=run_date,
            args=(chat_id, user_id, context) if context else (chat_id, user_id)
        )
        
    
    def schedule_periodic_permapin_check(
        self,
        check_func: Callable,
        context
    ) -> str:
        """
        Schedule periodic permapin check (every 5 minutes)
        
        Args:
            check_func: Function to call for checking
            context: Bot context
            
        Returns:
            Job ID
        """
        job_id = "periodic_permapin_check"
        
        # Schedule to run every 5 minutes
        self.scheduler.add_job(
            check_func,
            'interval',
            minutes=5,
            args=(context,),
            id=job_id,
            replace_existing=True
        )
        
        logger.info("Scheduled periodic permapin check (every 5 minutes)")
        return job_id
        return job_id
