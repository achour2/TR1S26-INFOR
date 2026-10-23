import graphene
from graphene_django import DjangoObjectType
from travelhub.models import voyages

# Le TYPE : équivalent du serializer
class VoyageType(DjangoObjectType):
    class Meta:
        model = voyages
        fields = "__all__"

# La QUERY : équivalent de la vue (lecture)
class Query(graphene.ObjectType):
    voyages = graphene.List(VoyageType)       # le champ

    def resolve_voyages(root, info):          # le resolver
        return voyages.objects.all()           # ← ton ORM est ICI

schema = graphene.Schema(query=Query)