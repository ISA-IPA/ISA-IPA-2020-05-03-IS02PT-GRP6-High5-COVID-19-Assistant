from flask import Flask, Response, request
import json

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


@app.route("/", methods=["POST"])
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


app.run(host='0.0.0.0', port=5000, debug=True)