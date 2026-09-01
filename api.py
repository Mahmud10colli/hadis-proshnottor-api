from flask import Flask, request, jsonify
import requests
import re
from functools import lru_cache

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


# =========================================================
# HTTP / JSON
# =========================================================

def request_json(url):
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Hadis-Proshnottor-API/3.0"
        }
    )

    response.raise_for_status()
    return response.json()


@lru_cache(maxsize=50)
def get_json(edition, number=None):

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

    last_error = "Unknown error"

    for url in urls:
        try:
            return request_json(url)
        except Exception as e:
            last_error = str(e)

    raise Exception(
        f"Could not load edition '{edition}'. "
        f"Last error: {last_error}"
    )


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(text):

    if text is None:
        return ""

    text = str(text).lower()

    # Arabic harakat
    text = re.sub(
        r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]",
        "",
        text
    )

    # Arabic tatweel
    text = text.replace("ـ", "")

    # Arabic letter normalization
    text = text.replace("أ", "ا")
    text = text.replace("إ", "ا")
    text = text.replace("آ", "ا")
    text = text.replace("ٱ", "ا")

    # punctuation
    text = re.sub(
        r"[^\w\u0600-\u06FF\u0980-\u09FF\s]",
        " ",
        text
    )

    # multiple spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =========================================================
# SEARCH VARIANTS
# =========================================================

SEARCH_MAP = {

    "allah": [
        "allah",
        "আল্লাহ",
        "الله"
    ],

    "god": [
        "god",
        "allah",
        "আল্লাহ",
        "الله"
    ],

    "namaz": [
        "namaz",
        "salah",
        "salat",
        "prayer",
        "নামাজ",
        "সালাত",
        "নামায",
        "صلاة",
        "الصلاة"
    ],

    "salah": [
        "salah",
        "salat",
        "namaz",
        "prayer",
        "নামাজ",
        "সালাত",
        "নামায",
        "صلاة",
        "الصلاة"
    ],

    "salat": [
        "salat",
        "salah",
        "namaz",
        "prayer",
        "নামাজ",
        "সালাত",
        "নামায",
        "صلاة",
        "الصلاة"
    ],

    "prayer": [
        "prayer",
        "salah",
        "salat",
        "namaz",
        "নামাজ",
        "সালাত",
        "নামায",
        "صلاة",
        "الصلاة"
    ],

    "roza": [
        "roza",
        "fasting",
        "sawm",
        "রোজা",
        "রোযা",
        "সিয়াম",
        "صيام",
        "الصيام"
    ],

    "fasting": [
        "fasting",
        "roza",
        "sawm",
        "রোজা",
        "রোযা",
        "সিয়াম",
        "صيام",
        "الصيام"
    ],

    "sawm": [
        "sawm",
        "fasting",
        "roza",
        "রোজা",
        "রোযা",
        "সিয়াম",
        "صيام",
        "الصيام"
    ],

    "zakat": [
        "zakat",
        "যাকাত",
        "زكاة",
        "الزكاة"
    ],

    "hajj": [
        "hajj",
        "হজ",
        "হজ্জ",
        "حج",
        "الحج"
    ],

    "wudu": [
        "wudu",
        "ওযু",
        "অজু",
        "وضوء"
    ],

    "ablution": [
        "ablution",
        "wudu",
        "ওযু",
        "অজু",
        "وضوء"
    ],

    "mosque": [
        "mosque",
        "মসজিদ",
        "مسجد"
    ],

    "masjid": [
        "masjid",
        "mosque",
        "মসজিদ",
        "مسجد"
    ],

    "prophet": [
        "prophet",
        "নবী",
        "নবীজি",
        "রাসূল",
        "রসূল",
        "رسول",
        "النبي"
    ],

    "muhammad": [
        "muhammad",
        "মুহাম্মদ",
        "মুহাম্মাদ",
        "محمد"
    ],

    "islam": [
        "islam",
        "ইসলাম",
        "الإسلام"
    ],

    "iman": [
        "iman",
        "ঈমান",
        "ইমান",
        "إيمان"
    ],

    "faith": [
        "faith",
        "iman",
        "ঈমান",
        "ইমান",
        "إيمان"
    ]
}


def query_variants(query):

    q = normalize_text(query)

    variants = set()

    if q:
        variants.add(q)

    if q in SEARCH_MAP:
        for value in SEARCH_MAP[q]:
            normalized = normalize_text(value)

            if normalized:
                variants.add(normalized)

    return list(variants)


def text_matches(text, variants):

    normalized = normalize_text(text)

    if not normalized:
        return False

    for variant in variants:
        if variant and variant in normalized:
            return True

    return False


# =========================================================
# HADITH FORMATTER
# =========================================================

def format_hadith(
    arabic_hadith,
    bengali_hadith,
    book_name
):

    arabic_hadith = arabic_hadith or {}
    bengali_hadith = bengali_hadith or {}

    reference = (
        arabic_hadith.get("reference")
        or bengali_hadith.get("reference")
        or {}
    )

    grades = (
        arabic_hadith.get("grades")
        or bengali_hadith.get("grades")
        or []
    )

    return {

        "hadith_number":
            arabic_hadith.get("hadithnumber")
            or bengali_hadith.get("hadithnumber")
            or "",

        "arabic_number":
            arabic_hadith.get("arabicnumber")
            or bengali_hadith.get("arabicnumber")
            or "",

        "arabic":
            arabic_hadith.get("text", ""),

        "bengali":
            bengali_hadith.get("text", ""),

        "book":
            book_name,

        "reference":
            reference,

        "grades":
            grades,

        "source":
            "fawazahmed0/hadith-api"
    }


# =========================================================
# SINGLE HADITH
# =========================================================

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

    arabic_hadiths = arabic_data.get(
        "hadiths",
        []
    )

    bengali_hadiths = bengali_data.get(
        "hadiths",
        []
    )

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


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return jsonify({

        "status": "ok",

        "message":
            "Hadis Proshnottor Combined API is running",

        "version":
            "3.0",

        "search":
            "/hadith/search?q=Allah&book=bukhari",

        "single":
            "/hadith/bukhari/1"

    })


# =========================================================
# SINGLE HADITH ROUTE
# =========================================================

@app.route("/hadith/<book>/<int:number>")
def single_hadith(book, number):

    result = get_hadith(
        book.lower(),
        number
    )

    if result is None:

        return jsonify({

            "error":
                "Unknown book",

            "available_books":
                list(BOOKS.keys())

        }), 404

    return jsonify(result)


# =========================================================
# SEARCH
# =========================================================

@app.route("/hadith/search")
def search_hadith():

    query = request.args.get(
        "q",
        ""
    ).strip()

    book = request.args.get(
        "book",
        "bukhari"
    ).strip().lower()

    if not query:

        return jsonify({

            "error":
                "Search query is required",

            "example":
                "/hadith/search?q=Allah&book=bukhari"

        }), 400

    if book not in BOOKS:

        return jsonify({

            "error":
                "Unknown book",

            "available_books":
                list(BOOKS.keys())

        }), 404

    info = BOOKS[book]

    # -----------------------------------------------------
    # Load Arabic edition
    # -----------------------------------------------------

    try:

        arabic_data = get_json(
            info["arabic"]
        )

    except Exception as e:

        return jsonify({

            "error":
                "Could not load Arabic hadith data",

            "details":
                str(e)

        }), 502

    # -----------------------------------------------------
    # Load Bengali edition
    # -----------------------------------------------------

    try:

        bengali_data = get_json(
            info["bengali"]
        )

    except Exception:

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

    # -----------------------------------------------------
    # Bengali index
    # -----------------------------------------------------

    bengali_by_number = {}

    for h in bengali_hadiths:

        number = h.get(
            "hadithnumber"
        )

        if number is not None:

            bengali_by_number[
                str(number)
            ] = h

    # -----------------------------------------------------
    # Search variants
    # -----------------------------------------------------

    variants = query_variants(query)

    results = []

    # -----------------------------------------------------
    # Search Arabic + Bengali
    # -----------------------------------------------------

    for arabic_hadith in arabic_hadiths:

        number = arabic_hadith.get(
            "hadithnumber"
        )

        bengali_hadith = (
            bengali_by_number.get(
                str(number),
                {}
            )
        )

        arabic_text = (
            arabic_hadith.get(
                "text",
                ""
            )
        )

        bengali_text = (
            bengali_hadith.get(
                "text",
                ""
            )
        )

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
                variant == normalize_text(
                    str(number)
                )
                for variant in variants
            )
        )

        if not matched:
            continue

        results.append(
            format_hadith(
                arabic_hadith,
                bengali_hadith,
                info["name"]
            )
        )

        if len(results) >= 50:
            break

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return jsonify({

        "query":
            query,

        "book":
            book,

        "count":
            len(results),

        "results":
            results

    })


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
