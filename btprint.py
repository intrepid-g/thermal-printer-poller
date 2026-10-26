"""Print text or a PNG on an M120-style BLE thermal printer.

    btprint 'Line one\nLine two'
    btprint -i picture.png
    btprint --feed 8 'more paper after'     # blank lines after the print (default 4, 0-255)
    btprint --no-rule 'no separator line'   # skip the rule drawn under each print

The printer's BLE address (a macOS-assigned UUID) is asked once, then saved.
"""

import asyncio
import sys

from bleak import BleakClient, BleakScanner
from PIL import Image, ImageDraw, ImageFont

import config

WRITE_CHAR = "0000ff02-0000-1000-8000-00805f9b34fb"
WIDTH = 384
CHUNK = 180
DEFAULT_FEED = 4
RULE_HEIGHT = 12  # rows of paper the separator takes; the line itself is 3 px thick
NAME_HINT = "Q244"  # how this printer advertises itself; a scan lists these first


def render(text: str) -> Image.Image:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    lines = text.split("\n")
    image = Image.new("1", (WIDTH, len(lines) * 56 + 20), 1)
    draw = ImageDraw.Draw(image)
    for i, line in enumerate(lines):
        draw.text((10, 10 + i * 56), line, font=font, fill=0)
    return image


def from_image(path) -> Image.Image:
    image = Image.open(path).convert("L")
    return image.resize((WIDTH, int(image.height * WIDTH / image.width))).convert("1")


def ask_address(_prompt: str) -> str:
    """Scan for BLE devices and let the user pick one, or paste an address."""
    print("Scanning for Bluetooth devices (5 s)...", file=sys.stderr)
    found = asyncio.run(BleakScanner.discover(timeout=5))
    found.sort(key=lambda d: not (d.name or "").startswith(NAME_HINT))
    for i, device in enumerate(found):
        print(f"  {i}: {device.name or '(unnamed)'}  {device.address}", file=sys.stderr)
    choice = input("Number from the list, or paste the printer's address: ").strip()
    return found[int(choice)].address if choice.isdigit() and int(choice) < len(found) else choice


def printer_address() -> str:
    return config.get("printer_addr", "", ask=ask_address)


def with_rule(image: Image.Image) -> Image.Image:
    """Append a horizontal rule so consecutive prints are visibly separated."""
    out = Image.new("1", (WIDTH, image.height + RULE_HEIGHT), 1)
    out.paste(image, (0, 0))
    y = image.height + RULE_HEIGHT // 2
    ImageDraw.Draw(out).rectangle((0, y - 1, WIDTH, y + 1), fill=0)
    return out


def feed_lines(override: int | None = None) -> int:
    value = override if override is not None else int(config.get_optional("feed", str(DEFAULT_FEED)))
    return max(0, min(255, value))


def rule_enabled(override: bool | None = None) -> bool:
    if override is not None:
        return override
    return config.get_optional("rule", "1").strip().lower() not in ("0", "false", "no", "off")


async def send(image: Image.Image, address: str, feed: int) -> None:
    raster = image.point(lambda p: 0 if p else 1).convert("1").tobytes()
    height = image.height
    data = b"\x1b@\x1dv0\x00" + (WIDTH // 8).to_bytes(2, "little") + height.to_bytes(2, "little") + raster + b"\x1bd" + bytes([feed])
    async with BleakClient(address, timeout=20) as client:
        for i in range(0, len(data), CHUNK):
            await client.write_gatt_char(WRITE_CHAR, data[i : i + CHUNK], response=False)
            await asyncio.sleep(0.02)
        await asyncio.sleep(3)


def print_image(image: Image.Image, feed: int | None = None, rule: bool | None = None) -> None:
    if rule_enabled(rule):
        image = with_rule(image)
    asyncio.run(send(image, printer_address(), feed_lines(feed)))


def main() -> None:
    args, feed, rule = sys.argv[1:], None, None
    while args and args[0] in ("--feed", "--no-rule"):
        if args[0] == "--no-rule":
            rule, args = False, args[1:]
        else:
            feed, args = int(args[1]), args[2:]
    if not args:
        sys.exit("usage: btprint [--feed N] [--no-rule] 'text' | btprint -i image.png")
    image = from_image(args[1]) if args[0] == "-i" else render(" ".join(args).replace("\\n", "\n"))
    print_image(image, feed, rule)


if __name__ == "__main__":
    main()
