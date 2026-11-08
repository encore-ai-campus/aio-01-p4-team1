"""Safety boundaries of the live request-scoped fault driver; no VM calls."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch

import ticket_fault_check as fault


class TicketFaultDriverTests(unittest.TestCase):
    def test_wrong_runtime_mode_never_logs_in_or_arms_fault(self):
        session = Mock()
        session.logout.return_value = True
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            with patch.object(fault, "Session", return_value=session), \
                 patch.object(fault, "deployment_state", new=AsyncMock(return_value={
                     "service_mode": "practice", "readonly_fault_mount": True})), \
                 patch.object(fault, "switch", new=AsyncMock()) as switch:
                report = fault.run({}, output)
            session.login.assert_not_called()
            session.call.assert_not_called()
            switch.assert_not_called()
            self.assertEqual(report["verdict"], "FAIL_OR_PARTIAL")
            self.assertFalse(report["checks"]["app_mode_and_readonly_gate"])
            self.assertTrue(output.is_file())

    def test_request_failure_always_disarms_own_switch_and_logs_out(self):
        session = Mock()
        session.login.return_value = True
        session.call.side_effect = TimeoutError("synthetic private text")
        session.logout.return_value = True
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            with patch.object(fault, "Session", return_value=session), \
                 patch.object(fault, "deployment_state", new=AsyncMock(return_value={
                     "service_mode": "app", "readonly_fault_mount": True})), \
                 patch.object(fault, "switch", new=AsyncMock(side_effect=[
                     {"armed": True}, {"disarmed": True}])) as switch:
                report = fault.run({"OKE_EMP_USER": "synthetic", "OKE_EMP_PASS": "synthetic"}, output)
            self.assertEqual([call.kwargs["enable"] for call in switch.await_args_list], [True, False])
            self.assertEqual(switch.await_args_list[0].args[1], switch.await_args_list[1].args[1])
            session.logout.assert_called_once()
            self.assertTrue(report["checks"]["fault_disarmed"])
            self.assertEqual(report["errors"], ["TimeoutError"])
            self.assertNotIn("synthetic private text", output.read_text())
            self.assertEqual(json.loads(output.read_text())["verdict"], "FAIL_OR_PARTIAL")


if __name__ == "__main__":
    unittest.main()
