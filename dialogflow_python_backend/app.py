from flask import Flask, Response, request
import json

app = Flask(__name__)

def getCovidStatusInCountryIntentHandler(country, date):
    country = country
    status = "Severe"
    date = date
    return f"The Covid Status in {country} is {status} {date}"

def uploadTemperatureToWebsite(temp):
    temperature = temp
    return f"Your tempurature {temperature} is successfully uploaded."

@app.route("/", methods = ["POST"])
def main():
    
    req = request.get_json(silent=True, force=True)
    print(req)
    intent_name = req["queryResult"]["intent"]["displayName"]

    if intent_name == "CheckCovidStatus":
        country = req["queryResult"]["parameters"]["country"]
        date = req["queryResult"]["parameters"]["date"]
        resp_text = getCovidStatusInCountryIntentHandler(country, date)
    elif intent_name == "UploadTemperature":
        temp = req["queryResult"]["parameters"]["temp"]
        resp_text = uploadTemperatureToWebsite(temp)
    else:
        resp_text = "Unable to find a matching intent. Try again."

    resp = {
        "fulfillmentText": resp_text
    }

    return Response(json.dumps(resp), status=200, content_type="application/json")

app.run(host='0.0.0.0', port=5000, debug=True)