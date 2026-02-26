from django import forms
from core.models import Promocao, Comercio
from django.core.validators import MinValueValidator
from datetime import date
from .models import Comercio, Cidade

class PromocaoForm(forms.ModelForm):
    class Meta:
        model = Promocao
        fields = ['nome', 'descricao', 'pontos_necessarios', 'premio', 'data_inicio', 'data_fim', 'sem_prazo']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_fim': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.data_inicio:
                self.initial['data_inicio'] = self.instance.data_inicio.strftime('%Y-%m-%d')
            if self.instance.data_fim:
                self.initial['data_fim'] = self.instance.data_fim.strftime('%Y-%m-%d')
                
    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        sem_prazo = cleaned_data.get('sem_prazo')
        
        
        if data_inicio:
            pass 

        if not sem_prazo:
            if not data_fim:
                raise forms.ValidationError("Se a promoção não é por tempo indeterminado, você deve informar a data de fim.")
            if data_inicio and data_fim < data_inicio:
                raise forms.ValidationError("A data de término não pode ser anterior à data de início.")
        else:
            # Se for sem prazo, ignoramos a data_fim
            cleaned_data['data_fim'] = None
            
        return cleaned_data

class ComercioForm(forms.ModelForm):
    class Meta:
        model = Comercio
        fields = ['nome_fantasia', 'razao_social', 'endereco', 'cidade', 'telefone', 'email', 'cnpj']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cidade'].empty_label = "Selecione uma cidade"
        self.fields['cidade'].queryset = Cidade.objects.all().order_by('nome')