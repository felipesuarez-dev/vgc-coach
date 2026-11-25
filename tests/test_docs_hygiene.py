from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEAD_SOURCE_PATTERN = ("championsmeta", "champions-lab", "championslab")
PERSONAL_PATH_PATTERNS = ("/home/felipe", "/Users/", "C:\\Users\\")


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if ".venv" not in path.parts and "node_modules" not in path.parts
    )


class DocsHygieneTests(unittest.TestCase):
    def test_evals_do_not_reference_retired_sources(self):
        offenders = []
        for path in markdown_files(REPO_ROOT / "data" / "fixtures" / "evals"):
            text = path.read_text().lower()
            if any(name in text for name in DEAD_SOURCE_PATTERN):
                offenders.append(path.relative_to(REPO_ROOT).as_posix())
        self.assertEqual(offenders, [])

    def test_live_skill_references_do_not_reference_retired_sources(self):
        offenders = []
        for path in markdown_files(REPO_ROOT / "docs" / "skills"):
            if path.name == "champions-reg-m-a-legality.md":
                continue
            text = path.read_text().lower()
            if any(name in text for name in DEAD_SOURCE_PATTERN):
                offenders.append(path.relative_to(REPO_ROOT).as_posix())
        self.assertEqual(offenders, [])

    def test_product_docs_do_not_contain_personal_machine_paths(self):
        offenders = []
        roots = [REPO_ROOT / "README.md", REPO_ROOT / "README.en.md"]
        roots.extend(markdown_files(REPO_ROOT / "docs"))
        for path in roots:
            if not path.exists():
                continue
            text = path.read_text()
            if any(pattern in text for pattern in PERSONAL_PATH_PATTERNS):
                offenders.append(path.relative_to(REPO_ROOT).as_posix())
        self.assertEqual(offenders, [])

    def test_skill_files_do_not_contain_ai_attribution_trailers(self):
        offenders = []
        for path in markdown_files(REPO_ROOT / "skills"):
            text = path.read_text()
            if "Co-Authored-By" in text or "Co-authored-by" in text:
                offenders.append(path.relative_to(REPO_ROOT).as_posix())
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
