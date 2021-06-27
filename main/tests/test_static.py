from django.test import TestCase
from django.urls import reverse


class StaticTestCase(TestCase):
    def test_modus(self):
        response = self.client.get(reverse("modus"))
        self.assertEqual(response.status_code, 200)

    def test_privacy(self):
        response = self.client.get(reverse("privacy"))
        self.assertEqual(response.status_code, 200)

    def test_guides_markdown(self):
        response = self.client.get(reverse("guides_markdown"))
        self.assertEqual(response.status_code, 200)

    def test_guides_images(self):
        response = self.client.get(reverse("guides_images"))
        self.assertEqual(response.status_code, 200)

    def test_comparisons(self):
        response = self.client.get(reverse("comparisons"))
        self.assertEqual(response.status_code, 200)

    def test_export(self):
        """Test export index page as an anon user."""
        response = self.client.get(reverse("export_index"))
        self.assertEqual(response.status_code, 200)
