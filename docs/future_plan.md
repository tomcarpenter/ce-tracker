# Future Plan

## Product Direction

- Keep CE Tracker local-first and offline-capable.
- Preserve simple data ownership: records, certificates, settings, and backups should remain easy to locate and inspect.
- Make routine CE entry fast while keeping compliance categories explicit.

## Planned Improvements

- Package the app as a launchable macOS app or shortcut.
- Improve startup behavior so the user does not need to remember terminal commands.
- Add clearer empty states for first-time setup and missing data folders.
- Add an "add another submission" workflow from the Submission page after a successful save.
- Support attaching the app to an Azure cloud container for storage instead of writing only to the current local data folder.
- Keep export and backup formats human-readable where practical.
- Add focused regression tests for form validation and backup mirroring.

## UX Rules

- Do not fill in a default date for CE events.
- Require the user to intentionally choose the completed date for each new event.
- Keep edit forms prefilled from the existing record, since those values were already chosen.
- Warn before submitting an event dated today: "Are you sure you want to submit an event that occurred today? Please verify the date."
- Warn when submitting an event that shares the same date as an existing event.
