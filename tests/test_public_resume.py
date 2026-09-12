"""Guard the public PDF against dark-theme tokens leaking onto white paper."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / 'scripts' / 'generate_public_resume.py'
spec = importlib.util.spec_from_file_location('generate_public_resume', SCRIPT)
resume = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resume)


def luminance(color):
    def linear(value):
        return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
    return sum(weight * linear(value) for weight, value in zip(
        (.2126, .7152, .0722), (color.red, color.green, color.blue)))


class PublicResumeTests(unittest.TestCase):
    def test_small_text_has_readable_print_contrast(self):
        for background in (resume.WHITE, resume.PALE):
            for ink in (resume.INK, resume.MUTED, resume.CRIMSON, resume.DEEP_CRIMSON):
                contrast = (luminance(background) + .05) / (luminance(ink) + .05)
                self.assertGreaterEqual(contrast, 4.5)

    def test_published_resume_has_current_role_and_preserves_history(self):
        resume.validate_resume(resume.DEFAULT_OUTPUT)
        reader = resume.PdfReader(resume.DEFAULT_OUTPUT)
        text = reader.pages[0].extract_text()
        self.assertIn('ASSOCIATE ENGINEER', text)
        self.assertIn('Open to jobs', text)
        self.assertIn('Telecom & Data Network Intern', text)
        self.assertIn('Associate Engineer', reader.metadata['/Title'])

    def test_header_role_line_stays_clear_of_contact_column(self):
        _, bold = resume.register_fonts()
        profile = resume.load_profile()
        role_line, specialty_line = resume.header_lines(profile)
        role_size = resume.fitted_font_size(role_line, bold, max_width=313, start_size=10)
        specialty_size = resume.fitted_font_size(specialty_line, bold, max_width=313, start_size=8.2)
        self.assertLessEqual(resume.pdfmetrics.stringWidth(role_line, bold, role_size), 313)
        self.assertLessEqual(resume.pdfmetrics.stringWidth(specialty_line, bold, specialty_size), 313)


if __name__ == '__main__':
    unittest.main()
