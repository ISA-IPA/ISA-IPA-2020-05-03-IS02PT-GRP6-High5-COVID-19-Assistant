import tagui as t
from selenium import webdriver
import imgkit
import time


def wait_for_pageload(selector):
    wait_status = 0
    for loop_wait in range(1, 60):
        print(f"{loop_wait}. waiting for page to appear. wait for 1s...")
        if t.present(selector):
            wait_status = 1
            break
        else:
            t.wait(1)
    print("Covid wait_status = {}".format(wait_status))

t.init()

t.url('https://www.worldometers.info/coronavirus/')

wait_for_pageload('//div[@class="maincounter-number"]')
num_country = int(t.count('(//a[@class="mt_a"])')/2)

print("Number of Countries found: " + str(num_country))

country_list = []
link_list = []

for n in range(1, num_country+1):
    try:
        country_row_xpath = f'(//a[@class="mt_a"])[{n}]'
        country_link_xpath = country_row_xpath + '/@href'
        country_link = 'https://www.worldometers.info/coronavirus/' + t.read(country_link_xpath)
        link_list.append(country_link)
        country_name = t.read(country_row_xpath)
        country_list.append(country_name)
        print(f"Link got for country: {country_name}")
    except Exception as e:
        print(f"Exception: {e} happen. Skipping")

t.close()
driver = webdriver.Chrome('./chromedriver')

options_country = {
    'format': 'png',
    'crop-h': '950',
    'crop-w': '700',
    'crop-x': '0',
    'crop-y': '0',
    'encoding': "UTF-8"
}

path_wkthmltoimage = r'D:\wkhtmltopdf\bin\wkhtmltoimage.exe'
config = imgkit.config(wkhtmltoimage=path_wkthmltoimage)

for n in range(num_country):
    try:
        print("Link: " + link_list[n] + ", Country Name: " + country_list[n])
        driver.get(link_list[n])
        time.sleep(3)
        country_case_chart = '//h3[contains(text(),"Total Coronavirus Cases in")]/..'
        country_case_chart_element = driver.find_element_by_xpath(country_case_chart).get_attribute('innerHTML')
        imgkit.from_string(country_case_chart_element, f'./static/trend/{country_list[n]}.png', options=options_country, config=config)
    except Exception as e:
        print(f"Exception: {e} happen. Skipping")
        driver.close()  # Occasionally, seesion might get closed by remote server.
        driver = webdriver.Chrome('./chromedriver')  # Closing web driver and starting a new session.

driver.close()
