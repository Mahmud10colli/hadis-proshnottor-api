from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BASE_URL = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"

BOOKS = {
    "bukhari": {
        "name": "Sahih al-Bukhari",
        "arabic": "ara-bukhari",
        "bengali": "ben-bukhari"
    },
    "muslim": {
        "name": "Sahih Muslim",
        "arabic": "ara-muslim",
        "bengali": "ben-muslim"
    },
    "abudawud": {
        "name": "Sunan Abu Dawud",
        "arabic": "ara-abudawud",
        "bengali": "ben-abudawud"
    },
    "tirmidhi": {
        "name": "Jami' at-Tirmidhi",
        "arabic": "ara-tirmidhi",
        "bengali": "ben-tirmidhi"
    },
    "ibnmajah": {
        "name": "Sunan Ibn Majah",
        "arabic": "ara-ibnmajah",
        "bengali": "ben-ibnmajah"
    },
    "nasai": {
        "name": "Sunan an-Nasa'i",
        "arabic": "ara-nasai",
        "bengali": "ben-nasai"
    },
    "malik": {
        "name": "Muwatta Malik",
        "arabic": "ara-malik",
        "bengali": "ben-malik"
    }
}


def get_json(url):
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.json()


def get_hadith(book, number):
    if book not in BOOKS:
        return None

    info = BOOKS[book]

    arabic_url = f"{BASE_URL}/{info['arabic']}/{number}.json"
    bengali_url = f"{BASE_URL}/{info['bengali']}/{number}.json"

    try:
        arabic_data = get_json(arabic_url)
    except Exception:
        arabic_data = {}

    try:
        bengali_data = get_json(bengali_url)
    except Exception:
        bengali_data = {}

    arabic_hadith = {}
    bengali_hadith = {}

    if isinstance(arabic_data, dict):
        hadiths = arabic_data.get("hadiths", [])
        if hadiths:
            arabic_hadith = hadiths[0]

    if isinstance(bengali_data, dict):
        hadiths = bengali_data.get("hadiths", [])
        if hadiths:
            bengali_hadith = hadiths[0]

    return {
        "hadith_number": (
            arabic_hadith.get("hadithnumber")
            or bengali_hadith.get("hadithnumber")
            or number
        ),

        "arabic_number": (
            arabic_hadith.get("arabicnumber")
            or bengali_hadith.get("arabicnumber")
        ),

        "arabic": arabic_hadith.get("text", ""),

        "bengali": bengali_hadith.get("text", ""),

        "book": info["name"],

        "reference": (
            arabic_hadith.get("reference")
            or bengali_hadith.get("reference")
            or {}
        ),

        "grades": arabic_hadith.get("grades", []),

        "source": "fawazahmed0/hadith-api"
    }


@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "Hadis Proshnottor Combined API is running"
    })


@app.route("/hadith/<book>/<int:number>")
def single_hadith(book, number):
    result = get_hadith(book, number)

    if result is None:
        return jsonify({
            "error": "Unknown book",
            "available_books": list(BOOKS.keys())
        }), 404

    return jsonify(result)


@app.route("/hadith/search")
def search_hadith():

    query = request.args.get("q", "").strip()
    book = request.args.get("book", "bukhari").strip().lower()

    if not query:
        return jsonify({
            "error": "Search query is required",
            "example": "/hadith/search?q=namaz&book=bukhari"
        }), 400

    if book not in BOOKS:
        return jsonify({
            "error": "Unknown book",
            "available_books": list(BOOKS.keys())
        }), 404

    info = BOOKS[book]

    try:
        arabic_data = get_json(
            f"{BASE_URL}/{info['arabic']}.json"
        )

        bengali_data = get_json(
            f"{BASE_URL}/{info['bengali']}.json"
        )

    except Exception as e:
        return jsonify({
            "error": "Could not load hadith data",
            "details": str(e)
        }), 502

    arabic_hadiths = arabic_data.get("hadiths", [])
    bengali_hadiths = bengali_data.get("hadiths", [])

    bengali_by_number = {}

    for h in bengali_hadiths:
        number = h.get("hadithnumber")
        if number is not None:
            bengali_by_number[str(number)] = h

    query_lower = query.lower()

    results = []

    for h in arabic_hadiths:

        arabic_text = h.get("text", "")
        number = h.get("hadithnumber")

        bengali_h = bengali_by_number.get(str(number), {})
        bengali_text = bengali_h.get("text", "")

        if (
            query_lower in arabic_text.lower()
            or query_lower in bengali_text.lower()
            or query_lower in str(number)
        ):

            results.append({
                "hadith_number": number,

                "arabic_number": h.get("arabicnumber"),

                "arabic": arabic_text,

                "bengali": bengali_text,

                "book": info["name"],

                "reference": h.get("reference", {}),

                "grades": h.get("grades", []),

                "source": "fawazahmed0/hadith-api"
            })

    return jsonify({
        "query": query,
        "book": book,
        "count": len(results),
        "results": results
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
