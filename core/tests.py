from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import os


class AdminPanelThemeAndBrandingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="testadmin",
            password="testpassword123",
            email="testadmin@ceis.edu.co"
        )

    def test_admin_site_header(self):
        from panel_rector.admin_site import AthenaAdminSite
        from django.contrib import admin
        self.assertIn("Panel Administrativo", AthenaAdminSite.site_header)
        self.assertNotIn("Panel del Rector", AthenaAdminSite.site_header)

    def test_admin_login_page_branding(self):
        response = self.client.get(reverse("admin:login"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("Panel Administrativo", content)
        self.assertNotIn("Panel del Rector", content)
        self.assertIn("theme-toggle", content)

    def test_admin_index_authenticated(self):
        self.client.login(username="testadmin", password="testpassword123")
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("Panel Administrativo", content)
        self.assertNotIn("Panel del Rector", content)
        self.assertIn("theme-toggle", content)

    def test_css_contains_light_mode_tokens(self):
        css_path = os.path.join(os.path.dirname(__file__), "..", "static", "admin", "css", "athena_panel.css")
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()

        self.assertIn('html[data-theme="light"]', css)
        self.assertIn('html[data-theme="dark"]', css)
        self.assertIn('--body-bg: #f8fafc;', css)
        self.assertIn('.theme-toggle', css)
        self.assertNotIn("Panel del Rector", css)
