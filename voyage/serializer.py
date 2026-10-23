from rest_framework import serializers
from travelhub.models import voyages

class VoyageSerializer(serializers.ModelSerializer):
    class Meta:
        model = voyages
        fields = "__all__"
