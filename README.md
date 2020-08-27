# admissions-queue
Бот-очередь для приёмной комиссии ФИВТ

## Deployment:
Requirements: Python 3.7+ (tested on 3.8.5), MongoDB \
Optionally: Prometheus instance to gather stats, white static IP to use telegram webhook

## Environment variables

`BOT_TOKEN` - Telegram bot API token (required). \
`AAPI_HOST` - [Admission API host link](https://github.com/alexnzarov/fict-admissions-queue-api) (e.g. `https://api.hatomist.pw`, required). \
`AAPI_TOKEN` - Admission API bearer token (required). \
`WEBHOOK_HOST` - Telegram webhook link (optional, long polling will be used otherwise, but webhook is preferable). \
`WEBHOOK_PORT` - Telegram webhook port (optional).

## Web server configuration
This bot runs on specified by `WEBHOOK_PORT` (if any) and has `/webhook` and `/metrics` endpoints (for telegram webhook and prometheus metrics respectively). Web server is bound to localhost and is meant to be accessed via https enabled reverse proxy. This could be changed in `main.py`-s "\_\_main\_\_" section.

## Database configuration
This bot uses local MongoDB installation running on port 27017 by default and uses `users` collection in  `adm_queue` database. This could be changed in `db.py` file.
