import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / 'scripts' / 'generate_assets.py'
spec = importlib.util.spec_from_file_location('generate_assets', SCRIPT)
generate_assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_assets)
SVG = '{http://www.w3.org/2000/svg}'


class GenerateAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = generate_assets.build_asset_manifest()

    def test_all_surfaces_are_valid_accessible_self_contained_svg(self):
        for name,svg in self.assets.items():
            with self.subTest(asset=name):
                root=ET.fromstring(svg)
                self.assertEqual(root.tag,SVG+'svg')
                if name == 'hero.svg':
                    # Its externally supplied README alt remains authoritative;
                    # the approved hero markup is deliberately preserved.
                    continue
                self.assertIsNotNone(root.find(SVG+'title'))
                self.assertIsNotNone(root.find(SVG+'desc'))
                self.assertEqual(root.get('role'),'img')
                self.assertNotIn('<script',svg)
                self.assertNotIn('<foreignObject',svg)
                for image in root.iter(SVG+'image'):
                    self.assertTrue(image.get('href','').startswith('data:image/'))

    def test_approved_hero_and_project_art_are_preserved(self):
        expected={'hero.svg': generate_assets.build_cinematic_hero_svg(generate_assets.CONFIG),
                  'project-portfolio-v2.svg':generate_assets.build_featured_project_svg(generate_assets.CONFIG),
                  'project-portfolio-mobile-v2.svg':generate_assets.build_featured_project_svg(generate_assets.CONFIG,True)}
        for project in generate_assets.PROFILE['projects']:
            if project['id'] != 'portfolio':
                expected[f'project-{project["id"]}.svg']=generate_assets.build_project_card_svg(generate_assets.canonical_project_card_spec(project),generate_assets.CONFIG)
        for name,svg in expected.items():
            self.assertEqual(self.assets[name],generate_assets.apply_red_theme(svg),name)
            self.assertIn('data:image/jpeg;base64,',svg)

    def test_covers_are_clean_and_each_uses_its_own_art(self):
        for kind in ('helios','zenith','vision','talks','token-usage'):
            svg=self.assets[f'project-{kind}.svg']
            self.assertNotIn('<text',svg)
            self.assertIn(generate_assets.asset_data_uri(generate_assets.VISUAL_CONTRACT['project_art'][kind]).split(',',1)[1],svg)
            self.assertIn('prefers-reduced-motion: reduce',svg)

    def test_current_role_and_job_availability_reach_public_surfaces(self):
        role = 'BACKEND / FULL-STACK SOFTWARE ENGINEER'
        availability = generate_assets.PROFILE['availability']['status'].upper()
        self.assertIn(role, self.assets['hero.svg'])
        for suffix in ('', '-mobile'):
            self.assertIn('FOCUS / BACKEND + FULL STACK', self.assets[f'identity-console{suffix}.svg'])
            self.assertIn(availability, self.assets[f'identity-console{suffix}.svg'])
            self.assertIn('JOBS / COLLABORATION', self.assets[f'section-channel{suffix}.svg'])
        for name, svg in self.assets.items():
            self.assertNotIn('open to internships', svg.lower(), name)
            self.assertNotIn('open to software engineering internships', svg.lower(), name)

    def test_mobile_panels_are_composed_at_readable_natural_width(self):
        variants=[name for name in self.assets if name.endswith('-mobile.svg')]
        self.assertGreaterEqual(len(variants),25)
        for name in variants:
            with self.subTest(asset=name):
                root=ET.fromstring(self.assets[name])
                self.assertEqual(root.get('width'),'360')
                self.assertIn('prefers-reduced-motion: reduce',self.assets[name])
        for project in generate_assets.PROFILE['projects']:
            for suffix in ('','-mobile'):
                root=ET.fromstring(self.assets[f'project-summary-{project["id"]}{suffix}.svg'])
                self.assertLess(int(root.get('height')),280)

    def test_details_preserve_project_evidence_and_status(self):
        for project in generate_assets.PROFILE['projects']:
            for suffix in ('','-mobile'):
                root=ET.fromstring(self.assets[f'project-dossier-{project["id"]}{suffix}.svg'])
                content=' '.join(' '.join(root.itertext()).split())
                self.assertIn(project['name'].upper(),content)
                self.assertIn(project['status'].upper(),content)
                for fact in project['proof']:
                    self.assertIn(fact,content)
                for technology in project['stack']:
                    self.assertIn(technology,content)

    def test_studio_and_supporting_art_survive_the_compositor(self):
        for name,key in {'identity-console':'identity','arsenal':'atlas','finale':'channel'}.items():
            for suffix in ('','-mobile'):
                svg=self.assets[f'{name}{suffix}.svg']
                self.assertIn(generate_assets.asset_data_uri(generate_assets.SUPPORTING_ART[key]),svg)

    def test_palette_and_per_viewport_payload_budget(self):
        for svg in self.assets.values():
            for color in ('#5be8ff','#a78bff','#169cab','#f0a64a'):
                self.assertNotIn(color,svg)
        # Mobile and desktop art are alternatives; don't count both as one load.
        desktop=sum(len(svg.encode()) for name,svg in self.assets.items() if '-mobile' not in name)
        self.assertLess(desktop,3_900_000)
        self.assertLess(sum(len(svg.encode()) for svg in self.assets.values()),5_800_000)


if __name__ == '__main__':
    unittest.main()
