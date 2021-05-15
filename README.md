![Python 3.9](https://img.shields.io/badge/python-3.9-blue)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This is a small toolbox to simplify re-streaming a [Google Nest Cam](https://store.google.com/product/nest_cam) to YouTube.

## High-level overview

- Set up a Google Cloud Platform project and [Device Access project](https://developers.google.com/nest/device-access/get-started)
- Set up `token-keeper.py` service
- Set up `stream-keeper.py` service
- Set up re-streaming service (for example, with [`ffmpeg`](https://www.ffmpeg.org/))

## `token-keeper.py`

This is a simple service to keep a valid access token in a file. Basically, it [obtains a new token](https://developers.google.com/identity/protocols/oauth2/web-server#offline) as soon as old one expires.

To use it, you need a client ID, client secret, and a refresh token. See the [Quick Start Guide on Google Developers](https://developers.google.com/nest/device-access/get-started) to obtain them.

```text
❯ ./token-keeper.py --help
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

Typically, you run this in a [systemd](https://en.wikipedia.org/wiki/Systemd) service.

### Example

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
Environment = "TOKEN_KEEPER_CLIENT_ID=<client-id>"
Environment = "TOKEN_KEEPER_CLIENT_SECRET=<client-secret>"
Environment = "TOKEN_KEEPER_REFRESH_TOKEN=<refresh-token>"
Environment = "TOKEN_KEEPER_ACCESS_TOKEN_FILE=/home/pi/access-token.txt"
```

## `stream-keeper.py`

This is a service to [generate an RSTP stream](https://developers.google.com/nest/device-access/traits/device/camera-live-stream#generatertspstream) and to [extend it](https://developers.google.com/nest/device-access/traits/device/camera-live-stream#extendrtspstream) periodically before it expires. It keeps a valid stream URL in a file.

Requires a valid access token from `token-keeper.py`.

TODO

### Example

TODO

## Integrating with [`ffmpeg`](https://www.ffmpeg.org/)

### Example: re-streaming to YouTube

```ini
TODO
```
