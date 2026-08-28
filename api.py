```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BASE_URL = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"

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


def get_json(path):

    urls = [
        f"{BASE_URL}/{path}.min.json",
        f"{BASE_URL}/{path}.json"
    ]

    for url in urls:

        try:

            response = requests.get(
                url,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()

        except Exception:
            pass

    return {}


def get_hadith(book, number):

    info = BOOKS[book]

    arabic_data = get_json(
        f"editions/{info['arabic']}/{number}"
    )

    bengali_data = get_json(
        f"editions/{info['bengali']}/{number}"
    )

    arabic_list = arabic_data.get(
        "hadiths",
        []
    )

    bengali_list = bengali_data.get(
        "hadiths",
        []
    )

    arabic = (
        arabic_list[0]
        if arabic_list
        else {}
    )

    bengali = (
        bengali_list[0]
        if bengali_list
        else {}
    )

    grades = arabic.get(
        "grades",
        []
    )

    if not grades:
        grades = bengali.get(
            "grades",
            []
        )

    return {

        "arabic": arabic.get(
            "text",
            ""
        ),

        "bengali": bengali.get(
            "text",
            ""
        ),

        "hadith_number": (
            arabic.get("hadithnumber")
            or bengali.get("hadithnumber")
            or number
        ),

        "arabic_number": (
            arabic.get("arabicnumber")
            or bengali.get("arabicnumber")
        ),

        "book": info["name"],

        "reference": (
            arabic.get("reference")
            or bengali.get("reference")
            or {}
        ),

        "grades": grades,

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

    if book not in BOOKS:

        return jsonify({
            "error": "Unknown book",
            "available_books": list(
                BOOKS.keys()
            )
        }), 404

    try:

        result = get_hadith(
            book,
            number
        )

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


@app.route("/hadith/search")
def search_hadith():

    query = request.args.get(
        "q",
        ""
    ).strip()

    book = request.args.get(
        "book",
        "bukhari"
    ).lower()

    if not query:

        return jsonify({
            "error": "Search query is required"
        }), 400

    if book not in BOOKS:

        return jsonify({
            "error": "Unknown book",
            "available_books": list(
                BOOKS.keys()
            )
        }), 404

    info = BOOKS[book]

    arabic_data = get_json(
        f"editions/{info['arabic']}"
    )

    bengali_data = get_json(
        f"editions/{info['bengali']}"
    )

    arabic_hadiths = arabic_data.get(
        "hadiths",
        []
    )

    bengali_hadiths = bengali_data.get(
        "hadiths",
        []
    )

    bengali_by_number = {}

    for h in bengali_hadiths:

        number = h.get(
            "hadithnumber"
        )

        if number is not None:

            bengali_by_number[
                str(number)
            ] = h

    results = []

    query_lower = query.lower()

    for h in arabic_hadiths:

        number = h.get(
            "hadithnumber"
        )

        arabic_text = h.get(
            "text",
            ""
        )

        bengali_h = bengali_by_number.get(
            str(number),
            {}
        )

        bengali_text = bengali_h.get(
            "text",
            ""
        )

        if (
            query_lower in arabic_text.lower()
            or query_lower in bengali_text.lower()
            or query_lower in str(number)
        ):

            grades = h.get(
                "grades",
                []
            )

            if not grades:

                grades = bengali_h.get(
                    "grades",
                    []
                )

            results.append({

                "arabic": arabic_text,

                "bengali": bengali_text,

                "hadith_number": number,

                "arabic_number": h.get(
                    "arabicnumber"
                ),

                "book": info["name"],

                "reference": (
                    h.get("reference")
                    or bengali_h.get(
                        "reference",
                        {}
                    )
                ),

                "grades": grades,

                "source": "fawazahmed0/hadith-api"
            })

    return jsonify({

        "query": query,

        "book": book,

        "count": len(results),

        "results": results

    })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
```
