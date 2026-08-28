import unittest
from am_aos.state import MissionState, transition
from am_aos.persistence import SQLiteStore


class StateAndPersistenceTests(unittest.TestCase):
    def test_valid_state_transition(self):
        self.assertEqual(transition(MissionState.READY, MissionState.RUNNING), MissionState.RUNNING)

    def test_illegal_transition_is_rejected(self):
        with self.assertRaises(ValueError):
            transition(MissionState.PASSED, MissionState.RUNNING)

    def test_terminal_no_go_cannot_resume(self):
        with self.assertRaises(ValueError):
            transition(MissionState.NO_GO, MissionState.RECOVERY)

    def test_sqlite_persists_contract_hash_and_events(self):
        store = SQLiteStore()
        store.save_mission("m1", "goal", {"goal": "goal"}, "abc123")
        self.assertEqual(store.mission_contract_hash("m1"), "abc123")
        store.append_event("e1", "h1", {"event": "TEST"})
        self.assertEqual(store.count_events(), 1)
        store.close()


if __name__ == "__main__":
    unittest.main()
