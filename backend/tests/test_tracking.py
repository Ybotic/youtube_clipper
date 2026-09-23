import unittest

from backend.services.tracking import calculate_dynamic_crop


class DynamicCropTests(unittest.TestCase):
    def test_no_faces_uses_center_crop(self):
        crop = calculate_dynamic_crop({}, (1920, 1080))
        self.assertFalse(crop["tracked"])
        self.assertEqual(crop["x"], "656.00")

    def test_off_center_prominent_face_moves_crop(self):
        tracking = {
            "samples": [
                {"time": 0, "x": 1450, "y": 540, "face_width": 180, "face_height": 180},
                {"time": 1, "x": 1460, "y": 540, "face_width": 180, "face_height": 180},
            ]
        }
        crop = calculate_dynamic_crop(tracking, (1920, 1080), duration=1)
        self.assertTrue(crop["tracked"])
        self.assertNotEqual(crop["x"], "656.00")

    def test_moving_subject_crop_is_smoothed_and_interpolated(self):
        tracking = {
            "samples": [
                {"time": 0, "x": 400, "y": 540, "face_width": 120, "face_height": 120},
                {"time": 1, "x": 440, "y": 540, "face_width": 120, "face_height": 120},
                {"time": 2, "x": 500, "y": 540, "face_width": 120, "face_height": 120},
                {"time": 3, "x": 600, "y": 540, "face_width": 120, "face_height": 120},
                {"time": 4, "x": 700, "y": 540, "face_width": 120, "face_height": 120},
                {"time": 5, "x": 800, "y": 540, "face_width": 120, "face_height": 120},
            ]
        }
        crop = calculate_dynamic_crop(tracking, (1920, 1080), duration=5)
        self.assertTrue(crop["tracked"])
        self.assertIn("if(lt(t\\,5.000)", crop["x"])
        self.assertIn("t-0.000", crop["x"])

    def test_centered_face_keeps_centered_crop(self):
        tracking = {
            "samples": [
                {"time": 0, "x": 960, "y": 540, "face_width": 120, "face_height": 120},
                {"time": 1, "x": 960, "y": 540, "face_width": 120, "face_height": 120},
            ]
        }
        crop = calculate_dynamic_crop(tracking, (1920, 1080), duration=1)
        self.assertTrue(crop["tracked"])
        self.assertAlmostEqual(float(crop["x"]), 656.0, places=2)


if __name__ == "__main__":
    unittest.main()
