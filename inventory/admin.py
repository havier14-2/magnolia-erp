from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Insumo, Receta, IngredienteReceta

class IngredienteInline(admin.TabularInline):
    model = IngredienteReceta
    extra = 1

@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    inlines = [IngredienteInline]

admin.site.register(Insumo)