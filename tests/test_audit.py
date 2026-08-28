import unittest
from dataclasses import replace

from am_aos.audit import TamperEvidentAuditLog


class AuditTests(unittest.TestCase):
    def test_hash_chain_verifies(self):
        log = TamperEvidentAuditLog()
        log.append("MISSION_CREATED", "m1", goal="x")
        log.append("TASK_STARTED", "t1")
        ok, reason = log.verify_chain()
        self.assertTrue(ok, reason)

    def test_tampering_is_detected(self):
        log = TamperEvidentAuditLog()
        log.append("MISSION_CREATED", "m1", goal="x")
        log.append("TASK_STARTED", "t1")
        original = log._events[0]
        log._events[0] = replace(original, data={"goal": "tampered"})
        ok, _ = log.verify_chain()
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
