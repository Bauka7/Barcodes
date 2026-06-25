import re


OFFICIAL_SHPI_BRANCH_CODES = [
    {"code": "01", "name": "Астанинский почтамт"},
    {"code": "02", "name": "Акмолинский ОФ"},
    {"code": "03", "name": "Актюбинский ОФ"},
    {"code": "04", "name": "Алматинский ОФ"},
    {"code": "05", "name": "Алматинский почтамт"},
    {"code": "06", "name": "Атырауский ОФ"},
    {"code": "07", "name": "Восточно-Казахстанский ОФ"},
    {"code": "08", "name": "Жамбылский ОФ"},
    {"code": "09", "name": "Западно-Казахстанский ОФ"},
    {"code": "10", "name": "Карагандинский ОФ"},
    {"code": "11", "name": "Костанайский ОФ"},
    {"code": "12", "name": "Кызылординский ОФ"},
    {"code": "13", "name": "Мангистауский ОФ"},
    {"code": "14", "name": "Павлодарский ОФ"},
    {"code": "15", "name": "Северо-Казахстанский ОФ"},
    {"code": "16", "name": "Шымкентский почтамт"},
    {"code": "17", "name": "Туркестанский ОФ"},
    {"code": "18", "name": 'Филиал АО "Казпочта" по области Абай'},
    {"code": "19", "name": "Республиканская служба специальной почтовой связи"},
    {"code": "20", "name": 'Филиал АО "Казпочта" по области Улытау'},
    {"code": "30", "name": 'ИЛЦ "ЮГ"'},
    {"code": "34", "name": 'Филиал АО "Казпочта" по области Жетысу'},
]

OFFICIAL_SHPI_BRANCH_CODE_VALUES = [
    item["code"] for item in OFFICIAL_SHPI_BRANCH_CODES
]

OFFICIAL_SHPI_BRANCH_NAME_BY_CODE = {
    item["code"]: item["name"] for item in OFFICIAL_SHPI_BRANCH_CODES
}

# Backward-compatible import name used by the SHPI Map service.
KAZPOST_REGION_CODES = OFFICIAL_SHPI_BRANCH_CODE_VALUES

_QUOTE_TRANSLATION = str.maketrans(
    {
        "«": '"',
        "»": '"',
        "“": '"',
        "”": '"',
        "„": '"',
        "‟": '"',
        "’": "'",
        "‘": "'",
    }
)

_OFFICIAL_MATCHERS = [
    ("01", ("астанинский почтамт",)),
    ("02", ("акмолинский оф",)),
    ("03", ("актюбинский оф",)),
    ("04", ("алматинский оф",)),
    ("05", ("алматинский почтамт",)),
    ("06", ("атырауский оф",)),
    ("07", ("восточно-казахстанский оф",)),
    ("08", ("жамбылский оф",)),
    ("09", ("западно-казахстанский оф",)),
    ("10", ("карагандинский оф",)),
    ("11", ("костанайский оф",)),
    ("12", ("кызылординский оф",)),
    ("13", ("мангистауский оф",)),
    ("14", ("павлодарский оф",)),
    ("15", ("северо-казахстанский оф",)),
    ("16", ("шымкентский почтамт",)),
    ("17", ("туркестанский оф",)),
    ("18", ('филиал ао "казпочта" по области абай', "области абай", "область абай")),
    (
        "19",
        (
            "республиканская служба специальной почтовой связи",
            "специальной почтовой связи",
            "спецпочтовой связи",
        ),
    ),
    (
        "20",
        (
            'филиал ао "казпочта" по области улытау',
            "области улытау",
            "область улытау",
            "области ұлытау",
            "область ұлытау",
        ),
    ),
    ("30", ('илц "юг"', "илц юг")),
    (
        "34",
        (
            'филиал ао "казпочта" по области жетысу',
            "области жетысу",
            "область жетысу",
            "области жетісу",
            "область жетісу",
        ),
    ),
]


def normalize_shpi_branch_name(value: str) -> str:
    normalized = value.lower().strip().translate(_QUOTE_TRANSLATION).replace("ё", "е")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def resolve_official_shpi_branch_code(name: str) -> str | None:
    normalized_name = normalize_shpi_branch_name(name)
    if not normalized_name:
        return None

    for code, patterns in _OFFICIAL_MATCHERS:
        if any(pattern in normalized_name for pattern in patterns):
            return code

    return None
