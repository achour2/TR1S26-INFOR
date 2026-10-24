from django.db import transaction
from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from travelhub.models import Activite, destinations, voyages
from .serializers import ActiviteSerializer, DestinationSerializer, VoyageSerializer


def _date_parameter(request, name):
    value = request.query_params.get(name)
    if not value:
        return None
    result = parse_date(value)
    if result is None:
        raise ValidationError({name: "Utilisez le format AAAA-MM-JJ."})
    return result


def _integer_parameter(value, name):
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise ValidationError({name: "Une valeur entière positive est attendue."}) from None
    if result < 1:
        raise ValidationError({name: "Une valeur entière positive est attendue."})
    return result


class OwnedResourcesMixin:
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)


class VoyageViewSet(OwnedResourcesMixin, viewsets.ModelViewSet):
    queryset = voyages.objects.all()
    serializer_class = VoyageSerializer
    search_fields = ("titre", "description")
    ordering_fields = ("titre", "date_Debut", "date_Fin", "status")
    ordering = ("date_Debut", "titre")

    def get_queryset(self):
        queryset = voyages.objects.prefetch_related("utilisateurs")
        if self.action in {"create", "update", "partial_update", "destroy", "participants"}:
            queryset = queryset.filter(createur=self.request.user)
        else:
            queryset = queryset.filter(
                Q(createur=self.request.user) | Q(utilisateurs=self.request.user)
            ).distinct()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            if status_filter not in voyages.Statut.values:
                raise ValidationError({"status": "Statut de voyage invalide."})
            queryset = queryset.filter(status=status_filter)
        start_min = _date_parameter(self.request, "date_debut_min")
        start_max = _date_parameter(self.request, "date_debut_max")
        if start_min:
            queryset = queryset.filter(date_Debut__gte=start_min)
        if start_max:
            queryset = queryset.filter(date_Debut__lte=start_max)
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        voyage = serializer.save(createur=self.request.user)
        voyage.utilisateurs.add(self.request.user)

    @action(detail=True, methods=("get", "post", "delete"), url_path="participants")
    def participants(self, request, pk=None):
        voyage = self.get_object()
        if request.method == "GET":
            return Response(list(voyage.utilisateurs.values("id", "username", "email")))
        user_id = request.data.get("user_id")
        if user_id is None:
            raise ValidationError({"user_id": "Ce champ est obligatoire."})
        user_id = _integer_parameter(user_id, "user_id")
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.filter(pk=user_id).first()
        if user is None:
            raise ValidationError({"user_id": "Utilisateur introuvable."})
        if request.method == "POST":
            voyage.utilisateurs.add(user)
            return Response({"detail": "Participant ajouté."}, status=status.HTTP_201_CREATED)
        if user.pk == voyage.createur_id:
            raise ValidationError({"user_id": "Le créateur ne peut pas être retiré du voyage."})
        voyage.utilisateurs.remove(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DestinationViewSet(OwnedResourcesMixin, viewsets.ModelViewSet):
    queryset = destinations.objects.all()
    serializer_class = DestinationSerializer
    search_fields = ("ville", "pays")
    ordering_fields = ("ville", "pays", "date_Arrive", "date_Depart")
    ordering = ("date_Arrive", "ville")

    def get_queryset(self):
        queryset = destinations.objects.select_related("voyages", "voyages__createur")
        if self.action in {"create", "update", "partial_update", "destroy"}:
            queryset = queryset.filter(voyages__createur=self.request.user)
        else:
            queryset = queryset.filter(
                Q(voyages__createur=self.request.user) | Q(voyages__utilisateurs=self.request.user)
            )
        if self.request.query_params.get("voyage"):
            queryset = queryset.filter(voyages_id=_integer_parameter(self.request.query_params["voyage"], "voyage"))
        for parameter, field, lookup in (
            ("arrivee_min", "date_Arrive", "gte"),
            ("arrivee_max", "date_Arrive", "lte"),
        ):
            value = _date_parameter(self.request, parameter)
            if value:
                queryset = queryset.filter(**{f"{field}__{lookup}": value})
        return queryset.distinct()


class ActiviteViewSet(OwnedResourcesMixin, viewsets.ModelViewSet):
    queryset = Activite.objects.all()
    serializer_class = ActiviteSerializer
    search_fields = ("nom", "description", "categorie")
    ordering_fields = ("nom", "date", "cout", "categorie")
    ordering = ("date", "nom")

    def get_queryset(self):
        queryset = Activite.objects.select_related(
            "destination", "destination__voyages", "destination__voyages__createur"
        )
        if self.action in {"create", "update", "partial_update", "destroy"}:
            queryset = queryset.filter(destination__voyages__createur=self.request.user)
        else:
            queryset = queryset.filter(
                Q(destination__voyages__createur=self.request.user)
                | Q(destination__voyages__utilisateurs=self.request.user)
            )
        if self.request.query_params.get("destination"):
            queryset = queryset.filter(destination_id=_integer_parameter(self.request.query_params["destination"], "destination"))
        if self.request.query_params.get("categorie"):
            queryset = queryset.filter(categorie__iexact=self.request.query_params["categorie"])
        date_min = _date_parameter(self.request, "date_min")
        date_max = _date_parameter(self.request, "date_max")
        if date_min:
            queryset = queryset.filter(date__gte=date_min)
        if date_max:
            queryset = queryset.filter(date__lte=date_max)
        return queryset.distinct()
