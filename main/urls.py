from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('pokemon/<pokemon_name>', views.pokemon_detail, name='pokemon_detail'),
    path('fight/<pokemon_name>', views.fight, name='fight'),
    path('api/pokemon/random', views.pokemon_random, name='pokemon_random'),
    path('api/pokemon/list/', views.get_pokemon_list, name='pokemon_list'),
    path('api/pokemon/<pokemon_id>/', views.get_pokemon_id, name='pokemon_id'),
    path('api/fight/', views.get_fight_info, name='fight_info'),
    path('api/fight/<int:number>/', views.update_pokemon_data, name='update_pokemon_data'),
    path('api/fight/fast/', views.get_fast_fight_result, name='fast_fight_result'),
    path('api/save/<pokemon_name>', views.get_pokemon_save, name='fast_fight_result')
]