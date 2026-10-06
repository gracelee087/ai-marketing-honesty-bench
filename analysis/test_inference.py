"""Regression cases for false certainty in statistical verdicts."""
import unittest

import numpy as np
import pandas as pd

from analyze import boot, h2_verdict, verdict


class InferenceTests(unittest.TestCase):
    def test_uncertain_other_claims_do_not_support_relocation(self):
        numbers = {"n_pairs": 36, "lo": -.56, "hi": -.11}
        for lo, hi in [(-.72, .19), (0., 0.), (-.1, .5)]:
            self.assertEqual(h2_verdict(numbers, {"n_pairs": 36, "lo": lo, "hi": hi}), "inconclusive")

    def test_joint_directional_evidence(self):
        decrease = {"n_pairs": 60, "lo": -.6, "hi": -.1}
        increase = {"n_pairs": 60, "lo": .1, "hi": .6}
        self.assertEqual(h2_verdict(decrease, increase), "supported")
        self.assertEqual(h2_verdict(decrease, decrease), "falsified")
        self.assertEqual(h2_verdict(increase, increase), "falsified")

    def test_one_company_cannot_supply_company_uncertainty(self):
        mean, lo, hi, n = boot(pd.Series([-4., -2.]), pd.Series(["same", "same"]))
        self.assertEqual((mean, n), (-3., 2))
        self.assertTrue(np.isnan(lo) and np.isnan(hi))
        self.assertEqual(verdict(lo, hi, -1), "inconclusive")
        interval = {"n_pairs": n, "lo": lo, "hi": hi}
        self.assertEqual(h2_verdict(interval, interval), "inconclusive")

    def test_empty_data_remains_distinct(self):
        result = boot(pd.Series(dtype=float), pd.Series(dtype=str))
        self.assertEqual(result[3], 0)
        empty = {"n_pairs": 0, "lo": np.nan, "hi": np.nan}
        self.assertEqual(h2_verdict(empty, empty), "no data")


if __name__ == "__main__":
    unittest.main()
