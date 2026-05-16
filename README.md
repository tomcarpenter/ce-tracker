# CE Tracker - Local-first CE Tracking System

A self-contained, offline-first Streamlit application for tracking continuing education (CE) hours for LMHC and PMH-C compliance.

## Quick Start

### 1. First Time Setup
```bash
chmod +x run_app.sh setup.sh
./setup.sh
```

### 2. Run the App
```bash
./run_app.sh
```

Or manually:
```bash
source .venv/bin/activate
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`

## Architecture

**Data Model:**
- **Parquet** (`data/ce_records.parquet`) = Source of truth
- **Backup Folder** (`backup_data/` by default) = `ce_records.parquet` plus per-event folders
- **Certificates** = UUID-named local storage with SHA256 hashing
- **Audit Log** = Append-only change tracking

**Runtime:**
- Self-contained `.venv` (no system Python dependency)
- Fully offline (no cloud services)
- Single-user local app
- Mac-native (Intel + Apple Silicon compatible)

## Project Structure

```
ce_tracker/
├── app.py                      # Streamlit entry point
├── run_app.sh                  # One-click launcher
├── setup.sh                    # Optional manual setup
├── requirements.txt            # Pinned dependencies
├── .venv/                      # Isolated environment
├── pages/                      # Streamlit multipage app
│   ├── 01_Dashboard.py
│   ├── 02_Submission.py
│   ├── 03_Data_Viewer.py
│   ├── 04_Edit_Entry.py
│   └── 05_Settings.py
├── utils/                      # Core modules
│   ├── storage.py              # Local data + backup mirror
│   ├── compliance.py           # Cycle tracking
│   ├── hashing.py              # SHA256 verification
│   ├── sync.py                 # File mirroring
│   └── file_manager.py         # Certificate storage
├── data/
│   ├── ce_records.parquet      # Primary storage
│   └── audit_log.csv           # Append-only log
├── certificates/
│   ├── root/                   # Primary storage
│   ├── backup/                 # Mirror storage
│   └── metadata/               # Certificate metadata
└── backup_data/                # Backup mirror
    ├── ce_records.parquet
    ├── audit_log.csv
    └── events/
        └── ce_YYYY-MM-DD_Event_Name/
            ├── ce_YYYY-MM-DD_Event_Name.txt
            └── ce_YYYY-MM-DD_Event_Name.pdf
```

## Features

### Compliance Tracking
- **LMHC General**: 32 hours per 2-year cycle
- **Ethics**: 6 hours per 2-year cycle (counts toward LMHC General)
- **Roles**: 2 hours per 2-year cycle (counts toward LMHC General)
- **Suicide Prevention**: 6 hours per 6-year cycle
- **Equity**: 2 hours per 4-year cycle
- **PMH-C**: 12 hours per 2-year cycle

Submission categories are stored as independent 1/0 flags. Ethics and Roles cannot be selected on the same CE entry.

### Pages
1. **Dashboard** - Progress tracking with cycle progress bars
2. **Submission** - Add new CE entry with certificate upload
3. **Data Viewer** - Browse, filter, and search records
4. **Edit Entry** - Modify or delete existing entries
5. **Settings** - Configure cycles, backup locations, sync status

### Data Safety
- Write-to-Parquet-first pattern (rollback on failure)
- Automatic separate-folder backup mirror
- Append-only audit log
- Certificate hashing + UUID naming
- Per-event evidence folders in backup

## Dependencies

All dependencies are pinned for reproducibility:
- streamlit (UI framework)
- pandas (data manipulation)
- pyarrow (Parquet support)
- numpy (numerical operations)
- watchdog (file monitoring)
- python-dateutil (date handling)

## Usage Tips

### Setting Compliance Cycles
Visit Settings page to configure:
- LMHC cycle start date
- Suicide Prevention cycle start date
- Equity cycle start date
- PMH-C cycle start date

### Backup Configuration
- Choose a data backup folder with the Settings folder picker
- App automatically updates the backup after submissions, edits, and deletes
- Backup contains a parent Parquet file and an `events/` folder with one subfolder per CE event

### PMH-C Submissions
Get helper text and form link on Dashboard page:
- Generates reminder about date requirements
- Links to PMH-C JotForm
- Tracks submission deadlines

## Data Recovery

The backup folder keeps a copy of `ce_records.parquet` plus human-readable event folders for recovery/reference.

## Troubleshooting

### App won't start
```bash
# Clear cache and reinstall
rm -rf .venv
./setup.sh
./run_app.sh
```

### Virtual environment issues
```bash
# Manually activate
source .venv/bin/activate
pip install -r requirements.txt

# Then run
streamlit run app.py
```

### Data sync issues
- Visit Settings page
- Confirm the data backup folder path is available
- Save settings to refresh the automatic backup mirror

## Notes

- This is a single-user, local-first application
- All data stored locally in `data/` directory
- No external services required
- Requires Python 3.8+
- Mac-optimized but portable to Linux/Windows

## License

Private use - CE Tracking System
