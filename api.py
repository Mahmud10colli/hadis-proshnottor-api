from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

BASE_URL = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"

BOOKS = {
    "bukhari": {
        "name": "Sahih al-Bukhari",
        "arabic": "ara-bukhari",
        "bengali": "ben-bukhari"
    }
}

cache = {}


def get_json(url):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.json()


def load_book(book):
    if book in cache:
        return cache[book]

    info = BOOKS[book]

    arabic_data = get_json(
        f"{BASE_URL}/{info['arabic']}.json"
    )

    bengali_data = get_json(
        f"{BASE_URL}/{info['bengali']}.json"
    )

    arabic_hadiths = arabic_data.get("hadiths", [])
    bengali_hadiths = bengali_data.get("hadiths", [])

    bengali_by_number = {
        h.get("hadithnumber"): h
        for h in bengali_hadiths
    }

    results = []

    for h in arabic_hadiths:
        number = h.get("hadithnumber")
        bn = bengali_by_number.get(number, {})

        metadata = arabic_data.get("metadata", {})
        section = metadata.get("section", {})

        chapter = ""

        if isinstance(section, dict) and section:
            chapter = next(iter(section.values()))

        results.append({
            "hadithnumber": number,
            "arabicnumber": h.get("arabicnumber"),
            "arabic": h.get("text"),

            # Bengali field-এর নতুন নাম
            "bnText": bn.get("text"),

            "book": info["name"],
            "chapter": chapter,
            "reference": h.get("reference"),
            "grades": h.get("grades", []),
            "source": "Fawaz Ahmed Hadith API"
        })

    cache[book] = results

    return results


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

    try:
        results = load_book(book)

        for item in results:
            if item["hadithnumber"] == number:
                return jsonify(item)

        return jsonify({
            "error": "Hadith not found"
        }), 404

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app.route("/search")
def search():

    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({
            "total": 0,
            "results": []
        })

    try:
        all_results = []

        for book in BOOKS:
            results = load_book(book)

            for item in results:

                arabic = item.get("arabic") or ""
                bn_text = item.get("bnText") or ""

                if (
                    query.lower() in bn_text.lower()
                    or query.lower() in arabic.lower()
                ):
                    all_results.append(item)

        return jsonify({
            "total": len(all_results),
            "results": all_results
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
