import tagui as t
import pandas as pd
import numpy as np
import datetime
import pytz
import json
import requests
import sqlite3

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
    data = {}
    region_detail = {}

    date_stamp = datetime.datetime.now(pytz.timezone('Singapore')).strftime('%Y-%m-%d')

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
    print(status)


crawl_covid_data()

