"""Pure to-do list layout and drawing for the thermal printer. No ORM, no clock, no files.

`parse_todo` checks the JSON a caller sends; `draw_todo` draws it as a 1-bit image with real check-boxes.
This file is byte-identical to `todo.py` in thermal-printer-poller (`btprint todo`); both repos pin the same
behaviour in tests. ponytail: two copies; fold into one package if the layout starts to change.
"""

from collections.abc import Callable
from dataclasses import dataclass

from PIL import Image, ImageDraw

MAX_ITEMS = 60
MARGIN = 10
GAP = 10  # box to text
THRESHOLD = 128
Measure = Callable[[str], int]


@dataclass(frozen=True)
class Todo:
    head: tuple[str, ...]  # title (upper-case) and subtitle, empty ones dropped
    rows: tuple[tuple[str, bool], ...]  # (text, done)
    totals: str  # "1 of 4 done", or "" when not asked


def _row(item) -> tuple[str, bool]:
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
    return text, done


def parse_todo(title, subtitle, items, show_totals) -> Todo:
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list.")
    if len(items) > MAX_ITEMS:
        raise ValueError(f"items is limited to {MAX_ITEMS}.")
    rows = tuple(_row(item) for item in items)
    head = tuple(line for line in (str(title or "").strip().upper(), str(subtitle or "").strip()) if line)
    totals = f"{sum(done for _, done in rows)} of {len(rows)} done" if show_totals else ""
    return Todo(head, rows, totals)


def wrap(text: str, measure: Measure, max_width: int) -> list[str]:
    """Greedy word wrap; a word wider than the line is split by character."""
    lines, current = [], ""
    for word in text.split(" "):
        candidate = f"{current} {word}" if current else word
        if measure(candidate) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = ""
        for char in word:
            if current and measure(current + char) > max_width:
                lines.append(current)
                current = ""
            current += char
    return [*lines, current]


def _box(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, done: bool) -> None:
    draw.rectangle((x, y, x + size, y + size), outline=0, width=3)
    if done:
        draw.line([(x + size * .2, y + size * .55), (x + size * .42, y + size * .8), (x + size * .85, y + size * .15)],
                  fill=0, width=4)


def draw_todo(todo: Todo, body, title, width: int = 384) -> Image.Image:
    """`body` and `title` are PIL fonts (a monospace pair). Returns a 1-bit image `width` px wide."""
    measure_body, measure_title = (lambda s: round(body.getlength(s))), (lambda s: round(title.getlength(s)))
    step, tstep = round(body.size * 1.3), round(title.size * 1.3)
    box = round(body.size * .85)
    text_x = MARGIN + box + GAP
    inner = width - 2 * MARGIN
    blocks = [(wrap(todo.head[0], measure_title, inner), title, tstep)] if todo.head else []
    blocks += [(wrap(line, measure_body, inner), body, step) for line in todo.head[1:]]
    item_lines = [wrap(text, measure_body, width - MARGIN - text_x) for text, _ in todo.rows]
    height = (2 * MARGIN + sum(len(lines) * h for lines, _, h in blocks) + 16
              + sum(len(lines) * step + 8 for lines in item_lines) + (step + 16 if todo.totals else 0))
    image = Image.new("L", (width, height), 255)
    draw, y = ImageDraw.Draw(image), MARGIN
    for lines, font, h in blocks:
        for line in lines:
            draw.text(((width - round(font.getlength(line))) // 2, y), line, font=font, fill=0)
            y += h
    if blocks:
        draw.line((MARGIN, y + 4, width - MARGIN, y + 4), fill=0, width=3)
        y += 16
    for (_, done), lines in zip(todo.rows, item_lines):
        _box(draw, MARGIN, y + (step - box) // 2, box, done)
        for line in lines:
            draw.text((text_x, y), line, font=body, fill=0)
            y += step
        y += 8
    if todo.totals:
        draw.line((MARGIN, y + 4, width - MARGIN, y + 4), fill=0, width=3)
        draw.text(((width - round(body.getlength(todo.totals))) // 2, y + 12), todo.totals, font=body, fill=0)
    return image.point(lambda v: 255 if v >= THRESHOLD else 0).convert("1")
