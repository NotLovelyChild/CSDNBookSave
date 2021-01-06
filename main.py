import pdfkit
from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import json

chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')
user_agent = "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
chrome_options.add_argument(user_agent)
chrome_options.add_argument('lang=zh_CN.UTF-8')
driver = webdriver.Chrome(options=chrome_options)


def save(content, path):
    path_wk = r'./wkhtmltopdf'
    config = pdfkit.configuration(wkhtmltopdf=path_wk)
    pdfkit.from_string(content, path, configuration=config)


def checkLogin(soup):
    header = soup.select(".toolbar-btn.toolbar-btn-login.csdn-toolbar-fl ")
    if len(header):
        if header[0].text.replace("\n", "") == "登录/注册":
            addCooks()
            return False
        else:
            return True


def gotoLogin():
    driver.find_element_by_class_name("toolbar-btn.toolbar-btn-login.csdn-toolbar-fl ").click()
    sleep(10)
    driver.get("https://book.csdn.net")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    if checkLogin(soup):
        saveCooks(driver.get_cookies())
        return driver.get_cookies()
    else:
        gotoLogin()


def saveCooks(cooks):
    with open('cooks.json', 'w') as file_obj:
        json.dump(cooks, file_obj)
        print("写入json文件：")
        file_obj.close


def addCooks():
    driver.delete_all_cookies()
    data = []
    try:
        with open('cooks.json', 'r') as file_obj:
            data = json.load(file_obj)
            file_obj.close
    except IOError:
        print('IO error')

    for cookie in data:
        driver.add_cookie(cookie)
    driver.refresh()
    sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    checkLogin(soup)


if __name__ == '__main__':
    chrome_options.add_argument('lang=zh_CN.UTF-8')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://book.csdn.net")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    if not checkLogin(soup):
        gotoLogin()
    # print(soup)
    # driver.quit()
