from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from .services import destination_enrichment
from travelhub.models import destinations, voyages


@login_required
def liste_destinations(request):
    queryset = destinations.objects.filter(
        Q(voyages__createur=request.user) | Q(voyages__utilisateurs=request.user)
    ).select_related("voyages").prefetch_related("activites").order_by("date_Arrive", "ville").distinct()
    return render(request, "destination/list.html", {"destinations": queryset})


def _voyage_autorise(request, voyage_pk):
    return get_object_or_404(
        voyages.objects.filter(Q(createur=request.user) | Q(utilisateurs=request.user)),
        pk=voyage_pk,
    )


def _voyage_cree_par(request, voyage_pk):
    return get_object_or_404(voyages, pk=voyage_pk, createur=request.user)


def _destination_autorisee(voyage, destination_pk):
    return get_object_or_404(destinations, pk=destination_pk, voyages=voyage)


def _dates_formulaire(request, champs):
    valeurs = {champ: request.POST.get(champ, "") for champ in champs}
    erreurs = []
    for champ in champs:
        if not valeurs[champ]:
            erreurs.append("Veuillez renseigner toutes les dates.")
            valeurs[champ] = None
            continue
        date = parse_date(valeurs[champ])
        if date is None:
            erreurs.append("Une date saisie est invalide.")
            valeurs[champ] = None
        else:
            valeurs[champ] = date
    return valeurs, erreurs


@login_required
def detail_destination(request, voyage_pk, destination_pk):
    voyage = _voyage_autorise(request, voyage_pk)
    destination = _destination_autorisee(voyage, destination_pk)
    activites = destination.activites.order_by("date", "nom")
    if voyage.createur_id != request.user.pk:
        return render(request, "destination/detail_participant.html", {
            "voyage": voyage,
            "destination": destination,
            "activites": activites,
        })
    return render(request, "destination/detail.html", {
        "voyage": voyage,
        "destination": destination,
        "activites": activites,
        "enrichissement": destination_enrichment(destination),
    })


@login_required
def creer_destination(request, voyage_pk):
    voyage = _voyage_cree_par(request, voyage_pk)
    valeurs = {}
    erreurs = []
    if request.method == "POST":
        valeurs = {
            "ville": request.POST.get("ville", "").strip(),
            "pays": request.POST.get("pays", "").strip(),
        }
        dates, erreurs = _dates_formulaire(request, ("date_Arrive", "date_Depart"))
        valeurs.update(dates)
        if not valeurs["ville"] or not valeurs["pays"]:
            erreurs.append("La ville et le pays sont obligatoires.")
        if len(valeurs["ville"]) > 100 or len(valeurs["pays"]) > 500:
            erreurs.append("La ville ou le pays dépasse la longueur autorisée.")
        if dates["date_Arrive"] and dates["date_Depart"]:
            if dates["date_Arrive"] > dates["date_Depart"]:
                erreurs.append("La date de départ doit être égale ou postérieure à la date d'arrivée.")
            if dates["date_Arrive"] < voyage.date_Debut or dates["date_Depart"] > voyage.date_Fin:
                erreurs.append("Les dates de destination doivent être comprises dans celles du voyage.")
        if not erreurs:
            destination = destinations.objects.create(voyages=voyage, **valeurs)
            return redirect("voyage:destination:detail", voyage_pk=voyage.pk, destination_pk=destination.pk)
    return render(request, "destination/form.html", {
        "voyage": voyage,
        "valeurs": valeurs,
        "erreurs": erreurs,
        "titre_page": "Ajouter une destination",
        "bouton": "Ajouter la destination",
    })


@login_required
def modifier_destination(request, voyage_pk, destination_pk):
    voyage = _voyage_cree_par(request, voyage_pk)
    destination = _destination_autorisee(voyage, destination_pk)
    valeurs = None
    erreurs = []
    if request.method == "POST":
        valeurs = {
            "ville": request.POST.get("ville", "").strip(),
            "pays": request.POST.get("pays", "").strip(),
        }
        dates, erreurs = _dates_formulaire(request, ("date_Arrive", "date_Depart"))
        valeurs.update(dates)
        if not valeurs["ville"] or not valeurs["pays"]:
            erreurs.append("La ville et le pays sont obligatoires.")
        if len(valeurs["ville"]) > 100 or len(valeurs["pays"]) > 500:
            erreurs.append("La ville ou le pays dépasse la longueur autorisée.")
        if dates["date_Arrive"] and dates["date_Depart"]:
            if dates["date_Arrive"] > dates["date_Depart"]:
                erreurs.append("La date de départ doit être égale ou postérieure à la date d'arrivée.")
            if dates["date_Arrive"] < voyage.date_Debut or dates["date_Depart"] > voyage.date_Fin:
                erreurs.append("Les dates de destination doivent être comprises dans celles du voyage.")
        if not erreurs:
            for champ, valeur in valeurs.items():
                setattr(destination, champ, valeur)
            destination.save()
            return redirect("voyage:destination:detail", voyage_pk=voyage.pk, destination_pk=destination.pk)
    if valeurs is None:
        valeurs = {
            "ville": destination.ville,
            "pays": destination.pays,
            "date_Arrive": destination.date_Arrive,
            "date_Depart": destination.date_Depart,
        }
    return render(request, "destination/form.html", {
        "voyage": voyage,
        "destination": destination,
        "valeurs": valeurs,
        "erreurs": erreurs,
        "titre_page": "Modifier la destination",
        "bouton": "Enregistrer",
    })


@login_required
def supprimer_destination(request, voyage_pk, destination_pk):
    voyage = _voyage_cree_par(request, voyage_pk)
    destination = _destination_autorisee(voyage, destination_pk)
    if request.method == "POST":
        destination.delete()
        return redirect("voyage:detail", pk=voyage.pk)
    return render(request, "destination/confirm_delete.html", {"voyage": voyage, "destination": destination})
