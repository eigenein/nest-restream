#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from time import sleep
from typing import Annotated
from urllib.parse import ParseResult, parse_qs, urlencode, urlparse

import click
from click import command, option
from loguru import logger
from pydantic import BaseModel, Field
from requests import Session

TIME_MARGIN = timedelta(seconds=10)


class Stream(BaseModel):
    expires_at: Annotated[datetime, Field(alias="expiresAt")]
    extension_token: Annotated[str, Field(alias="streamExtensionToken")]
    token: Annotated[str, Field(alias="streamToken")]
    urls: Annotated[dict[str, str], Field(alias="streamUrls", default_factory=dict)]

    @property
    def url(self) -> str:
        try:
            return next(iter(self.urls.values()))
        except StopIteration as e:
            raise ValueError("no stream URLs") from e


@command(context_settings={"max_content_width": 120})
@option(
    "--access-token-file",
    type=click.Path(dir_okay=False, readable=True, writable=False, exists=True),
    required=True,
    show_envvar=True,
)
@option("--device-id", required=True, show_envvar=True)
@option("--project-id", required=True, show_envvar=True, help="Device Access project ID.")
@option(
    "--stream-url-file",
    type=click.Path(dir_okay=False, readable=False, writable=True),
    required=True,
    show_envvar=True,
)
def main(*, access_token_file: str, project_id: str, device_id: str, stream_url_file: str):
    """Keeps a valid RTSP stream URL."""
    access_token_path = Path(access_token_file)
    stream_url_path = Path(stream_url_file)
    command_url = (
        f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{project_id}/devices/{device_id}:executeCommand"
    )

    session = Session()

    logger.info("Generating initial stream URL…")
    stream = generate_stream(
        session,
        command_url=command_url,
        access_token=read_access_token(access_token_path),
    )
    logger.info("Obtained stream URL. Valid until: {}.", stream.expires_at.astimezone(tz=None))
    write_stream_url(stream_url_path, stream.url)
    stream_url: ParseResult = urlparse(stream.url)
    query: dict[str, list[str]] = parse_qs(stream_url.query)

    while True:
        sleep((stream.expires_at - datetime.now(tz=timezone.utc) - TIME_MARGIN).total_seconds())
        logger.info("Extending the stream…")
        stream = extend_stream(
            session,
            command_url=command_url,
            access_token=read_access_token(access_token_path),
            extension_token=stream.extension_token,
        )
        logger.info("Stream extended. Valid until: {}.", stream.expires_at.astimezone(tz=None))
        query["auth"] = [stream.token]
        stream_url = stream_url._replace(query=urlencode(query, doseq=True, safe="/"))
        write_stream_url(stream_url_path, stream_url.geturl())
        logger.info("URL file updated.")


def read_access_token(from_path: Path) -> str:
    return from_path.read_text().strip()


def write_stream_url(to_path: Path, url: str):
    to_path.write_text(url)


def generate_stream(session: Session, *, access_token: str, command_url: str) -> Stream:
    """
    https://developers.google.com/nest/device-access/traits/device/camera-live-stream#generatertspstream
    """
    with session.post(
        command_url,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"command": "sdm.devices.commands.CameraLiveStream.GenerateRtspStream"},
    ) as response:
        response.raise_for_status()
        return Stream.parse_obj(response.json()["results"])


def extend_stream(
    session: Session,
    *,
    command_url: str,
    access_token: str,
    extension_token: str,
) -> Stream:
    """
    https://developers.google.com/nest/device-access/traits/device/camera-live-stream#extendrtspstream
    """
    with session.post(
        command_url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "command": "sdm.devices.commands.CameraLiveStream.ExtendRtspStream",
            "params": {"streamExtensionToken": extension_token},
        },
    ) as response:
        response.raise_for_status()
        return Stream.parse_obj(response.json()["results"])


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
