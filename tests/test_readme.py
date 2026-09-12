import importlib.util
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('generate_readme',ROOT/'scripts'/'generate_readme.py')
generate_readme=importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_readme)


class ReadmeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile=generate_readme.load_profile()
        cls.readme=(ROOT/'README.md').read_text(encoding='utf-8')

    def test_readme_matches_canonical_generator(self):
        self.assertEqual(self.readme,generate_readme.render_readme(self.profile))

    def test_all_six_projects_have_cover_details_and_source(self):
        expected=('portfolio','vision','zenith','helios','token-usage','talks')
        self.assertEqual(generate_readme.SELECTED_PROJECT_IDS,expected)
        positions=[]
        for pid in expected:
            project=next(x for x in self.profile['projects'] if x['id']==pid)
            positions.append(self.readme.index(f'<a id="project-{pid}">'))
            self.assertIn(project['repo'],self.readme)
            self.assertIn(generate_readme.PROJECT_VISUALS[pid],self.readme)
            self.assertIn(f'project-summary-{pid}-mobile.svg',self.readme)
            for fact in project['proof']:
                self.assertIn(fact,self.readme)
        self.assertEqual(positions,sorted(positions))

    def test_every_authored_link_is_visual_and_anchors_resolve(self):
        self.assertEqual(re.findall(r'(?<!!)\[[^\]]+\]\([^)]+\)',self.readme),[])
        links=re.findall(r'<a href="[^"]+">.*?</a>',self.readme,re.DOTALL)
        self.assertGreaterEqual(len(links),30)
        self.assertTrue(all('<img ' in link for link in links))
        targets=set(re.findall(r'<a href="#([^"]+)"',self.readme))
        anchors=re.findall(r'<a id="([^"]+)"',self.readme)
        self.assertEqual(targets,{'user-content-'+anchor for anchor in anchors})
        self.assertEqual(len(anchors),len(set(anchors)))

    def test_every_referenced_visual_is_generated_or_independently_published(self):
        from generate_assets import build_asset_manifest
        generated=set(build_asset_manifest())
        independent={'stats.svg','stats-mobile.svg','contribution-stream.svg','contribution-stream-mobile.svg',*generate_readme.MOTION_ASSETS}
        referenced=set(re.findall(r'/output/([a-z0-9-]+\.(?:svg|gif|png))',self.readme))
        self.assertEqual(referenced,generated|independent)

    def test_native_disclosures_and_mobile_motion_fallbacks(self):
        self.assertEqual(self.readme.count('<details>'),7)
        self.assertEqual(self.readme.count('</details>'),7)
        self.assertNotIn('<details open',self.readme)
        self.assertIn('(max-width: 600px) and (prefers-reduced-motion: reduce)',self.readme)
        for filename in generate_readme.RESPONSIVE_ASSETS:
            self.assertIn(filename.replace('.svg','-mobile.svg'),self.readme)
        self.assertGreater(self.readme.index('systems-reel-v8.gif'),self.readme.index('section-operator.svg'))

    def test_images_have_accessible_copy_and_mobile_safe_widths(self):
        tags=re.findall(r'<img\b[^>]*?/>',self.readme)
        self.assertTrue(all(re.search(r'alt="[^"]+"',tag) for tag in tags))
        self.assertTrue(all(width in {'100%','95%','350','145'} for width in re.findall(r'width="([^"]+)"',self.readme)))
        self.assertNotIn('<table',self.readme)
        visible=re.sub(r'<[^>]+>','',re.sub(r'<!--.*?-->','',self.readme,flags=re.S)).strip()
        self.assertEqual(visible,'')

    def test_privacy_and_views_are_preserved(self):
        lower=self.readme.lower()
        self.assertIn('mailto:ayushroy.dev@gmail.com',lower)
        self.assertIn('ayush_roy_resume_public.pdf',lower)
        self.assertIn('https://komarev.com/ghpvc/',lower)
        for forbidden in ('cgpa','yorayriniwnl@gmail.com','deep learning','convolutional neural network'):
            self.assertNotIn(forbidden,lower)

    def test_current_career_status_is_accessible_and_cache_busted(self):
        self.assertIn('Currently Associate Engineer · Automotive Industry.', self.readme)
        self.assertIn('Open to jobs', self.readme)
        self.assertNotIn('internships', self.readme.lower())
        for asset in ('hero.svg', 'identity-console.svg', 'identity-console-mobile.svg', 'section-channel.svg', 'section-channel-mobile.svg'):
            self.assertIn(f'/output/{asset}?rev=career-v1', self.readme)

    def test_original_cover_cache_versions_are_preserved(self):
        for filename in generate_readme.PROJECT_VISUALS.values():
            revision=generate_readme.ASSET_REVISIONS[filename]
            self.assertIn(f'/output/{filename}?rev={revision}',self.readme)


if __name__=='__main__':
    unittest.main()
