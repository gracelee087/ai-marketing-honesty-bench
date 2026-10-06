import ast
import json
import unittest
from pathlib import Path

from engine import CONDITIONS, SELECT, control_pass, control_text, measures, parse_reader, prompt, schedule

HERE = Path(__file__).resolve().parent
COMPANIES = json.loads((HERE / "companies.json").read_text(encoding="utf-8"))


class StudyTests(unittest.TestCase):
    def test_heldout_grid_and_only_intended_prompt_difference(self):
        old = json.loads((HERE.parent / "data" / "companies.json").read_text(encoding="utf-8"))
        self.assertTrue({c["facts"]["Company"] for c in old}.isdisjoint(c["facts"]["Company"] for c in COMPANIES))
        self.assertEqual(len(COMPANIES), 10)
        self.assertEqual(sum(c["team_type"] == "solo" for c in COMPANIES), 5)
        rows = schedule(COMPANIES)
        self.assertEqual(rows, schedule(COMPANIES))
        self.assertEqual(len({(r['company_id'], r['condition']) for r in rows}), 30)
        for c in COMPANIES:
            self.assertEqual(prompt(c, "E"), prompt(c, "C") + "\n" + SELECT)
            self.assertTrue(prompt(c, "C").startswith(prompt(c, "A")))
        for i in range(0, 30, 3):
            self.assertEqual(len({r['company_id'] for r in rows[i:i+3]}), 1)
            self.assertEqual({r['condition'] for r in rows[i:i+3]}, set(CONDITIONS))

    def test_invalid_judge_is_never_clean(self):
        copy = "Our team has 97 employees."
        for raw in ('{}', '{"claims": null}', '{"claims": [{"category":"unknown", "quote":"97"}]}',
                    '{"claims": [{"category":"team", "quote":"not in this copy"}]}',
                    '{"claims": [{"category":"team", "quote":""}]}'):
            self.assertIsNone(parse_reader(raw, copy))
        self.assertEqual(parse_reader('{"claims": []}', copy)["total"], 0)
        r = parse_reader('```json\n{"claims":[{"quote":"97 employees", "category":"team"}]}\n```', copy)
        self.assertEqual(r["total"], 1)
        self.assertTrue(control_pass("wrong_team", r))

    def test_text_metrics_and_control_construction(self):
        c = {"facts": {"Company":"one two three four five"}}
        self.assertEqual(measures(c, "one two three four five")["overlap"], 1)
        self.assertEqual(measures(c, "different words live here")["overlap"], 0)
        self.assertGreater(measures(c, "one two three four one two three four")["repeat_share"], 0)
        for c in COMPANIES:
            self.assertIn(c["facts"]["Price"], control_text(c, "supported"))
            self.assertNotIn("987", str(c["facts"]))
            self.assertNotIn("97 employees", str(c["facts"]))
            self.assertIn("$987", control_text(c, "wrong_price"))
            self.assertIn("97 employees", control_text(c, "wrong_team"))

    def test_standalone_tasks_compile_without_running(self):
        for name in ("writer_task.py", "control_task.py"):
            source = (HERE / name).read_text(encoding="utf-8")
            ast.parse(source)
            self.assertIn('"human_validation": False', source)
            self.assertNotIn("private/", source)


if __name__ == "__main__":
    unittest.main()
