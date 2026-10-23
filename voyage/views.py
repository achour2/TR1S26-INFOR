from django.shortcuts import render, redirect
from travelhub.models import voyages
from django.http import HttpResponse
from django.db.models import Q
# Create your views here.

def creer_voyage(request,):
    erreurs = []
    if request.method == 'POST':
        titre = request.POST.get('titre')
        description = request.POST.get('description')
        date_Debut = request.POST.get('date_Debut')
        date_Fin= request.POST.get('date_Fin')
        status = request.POST.get('status')
# verifier la validiter des donnees
        if not titre :
            erreurs.append('le titre est obligatoire')
        if not date_Debut :
            erreurs.append('la date de debut est obligtoire')
        if not date_Fin or date_Fin < date_Debut:
            erreurs.append('verifier la date de fin')
        if not erreurs:
            voyages.objects.create(titre=titre, description=description,
                                date_Debut=date_Debut, date_Fin=date_Fin,
                                status=status)
            return redirect('voyage:creer') # retour, un message de creation

    context = {'erreurs': erreurs} #pour le HTML
    context['voyages'] = voyages.objects.order_by('date_Debut')
    return render(request, 'voyage/list.html', context=context)

# trouver un voyage avec son nom
def selictionner_voyage(request,titre):
    if request.method == 'GET' :
        voyage = voyages.objects.filter(titre=titre)

        if voyage.exists():
            print ("voyage trouver")
        else :
            return ("voyage introuvable")

        for voyage in voyages:
            print(voyage.titre,
                  voyage.description,
                  voyage.date_Debut,
                  voyage.date_Fin)
    return

# afficher tout les voyage
def liste_voyages (request) :
    if request.method == 'GET':
        voyage = voyages.objects.all()

    for voyage in voyages:
        print(voyage.titre,
              voyage.description,
              voyage.date_Debut,
              voyage.date_Fin)

    voyage = (voyages.objects.order_by('date_Debut')) # Les affiches par le date la plus proche
    return render(request, 'voyage/list.html', {'voyages': voyage},)


#modifier un voyage a amiloiree
def modifier_voyage(request,titre) :
    if not voyages.titre :
        return HttpResponse("le voyage n'existe pas choisez un autre titre")
    else :
        voyage = (voyages.objects.filter(titre=titre )
                  .exclude(titre__contains="Alger" == titre )
                  .update(titre=titre))
        return HttpResponse("la modification de voyage est a jour")

#supprimer un voyege
def supprimer_voyage(request,titre):
    if not voyages.titre :
        return HttpResponse("le voyage n'exicte pas choisez un autre titre")
    else :
        voyage = voyages.objects.get(titre=titre)
        voyage.delete()
        return HttpResponse ("le voyge ", voyages.objects.get(titre=titre), "est bien supprimer ")


