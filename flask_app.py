from flask import Flask, request
import logging
import json
import requests


def get_country(city_name):
    try:
        url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            'geocode': city_name,
            'format': 'json'
        }
        data = requests.get(url, params).json()
        # все отличие тут, мы получаем имя страны
        return data['response']['GeoObjectCollection']['featureMember'][0][
            'GeoObject']['metaDataProperty']['GeocoderMetaData'][
            'AddressDetails']['Country']['CountryName']
    except Exception as e:
        return e

def get_inf_organization(org,city):
    try:
        url = "https://search-maps.yandex.ru/v1/"
        key = 'dda3ddba-c9ea-4ead-9010-f43fbc15c6e3'
        coord = get_coordinates(city)
        cor = ''
        cor = str(coord[0]) + ', ' + str(coord[1])
        print(cor)
        params = {
            'apikey': key,
            'text': org,
            'lang': 'ru_RU',
            'll': cor,
            "type": "biz"
            }
        data = requests.get(url, params).json()
        organization = data["features"][0]
        address = organization["properties"]["CompanyMetaData"]["address"]
        name =  organization["properties"]["CompanyMetaData"]["name"]
        phone = organization["properties"]["CompanyMetaData"]["Phones"][0]["formatted"]
        hours = organization['properties']['CompanyMetaData']["Hours"]["text"]
        inf = 'Нашла: ' + name + '. По адресу: ' + address + '. Работает: ' + hours + '. Телефон: ' + phone
        # все отличие тут, мы получаем имя страны
        return inf
    except Exception as e:
        return e
def get_coordinates(city_name):
    try:
        # url, по которому доступно API Яндекс.Карт
        url = "https://geocode-maps.yandex.ru/1.x/"
        # параметры запроса
        params = {
            # город, координаты которого мы ищем
            'geocode': city_name,
            # формат ответа от сервера, в данном случае JSON
            'format': 'json'
        }
        # отправляем запрос
        response = requests.get(url, params)
        # получаем JSON ответа
        json = response.json()
        # получаем координаты города (там написаны долгота(longitude),
        # широта(latitude) через пробел).
        # Посмотреть подробное описание JSON-ответа можно
        # в документации по адресу
        # https://tech.yandex.ru/maps/geocoder/
        coordinates_str = json['response']['GeoObjectCollection'][
            'featureMember'][0]['GeoObject']['Point']['pos']
        # Превращаем string в список, так как точка -
        # это пара двух чисел - координат
        long, lat = map(float, coordinates_str.split())
        # Вернем ответ
        return long, lat
    except Exception as e:
        return e

app = Flask(__name__)

# Добавляем логирование в файл. Чтобы найти файл,
# перейдите на pythonwhere в раздел files, он лежит в корневой папке
logging.basicConfig(level=logging.INFO, filename='app.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Request: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    global d
    global city
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Я могу рассказать об организациях в вашем городе. О каком городе вы хотели бы узнать?'
        d = 0
        return

    # Получаем города из нашего
    cities = get_cities(req)
    if not cities and d == 0:
        res['response']['text'] = 'К сожалению такого не нашлось'
    elif len(cities) == 1 and d == 0:
        city = cities[0]
        res['response']['text'] = 'Этот город в стране - ' + get_country(cities[0]) + '. Какие организации поискать?'
        d = 1
    elif len(cities) > 1:
        res['response']['text'] = 'Я могу рассказать только про один город!'
    elif d == 1:
        inf = get_inf_organization(req['request']['original_utterance'].lower(), city)
        res['response']['text'] = inf + '. О чём ещё вам рассказать?'
        d = 2
        pass
    elif d == 2:
        g = 0
        for i in ['нет','не надо','не нужно','не хочу','ни о чём','ни о чем','no']:
            if i in req['request']['original_utterance'].lower():
                g = 1
        if g == 1:
            res['response']['text'] = 'Приятно помогать! До свидания!'
            res['response']['end_session'] = True
            d = 0
        else:
            inf = get_inf_organization(req['request']['original_utterance'].lower(), city)
            res['response']['text'] = inf + '. О чём ещё вам рассказать?'


def get_cities(req):
    cities = []
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            if 'city' in entity['value']:
                cities.append(entity['value']['city'])
    return cities


if __name__ == '__main__':
    app.run()
