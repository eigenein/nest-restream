#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime
from itertools import count
from time import sleep

from click import command, option
from loguru import logger
from requests import RequestException, Session

URL = "https://upload.youtube.com/closedcaption"


@command(context_settings={"max_content_width": 120})
@option("-c", "--cid", required=True, show_envvar=True)
@option("-f", "--datetime-format", default="%H:%M:%S", required=True, show_envvar=True, show_default=True)
def main(*, cid: str, datetime_format: str):
    """Sends the current date and time to YouTube in closed captions."""
    logger.info("Starting…")
    session = Session()
    for seq in count(start=1):
        caption = f"{datetime.utcnow().isoformat(timespec='milliseconds')}\n{datetime.now():{datetime_format}}\n"
        with session.post(
            URL,
            headers={"Content-Type": "text/plain"},
            data=caption.encode("utf-8"),
            params={"cid": cid, "seq": seq},
        ) as response:
            try:
                response.raise_for_status()
            except RequestException:
                logger.error("{}", response.text)
        sleep(1.0)


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stderr,
        colorize=True,
        format="<level>{message}</level>",
        backtrace=True,
        diagnose=True,
    )
    main(auto_envvar_prefix="STREAM_KEEPER")
