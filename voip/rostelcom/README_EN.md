# CloudPBX RT Calls Downloader

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/FUYOH666/voip-calls-downloader)

**Automatic call records downloader for CloudPBX Rostelecom. The system automatically downloads incoming call records longer than 3 minutes and saves them to a specified folder.**

---

## Overview

CloudPBX RT Calls Downloader is a tool for automatically downloading call records from CloudPBX Rostelecom. The project helps eliminate manual routine work, saving time and energy.

---

## Problems It Solves

- **Manual record downloads** — no need to manually log into CloudPBX dashboard and download files
- **Multiple accounts** — support for up to 16 accounts simultaneously
- **New call tracking** — automatic monitoring and downloading of new records
- **File duplication** — automatic tracking of already downloaded records
- **Filtering** — configurable filters by duration and call direction

---

## Features

- ✅ Automatic download of incoming call records
- ✅ Support for up to 16 accounts simultaneously (parallel processing)
- ✅ Filtering by call duration (configurable minimum)
- ✅ Automatic monitoring of new records
- ✅ Duplicate download protection (SQLite database)
- ✅ Configurable check intervals
- ✅ Detailed logging of all operations
- ✅ Auto-start via systemd (optional)

---

## Requirements

- **Python 3.12** (must be installed on the system)
- **uv** - Python package manager (install: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Linux** or **macOS** (Windows not supported)
- Credentials for CloudPBX Rostelecom access (login, password, domain)

---

## Installation

### Step 1: Install uv

If uv is not yet installed, install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via pip:
```bash
pip install uv
```

### Step 2: Prepare the project

```bash
cd rostelcom
```

### Step 3: Sync dependencies

```bash
uv sync
```

This command will automatically:
- Create a virtual environment (if it doesn't exist)
- Install all dependencies from `pyproject.toml`
- Create a `uv.lock` file with pinned versions

**Note:** The `uv.lock` file should be committed to the repository to ensure reproducible builds.

---

## Configuration

### Step 1: Create configuration file

Copy the example configuration:

```bash
cp .env.example .env
```

### Step 2: Edit .env file

Open the `.env` file in any text editor and fill in your data.

#### For a single account (simple mode):

```bash
CITY_1_NAME=Your_Account_Name
CITY_1_LOGIN=your_login
CITY_1_PASSWORD=your_password
CITY_1_DOMAIN=your_domain.rt.ru
```

#### For multiple accounts:

Fill in data for each account (from CITY_1 to CITY_16):

```bash
CITY_1_NAME=Account_Name_1
CITY_1_LOGIN=login1
CITY_1_PASSWORD=password1
CITY_1_DOMAIN=XXXXXX.XX.rt.ru

CITY_2_NAME=Account_Name_2
CITY_2_LOGIN=login2
CITY_2_PASSWORD=password2
CITY_2_DOMAIN=XXXXXX.XX.rt.ru

# ... and so on for all needed accounts
```

### Step 3: Configure download folder

In the `.env` file, find the line:

```bash
DOWNLOAD_DIR=./downloads
```

You can change the path to your own (absolute or relative).

---

## Usage

### Single account mode

**One-time run (test):**
```bash
uv run call_records_watcher.py --city-id 1 --once
```

**Continuous mode (check every 5 minutes):**
```bash
uv run call_records_watcher.py --city-id 1
```

**Health check (system status check):**
```bash
uv run call_records_watcher.py --city-id 1 --health
```

Press `Ctrl+C` to stop.

### Multiple accounts mode (recommended)

**One-time run (test):**
```bash
./run_multi_watcher.sh --once
```

**Continuous mode:**
```bash
./run_multi_watcher.sh
```

**Health check for all cities:**
```bash
./run_multi_watcher.sh --health
```

The script will automatically:
- Check for uv presence
- Sync dependencies via `uv sync`
- Check for .env file presence
- Start downloading for all configured accounts in parallel

Press `Ctrl+C` to stop.

---

## Acceptance Testing

After installation and configuration, verify that everything works correctly:

### 1. Configuration check

Run health check to verify configuration:

```bash
uv run call_records_watcher.py --city-id 1 --health
```

Should output:
- ✅ Status: healthy
- ✅ All checks (database, download_dir, cloudpbx_auth) in "ok" status

### 2. Test run

Run a one-time check:

```bash
uv run call_records_watcher.py --city-id 1 --once
```

Check:
- Successful authentication in logs
- Presence of new records (if any)
- No errors

### 3. Check downloaded files

```bash
ls -lh downloads/
```

MP3 files should appear with names like:
```
2025-01-15_14-30-45_79991234567_180sec.mp3
```

### 4. Check database

```bash
sqlite3 cloudpbx_calls.db "SELECT COUNT(*) as total_files FROM downloaded_records;"
```

### 5. Check logs

```bash
tail -f watcher.log
```

Logs should contain:
- Initialization information
- Successful authentication
- Information about found and downloaded records
- Log format with `pathname:lineno` for debugging

If all checks pass successfully — the system is ready to use!

---

## Additional Settings

All settings are in the `.env` file. Main parameters:

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `DOWNLOAD_DIR` | `./downloads` | Folder for saving MP3 files |
| `MIN_DURATION_SECONDS` | `180` | Minimum call duration (3 minutes) |
| `ONLY_INCOMING` | `true` | Only incoming calls |
| `CHECK_INTERVAL` | `300` | Interval for checking new calls (5 minutes) |
| `LOOKBACK_HOURS` | `24` | How far back to search for calls (24 hours) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

---

## Auto-start (optional)

If you want the system to start automatically on computer boot, you can configure auto-start via systemd.

### Create systemd service

Create file `/etc/systemd/system/cloudpbx-downloader.service`:

```bash
sudo nano /etc/systemd/system/cloudpbx-downloader.service
```

Insert the following content (replace `your_username` with your username and `/path/to/project` with the actual project path):

```ini
[Unit]
Description=CloudPBX RT Calls Downloader
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/project
ExecStart=/path/to/project/.venv/bin/python multi_account_downloader.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

### Activate service

```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudpbx-downloader
sudo systemctl start cloudpbx-downloader
```

### Check status

```bash
sudo systemctl status cloudpbx-downloader
```

### View logs

```bash
journalctl -u cloudpbx-downloader -f
```

---

## Project Structure

```
rostelcom/
├── cloudpbx_auth.py              # Authentication module
├── call_records_watcher.py        # Downloader for single account
├── multi_account_downloader.py    # Orchestrator for multiple accounts
├── config.py                      # Configuration module (pydantic-settings)
├── config.yaml                    # YAML configuration (reference)
├── pyproject.toml                 # Dependencies and project metadata
├── uv.lock                        # Pinned dependency versions
├── .env.example                   # Configuration example
├── run_multi_watcher.sh          # Launch script (multiple accounts)
├── run_watcher.sh                 # Launch script (single account)
├── tests/                         # Tests
└── README.md                      # This instruction
```

---

## Troubleshooting

### Error: ".env file not found"

**Solution:** Make sure you copied `.env.example` to `.env`:
```bash
cp .env.example .env
```

### Error: "uv not installed"

**Solution:** Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via pip:
```bash
pip install uv
```

### Error: "Required variables not set"

**Solution:** Check that all required fields are filled in the `.env` file:
- `CITY_N_NAME`
- `CITY_N_LOGIN`
- `CITY_N_PASSWORD`
- `CITY_N_DOMAIN`

Replace `N` with the account number (1, 2, 3, etc.).

**Important:** When using pydantic-settings, configuration is validated at startup. On validation errors, the application will exit with a clear error message.

### Error: "Authentication error"

**Solution:** Check:
1. Correctness of login and password
2. Correctness of domain (format: `XXXXXX.XX.rt.ru`)
3. Internet connection availability
4. Run health check: `uv run call_records_watcher.py --city-id 1 --health`

### Configuration validation error

**Solution:** When using pydantic-settings, all parameters are validated at startup. Check:
1. Format of values in `.env` (numbers should be numbers, boolean values - true/false)
2. Required parameters are filled
3. Values are in valid ranges (e.g., `CHECK_INTERVAL >= 60`)

### Files not downloading

**Possible reasons:**
1. No calls longer than 3 minutes in the last 24 hours
2. No incoming calls (if `ONLY_INCOMING=true` filter is enabled)
3. Calls were already downloaded earlier (checked via database)

**Solution:** Check settings in `.env`:
- `MIN_DURATION_SECONDS` - minimum duration (default 180 seconds = 3 minutes)
- `ONLY_INCOMING` - only incoming calls (default `true`)
- `LOOKBACK_HOURS` - how far back to search for calls (default 24 hours)

Run health check for diagnostics:
```bash
uv run call_records_watcher.py --city-id 1 --health
```

### Script won't start (permission denied)

**Solution:** Make the script executable:
```bash
chmod +x run_multi_watcher.sh
chmod +x run_watcher.sh
```

### Dependency sync error

**Solution:** 
1. Check for `pyproject.toml` file
2. Check Python version (should be 3.12)
3. Try deleting `.venv` and running `uv sync` again:
```bash
rm -rf .venv
uv sync
```

---

## Support

If problems occur, check:
1. Correctness of `.env` file filling
2. Logs (`*.log` files)
3. Internet connection availability
4. Python version (should be 3.12)

---

## Contributing

We welcome any contribution! Please read [CONTRIBUTING.md](../CONTRIBUTING.md) in the repository root.

---

## License

This project is distributed under the MIT license. See [LICENSE](../LICENSE) for detailed information.

---

**Ready to use!** The system automatically downloads call records and tracks already downloaded files to avoid downloading them again.

