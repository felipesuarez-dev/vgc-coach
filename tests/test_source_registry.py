import copy
import importlib.util
import pathlib
import sys
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tools" / "render_source_registry_docs.py"
REGISTRY_PATH = REPO_ROOT / "docs" / "skills" / "shared" / "references" / "live-source-registry.yaml"
SHARED_MAP_PATH = REPO_ROOT / "docs" / "skills" / "shared" / "references" / "live-source-map.md"
LEGACY_MAP_PATH = REPO_ROOT / "docs" / "skills" / "vgc-meta-research" / "references" / "current-source-map.md"


def load_module():
    spec = importlib.util.spec_from_file_location("render_source_registry_docs", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SourceRegistryTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_registry_contains_expected_sources_and_stacks(self):
        registry = self.module.load_registry(REGISTRY_PATH)

        self.assertEqual(registry["minimum_stack"]["official"], 1)
        self.assertEqual(registry["minimum_stack"]["tournament_meta"], 1)
        self.assertEqual(registry["minimum_stack"]["broader_meta"], 1)
        self.assertEqual(registry["team_build_stack"]["official_roster"], 1)

        by_id = {entry["id"]: entry for entry in registry["sources"]}
        self.assertEqual(
            tuple(by_id),
            (
                "regulation-set-m-c",
                "official-roster-m-c",
                "championship-series-calendar",
                "championship-series-results",
                "infovgc",
                "labmaus",
                "limitless",
                "pokestats",
                "smogon",
                "pikalytics-champions",
                "pokebase",
                "pokepaste",
                "pokedata-events",
                "pokedata-standings",
                "victory-road",
                "regulation-set-m-d",
            ),
        )
        self.assertNotIn("championsmeta", by_id)
        self.assertNotIn("champions-lab", by_id)
        self.assertNotIn("championslab", by_id)

        regulation = by_id["regulation-set-m-c"]
        self.assertEqual(regulation["regulation_id"], "regulation-m-c")
        self.assertEqual(regulation["temporal_status"], "current")
        self.assertEqual(
            regulation["canonical_url"],
            "https://news.pokemon-home.com/en/page/816.html",
        )
        self.assertEqual(regulation["active_window"]["start"], "2026-09-09T02:00:00Z")
        self.assertEqual(regulation["active_window"]["end"], "2026-12-02T01:59:00Z")

        roster = by_id["official-roster-m-c"]
        self.assertEqual(roster["role"], "official_roster")
        self.assertEqual(roster["temporal_status"], "current")
        self.assertIn("roster_legality", roster["allowed_claim_types"])

        successor = by_id["regulation-set-m-d"]
        self.assertEqual(successor["regulation_id"], "regulation-m-d")
        self.assertEqual(successor["temporal_status"], "upcoming")
        self.assertFalse(successor["required_for_minimum_stack"])
        self.assertEqual(successor["active_window"]["start"], "2026-12-02T02:00:00Z")
        self.assertEqual(successor["active_window"]["end"], "2027-03-03T01:59:00Z")

    def test_current_meta_sources_require_freshness_rules(self):
        registry = self.module.load_registry(REGISTRY_PATH)
        by_id = {entry["id"]: entry for entry in registry["sources"]}

        self.assertEqual(by_id["infovgc"]["freshness"]["max_age_days"], 1)
        self.assertEqual(by_id["labmaus"]["freshness"]["max_age_days"], 1)
        self.assertEqual(by_id["limitless"]["freshness"]["max_age_days"], 1)
        self.assertEqual(by_id["smogon"]["freshness"]["max_age_days"], 7)
        self.assertEqual(by_id["pikalytics-champions"]["freshness"]["max_age_days"], 7)
        self.assertIn("fetched_at", by_id["infovgc"]["required_evidence_fields"])
        self.assertIn("source_url", by_id["labmaus"]["required_evidence_fields"])

    def test_labmaus_fallback_uses_the_repo_fetcher(self):
        registry = self.module.load_registry(REGISTRY_PATH)
        by_id = {entry["id"]: entry for entry in registry["sources"]}
        fallback = " ".join(by_id["labmaus"]["fallback_if_unavailable"])

        self.assertIn("python3 tools/fetch_labmaus.py", fallback)
        self.assertIn("do not use generic `curl -k`", fallback)

    def test_registry_rejects_missing_required_evidence_fields(self):
        payload = copy.deepcopy(self.module.load_registry(REGISTRY_PATH))
        del payload["sources"][0]["required_evidence_fields"]

        with self.assertRaisesRegex(ValueError, "required_evidence_fields"):
            self.module.validate_registry(payload)

    def test_official_regulation_requires_regulation_id(self):
        payload = copy.deepcopy(self.module.load_registry(REGISTRY_PATH))
        del payload["sources"][0]["regulation_id"]

        with self.assertRaisesRegex(ValueError, "regulation_id"):
            self.module.validate_registry(payload)

    def test_official_roster_requires_active_window(self):
        payload = copy.deepcopy(self.module.load_registry(REGISTRY_PATH))
        del payload["sources"][1]["active_window"]

        with self.assertRaisesRegex(ValueError, "active_window"):
            self.module.validate_registry(payload)

    def test_registry_rejects_missing_minimum_stack_url(self):
        payload = copy.deepcopy(self.module.load_registry(REGISTRY_PATH))
        payload["sources"][0]["canonical_url"] = ""

        with self.assertRaisesRegex(ValueError, "canonical_url"):
            self.module.validate_registry(payload)

    def test_registry_rejects_current_meta_source_without_freshness(self):
        payload = copy.deepcopy(self.module.load_registry(REGISTRY_PATH))
        del payload["sources"][4]["freshness"]

        with self.assertRaisesRegex(ValueError, "freshness"):
            self.module.validate_registry(payload)

    def test_upcoming_official_source_does_not_satisfy_current_stack(self):
        payload = copy.deepcopy(self.module.load_registry(REGISTRY_PATH))
        current = payload["sources"][0]
        successor = payload["sources"][-1]
        current["temporal_status"] = "upcoming"
        successor["required_for_minimum_stack"] = True

        with self.assertRaisesRegex(ValueError, "current official_regulation"):
            self.module.validate_registry(payload)

    def test_upcoming_roster_does_not_satisfy_team_build_stack(self):
        payload = copy.deepcopy(self.module.load_registry(REGISTRY_PATH))
        current_roster = payload["sources"][1]
        upcoming_roster = copy.deepcopy(current_roster)
        upcoming_roster.update(
            {
                "id": "official-roster-m-d",
                "display_name": "Regulation M-D Eligible Roster",
                "priority": 17,
                "regulation_id": "regulation-m-d",
                "temporal_status": "upcoming",
                "canonical_url": "https://example.com/m-d-roster",
                "active_window": {
                    "start": "2026-12-02T02:00:00Z",
                    "end": "2027-03-03T01:59:00Z",
                },
                "required_for_minimum_stack": True,
            }
        )
        current_roster["required_for_minimum_stack"] = False
        payload["sources"].append(upcoming_roster)

        with self.assertRaisesRegex(ValueError, "team_build_stack.official_roster"):
            self.module.validate_registry(payload)

    def test_rendered_shared_map_matches_generated_output(self):
        registry = self.module.load_registry(REGISTRY_PATH)
        rendered = self.module.render_markdown(registry)
        committed = SHARED_MAP_PATH.read_text()

        self.assertEqual(committed, rendered)
        self.assertIn("# Shared Live Source Map", committed)
        self.assertIn("## Recommended Minimum Live Stack", committed)
        self.assertIn("## Recommended Team-Build Legality Stack", committed)
        self.assertIn("Regulation M-C Eligible Roster", committed)
        self.assertIn("Temporal status: `upcoming`", committed)
        self.assertIn("Regulation Set M-D", committed)
        self.assertIn("Role: `official_roster`", committed)
        self.assertIn("Role: `event_standings`", committed)
        self.assertIn("2027-03-03T01:59:00Z", committed)

    def test_legacy_meta_research_map_is_wrapper_to_shared_doc(self):
        content = LEGACY_MAP_PATH.read_text()

        self.assertIn("Compatibility wrapper", content)
        self.assertIn("../../shared/references/live-source-map.md", content)


if __name__ == "__main__":
    unittest.main()
