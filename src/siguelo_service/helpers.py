from datetime import date as Date
from datetime import datetime as Datetime
from datetime import time as Time
from datetime import timedelta as Timedelta
from time import sleep

from loguru import logger


def wait_until_request_rate_is_renewed() -> None:
    today = Date.today()
    tomorrow = today + Timedelta(days=1)
    now = Datetime.now()
    hour = Time(6)
    target = Datetime.combine(tomorrow, hour)
    difference = target - now
    seconds = int(difference.total_seconds())
    logger.info(f"Waiting {seconds} seconds until request rate is renewed...")
    return sleep(seconds)
