# thermal-printer-poller

Print on a Bluetooth (BLE) M120-style thermal printer from a Mac, and poll an
[Everything](https://github.com/intrepid-g/everything) server for print jobs.

The printer's computer pulls jobs over MCP, so it can sit behind NAT and sleep.
Queue contract: [`docs/PRINTING.md`](https://github.com/intrepid-g/everything/blob/main/docs/PRINTING.md).

## Install

```sh
make install      # puts btprint and thermal-poller in ~/.local/bin
```

## First run

`thermal-poller` asks once, in a terminal, then saves to `~/.config/thermal-printer/config.json` (mode 600):

1. **Printer**: it scans Bluetooth and lets you pick the device (names starting `Q244` first) or paste its address. macOS gives each Mac its own UUID for the printer, so this is per machine.
2. **Server MCP URL**, e.g. `https://your-host/mcp/`
3. **Token**: an Everything AgentToken with only the **Print queue poller** scope. It can claim and finish jobs, nothing else.

Environment variables override the file: `BTPRINT_ADDR`, `EVERYTHING_URL`, `EVERYTHING_PRINT_TOKEN`.
To change a value, edit or delete the file.

## Use

```sh
btprint 'Line one\nLine two'      # print text
btprint -i picture.png            # print an image
btprint --feed 8 'hi'             # more paper after the print
btprint --no-rule 'hi'            # no separator line
make run                          # poll every 30 s (or run thermal-poller)
make once                         # one poll, e.g. from launchd/cron
```

## Separator and paper feed

Every print ends with a horizontal rule (so separate prints are easy to tell apart), then feeds paper
so the text clears the tear bar. Both are configurable:

| Setting | Flag | Env / config key | Default |
| --- | --- | --- | --- |
| Blank lines fed after a print (0-255) | `--feed N` | `BTPRINT_FEED` / `feed` | 4 |
| Rule under each print | `--no-rule` | `BTPRINT_RULE=0` / `rule` | on |

Flags apply to one `btprint` call; the env var or a key in `~/.config/thermal-printer/config.json`
(e.g. `"feed": 8`) applies to `btprint` and `thermal-poller` alike.

## How the printer works

- BLE only. The macOS serial port accepts writes but nothing reaches the printer.
- It ignores ESC/POS text and prints raster images sent as `GS v 0` (384 px wide, 1 bit).
- Writes go to characteristic `ff02` in ~180-byte chunks, 20 ms apart.
- Paper feeds but nothing prints: the data is being read as text. Connection fails: the printer is off or connected to a phone app.

## License

MIT
