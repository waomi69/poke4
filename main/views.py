import ftplib
import io
import requests, random
import smtplib
from email.mime.text import MIMEText
from django.conf import settings
import json
from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from .models import Fight, FightForm, FastFightForm, EmailForm, SavePokemonInfo
from django.http import JsonResponse
from datetime import date
from django.core.cache import cache

with open('main/ftp.json', 'r') as file:
    data = file.read()
ftp_params = json.loads(data)


def get_random_pokemon(pokemon_name):
    all_pokemons = get_all_pokemons()
    random_index = random.randrange(len(all_pokemons))
    if pokemon_name != all_pokemons[random_index]:
        opponent_pokemon = get_pokemon_data(all_pokemons[random_index])
        return {
            'name': opponent_pokemon['name'],
            'hp': opponent_pokemon['hp'],
            'attack': opponent_pokemon['attack'],
            'png': opponent_pokemon['png'],
        }
    else:
        get_random_pokemon(pokemon_name)


def fight(request, pokemon_name):
    user_pokemon = get_pokemon_data(pokemon_name)

    if not user_pokemon:
        return redirect('home')

    form = None
    fast_form = None
    email_form = None
    round = None

    if request.method == 'POST':
        if 'fast_fight' in request.POST:
            email_form = EmailForm(request.POST)
            if email_form.is_valid():
                user_email = email_form.cleaned_data['email']

                # Обработка быстрого боя
                user_hp = request.session.get('user_hp')
                opponent_hp = request.session.get('opponent_hp')
                round = request.session.get('round')

                while user_hp > 0 and opponent_hp > 0:
                    user_number = random.randint(1, 10)
                    attack_time = timezone.now()

                    # Получаем данные из сессии
                    user_hp = request.session.get('user_hp')
                    opponent_hp = request.session.get('opponent_hp')
                    user_attack = request.session.get('user_attack')
                    opponent_attack = request.session.get('opponent_attack')

                    opponent_number = random.randint(1, 10)
                    print(user_number, opponent_number)

                    # Обработка атаки пользователя и противника
                    if user_number % 2 == opponent_number % 2:
                        opponent_hp -= user_attack
                    else:
                        user_hp -= opponent_attack

                    print(user_hp, opponent_hp)

                    if user_hp <= 0 or opponent_hp <= 0:
                        fight_result = Fight(
                            pokemon_name=user_pokemon['name'],
                            enemy_name=request.session.get('opponent_pokemon')['name'],
                            result=user_hp > opponent_hp,
                            date=attack_time,
                            round_count=round
                        )
                        fight_result.save()

                        # Отправка результата на email пользователя
                        email_subject = "Результат боя"
                        email_message = "Ваш покемон: {}\nПротивник: {}\nРезультат: {}".format(
                            user_pokemon['name'],
                            request.session.get('opponent_pokemon')['name'],
                            "Вы выиграли" if user_hp > opponent_hp else "Вы проиграли"
                        )
                        send_email(email_subject, email_message, user_email)

                        return render(request, 'main/battle_result.html', {
                            'user_pokemon': user_pokemon,
                            'opponent_pokemon': request.session.get('opponent_pokemon'),
                            'user_attack': user_attack,
                            'opponent_attack': opponent_attack,
                            'user_hp': user_hp,
                            'opponent_hp': opponent_hp,
                            'opponent_png': request.session.get('opponent_pokemon')['png'],
                            'round': round
                        })

                    # Обновление данных боя в сессии
                    request.session['user_hp'] = user_hp
                    request.session['opponent_hp'] = opponent_hp
                    request.session['round'] += 1

        else:
            form = FightForm(request.POST)
            if form.is_valid():
                user_number = form.cleaned_data['user_number']
                attack_time = timezone.now()
                round = request.session.get('round')
                round += 1

                # Получаем данные из сессии
                user_hp = request.session.get('user_hp')
                opponent_hp = request.session.get('opponent_hp')
                user_attack = request.session.get('user_attack')
                opponent_attack = request.session.get('opponent_attack')

                opponent_number = random.randint(1, 10)
                print(user_number, opponent_number)

                # Обработка атаки пользователя и противника
                if user_number % 2 == opponent_number % 2:
                    opponent_hp -= user_attack
                else:
                    user_hp -= opponent_attack

                if user_hp <= 0 or opponent_hp <= 0:
                    fight_result = Fight(
                        pokemon_name=user_pokemon['name'],
                        enemy_name=request.session.get('opponent_pokemon')['name'],
                        result=user_hp > opponent_hp,
                        date=attack_time,
                        round_count=round
                    )
                    fight_result.save()

                    return render(request, 'main/battle_result.html', {
                        'user_pokemon': user_pokemon,
                        'opponent_pokemon': request.session.get('opponent_pokemon'),
                        'user_attack': user_attack,
                        'opponent_attack': opponent_attack,
                        'user_hp': user_hp,
                        'opponent_hp': opponent_hp,
                        'opponent_png': request.session.get('opponent_pokemon')['png'],
                        'round': round
                    })

                # Обновление данных боя в сессии
                request.session['user_hp'] = user_hp
                request.session['opponent_hp'] = opponent_hp
    else:
        form = FightForm()
        fast_form = FastFightForm()
        email_form = EmailForm()
        round = 1

        # Генерируем случайного противника, если это начало боя
        opponent_pokemon = get_random_pokemon(user_pokemon['name'])

        if not opponent_pokemon:
            return redirect('home')

        # Инициализируем статистику боя
        user_hp = user_pokemon['hp']
        opponent_hp = opponent_pokemon['hp']
        user_attack = user_pokemon['attack']
        opponent_attack = opponent_pokemon['attack']
        user_png = user_pokemon['png']
        opponent_png = opponent_pokemon['png']

        # Сохраняем данные боя в сессии
        request.session['user_pokemon'] = user_pokemon
        request.session['opponent_pokemon'] = opponent_pokemon
        request.session['user_attack'] = user_attack
        request.session['opponent_attack'] = opponent_attack
        request.session['user_hp'] = user_hp
        request.session['opponent_hp'] = opponent_hp
        request.session['user_png'] = user_png
        request.session['opponent_png'] = opponent_png
        request.session['round'] = round

    return render(request, 'main/fight.html', {
        'user_pokemon': user_pokemon,
        'opponent_pokemon': request.session.get('opponent_pokemon'),
        'user_hp': request.session.get('user_hp'),
        'opponent_hp': request.session.get('opponent_hp'),
        'user_attack': request.session.get('user_attack'),
        'opponent_attack': request.session.get('opponent_attack'),
        'user_png': request.session.get('user_png'),
        'opponent_png': request.session.get('opponent_png'),
        'form': form,
        'fast_form': fast_form,
        'email_form': email_form,
        'round': round
    })


def get_pokemon_save(request, user_pokemon):
    pokemon = get_pokemon_data(user_pokemon)

    # pokemon = JsonResponse(response)

    folder_name = str(date.today()).replace('-', '').strip()
    text_markdown = f"# Name: {pokemon['name']}\n\n### Info:\n* hp: {pokemon['hp']}\n* attack: {pokemon['attack']}\n* " \
                    f"height: {pokemon['height']}\n* png: {pokemon['png']} \n* weight: {pokemon['weight']} "

    byte_text_markdown = text_markdown.encode('utf-8')

    ftp = ftplib.FTP(host=ftp_params['hostname'])
    ftp.login(user=ftp_params['username'], passwd=ftp_params['password'])

    files = ftp.nlst()
    if folder_name not in files:
        ftp.mkd(folder_name)
    ftp.cwd(folder_name)
    ftp.storbinary(f"STOR {pokemon['name']}.md", io.BytesIO(byte_text_markdown))
    ftp.quit()

    return render(request, 'main/save_result.html', {'result': 'Success'})


def pokemon_detail(request, pokemon_name):
    # Сначала пробуем получить данные из кэша
    pokemon_detail_cached = cache.get('pokemon_detail' + str(pokemon_name))
    if not pokemon_detail_cached:
        # Если данных в кэше нет, получить их и сохранить в кэш
        pokemon_detail_cached = get_pokemon_data(pokemon_name)
        cache.set(('pokemon_detail' + str(pokemon_name)), pokemon_detail_cached,
                  3600)  # Кэшировать на 1 час (время в секундах)

    if request.method == 'POST':
        if 'save_info' in request.POST:
            return get_pokemon_save(request, pokemon_name)
    else:

        return render(request, 'main/pokemon_detail.html', {'pokemon': pokemon_detail_cached})


def index(request):
    if 'search' in request.GET:
        pokemon_name = request.GET['search']
        pokemon = get_pokemon_data(pokemon_name)
        return render(request, 'main/search.html', {'pokemon': pokemon})

    page_number = int(request.GET.get('page', 1))
    limit = 3  # Количество покемонов на каждой странице
    offset = (page_number - 1) * limit

    # Сначала пробуем получить данные из кэша
    all_pokemons_name_cached = cache.get('all_pokemons')
    if not all_pokemons_name_cached:
        # Если данных в кэше нет, получить их и сохранить в кэш
        all_pokemons_name_cached = get_all_pokemons()
        cache.set('all_pokemons', all_pokemons_name_cached, 3600)  # Кэшировать на 1 час (время в секундах)

    paginator = Paginator(all_pokemons_name_cached, 3)

    # Сначала пробуем получить данные из кэша
    pokemon_info_cached = cache.get('pokemon_list' + str(page_number))

    if not pokemon_info_cached:
        # Если данных в кэше нет, получить их и сохранить в кэш
        pokemon_info_cached = get_pokemon_names(limit, offset)
        cache.set(('pokemon_list' + str(page_number)), pokemon_info_cached,
                  3600)

    page = paginator.get_page(page_number)
    # Используйте данные из кэша для отображения
    return render(request, 'main/index.html', {
        'title': 'Main page of site',
        'pokemon_info': pokemon_info_cached,
        'page_number': page
    })


def get_all_pokemons():
    url = 'https://pokeapi.co/api/v2/pokemon'
    res = requests.get(url)
    data = res.json()
    limit = data["count"]  # Количество покемонов для получения
    offset = 0  # Начальное смещение списка
    params = {"limit": limit, "offset": offset}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        pokemon_names = [pokemon['name'] for pokemon in data['results']]

        return pokemon_names
    else:
        return []


def get_pokemon_names(limit, offset):
    url = f'https://pokeapi.co/api/v2/pokemon?limit={limit}&offset={offset}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        pokemon_list = []

        for pokemon in results:
            pokemon_info = get_pokemon_data(pokemon['name'])
            pokemon_list.append(pokemon_info)

        return pokemon_list
    else:
        return []


def get_pokemon_data(pokemon_name):
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name}/'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        abilities = []
        for j in range(len(data['abilities'])):
            abilities.append([data['abilities'][j]['ability']['name']])

        pokemon_data = {
            'name': data['name'],
            'weight': data['weight'],
            'abilities': [abilities],
            'height': data['height'],
            'png': data['sprites']['front_default'],
            'hp': data['stats'][0]['base_stat'],  # Здоровье
            'attack': data['stats'][1]['base_stat'],  # Урон
        }
        return pokemon_data
    else:
        return None


def send_email(subject, message, to_email):
    sender = settings.MY_EMAIL
    password = settings.MY_EMAIL_PASSWORD

    # Создание объекта MIMEText для сообщения
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email

    # SMTP-сервер и порт (для Gmail)
    server = smtplib.SMTP(str(settings.EMAIL_SERVER), settings.EMAIL_PORT)

    # защищенное соединение
    server.starttls()

    # Вход в свой email аккаунт
    server.login(sender, password)
    # Отправка email
    server.sendmail(sender, to_email, msg.as_string())

    # Закрытие соединения
    server.quit()


# http://127.0.0.1:8000/api/pokemon/list/?page=1&limit=5&filters=name,id,height,weight
def get_pokemon_list(request):
    # характеристики, которые пользователь указал в параметрах запроса
    page = request.GET.get('page')
    page = int(page) if page and page.isdigit() else 1
    limit = request.GET.get('limit')
    limit = int(limit) if limit and limit.isdigit() else 5
    offset = (page - 1) * limit

    filters = request.GET.get('filters', '').split(',')

    # Генерируйте URL для API запроса, включая характеристики
    url = f'https://pokeapi.co/api/v2/pokemon?limit={limit}&offset={offset}'
    response = requests.get(url)

    filtered_pokemon_list = []

    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])

        for result in results:
            details_url = result['url']
            details_response = requests.get(details_url)

            if details_response.status_code == 200:
                details = details_response.json()

                # словарь, в котором характеристики покемона будут только те, которые указал пользователь
                filtered_details = {key: details[key] for key in filters if key in details}
                filtered_pokemon_list.append(filtered_details)

    return JsonResponse({'filtered_pokemon_list': filtered_pokemon_list})


# http://127.0.0.1:8000/api/pokemon/1/?filters=name,id,height,weight
def get_pokemon_id(request, pokemon_id):
    filters = request.GET.get('filters', '').split(',')

    id = int(pokemon_id) if pokemon_id and pokemon_id.isdigit() else 1
    url = f'https://pokeapi.co/api/v2/pokemon/{id}/'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        filtered_details = {key: data[key] for key in filters if key in data}
    else:
        return JsonResponse({'pokemon_id_info': 'error'})

    return JsonResponse({'pokemon_id_info': filtered_details})


# http://127.0.0.1:8000/api/pokemon/random
def pokemon_random(request):
    all_pokemons = get_all_pokemons()
    random_index = random.randrange(len(all_pokemons))
    url = f'https://pokeapi.co/api/v2/pokemon/{all_pokemons[random_index]}/'
    response = requests.get(url)
    pokemon_id = 'Покемона с таким id не существует'
    if response.status_code == 200:
        data = response.json()
        pokemon_id = data['id']

    return JsonResponse({'random pokemon id': pokemon_id})


# http://127.0.0.1:8000/api/fight/?pokemon_id=4&opponent_id=1
def get_fight_info(request):
    user_pokemon = request.GET.get('pokemon_id')
    user_pokemon = int(user_pokemon) if user_pokemon and user_pokemon.isdigit() else 1
    opponent_pokemon = request.GET.get('opponent_id')
    opponent_pokemon = int(opponent_pokemon) if opponent_pokemon and opponent_pokemon.isdigit() else 2
    user_pokemon_info = get_pokemon_data(user_pokemon)
    opponent_pokemon_info = get_pokemon_data(opponent_pokemon)

    info = {
        "your pokemon": user_pokemon_info,
        "opponent pokemon": opponent_pokemon_info,
    }

    return JsonResponse(info)


# http://127.0.0.1:8000/api/fight/5/?pokemon_id=4&opponent_id=1
def update_pokemon_data(request, number):
    user_pokemon = request.GET.get('pokemon_id')
    user_pokemon = int(user_pokemon) if user_pokemon and user_pokemon.isdigit() else 1
    opponent_pokemon = request.GET.get('opponent_id')
    opponent_pokemon = int(opponent_pokemon) if opponent_pokemon and opponent_pokemon.isdigit() else 2
    user_pokemon_info = get_pokemon_data(user_pokemon)
    opponent_pokemon_info = get_pokemon_data(opponent_pokemon)

    hp_select = user_pokemon_info['hp']
    hp_vs = opponent_pokemon_info['hp']
    round_winner = None

    vs_number = random.randint(1, 10)

    # проверка кто атакует и пересчёт hp
    if hp_vs > 0 and hp_select > 0:
        if number % 2 == vs_number % 2:
            hp_vs -= user_pokemon_info['attack']
            round_winner = user_pokemon_info['name']
        else:
            hp_select -= opponent_pokemon_info['attack']
            round_winner = opponent_pokemon_info['name']

    # проверка победителя
    winner = None
    if hp_select <= 0:
        winner = opponent_pokemon_info['name']
    elif hp_vs <= 0:
        winner = user_pokemon_info['name']

    # формирование ответа
    res = {
        "select_pokemon": {
            "name": user_pokemon_info['name'],
            "hp": hp_select,
            "attack": user_pokemon_info['attack'],
        },
        "vs_pokemon": {
            "name": opponent_pokemon_info['name'],
            "hp": hp_vs,
            "attack": opponent_pokemon_info['attack'],
        },
        "round_results": [{
            "number": number,
            "hp": hp_select,
        },
            {
                "number": vs_number,
                "hp": hp_vs,
            },
            round_winner],
        "game_winner": winner,
    }
    return JsonResponse(res)


# http://127.0.0.1:8000/api/fight/fast/?pokemon_id=4&opponent_id=1
def get_fast_fight_result(request):
    user_pokemon = request.GET.get('pokemon_id')
    user_pokemon = int(user_pokemon) if user_pokemon and user_pokemon.isdigit() else 1
    opponent_pokemon = request.GET.get('opponent_id')
    opponent_pokemon = int(opponent_pokemon) if opponent_pokemon and opponent_pokemon.isdigit() else 2
    user_pokemon_info = get_pokemon_data(user_pokemon)
    opponent_pokemon_info = get_pokemon_data(opponent_pokemon)

    hp_select = user_pokemon_info['hp']
    hp_vs = opponent_pokemon_info['hp']

    rounds = []  # история раундов

    # раунды, пока у кого-нибудь не закончится hp
    while hp_select > 0 and hp_vs > 0:
        number = random.randint(1, 10)
        vs_number = random.randint(1, 10)

        round_winner = None
        # проверка кто атакует и пересчёт hp
        if number % 2 == vs_number % 2:
            hp_vs -= user_pokemon_info['attack']
            round_winner = user_pokemon_info['name']
        else:
            hp_select -= opponent_pokemon_info['attack']
            round_winner = opponent_pokemon_info['name']
        # запись в историю раундов
        rounds.append([{
            "number": number,
            "hp": hp_select,
        },
            {
                "number": vs_number,
                "hp": hp_vs,
            }, round_winner])

    # проверка победителя
    winner = None
    if hp_select <= 0:
        winner = opponent_pokemon_info['name']
    elif hp_vs <= 0:
        winner = user_pokemon_info['name']

    # формирование ответа
    res = {
        "select_pokemon": {
            "name": user_pokemon_info['name'],
            "hp": hp_select,
            "attack": user_pokemon_info['attack'],
        },
        "vs_pokemon": {
            "name": opponent_pokemon_info['name'],
            "hp": hp_vs,
            "attack": opponent_pokemon_info['attack'],
        },
        "rounds": rounds,
        "game_winner": winner,
    }
    return JsonResponse(res)
