"""Run: make test. USB is preferred; BLE is the fallback."""

import unittest
from unittest import mock

from PIL import Image

import btprint


class PayloadTest(unittest.TestCase):
    def test_blank_two_row_page_is_init_raster_header_zero_rows_and_feed(self):
        data = btprint.payload(Image.new("1", (384, 2), 1), 4)
        self.assertEqual(data, b"\x1b@\x1dv0\x00" + b"\x30\x00" + b"\x02\x00" + bytes(96) + b"\x1bd\x04")

    def test_black_pixels_become_one_bits(self):
        image = Image.new("1", (384, 1), 1)
        image.putpixel((0, 0), 0)
        raster = btprint.payload(image, 0)[10:-3]
        self.assertEqual(raster[0], 0b10000000)


class RoutingTest(unittest.TestCase):
    def test_usb_printer_counts_as_online_without_any_bluetooth_scan(self):
        with mock.patch.object(btprint, "usb_device", return_value=object()), \
                mock.patch.object(btprint.asyncio, "run") as scan:
            self.assertTrue(btprint.printer_online())
        scan.assert_not_called()

    def test_print_uses_usb_when_plugged_in_and_never_touches_ble(self):
        with mock.patch.object(btprint, "usb_device", return_value="dev"), \
                mock.patch.object(btprint, "send_usb") as usb_send, \
                mock.patch.object(btprint, "send") as ble_send, \
                mock.patch.object(btprint, "rule_enabled", return_value=False), \
                mock.patch.object(btprint, "feed_lines", return_value=0):
            btprint.print_image(Image.new("1", (384, 2), 1))
        usb_send.assert_called_once()
        ble_send.assert_not_called()


if __name__ == "__main__":
    unittest.main()


class TodoTest(unittest.TestCase):
    GOLDEN = "GROCERY RUN\nMon 16 Nov 2026\n\n[ ] Milk\n[x] Bananas\n\n1 of 2 done"
    DOC = ('{"title":"Grocery run","subtitle":"Mon 16 Nov 2026","show_totals":true,'
           '"items":[{"text":"Milk","done":false},{"text":"Bananas","done":true}]}')

    def test_json_becomes_the_golden_checklist(self):
        self.assertEqual(btprint.todo_text(self.DOC), self.GOLDEN)

    def test_bad_json_or_empty_items_exit_with_a_message(self):
        for raw in ("not json", "[]", '{"items":[]}'):
            with self.assertRaises(SystemExit):
                btprint.todo_text(raw)


class WrapTest(unittest.TestCase):
    def test_long_line_wraps_inside_the_paper_and_keeps_blank_lines(self):
        font = btprint.ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        lines = btprint.wrap("[ ] Bread, the good kind of bread\n\nend", font, btprint.WIDTH - 20)
        self.assertGreater(len(lines), 3)
        self.assertEqual(lines[-2:], ["", "end"])
        self.assertTrue(all(font.getlength(line) <= btprint.WIDTH - 20 for line in lines))
