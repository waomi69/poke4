from django.http import HttpResponse
from django.urls import reverse
from django.test import TestCase, LiveServerTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait

from main.models import FightForm

from main.views import fight
from django.contrib.auth.models import User


class PokemonsViewTest(TestCase):

    def test_index(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["pokemon_info"]), 3)
        self.assertEqual(response.context["pokemon_info"][0]["name"], "bulbasaur")

    def test_pokemon_detail(self):
        url = reverse('pokemon_detail', args=["bulbasaur"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["pokemon"]["name"], "bulbasaur")
        self.assertEqual(response.context["pokemon"]["attack"], 49)
        self.assertEqual(response.context["pokemon"]["height"], 7)
        abilities = response.context["pokemon"]["abilities"]
        total_abilities = sum(len(ability_list) for ability_list in abilities)
        self.assertEqual(total_abilities, 2)

        # def test_fight(self):
        # url = reverse('fight', args=["bulbasaur"])
        # response = self.client.get(url)
        # self.assertEqual(response.status_code, 200)
        # self.assertEqual(response.context["user_pokemon"]["name"], "bulbasaur")
        # self.assertEqual(response.context["user_pokemon"]["attack"], 49)
        # self.assertTrue(response.context["opponent_pokemon"]["name"] != "bulbasaur")
        # self.assertTrue(response.context["round"] == 1)
        from django.test import TestCase, RequestFactory

    def test_fight(self):
        # Создаем запрос с использованием reverse
        url = reverse('fight', args=["pikachu"])
        response_before_fight = self.client.get(url)

        # Проверяем, что получен ожидаемый HTTP-ответ перед началом боя
        self.assertEqual(response_before_fight.status_code, 200)

        # # Устанавливаем статичные значения для вражеского покемона (Bulbasaur)
        # self.client.session['opponent_pokemon'] = {
        #     'name': 'bulbasaur',
        #     'hp': 45,
        #     'attack': 49,
        #     'png': 'bulbasaur.png'
        # }
        #
        # # Устанавливаем статичные значения для союзного покемона (Pikachu)
        # self.client.session['user_pokemon'] = {
        #     'name': 'pikachu',
        #     'hp': 35,
        #     'attack': 55,
        #     'png': 'pikachu.png'
        # }

        # Проверяем, что данные были сохранены в сессии перед началом боя
        user_hp_before_fight = self.client.session['user_hp']
        opponent_hp_before_fight = self.client.session['opponent_hp']

        form_data = {
            'user_number': 5,
            'pokemon_name': 'pikachu'
        }
        # Вызываем функцию после окончания боя
        response_after_fight = self.client.post(url, form_data)

        # Проверяем, что получен ожидаемый HTTP-ответ после боя
        self.assertEqual(response_after_fight.status_code, 200)

        # Проверяем, что данные были сохранены в сессии после боя
        user_hp_after_fight = self.client.session['user_hp']
        opponent_hp_after_fight = self.client.session['opponent_hp']

        # Дополнительно можно проверить значения user_hp и opponent_hp до и после боя
        self.assertEqual(user_hp_before_fight, self.client.session['user_pokemon']['hp'])
        self.assertEqual(opponent_hp_before_fight, self.client.session['opponent_pokemon']['hp'])
        # Дополнительно можно проверить, что значения изменились после боя
        print(f"Before Fight: user_hp={user_hp_before_fight}, opponent_hp={opponent_hp_before_fight}")
        print(f"After Fight: user_hp={user_hp_after_fight}, opponent_hp={opponent_hp_after_fight}")

        self.assertTrue(
            user_hp_before_fight != user_hp_after_fight or opponent_hp_before_fight != opponent_hp_after_fight)

        # Проверяем, что данные в сессии были использованы для рендеринга
        print(f"Rendered user_hp={response_after_fight.context['user_hp']}, opponent_hp={response_after_fight.context['opponent_hp']}")

        self.assertEqual(response_after_fight.context['user_hp'], user_hp_after_fight)
        self.assertEqual(response_after_fight.context['opponent_hp'], opponent_hp_after_fight)


    def test_api_pokemon_random(self):
        url = reverse('pokemon_random')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        data = response.json()
        self.assertIn('random pokemon id', data)

    def test_api_pokemon_list(self):
        url = reverse('pokemon_list')
        response = self.client.get(url, {'page': 1, 'limit': 5, 'filters': 'name,id'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('filtered_pokemon_list', data)
        self.assertEqual(len(data["filtered_pokemon_list"]), 5)
        self.assertEqual(len(data["filtered_pokemon_list"][0]), 2)
        self.assertEqual(data["filtered_pokemon_list"][4]["name"], "charmeleon")

    def test_api_pokemon_id(self):
        url = reverse('pokemon_id', args=["bulbasaur"])
        response = self.client.get(url, {'filters': 'name,id,height,weight'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["pokemon_id_info"]["name"], "bulbasaur")
        self.assertIn('weight', data["pokemon_id_info"])
        self.assertEqual(data["pokemon_id_info"]["height"], 7)

    def test_api_fight_info(self):
        url = reverse('fight_info')
        response = self.client.get(url, {'pokemon_id': 4, 'opponent_id': 1})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertTrue(data["your pokemon"] != data["opponent pokemon"])
        self.assertEqual(data["your pokemon"]["name"], "charmander")

    def test_api_update_pokemon_data(self):
        url = reverse('update_pokemon_data', args=[5])
        response = self.client.get(url, {'pokemon_id': 4, 'opponent_id': 1})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('round_results', data)
        self.assertTrue(data["select_pokemon"] != data["vs_pokemon"])
        self.assertEqual(data["select_pokemon"]["attack"], 52)
        self.assertEqual(data["round_results"][0]["number"], 5)

    def test_api_fast_fight_result(self):
        url = reverse('fast_fight_result')
        response = self.client.get(url, {'pokemon_id': 4, 'opponent_id': 1})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('rounds', data)
        self.assertTrue(data["select_pokemon"] != data["vs_pokemon"])
        self.assertEqual(data["select_pokemon"]["attack"], 52)
        self.assertTrue(data["rounds"][len(data["rounds"]) - 1][-1] == data['game_winner'])

    def test_api_save_pokemon(self):
        url = reverse('save_pokemon', args=["bulbasaur"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.context
        self.assertTrue(data["result"] == 'Success')


class SeleniumTests(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_index(self):
        self.selenium.get(f"{self.live_server_url}/")
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        self.assertIn("Список", self.selenium.find_element(By.XPATH, "/html/body/div/div/div[1]/h1").text)
        # тестирование работы перехода на следующую страницу
        self.selenium.find_element(By.XPATH, "/html/body/div/div/div[3]/span/a[1]").click()
        self.assertTrue("charmander" ==
                        self.selenium.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[1]/div/div/h5").text)
        # тестирование поиска покемона по имени
        search_string = self.selenium.find_element(By.XPATH, "/html/body/div/div/div[1]/form/input")
        search_string.send_keys("ivysaur")
        self.selenium.find_element(By.XPATH, "/html/body/div/div/div[1]/form/button").click()
        self.assertTrue("ivysaur" ==
                        self.selenium.find_element(By.XPATH, "/html/body/div/div/div/div/div/h5").text)

    def test_read(self):
        self.selenium.get(f"{self.live_server_url}/pokemon/ivysaur")
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        self.assertIn("ivysaur", self.selenium.title)
        self.assertIn("Abilities",
                      self.selenium.find_element(By.XPATH, "/html/body/div/div/div/div/div[2]/p[5]").text)
        # тестирование сохранения информации о покемоне
        self.selenium.find_element(By.XPATH, "/html/body/div/div/div/div/div[2]/form/button").click()
        self.assertIn("Success",
                      self.selenium.find_element(By.XPATH, "/html/body/div/div/div").text)

    def test_fight(self):
        self.selenium.get(f"{self.live_server_url}/fight/ivysaur")
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        self.assertIn("раунд 1", self.selenium.find_element(By.XPATH, "/html/body/div/div/div/h2").text)

        user_number = self.selenium.find_element(By.XPATH, '//*[@id="id_user_number"]')
        user_number.send_keys("5")
        self.selenium.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div[1]/form/button").click()

        self.selenium.get(f"{self.live_server_url}/fight/ivysaur")
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        user_mail = self.selenium.find_element(By.XPATH, '//*[@id="id_email"]')
        user_mail.send_keys("kuldarevilya9@gmail.com")
        self.selenium.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div[2]/form/button").click()
