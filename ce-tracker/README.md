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
- **Parquet** (ce_records.parquet) = Source of truth
- **CSV** (ce_records.csv) = External mirror for compatibility
- **Certificates** = Dual storage (root + backup) with SHA256 hashing
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
│   ├── storage.py              # Parquet/CSV sync
│   ├── compliance.py           # Cycle tracking
│   ├── hashing.py              # SHA256 verification
│   ├── sync.py                 # File mirroring
│   └── file_manager.py         # Certificate storage
├── data/
│   ├── ce_records.parquet      # Primary storage
│   ├── ce_records.csv          # Mirror
│   └── audit_log.csv           # Append-only log
├── certificates/
│   ├── root/                   # Primary storage
│   ├── backup/                 # Mirror storage
│   └── metadata/               # Certificate metadata
└── backup_csv/                 # User-selected CSV destination
```

## Features

### Compliance Tracking
- **LMHC**: 40 hours per 2-year cycle
- **Suicide Prevention**: 6 hours per 6-year cycle
- **Equity**: 6 hours per 4-year cycle
- **PMH-C**: 60 hours per 2-year cycle

### Pages
1. **Dashboard** - Progress tracking with cycle progress bars
2. **Submission** - Add new CE entry with certificate upload
3. **Data Viewer** - Browse, filter, and search records
4. **Edit Entry** - Modify or delete existing entries
5. **Settings** - Configure cycles, backup locations, sync status

### Data Safety
- Write-to-Parquet-first pattern (rollback on failure)
- Startup reconciliation check (Parquet vs CSV)
- Append-only audit log
- Certificate hashing + UUID naming
- Dual-location backup

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
- Set external CSV backup folder (e.g., iCloud Drive)
- Set external certificate backup folder
- App automatically mirrors files during sync

### PMH-C Submissions
Get helper text and form link on Dashboard page:
- Generates reminder about date requirements
- Links to PMH-C JotForm
- Tracks submission deadlines

## Data Recovery

If conflicts occur:
1. App detects mismatch on startup
2. Shows reconciliation UI
3. Options:
   - **Safe**: Use Parquet (recommended)
   - **Recovery**: Use CSV (if Parquet corrupted)
   - View detailed row comparison

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
- Click "Force Reconciliation Check"
- Review reconciliation UI if needed

## Notes

- This is a single-user, local-first application
- All data stored locally in `data/` directory
- No external services required
- Requires Python 3.8+
- Mac-optimized but portable to Linux/Windows

## License

Private use - CE Tracking System
