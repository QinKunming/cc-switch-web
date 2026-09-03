"""Minimal TOML writer + parse helper.

Reads use the stdlib tomllib (Python 3.11+). Writes are always full
regenerations from a dict built by forms/presets, so a small deterministic
renderer is enough — no external dependency needed.

Supported value types: str / bool / int / float / list-of-scalars / nested dict
(rendered as [table] sections, dotted paths, quoted keys when needed).
"""
import json
import tomllib


def _fmt_key(key: str) -> str:
    """Bare key when possible, quoted (basic string) otherwise."""
    if key and all(c.isalnum() or c in "_-" for c in key):
        return key
    return json.dumps(key, ensure_ascii=False)


def _fmt_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, str):
        # JSON basic string escaping is a TOML basic string escaping subset
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        if not v:
            return "[]"
        return "[" + ", ".join(_fmt_value(x) for x in v) + "]"
    raise ValueError(f"Unsupported TOML value: {v!r}")


def _emit_table(out: list, path: list, table: dict) -> None:
    for k, v in table.items():
        if not isinstance(v, dict):
            continue
        sub_path = path + [k]
        out.append("[" + ".".join(_fmt_key(p) for p in sub_path) + "]")
        body = [f"{_fmt_key(ck)} = {_fmt_value(cv)}"
                for ck, cv in v.items() if not isinstance(cv, dict)]
        out.extend(body)
        if any(isinstance(cv, dict) for cv in v.values()):
            if body:
                out.append("")
            _emit_table(out, sub_path, v)
        out.append("")


def dumps_toml(data: dict) -> str:
    """Render dict -> TOML text. Root scalar keys come first (required), then tables."""
    if not isinstance(data, dict):
        raise ValueError("TOML root must be a table/dict")
    out: list[str] = []
    for k, v in data.items():
        if not isinstance(v, dict):
            out.append(f"{_fmt_key(k)} = {_fmt_value(v)}")
    if out and any(isinstance(v, dict) for v in data.values()):
        out.append("")
    _emit_table(out, [], data)
    text = "\n".join(out)
    if not text.strip():
        return ""
    return text.rstrip("\n") + "\n"


def parse_toml(text: str) -> dict:
    """Parse TOML (for validation / mutation round-trips). Empty text -> {}.

    Raises tomllib.TOMLDecodeError (a ValueError) on invalid syntax.
    """
    if not text or not text.strip():
        return {}
    return tomllib.loads(text)
