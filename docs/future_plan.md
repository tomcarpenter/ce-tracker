# Future Plan

## Product Direction

- Keep CE Tracker local-first and offline-capable.
- Preserve simple data ownership: records, certificates, settings, and backups should remain easy to locate and inspect.
- Make routine CE entry fast while keeping compliance categories explicit.

## Planned Improvements

- Package the app as a launchable macOS app or shortcut.
- Improve startup behavior so the user does not need to remember terminal commands.
- Package the app as a self-contained macOS app bundle that can be shared and launched normally on another Mac.
- Store packaged-app data in a stable macOS user data location, such as `~/Library/Application Support/CE Tracker`.
- Add a launcher that starts the local Streamlit server internally and opens the app in a browser or desktop-style window.
- Add app metadata, versioning, and a custom icon for the macOS app.
- Test the packaged app on a clean Mac user account before sharing.
- Consider Apple signing/notarization if the app needs a smoother install experience without macOS security warnings.
- Add clearer empty states for first-time setup and missing data folders.
- Add an "add another submission" workflow from the Submission page after a successful save.
- Support attaching the app to an Azure cloud container for storage instead of writing only to the current local data folder.
- Improve app speed by reducing repeated full-data reloads during Streamlit reruns.
- Add Streamlit caching for read-heavy data loading and derived dashboard calculations.
- Clear or refresh cached data only after submissions, edits, deletes, imports, or settings changes.
- Avoid rebuilding backup/export artifacts unless data has actually changed.
- Evaluate SQLite as the primary live data store, with Parquet and CSV retained as export or backup formats.
- Keep export and backup formats human-readable where practical.
- Add focused regression tests for form validation and backup mirroring.

## Dashboard Ideas

- Add an "in the last 6 years" dashboard view as an alternate way to track completed hours.
- Use speedometer-style gauges for the six-year view.
- Add alerts for upcoming compliance deadlines.

## UX Rules

- Do not fill in a default date for CE events.
- Require the user to intentionally choose the completed date for each new event.
- Keep edit forms prefilled from the existing record, since those values were already chosen.
- Warn before submitting an event dated today: "Are you sure you want to submit an event that occurred today? Please verify the date."
- Warn when submitting an event that shares the same date as an existing event.
