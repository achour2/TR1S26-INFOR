from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from travelhub.models import Activite, destinations, voyages


@login_required
def accueil(request):
    mes_voyages = voyages.objects.filter(
        Q(createur=request.user) | Q(utilisateurs=request.user)
    ).distinct()
    context = {
        "nombre_voyages": mes_voyages.count(),
        "nombre_destinations": destinations.objects.filter(voyages__utilisateurs=request.user).distinct().count(),
        "nombre_activites": Activite.objects.filter(
            destination__voyages__utilisateurs=request.user
        ).distinct().count(),
        "prochains_voyages": mes_voyages.order_by("date_Debut")[:3],
    }
    return render(request, "travelhub/dashboard.html", context)
