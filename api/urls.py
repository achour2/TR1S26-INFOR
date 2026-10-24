from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ActiviteViewSet, DestinationViewSet, VoyageViewSet

router = DefaultRouter()
router.register("voyages", VoyageViewSet, basename="api-voyage")
router.register("destinations", DestinationViewSet, basename="api-destination")
router.register("activites", ActiviteViewSet, basename="api-activite")

urlpatterns = [path("", include(router.urls))]
