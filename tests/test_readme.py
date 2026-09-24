import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("generate_readme", ROOT / "scripts" / "generate_readme.py")
generate_readme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_readme)


class ReadmeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = generate_readme.load_profile()
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_readme_matches_canonical_generator(self):
        self.assertEqual(self.readme, generate_readme.render_readme(self.profile))

    def test_all_six_projects_have_selectable_copy_art_and_links(self):
        expected = ("portfolio", "vision", "zenith", "helios", "token-usage", "talks")
        self.assertEqual(generate_readme.SELECTED_PROJECT_IDS, expected)
        positions = []
        for pid in expected:
            project = next(item for item in self.profile["projects"] if item["id"] == pid)
            positions.append(self.readme.index(f'<a id="project-{pid}"></a>'))
            self.assertIn(project["name"], self.readme)
            self.assertIn(project["summary"], self.readme)
            self.assertIn(project["repo"], self.readme)
            self.assertIn(generate_readme.PROJECT_VISUALS[pid], self.readme)
            self.assertIn(f'`{project["status"]}`', self.readme)
            for fact in project["proof"]:
                self.assertIn(fact, self.readme)
        self.assertEqual(positions, sorted(positions))

    def test_human_readable_links_and_project_anchors_resolve(self):
        markdown_links = re.findall(r"(?<!!)\[[^\]]+\]\([^)]+\)", self.readme)
        self.assertGreaterEqual(len(markdown_links), 20)
        targets = set(re.findall(r"\]\(#([^)]*)\)", self.readme))
        anchors = re.findall(r'<a id="([^"]+)"', self.readme)
        self.assertEqual(targets, {"user-content-" + anchor for anchor in anchors})
        self.assertEqual(len(anchors), 6)
        self.assertEqual(len(anchors), len(set(anchors)))

    def test_every_referenced_visual_is_generated_or_independently_published(self):
        from generate_assets import build_asset_manifest

        generated = set(build_asset_manifest())
        independent = {"stats.svg", "contribution-stream.svg", *generate_readme.MOTION_ASSETS}
        referenced = set(re.findall(r"/output/([a-z0-9-]+\.(?:svg|gif|png))", self.readme))
        self.assertTrue(referenced <= generated | independent)
        self.assertTrue({"hero.svg", *generate_readme.PROJECT_VISUALS.values()} <= referenced)

    def test_motion_is_prominent_responsive_and_reduced_motion_safe(self):
        self.assertIn("(max-width: 600px) and (prefers-reduced-motion: reduce)", self.readme)
        self.assertLess(self.readme.index("systems-reel-v9.gif"), self.readme.index("## Selected systems"))
        for filename in generate_readme.MOTION_ASSETS:
            self.assertIn(filename, self.readme)
        self.assertEqual(self.readme.count("<details>"), 7)
        self.assertEqual(self.readme.count("</details>"), 7)
        self.assertNotIn("<details open", self.readme)

    def test_images_have_meaningful_alt_text_and_readme_has_selectable_copy(self):
        tags = re.findall(r"<img\b[^>]*?/>", self.readme)
        self.assertGreaterEqual(len(tags), 4)
        self.assertTrue(all(re.search(r'alt="[^\"]+"', tag) for tag in tags))
        self.assertTrue(all(width in {"100%", "350"} for width in re.findall(r'width="([^\"]+)"', self.readme)))
        self.assertNotIn("<table", self.readme.lower())
        visible = re.sub(r"<[^>]+>", "", re.sub(r"<!--.*?-->", "", self.readme, flags=re.S)).strip()
        self.assertGreater(len(visible), 2500)
        for phrase in ("Open to jobs", "Bengaluru", "Associate Engineer", "Selected systems", "Field notes", "Open channel"):
            self.assertIn(phrase, visible)

    def test_privacy_and_contact_links_are_preserved(self):
        lower = self.readme.lower()
        self.assertIn("mailto:ayushroy.dev@gmail.com", lower)
        self.assertIn("ayush_roy_resume_public.pdf", lower)
        self.assertIn("https://komarev.com/ghpvc/", lower)
        for forbidden in ("cgpa", "yorayriniwnl@gmail.com", "deep learning", "convolutional neural network"):
            self.assertNotIn(forbidden, lower)

    def test_career_status_is_plain_text_and_core_visuals_are_cache_busted(self):
        self.assertIn("Associate Engineer · Automotive Technology Services", self.readme)
        self.assertIn("Open to jobs", self.readme)
        self.assertNotIn("internships", self.readme.lower())
        for asset in ("hero.svg", *generate_readme.PROJECT_VISUALS.values()):
            revision = generate_readme.ASSET_REVISIONS[asset]
            self.assertIn(f"/output/{asset}?rev={revision}", self.readme)


if __name__ == "__main__":
    unittest.main()
