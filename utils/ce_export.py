"""Helpers for exporting CE records and certificate evidence bundles."""

from io import BytesIO
from pathlib import Path
import json
import re
import shutil
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd


def safe_filename(value: object) -> str:
    """Create a readable filesystem-safe filename segment."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("_")
    return cleaned or "untitled"


def ce_basename(record: pd.Series) -> str:
    """Build the canonical CE export basename: ce_DATE_EVENT."""
    date_value = pd.to_datetime(record.get("date", ""), errors="coerce")
    date_part = date_value.strftime("%Y-%m-%d") if not pd.isna(date_value) else "undated"
    title_part = safe_filename(record.get("title", "event"))
    return f"ce_{date_part}_{title_part}"


def certificate_path(record: pd.Series) -> Path | None:
    """Resolve the stored certificate path for a CE record."""
    stored_path = record.get("certificate_path", "")
    if not stored_path:
        return None

    path = Path(stored_path)
    if path.exists():
        return path

    fallback = Path("certificates/root") / path.name
    if fallback.exists():
        return fallback

    return None


def attachment_filename(certificate_path_value: str) -> str:
    """Return the original uploaded filename when metadata is available."""
    if not certificate_path_value:
        return ""

    path = Path(certificate_path_value)
    metadata_path = Path("certificates/metadata") / f"{path.stem}.json"

    if metadata_path.exists():
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            return metadata.get("original_filename") or path.name
        except Exception:
            return path.name

    return path.name


def has_attachment(certificate_path_value: str) -> bool:
    """Check whether a record points to an existing attachment file."""
    if not certificate_path_value:
        return False

    path = Path(certificate_path_value)
    return path.exists() or (Path("certificates/root") / path.name).exists()


def record_details_text(record: pd.Series) -> str:
    """Create a text details sheet for a CE record."""
    date_value = pd.to_datetime(record.get("date", ""), errors="coerce")
    completed = date_value.strftime("%Y-%m-%d") if not pd.isna(date_value) else ""
    certificate = certificate_path(record)
    original_filename = attachment_filename(record.get("certificate_path", ""))

    lines = [
        "CE Submission Details",
        "",
        f"Date completed: {completed}",
        f"Course/training title: {record.get('title', '')}",
        f"Trainer name: {record.get('trainer_name', '')}",
        f"Organization: {record.get('organization', '')}",
        f"CE hours: {record.get('hours', '')}",
        f"Categories: {record.get('category', '')}",
        f"Notes: {record.get('notes', '')}",
        "",
        f"Certificate attached: {'Yes' if certificate else 'No'}",
        f"Original certificate filename: {original_filename}",
        f"Stored certificate path: {record.get('certificate_path', '')}",
        f"Certificate SHA256: {record.get('certificate_hash', '')}",
        "",
        f"Record ID: {record.get('id', '')}",
        f"Created: {record.get('created_at', '')}",
        f"Updated: {record.get('updated_at', '')}",
    ]

    return "\n".join(lines).strip() + "\n"


def build_ce_zip(records: pd.DataFrame, folder_per_record: bool = False) -> tuple[bytes, int, int]:
    """
    Build a ZIP with CE detail sheets and attached certificate files.

    Returns: (zip bytes, records exported, certificate files exported)
    """
    buffer = BytesIO()
    record_count = 0
    file_count = 0
    used_names: set[str] = set()
    used_bases: set[str] = set()

    with ZipFile(buffer, "w", ZIP_DEFLATED) as zip_file:
        for _, record in records.iterrows():
            base = _unique_name(ce_basename(record), used_bases)
            folder = f"{base}/" if folder_per_record else ""

            txt_name = _unique_name(f"{folder}{base}.txt", used_names)
            zip_file.writestr(txt_name, record_details_text(record))
            record_count += 1

            cert_path = certificate_path(record)
            if cert_path:
                cert_name = _unique_name(f"{folder}{base}{cert_path.suffix}", used_names)
                zip_file.write(cert_path, cert_name)
                file_count += 1

    return buffer.getvalue(), record_count, file_count


def write_ce_folders(records: pd.DataFrame, destination_dir: Path) -> tuple[int, int]:
    """
    Write one folder per CE record with details text and certificate file.

    Returns: (records exported, certificate files exported)
    """
    destination_dir.mkdir(parents=True, exist_ok=True)
    record_count = 0
    file_count = 0
    used_bases: set[str] = set()

    for _, record in records.iterrows():
        base = _unique_name(ce_basename(record), used_bases)
        record_dir = destination_dir / base
        record_dir.mkdir(parents=True, exist_ok=True)

        (record_dir / f"{base}.txt").write_text(record_details_text(record), encoding="utf-8")
        record_count += 1

        cert_path = certificate_path(record)
        if cert_path:
            shutil.copy2(cert_path, record_dir / f"{base}{cert_path.suffix}")
            file_count += 1

    return record_count, file_count


def _unique_name(name: str, used_names: set[str]) -> str:
    """Avoid duplicate ZIP names when multiple records share date/title."""
    path = Path(name)
    candidate = name
    counter = 2

    while candidate in used_names:
        candidate = str(path.with_name(f"{path.stem}_{counter}{path.suffix}"))
        counter += 1

    used_names.add(candidate)
    return candidate
