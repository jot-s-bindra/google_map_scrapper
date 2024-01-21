from flask import Flask, jsonify
from selenium import webdriver
from bs4 import BeautifulSoup
import time

from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
import urllib.parse



app = Flask(__name__)


@app.route('/scrap/<position>/<city>/<count>', methods=['GET'])
def scrap(position, city, count):
    count = int(count)
    print('count', count)
    search_query = position + ' ' + ' in ' + ' ' + city
    search_query_encoded = urllib.parse.quote(
        search_query)  # Encode the search query for the URL

    link = f"https://www.google.com/maps/search/{search_query_encoded}/"
    print(link)

    browser = webdriver.Chrome()

    start_time = time.time()
    time.sleep(1)
    browser.get(str(link))
    time.sleep(3)
    action = ActionChains(browser)
    a = browser.find_elements(By.CLASS_NAME, "hfpxzc")
    prev = len(a)
    while len(a) < count:
        print(len(a))
        var = len(a)
        scroll_origin = ScrollOrigin.from_element(a[len(a)-1])
        time.sleep(0.4)
        action.scroll_from_origin(scroll_origin, 0, 1500).perform()
        # time.sleep(2)
        a = browser.find_elements(By.CLASS_NAME, "hfpxzc")
        if (len(a) == prev):
            time.sleep(1)
            scroll_origin = ScrollOrigin.from_element(a[len(a)-1])
            action.scroll_from_origin(scroll_origin, 0, 1500).perform()
            a = browser.find_elements(By.CLASS_NAME, "hfpxzc")
            if (len(a) >= (count*0.9)):
                break

        if (time.time()-start_time > 100):
            print("Timout limit reached")
            break
        prev = len(a)

    source = browser.page_source
    soup = BeautifulSoup(source, 'html.parser')
    elements_list = soup.find_all("div", class_="Nv2PK")

    output = []
    for ele in elements_list:
        try:
            name = ele.find("a", class_='hfpxzc')['aria-label']
            phone = ele.find("span", class_='UsdlK').text
        except:
            print("Error")
        try:
            url = ele.find("a", class_='lcr4fd')['href']
        except:
            url = ""
        try:
            adress = ele.find_all("div", class_='W4Efsd')[1].find(
                "div", class_='W4Efsd').find_all('span')[2].text[7:]
        except:
            adress = ""
        try:
            rating = (ele.find("span", class_='ZkP5Je')
                      ['aria-label'].split()[0])
        except:
            rating = ""

        data_dict = {
            "Name": name,
            "Phone": phone,
            "Address": adress,
            "Website": url,
            "rating": rating
        }

        output.append(data_dict)

    return jsonify(output)


if __name__ == '__main__':
    app.run(debug=True, port=5551)
