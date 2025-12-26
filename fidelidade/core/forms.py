from django import forms
from core.models import Promocao, Comercio
from django.core.validators import MinValueValidator
from datetime import date
from .models import Comercio, Cidade

class PromocaoForm(forms.ModelForm):
    class Meta:
        model = Promocao
        fields = ['nome', 'descricao', 'pontos_necessarios', 'premio', 'data_inicio', 'data_fim']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        
        if data_inicio and data_fim:
            if data_inicio < date.today():
                raise forms.ValidationError("A data de início não pode ser no passado.")
            if data_fim < data_inicio:
                raise forms.ValidationError("A data de término não pode ser anterior à data de início.")
        
        return cleaned_data

class ComercioForm(forms.ModelForm):
    class Meta:
        model = Comercio
        fields = ['nome_fantasia', 'razao_social', 'endereco', 'cidade', 'telefone', 'email', 'cnpj']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cidade'].empty_label = "Selecione uma cidade"
        self.fields['cidade'].queryset = Cidade.objects.all().order_by('nome')