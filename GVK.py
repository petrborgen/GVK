#!/usr/bin/env python3

import time
import requests
import os
from sys import platform
import copy
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor as PoolExecutor
import configparser


# Каркасы урлов для запросам к разным методами ВК Api
utils_resolveScreenName = 'https://api.vk.com/method/utils.resolveScreenName'
groups_getById = 'https://api.vk.com/method/groups.getById'
users_get = 'https://api.vk.com/method/users.get'
photos_getAlbums = 'https://api.vk.com/method/photos.getAlbums'
photos_get = 'https://api.vk.com/method/photos.get'
groups_search = 'https://api.vk.com/method/groups.search'
account_getProfileInfo = 'https://api.vk.com/method/account.getProfileInfo'

egyptian_power = None

if platform.startswith('linux'):
    slash = '/'
else:
    slash = '\\'


class Answer:
    Yes = ['y', 'yes', 'н', 'нуы', 'да', 'la', 'ok', 'щл', 'ок', 'jr', 'конечно', 'rjytxyj']
    No = ['n', 'no', 'т', 'тщ', 'не', 'yt', 'нет', 'ytn', 'неа', 'ytf']
    Quit = ['q', 'й']
    Back = ['b', 'и']
    BackBack = ['bb', 'ии']
    Search = ['s', 'ы']
    Inverted = ['i', 'ш', '.', '/', 'ю']


def create_config(path, token):
    config = configparser.ConfigParser()
    config.add_section('Settings')
    config.set('Settings', 'TOKEN', token)

    with open(path, 'w') as config_file:
        config.write(config_file)


def shine(text_in, color):
    # Цвета для ответов программы
    color_dic = dict(GOLD='\033[93m',
                     BOLD='\033[1m',
                     OK='\033[92m',
                     FAIL='\033[91m',
                     END='\033[0m')
    text_out = color_dic[color] + text_in + color_dic['END']
    return text_out


# Указатель строки ввода
user_m = shine('[>] ', 'GOLD')


# Для демонстрации удалённости меню от начала
def mini_m(level):
    m = ['•'] * 4
    m[level] = shine('☻', 'GOLD')
    print(*m, '\n')


# Ограничивает ширину текстового вывода
def text_restrict(text, length_stop):
    text_length = len(text)
    piece_count = (text_length // length_stop)
    if text_length % length_stop != 0:
        piece_count += 2
    else:
        piece_count += 1
    result_text = []

    for n in range(piece_count):
        start_point = length_stop * n - length_stop
        end_point = length_stop * n
        splitting = text[start_point:end_point].rpartition(' ')

        result_text.append(splitting[0])
        result_text.append('\n')
        result_text.append(splitting[2])

    result_text = ''.join(result_text)
    return result_text


# Табличник
def tabula(headers, data, length_control):
    columns = copy.deepcopy(headers)
    main_list = copy.deepcopy(data)
    # Докидываем имена колонок в список
    main_list.insert(0, columns)

    # Список самых длинных элементов в каждой строке
    max_obj_lengths = []
    # Максимальные длины будущих столбцов
    max_column_lengths = [0] * len(main_list[0])  # Заполняем заготовку нулями
    for _lst, lst in enumerate(main_list):
        obj_lengths = []  # Список длин каждого элемента в lst(строке)
        for _obj, obj in enumerate(lst):
            obj_len = len(str(obj))  # Длина элемента obj
            # Обрезаем слишком длинное, если не задействован контроль длины
            if length_control == 0 and obj_len >= 140:
                lst[_obj] = str(obj)[:140 + 3] + '...'
                obj_len = len(str(obj))
            obj_lengths.append(obj_len)
            # Если длина элемента оказалась больше максимальной длины в соотв.столбце, обновляем значение макс. длины
            if obj_len > max_column_lengths[_obj]:
                max_column_lengths[_obj] = obj_len
        max_obj_lengths.append(max(obj_lengths))

    # Находим самый длинный объект
    max_obj = max(max_obj_lengths)
    dotdotdot = ''
    if length_control > 3:
        max_obj = length_control
        dotdotdot = '...'

    if max(max_column_lengths) != max_obj:
        max_column_lengths[max_column_lengths.index(max(max_column_lengths))] = max_obj

    # Преобразуем элементы изначального списка в развёртки будущих элементов таблицы, раздвигая столбцы
    for n in range(len(main_list[0])):
        for lst in main_list:
            column_obl_length = len(str(lst[n]))
            if column_obl_length < max_column_lengths[n]:
                lst[n] = ' ' + (str(lst[n]) + ' ' * (max_column_lengths[n] - column_obl_length) + ' │')
            elif column_obl_length == max_column_lengths[n]:
                lst[n] = ' ' + (str(lst[n]) + ' │')
            else:
                lst[n] = ' ' + (str(lst[n])[:max_obj - 3] + dotdotdot + ' │')

    # Функция печати линии
    def print_frame_line(template, lengths):
        line_templates = dict(
            TABLE_TOP=['╒', '═', '╤', '╕'],
            BODY_TOP=['╞', '═', '╪', '╡'],
            BODY=['├', '─', '┼', '┤'],
            TABLE_END=['╘', '═', '╧', '╛']
        )
        s = line_templates[template][0]
        for _length, length in enumerate(lengths):
            s += line_templates[template][1] * length
            if _length + 1 < len(lengths):
                s += line_templates[template][2]
        s += line_templates[template][3]
        print(s)

    # Формируем список длин элементов в заголовке, чтобы на его основе выводить рамки
    lst0_obj_lengths = []
    for _obj, obj in enumerate(main_list[0]):
        lst0_obj_lengths.append(len(str(obj)))

    # Расставляем рамки и печатаем таблицу
    for _lst, lst in enumerate(main_list):
        if _lst == 0:
            print_frame_line('TABLE_TOP', lst0_obj_lengths)
            print('\033[93m│', *lst, '\033[0m')
        elif _lst == 1:
            print_frame_line('BODY_TOP', lst0_obj_lengths)
            print('│', *lst)
        else:
            print_frame_line('BODY', lst0_obj_lengths)
            print('│', *lst)
    print_frame_line('TABLE_END', lst0_obj_lengths)


def gj_account_get_profile_info():
    params = dict(access_token=TOKEN, v=5.52)
    try:
        response = requests.get(account_getProfileInfo, params)
    except requests.exceptions.ConnectionError:
        input(shine('\n Беда с интернетом!', 'FAIL'))
        quit()
    else:
        response = response.json()
        return response


# Список групп по ключевому слову
def gj_groups_search(what_find, offset, count):
    params = dict(q=what_find, offset=offset, count=count, access_token=TOKEN, v=5.52)
    try:
        response = requests.get(groups_search, params)
    except requests.exceptions.ConnectionError:
        input(shine('\n Беда с интернетом!', 'FAIL'))
        quit()
    else:
        response = response.json()
        return response


# Определяет тип объекта (пользователь, сообщество, приложение) и его идентификатор по короткому адресу (screen_name)
def gj_utils_resolve_screen_name(screen_name):
    params = dict(screen_name=screen_name, access_token=TOKEN, v=5.52)
    try:
        response = requests.get(utils_resolveScreenName, params)
    except requests.exceptions.ConnectionError:
        input(shine('\n Беда с интернетом!', 'FAIL'))
        quit()
    else:
        response = response.json()
        return response


# Возвращает информацию о заданном сообществе
def gj_groups_get_by_id(*group_ids):
    params = dict(group_ids=group_ids, fields='description', access_token=TOKEN, v=5.52)
    try:
        response = requests.get(groups_getById, params)
    except requests.exceptions.ConnectionError:
        input(shine('\n Беда с интернетом!', 'FAIL'))
        quit()
    else:
        response = response.json()
        return response


# Возвращает расширенную информацию о пользователях
def gj_users_get(user_id):
    params = dict(user_id=user_id, access_token=TOKEN, v=5.52)
    try:
        response = requests.get(users_get, params)
    except requests.exceptions.ConnectionError:
        input(shine('\n Беда с интернетом! ', 'FAIL'))
        quit()
    else:
        response = response.json()
        return response


# Возвращает список фотоальбомов пользователя или сообщества
def gj_photos_get_albums(owner_id):
    params = dict(owner_id=owner_id, access_token=TOKEN, v=5.52)
    try:
        response = requests.get(photos_getAlbums, params)
    except requests.exceptions.ConnectionError:
        input(shine('\n Беда с интернетом! ', 'FAIL'))
        quit()
    else:
        response = response.json()
        return response


# Фильтрация данных из списка соббществ с добавлением доп.информации
def group_sort(groups_items):
    sorted_list = []
    for _group, group in enumerate(groups_items):
        sorted_list.append([])
        # Обрезает длинные названия. Но нахуя?
        group['name'] = group['name'][:140]
        # Достаём для каждого сообщества его имя и короткий адрес, в первую колонку ддобавляем нумерацию
        sorted_list[groups_items.index(group)].extend([str(_group + 1), str(group['name']),
                                                       group['screen_name']])
    return sorted_list


# Фильтрация данных из списка альбомов с добавлением доп.информации
def alb_sort(albums_items):
    sorted_list = []
    sizes = [0]
    # Достаём для каждого альбома его имя, айдишник, дату последнего обновления и количество элементов
    for _album, album in enumerate(albums_items):
        sorted_list.append([])
        sizes.append(album['size'])
        sorted_list[_album].extend([str(album['title']), str(album['id']), album['size']])

    # Сортируем альбомы по количеству элеменов
    sorted_list.sort(key=lambda n: n[-1], reverse=True)

    # Добавляем нумерацию в первую колонку
    for _n, n in enumerate(sorted_list):
        n.insert(0, str(_n + 1))

    # Вычисляем какую-то дичь и на её основе рисуем визуальные маркеры распределения пространства в альбомах
    max_size = max(sizes) + 1
    mean_size = int(sum(sizes) / len(sizes)) + 1
    for n in sorted_list:
        somefuckvalue = int((int(n[-1]) / mean_size) * 25 / (max_size / mean_size))
        if somefuckvalue < 1 and n[-1] > 0:
            indicator, somefuckvalue = '▌', 1
        elif somefuckvalue < 1 and n[-1] <= 0:
            indicator = ''
        else:
            indicator = '█'

        n.insert(3, indicator * somefuckvalue)

    return sorted_list, sum(sizes)


# Возвращает список фотографий в альбоме
def gj_photos_get(album_id, offset, owner_id):
    params = dict(owner_id=owner_id, album_id=album_id, count=1000,
                  offset=offset, access_token=TOKEN, v=5.52)
    try:
        response = requests.get(photos_get, params)
    except requests.exceptions.ConnectionError:
        input(shine('\n Беда с интернетом! ', 'FAIL'))
        quit()
    else:
        response = response.json()
        if 'error' in response:
            if response['error']['error_code'] == 200:
                return response
            else:
                print(shine('\nSorry friend, but ' + response['error']['error_msg'].lower() + '...\n', 'FAIL'))
                input(shine('Нажми ENTER\n', 'BOLD'))
                time.sleep(0.1)
                quit()

        return response


# Сохраняет фотографии
def photo_save(photo_items, album_dir):
    # Размер фото : ссылка на него
    photo_dic = {}
    # Только размеры
    photo_list = []

    # Вытаскиваем разрешения фото и ссылки
    for item in photo_items:
        if 'photo_' in item:
            photo_size = int(item.partition('_')[2])
            photo_link = photo_items[item]
            photo_dic.setdefault(photo_size, photo_link)
            photo_list.append(photo_size)

    # НАходим версию фото в максимальном разрешении
    max_size = max(photo_list)
    max_size = 'photo_' + str(max_size)

    # Вытаскиваем название файла на сервере
    file_name = photo_items[max_size].rpartition('?size')[0].rpartition('/')[2]

    # Проверяем, что в директории сохранения нет ещё файла с таким именем
    check_file = os.path.exists(album_dir + '\\' + file_name)

    # Сохраняем файл на диск
    if not check_file:
        p = requests.get(photo_items[max_size])
        f = open(album_dir + '\\' + file_name, 'wb')
        f.write(p.content)
        f.close()

    # ВК не любит слишком частых запросов
    time.sleep(0.3)


# МАЛЫЙ ЗАГРУЗЧИК
def save_one(albums_items, album_id, album_dir, owner_id, lock):
    album_id = int(album_id)

    # Мудрый ВК не даёт получить больше тысячи объектов за раз, будем склеивать из нескольких кусков
    glued_photos_items = []

    # Инициируем получение списка фото на каждую тысячу
    for album in albums_items:
        if album['id'] == album_id:
            size = album['size']
            rerun = size / 1000
            rerun = int(rerun)

            # Отступ, необходимый для получения определенного подмножества записей.
            offset = 0

            if rerun <= 1:
                rerun += 1

            # В несколько заходом достаём инфу по всем фото в альбоме
            for n in range(0, rerun):

                # Проникаем внутрь альбома
                time.sleep(0.1)
                photos_info = gj_photos_get(album_id, offset, owner_id)

                # Если альбом не предоставляет к себе доступа, отдаём его айдишник в сборщик недоступного
                if 'error' in photos_info:
                    lock.append(album_id)
                    break
                else:
                    photos_items = photos_info['response']['items']

                # Склеиваем список фоток
                glued_photos_items += photos_items
                offset += 1000

    # Маленький загрузчик отращивает себе несколько очумелых ручек
    # и запускает их поглубже в объединённый список фотографий
    with PoolExecutor(max_workers=egyptian_power) as executor:
        for photo_items in glued_photos_items:
            executor.submit(photo_save, photo_items, album_dir)
    executor.shutdown(wait=True)
    return lock


# БОЛЬШОЙ ЗАГРУЗЧИК
def save_all(albums_items, main_dir, owner_id, lock):
    # Для каждого альбома запускаем маленький загрузчик
    for album in tqdm(albums_items):
        album_id = album['id']

        # Игнорируем некрасивые символы в имени альбома
        name = album['title']
        ignore_symbols = ['/', '\\', ':', '*', '?', '<', '>', '|', '"', '%', '!', '@', '+', ' ']
        for i in ignore_symbols:
            if i in name:
                name = name.replace(i, '_')

        # Лепим к адресу каталога загрузки имя альбома
        album_dir = main_dir + name

        # Проверяем каталог на наличие и создаём его, если наличие не подтвердилось
        check_file = os.path.exists(album_dir)
        if not check_file:
            os.mkdir(main_dir + name)

        # Старший брат вызывает младшего
        lock = save_one(albums_items, album_id, album_dir, owner_id, lock)
    return lock


# Раздел скачивания альбомов
def stage3(albums_info, owner_id):
    # Достаём количество альбомов
    albums_count = albums_info['response']['count']
    # И их данные
    albums_items = albums_info['response']['items']
    # Структурируем данные в предтабличную форму, отсеивая ненужное и добавляя нужное
    albums_sorted, photos_count = alb_sort(albums_items)

    # Выводим на экран общее количество альбомов и фотографий в них
    time.sleep(0.1)
    print(f'{shine("Всего альбомов:", "GOLD")}\n{albums_count}\n')
    time.sleep(0.1)
    print(f'{shine("Всего фото:", "GOLD")}\n{photos_count}\n')
    time.sleep(0.1)

    # Колонки будущей таблицы
    columns = ['№', 'НАЗВАНИЕ АЛЬБОМА', 'ID АЛЬБОМА', 'ИНФОГРАФИКА', '♦']

    # Печатаем таблицу
    time.sleep(0.1)
    tabula(headers=columns, data=albums_sorted, length_control=0)
    time.sleep(0.1)

    # __ВЫБОР ОБЪЕКТОВ ДЛЯ СКАЧИВАНИЯ__
    while True:
        try:
            while True:
                # Печатаем меню выбора альбома для скачивания
                time.sleep(0.1)
                print(f'\n • Введи{shine(" номер строки", "GOLD")}, чтобы скачать соответствующий альбом'
                      f'\n • Введи{shine(" 0 (нуль)", "GOLD")}, чтобы скачать их все'
                      f'\n • Введи{shine(" B", "GOLD")}, чтобы вернуться назад'
                      f'\n • Введи{shine(" BB", "GOLD")}, чтобы вернуться в самое начало'
                      f'\n • Введи{shine(" Q", "GOLD")}, чтобы выйти\n')

                # Получаем номер альбома для скачки или команду скачать их все (0)
                album_number = input(user_m).lower()

                # Если был инициирован пустой ввод, вызываем поле ввода ещё раз
                while True:
                    if album_number == '':
                        album_number = input(user_m).lower()
                        time.sleep(0.1)
                        continue
                    else:
                        break

                # Соотносим номер введённой юзером строки с командой меню
                if album_number != '0':
                    if album_number in Answer.Back:
                        time.sleep(0.1)
                        break
                    elif album_number in Answer.BackBack:
                        time.sleep(0.1)
                        stage0()
                    elif album_number in Answer.Quit:
                        time.sleep(0.1)
                        quit()
                    else:
                        # ...либо айдишником альбома
                        for n in albums_sorted:
                            if album_number == n[0]:
                                album_id = n[2]
                                break
                            elif album_number == n[2]:
                                break
                        else:
                            print(shine('\n Ты ввёл неправильный номер, будь внимательнее!', 'FAIL'))
                            time.sleep(0.1)
                            break

                # Узнаём директорию, в которую будут сохранены фотографии
                time.sleep(0.1)
                main_dir = input(f'\n • Введи{shine(" адрес папки", "GOLD")} сохранения'
                                 f' либо{shine(" B ", "GOLD")}— назад'
                                 f' либо{shine(" BB ", "GOLD")}— в начало\n\n{user_m}').lower()

                time.sleep(0.1)

                # Предостерегаемся от пустого ввода
                while True:
                    if main_dir == '':
                        main_dir = input(user_m).lower()
                        continue
                    else:
                        break

                # Вновь проверяем на ввод команды меню
                if main_dir in Answer.Back:
                    time.sleep(0.1)
                    break
                elif main_dir in Answer.BackBack:
                    time.sleep(0.1)
                    stage0()
                elif main_dir in Answer.Quit:
                    time.sleep(0.1)
                    quit()

                # Добавляем к директории косую черту
                main_dir = main_dir + slash
                # Проверяем на наличие указанного местоположения
                check_dir = os.path.exists(main_dir)
                # Предлагаем создать, если не обнаруживаем
                if not check_dir:
                    print(f'\n • Такой папки не существует, создать её? '
                          f'({shine("Yes", "OK")}/{shine("No", "FAIL")})\n')
                    save_answer = ''
                    while True:
                        if save_answer == '':
                            save_answer = input(user_m).lower()
                            time.sleep(0.1)
                            continue
                        else:
                            break

                    # Получив согласие, создаём
                    if save_answer in Answer.Yes:
                        try:
                            os.mkdir(main_dir)
                        except:
                            time.sleep(0.1)
                            print(shine('\n Не удаётся создать директорию', 'FAIL'))
                            input(shine('\n Нажми ENTER, чтобы вернуться в меню\n ', 'BOLD'))
                            time.sleep(0.1)
                            break
                    # Иначе возвращаемся в меню
                    elif save_answer in Answer.No:
                        break
                    else:
                        print(shine('\n Неверная команда\n', 'FAIL'))
                        time.sleep(0.1)
                        break

                # Сюда помещаются айдишники недоступных альбомов
                lock = []

                # Если юзер ввёл ноль, скачиваем все альбомы
                if album_number == '0':

                    print(shine('\n Постарайся не нажимать ничего во время выполнения.\n', 'BOLD'))

                    # Передаём в большой загрузчик данные всех альбомов, каталог загрузки и сборщик залоченных альбомов
                    # и засекаем время выполнения
                    time0 = time.time()
                    try:
                        lock = save_all(albums_items, main_dir, owner_id, lock)
                    except OSError:
                        print(shine('\nЗакончилось свободное пространство на диске, '
                                    'освободи его и запусти процедуру заново\n', 'FAIL'))
                        input(shine('Нажми ENTER для возврата в меню\n', 'BOLD'))
                        time.sleep(0.1)
                        break

                    # Завершаем
                    print("--- %s seconds ---" % (time.time() - time0))
                    time1 = time.time()

                    time.sleep(0.1)

                    print('\n┊┊┊▕▔╲▂▂▂╱▔▏┊┊┊┊')
                    print('╭━━╮╭┈╮┈╭┈╮╭━━╮┈')
                    print('╰╰╰┃▏╭╮┈╭╮▕┃╯╯╯┈')
                    print('┈┃┈┃▏┈┈▅┈┈▕┃┈┃┈┈')
                    print('┈┃┈┃▏┈╰┻╯┈▕┃┈┃┈┈')
                    print('┈┃┈╰▅▅▅☼▅▅▅╯┈┃┈┈')
                    print('┈╰━━┓┈╭┻╮┈┏━━╯┈┈')
                    print(shine('\n Шалость удалась! ', 'OK'))

                    # Если в списке залоченных альбомов по итогу что-то осело, выводим это на экран
                    lock2 = []
                    if lock:
                        time.sleep(0.1)
                        print(shine('\n\n Но, к сожалению, следующие альбомы оказались закрыты:\n', 'FAIL'))
                        for album in albums_sorted:
                            for n in lock:
                                if str(n) == album[2]:
                                    lock2.append(album[0] + ') ' + album[1])
                        for m in lock2:
                            print('', shine(m, 'FAIL'))

                    time.sleep(0.1)

                    # Предохраняемся от нажатия клавиш во время скачивания
                    while True:
                        input(shine('\n Нажми ENTER, чтобы скачать что-нибудь ещё\n ', 'BOLD'))
                        time2 = time.time()
                        if (time2 - time1) < 0.5:
                            continue
                        else:
                            break
                    break

                # Если юзер ввёл айдишник альбома или что-то похожее
                else:
                    # Засекаем время и передаём данные в малый загрузчик
                    time0 = time.time()
                    print(shine('\n Не нажимай ничего в процессе. Лучше пока сходи выпей чаю...\n', 'BOLD'))
                    lock = save_one(albums_items, album_id, main_dir, owner_id, lock)

                    # Завершаем
                    time1 = time.time()
                    print("--- %s seconds ---" % (time.time() - time0))

                    # Если список залоченных альбомов вернулся не пустым
                    if lock:
                        print(shine('\n Мне не удалось получить данные с альбома', 'FAIL'))

                    # Успех!
                    else:
                        print(shine('\n Отставить чай! Операция выполнена ', 'OK'))

                    time.sleep(0.1)

                    # Предохраняемся от нажатия клавиш в процессе скачивания
                    while True:
                        input(shine('\n Нажми ENTER для возврата в меню\n ', 'BOLD'))
                        time2 = time.time()
                        if (time2 - time1) < 0.5:
                            continue
                        else:
                            break

        except ValueError:
            time.sleep(0.1)
            print(shine('\n Ты что-то не так вводишь', 'FAIL'))
            continue

        if album_number in Answer.Back:
            os.system('cls||clear')
            break


# Этап получения информации о пользователе или сообществе
def stage2(link):
    while True:

        # __ВЫЯСНЯЕМ ИСТИННУЮ ПРИРОДУ ССЫЛКИ__

        # Обрезаем ссылку до короткого адреса
        screen_name = link.rpartition('/')[2]
        # Запрашиваем у ВК информацию по полученному адресу
        link_info = gj_utils_resolve_screen_name(screen_name)

        # Отлов ошибок
        try:
            if not link_info['response']:
                time.sleep(0.1)
                input(shine('\n Не нашёл такого аккаунта', 'FAIL') +
                      shine('\n\n Нажми ENTER для повторного ввода\n ', 'BOLD'))
                time.sleep(0.1)
                os.system('cls||clear')
                break
            if 'error' in link_info:
                time.sleep(0.1)
                print(shine('\n Sorry friend, but ' + link_info['error']['error_msg'].lower() + '...\n', 'FAIL'))
                input(shine(' Нажми ENTER\n ', 'BOLD'))
                time.sleep(0.1)
                os.system('cls||clear')
                break
        except KeyError:
            print(shine('\tНе балуйся! ', 'BOLD'))
            time.sleep(0.3)
            break

        # Чистим экран и выводим индикатор разделов
        os.system('cls||clear')
        mini_m(3)

        # __ЕСЛИ ССЫЛКА ВЕДЁТ НА ГРУППУ__
        if 'group' in link_info['response']['type']:
            # Достаём айдишник
            group_id = link_info['response']['object_id']
            # Чёрточка даёт понять ВК, что перед ним айдишник сообщества
            owner_id = '-' + str(group_id)
            # Запрашиваем информацию об альбомах сообщества
            albums_info = gj_photos_get_albums(owner_id)
            # Выспрашиваем у ВК подробности о сообществе
            group_info = gj_groups_get_by_id(group_id)

            # Следим за ошибками
            if 'error' in group_info:
                time.sleep(0.1)
                print(shine('\n Sorry friend, but ' + group_info['error']['error_msg'].lower() + '...\n', 'FAIL'))
                input(shine(' Нажми ENTER\n ', 'BOLD'))
                time.sleep(0.1)
                break

            # Фиксируем имя сообщества и его описание
            group_name = group_info['response'][0]['name']
            group_description = group_info['response'][0]['description']

            # Выводим интересующую информацию о сообществе на экран (имя, айдишник, короткая ссылка, описание)
            time.sleep(0.1)
            print(shine('Сообщество:\n', 'GOLD') + f'«{group_name}»')
            time.sleep(0.1)
            print(shine('\nID сообщества:\n', 'GOLD') + owner_id)
            time.sleep(0.1)
            print(shine('\nКороткий адрес сообщества:\n', 'GOLD') + screen_name)
            time.sleep(0.1)
            print(shine('\nОписание:', 'GOLD') + text_restrict(group_description, 110) + '\n')

            # Не забывая про ошибки
            if 'error' in albums_info:
                if 'Access denied: group photos are disabled' in albums_info['error']['error_msg']:
                    input(shine('Альбомы закрыты либо отсутствуют\n\n', 'FAIL') +
                          shine('Нажми Enter для повторного ввода\n', 'BOLD'))
                    time.sleep(0.1)
                elif 'Access denied: group access is denied' in albums_info['error']['error_msg']:
                    input(shine('\nСообщество недоступно\n\n', 'FAIL') +
                          shine('Нажми Enter для повторного ввода\n', 'BOLD'))
                    time.sleep(0.1)
                break

        # __ЕСЛИ ССЫЛКА ВЕДЁТ НА ПОЛЬЗОВАТЕЛЯ__
        elif 'user' in link_info['response']['type']:
            # Достаём айдишник
            user_id = link_info['response']['object_id']
            owner_id = user_id
            # Запрашиваем информацию об альбомах
            albums_info = gj_photos_get_albums(owner_id)
            # Расспрашиваем ВК о пользователе
            user_info = gj_users_get(user_id)

            # Ошибки
            if 'error' in user_info:
                time.sleep(0.1)
                print(shine('\n Sorry friend, but ' + user_info['error']['error_msg'].lower() + '...\n', 'FAIL'))
                input(shine(' Нажми ENTER\n ', 'BOLD'))
                time.sleep(0.1)
                break

            # Фиксируем имя пользователя и его фамилию
            first_name = user_info['response'][0]['first_name']
            last_name = user_info['response'][0]['last_name']

            # Выводим интересующую информацию о пользователе на экран (имя/фамилия, айдишник, погоняло)
            time.sleep(0.1)
            print(shine('Пользователь:\n', 'GOLD') + f'«{first_name} {last_name}»')
            time.sleep(0.1)
            print(shine('\nПогоняло пользователя:\n', 'GOLD') + str(screen_name))
            time.sleep(0.1)
            print(shine('\nID пользователя:\n', 'GOLD') + str(owner_id) + '\n')

            # Ошибочки
            if 'error' in albums_info:
                time.sleep(0.1)
                print(shine('\nSorry friend, but ' + albums_info['error']['error_msg'].lower() + '...\n', 'FAIL'))
                time.sleep(0.1)
                input(shine('Нажми ENTER для повторного ввода\n', 'BOLD'))
                time.sleep(0.1)
                break

        # Родила царица в ночь и не сообщество, и не юзера...
        else:
            input(shine(' Ты что-то не то ввёл\n\n Нажми Enter для повторного ввода\n ', 'FAIL'))
            time.sleep(0.1)
            break

        # Переходим к меню отображения и скачивания альбомов
        stage3(albums_info, owner_id)
        break


# Поисковый раздел
def stage1():
    while True:
        # Очищаем экран
        os.system('cls||clear')
        # Выводим индикатор разделов
        mini_m(1)
        # Выводим меню
        print(f' • Введи слово для поиска группы с таким именем (только безопасный поиск)\n'
              f' • Введи{shine(" B", "GOLD")}, чтобы вернуться назад\n'
              f' • Введи{shine(" Q", "GOLD")}, чтобы выйти\n')

        # __ПоДГОТОВКА К ПОИСКУ__

        # Что хотим найти
        what_find = ''

        # Защита от пустого ввода
        while True:
            if what_find == '':
                what_find = input(user_m).lower()
                time.sleep(0.1)
                continue
            else:
                break

        # Проверяем на ввод различные команды
        if what_find in Answer.Quit:
            time.sleep(0.1)
            quit()
        elif what_find in Answer.Back or what_find in Answer.BackBack:
            time.sleep(0.1)
            stage0()

        # Смещение, необходимое для выборки определённого подмножества результатов поиска
        offset = 0
        # Количество результатов поиска, которое необходимо вернуть
        count = 1000

        # Инициируем поисковую функцию по группам

        find = gj_groups_search(what_find, offset, count)

        # Если функция возвращает ошибку, выводим её текст на экран
        if 'error' in find:
            time.sleep(0.1)
            print(shine('\n Sorry friend, but ' + find['error']['error_msg'].lower() + '...\n', 'FAIL'))
            input(shine(' Нажми ENTER\n ', 'BOLD'))
            time.sleep(0.1)
            stage1()

        # Получаем количество сообществ, соответствующих запросу
        groups_count = find['response']['count']
        if groups_count > 0:
            # И их данные
            groups_items = find['response']['items']
        else:
            print(shine('\n По запросу ничего не найдено', 'FAIL'))
            input(shine('\n Нажми ENTER для новой попытки\n ', 'BOLD'))
            time.sleep(0.1)
            stage1()

        # Колонки будущей таблицы
        columns = ['№', 'НАЗВАНИЕ СООЩЕСТВА', 'КОРОТКИЙ АДРЕС СООБЩЕСТВА']

        # Чтобы выводить будущую таблицу на экран кусками по 20
        drift_for = 0
        drift_before = 20
        drift_list = group_sort(groups_items)

        # __ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ ПОИСКА__
        destination = 1
        while True:
            # Очищаем экран
            os.system('cls||clear')
            # Выводим индикатор разделов
            mini_m(2)
            # Выводим количество найденных сообществ
            print('По запросу ' + shine(f'«{what_find}»', 'BOLD') + ' найдено '
                  + shine(str(groups_count), 'BOLD') + ' сообществ\n')

            # Печатаем таблицу с именами найденных сообществ
            tabula(headers=columns, data=drift_list[drift_for:drift_before], length_control=75)

            # Выводим очередное меню
            print(f'\n • Введи {shine("номер строки", "GOLD")}, чтобы отобразить содержимое\n'
                  f' • Введи {shine("B", "GOLD")}, чтобы вернуться назад\n'
                  f' • Введи {shine("BB", "GOLD")}, чтобы вернуться в самое начало\n'
                  f' • Введи {shine("Q", "GOLD")}, чтобы выйти\n'
                  f' • Нажми {shine("ENTER", "GOLD")}, чтобы листать список\n'
                  f' • Введи {shine("I", "GOLD")}, чтобы изменить направление перелистывания\n')

            # Запрашиваем у пользователя номерок интересующего его сообщества из найденных по запросу
            group_number = str(input(user_m)).lower()

            # Проверяем на ввод команды навигации по разделам (выход/назад/самое начало)
            if group_number in Answer.Quit:
                time.sleep(0.1)
                quit()
            elif group_number in Answer.Back:
                time.sleep(0.1)
                stage1()
            elif group_number in Answer.BackBack:
                time.sleep(0.1)
                stage0()

            # или перелистывание по энтеру (командой "I" меняем направление)
            elif group_number == '' or group_number in Answer.Inverted:
                if group_number in Answer.Inverted:
                    destination = -destination
                if destination == 1:
                    if drift_before < groups_count and drift_before < 1000:
                        drift_for += 20
                        drift_before += 20
                elif destination == -1:
                    if drift_for > 1:
                        drift_for -= 20
                        drift_before -= 20
                continue

            else:
                # Соотносим номер введённой юзером строки с коротким адресом сообщества
                for n in drift_list:
                    if n[0] == group_number:
                        link = n[2]
                        # И переносимся на следующий этап
                        stage2(link)
                continue


# Верхний раздел
def stage0():
    while True:
        # Очищаем экран
        os.system('cls||clear')
        # Выводим индикатор разделов
        mini_m(0)
        # Выводим меню
        print(f' • Введи адрес ВК-сообщества для отображения списка альбомов\n'
              f' • Введи {shine("S", "GOLD")}, чтобы найти группу по названию\n'
              f' • Введи {shine("Q", "GOLD")}, чтобы выйти\n')

        # Получаем от пользователя ссылку или команду
        link = str(input(user_m)).lower()

        # Защита от пустого ввода
        if link == '':
            print(shine('\tНе балуйся!', 'BOLD'))
            time.sleep(0.3)
            stage0()

        # Проверяем на ввод различные команды
        # Например, выход и переход назад по меню
        if link in Answer.Quit:
            quit()
        elif link in Answer.Back or link in Answer.BackBack:
            print(shine('\tДальше отступать некуда!', 'BOLD'))
            time.sleep(1)
            stage0()
        # Или переход в раздел поиска по ключевому слову
        elif link in Answer.Search:
            time.sleep(0.1)
            stage1()
        # И прочее
        elif link == 'египетская сила'.lower():
            egyptian_power = input(user_m)
            while not egyptian_power.isdigit() and egyptian_power != 'None':
                egyptian_power = input(user_m)
                time.sleep(0.1)
                continue

        # Иначе считаем введённое прямой ссылкой и переходим в соответствующий раздел
        else:
            # Переход на следующий этап
            stage2(link)


# Если есть файл с токеном
if os.path.isfile('gvk_config.ini'):
    ini_config = configparser.ConfigParser()
    ini_config.read('gvk_config.ini')
    if 'TOKEN' in ini_config['Settings']:
        TOKEN = ini_config['Settings']['TOKEN']
        if not ('error' in gj_account_get_profile_info()):
            stage0()
        else:
            print('\nВ конфигурационном файле указан неверный токен!')


# Если файла нет, просим ввести токен лично
attempt = 1
print('\nВВЕДИТЕ ТОКЕН ПОЛЬЗОВАТЕЛЯ')
print('* ..либо нажмите ENTER для дополнительной информации')
TOKEN = input('\n>>> ')
time.sleep(0.1)
manual = '\n╔╗ ╔╗ ╔═══╗ ╔╗    ╔═══╗\n' \
'║║ ║║ ║╔══╝ ║║    ║╔═╗║\n' \
'║╚═╝║ ║╚══╗ ║║    ║╚═╝║\n' \
'║╔═╗║ ║╔══╝ ║║ ╔╗ ║╔══╝\n' \
'║║ ║║ ║╚══╗ ║╚═╝║ ║║   \n' \
'╚╝ ╚╝ ╚═══╝ ╚═══╝ ╚╝   \n' \
f'\n\nДля получения {shine("токена", "BOLD")} перейдите по {shine("↓↓ ссылке внизу ↓↓", "BOLD")}, подтвердите разрешения и скопируйте то, что появится' \
            f' в изменившейся адресной строке браузера между {shine("access_token=", "GOLD")} и литерой {shine("&", "GOLD")}' \
            f'\n\nЛибо сформируйте запрос самостоятельно при помощи данного сайта: {shine("https://vkhost.github.io/", "GOLD")}\n\n' \
            f'\n{shine("↓↓↓ТА САМАЯ ССЫЛКА↓↓↓", "BOLD")}\n\n{shine("<ИСПОЛЬЗУЙ МЕТОД ВЫШЕ>", "GOLD")}\n\n\n{shine("...и наконец,", "BOLD")}'

while True:
    if TOKEN == '' or 'error' in gj_account_get_profile_info():
        attempt += 1
        os.system('cls||clear')
        print(manual)
        print('\nВВЕДИТЕ ТОКЕН ПОЛЬЗОВАТЕЛЯ')
        print('\n(Попытка — ' + shine(str(attempt), "GOLD") + ')')
        TOKEN = input('\n>>> ')
        time.sleep(0.1)
        continue
    else:
        time.sleep(0.1)
        break

# Создаём файл с токеном
ini_path = 'gvk_config.ini'
create_config(ini_path, TOKEN)

# Начинаем приключение
stage0()
