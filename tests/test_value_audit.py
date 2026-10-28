"""Meaningful alignment/coverage tests; no network, CLI or model calls."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("value_audit", Path(__file__).resolve().parents[1] / "tools/value_audit.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class ValueAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "scoring/demo").mkdir(parents=True)
        self.mapping = {}

    def artifact(self, mode, trial=1, task="T01", scores=(3, 3), adherence=None, status="ok", code=None, model="producer-v1"):
        code = code or f"A{len(self.mapping):08x}"
        output = self.root / "runs/demo" / model / f"{task}-{mode}-t{trial}.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(f"---\n技能: demo\n任务: {task}\n模型: {model}\n模式: {mode}\n试验: {trial}\n状态: {status}\n---\n正文\n", encoding="utf-8")
        self.mapping[code] = {"file": str(output), "skill": "demo", "task": task, "model": model, "mode": mode}
        dest = self.root / "scoring/demo" / code
        dest.mkdir(exist_ok=True)
        for judge, score in zip(("judgeA-v1", "judgeB-v1"), scores):
            (dest / f"{judge}.json").write_text(json.dumps({"评分者": judge, "正确性": score, "完整性": score,
                                                            "表达清晰": score, "技能遵循": adherence, "判定": "PASS"}), encoding="utf-8")
        (self.root / "scoring/demo/映射表.json").write_text(json.dumps(self.mapping), encoding="utf-8")
        return dest

    def run_audit(self):
        return audit.audit(self.root)

    def test_m2_only_cannot_be_called_effective(self):
        self.artifact("M2", scores=(5, 5), adherence=5)
        result = self.run_audit()["results"][0]
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertEqual(result["comparisons"]["M2-M1"]["paired_samples"], 0)
        self.assertEqual(result["effectiveness_decision"], "not_established")

    def test_common_weights_ignore_adherence_and_m4_null(self):
        self.artifact("M1", scores=(3, 3))
        self.artifact("M2", scores=(3, 3), adherence=0)
        self.artifact("M4", scores=(3, 3), adherence=None)
        result = self.run_audit()["results"][0]
        self.assertEqual(result["comparisons"]["M2-M1"]["task_equal_mean_delta"], 0)
        self.assertEqual(result["comparisons"]["M2-M4"]["task_equal_mean_delta"], 0)
        self.assertLess(result["diagnostics_not_comparable_between_modes"]["M2"]["historical_absolute_mean"], 3)

    def test_trials_are_paired_and_never_overwritten(self):
        for trial, baseline, treated in ((1, 1, 4), (2, 4, 2)):
            self.artifact("M1", trial, scores=(baseline, baseline))
            self.artifact("M2", trial, scores=(treated, treated))
        contrast = self.run_audit()["results"][0]["comparisons"]["M2-M1"]
        self.assertEqual(contrast["paired_samples"], 2)
        self.assertEqual(contrast["task_equal_mean_delta"], .5)
        self.assertEqual(contrast["within_task"][0]["paired_trials"], 2)
        self.assertIsNotNone(contrast["within_task"][0]["trial_sd"])
        self.assertIsNone(contrast["confidence_interval"])

    def test_different_tasks_or_trials_do_not_pair(self):
        self.artifact("M1", trial=1, task="T01")
        self.artifact("M2", trial=2, task="T01")
        self.artifact("M4", trial=1, task="T02")
        result = self.run_audit()["results"][0]
        self.assertTrue(all(v["paired_samples"] == 0 for v in result["comparisons"].values()))

    def test_unmatched_judges_and_self_votes_do_not_fill_pool(self):
        dest = self.artifact("M1")
        (dest / "judgeB-v1.json").unlink()
        dest2 = self.artifact("M2")
        (dest2 / "producer-v1.json").write_text(json.dumps({"评分者": "producer-v1", "正确性": 5, "完整性": 5, "表达清晰": 5}))
        result = self.run_audit()["results"][0]["comparisons"]["M2-M1"]
        self.assertEqual(result["paired_samples"], 0)
        self.assertEqual(result["insufficient_judge_pool_pairs"], 1)

    def test_incomplete_boolean_nan_and_out_of_scale_are_rejected(self):
        for bad in (True, float("nan"), 6, -1, None, "5"):
            with self.subTest(bad=bad):
                self.assertIsNone(audit.weighted({"正确性": bad, "完整性": 3, "表达清晰": 3}, audit.COMMON_WEIGHTS))
        self.assertIsNone(audit.weighted({"正确性": 4, "表达清晰": 4}, audit.COMMON_WEIGHTS))

    def test_invalid_artifact_or_duplicate_cell_not_paired(self):
        self.artifact("M1")
        self.artifact("M2", status="fail:invalid-output")
        report = self.run_audit()
        self.assertEqual(report["results"][0]["comparisons"]["M2-M1"]["paired_samples"], 0)
        self.assertIn("artifact_not_ok", report["issues"]["counts"])
        self.artifact("M2", code="A11111111")
        self.artifact("M2", code="A22222222")
        report = self.run_audit()
        self.assertIn("duplicate_task_trial_mode", report["issues"]["counts"])
        self.assertEqual(report["results"][0]["comparisons"]["M2-M1"]["paired_samples"], 0)

    def test_task_equal_weight_not_trial_weight(self):
        for trial in (1, 2, 3):
            self.artifact("M1", trial=trial, task="A", scores=(0, 0))
            self.artifact("M2", trial=trial, task="A", scores=(2, 2))
        self.artifact("M1", task="B", scores=(2, 2))
        self.artifact("M2", task="B", scores=(0, 0))
        result = self.run_audit()["results"][0]["comparisons"]["M2-M1"]
        self.assertEqual(result["task_equal_mean_delta"], 0)

    def test_snapshot_counts_candidates_without_computing_gains(self):
        path = self.root / "site.json"
        rows = [{"模型": "m", "任务": "T", "模式": mode, "总分": score} for mode, score in (("M1", 1), ("M2", 5), ("M4", 2))]
        path.write_text(json.dumps({"generated": "old", "skills": {"demo": {"tasks": rows, "gains": {"untrusted": 99}}}}))
        report = audit.audit_snapshot(path)
        result = report["results"][0]
        self.assertEqual(report["coverage"]["aggregate_candidate_task_pairs"], {"M2-M1": 1, "M2-M4": 1})
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertTrue(all(v["task_equal_mean_delta"] is None and v["paired_samples"] == 0 for v in result["comparisons"].values()))
        self.assertIn("insufficient_evidence", audit.markdown(report))

    def test_relocated_chinese_run_directory_preserves_metadata_check(self):
        self.artifact("M1")
        self.artifact("M2")
        for value in self.mapping.values():
            value["file"] = value["file"].replace("/runs/", "/结果/")
        (self.root / "scoring/demo/映射表.json").write_text(json.dumps(self.mapping))
        report = self.run_audit()
        self.assertEqual(report["results"][0]["comparisons"]["M2-M1"]["paired_samples"], 1)
        self.assertEqual(report["issues"]["total"], 0)


if __name__ == "__main__":
    unittest.main()
