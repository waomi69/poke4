from django.db import models
from django import forms


class FightForm(forms.Form):
    user_number = forms.IntegerField(
        label='Ваша атака (от 1 до 10)',
        min_value=1,
        max_value=10,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class FastFightForm(forms.Form):
    pass


class EmailForm(forms.Form):
    email = forms.EmailField(label="Введите ваш адрес электронной почты, чтобы получить результат боя",
                             required=True,
                             widget=forms.TextInput(
                                 attrs={'class': 'form-control', 'placeholder': 'Ваш адрес электронной почты'}))


class SavePokemonInfo(forms.Form):
    pass


class Fight(models.Model):
    date = models.DateTimeField()
    round_count = models.IntegerField()
    pokemon_name = models.CharField(max_length=30)
    enemy_name = models.CharField(max_length=30)
    result = models.BooleanField()
