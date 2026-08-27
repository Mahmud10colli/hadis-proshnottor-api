from flask import Flask, jsonify, request
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
        return jsonify({"error": "Book not supported"}), 404

    info = BOOKS[book]

    try:
        arabic_data = get_json(
            f"{BASE_URL}/{info['arabic']}/{number}.json"
        )

        bengali_data = get_json(
            f"{BASE_URL}/{info['bengali']}/{number}.json"
        )

        arabic_hadith = arabic_data.get("hadiths", [{}])[0]
        bengali_hadith = bengali_data.get("hadiths", [{}])[0]

        metadata = arabic_data.get("metadata", {})
        section = metadata.get("section", {})

        return jsonify({
            "hadithnumber": arabic_hadith.get("hadithnumber"),
            "arabicnumber": arabic_hadith.get("arabicnumber"),
            "arabic": arabic_hadith.get("text"),
            "bengali": bengali_hadith.get("text"),
            "book": info["name"],
            "chapter": section,
            "reference": arabic_hadith.get("reference"),
            "grades": arabic_hadith.get("grades", []),
            "source": "Fawaz Ahmed Hadith API"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search")
def search():

    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({
            "results": []
        })

    results = []

    # বর্তমানে Bukhari-এর প্রথম 100 হাদিসে অনুসন্ধান
    # পরবর্তীতে আমরা সব হাদিসের জন্য এটিকে উন্নত করব।
    for number in range(1, 101):

        try:
            data = get_json(
                f"{BASE_URL}/ben-bukhari/{number}.json"
            )

            hadith = data.get("hadiths", [{}])[0]
            text = hadith.get("text", "")

            if query.lower() in text.lower():

                full = get_json(
                    f"{BASE_URL}/ara-bukhari/{number}.json"
                )

                arabic_hadith = full.get("hadiths", [{}])[0]
                metadata = full.get("metadata", {})

                results.append({
                    "hadithnumber": arabic_hadith.get("hadithnumber"),
                    "arabic": arabic_hadith.get("text"),
                    "bengali": text,
                    "book": "Sahih al-Bukhari",
                    "chapter": metadata.get("section", {}),
                    "reference": arabic_hadith.get("reference"),
                    "source": "Fawaz Ahmed Hadith API"
                })

        except Exception:
            continue

    return jsonify({
        "total": len(results),
        "results": results
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
