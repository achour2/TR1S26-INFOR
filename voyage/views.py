from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from travelhub.models import voyages


def _form_data(request):
    """Valide les champs communs aux formulaires de création et de modification."""
    data = {
        "titre": request.POST.get("titre", "").strip(),
        "description": request.POST.get("description", "").strip(),
        "date_Debut": request.POST.get("date_Debut", ""),
        "date_Fin": request.POST.get("date_Fin", ""),
        "status": request.POST.get("status", voyages.Statut.PLANIFIE),
    }
    erreurs = []
    for champ, libelle in (("date_Debut", "début"), ("date_Fin", "fin")):
        if data[champ]:
            parsed = parse_date(data[champ])
            if parsed is None:
                erreurs.append(f"La date de {libelle} est invalide.")
                data[champ] = None
            else:
                data[champ] = parsed
    if not data["titre"]:
        erreurs.append("Le titre est obligatoire.")
    if not data["date_Debut"]:
        erreurs.append("La date de début est obligatoire.")
    if not data["date_Fin"]:
        erreurs.append("La date de fin est obligatoire.")
    elif data["date_Debut"] and data["date_Fin"] < data["date_Debut"]:
        erreurs.append("La date de fin doit être égale ou postérieure à la date de début.")
    if data["status"] not in voyages.Statut.values:
        erreurs.append("Veuillez choisir un statut valide.")
    if len(data["titre"]) > 100:
        erreurs.append("Le titre ne peut pas dépasser 100 caractères.")
    if len(data["description"]) > 1000:
        erreurs.append("La description ne peut pas dépasser 1000 caractères.")
    return data, erreurs


@login_required
def liste_voyages(request):
    queryset = voyages.objects.filter(
        Q(createur=request.user) | Q(utilisateurs=request.user)
    ).distinct()

    recherche = request.GET.get("q", "").strip()
    statut = request.GET.get("status", "")
    if recherche:
        queryset = queryset.filter(
            Q(titre__icontains=recherche) | Q(description__icontains=recherche)
        )
    if statut in voyages.Statut.values:
        queryset = queryset.filter(status=statut)

    tris = {
        "date_debut": "date_Debut",
        "date_fin": "date_Fin",
        "-date_debut": "-date_Debut",
        "-date_fin": "-date_Fin",
    }
    tri = request.GET.get("tri", "date_debut")
    if tri == "titre":
        queryset = queryset.order_by("titre")
    elif tri == "-titre":
        queryset = queryset.order_by("-titre")
    else:
        queryset = queryset.order_by(tris.get(tri, "date_Debut"))

    return render(request, "voyage/list.html", {
        "voyages": queryset,
        "statuts": voyages.Statut.choices,
        "recherche": recherche,
        "statut_selectionne": statut,
        "tri": tri,
    })


@login_required
def detail_voyage(request, pk):
    voyage = get_object_or_404(
        voyages.objects.prefetch_related("destinations__activites").filter(
            Q(createur=request.user) | Q(utilisateurs=request.user)
        ),
        pk=pk,
    )
    peut_modifier = voyage.createur_id == request.user.pk
    if not peut_modifier:
        return render(request, "voyage/detail_participant.html", {"voyage": voyage})
    return render(request, "voyage/detail.html", {"voyage": voyage})


@login_required
def creer_voyage(request):
    erreurs = []
    data = None
    if request.method == "POST":
        data, erreurs = _form_data(request)
        if not erreurs:
            voyage = voyages.objects.create(createur=request.user, **data)
            voyage.utilisateurs.add(request.user)
            return redirect("voyage:detail", pk=voyage.pk)
    return render(request, "voyage/form.html", {
        "erreurs": erreurs,
        "donnees": data or {},
        "statuts": voyages.Statut.choices,
        "titre_page": "Créer un voyage",
        "bouton": "Créer",
    })


@login_required
def modifier_voyage(request, pk):
    voyage = get_object_or_404(voyages, pk=pk, createur=request.user)
    erreurs = []
    data = None
    if request.method == "POST":
        data, erreurs = _form_data(request)
        if not erreurs:
            for champ, valeur in data.items():
                setattr(voyage, champ, valeur)
            voyage.save()
            return redirect("voyage:detail", pk=voyage.pk)
    return render(request, "voyage/form.html", {
        "voyage": voyage,
        "erreurs": erreurs,
        "donnees": data or {
            "titre": voyage.titre,
            "description": voyage.description,
            "date_Debut": voyage.date_Debut,
            "date_Fin": voyage.date_Fin,
            "status": voyage.status,
        },
        "statuts": voyages.Statut.choices,
        "titre_page": "Modifier le voyage",
        "bouton": "Enregistrer",
    })


@login_required
def supprimer_voyage(request, pk):
    voyage = get_object_or_404(voyages, pk=pk, createur=request.user)
    if request.method == "POST":
        voyage.delete()
        return redirect("voyage:liste_voyages")
    return render(request, "voyage/confirm_delete.html", {"voyage": voyage})
