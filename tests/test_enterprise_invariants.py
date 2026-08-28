import unittest

from am_aos.policy import AuthorityPolicy, PolicyViolation
from am_aos.evidence import EvidenceLedger, canonical_hash
from am_aos.assurance import VerificationGate, GateState, ClaimBoundary


class EnterpriseInvariantTests(unittest.TestCase):
    def test_authority_ceiling_cannot_be_bypassed(self):
        policy = AuthorityPolicy(["EXECUTE"])
        with self.assertRaises(PolicyViolation):
            policy.assert_allowed("ADMIN", ["ADMIN"])
        with self.assertRaises(PolicyViolation):
            policy.assert_allowed("EXECUTE", ["REVIEW"])

    def test_policy_is_immutable(self):
        policy = AuthorityPolicy(["EXECUTE"])
        with self.assertRaises(AttributeError):
            policy._allowed = frozenset(["ADMIN"])

    def test_missing_evidence_is_no_go(self):
        ledger = EvidenceLedger()
        result = VerificationGate().evaluate(ledger, [], True)
        self.assertEqual(result.state, GateState.NO_GO)

    def test_wrong_evidence_fails(self):
        ledger = EvidenceLedger()
        ledger.append("e1", "t1", "claim", False, "test", True)
        result = VerificationGate().evaluate(ledger, ["e1"], True)
        self.assertEqual(result.state, GateState.FAIL)

    def test_sufficient_evidence_passes(self):
        ledger = EvidenceLedger()
        ledger.append("e1", "t1", "claim", True, "test", True)
        result = VerificationGate().evaluate(ledger, ["e1"], True)
        self.assertEqual(result.state, GateState.PASS)

    def test_duplicate_evidence_is_rejected(self):
        ledger = EvidenceLedger()
        ledger.append("e1", "t1", "claim", True, "test", True)
        with self.assertRaises(ValueError):
            ledger.append("e1", "t1", "claim", True, "test", True)

    def test_evidence_hash_is_deterministic(self):
        self.assertEqual(canonical_hash({"a": 1}), canonical_hash({"a": 1}))

    def test_global_proof_claim_is_blocked(self):
        with self.assertRaises(ValueError):
            ClaimBoundary.validate("GLOBALLY_PROVEN", "repository tests")

    def test_claim_requires_scope(self):
        with self.assertRaises(ValueError):
            ClaimBoundary.validate("TESTED", "")


if __name__ == "__main__":
    unittest.main()
