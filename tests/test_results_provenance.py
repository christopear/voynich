"""Every committed results directory must name code that still exists (see AGENTS.md, mistake 7).

The October layout migration silently dropped the code behind several result
sets. If this test fails because of a new results directory, add it to
PRODUCERS with the module(s) that generate it; never remove a producer whose
results are still committed.
"""
import importlib.util
import unittest

from voynich.paths import ROOT

PRODUCERS = {
    "review_2026-09-24": ["voynich.experiments.e01_terminal_sandhi", "voynich.experiments.e04_naibbe_positive_control",
                          "voynich.boundary"],
    "frontier_2026-09-24": ["voynich.experiments.e06_boundary_frontier", "voynich.experiments.e07_boundary_robustness"],
    "mechanisms_2026-09-24": ["voynich.experiments.e08_robustness_gate", "voynich.experiments.e09_mechanism_benchmark",
                              "voynich.experiments.e10_recovery_sensitivity", "voynich.experiments.e11_mixture_controls"],
    "reconstruction_2026-09-25": ["voynich.experiments.e12_reconstruct_claims"],
    "equivalence_2026-09-25": ["voynich.experiments.e13_equivalence_classes", "voynich.experiments.e14_equivalence_posthoc"],
    "coupled_cipher_2026-09-25": ["voynich.experiments.e15_coupled_cipher_transfer"],
    "coupling_test_2026-09-25": ["voynich.experiments.e16_coupling_aware_test"],
    "coupling_test_v2_2026-09-25": ["voynich.experiments.e17_coupling_test_v2"],
    "coupling_test_v3_2026-09-26": ["voynich.experiments.e18_coupling_test_v3"],
    "v101_2026-09-26": ["voynich.experiments.e19_v101_mapping", "voynich.experiments.e20_v101_variant_test",
                        "voynich.experiments.posthoc_e20_v101_variant_rates", "voynich.experiments.e21_v101_ports"],
    "v101_followup_2026-09-26": ["voynich.experiments.e22_v101_gain_decomposition",
                                 "voynich.experiments.posthoc_e22_v101_spacing",
                                 "voynich.experiments.e23_v101_variant_followups",
                                 "voynich.experiments.posthoc_e23_v101_locality"],
    "cipher_families_2026-09-26": ["voynich.experiments.e24_cipher_family_benchmark",
                                   "voynich.experiments.e25_homophone_recovery"],
    "decipher_framework_2026-09-30": ["voynich.experiments.e26_decipherment_search"],
    "laboratory_2026-10-08": ["voynich.laboratory.roundtrips", "voynich.laboratory.benchmark",
                              "voynich.laboratory.focused", "voynich.laboratory.page_recovery",
                              "voynich.laboratory.shift_recovery", "voynich.laboratory.report"],
    "medical_recovery_2026-10-08": ["voynich.laboratory.medical_recovery", "voynich.laboratory.medical_report"],
    "voynich_pilot_2026-10-09": ["voynich.laboratory.voynich_pilot", "voynich.laboratory.voynich_pilot_report"],
    "line_rotation_2026-10-09": ["voynich.laboratory.rotation_pilot", "voynich.laboratory.rotation_report"],
    "phase_initialization_2026-10-09": ["voynich.laboratory.phase_initialization", "voynich.laboratory.phase_report",
                                        "voynich.laboratory.clock_audit"],
    "capacity_screen_2026-10-09": ["voynich.evaluation.capacity"],
}
NOT_RESULT_SETS = {"overnight", "runs", "scratch"}   # logs, ignored run archives, scratch output


class ResultsProvenanceTests(unittest.TestCase):
    def test_every_results_directory_has_a_producer(self):
        dirs = {p.name for p in (ROOT / "results").iterdir() if p.is_dir()} - NOT_RESULT_SETS
        self.assertEqual(sorted(dirs - set(PRODUCERS)), [], "add the producing module(s) to PRODUCERS")

    def test_every_producer_exists(self):
        missing = [m for mods in PRODUCERS.values() for m in mods if importlib.util.find_spec(m) is None]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
