import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import sys

try:
    import PyPDF2
except ImportError:
    import pypdf as PyPDF2

    sys.modules["PyPDF2"] = PyPDF2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import index as app


class MetadataExtractorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        self.plain_image = os.path.join(self.temp_dir.name, "plain.jpg")
        Image.new("RGB", (64, 48), "#356aa0").save(self.plain_image)

        self.exif_image = os.path.join(self.temp_dir.name, "camera.jpg")
        exif = Image.Exif()
        exif[271] = "Test Camera Company"
        exif[272] = "Model X"
        exif[306] = "2026:07:27 10:15:00"
        Image.new("RGB", (80, 60), "#29415a").save(
            self.exif_image, exif=exif
        )

        self.pdf_path = os.path.join(self.temp_dir.name, "sample.pdf")
        writer = PyPDF2.PdfWriter()
        writer.add_blank_page(width=200, height=200)
        writer.add_metadata(
            {
                "/Title": "Metadata Test",
                "/Author": "Coursework Student",
                "/Creator": "Automated Test",
            }
        )
        with open(self.pdf_path, "wb") as stream:
            writer.write(stream)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_degree_conversion(self):
        result = app._convert_to_degrees((27, 42, 30))
        self.assertAlmostEqual(result, 27.7083333333, places=6)

    def test_gps_positive_and_negative_hemispheres(self):
        north_east = app.extract_gps(
            {1: "N", 2: (27, 42, 30), 3: "E", 4: (85, 19, 30)}
        )
        south_west = app.extract_gps(
            {1: "S", 2: (27, 42, 30), 3: "W", 4: (85, 19, 30)}
        )
        self.assertGreater(north_east[0], 0)
        self.assertGreater(north_east[1], 0)
        self.assertLess(south_west[0], 0)
        self.assertLess(south_west[1], 0)

    def test_classification_rules(self):
        self.assertEqual(app.classify("GPSLatitude"), "sensitive")
        self.assertEqual(app.classify("DateTimeOriginal"), "warning")
        self.assertEqual(app.classify("Dimensions"), "normal")

    def test_plain_image_metadata(self):
        rows = app.extract_image_metadata(self.plain_image)
        values = {row["key"]: row["value"] for row in rows}
        self.assertEqual(values["Format"], "JPEG")
        self.assertEqual(values["Dimensions"], "64 × 48 px")
        self.assertIn("No EXIF metadata", values["EXIF Data"])

    def test_image_exif_categories(self):
        rows = app.extract_image_metadata(self.exif_image)
        categories = {row["key"]: row["category"] for row in rows}
        self.assertEqual(categories["Make"], "warning")
        self.assertEqual(categories["Model"], "warning")
        self.assertEqual(categories["DateTime"], "warning")

    def test_pdf_metadata(self):
        rows = app.extract_pdf_metadata(self.pdf_path)
        values = {row["key"]: row["value"] for row in rows}
        categories = {row["key"]: row["category"] for row in rows}
        self.assertEqual(values["Pages"], "1")
        self.assertEqual(values["Title"], "Metadata Test")
        self.assertEqual(categories["Author"], "sensitive")
        self.assertEqual(categories["Creator"], "warning")

    def test_missing_image_returns_error_row(self):
        rows = app.extract_image_metadata(
            os.path.join(self.temp_dir.name, "missing.jpg")
        )
        self.assertEqual(rows[0]["key"], "Error")
        self.assertEqual(rows[0]["category"], "sensitive")

    def test_unsupported_extension_is_rejected(self):
        fake_app = object.__new__(app.MetadataExtractorApp)
        fake_app._current_file = ""
        fake_app._populate = lambda rows, path: self.fail(
            "Unsupported input should not be populated"
        )
        with patch.object(app.messagebox, "showwarning") as warning:
            fake_app._analyse(
                os.path.join(self.temp_dir.name, "notes.txt")
            )
        warning.assert_called_once()
        self.assertEqual(warning.call_args.args[0], "Unsupported")

    def test_image_dispatch_calls_populate(self):
        fake_app = object.__new__(app.MetadataExtractorApp)
        captured = {}
        fake_app._populate = lambda rows, path: captured.update(
            {"rows": rows, "path": path}
        )
        fake_app._analyse(self.plain_image)
        self.assertEqual(captured["path"], self.plain_image)
        self.assertGreaterEqual(len(captured["rows"]), 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
