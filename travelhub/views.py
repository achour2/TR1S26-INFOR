from django.shortcuts import render
from django.http import HttpResponse

def reponse(request):
    return HttpResponse(f"Bonjour c'est la tache ")
