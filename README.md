# FinnScraper

A minimal [Finn.no](https://www.finn.no/) web scraper. Educational and personal use only. WIP.

## Setup

Clone the repo and install dependencies:

```bash
pip install -r requirements.txt
```

Customize your search by creating a `.env` file:

```bash
WEBHOOK_URL=https://discord.com/api/webhooks/...
URL=https://www.finn.no/realestate/lettings/search.html?location=...
SCAN_INTERVAL = XXX (in seconds) 
REQUEST_TIMEOUT = XXX (in seconds)
```

Then run:

```bash
python main.py
```
