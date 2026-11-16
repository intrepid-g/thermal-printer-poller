"""Pure to-do list layout for `btprint todo`.

A copy of `printing/todo.py` in the `everything` repo (the MCP tool `enqueue_todo_list`); both pin the
same golden text in a test. ponytail: two copies; fold into one package if the layout starts to change.
"""

MAX_ITEMS = 60
BOX_OPEN, BOX_DONE = "[ ]", "[x]"


def _item_line(item) -> tuple[str, bool]:
    """An item is a string (not done) or {"text": ..., "done": bool}."""
    if isinstance(item, str):
        text, done = item, False
    elif isinstance(item, dict):
        text, done = item.get("text"), bool(item.get("done"))
    else:
        raise ValueError("each item must be a string or {text, done}.")
    text = " ".join(str(text or "").split())
    if not text:
        raise ValueError("each item needs text.")
    return f"{BOX_DONE if done else BOX_OPEN} {text}", done


def format_todo(title: str, subtitle: str, items: list, show_totals: bool) -> str:
    """Title, subtitle, a blank line, one `[ ]`/`[x]` line per item, then "N of M done" if asked."""
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list.")
    if len(items) > MAX_ITEMS:
        raise ValueError(f"items is limited to {MAX_ITEMS}.")
    rows = [_item_line(item) for item in items]
    head = [line for line in ((title or "").strip().upper(), (subtitle or "").strip()) if line]
    out = [*head, *([""] if head else []), *(line for line, _ in rows)]
    if show_totals:
        out += ["", f"{sum(done for _, done in rows)} of {len(rows)} done"]
    return "\n".join(out)
