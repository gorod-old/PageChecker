# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import json
import math
import os
import threading
import winsound
from random import uniform, choice
from time import sleep, perf_counter

import requests
from bs4 import BeautifulSoup as BS

parser = None
app_window = None
host = 'http://www.rustools.ru/catalog/category209/product103495'
ajax_params = {}
user_agents_list = []
proxies_list = []
not_parse = []
encoding = 'utf-8'


def beep():
    frequency = 2500  # Set Frequency To 2500 Hertz
    duration = 500  # Set Duration To 1000 ms == 1 second
    winsound.Beep(frequency, duration)


def time_str(num):
    if num < 10:
        return '0' + str(num)
    return str(num)


def get_time(sec):
    hour_ = math.trunc(sec / 3600)
    min_ = math.trunc(sec % 3600 / 60)
    sec_ = math.trunc(sec % 3600 % 60)
    return time_str(hour_) + ':' + time_str(min_) + ':' + time_str(sec_)


def get_user_agents_list():
    ua_list = open('user-agents.txt').read().strip().split('\n')
    for ua in ua_list:
        if len(ua) == 0:
            ua_list.remove(ua)
    return ua_list


def get_proxies_list():
    p_list = open('proxies.txt').read().strip().split('\n')
    for p in p_list:
        if len(p) == 0:
            p_list.remove(p)
    return p_list


def save_html(html_str):
    html = open("page.html", "w", encoding=encoding)
    html.seek(0)
    html.write(html_str)
    html.close()


def write_json(json_data):
    root = os.getcwd() + '/result data'
    if not os.path.isdir(root):
        os.mkdir(root)
    path = os.getcwd() + '/result data/result.json'
    if os.path.exists(path):
        os.remove(path)
    with open(path, 'a', encoding='utf-8') as file:
        json.dump(json_data, file, indent=4, ensure_ascii=False)


def get_request_data(url):
    data = None
    # 10 попыток запросов на сервер с временной отсрочкой сменой ip и user-agent
    for i in range(10):
        timeout = uniform(3, 6)
        sleep(timeout)
        prx = None
        if app_window and app_window.proxy and len(proxies_list) > 0:
            _proxy = choice(proxies_list)
            prx = {
                'http': 'http://' + _proxy,
                'https': 'https://' + _proxy,
            }
        user_agent = {
            'user-agent': choice(user_agents_list),
            'accept': '*/*'
        }
        try:
            data = request_data(url, user_agent, prx)
        finally:
            if data is not None and data.status_code == 200:
                break

    if data is None:
        not_parse.append(url)
    else:
        data.encoding = encoding
    return data


def set_variables():
    global user_agents_list, proxies_list, app_window
    if os.path.exists(os.getcwd() + '/user-agents.txt'):
        print('user-agents.txt - is found')
        user_agents_list = get_user_agents_list()
    if os.path.exists(os.getcwd() + '/proxies.txt'):
        print('proxies.txt - is found')
        proxies_list = get_proxies_list()
    if app_window and len(proxies_list) == 0:
        app_window.proxy_off()


def request_data(url, headers=None, proxies=None, params=None):
    r = requests.get(url, headers=headers, proxies=proxies, params=params)
    return r


def get_page():
    print(host)
    data = get_request_data(host)
    soup = BS(data.text, 'html.parser')
    cat_list = soup.select('div.path a')
    for cat in cat_list:
        print(cat.text.strip())
    save_html(soup.prettify())


class AsyncProcess:
    def __init__(self, name, function, stream_num, callback, args=()):
        super(AsyncProcess, self).__init__()

        self.stream_list = []
        self.start_time = perf_counter()
        print('process: "', name, '", start time: ', self.start_time)
        self.name = name
        self.stream_num = stream_num
        self.callback = callback
        for num in range(stream_num):
            args_ = args
            if stream_num > 1:
                args_ = args + (num + 1,)  # добавляем номер процесса
            self.stream_list.append(threading.Thread(target=function, args=args_))
            self.stream_list[num].start()
            sleep(1)
        t = threading.Thread(target=self.waiting_for_process_end, args=())
        t.start()

    def waiting_for_process_end(self):
        for num in range(self.stream_num):
            self.stream_list[num].join()
        ov_time = perf_counter() - self.start_time
        print('process: "', self.name, '", end time: ', perf_counter())
        print('process: "', self.name, '" - completed, total time: ', get_time(ov_time), ' sec')
        if parser and self.callback:
            class_method = getattr(TestParser, self.callback)
            class_method(parser)


class TestParser:
    def __init__(self, urls_, search_):
        super(TestParser, self).__init__()
        self.pars_data = []
        self.process = None
        self.urls = urls_
        self.search_data = search_
        self.cpu_count = os.cpu_count()

    def start(self):
        if self.process:
            return
        self.process = AsyncProcess('pars data', self.async_pars, self.cpu_count, 'end')

    def end(self):
        write_json(self.pars_data)

    def async_pars(self, num):
        while num - 1 < len(self.urls):
            data = get_request_data(self.urls[num - 1])
            if data is not None:
                soup = BS(data.text, 'html.parser')
                save_html(soup.prettify())
                pars_data = {}
                for key in self.search_data.keys():
                    try:
                        el_text = soup.select(self.search_data[key])[0].text.strip()
                        pars_data.update({key: el_text})
                    except Exception as e:
                        print(str(e))
                if len(pars_data) > 0:
                    self.pars_data.append(pars_data)
            num += self.cpu_count


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    urls = [
        'https://hidemy.name/ru/proxy-list/?start=0#list',
    ]
    search_data = {
        'ip': 'div.table_block table tbody tr td:nth-child(1)',
        'port': 'div.table_block table tbody tr td:nth-child(2)',
    }
    set_variables()
    parser = TestParser(urls, search_data)
    parser.start()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
