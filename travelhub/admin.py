from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count

from .models import Activite, destinations, voyages


class DestinationInline(admin.TabularInline):
    model = destinations
    extra = 0


class ActiviteInline(admin.TabularInline):
    model = Activite
    extra = 0


@admin.register(voyages)
class VoyageAdmin(admin.ModelAdmin):
    list_display = ("titre", "createur", "date_Debut", "date_Fin", "status", "nombre_participants")
    list_filter = ("status", "date_Debut", "createur")
    search_fields = ("titre", "description", "createur__username", "utilisateurs__username")
    filter_horizontal = ("utilisateurs",)
    inlines = (DestinationInline,)
    list_select_related = ("createur",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            participant_count=Count("utilisateurs", distinct=True)
        )

    @admin.display(description="Participants")
    def nombre_participants(self, obj):
        return obj.participant_count


@admin.register(destinations)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("ville", "pays", "voyages", "date_Arrive", "date_Depart")
    list_filter = ("pays", "date_Arrive")
    search_fields = ("ville", "pays", "voyages__titre")
    inlines = (ActiviteInline,)


@admin.register(Activite)
class ActiviteAdmin(admin.ModelAdmin):
    list_display = ("nom", "categorie", "destination", "date", "cout")
    list_filter = ("categorie", "date")
    search_fields = ("nom", "description", "destination__ville")


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
