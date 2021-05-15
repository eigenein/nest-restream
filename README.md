![Python 3.9](https://img.shields.io/badge/python-3.9-blue)

This is a small toolbox to simplify re-streaming a [Google Nest Cam](https://store.google.com/product/nest_cam) to YouTube.

## `token-keeper.py`

This is a simple service to keep a working access token in a file. Basically, it [obtains a new token](https://developers.google.com/identity/protocols/oauth2/web-server#offline) as soon as old one expires.

To use it, you need a client ID, client secret, and a refresh token. See the [Quick Start Guide on Google Developers](https://developers.google.com/nest/device-access/get-started) to obtain them.

```text
❯ ./token-keeper.py --help
Usage: token-keeper.py [OPTIONS]

  Google Device Access token refresh service.

  Implements https://developers.google.com/identity/protocols/oauth2/web-server#offline.

Options:
  --client-id TEXT           [env var: TOKEN_KEEPER_CLIENT_ID;required]
  --client-secret TEXT       [env var: TOKEN_KEEPER_CLIENT_SECRET;required]
  --refresh-token-file FILE  [env var: TOKEN_KEEPER_REFRESH_TOKEN_FILE;required]
  --access-token-file FILE   [env var: TOKEN_KEEPER_ACCESS_TOKEN_FILE;required]
  --help                     Show this message and exit.
```

Typically, you run this in a [systemd](https://en.wikipedia.org/wiki/Systemd) service. Here's an example:

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

This is a service to [generate an RSTP stream](https://developers.google.com/nest/device-access/traits/device/camera-live-stream#generatertspstream) and to [extend it](https://developers.google.com/nest/device-access/traits/device/camera-live-stream#extendrtspstream) periodically before it expires.

TODO
