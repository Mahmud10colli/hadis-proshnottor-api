from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

BASE_URL = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
RAW_URL = "https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions"

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


# ---------------------------------------------------------
# HTTP / JSON
# ---------------------------------------------------------

def get_json(edition, number=None):
    """
    CDN -> GitHub Raw fallback.
    """

    if number is None:
        urls = [
            f"{BASE_URL}/{edition}.min.json",
            f"{BASE_URL}/{edition}.json",
            f"{RAW_URL}/{edition}.min.json",
            f"{RAW_URL}/{edition}.json"
        ]
    else:
        urls = [
            f"{BASE_URL}/{edition}/{number}.min.json",
            f"{BASE_URL}/{edition}/{number}.json",
            f"{RAW_URL}/{edition}/{number}.min.json",
            f"{RAW_URL}/{edition}/{number}.json"
        ]

    last_error = None

    for url in urls:
        try:
            response = requests.get(
                url,
                timeout=30,
                headers={
                    "User-Agent": "Hadis-Proshnottor-API/1.0"
                }
            )

            if response.status_code == 200:
                return response.json()

            last_error = f"HTTP {response.status_code}"

        except Exception as e:
            last_error = str(e)

    raise Exception(
        f"Could not load edition '{edition}'. Last error: {last_error}"
    )


# ---------------------------------------------------------
# Text helpers
# ---------------------------------------------------------

def normalize_text(text):
    if not text:
        return ""

    text = str(text).lower()

    # Arabic harakat remove
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)

    # Bengali punctuation / common punctuation
    text = re.sub(r"[^\w\u0600-\u06FF\u0980-\u09FF\s]", " ", text)

    # Multiple spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def query_variants(query):
    """
    User English/Bengali/Arabic যেভাবেই লিখুক,
    সাধারণ গুরুত্বপূর্ণ শব্দের equivalent search তৈরি করবে।
    """

    q = normalize_text(query)

    variants = {q}

    translations = {
        "allah": ["allah", "আল্লাহ", "الله"],
        "god": ["god", "allah", "আল্লাহ", "الله"],
        "namaz": ["namaz", "salah", "salat", "নামাজ", "সালাত", "صلاة", "الصلاة"],
        "salah": ["salah", "salat", "namaz", "নামাজ", "সালাত", "صلاة", "الصلاة"],
        "salat": ["salat", "salah", "namaz", "নামাজ", "সালাত", "صلاة", "الصلاة"],
        "prayer": ["prayer", "salah", "salat", "namaz", "নামাজ", "সালাত", "صلاة"],
        "roza": ["roza", "fasting", "sawm", "রোজা", "সিয়াম", "صيام", "الصيام"],
        "fasting": ["fasting", "roza", "sawm", "রোজা", "সিয়াম", "صيام", "الصيام"],
        "sawm": ["sawm", "fasting", "roza", "রোজা", "সিয়াম", "صيام", "الصيام"],
        "zakat": ["zakat", "যাকাত", "زكاة", "الزكاة"],
        "hajj": ["hajj", "হজ", "حج", "الحج"],
        "wudu": ["wudu", "ওযু", "অজু", "وضوء"],
        "ablution": ["ablution", "wudu", "ওযু", "অজু", "وضوء"],
        "mosque": ["mosque", "মসজিদ", "مسجد"],
        "masjid": ["masjid", "mosque", "মসজিদ", "مسجد"],
        "prophet": ["prophet", "নবী", "রাসূল", "رسول", "النبي"],
        "muhammad": ["muhammad", "মুহাম্মদ", "محمد"],
        "islam": ["islam", "ইসলাম", "الإسلام"],
        "iman": ["iman", "ঈমান", "إيمان"],
        "faith": ["faith", "iman", "ঈমান", "إيمان"]
    }

    if q in translations:
        variants.update(translations[q])

    return [normalize_text(v) for v in variants if v]


def text_matches(text, variants):
    normalized = normalize_text(text)

    for variant in variants:
        if variant and variant in normalized:
            return True

    return False


# ---------------------------------------------------------
# Hadith formatter
# ---------------------------------------------------------

def format_hadith(arabic_hadith, bengali_hadith, book_name):

    arabic_hadith = arabic_hadith or {}
    bengali_hadith = bengali_hadith or {}

    return {
        "hadith_number": (
            arabic_hadith.get("hadithnumber")
            or bengali_hadith.get("hadithnumber")
            or ""
        ),

        "arabic_number": (
            arabic_hadith.get("arabicnumber")
            or bengali_hadith.get("arabicnumber")
            or ""
        ),

        "arabic": arabic_hadith.get("text", ""),

        "bengali": bengali_hadith.get("text", ""),

        "book": book_name,

        "reference": (
            arabic_hadith.get("reference")
            or bengali_hadith.get("reference")
            or {}
        ),

        "grades": (
            arabic_hadith.get("grades")
            or bengali_hadith.get("grades")
            or []
        ),

        "source": "fawazahmed0/hadith-api"
    }


# ---------------------------------------------------------
# Single Hadith
# ---------------------------------------------------------

def get_hadith(book, number):

    if book not in BOOKS:
        return None

    info = BOOKS[book]

    try:
        arabic_data = get_json(
            info["arabic"],
            number
        )
    except Exception:
        arabic_data = {}

    try:
        bengali_data = get_json(
            info["bengali"],
            number
        )
    except Exception:
        bengali_data = {}

    arabic_hadiths = arabic_data.get("hadiths", [])
    bengali_hadiths = bengali_data.get("hadiths", [])

    arabic_hadith = (
        arabic_hadiths[0]
        if arabic_hadiths
        else {}
    )

    bengali_hadith = (
        bengali_hadiths[0]
        if bengali_hadiths
        else {}
    )

    return format_hadith(
        arabic_hadith,
        bengali_hadith,
        info["name"]
    )


# ---------------------------------------------------------
# Home
# ---------------------------------------------------------

@app.route("/")
def home():

    return jsonify({
        "status": "ok",
        "message": "Hadis Proshnottor Combined API is running",
        "version": "2.0",
        "search": "/hadith/search?q=Allah&book=bukhari",
        "single": "/hadith/bukhari/1"
    })


# ---------------------------------------------------------
# Single Hadith Route
# ---------------------------------------------------------

@app.route("/hadith/<book>/<int:number>")
def single_hadith(book, number):

    result = get_hadith(
        book.lower(),
        number
    )

    if result is None:

        return jsonify({
            "error": "Unknown book",
            "available_books": list(BOOKS.keys())
        }), 404

    return jsonify(result)


# ---------------------------------------------------------
# SEARCH
# ---------------------------------------------------------

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
            "example": "/hadith/search?q=Allah&book=bukhari"
        }), 400

    if book not in BOOKS:

        return jsonify({
            "error": "Unknown book",
            "available_books": list(BOOKS.keys())
        }), 404

    info = BOOKS[book]

    # ---------------------------------------------
    # Load Arabic edition
    # ---------------------------------------------

    try:

        arabic_data = get_json(
            info["arabic"]
        )

    except Exception as e:

        return jsonify({
            "error": "Could not load Arabic hadith data",
            "details": str(e)
        }), 502

    # ---------------------------------------------
    # Load Bengali edition
    # ---------------------------------------------

    try:

        bengali_data = get_json(
            info["bengali"]
        )

    except Exception as e:

        bengali_data = {
            "hadiths": []
        }

    arabic_hadiths = arabic_data.get(
        "hadiths",
        []
    )

    bengali_hadiths = bengali_data.get(
        "hadiths",
        []
    )

    # ---------------------------------------------
    # Bengali index
    # ---------------------------------------------

    bengali_by_number = {}

    for h in bengali_hadiths:

        number = h.get(
            "hadithnumber"
        )

        if number is not None:

            bengali_by_number[
                str(number)
            ] = h

    # ---------------------------------------------
    # Search variants
    # ---------------------------------------------

    variants = query_variants(query)

    results = []

    # ---------------------------------------------
    # Search
    # ---------------------------------------------

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

        # Search Arabic + Bengali + Hadith number
        matched = (
            text_matches(
                arabic_text,
                variants
            )
            or
            text_matches(
                bengali_text,
                variants
            )
            or
            any(
                variant in str(number).lower()
                for variant in variants
                if variant
            )
        )

        if not matched:
            continue

        results.append(
            format_hadith(
                h,
                bengali_h,
                info["name"]
            )
        )

        # Search result limit
        if len(results) >= 50:
            break

    # ---------------------------------------------
    # Response
    # ---------------------------------------------

    return jsonify({

        "query": query,

        "book": book,

        "count": len(results),

        "results": results

    })


# ---------------------------------------------------------
# Run
# ---------------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
