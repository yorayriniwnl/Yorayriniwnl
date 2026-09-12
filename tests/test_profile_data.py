import hashlib
import json
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).parents[1]
DATA_PATH = ROOT / "data" / "profile.json"


class ProfileDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    def test_validator_accepts_canonical_data(self):
        from scripts.profile_data import validate_profile

        validate_profile(self.profile)

    def test_repository_audit_locks_public_scope_and_proposed_pins(self):
        from scripts.profile_data import load_repository_audit

        audit = load_repository_audit()
        self.assertEqual(audit["account"], "yorayriniwnl")
        self.assertEqual(audit["repository_count_expected"], 25)
        self.assertEqual(audit["repository_count_audited"], 25)
        self.assertEqual(audit["missing_local_clones"], [])
        self.assertEqual(
            [item["name"] for item in audit["proposed_pins"]],
            [
                "Yor-Ayrin-iwnl",
                "yor-talksv2",
                "Yor-Helios",
                "Yor-Zenith",
                "Yor-Ai-vs-real-image",
                "Hyperliquid_Analysis",
            ],
        )

    def test_design_tokens_are_the_palette_source_of_truth(self):
        from scripts.profile_data import load_design_tokens

        tokens = load_design_tokens()
        self.assertEqual(tokens["color"]["crimson"], "#ff1f2d")
        self.assertEqual(tokens["color"]["deepCrimson"], "#8f0014")
        self.assertEqual(set(tokens["worlds"]), {"portfolio", "helios", "zenith", "vision", "talks", "token-usage"})
        self.assertEqual(
            self.profile["visual_contract"]["palette"]["deep_crimson"],
            tokens["color"]["deepCrimson"],
        )
        self.assertIn("reducedMotionMediaQuery", tokens["accessibility"])

    def test_public_contact_uses_professional_email_and_no_phone(self):
        serialized = json.dumps(self.profile, ensure_ascii=False)

        self.assertEqual(self.profile["contact"]["email"], "ayushroy.dev@gmail.com")
        self.assertNotIn("yorayriniwnl@gmail.com", serialized)
        self.assertNotIn("89189", serialized)

    def test_public_education_omits_cgpa(self):
        serialized = json.dumps(self.profile["education"], ensure_ascii=False).lower()

        self.assertNotIn("cgpa", serialized)
        self.assertNotIn("7.00/10", serialized)

    def test_current_role_and_availability_match_user_update(self):
        self.assertEqual(self.profile['identity']['role'], 'Associate Engineer · Automotive Technology Services')
        self.assertEqual(self.profile['availability']['status'], 'Open to jobs')

    def test_applied_ml_claim_matches_resume_evidence(self):
        vision = next(project for project in self.profile["projects"] if project["id"] == "vision")
        evidence = " ".join([vision["summary"], *vision["proof"], *vision["stack"]]).lower()

        for term in ("lbp", "glcm", "svm", "78.5%", "local inference"):
            self.assertIn(term, evidence)
        self.assertNotIn("cnn", evidence)
        self.assertNotIn("deep learning", evidence)

    def test_approved_hero_binary_is_unchanged(self):
        contract = self.profile["visual_contract"]
        digest = hashlib.sha256((ROOT / contract["approved_hero"]).read_bytes()).hexdigest()

        self.assertEqual(digest, contract["approved_hero_sha256"])

    def test_source_delivery_and_github_visual_contract_is_complete(self):
        contract = self.profile["visual_contract"]
        derivatives = [contract["optimized_hero"], contract["delivery"]["flagship_art"], *contract["project_art"].values()]

        self.assertEqual(set(contract["project_art"]), {"helios", "zenith", "vision", "talks", "token-usage"})
        self.assertEqual(contract["project_art"], contract["delivery"]["project_art"])
        self.assertEqual(set(contract["source"]["supporting_art"]), {"identity", "atlas", "channel"})
        self.assertEqual(set(contract["delivery"]["supporting_art"]), {"identity", "atlas", "channel"})
        self.assertEqual(contract["source"]["hero"], contract["approved_hero"])
        self.assertTrue(contract["source"]["flagship_art"].endswith("cinematic-crimson-v6.png"))
        self.assertTrue(contract["delivery"]["flagship_art"].endswith("cinematic-crimson-v6-optimized.jpg"))
        for relative_path in derivatives:
            with self.subTest(asset=relative_path):
                path = ROOT / relative_path
                self.assertTrue(path.is_file())
                self.assertEqual(path.suffix, ".jpg")

        expected_project_versions = {
            "helios": "v8",
            "zenith": "v7",
            "vision": "v9",
            "talks": "v7",
            "token-usage": "v8",
        }
        for project_id, relative_path in contract["source"]["project_art"].items():
            with self.subTest(project=project_id):
                self.assertTrue(relative_path.endswith(f"-cinematic-crimson-{expected_project_versions[project_id]}.png"))
                self.assertTrue((ROOT / relative_path).is_file())
        for project_id, relative_path in contract["delivery"]["project_art"].items():
            with self.subTest(delivery=project_id):
                self.assertIn(
                    f"cinematic-crimson-{expected_project_versions[project_id]}-optimized.jpg",
                    relative_path,
                )
        for key, relative_path in contract["source"]["supporting_art"].items():
            with self.subTest(supporting_source=key):
                self.assertTrue(relative_path.endswith("-v1.png"))
                self.assertTrue((ROOT / relative_path).is_file())
        for key, relative_path in contract["delivery"]["supporting_art"].items():
            with self.subTest(supporting_delivery=key):
                self.assertTrue(relative_path.endswith("-v1-optimized.jpg"))
                self.assertTrue((ROOT / relative_path).is_file())
        github_paths = [
            contract["github_derivative"]["hero"],
            *contract["github_derivative"]["project_art"].values(),
        ]
        self.assertTrue(all(path.startswith("output/") for path in github_paths))

    def test_legacy_upscaled_visual_contract_is_explicitly_not_native_4k(self):
        contract = self.profile["visual_contract"]["high_resolution"]
        self.assertIn("legacy upscaled archive", contract["status"])
        self.assertIn("not a native 4K source", contract["status"])

        with Image.open(ROOT / contract["hero"]) as hero:
            self.assertEqual(hero.size, (3840, 1777))

        for project_id, relative_path in contract["project_art"].items():
            with self.subTest(project=project_id), Image.open(ROOT / relative_path) as image:
                self.assertEqual(image.size, (3840, 2160))
                if project_id == "token-usage":
                    self.assertIn("concept-crimson-v1-4k.jpg", relative_path)
                else:
                    self.assertIn("keyart-v5-4k.jpg", relative_path)


if __name__ == "__main__":
    unittest.main()
