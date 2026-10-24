from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from travelhub.models import Activite, destinations, voyages


def _contexte_autorise(request, voyage_pk, destination_pk):
    voyage = get_object_or_404(voyages, pk=voyage_pk, createur=request.user)
    destination = get_object_or_404(destinations, pk=destination_pk, voyages=voyage)
    return voyage, destination


@login_required
def liste(request):
    activites = Activite.objects.filter(
        Q(destination__voyages__createur=request.user)
        | Q(destination__voyages__utilisateurs=request.user)
    ).select_related("destination", "destination__voyages").order_by("date", "nom").distinct()
    return render(request, "activite/list.html", {"activites": activites})


def _formulaire(request, destination):
    valeurs = {
        "nom": request.POST.get("nom", "").strip(),
        "description": request.POST.get("description", "").strip(),
        "categorie": request.POST.get("categorie", "").strip(),
        "date": request.POST.get("date", ""),
        "cout": request.POST.get("cout", "0"),
    }
    erreurs = []
    if not valeurs["date"]:
        erreurs.append("La date est obligatoire.")
        date = None
    else:
        date = parse_date(valeurs["date"])
        if date is None:
            erreurs.append("La date saisie est invalide.")
    if not valeurs["nom"] or not valeurs["categorie"]:
        erreurs.append("Le nom et la catégorie sont obligatoires.")
    if len(valeurs["nom"]) > 100 or len(valeurs["categorie"]) > 1000 or len(valeurs["description"]) > 1000:
        erreurs.append("Un champ dépasse la longueur autorisée.")
    try:
        cout = Decimal(valeurs["cout"])
        if not cout.is_finite() or cout < 0 or cout > Decimal("9999999999.99"):
            raise InvalidOperation
        valeurs["cout"] = cout.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        erreurs.append("Le coût doit être un montant positif valide.")
    if date and (date < destination.date_Arrive or date > destination.date_Depart):
        erreurs.append("La date de l'activité doit être comprise dans le séjour.")
    if date:
        valeurs["date"] = date
    return valeurs, erreurs


@login_required
def creer(request, voyage_pk, destination_pk):
    voyage, destination = _contexte_autorise(request, voyage_pk, destination_pk)
    valeurs, erreurs = {}, []
    if request.method == "POST":
        valeurs, erreurs = _formulaire(request, destination)
        if not erreurs:
            Activite.objects.create(destination=destination, **valeurs)
            return redirect("voyage:destination:detail", voyage_pk=voyage.pk, destination_pk=destination.pk)
    return render(request, "activite/form.html", {
        "voyage": voyage,
        "destination": destination,
        "valeurs": valeurs,
        "erreurs": erreurs,
        "titre_page": "Ajouter une activité",
        "bouton": "Ajouter l'activité",
    })


@login_required
def modifier(request, voyage_pk, destination_pk, activite_pk):
    voyage, destination = _contexte_autorise(request, voyage_pk, destination_pk)
    activite = get_object_or_404(Activite, pk=activite_pk, destination=destination)
    valeurs, erreurs = None, []
    if request.method == "POST":
        valeurs, erreurs = _formulaire(request, destination)
        if not erreurs:
            for champ, valeur in valeurs.items():
                setattr(activite, champ, valeur)
            activite.save()
            return redirect("voyage:destination:detail", voyage_pk=voyage.pk, destination_pk=destination.pk)
    if valeurs is None:
        valeurs = {
            "nom": activite.nom,
            "description": activite.description,
            "categorie": activite.categorie,
            "date": activite.date,
            "cout": activite.cout,
        }
    return render(request, "activite/form.html", {
        "voyage": voyage,
        "destination": destination,
        "activite": activite,
        "valeurs": valeurs,
        "erreurs": erreurs,
        "titre_page": "Modifier l'activité",
        "bouton": "Enregistrer",
    })


@login_required
def supprimer(request, voyage_pk, destination_pk, activite_pk):
    voyage, destination = _contexte_autorise(request, voyage_pk, destination_pk)
    activite = get_object_or_404(Activite, pk=activite_pk, destination=destination)
    if request.method == "POST":
        activite.delete()
        return redirect("voyage:destination:detail", voyage_pk=voyage.pk, destination_pk=destination.pk)
    return render(request, "activite/confirm_delete.html", {
        "voyage": voyage,
        "destination": destination,
        "activite": activite,
    })
