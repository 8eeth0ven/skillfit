import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("collect_portability", ROOT / "tools/collect.py")
collect = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collect)


class CollectPortabilityTests(unittest.TestCase):
    def test_known_old_and_current_paths_become_relative(self):
        suffix = "owner__repository/demo/SKILL.md"
        for value in (f"/old/workspace/本地库/{suffix}", f"本地库/{suffix}",
                      f"/old/workspace/library/{suffix}", f"library/{suffix}",
                      f"./library/{suffix}", f"C:\\old\\library\\{suffix.replace('/', chr(92))}"):
            with self.subTest(value=value):
                self.assertEqual(collect.normalize_skill_path(value), f"library/{suffix}")
        self.assertEqual(collect.normalize_skill_path("/old/library/owner__repo/demo/library/SKILL.md"),
                         "library/owner__repo/demo/library/SKILL.md")

    def test_traversal_and_unknown_paths_are_rejected(self):
        for value in ("library/../private/SKILL.md", "/old/../workspace/library/demo/SKILL.md",
                      "本地库/demo/../../private", "library\\..\\private", "/private/demo/SKILL.md",
                      "C:\\private\\demo.md", "other/demo.md", "library", "", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    collect.normalize_skill_path(value)

    def test_load_and_save_normalize_all_paths_without_changing_other_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "library/db.json"
            database.parent.mkdir()
            old = {"更新": "snapshot", "条目": [{"路径": "/old/workspace/本地库/owner__repo/demo/SKILL.md", "stars": 123}]}
            database.write_text(json.dumps(old), encoding="utf-8")
            with patch.object(collect, "DB", database):
                loaded = collect.load_db()
                self.assertEqual(loaded["条目"][0]["路径"], "library/owner__repo/demo/SKILL.md")
                self.assertEqual(loaded["条目"][0]["stars"], 123)
                self.assertEqual(json.loads(database.read_text()), old)  # load is read-only
                collect.save_db(old)
                self.assertEqual(json.loads(database.read_text()), loaded)
                self.assertNotIn("/old/workspace", database.read_text())

    def test_unknown_absolute_path_prevents_any_database_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "db.json"
            database.write_text("unchanged", encoding="utf-8")
            invalid = {"条目": [{"路径": "library/demo/SKILL.md"}, {"路径": "/private/demo.md"}]}
            with patch.object(collect, "DB", database):
                with self.assertRaises(ValueError) as error:
                    collect.save_db(invalid)
            self.assertEqual(database.read_text(), "unchanged")
            self.assertNotIn("/private", str(error.exception))

    def test_seed_resolves_normalized_legacy_path_against_project(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            document = project / "library/owner__repo/demo/SKILL.md"
            document.parent.mkdir(parents=True)
            document.write_text("示例规则", encoding="utf-8")
            db = {"条目": [{"路径": "/old/workspace/本地库/owner__repo/demo/SKILL.md",
                            "stars": 1000, "repo": "owner/repo", "skill": "demo", "状态": "待评"}]}
            with patch.object(collect, "PROJ", project), patch.object(collect, "TDIR", project / "tasks"):
                made = collect.seed_tasks(db, 1000)
            self.assertEqual(made, ["demo__owner"])
            manifest = project / "tasks/demo__owner/技能文件.txt"
            self.assertEqual(Path(manifest.read_text().strip()), document)
            self.assertTrue(Path(manifest.read_text().strip()).is_file())


if __name__ == "__main__":
    unittest.main()
