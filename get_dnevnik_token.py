# -*- coding: utf-8 -*-
from selenium import webdriver
import time

browser = webdriver.Chrome()
browser.get("https://dnevnik2.petersburgedu.ru/students/my")

go = input("Залогинтесь на портале, и нажмите Enter")

print("получаем cookie")
cookies = browser.get_cookies()


for cookie in cookies:
    if cookie['name'] == 'X-JWT-Token':
        print(cookie['value'])
        browser.quit()

print('Cookie не найдено')
browser.quit()
