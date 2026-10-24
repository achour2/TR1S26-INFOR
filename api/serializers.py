from rest_framework import serializers

from travelhub.models import Activite, destinations, voyages


class VoyageSerializer(serializers.ModelSerializer):
    createur = serializers.ReadOnlyField(source="createur_id")
    participants = serializers.PrimaryKeyRelatedField(
        source="utilisateurs", many=True, read_only=True
    )

    class Meta:
        model = voyages
        fields = (
            "id", "titre", "description", "date_Debut", "date_Fin",
            "status", "createur", "participants",
        )
        read_only_fields = ("id", "createur", "participants")

    def validate(self, attrs):
        start = attrs.get("date_Debut", getattr(self.instance, "date_Debut", None))
        end = attrs.get("date_Fin", getattr(self.instance, "date_Fin", None))
        if start and end and end < start:
            raise serializers.ValidationError({"date_Fin": "La fin doit être égale ou postérieure au début."})
        return attrs


class DestinationSerializer(serializers.ModelSerializer):
    voyages = serializers.PrimaryKeyRelatedField(queryset=voyages.objects.all())

    class Meta:
        model = destinations
        fields = ("id", "ville", "pays", "date_Arrive", "date_Depart", "voyages")
        read_only_fields = ("id",)

    def validate_voyages(self, voyage):
        if voyage.createur_id != self.context["request"].user.id:
            raise serializers.ValidationError("Ce voyage ne vous appartient pas.")
        return voyage

    def validate(self, attrs):
        start = attrs.get("date_Arrive", getattr(self.instance, "date_Arrive", None))
        end = attrs.get("date_Depart", getattr(self.instance, "date_Depart", None))
        voyage = attrs.get("voyages", getattr(self.instance, "voyages", None))
        if start and end and end < start:
            raise serializers.ValidationError({"date_Depart": "Le départ doit être après l'arrivée."})
        if voyage and start and end and (start < voyage.date_Debut or end > voyage.date_Fin):
            raise serializers.ValidationError("Les dates de destination doivent rester dans celles du voyage.")
        return attrs


class ActiviteSerializer(serializers.ModelSerializer):
    destination = serializers.PrimaryKeyRelatedField(queryset=destinations.objects.all())

    class Meta:
        model = Activite
        fields = ("id", "nom", "description", "categorie", "date", "cout", "destination")
        read_only_fields = ("id",)

    def validate_destination(self, destination):
        if destination.voyages.createur_id != self.context["request"].user.id:
            raise serializers.ValidationError("Cette destination ne vous appartient pas.")
        return destination

    def validate(self, attrs):
        destination = attrs.get("destination", getattr(self.instance, "destination", None))
        activity_date = attrs.get("date", getattr(self.instance, "date", None))
        if destination and activity_date and not (
            destination.date_Arrive <= activity_date <= destination.date_Depart
        ):
            raise serializers.ValidationError({"date": "La date doit être comprise dans le séjour."})
        if attrs.get("cout", getattr(self.instance, "cout", 0)) < 0:
            raise serializers.ValidationError({"cout": "Le coût doit être positif ou nul."})
        return attrs
