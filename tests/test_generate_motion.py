import importlib.util
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_motion.py"
spec = importlib.util.spec_from_file_location("generate_motion", SCRIPT)
generate_motion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_motion)


class GenerateMotionTests(unittest.TestCase):
    def test_responsive_reels_are_compact_and_genuinely_animated(self):
        for mobile, size in ((False, (1200, 480)), (True, (600, 760))):
            with self.subTest(mobile=mobile):
                payload = generate_motion.build_systems_reel_gif(mobile)
                self.assertLess(len(payload), 500_000)
                with Image.open(BytesIO(payload)) as image:
                    self.assertEqual(image.format, "GIF")
                    self.assertEqual(image.size, size)
                    self.assertTrue(image.is_animated)
                    self.assertEqual(image.n_frames, generate_motion.FRAME_COUNT)
                    self.assertEqual(image.info.get("loop"), 0)
                    self.assertEqual(image.info.get("duration"), generate_motion.FRAME_DURATION)
                    first = image.convert("RGB")
                    image.seek(image.n_frames // 2)
                    middle = image.convert("RGB")
                    self.assertIsNotNone(ImageChops.difference(first, middle).getbbox())

    def test_reel_names_all_six_visual_worlds(self):
        source = generate_motion.build_frame(0, mobile=False)
        self.assertEqual(source.size, (1200, 480))
        labels = [scene[1] for scene in generate_motion.SCENES]
        for label in ("PORTFOLIO", "HELIOS", "ZENITH", "VISION", "TALKS", "TOKEN USAGE"):
            self.assertIn(label, labels)

    def test_each_motion_world_uses_its_own_design_token_palette(self):
        self.assertEqual(len(generate_motion.SCENES), 6)
        self.assertEqual(len({colors[2] for colors in generate_motion.MOTION_PALETTES.values()}), 6)
        for (code, label, _note, _renderer, colors), kind in zip(
            generate_motion.SCENES, generate_motion.MOTION_PALETTES
        ):
            with self.subTest(world=f"{code} {label}"):
                self.assertEqual(colors, generate_motion.MOTION_PALETTES[kind])
                self.assertLessEqual(max(colors[0]), 20)
                self.assertLessEqual(max(colors[1]), 60)

    def test_posters_are_first_frames_and_motion_is_periodic(self):
        for mobile in (False, True):
            poster = generate_motion.build_frame(0, mobile)
            cycle = generate_motion.build_frame(generate_motion.FRAME_COUNT, mobile)
            self.assertIsNone(ImageChops.difference(poster, cycle).getbbox())
            visible_colors = {color for _count, color in poster.convert("RGB").getcolors(1_000_000)}
            for palette in generate_motion.MOTION_PALETTES.values():
                self.assertIn(palette[2], visible_colors)
            buffer = BytesIO()
            poster.save(buffer, format="PNG", optimize=True)
            self.assertLess(len(buffer.getvalue()), 50_000)


if __name__ == "__main__":
    unittest.main()
