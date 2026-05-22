from django import forms
from .models import Turno, ParticipanteTurno, ReglaDistribucion
from django.contrib.auth.models import User

class ReglaDistribucionForm(forms.ModelForm):
    class Meta:
        model = ReglaDistribucion
        fields = ['nombre_rol', 'porcentaje_am', 'porcentaje_pm', 'activo']
        widgets = {
            'nombre_rol': forms.TextInput(attrs={'class': 'form-control'}),
            'porcentaje_am': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.01'}),
            'porcentaje_pm': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.01'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ['fecha', 'tipo', 'propinas_sistema', 'efectivo']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'propinas_sistema': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 31020'}),
            'efectivo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 5000'}),
        }

class ParticipanteForm(forms.ModelForm):
    class Meta:
        model = ParticipanteTurno
        fields = ['empleado', 'rol']
        widgets = {
            'empleado': forms.Select(attrs={'class': 'form-select'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar roles que estén marcados como activos
        self.fields['rol'].queryset = ReglaDistribucion.objects.filter(activo=True)
        # Solo mostrar empleados que estén activos
        self.fields['empleado'].queryset = User.objects.filter(is_active=True).exclude(is_superuser=True)
