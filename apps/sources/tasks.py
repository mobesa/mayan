from __future__ import absolute_import

from datetime import timedelta, datetime
import platform
import logging

from django.db.models import Q

from job_processor.api import process_job
from lock_manager import Lock, LockError

from .models import POP3Email
from .conf.settings import POP3_TIMEOUT

logger = logging.getLogger(__name__)


def task_fetch_single_pop3_email(pop3_email):
    try:
        lock_id = u'task_fetch_pop3_email-%d' % pop3_email.pk
        logger.debug('trying to acquire lock: %s' % lock_id)
        lock = Lock.acquire_lock(lock_id, POP3_TIMEOUT + 60) # Lock expiration = POP3 timeout + 60 seconds
        logger.debug('acquired lock: %s' % lock_id)
        try:
            pop3_email.fetch_mail()
        except Exception, exc:
            raise
        finally:
            lock.release()
    except LockError:
        logger.error('unable to obtain lock')
        pass
    

def task_fetch_pop3_emails():
    logger.debug('executing')
    for pop3_email in POP3Email.objects.filter(enabled=True):
        try:
            task_fetch_single_pop3_email(pop3_email)
        except Exception, exc:
            logger.error('Unhandled exception: %s' % exc)