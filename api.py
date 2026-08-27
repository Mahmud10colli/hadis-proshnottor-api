from flask import Flask, jsonify
import requests

app = Flask(__name__)

BASE_URL = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"

BOOKS = {
    "bukhari": {
        "arabic": "ara-bukhari",
        "bengali": "ben-bukhari",
        "name": "Sahih al-Bukhari"
    }
}


def get_json(url):
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.json()


@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "Hadis Proshnottor API is running"
    })


@app.route("/hadith/<book>/<int:number>")
def hadith(book, number):

    if book not in BOOKS:
        return jsonify({
            "error": "Book not supported"
        }), 404

    info = BOOKS[book]

    arabic_url = f"{BASE_URL}/{info['arabic']}/{number}.json"
    bengali_url = f"{BASE_URL}/{info['bengali']}/{number}.json"

    try:
        arabic_data = get_json(arabic_url)
        bengali_data = get_json(bengali_url)

        arabic_hadith = arabic_data.get("hadiths", [{}])[0]
        bengali_hadith = bengali_data.get("hadiths", [{}])[0]

        metadata = arabic_data.get("metadata", {})
        section = metadata.get("section", {})

        result = {
            "hadithnumber": arabic_hadith.get("hadithnumber"),
            "arabicnumber": arabic_hadith.get("arabicnumber"),

            "arabic": arabic_hadith.get("text"),
            "bengali": bengali_hadith.get("text"),

            "book": info["name"],

            "chapter": section,

            "reference": arabic_hadith.get("reference"),

            "grades": arabic_hadith.get("grades", []),

            "source": "Fawaz Ahmed Hadith API",

            "metadata": metadata
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
