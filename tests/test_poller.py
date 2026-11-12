"""Run: make test. Poller must not claim jobs while the printer is absent."""

import unittest
from unittest import mock

import poller


class PollOnceTest(unittest.TestCase):
    def test_offline_printer_claims_nothing_so_no_attempt_is_burned(self):
        with mock.patch.object(poller.btprint, "printer_online", return_value=False), \
                mock.patch.object(poller, "call") as call:
            self.assertEqual(poller.poll_once("u", "t"), 0)
        call.assert_not_called()

    def test_online_printer_claims_and_finishes_a_job(self):
        job = {"id": 7, "kind": "text", "copies": 1, "text": "hi"}
        calls = []

        def fake_call(url, token, tool, arguments):
            calls.append((tool, arguments))
            return [job] if tool == "claim_print_jobs" else {}

        with mock.patch.object(poller.btprint, "printer_online", return_value=True), \
                mock.patch.object(poller.btprint, "print_image"), \
                mock.patch.object(poller, "call", side_effect=fake_call):
            self.assertEqual(poller.poll_once("u", "t"), 1)
        self.assertEqual(calls[-1], ("finish_print_job", {"id": 7, "ok": True}))


if __name__ == "__main__":
    unittest.main()
