![Python 3.9](https://img.shields.io/badge/python-3.9-blue)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This is a small toolbox to simplify re-streaming a [Google Nest Cam](https://store.google.com/product/nest_cam) to YouTube.

## High-level overview

- Set up a Google Cloud Platform project and [Device Access project](https://developers.google.com/nest/device-access/get-started)
- Set up `token-keeper.py` service unit
- Set up `stream-keeper.py` service unit
- Set up re-streaming service unit
- Set up `subtitles-sender.py` service unit (TODO)

## `token-keeper.py`

This is a simple service to keep a valid access token in a file. Basically, it [obtains a new token](https://developers.google.com/identity/protocols/oauth2/web-server#offline) as soon as old one expires.

To use it, you need a client ID, client secret, and a refresh token. See the [Quick Start Guide on Google Developers](https://developers.google.com/nest/device-access/get-started) to obtain them.

```text
Usage: token-keeper.py [OPTIONS]

  Google Device Access token refresh service.

  Implements https://developers.google.com/identity/protocols/oauth2/web-server#offline

Options:
  --client-id TEXT          [env var: TOKEN_KEEPER_CLIENT_ID;required]
  --client-secret TEXT      [env var: TOKEN_KEEPER_CLIENT_SECRET;required]
  --refresh-token TEXT      [env var: TOKEN_KEEPER_REFRESH_TOKEN;required]
  --access-token-file FILE  [env var: TOKEN_KEEPER_ACCESS_TOKEN_FILE;required]
  --help                    Show this message and exit.
```

### [systemd](https://en.wikipedia.org/wiki/Systemd) service

```ini
[Unit]
Description = Token Keeper
BindsTo = network-online.target
After = network.target network-online.target

[Install]
WantedBy = multi-user.target

[Service]
WorkingDirectory = /home/pi
StandardOutput = journal
StandardError = journal
Restart = always
User = pi
ExecStart = /home/pi/nest-restream/venv/bin/python /home/pi/nest-restream/token-keeper.py
Environment = "TOKEN_KEEPER_CLIENT_ID=<gcp-client-id>"
Environment = "TOKEN_KEEPER_CLIENT_SECRET=<gcp-client-secret>"
Environment = "TOKEN_KEEPER_REFRESH_TOKEN=<gcp-refresh-token>"
Environment = "TOKEN_KEEPER_ACCESS_TOKEN_FILE=/home/pi/access-token.txt"
```

## `stream-keeper.py`

This is a service to [generate an RSTP stream](https://developers.google.com/nest/device-access/traits/device/camera-live-stream#generatertspstream) and to [extend it](https://developers.google.com/nest/device-access/traits/device/camera-live-stream#extendrtspstream) periodically before it expires. It keeps a valid stream URL in a file that can be specified as `EnvironmentFile` in `systemd`.

Requires a valid access token from `token-keeper.py`.

```text
Usage: stream-keeper.py [OPTIONS]

  Keeps a valid RTSP stream URL.

Options:
  --access-token-file FILE  [env var: STREAM_KEEPER_ACCESS_TOKEN_FILE;required]
  --device-id TEXT          [env var: STREAM_KEEPER_DEVICE_ID;required]
  --project-id TEXT         Device Access project ID.  [env var: STREAM_KEEPER_PROJECT_ID;required]
  --stream-url-file FILE    [env var: STREAM_KEEPER_STREAM_URL_FILE;required]
  --help                    Show this message and exit.
```

### [systemd](https://en.wikipedia.org/wiki/Systemd) service

```ini
[Unit]
Description = Stream Keeper
BindsTo = network-online.target
After = network.target network-online.target

[Install]
WantedBy = multi-user.target

[Service]
WorkingDirectory = /home/pi
StandardOutput = journal
StandardError = journal
Restart = always
User = pi
ExecStart = /home/pi/nest-restream/venv/bin/python /home/pi/nest-restream/stream-keeper.py
Environment = "STREAM_KEEPER_ACCESS_TOKEN_FILE=/home/pi/access-token.txt"
Environment = "STREAM_KEEPER_DEVICE_ID=<device-id>"
Environment = "STREAM_KEEPER_PROJECT_ID=<device-access-project-id>"
Environment = "STREAM_KEEPER_STREAM_URL_FILE=/home/pi/stream-url.txt"
```

## Integrating with [`ffmpeg`](https://www.ffmpeg.org/)

### Example: re-streaming to YouTube

The stream URL changes every few minutes, thus I set `RestartSec = 0` to make restarts as quick as possible. This isn't perfect, of course, and I'd be happy to hear a better solution.

`${STREAM_KEEPER_STREAM_URL}` is being set in `stream-url.txt` by `stream-keeper.py`.

```ini
[Unit]
Description = Restream
BindsTo = network-online.target
After = network.target network-online.target

[Service]
WorkingDirectory = /home/pi
StandardOutput = journal
StandardError = journal
Restart = always
RestartSec = 0
TimeoutStopSec = 3
StartLimitInterval = 0
User = pi
EnvironmentFile = /home/pi/stream-url.txt
ExecStart = ffmpeg \
    -loglevel warning \
    -nostdin \
    -stats \
    -xerror \
    -thread_queue_size 256 \
    -fflags nobuffer \
    -rtsp_transport tcp \
    -stimeout 3000000 \
    -i ${STREAM_KEEPER_STREAM_URL} \
    -codec copy \
    -flags +cgop \
    -hls_time 2 \
    -hls_list_size 4 \
    -method PUT \
    -http_persistent 1 \
    'https://a.upload.youtube.com/http_upload_hls?cid=<cid>&copy=0&file=live.m3u8'

[Install]
WantedBy = multi-user.target
```
