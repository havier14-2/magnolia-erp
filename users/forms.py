from django import forms
from django.contrib.auth.models import User, Group

class CreacionUsuarioForm(forms.ModelForm):
    # Campo extra para la contraseña y el rol
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Contraseña")
    rol = forms.ModelChoiceField(
        queryset=Group.objects.all(), 
        empty_label="Seleccione un Rol",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        # 1. Guardamos el usuario base
        user = super().save(commit=False)
        # 2. Encriptamos la contraseña de forma segura
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            # 3. Le asignamos el rol seleccionado (Administrador o Encargado)
            grupo = self.cleaned_data['rol']
            user.groups.add(grupo)
        return user