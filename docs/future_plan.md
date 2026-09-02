# Future Plan

## Product Direction

- Keep CE Tracker local-first and offline-capable.
- Preserve simple data ownership: records, certificates, settings, and backups should remain easy to locate and inspect.
- Make routine CE entry fast while keeping compliance categories explicit.
- Maintain one codebase and one repo, with development and production behavior selected by runtime configuration rather than separate app forks.
- Assume one active editor for the app; optimize for simple backup/restore rather than multi-editor real-time sync.

## Target Architecture

- Use SQLite as the primary local store for records, settings, audit log, certificate metadata, and other structured app data.
- Store certificate/PDF files as files on disk, referenced from SQLite by stable IDs/paths.
- Use Azure Blob primarily as a durable cloud backup destination for SQLite snapshots, certificate/PDF files, and portable exports.
- Keep Parquet and CSV as export or backup formats rather than the primary live data store.
- Avoid complex multi-device merge logic unless the app later needs multiple active editors.

## Local Data And SQLite

- Store production SQLite data outside the app bundle and outside the repo, using a stable macOS user data location such as `~/Library/Application Support/CE Tracker`.
- Keep app code replaceable and user data separate so app updates cannot overwrite production records or certificates.
- Store user-editable app settings inside the active data directory.
- Create an automatic backup before SQLite schema migrations.
- Version SQLite schema migrations so upgrades are repeatable and auditable.

## Development And Production

- Add explicit environment configuration via `CE_TRACKER_ENV`, with expected values such as `development` and `production`.
- Add explicit data-root configuration via environment variables or app config, such as `CE_TRACKER_DATA_DIR`.
- Make packaged production builds default to `~/Library/Application Support/CE Tracker`.
- Make local development default to a distinct development data directory, such as repo-local ignored `dev_data/` or `~/Library/Application Support/CE Tracker Dev`.
- Use temporary isolated data directories for automated tests.
- Keep sample/dummy seed data in the repo, but keep active dev data in gitignored `dev_data/`.
- Use dev seed data only through an intentional seed command or first-run dev setup.
- Resolve configuration at startup: read launch environment, choose data directory, create missing directories, open SQLite, load settings, then render pages.
- Add visible development labeling when the app is running against dev data.
- Add guardrails so migrations, destructive maintenance, and tests cannot accidentally run against production data.

## Launchers And Packaging

- Package the app as a self-contained macOS app bundle that can be shared and launched normally on another Mac.
- Add a launcher that starts the local Streamlit server internally and opens the app in a browser or desktop-style window.
- Have the packaged macOS launcher set `CE_TRACKER_ENV=production` and `CE_TRACKER_DATA_DIR="$HOME/Library/Application Support/CE Tracker"` before starting the app.
- Add a repo-local development launcher, such as `run_dev.sh`, that sets `CE_TRACKER_ENV=development` and `CE_TRACKER_DATA_DIR="./dev_data"` before starting Streamlit.
- Allow manual development launches from the terminal by setting those environment variables before `streamlit run app.py`.
- Improve startup behavior so the user does not need to remember terminal commands.
- Add app metadata, versioning, and a custom icon for the macOS app.
- Test the packaged app on a clean Mac user account before sharing.
- Consider Apple signing/notarization if the app needs a smoother install experience without macOS security warnings.

## Azure Cloud Backup

- Push cloud backups periodically in the background or after meaningful changes.
- Upload SQLite snapshots, certificate/PDF files, and portable exports to Azure Blob.
- Enable Azure Blob soft delete and blob versioning to protect against accidental local deletes, cloud deletes, and overwrites.
- Use timestamped cloud snapshots so previous app states can be restored after accidental deletion or bad edits.
- Add restore-from-cloud and pull-latest workflows.
- Allow multiple Macs to point at the same Azure container/prefix for shared family storage.
- Add cloud conflict checks before upload so one Mac does not silently overwrite newer data uploaded by another Mac.
- Track a device ID and last-synced cloud version/ETag for each Mac install.
- Assume an initial cloud storage ceiling around 200 MB, making Azure Blob storage cost operationally negligible under normal use.
- Prefer the Hot tier and LRS redundancy for simple family backup unless recovery requirements change.
- Add lifecycle rules for old versions and soft-deleted blobs, likely 90-180 days to start.
- Add a low Azure budget alert, such as $1/month or $5/month, to catch accidental misconfiguration.

## Azure Auth And Settings

- Define a private two-person permission model before shipping cloud backup.
- Keep the Azure container private with no anonymous public access.
- Avoid sharing Azure account keys; use scoped credentials with only the permissions the app needs.
- Prefer SAS tokens for the first private-family implementation.
- Store cloud credentials securely on each Mac, preferably in macOS Keychain in a later packaged-app version.
- Add Azure setup controls to the Settings page: enable/disable Azure, account URL, container name, prefix, SAS token, test connection, save, replace token, and disconnect.
- Let the app write Azure configuration from the Settings page into local configuration.
- Keep non-secret Azure settings in local JSON; decide whether the SAS token starts in local JSON or goes directly to macOS Keychain.
- If the SAS token is stored in local JSON, ensure that file is never committed, never uploaded to Azure backups, and never shown in full in the UI.
- Mask the saved SAS token in Settings and provide a deliberate replace-token flow.
- Validate the Azure connection after save and show whether the configured container is reachable.
- Warn if the SAS token is expired, near expiration, too broadly scoped, or includes delete permission.

## Performance Plan

- Optimize the app around fast local SQLite reads/writes first.
- Reduce repeated full-data reloads during Streamlit reruns.
- Add Streamlit caching for read-heavy data loading and derived dashboard calculations.
- Clear or refresh cached data only after submissions, edits, deletes, imports, or settings changes.
- Avoid rebuilding backup/export artifacts unless data has actually changed.

## Dashboard Improvements

- Add an "in the last 6 years" dashboard view as an alternate way to track completed hours.
- Use speedometer-style gauges for the six-year view.
- Add alerts for upcoming compliance deadlines.

## Submission UX

- Do not fill in a default date for CE events.
- Require the user to intentionally choose the completed date for each new event.
- Keep edit forms prefilled from the existing record, since those values were already chosen.
- Add an "add another submission" workflow from the Submission page after a successful save.
- Warn before submitting an event dated today: "Are you sure you want to submit an event that occurred today? Please verify the date."
- Warn when submitting an event that shares the same date as an existing event.
- Add clearer empty states for first-time setup and missing data folders.

## Testing And Safety

- Add focused regression tests for form validation and backup mirroring.
- Add tests for SQLite migrations and pre-migration backups.
- Add tests for dev/prod data-root resolution.
- Add tests for Azure configuration validation without requiring live Azure access.
