```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BASE_URL = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"
RAW_URL = "https://raw.githubusercontent.com/fawazahmed0/hadith-api/1"

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


def get_json(endpoint):
    """
    Try multiple official Fawaz Ahmed API URLs.
    """

    urls = [
        f"{BASE_URL}/{endpoint}.json",
        f"{BASE_URL}/{endpoint}.min.json",
        f"{RAW_URL}/{endpoint}.json",
        f"{RAW_URL}/{endpoint}.min.json"
    ]

    last_error = None

    for url in urls:
        try:
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            last_error = str(e)

    raise Exception(last_error or "Could not load API data")


def get_hadith_from_edition(edition, number):
    """
    Get a single hadith from an edition.
    """

    try:
        data = get_json(f"editions/{edition}/{number}")

        if isinstance(data, dict):
            hadiths = data.get("hadiths", [])

            if hadiths:
                return hadiths[0]

    except Exception:
        pass

    return {}


def get_all_edition(edition):
    """
    Get the complete edition.
    """

    try:
        data = get_json(f"editions/{edition}")

        if isinstance(data, dict):
            return data

    except Exception:
        pass

    return {}


def get_info():
    """
    Get official Fawaz Ahmed info data.
    """

    try:
        return get_json("info")
    except Exception:
        return {}


def clean_grades(hadith):
    """
    Return grades exactly as supplied by the source.
    Never invent a grade.
    """

    grades = hadith.get("grades", [])

    if grades is None:
        return []

    if isinstance(grades, list):
        return grades

    return [grades]


def get_hadith(book, number):

    if book not in BOOKS:
        return None

    info = BOOKS[book]

    arabic_hadith = get_hadith_from_edition(
        info["arabic"],
        number
    )

    bengali_hadith = get_hadith_from_edition(
        info["bengali"],
        number
    )

    # Hadith number
    hadith_number = (
        arabic_hadith.get("hadithnumber")
        or bengali_hadith.get("hadithnumber")
        or number
    )

    # Arabic number
    arabic_number = (
        arabic_hadith.get("arabicnumber")
        or bengali_hadith.get("arabicnumber")
    )

    # Arabic text
    arabic_text = arabic_hadith.get("text", "")

    # Bengali translation
    bengali_text = bengali_hadith.get("text", "")

    # Reference
    reference = (
        arabic_hadith.get("reference")
        or bengali_hadith.get("reference")
        or {}
    )

    # Grades
    grades = clean_grades(arabic_hadith)

    # If Arabic edition has no grade, try Bengali edition
    if not grades:
        grades = clean_grades(bengali_hadith)

    return {
        "arabic": arabic_text,

        "bengali": bengali_text,

        "hadith_number": hadith_number,

        "arabic_number": arabic_number,

        "book": info["name"],

        "reference": reference,

        "grades": grades,

        "source": "fawazahmed0/hadith-api"
    }


@app.route("/")
def home():

    return jsonify({
        "status": "ok",
        "message": "Hadis Proshnottor Combined API is running",
        "available_books": list(BOOKS.keys())
    })


@app.route("/hadith/<book>/<int:number>")
def single_hadith(book, number):

    if book not in BOOKS:

        return jsonify({
            "error": "Unknown book",
            "available_books": list(BOOKS.keys())
        }), 404

    try:

        result = get_hadith(book, number)

        if result is None:

            return jsonify({
                "error": "Hadith not found"
            }), 404

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "error": "Could not load hadith",
            "details": str(e)
        }), 502


@app.route("/hadith/search")
def search_hadith():

    query = request.args.get("q", "").strip()

    book = request.args.get(
        "book",
        "bukhari"
    ).strip().lower()

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

        # Arabic complete edition
        arabic_data = get_all_edition(
            info["arabic"]
        )

        # Bengali complete edition
        bengali_data = get_all_edition(
            info["bengali"]
        )

    except Exception as e:

        return jsonify({
            "error": "Could not load hadith data",
            "details": str(e)
        }), 502

    arabic_hadiths = arabic_data.get(
        "hadiths",
        []
    )

    bengali_hadiths = bengali_data.get(
        "hadiths",
        []
    )

    # Match Bengali using hadith number
    bengali_by_number = {}

    for h in bengali_hadiths:

        h_number = h.get("hadithnumber")

        if h_number is not None:

            bengali_by_number[
                str(h_number)
            ] = h

    query_lower = query.lower()

    results = []

    for h in arabic_hadiths:

        arabic_text = h.get(
            "text",
            ""
        )

        number = h.get(
            "hadithnumber"
        )

        bengali_h = bengali_by_number.get(
            str(number),
            {}
        )

        bengali_text = bengali_h.get(
            "text",
            ""
        )

        number_text = str(
            number or ""
        )

        # Search Arabic, Bengali or Hadith number
        if (
            query_lower in arabic_text.lower()
            or query_lower in bengali_text.lower()
            or query_lower in number_text.lower()
        ):

            grades = clean_grades(h)

            if not grades:
                grades = clean_grades(
                    bengali_h
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
