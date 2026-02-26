# Stranzit Audio Downloader

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/FUYOH666/voip-calls-downloader)

**Automated system for monitoring and downloading new audio calls from the [lk.stranzit.ru](https://lk.stranzit.ru/Account) personal dashboard.**

---

## Overview

Stranzit Audio Downloader is a tool for automatically downloading call records from the Svyaztransit personal dashboard. The project helps eliminate manual routine work, saving time and energy.

---

## Problems It Solves

- **Manual record downloads** — no need to manually log into the dashboard and download files
- **New call tracking** — automatic monitoring and downloading of new records
- **File duplication** — automatic tracking of already downloaded records
- **Filtering** — configurable filters by direction, duration, and other parameters

---

## Features

- ✅ Real-time monitoring of incoming calls
- ✅ Automatic download of new records
- ✅ Readable filenames in format: `DD.MM.YYYY_HH-MM-SS_NUMBER_DIRECTION.mp3`
- ✅ Tracking of downloaded files (no duplication)
- ✅ Secure credential handling via environment variables
- ✅ Health check and system status monitoring
- ✅ Automatic restart on failures
- ✅ Cron support for automatic startup
- ✅ Configurable filters by direction and duration

---

## Requirements

- **Python 3.12** or higher
- **uv** - Python package manager (install: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Linux** or **macOS** (Windows not supported)
- Internet access
- Credentials for logging into lk.stranzit.ru dashboard

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
cd svyaztransit
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

Copy the example settings file:

```bash
cp .env.example .env
```

### Step 2: Edit .env file

Open the `.env` file in any text editor and fill in:

- `STRANZIT_USERNAME` - your login for the dashboard
- `STRANZIT_PASSWORD` - your password

### Step 3: Additional settings

If needed, configure other parameters:
- Check interval (`CHECK_INTERVAL`)
- Record filters (`CALL_FILTER_*`)
- Download folder (`DOWNLOAD_DIR`)

See the `.env.example` file for detailed descriptions of all parameters.

---

## Usage

### One-time run

Execute one check for new calls and exit:

```bash
uv run call_records_watcher.py --once
```

### Continuous operation mode

Start the program in continuous monitoring mode:

```bash
uv run call_records_watcher.py
```

### Health check (system status check)

```bash
uv run call_records_watcher.py --health
```

Or use a separate script:

```bash
uv run health_check.py
```

The program will check for new calls every 5 minutes (or another interval specified in `.env`). Press `Ctrl+C` to stop.

### Using launch script

```bash
./run_watcher.sh
```

The script will automatically:
- Check for uv presence
- Sync dependencies via `uv sync`
- Check for .env file presence
- Start watcher

### Automatic startup via cron

To run the program automatically in the background, configure cron:

```bash
./setup_cron.sh
```

The script will prompt you to choose a check interval (every minute, every 5 minutes, or every 10 minutes).

---

## Acceptance Testing

After installation and configuration, verify that everything works correctly:

### 1. Configuration check

Run health check to verify configuration:

```bash
uv run call_records_watcher.py --health
```

Should output:
- ✅ Status: healthy
- ✅ All checks (database, download_dir, disk_space, stranzit_auth) in "ok" status

### 2. Test run

Run a one-time check:

```bash
uv run call_records_watcher.py --once
```

Check:
- Successful authentication in logs
- Presence of new records (if any)
- No errors

### 3. Check downloaded files

```bash
ls -lh downloads/
```

MP3 files should appear.

### 4. Check database

```bash
sqlite3 stranzit_calls.db "SELECT COUNT(*) as total_files FROM downloaded_records;"
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

## Usage Examples

### Example 1: One-time download of today's calls

1. Configure `.env`:
   ```bash
   CALL_FILTER_START=today_start
   CALL_FILTER_END=now
   CALL_FILTER_DIRECTION=incoming
   ```

2. Run:
   ```bash
   uv run call_records_watcher.py --once
   ```

### Example 2: Download all incoming calls longer than 3 minutes

1. Configure `.env`:
   ```bash
   CALL_FILTER_DIRECTION=incoming
   CALL_FILTER_DURATION_OP=>=
   CALL_FILTER_DURATION=00:03:00
   ```

2. Run in continuous mode:
   ```bash
   uv run call_records_watcher.py
   ```

---

## Parameter Settings

All settings are in the `.env` file. Main parameters:

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `DOWNLOAD_DIR` | `./downloads` | Folder for saving files |
| `CHECK_INTERVAL` | `300` | Check interval in seconds (5 minutes) |
| `CALL_FILTER_START` | `today_start` | Start of period for searching calls |
| `CALL_FILTER_END` | `now` | End of period for searching calls |
| `CALL_FILTER_DIRECTION` | `incoming` | Call direction (`incoming`, `outgoing`, `any`) |
| `CALL_FILTER_DURATION_OP` | `>=` | Duration filter operator |
| `CALL_FILTER_DURATION` | `00:03:00` | Duration value in HH:MM:SS format |

See the `.env.example` file for detailed descriptions of all parameters.

---

## Project Structure

```
svyaztransit/
├── call_records_watcher.py   # Main downloader script
├── stranzit_auth.py          # Authentication module
├── config.py                 # Configuration module (pydantic-settings)
├── health_check.py           # System status check script
├── auto_restart.py          # Automatic restart script
├── pyproject.toml           # Dependencies and project metadata
├── uv.lock                  # Pinned dependency versions
├── .env.example             # Example settings file
├── run_watcher.sh           # Launch script for cron
├── setup_cron.sh            # Automatic startup setup script
└── README.md                # This instruction
```

---

## Security

- Login and password are stored only in the `.env` file, which should not be committed to git
- Passwords are never logged or transmitted to third parties
- The `.env` file is added to `.gitignore` for security
- Never commit `.env` files to the repository

---

## Troubleshooting

### Error ".env file not found"

**Solution:** Make sure you copied `.env.example` to `.env`:
```bash
cp .env.example .env
```

### Error "uv not installed"

**Solution:** Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via pip:
```bash
pip install uv
```

### Error "Credentials not set"

**Solution:** Check that the `.env` file exists and contains `STRANZIT_USERNAME` and `STRANZIT_PASSWORD`.

**Important:** When using pydantic-settings, configuration is validated at startup. On validation errors, the application will exit with a clear error message.

### Error "Login error"

**Solution:** Check the correctness of login and password in the `.env` file. Make sure you have internet access and the lk.stranzit.ru site is accessible.

Run health check for diagnostics:
```bash
uv run call_records_watcher.py --health
```

### Configuration validation error

**Solution:** When using pydantic-settings, all parameters are validated at startup. Check:
1. Format of values in `.env` (numbers should be numbers, boolean values - true/false)
2. Required parameters are filled
3. Values are in valid ranges (e.g., `CHECK_INTERVAL >= 60`)

### Files not downloading

**Possible reasons:**
- No free disk space
- `downloads/` folder doesn't exist or is not writable
- No new calls in the specified period

**Solution:**
- Check for free disk space
- Make sure the `downloads/` folder exists and is writable
- Check logs: `tail -f watcher.log`
- Run health check: `uv run call_records_watcher.py --health`

### Program won't start

**Solution:**
- Make sure uv is installed: `uv --version`
- Check dependency sync: `uv sync`
- Check Python version: `python3 --version` (should be 3.12 or higher)
- Check for `pyproject.toml` file

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

## Important Notes

1. Make sure usage complies with lk.stranzit.ru service rules
2. Use reasonable intervals between requests (minimum 5 minutes)
3. Regularly check for free disk space
4. Make backups of the `downloads/` folder and database

---

## Support

If problems occur, check:
1. Logs in the `watcher.log` file
2. Settings in the `.env` file
3. System status via `health_check.py`

---

## Contributing

We welcome any contribution! Please read [CONTRIBUTING.md](../CONTRIBUTING.md) in the repository root.

---

## License

This project is distributed under the MIT license. See [LICENSE](../LICENSE) for detailed information.

---

*Automated system for downloading audio calls from Stranzit personal dashboard*

