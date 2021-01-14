import pdfkit
from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import json
import os
import threading

chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')
user_agent = "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
chrome_options.add_argument(user_agent)
chrome_options.add_argument('lang=zh_CN.UTF-8')
driver = webdriver.Chrome(options=chrome_options)


class pdfThread(threading.Thread):
    def __init__(self, content, path):
        threading.Thread.__init__(self)
        self.content = content
        self.path = path

    def run(self) -> None:
        path_wk = r'./wkhtmltopdf'
        config = pdfkit.configuration(wkhtmltopdf=path_wk)
        result = pdfkit.from_string("<meta charset='utf-8'>%s" % self.content, self.path, configuration=config)
        if result:
            print("%s 保存成功" % self.path)
        else:
            print("%s 保存失败" % self.path)


def save(content, path):
    p_thread = pdfThread(content, path.replace("html", "pdf"))
    print("开始执行保存命令")
    print(path)
    with open(path, 'w') as file_obj:
        file_obj.write(content)
        print("保存Html成功")
        file_obj.close()
        p_thread.start()


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
        return True
    else:
        gotoLogin()


def saveCooks(cooks):
    with open('cooks.json', 'w') as file_obj:
        json.dump(cooks, file_obj)
        file_obj.close()


def addCooks():
    driver.delete_all_cookies()
    data = []
    try:
        with open('cooks.json', 'r') as file_obj:
            data = json.load(file_obj)
            file_obj.close()
    except IOError:
        print('IO error')

    for cookie in data:
        driver.add_cookie(cookie)
    driver.refresh()
    sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    checkLogin(soup)


def getBookList():
    tags = driver.find_elements_by_class_name("category-item")
    tagsData = []
    for tag in tags:
        if tag.text == "分类" or tag.text == "编辑推荐内容":
            continue
        tag.click()
        tagname = tag.text
        sleep(5)
        while True:
            sleep(0.5)
            driver.execute_script('window.scrollBy(0,100)')
            extra = driver.find_element_by_class_name("extra-info").find_element_by_class_name("text-align-center")
            print(extra.is_displayed())
            if extra.is_displayed():
                break

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        booklist = soup.select(".category-book-item")
        books = []
        for book in booklist:
            bookData = {}
            a = book.select('a')
            if len(a):
                href = a[0]['href']
                bookData['href'] = href

            name = book.select('.book-title')
            if len(name):
                bookName = name[0].text
                bookData['bookName'] = bookName

            bookdesc = book.select('.book-desc')
            if len(bookdesc):
                desc = bookdesc[0].text
                bookData['desc'] = desc

            bookauthor = book.select('.book-author')
            if len(bookauthor):
                author = bookauthor[0].text
                bookData['author'] = author

            print(bookData)
            books.append(bookData)

        tagsData.append({
            'tagName': tagname,
            'bookData': books
        })

    with open('books.json', 'w') as file_obj:
        json.dump(tagsData, file_obj)
        print("保存书本数据")
        file_obj.close()


def downloadBook(bookUrl, bookName, bookAuthor, bookDesc, tagName):
    # 文件夹检测
    path = "/Volumes/J/PDFs/%s" % tagName
    if not os.path.exists(path):
        os.makedirs(path)
        # 判断本地是否已经下载过
    # savePath = "%s/%s.pdf" % (path, bookName)
    savePath = "%s/%s.html" % (path, bookName.replace("/","_"))
    if os.path.exists(savePath):
        print("%s 已存在" % bookName)
        return
    # 开始加载书本
    book = ""
    book += ("<h1>%s</h1>" % bookName)
    book += ("<h2>%s</h2>" % bookAuthor)
    book += ("<h3>%s</h3>" % bookDesc)
    driver.get(bookUrl)
    driver.find_element_by_class_name("csdn-buttom-red-default").click()
    sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    index = soup.select(".popup-info")
    # 目录
    if len(index):
        book += str(index[0])

    # 跳转第一章
    bookID = bookUrl.split('/')[-1]
    driver.get("https://book.csdn.net/book/%s/chapter/1" % bookID)

    # 抓取每一章
    while True:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        bookContent = soup.select(".ebook-chapter-content")
        if len(bookContent):
            book += str(bookContent[0])
        nextButton = driver.find_element_by_class_name("next")
        if nextButton.text == "下一页":
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            sleep(1)
            nextButton.click()
            sleep(4)
            saveCooks(driver.get_cookies())
        else:
            break

    save(book, savePath)


if __name__ == '__main__':
    data = []
    driver.get("https://book.csdn.net")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    if not checkLogin(soup):
        if gotoLogin():
            # 只需要运行一次
            # getBookList()
            try:
                with open('books.json', 'r') as file_obj:
                    data = json.load(file_obj)
                    file_obj.close()
            except IOError:
                print('IO error')

            for tag in data:
                print(tag['tagName'])
                for book in tag["bookData"]:
                    print(book['bookName'])
                    downloadBook(book['href'], book['bookName'], book['author'], book['desc'], tag['tagName'])

    print("内容抓取完毕")
    sleep(10 * 60)
