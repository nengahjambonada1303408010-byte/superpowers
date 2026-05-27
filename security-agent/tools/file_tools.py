import os
import json
from pathlib import Path

TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Read the content of a source code or config file. Only allowed for files with approved extensions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to read"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_directory",
        "description": "List files and directories at the given path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to list"}
            },
            "required": ["path"],
        },
    },
]

ALLOWED_EXTENSIONS = {
    ".py", ".php", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
    ".rb", ".cs", ".cpp", ".c", ".h", ".html", ".css", ".json",
    ".yaml", ".yml", ".env", ".conf", ".xml", ".sh", ".sql",
}


def read_file(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() not in ALLOWED_EXTENSIONS:
        return json.dumps({"error": f"File extension '{p.suffix}' not allowed for security scanning."})
    if not p.exists():
        return json.dumps({"error": f"File not found: {path}"})
    if p.stat().st_size > 500_000:
        return json.dumps({"error": "File too large (>500KB). Provide a smaller excerpt."})
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
        return json.dumps({"path": str(p), "content": content, "lines": content.count("\n") + 1})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def list_directory(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return json.dumps({"error": f"Path not found: {path}"})
    if not p.is_dir():
        return json.dumps({"error": f"Not a directory: {path}"})
    try:
        entries = []
        for entry in sorted(p.iterdir())[:100]:
            entries.append({
                "name": entry.name,
                "type": "dir" if entry.is_dir() else "file",
                "extension": entry.suffix.lower() if entry.is_file() else "",
                "size": entry.stat().st_size if entry.is_file() else 0,
            })
        return json.dumps({"path": str(p), "entries": entries, "count": len(entries)})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def dispatch(tool_name: str, tool_input: dict) -> str:
    if tool_name == "read_file":
        return read_file(tool_input["path"])
    if tool_name == "list_directory":
        return list_directory(tool_input["path"])
    return json.dumps({"error": f"Unknown tool: {tool_name}"})
