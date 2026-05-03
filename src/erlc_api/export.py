from __future__ import annotations

import csv
import html
import io
import json
from pathlib import Path
from typing import Any

from . import _utility as u


def _flat_rows(data: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in u.rows(data):
        converted = u.model_dict(item)
        if isinstance(converted, dict):
            converted = {key: value for key, value in converted.items() if key not in {"raw", "extra"}}
            out.append(converted)
        else:
            out.append({"value": converted})
    return out


def _columns(rows: list[dict[str, Any]], requested: list[str] | None = None) -> list[str]:
    if requested is not None:
        return requested
    seen: list[str] = []
    for row in rows:
        for key in row:
            if key not in seen:
                seen.append(key)
    return seen


def _cell(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False)
    return value


class Exporter:
    """Export models/lists to lightweight text formats, with optional XLSX."""

    def __init__(self, data: Any) -> None:
        self.data = data

    def json(self, *, indent: int | None = 2) -> str:
        return json.dumps(u.model_dict(self.data), indent=indent, ensure_ascii=False, default=str)

    def csv(self, *, columns: list[str] | None = None) -> str:
        rows = _flat_rows(self.data)
        cols = _columns(rows, columns)
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _cell(value) for key, value in row.items()})
        return stream.getvalue()

    def markdown(self, *, columns: list[str] | None = None) -> str:
        rows = _flat_rows(self.data)
        cols = _columns(rows, columns)
        if not cols:
            return ""
        lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
        for row in rows:
            lines.append("| " + " | ".join(str(_cell(row.get(col, ""))).replace("|", "\\|") for col in cols) + " |")
        return "\n".join(lines)

    def html(self, *, columns: list[str] | None = None) -> str:
        rows = _flat_rows(self.data)
        cols = _columns(rows, columns)
        head = "".join(f"<th>{html.escape(str(col))}</th>" for col in cols)
        body = []
        for row in rows:
            body.append("<tr>" + "".join(f"<td>{html.escape(str(_cell(row.get(col, ''))))}</td>" for col in cols) + "</tr>")
        return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"

    def xlsx(self, path: str | Path, *, sheet_name: str = "data", columns: list[str] | None = None) -> Path:
        try:
            from openpyxl import Workbook
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("XLSX export requires `pip install erlc-api[export]`.") from exc

        rows = _flat_rows(self.data)
        cols = _columns(rows, columns)
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name
        ws.append(cols)
        for row in rows:
            ws.append([_cell(row.get(col, "")) for col in cols])
        target = Path(path)
        wb.save(target)
        return target


__all__ = ["Exporter"]
