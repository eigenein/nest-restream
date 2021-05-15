#!/usr/bin/env python3
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep

import click
from click import command, option
from loguru import logger
from requests import Session

TIME_MARGIN = timedelta(seconds=10)


@dataclass
class Token:
    access_token: str
    requested_at: datetime
    expires_at: datetime


@command(context_settings={"max_content_width": 120})
@option("--client-id", required=True, show_envvar=True)
@option("--client-secret", required=True, show_envvar=True)
@option("--refresh-token", required=True, show_envvar=True)
@option(
    "--access-token-file",
    type=click.Path(dir_okay=False, readable=False, writable=True, exists=False),
    required=True,
    show_envvar=True,
)
def main(*, client_id: str, client_secret: str, refresh_token: str, access_token_file: str):
    """
    Google Device Access token refresh service.

    Implements https://developers.google.com/identity/protocols/oauth2/web-server#offline
    """
    access_token_path = Path(access_token_file)
    session = Session()
    while True:
        logger.info("Obtaining a new token…")
        token = get_token(
            session=session,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
        )
        logger.info("Saving the token…")
        access_token_path.write_text(token.access_token)
        logger.info("Token updated. Valid until: {}.", token.expires_at)
        sleep((token.expires_at - token.requested_at - TIME_MARGIN).total_seconds())


def get_token(session: Session, *, client_id: str, client_secret: str, refresh_token: str) -> Token:
    requested_at = datetime.now()
    with session.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    ) as response:
        response.raise_for_status()
        payload = response.json()
        return Token(
            access_token=payload["access_token"],
            requested_at=requested_at,
            expires_at=(requested_at + timedelta(seconds=payload["expires_in"])),
        )


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stderr,
        colorize=True,
        format="<level>{message}</level>",
        backtrace=True,
        diagnose=True,
    )
    main(auto_envvar_prefix="TOKEN_KEEPER")
