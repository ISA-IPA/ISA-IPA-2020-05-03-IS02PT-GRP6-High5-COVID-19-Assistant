from flask import Flask, Response, request, jsonify, g
import json
import sqlite3
from uuid import uuid4
from datetime import datetime, timedelta
from selenium import webdriver
import matplotlib.pyplot as plt


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

driver = webdriver.Chrome('./chromedriver.exe')  # Optional argument, if not specified will search path.
# driver = webdriver.Chrome(options=options, executable_path=r'chromedriver')

stamp = 0
temp = 0
symp = "No"
email = ""
language = []


def get_default_welcome():

    try:
        date = datetime.today().strftime('%Y-%m-%d')
        tmp_list = [date, 'Global']
        rows = query_db("SELECT * from TB_CASE WHERE date_stamp = ? and country_name = ?", tmp_list)
        result = json.loads(rows[0][2])
        total_cases = result["total_cases"]
        total_deaths = result["total_deaths"]
        total_recovered = result["total_recovered"]

        resp = {
            "fulfillment_text": f"Hello, worldwide Covid-19 Status: Total Confirmed Cases: {total_cases}, Total Death Cases: {total_deaths}, and Total Recovered Cases: {total_recovered}"
        }
    except Exception as e:
        print(e)
        resp = {
            "fulfillment_text": "Hello, Welcome to Covid-19 Status Bot!"
        }
    return resp


def update_subscription_in_db():
    try:
        date_stamp = datetime.now()
        language_text = ""
        for lang in language:
            language_text += lang + ","
        language_text = language_text[:-1]
        print("Language: " + language_text)
        tmp_list = [email, date_stamp, language_text]
        update_db("REPLACE INTO SUBSCRIPTION_INFO (to_email, date_stamp, languages) VALUES (?,?,?);", tmp_list)
    except Exception as e:
        print(e)


def get_covid_status_in_country(host, country, date):
    try:
        if date is None:
            date = datetime.today().strftime('%Y-%m-%d')
        elif date == "":
            date = datetime.today().strftime('%Y-%m-%d')
        else:
            date = date[:10]
        print("date: " + str(date))

        host = host

        if country == "United States":
            country = "USA"
        elif country == "United Kingdom":
            country = "UK"
        elif country == "United Arab Emirates":
            country = "UAE"
        elif country == "South Korea":
            country = "S. Korea"
        print("country: " + country)

        tmp_list = [date, country]
        rows = query_db("SELECT * from TB_CASE WHERE date_stamp = ? and country_name Like ?", tmp_list)

        print(rows)
        result = json.loads(rows[0][2])
        total_cases = result["total_cases"]
        total_deaths = result["total_deaths"]
        total_recovered = result["total_recovered"]

        plot_line_chart_by_country(country)

        resp = {
            "fulfillment_messages": [
                {
                    "platform": "SLACK",
                    "card": {
                        "title": f"Overall Covid-19 Status of {country}",
                        "subtitle": f"Total Confirmed Cases: {total_cases}, Total Death Cases: {total_deaths}, and Total Recovered Cases: {total_recovered}",
                        "image_uri": f"https://{host}/static/covid_no_trend_{country}.png"
                    }
                }
            ]
        }
    except Exception as e:
        print(e)
        resp = {
            "fulfillment_text": f"Error happens while checking for {country} Covid-19 Status."
        }
    return resp


def plot_line_chart_by_country(country):
    try:
        threshold = datetime.today() - timedelta(days=5)
        threshold_str = threshold.strftime('%Y-%m-%d')
        print("Threshold: " + str(threshold))

        tmp_list = [country, threshold_str]
        rows = query_db("SELECT * from TB_CASE WHERE country_name = ? AND date_stamp > ? ORDER BY date_stamp ASC", tmp_list)

        date_stamp_list = [(threshold + timedelta(days=1)).strftime('%Y-%m-%d'),
                           (threshold + timedelta(days=2)).strftime('%Y-%m-%d'),
                           (threshold + timedelta(days=3)).strftime('%Y-%m-%d'),
                           (threshold + timedelta(days=4)).strftime('%Y-%m-%d'),
                           (threshold + timedelta(days=5)).strftime('%Y-%m-%d')]
        confirmed_no_list = [0, 0, 0, 0, 0]
        new_no_list = [0, 0, 0, 0, 0]
        death_no_list = [0, 0, 0, 0, 0]

        for row in rows:
            date_stamp = str(row[0])
            if date_stamp in date_stamp_list:
                index = date_stamp_list.index(date_stamp)
                result = json.loads(row[2])
                confirmed_no_list[index] = result["total_cases"]
                new_no_list[index] = result["new_cases"]
                death_no_list[index] = result["total_deaths"]

        plt.plot(date_stamp_list, confirmed_no_list, label="Total Confirmed")
        plt.plot(date_stamp_list, new_no_list, label="New Case")
        plt.plot(date_stamp_list, death_no_list, label="Total Death")
        plt.legend()
        plt.savefig("./static/covid_no_trend_" + country + ".png")
    except Exception as e:
        print(e)
    finally:
        plt.close("all")


def get_news_from_db(host):
    try:
        rows = query_db("SELECT * FROM NEWS_INFO")
        size = len(rows)

        if size > 0:
            resp = {"fulfillment_messages": []}
            for row in rows:
                resp["fulfillment_messages"].append(
                    {
                        "platform": "SLACK",
                        "card": {
                            "title": row[1],
                            "subtitle": "Summary: " + row[3],
                            "image_uri": f"https://{host}/static/who.PNG",
                            "buttons": [
                                {
                                    "text": "Read the article",
                                    "postback": row[2]
                                }
                            ]
                        }
                    }
                )
        else:
            resp = {
                "fulfillment_text": "There's no News available."
            }
        print(resp)
    except Exception as e:
        print(e)
        resp = {
            "fulfillment_text": "Error happens while getting news."
        }
    return resp


def init_upload_temperature():
    try:
        email_info = None
        with open("email_info.json", 'r') as load_f:  # Ask lecturer for this exercise_2/email_info.json file
            email_info = json.load(load_f)

        email_info = email_info['1']

        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        global driver

        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
          """
        })
        driver.get(
            "https://vafs.nus.edu.sg/adfs/oauth2/authorize?response_type=code&client_id=97F0D1CACA7D41DE87538F9362924CCB-184318&resource=sg_edu_nus_oauth&redirect_uri=https%3A%2F%2Fmyaces.nus.edu.sg%3A443%2Fhtd%2Fhtd")

        email = driver.find_element_by_xpath("//input[@id='userNameInput']");

        password = driver.find_element_by_xpath("//input[@id='passwordInput']");

        email.send_keys(email_info['email']);
        password.send_keys(email_info['password']);

        login = driver.find_element_by_id("submitButton");
        login.click()

    except Exception as e:
        print(e)


def trigger_upload_temperature(temp, symp):
    try:
        global driver
        temperature = driver.find_element_by_xpath("//input[@id='temperature']");
        symptom_y = driver.find_element_by_xpath("//input[@value='Y']");
        symptom_n = driver.find_element_by_xpath("//input[@value='N']");

        temperature.send_keys(str(temp))

        if 'y' in symp:
            symptom_y.click();
        else:
            symptom_n.click();

        submit = driver.find_element_by_xpath("//input[@value='Submit']");

        submit.click();

        st = datetime.now()
        global stamp
        stamp = str(st).replace(' ', '_').replace(':', '_').replace('.', '_')

        driver.save_screenshot("./static/nus_temp_screenshot_" + stamp + ".png")

        back = driver.find_element_by_xpath("//input[@value='Back']");

        back.click();

    except Exception as e:
        print(e)


def get_screenshot_from_local(host):
    try:
        resp = {
            "fulfillment_messages": [
                {
                    "platform": "SLACK",
                    "card": {
                        "title": f"The screenshot of your latest upload",
                        "subtitle": f"Your record - Temperature: {temp}, and Symptom: {symp}",
                        "image_uri": f"https://{host}/static/nus_temp_screenshot_{stamp}.png"
                    }
                },
                {
                    "platform": "SLACK",
                    "quick_replies": {
                        "quick_replies": ["Check my records", "Greetings", "News?"]
                    }
                }
            ]
        }
    except Exception as e:
        print(e)
        resp = {
            "fulfillment_text": "Error happens while checking screenshot."
        }
    return resp


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def query_db(query, args=()):
    cur = get_db().cursor()
    cur.execute(query, args)

    rv = cur.fetchall()  # Retrive all rows
    cur.close()
    return rv
    # return (rv[0] if rv else None) if one else rv


def update_db(query, args=(), one=False):
    conn = get_db()
    conn.execute(query, args)
    conn.commit()
    conn.close()
    return "DB updated"


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.after_request
def add_header(response):
    response.headers['Pragma'] = 'no-cache'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Expires'] = '0'
    return response


@app.route("/")  # take note of this decorator syntax, it's a common pattern
def home():
    return "API is up and running..."


@app.route('/update_case', methods=['GET', 'POST'])
def raise_case():
    data = request.json

    date_stamp = data['date_stamp']
    country_name = data['country_name']
    conv_info_str = data['conv_info_str']

    tmp_list = [date_stamp, country_name, conv_info_str]

    update_db("INSERT INTO TB_CASE (date_stamp, country_name, conv_info) VALUES (?,?,?);", tmp_list)

    return "Cases updated with time stamp as " + date_stamp


@app.route('/query_case', methods=['GET', 'POST'])
def search_case():
    date = request.args.get('date')
    search_country = request.args.get('country')

    tmp_list = [date, search_country]

    rows = query_db("SELECT * from TB_CASE WHERE date_stamp = ? and country_name = ?", tmp_list)

    return jsonify(rows)


@app.route('/init', methods=['POST'])
def init_db():
    sql_create_table = """ CREATE TABLE IF NOT EXISTS TB_CASE (
                                          date_stamp text NOT NULL,
                                          country_name text NOT NULL,
                                          conv_info text NOT NULL,  
                                          PRIMARY KEY(date_stamp, country_name)
                                      );"""

    update_db(sql_create_table)
    return "DB created!"


@app.route('/drop_table', methods=['GET', 'POST'])
def drop_table():
    sql_drop_table = """ DROP TABLE IF EXISTS TB_CASE ; """

    update_db(sql_drop_table)
    return "DB dropped!"


@app.route('/create_news', methods=['POST'])
def create_news_db():
    sql_create_table = """ CREATE TABLE IF NOT EXISTS NEWS_INFO (
                                          date_stamp text NOT NULL,
                                          news_title text NOT NULL,
                                          news_link text NOT NULL,
                                          news_summary text NOT NULL,  
                                          PRIMARY KEY(date_stamp, news_title)
                                      );"""

    update_db(sql_create_table)
    return "DB created!"


@app.route('/create_subscription', methods=['POST'])
def create_subscription_db():
    sql_create_table = """ CREATE TABLE IF NOT EXISTS SUBSCRIPTION_INFO (
                                          to_email text NOT NULL,
                                          date_stamp text NOT NULL,
                                          languages text NOT NULL, 
                                          PRIMARY KEY(to_email)
                                      );"""

    update_db(sql_create_table)
    return "DB created!"


@app.route("/main", methods=["POST"])
def main():
    req = request.get_json(silent=True, force=True)
    host = request.host
    intent_name = req["queryResult"]["intent"]["displayName"]
    print(req)

    if intent_name == "Default Welcome Intent":
        resp = get_default_welcome()
    elif intent_name == "CheckCovidStatus":
        country = req["queryResult"]["parameters"]["country"]
        date = req["queryResult"]["parameters"]["date"]
        if country is None or country == "":
            country = "Global"
        resp = get_covid_status_in_country(host, country, date)
    elif intent_name == "PopulateTemperature":
        temp_var = req["queryResult"]["parameters"]["temp"]
        global temp
        temp = temp_var
        resp = {
            "fulfillment_text": f"Your Temperature: {temp} is recorded. Do you have any symptom?"
        }
    elif intent_name == "PopulateSymptom":
        symp_var = req["queryResult"]["parameters"]["symp"]
        global symp
        symp = symp_var

        trigger_upload_temperature(temp, symp)
        resp = {
            "fulfillment_messages": [
                {
                    "platform": "SLACK",
                    "quick_replies": {
                        "title": "Your record have been successfully uploaded.",
                        "quick_replies": ["Check my records", "Greetings", "News?"]
                    }
                }
            ]
        }
    elif intent_name == "CheckRecord":
        resp = get_screenshot_from_local(host)
    elif intent_name == "RetrieveNews":
        resp = get_news_from_db(host)
    elif intent_name == "PopulateEmailAddress":
        email_var = req["queryResult"]["parameters"]["email"]
        global email
        email = email_var
        resp = {
            "fulfillment_text": f"Your Email Address: {email} is recorded. "
                                f"What's your preferred languages? If multiple languages preferred, please use "
                                f"comma - ',' to separate them: English, Chinese"
        }
    elif intent_name == "PopulateLanguagesList":
        language_var = req["queryResult"]["parameters"]["language"]
        global language
        language = language_var
        update_subscription_in_db()
        resp = {
            "fulfillment_text": f"Your subscription has been successfully updated. "
        }
    else:
        resp = {
            "fulfillment_text": "Unable to find a matching intent. Try again."
        }

    return Response(json.dumps(resp), status=200, content_type="application/json")


if __name__ == '__main__':
    DATABASE = "./db/demo.db"

    # Generate a globally unique address for this node
    node_identifier = str(uuid4()).replace('-', '')

    init_upload_temperature()

    print(node_identifier)
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5001, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port, debug=True)
