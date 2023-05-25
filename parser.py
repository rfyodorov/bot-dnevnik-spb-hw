import json
import datetime as dt
from datetime import timedelta, datetime
import pathlib
from urllib.parse import urljoin
import requests
from requests.cookies import RequestsCookieJar
import logging


def run_parser(day='tommorow') -> str:
    """
    Определяем дату, за которую требуется получить данные.
    Используем вспомогательные функции: parser_person(), parser_homework(), parser_schedule()
    """

    # определяем дату для запроса
    if day == 'today':
        target_day = dt.date.today()
        ''' если завтра СБ или ВС, то выбираем ПН'''
        if target_day.isoweekday() == 6:
            target_day += timedelta(days=2)
        elif target_day.isoweekday() == 7:
            target_day += timedelta(days=1)
        get_day = target_day
    elif day == 'tommorow':  # завтра
        target_day = dt.date.today() + timedelta(days=1)
        ''' если завтра СБ или ВС, то выбираем ПН'''
        if target_day.isoweekday() == 6:
            target_day += timedelta(days=2)
        elif target_day.isoweekday() == 7:
            target_day += timedelta(days=1)
        get_day = target_day
    elif day == 'tommorow2':  # послезавтра
        target_day = dt.date.today() + timedelta(days=2)
        ''' если послезавтра СБ или ВС, то выбираем ПН'''
        if target_day.isoweekday() == 6:
            target_day += timedelta(days=2)
        elif target_day.isoweekday() == 7:
            target_day += timedelta(days=1)
        get_day = target_day
    else:
        try:
            get_day = datetime.strptime(day, '%Y-%m-%d').date()
        except ValueError:
            return 'Дата задана не правильно.\nПример: /date 2023-05-18'

    # запрашиваем базовые данные ученика
    try:
        school_id, school, school_class, education_id, group_id, hash_uid = parser_person()
        schoolboy_desc = {'school_id': school_id,
                          'school': school,
                          'school_class': school_class,
                          'education_id': education_id,
                          'group_id': group_id,
                          'hash_uid': hash_uid}
    except ValueError:
        return 'Ошибка подключения серверу API.\nПопробуйте повторить запрос позже.'

    # узнаем расписание уроков и ДЗ
    homeworks = parser_homework(get_day, schoolboy_desc)
    schedule = parser_schedule(get_day, schoolboy_desc)

    output = '<b><u> Домашнее задание на ' + str(get_day) + "</u></b>\n\n"
    for key in schedule:
        if key in homeworks:
            if len(homeworks[key][1]):
                output += homeworks[key][0] + ": " + homeworks[key][1] + "\n\n"

    return output


def run_parser_wallet() -> str:
    # запрашиваем базовые данные ученика
    try:
        school_id, school, school_class, education_id, group_id, hash_uid = parser_person()
        schoolboy_desc = {'school_id': school_id,
                          'school': school,
                          'school_class': school_class,
                          'education_id': education_id,
                          'group_id': group_id,
                          'hash_uid': hash_uid}
    except ValueError:
        return 'Ошибка подключения серверу API.\nПопробуйте повторить запрос позже.'

    output = wallet(schoolboy_desc)

    return str(output)


def run_parser_teacher() -> str:
    # запрашиваем базовые данные ученика
    try:
        school_id, school, school_class, education_id, group_id, hash_uid = parser_person()
        schoolboy_desc = {'school_id': school_id,
                          'school': school,
                          'school_class': school_class,
                          'education_id': education_id,
                          'group_id': group_id,
                          'hash_uid': hash_uid}
    except ValueError:
        return 'Ошибка подключения серверу API.\nПопробуйте повторить запрос позже.'

    output = parser_teacher(schoolboy_desc)

    return str(output)


def parser_homework(get_day, schoolboy_desc: dict) -> dict:
    """получаем id и назнание предмета с ДЗ"""
    day_start = get_day - timedelta(days=5)
    day_end = get_day

    # создаем параметры для запроса (все что идет после url)
    params = {
        'p_educations[]': str(schoolboy_desc['education_id']),
        'p_limit': '100',
        'p_datetime_from': str(day_start),
        'p_datetime_to': str(day_end),
        'p_page': '1',
    }

    data_json = connector_api('lesson', params)

    output = {}
    data = data_json['data']['items']
    for lesson in data:
        tasks = lesson['tasks']
        if tasks:
            homework = tasks[0]['task_name']
        else:
            homework = ""
        output[lesson['subject_id']] = (lesson['subject_name'], homework)

    logging.debug('Домашнее задание на ' + str(get_day))
    logging.debug(output)
    return output


def parser_schedule(get_day, schoolboy_desc: dict) -> dict:
    """получаем расписание уроков в заданный день, id и назнание предмета"""

    # создаем параметры для запроса (все что идет после url)
    params = {
        'p_educations[]': str(schoolboy_desc['education_id']),
        'p_limit': '100',
        'p_datetime_from': str(get_day),
        'p_datetime_to': str(get_day),
        'p_page': '1',
    }

    data_json = connector_api('schedule', params)

    output = {}
    data = data_json['data']['items']
    for lesson in data:
        output[lesson['subject_id']] = (lesson['number'], lesson['subject_name'])

    logging.debug('* Расписание уроков на ' + str(get_day))
    logging.debug(output)
    return output


def wallet(schoolboy_desc: dict) -> dict:
    """получаем расписание уроков в заданный день, id и назнание предмета"""

    # создаем параметры для запроса (все что идет после url)
    # params = {
    #     'p_educations[]': str(schoolboy_desc['education_id']),
    #     'p_limit': '100',
    #     'p_datetime_from': str(get_day),
    #     'p_datetime_to': str(get_day),
    #     'p_page': '1',
    # }
    params = {'RegId': str(schoolboy_desc['hash_uid'])}

    data_json = connector_api('wallet', params)

    account_type = {}
    output = "<b><u>Баланс</u></b>\n\n"
    data = data_json['accounts']
    for account in data:
        output += account['accounttypename'] + ' :' + account['sum'] + '\n'
        account_type[account['accounttypeid']] = account['accounttypename']

    output += "\n<code>"
    data_json = connector_api('wallet_avg', params)
    data = data_json['average']
    for item in data:
        type_id = item['accounttypeid ']
        output += account_type[type_id] + '\n'
        output += 'Среднее в день: ' + item['averagesum']
        output += ' (сумма ' + item['sum'] + ' за ' + item['daycount'] + ' дней)\n\n'

    output += "</code>"

    logging.debug('* Кошелёк')
    logging.debug(output)
    return output


def parser_teacher(schoolboy_desc: dict) -> str:
    # создаем параметры для запроса (все что идет после url)
    params = {
        'p_educations[]': str(schoolboy_desc['education_id']),
        'p_page': '1'
    }

    data_json = connector_api('teacher', params)

    output = ""
    data = data_json['data']['items']
    for teacher in data:
        output += f'<b>{teacher["surname"]} {teacher["firstname"]} {teacher["middlename"]}</b>\n'
        output += f'<b><i>{teacher["position_name"]}</i></b>\n'
        output += '<code>'
        for subject in teacher['subjects']:
            output += subject["name"] + '\n'
        output += '</code>\n'

    logging.debug('Учителя:')
    logging.debug(output)
    return output


def parser_person():
    """получаем базовые сведения об ученике (нужен education_id)"""

    params = {}
    data_json = connector_api('person', params)

    data = data_json['data']['items'][0]['educations'][0]
    school_id = data['institution_id']
    school = data['institution_name']
    school_class = data['group_name']
    education_id = data['education_id']
    group_id = data['group_id']
    hash_uid = data_json['data']['items'][0]['hash_uid']
    return school_id, school, school_class, education_id, group_id, hash_uid


def connector_api(path_name: str, params: dict) -> dict:
    """
    подключемся к api сервера, получаем от json
    требуется иметь валидную cookie
    """

    # базовые переменные
    conf_vars = read_config()
    base_url = conf_vars['base_url']

    path = get_link(path_name)
    url = urljoin(base_url, path)
    logging.info(path)
    logging.info(f'URL: {url}')

    session = requests.Session()
    # Создаем cookie для аутентификации
    cookies_jar = make_cookie()
    session.cookies.update(cookies_jar)

    # логирование
    params_str = '?'
    for key, value in params.items():
        params_str = params_str + key + "=" + value + ","
    logging.info(f'Parameters: {params_str[:-1]}')

    # пробуем открыть подключение (для wallet нужен POST)
    if path_name == 'wallet' or path_name == 'wallet_avg':
        hash_token = cookies_jar.get('X-JWT-Token')
        headers = {'X-JWT-Token': hash_token}
        try:
            res = requests.post(url, params, headers=headers)
        except requests.exceptions.SSLError:
            logging.error(f'Не могу подключються к серверу {base_url}')
            return {}
    else:
        try:
            res = session.get(url, params=params)
        except requests.exceptions.SSLError:
            logging.error(f'Не могу подключються к серверу {base_url}')
            return {}

        if res.status_code == 401:
            logging.error(f'Ошибка авторизации на dnevnik2 (HTTP={res.status_code} Проверьте срок действия cookie)')
            return {}
        elif res.status_code != 200:
            logging.error(f'Невозможно получить данные от dnevnik2 (HTTP={res.status_code})')
            return {}

    logging.info(f'HTTP response: {res.status_code}')

    return res.json()


def read_config() -> dict:
    """чтение всех параметров конфигурации из файла"""
    folder_path = pathlib.Path(__file__).parent.absolute()
    global_path = folder_path.joinpath('config.json')
    with open(global_path, "r") as config_file:
        conf_vars = json.load(config_file)
    return conf_vars


def make_cookie():
    """создаём cookie (читаем из файла), необходимые для авторизации"""
    cookies_path = pathlib.Path(__file__).parent.absolute()
    cookies_path = cookies_path.joinpath('cookies.json')

    if not cookies_path.exists():
        raise ValueError(f"file {cookies_path} doesn't exist")
    # else:
    #     logging.debug('("Used: ",cookies_path)

    with cookies_path.open('r', encoding='utf-8') as cookies_file:
        cookies = json.load(cookies_file)

    cookies_jar = RequestsCookieJar()
    for item in cookies:
        cookies_jar.set(**item)

    return cookies_jar


def get_link(target_name: str) -> str:
    """url для скрытого api"""
    dnevnik_links = {
        'person': '/api/journal/person/related-child-list',
        'schedule': '/api/journal/schedule/list-by-education',
        'lesson': '/api/journal/lesson/list-by-education',
        'wallet': '/fps/api/netrika/mobile/v1/accounts/',
        'wallet_avg': 'fps/api/netrika/mobile/v1/average/',
        'teacher': '/api/journal/teacher/list',
        'score': '/api/group/group/get-list-period'
    }
    if target_name in dnevnik_links:
        return dnevnik_links[target_name]
    else:
        return ""
