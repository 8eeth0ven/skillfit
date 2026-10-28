import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("bench_portability", ROOT / "tools/bench.py")
bench = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bench)


class PortabilityTests(unittest.TestCase):
    def test_init_and_preview_in_another_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "BENCH_ROOT": directory,
                   "BENCH_SKILLS_DIR": str(Path(directory) / "missing-skills")}
            command = [sys.executable, str(ROOT / "tools/bench.py")]
            first = subprocess.run(command + ["init-example"], cwd=directory, env=env,
                                   capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            example = Path(directory) / "tasks/format-check"
            self.assertTrue((example / "rules.md").is_file())
            preview = subprocess.run(command + ["preview", "--skills", "format-check"],
                                     cwd=directory, env=env, capture_output=True, text=True)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertEqual(preview.stdout.count("| format-check |"), 6)
            self.assertFalse((Path(directory) / "runs").exists())
            second = subprocess.run(command + ["init-example"], cwd=directory, env=env,
                                    capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertTrue((example / "rules.md").is_file())

    def test_export_copies_external_frontend_without_data(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "site"
            original = (ROOT / "site/index.html").read_bytes()
            bench.write_site_assets(destination)
            self.assertEqual((destination / "index.html").read_bytes(), original)
            self.assertTrue((destination / "app.js").is_file())
            self.assertTrue((destination / "style.css").is_file())
            self.assertTrue((destination / "assets/skillfit-hero.png").is_file())
            self.assertFalse((destination / "data.json").exists())
            self.assertEqual((ROOT / "site/index.html").read_bytes(), original)

    def test_refresh_restores_canonical_template_after_legacy_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            (site / "template.html").write_text("canonical frontend", encoding="utf-8")
            (site / "index.html").write_text("legacy frontend", encoding="utf-8")
            for name in ("app.js", "style.css"):
                (site / name).write_text("asset", encoding="utf-8")
            with patch.object(bench, "FRONTEND_SOURCE", site):
                bench.write_site_assets(site)
            self.assertEqual((site / "index.html").read_text(), "canonical frontend")

    def test_legacy_manifest_still_works(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "demo"
            skill.mkdir()
            document = root / "source.md"
            document.write_text("示例规则", encoding="utf-8")
            (skill / "技能文件.txt").write_text(str(document), encoding="utf-8")
            with patch.object(bench, "TDIR", root):
                self.assertEqual(bench.skill_paths("demo"), [document])
                self.assertIn("示例规则", bench.skill_docs("demo"))

    def test_filler_length_for_large_documents_without_installed_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            with patch.object(bench, "SKILLS_DIR", missing):
                for length in (0, 200, 48000):
                    self.assertEqual(len(bench.filler_docs("demo", length)), length)
                with self.assertRaises(SystemExit):
                    bench.manifest()


if __name__ == "__main__":
    unittest.main()
