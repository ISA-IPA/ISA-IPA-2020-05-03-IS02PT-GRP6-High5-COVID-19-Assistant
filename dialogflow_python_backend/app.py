from flask import Flask, Response, request, jsonify, g
import json
import sqlite3
from uuid import uuid4
import pytz
import datetime

app = Flask(__name__)


def get_covid_status_in_country(host, country, date):
    country = country
    status = "Severe"
    date = date
    host = host

    # TO-DO: Tagui to store Covid-19 data Image at: folder "static" with name "Overall.PNG", "New.PNG" and "Death.PNG"
    overall = "Overall.PNG"
    new = "New.PNG"
    death = "Death.PNG"

    resp = {
        "fulfillment_messages": [
            {
                "platform": "SLACK",
                "card": {
                    "title": f"Overall Covid-19 Status of {country}",
                    "image_uri": f"https://{host}/static/{overall}",
                    "buttons": [
                        {
                            "text": "New Cases",
                            "postback": f"https://{host}/static/{new}"
                        },
                        {
                            "text": "Death Cases",
                            "postback": f"https://{host}/static/{death}"
                        }
                    ]
                }
            }
        ]
    }

    return resp


def upload_temperature_to_website(host, temp):
    temperature = temp

    # TO-DO: Tagui to store Temperature Image at: folder "static" with name "temperature.jpg"
    resp_text = f"Your tempurature {temperature} is successfully uploaded."
    image_name = "temperature.jpg"

    resp = {
        "fulfillment_messages": [
            {
                "platform": "SLACK",
                "card": {
                    "title": resp_text,
                    "image_uri": f"https://{host}/static/{image_name}"
                }
            }
        ]
    }
    return resp


def redirect_to_website():
    resp = {
        "fulfillment_messages": [
            {
                "platform": "SLACK",
                "card": {
                    "title": "Today's News Available at:",
                    "buttons": [
                        {
                            "text": "Singapore MOH",
                            "postback": "https://www.moh.gov.sg/covid-19"
                        },
                        {
                            "text": "WHO Website",
                            "postback": "https://www.who.int/emergencies/diseases/novel-coronavirus-2019/situation-reports"
                        }
                    ]
                }
            }
        ]
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
                                      ); """

    update_db(sql_create_table)
    return "DB created!"


@app.route('/drop_table', methods=['GET', 'POST'])
def drop_table():
    sql_drop_table = """ DROP TABLE IF EXISTS TB_CASE ; """

    update_db(sql_drop_table)
    return "DB dropped!"


@app.route("/main", methods=["POST"])
def main():
    req = request.get_json(silent=True, force=True)
    host = request.host
    intent_name = req["queryResult"]["intent"]["displayName"]
    print(req)

    if intent_name == "CheckCovidStatus":
        country = req["queryResult"]["parameters"]["country"]
        date = req["queryResult"]["parameters"]["date"]
        resp = get_covid_status_in_country(host, country, date)

    elif intent_name == "UploadTemperature":
        temp = req["queryResult"]["parameters"]["temp"]
        resp = upload_temperature_to_website(host, temp)
    elif intent_name == "RedirectToLink":
        resp = redirect_to_website()
    else:
        resp = {
            "fulfillment_text": "Unable to find a matching intent. Try again."
        }

    return Response(json.dumps(resp), status=200, content_type="application/json")


if __name__ == '__main__':
    DATABASE = "./db/demo.db"

    # Generate a globally unique address for this node
    node_identifier = str(uuid4()).replace('-', '')

    print(node_identifier)
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5001, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port, debug=True)
