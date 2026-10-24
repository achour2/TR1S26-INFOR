from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from travelhub.models import destinations, voyages


class VoyageOwnershipPageTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("proprietaire", password="test-password-123")
        self.participant = User.objects.create_user("participant", password="test-password-123")
        self.trip = voyages.objects.create(
            titre="Voyage historique", description="Voyage de test",
            date_Debut=date(2031, 6, 1), date_Fin=date(2031, 6, 10),
            createur=None,
        )
        self.trip.utilisateurs.add(self.participant)
        self.destination = destinations.objects.create(
            ville="Québec", pays="Canada", date_Arrive=date(2031, 6, 2),
            date_Depart=date(2031, 6, 4), voyages=self.trip,
        )

    def test_legacy_participant_sees_read_only_trip_page(self):
        self.client.force_login(self.participant)
        response = self.client.get(reverse("voyage:detail", kwargs={"pk": self.trip.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "voyage/detail_participant.html")
        self.assertContains(response, "n'a pas encore de créateur attribué")
        self.assertNotContains(response, "Modifier le voyage")

    def test_legacy_participant_sees_read_only_destination_page(self):
        self.client.force_login(self.participant)
        response = self.client.get(reverse(
            "voyage:destination:detail",
            kwargs={"voyage_pk": self.trip.pk, "destination_pk": self.destination.pk},
        ))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "destination/detail_participant.html")
        self.assertNotContains(response, "Supprimer")
