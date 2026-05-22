from django import forms
from .models import Insumo, IngredienteReceta

class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = ['nombre', 'unidad_medida', 'stock_actual', 'alerta_minimo', 'costo_unitario']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-select'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'alerta_minimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control'}),
        }



class IngredienteRecetaForm(forms.ModelForm):
    class Meta:
        model = IngredienteReceta
        fields = ['insumo', 'cantidad_necesaria']
        widgets = {
            'insumo': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_necesaria': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.001', 
                'placeholder': 'Ej: 150 (gr) o 1 (un)'
            }),
        }



class SincronizacionFudoForm(forms.Form):
    archivo_ventas = forms.FileField(
        label="Reporte de Productos Vendidos (CSV/Excel)",
        widget=forms.FileInput(attrs={
            'class': 'form-control', 
            'accept': '.csv, .xlsx, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel'
        })
    )


# Añade esto al final de inventory/forms.py
from .models import Receta

class RecetaPrecioForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ['precio_venta']
        widgets = {
            'precio_venta': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'placeholder': 'Ej: 3500'
            }),
        }