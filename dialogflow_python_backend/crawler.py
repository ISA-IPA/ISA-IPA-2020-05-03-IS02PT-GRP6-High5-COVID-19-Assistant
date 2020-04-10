import datetime
import json
import sqlite3

import pytz
import tagui as t

t.init()


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


def insert_db(json_data):
    # url = 'http://0.0.0.0:5001/raise_case'
    # headers = {"Accept": "application/json"}
    # response = requests.get(url, headers = headers, data=json_data)

    DATABASE = "./db/demo.db"
    db = sqlite3.connect(DATABASE)

    date_stamp = json_data['date_stamp']
    country_name = json_data['country_name']
    conv_info_str = json_data['conv_info_str']

    tmp_list = [date_stamp, country_name, conv_info_str]

    query = "INSERT INTO TB_CASE (date_stamp, country_name, conv_info) VALUES (?,?,?);"

    db.execute(query, tmp_list)
    db.commit()
    db.close()
    return 'OK'


def crawl_covid_data():
    date_stamp = datetime.datetime.now(pytz.timezone('Singapore')).strftime('%Y-%m-%d')

    status = extract_global(date_stamp)
    print(status)
    # all countries
    status = extract_all_countries(date_stamp, status)
    print(status)


def extract_all_countries(date_stamp, status):
    num_country = int(t.count('(//a[@class="mt_a"])') / 2)  # first half is for today, second half is for yesterday
    for n in range(1, num_country + 1):
        data = {}
        region_detail = {}
        data['date_stamp'] = date_stamp
        country_row_xpath = f'(//a[@class="mt_a"])[{n}]'

        country_total_cases_xpath = country_row_xpath + '/../following-sibling::td[1]'
        country_new_cases_xpath = country_row_xpath + '/../following-sibling::td[2]'
        country_total_deaths_xpath = country_row_xpath + '/../following-sibling::td[3]'
        country_new_deaths_xpath = country_row_xpath + '/../following-sibling::td[4]'
        country_total_recovered_xpath = country_row_xpath + '/../following-sibling::td[5]'
        country_active_cases_xpath = country_row_xpath + '/../following-sibling::td[6]'
        country_serious_cases_xpath = country_row_xpath + '/../following-sibling::td[7]'

        region_detail['total_cases'] = convert_extracted_numbers(t.read(country_total_cases_xpath))
        region_detail['new_cases'] = convert_extracted_numbers(t.read(country_new_cases_xpath))
        region_detail['total_deaths'] = convert_extracted_numbers(t.read(country_total_deaths_xpath))
        region_detail['new_deaths'] = convert_extracted_numbers(t.read(country_new_deaths_xpath))
        region_detail['total_recovered'] = convert_extracted_numbers(t.read(country_total_recovered_xpath))
        region_detail['active_cases'] = convert_extracted_numbers(t.read(country_active_cases_xpath))
        region_detail['serious_cases'] = convert_extracted_numbers(t.read(country_serious_cases_xpath))

        conv_info_str = json.dumps(region_detail)
        data['conv_info_str'] = conv_info_str

        country_name = t.read(country_row_xpath)
        data['country_name'] = country_name

        status = insert_db(data)
    return status


def extract_global(date_stamp):
    data = {}
    region_detail = {}
    data['date_stamp'] = date_stamp
    # World data
    data['country_name'] = 'Global'
    t.url('https://www.worldometers.info/coronavirus/')
    wait_for_pageload('//div[@class="maincounter-number"]')
    global_case = t.read('(//div[@class="maincounter-number"])[1]/span')
    global_death = t.read('(//div[@class="maincounter-number"])[2]/span')
    global_recovered = t.read('(//div[@class="maincounter-number"])[3]/span')
    region_detail['total_cases'] = int(global_case.replace(',', ''))
    region_detail['total_deaths'] = int(global_death.replace(',', ''))
    region_detail['total_recovered'] = int(global_recovered.replace(',', ''))
    conv_info_str = json.dumps(region_detail)
    data['conv_info_str'] = conv_info_str
    status = insert_db(data)
    return status


def convert_extracted_numbers(raw_value):
    try:
        result = int(raw_value.strip().replace('+', '').replace(',', ''))
    except Exception as e:
        print('Exception happened for ' + raw_value)
        result = 0
    return result


crawl_covid_data()
