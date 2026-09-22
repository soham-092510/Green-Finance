# =====================================================================
# ECO MONITOR / GREEN-FINANCE — TEST_ACCURACY_ENGINE.PY
# Purpose: Comprehensive unit & integration test suite for the
#          Energy Attribution & Accuracy Engine, Baseline Calibration,
#          Double-Entry Banking, and Repeatability CV.
# =====================================================================

import unittest
from backend.db.session import SessionLocal
from backend.db.database import init_db
from backend.services import baseline_service, accuracy_service, payment_service
from backend.models.user import User
from backend.models.account import Account
from backend.models.accuracy import BaselineProfile, ValidationRun
from fastapi import HTTPException


class TestAccuracyEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize database tables and seed data
        init_db()

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_baseline_calibration_and_stats(self):
        """Tests that baseline calibration accurately calculates mean, std, and CV."""
        baseline_service.start_calibration(duration_seconds=5)
        
        # Record controlled samples around 18.7W
        samples = [18.2, 18.5, 18.7, 18.9, 19.2]
        for s in samples:
            baseline_service.calibration_manager.record_sample(s)
            
        progress = baseline_service.get_calibration_status()
        self.assertGreater(progress["sample_count"], 0)
        self.assertAlmostEqual(progress["mean_idle_power_watts"], 18.7, delta=0.5)
        self.assertLessEqual(progress["idle_cv_percent"], 5.0)

        # Test Locking
        profile = baseline_service.lock_baseline_profile(self.db)
        self.assertEqual(profile.status, "LOCKED")
        self.assertIsNotNone(profile.id)

    def test_02_baseline_drift_detection(self):
        """Tests that drift detection flags when idle power surges > 15%."""
        # Baseline = 18.7W. Current = 19.1W (Diff ~2.1% -> STABLE)
        res_stable = baseline_service.check_baseline_drift(current_idle_watts=19.1, locked_baseline_watts=18.7)
        self.assertEqual(res_stable["status"], "STABLE")
        self.assertFalse(res_stable["is_alert"])

        # Baseline = 18.7W. Current = 24.5W (Diff ~31% -> DRIFT_DETECTED)
        res_drift = baseline_service.check_baseline_drift(current_idle_watts=24.5, locked_baseline_watts=18.7)
        self.assertEqual(res_drift["status"], "DRIFT_DETECTED")
        self.assertTrue(res_drift["is_alert"])

    def test_03_energy_conservation_and_fidelity(self):
        """Tests the exact waterfall: 1000J - (800J + 150J) = 50J (5%) -> 95% Fidelity."""
        res = accuracy_service.calculate_energy_residual_and_fidelity(
            host_joules=1000.0,
            container_joules=800.0,
            idle_joules=150.0
        )
        self.assertEqual(res["accounted_energy_joules"], 950.0)
        self.assertEqual(res["residual_joules"], 50.0)
        self.assertEqual(res["residual_percent"], 5.0)
        self.assertEqual(res["fidelity_percent"], 95.0)
        self.assertTrue(res["is_within_tolerance"])

    def test_04_transaction_repeatability_cv(self):
        """Tests that repeated transactions achieve CV <= 5.0%."""
        # Simulated 50 identical runs around 0.70 Joules
        import random
        energies = [random.gauss(0.70, 0.02) for _ in range(50)]
        res = accuracy_service.calculate_transaction_repeatability(energies)
        self.assertLessEqual(res["cv_percent"], 5.0)
        self.assertEqual(res["status"], "PASS")

    def test_05_atomic_bank_transfer(self):
        """Tests atomic inter-bank transfer between HDFC9999 and MAH123."""
        # Check initial balances
        _, sender_acc = payment_service.get_user_cash_account(self.db, "HDFC9999")
        _, recip_acc = payment_service.get_user_cash_account(self.db, "MAH123")
        initial_sender = sender_acc.balance
        initial_recip = recip_acc.balance

        transfer_amt = 1500.0
        resp = payment_service.execute_bank_transfer(
            db=self.db,
            source_bank_id="HDFC9999",
            dest_bank_id="MAH123",
            amount=transfer_amt,
            note="Test vendor payment"
        )

        self.assertEqual(resp["status"], "COMPLETED")
        self.assertEqual(resp["amount"], transfer_amt)
        self.assertIsNotNone(resp["audit_hash"])
        self.assertEqual(len(resp["audit_hash"]), 64)  # SHA-256 length

        # Verify balance updates
        self.db.refresh(sender_acc)
        self.db.refresh(recip_acc)
        self.assertEqual(sender_acc.balance, initial_sender - transfer_amt)
        self.assertEqual(recip_acc.balance, initial_recip + transfer_amt)

    def test_06_insufficient_balance_rejected(self):
        """Tests that overdraft attempts are rejected with 400 Bad Request."""
        with self.assertRaises(HTTPException) as ctx:
            payment_service.execute_bank_transfer(
                db=self.db,
                source_bank_id="HDFC9999",
                dest_bank_id="MAH123",
                amount=99999999.0
            )
        self.assertEqual(ctx.exception.status_code, 400)

    def test_07_validation_report_generation(self):
        """Tests compiling the formal Energy Validation Report with SHA-256 signature."""
        report = accuracy_service.generate_formal_validation_report(self.db)
        self.assertTrue(report["report_id"].startswith("EVR-"))
        self.assertIn("audit_signature_sha256", report)
        self.assertEqual(len(report["audit_signature_sha256"]), 64)
        self.assertEqual(report["key_findings"]["fidelity_certification"], "VERIFIED (Residual <= 6.0%)")


if __name__ == "__main__":
    unittest.main()
