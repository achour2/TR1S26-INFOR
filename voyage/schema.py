import graphene
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphql import GraphQLError

from travelhub.models import Activite, destinations, voyages


def _user(info):
    user = getattr(info.context, "user", None)
    if not user or not user.is_authenticated:
        raise GraphQLError("Authentification requise.")
    return user


def _save(instance):
    try:
        instance.full_clean()
        instance.save()
    except DjangoValidationError as exc:
        raise GraphQLError(" ".join(exc.messages)) from exc
    return instance


def _owned_voyage(info, pk):
    return voyages.objects.filter(pk=pk, createur=_user(info)).first()


def _owned_destination(info, pk):
    return destinations.objects.filter(pk=pk, voyages__createur=_user(info)).select_related("voyages").first()


class ActivityType(DjangoObjectType):
    destination_id = graphene.Int()

    class Meta:
        model = Activite
        fields = ("id", "nom", "description", "categorie", "date", "cout")

    @staticmethod
    def resolve_destination_id(root, info):
        return root.destination_id


class DestinationType(DjangoObjectType):
    voyage_id = graphene.Int()
    activites = graphene.List(ActivityType)

    class Meta:
        model = destinations
        fields = ("id", "ville", "pays", "date_Arrive", "date_Depart")

    @staticmethod
    def resolve_voyage_id(root, info):
        return root.voyages_id

    @staticmethod
    def resolve_activites(root, info):
        return root.activites.order_by("date", "nom")


class VoyageType(DjangoObjectType):
    createur_id = graphene.Int()
    participants = graphene.List(graphene.Int)
    destinations = graphene.List(DestinationType)

    class Meta:
        model = voyages
        fields = ("id", "titre", "description", "date_Debut", "date_Fin", "status")

    @staticmethod
    def resolve_createur_id(root, info):
        return root.createur_id

    @staticmethod
    def resolve_participants(root, info):
        return root.utilisateurs.values_list("id", flat=True)

    @staticmethod
    def resolve_destinations(root, info):
        return root.destinations.order_by("date_Arrive", "ville")


class Query(graphene.ObjectType):
    voyages = graphene.List(VoyageType, status=graphene.String())
    voyage = graphene.Field(VoyageType, id=graphene.Int(required=True))
    destinations = graphene.List(DestinationType, voyage_id=graphene.Int())
    destination = graphene.Field(DestinationType, id=graphene.Int(required=True))
    activites = graphene.List(ActivityType, destination_id=graphene.Int())
    activite = graphene.Field(ActivityType, id=graphene.Int(required=True))

    @staticmethod
    def resolve_voyages(root, info, status=None):
        user = _user(info)
        queryset = voyages.objects.filter(
            Q(createur=user) | Q(utilisateurs=user)
        ).prefetch_related("destinations").distinct()
        if status in voyages.Statut.values:
            queryset = queryset.filter(status=status)
        return queryset.order_by("date_Debut", "titre")

    @staticmethod
    def resolve_voyage(root, info, id):
        user = _user(info)
        return voyages.objects.filter(Q(createur=user) | Q(utilisateurs=user), pk=id).first()

    @staticmethod
    def resolve_destinations(root, info, voyage_id=None):
        user = _user(info)
        queryset = destinations.objects.filter(
            Q(voyages__createur=user) | Q(voyages__utilisateurs=user)
        )
        if voyage_id is not None:
            queryset = queryset.filter(voyages_id=voyage_id)
        return queryset.order_by("date_Arrive", "ville").distinct()

    @staticmethod
    def resolve_destination(root, info, id):
        user = _user(info)
        return destinations.objects.filter(
            Q(voyages__createur=user) | Q(voyages__utilisateurs=user), pk=id
        ).first()

    @staticmethod
    def resolve_activites(root, info, destination_id=None):
        user = _user(info)
        queryset = Activite.objects.filter(
            Q(destination__voyages__createur=user)
            | Q(destination__voyages__utilisateurs=user)
        )
        if destination_id is not None:
            queryset = queryset.filter(destination_id=destination_id)
        return queryset.order_by("date", "nom").distinct()

    @staticmethod
    def resolve_activite(root, info, id):
        user = _user(info)
        return Activite.objects.filter(
            Q(destination__voyages__createur=user)
            | Q(destination__voyages__utilisateurs=user), pk=id
        ).first()


class CreateVoyage(graphene.Mutation):
    class Arguments:
        titre = graphene.String(required=True)
        description = graphene.String()
        date_debut = graphene.Date(required=True)
        date_fin = graphene.Date(required=True)
        status = graphene.String()

    voyage = graphene.Field(VoyageType)

    @classmethod
    @transaction.atomic
    def mutate(cls, root, info, titre, date_debut, date_fin, description="", status="planifie"):
        user = _user(info)
        if date_fin < date_debut:
            raise GraphQLError("La date de fin doit être égale ou postérieure au début.")
        if status not in voyages.Statut.values:
            raise GraphQLError("Statut de voyage invalide.")
        voyage = _save(voyages(
            titre=titre, description=description, date_Debut=date_debut,
            date_Fin=date_fin, status=status, createur=user,
        ))
        voyage.utilisateurs.add(user)
        return CreateVoyage(voyage=voyage)


class UpdateVoyage(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        titre = graphene.String()
        description = graphene.String()
        date_debut = graphene.Date()
        date_fin = graphene.Date()
        status = graphene.String()

    voyage = graphene.Field(VoyageType)

    @classmethod
    def mutate(cls, root, info, id, **changes):
        voyage = _owned_voyage(info, id)
        if not voyage:
            raise GraphQLError("Voyage introuvable ou accès refusé.")
        for field, value in changes.items():
            if value is not None:
                setattr(voyage, {"date_debut": "date_Debut", "date_fin": "date_Fin"}.get(field, field), value)
        if voyage.status not in voyages.Statut.values:
            raise GraphQLError("Statut de voyage invalide.")
        return UpdateVoyage(voyage=_save(voyage))


class DeleteVoyage(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, id):
        voyage = _owned_voyage(info, id)
        if not voyage:
            raise GraphQLError("Voyage introuvable ou accès refusé.")
        voyage.delete()
        return DeleteVoyage(success=True)


class CreateDestination(graphene.Mutation):
    class Arguments:
        voyage_id = graphene.Int(required=True)
        ville = graphene.String(required=True)
        pays = graphene.String(required=True)
        date_arrive = graphene.Date(required=True)
        date_depart = graphene.Date(required=True)

    destination = graphene.Field(DestinationType)

    @classmethod
    def mutate(cls, root, info, voyage_id, ville, pays, date_arrive, date_depart):
        voyage = _owned_voyage(info, voyage_id)
        if not voyage:
            raise GraphQLError("Voyage introuvable ou accès refusé.")
        if date_arrive < voyage.date_Debut or date_depart > voyage.date_Fin:
            raise GraphQLError("Les dates de destination doivent rester dans celles du voyage.")
        return CreateDestination(destination=_save(destinations(
            voyages=voyage, ville=ville, pays=pays,
            date_Arrive=date_arrive, date_Depart=date_depart,
        )))


class UpdateDestination(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        ville = graphene.String()
        pays = graphene.String()
        date_arrive = graphene.Date()
        date_depart = graphene.Date()

    destination = graphene.Field(DestinationType)

    @classmethod
    def mutate(cls, root, info, id, **changes):
        destination = _owned_destination(info, id)
        if not destination:
            raise GraphQLError("Destination introuvable ou accès refusé.")
        for field, value in changes.items():
            if value is not None:
                setattr(destination, {"date_arrive": "date_Arrive", "date_depart": "date_Depart"}.get(field, field), value)
        if destination.date_Arrive < destination.voyages.date_Debut or destination.date_Depart > destination.voyages.date_Fin:
            raise GraphQLError("Les dates de destination doivent rester dans celles du voyage.")
        return UpdateDestination(destination=_save(destination))


class DeleteDestination(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, id):
        destination = _owned_destination(info, id)
        if not destination:
            raise GraphQLError("Destination introuvable ou accès refusé.")
        destination.delete()
        return DeleteDestination(success=True)


class CreateActivite(graphene.Mutation):
    class Arguments:
        destination_id = graphene.Int(required=True)
        nom = graphene.String(required=True)
        description = graphene.String()
        categorie = graphene.String(required=True)
        date = graphene.Date(required=True)
        cout = graphene.Decimal()

    activite = graphene.Field(ActivityType)

    @classmethod
    def mutate(cls, root, info, destination_id, nom, categorie, date, description="", cout=0):
        destination = _owned_destination(info, destination_id)
        if not destination:
            raise GraphQLError("Destination introuvable ou accès refusé.")
        if not destination.date_Arrive <= date <= destination.date_Depart:
            raise GraphQLError("La date de l'activité doit être comprise dans le séjour.")
        return CreateActivite(activite=_save(Activite(
            destination=destination, nom=nom, description=description,
            categorie=categorie, date=date, cout=cout,
        )))


class UpdateActivite(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        nom = graphene.String()
        description = graphene.String()
        categorie = graphene.String()
        date = graphene.Date()
        cout = graphene.Decimal()

    activite = graphene.Field(ActivityType)

    @classmethod
    def mutate(cls, root, info, id, **changes):
        activity = Activite.objects.filter(
            pk=id, destination__voyages__createur=_user(info)
        ).select_related("destination", "destination__voyages").first()
        if not activity:
            raise GraphQLError("Activité introuvable ou accès refusé.")
        for field, value in changes.items():
            if value is not None:
                setattr(activity, field, value)
        if not activity.destination.date_Arrive <= activity.date <= activity.destination.date_Depart:
            raise GraphQLError("La date de l'activité doit être comprise dans le séjour.")
        return UpdateActivite(activite=_save(activity))


class DeleteActivite(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, id):
        activity = Activite.objects.filter(pk=id, destination__voyages__createur=_user(info)).first()
        if not activity:
            raise GraphQLError("Activité introuvable ou accès refusé.")
        activity.delete()
        return DeleteActivite(success=True)


class Mutation(graphene.ObjectType):
    create_voyage = CreateVoyage.Field()
    update_voyage = UpdateVoyage.Field()
    delete_voyage = DeleteVoyage.Field()
    create_destination = CreateDestination.Field()
    update_destination = UpdateDestination.Field()
    delete_destination = DeleteDestination.Field()
    create_activite = CreateActivite.Field()
    update_activite = UpdateActivite.Field()
    delete_activite = DeleteActivite.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
