from django.test import TestCase
from django.urls import reverse

from main import models


class SnapshotCreateTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)

    def test_snapshot_create(self):
        data = {
            "title": "New blog",
            "body": "Hey audience!",
        }
        response = self.client.post(
            reverse("snapshot_create"),
            data=data,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.Snapshot.objects.all().count(), 1)
        self.assertEqual(models.Snapshot.objects.all().first().title, data["title"])
        self.assertEqual(models.Snapshot.objects.all().first().body, data["body"])
        self.assertEqual(models.Snapshot.objects.all().first().owner, self.user)


class SnapshotDetailTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.snapshot = models.Snapshot.objects.create(
            owner=self.user,
            title="New blog",
            body="hello world",
        )

    def test_snapshot_detail(self):
        response = self.client.get(
            reverse("snapshot_detail", args=(self.snapshot.id,)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.snapshot.id)
        self.assertContains(response, self.snapshot.title)


class SnapshotListTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(username="alice")
        self.client.force_login(self.user)
        self.snapshot_a = models.Snapshot.objects.create(
            owner=self.user,
            title="New blog",
            body="hello world",
        )
        self.snapshot_b = models.Snapshot.objects.create(
            owner=self.user,
            title="New blog",
            body="Hello new world",
        )

    def test_snapshot_list(self):
        response = self.client.get(reverse("snapshot_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.snapshot_a.id)
        self.assertContains(response, self.snapshot_a.title)
        self.assertContains(response, self.snapshot_b.id)
        self.assertContains(response, self.snapshot_b.title)


class SnapshotDetailNonOwnerTestCase(TestCase):
    """Test snapshots cannot be accessed by non-owners."""

    def setUp(self):
        self.user_a = models.User.objects.create(username="alice")
        self.snapshot_a = models.Snapshot.objects.create(
            owner=self.user_a,
            title="New blog",
            body="hello world",
        )

    def test_snapshot_detail_nonauth(self):
        self.user_b = models.User.objects.create(username="bob")
        self.client.force_login(self.user_b)
        response = self.client.get(
            reverse("snapshot_detail", args=(self.snapshot_a.id,)),
        )
        self.assertEqual(response.status_code, 403)


class SnapshotListNonownerTestCase(TestCase):
    """Test snapshot list cannot be accessed by non-owners."""

    def setUp(self):
        self.user_a = models.User.objects.create(username="alice")
        self.snapshot_a = models.Snapshot.objects.create(
            owner=self.user_a,
            title="New blog",
            body="hello world",
        )

    def test_snapshot_detail_nonauth(self):
        self.user_b = models.User.objects.create(username="bob")
        self.client.force_login(self.user_b)
        response = self.client.get(
            reverse("snapshot_list"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "none")
