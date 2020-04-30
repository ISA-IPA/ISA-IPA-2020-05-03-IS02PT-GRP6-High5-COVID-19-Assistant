import schedule
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.cloud import translate
import sqlite3

language_map = {
    "irish": "ga",
    "italian": "it",
    "arabic": "ar",
    "japanese": "ja",
    "korean": "ko",
    "latin": "la",
    "chinese": "zh",
    "malay": "ms",
    "norwegian": "no",
    "czech": "cs",
    "persian": "fa",
    "danish": "da",
    "polish": "pl",
    "dutch": "nl",
    "portuguese": "pt",
    "english": "en",
    "esperanto": "eo",
    "russian": "ru",
    "filipino": "tl",
    "finnish": "fi",
    "french": "fr",
    "spanish": "es",
    "swedish": "sv",
    "german": "de",
    "tamil": "ta",
    "greek": "el",
    "thai": "th",
    "turkish": "tr",
    "hindi": "hi",
    "vietnamese": "vi",
    "icelandic": "is",
    "welsh": "cy",
    "indonesian": "id"
}


def query_db(query, args=()):
    DATABASE = "./db/demo.db"
    db = sqlite3.connect(DATABASE)
    cur = db.cursor()
    cur.execute(query, args)

    rv = cur.fetchall()  # Retrive all rows
    cur.close()
    return rv
    # return (rv[0] if rv else None) if one else rv


def input_text_translation(text, target):
    try:
        client = translate.TranslationServiceClient.from_service_account_json(
            "D:/GoogleCloud/ipadaiyirui001-9cad5c929128.json")
        parent = client.location_path('ipadaiyirui001', 'global')

        contents = [text]
        target_language_code = language_map[target.lower()]

        response = client.translate_text(contents, target_language_code, parent)

        translation_api_reply = ""
        for translation in response.translations:
            translation_api_reply += format(translation.translated_text)

        resp = translation_api_reply
    except Exception as e:
        print(e)
        resp = ""
    return resp


def send_subscription_email():
    try:
        subs_rows = query_db("SELECT * from SUBSCRIPTION_INFO")
        print(subs_rows)

        news_rows = query_db("SELECT * FROM NEWS_INFO")
        size = len(news_rows)
        print("No of News: " + str(size))
        password = "covid@19Bot"
        title = news_rows[0][1]
        content = news_rows[0][3]
        message = content

        for row in subs_rows:
            msg = MIMEMultipart()
            msg['Subject'] = "News from your Covid-19 Bot: " + title
            msg['From'] = "issipacovid19utilbot@gmail.com"
            msg['To'] = row[0]
            languages = str(row[2]).split(",")
            for lang in languages:
                if lang != "English":
                    message += input_text_translation(content, lang)
            message += " Read more: " + news_rows[0][2]
            msg.attach(MIMEText(message, 'plain'))
            s = smtplib.SMTP('smtp.gmail.com: 587')
            s.starttls()
            s.login(msg['From'], password)
            s.sendmail(msg['From'], msg['To'], msg.as_string())
            s.quit()
    except Exception as e:
        print(e)


schedule.every().day.at("00:05").do(send_subscription_email)

while True:
    schedule.run_pending()
    time.sleep(1)
