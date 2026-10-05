"""Generate deterministic demo wines, users, and likes."""

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parents[1] / "src" / "wine_recommendation" / "data"
WINES_PATH = DATA_DIR / "mock_wines.json"
USERS_PATH = DATA_DIR / "mock_users.json"
LIKES_PATH = DATA_DIR / "mock_likes.json"

COLOR_LABELS = {"red": "красное", "white": "белое", "rose": "розовое"}
SUGAR_LABELS = {
    "dry": "сухое",
    "semi_dry": "полусухое",
    "semi_sweet": "полусладкое",
    "sweet": "сладкое",
}
PROFILES = {
    "red": [
        ("Valle Rosso", "Италия", "Тоскана", "Санджовезе"),
        ("Rio Alto", "Испания", "Риоха", "Темпранильо"),
        ("Andes Crown", "Аргентина", "Мендоса", "Мальбек"),
        ("Kakheti Sun", "Грузия", "Кахетия", "Саперави"),
        ("Douro Hills", "Португалия", "Дору", "Турига Насьональ"),
        ("Cape Reserve", "ЮАР", "Стелленбос", "Пинотаж"),
        ("Black Sea Cellar", "Россия", "Краснодарский край", "Каберне Совиньон"),
    ],
    "white": [
        ("Loire Etoile", "Франция", "Долина Луары", "Совиньон Блан"),
        ("Rhine Gold", "Германия", "Мозель", "Рислинг"),
        ("Pacific Vale", "Чили", "Касабланка", "Шардоне"),
        ("Danube Pearl", "Венгрия", "Токай", "Мускат"),
        ("Cape Breeze", "ЮАР", "Западный Кейп", "Шенен Блан"),
        ("Veneto Luna", "Италия", "Венето", "Пино Гриджио"),
        ("Crimean Coast", "Россия", "Крым", "Алиготе"),
    ],
    "rose": [
        ("Provence Ciel", "Франция", "Прованс", "Гренаш, Сенсо"),
        ("Navarra Bloom", "Испания", "Наварра", "Гарнача"),
        ("Adriatic Rose", "Италия", "Абруццо", "Монтепульчано"),
        ("Kuban Blush", "Россия", "Кубань", "Цвайгельт"),
        ("Alazani Rose", "Грузия", "Кахетия", "Саперави"),
        ("Mendoza Pink", "Аргентина", "Мендоса", "Мальбек"),
        ("Cape Coral", "ЮАР", "Западный Кейп", "Пинотаж"),
    ],
}
USERNAMES = [
    "Алексей",
    "Мария",
    "Дмитрий",
    "Анна",
    "Михаил",
    "Елена",
    "Сергей",
    "Ольга",
    "Андрей",
    "Наталья",
    "Иван",
    "Екатерина",
    "Никита",
    "Светлана",
    "Павел",
    "Ирина",
    "Артём",
    "Татьяна",
    "Роман",
    "Вера",
]


def build_wines(existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    wines = existing[:16]
    colors = list(COLOR_LABELS)
    sugars = list(SUGAR_LABELS)
    for number in range(17, 101):
        position = number - 17
        color = colors[position % len(colors)]
        sugar = sugars[(position // len(colors)) % len(sugars)]
        profiles = PROFILES[color]
        brand, country, region, grape = profiles[(position // 12) % len(profiles)]
        price = 549 + ((position * 137) % 2550)
        rating = round(3.8 + ((position * 7) % 12) / 10, 1)
        wine = {
            "id": f"mock-{number:03d}",
            "name": (
                f"Вино {brand} Selection {number} {COLOR_LABELS[color]} "
                f"{SUGAR_LABELS[sugar]}, 750мл"
            ),
            "brand": brand,
            "country": country,
            "region": region,
            "color": COLOR_LABELS[color],
            "sugar_type": SUGAR_LABELS[sugar],
            "grape": grape,
            "volume": 0.75,
            "description": f"Демо-вино {brand}: сбалансированный вкус и яркий аромат.",
            "price": price,
            "is_available": position % 19 != 0,
            "rating": rating,
            "reviews_count": 12 + ((position * 43) % 480),
            "product_url": f"https://example.test/wines/mock-{number:03d}",
        }
        if position % 3 == 0:
            wine["old_price"] = price + 250
        wines.append(wine)
    return wines


def normalized(value: str, labels: dict[str, str]) -> str:
    return next(key for key, label in labels.items() if label == value)


def main() -> None:
    payload = json.loads(WINES_PATH.read_text(encoding="utf-8"))
    wines = build_wines(payload["items"])
    users = [
        {"external_id": f"mock-user-{number:03d}", "username": username}
        for number, username in enumerate(USERNAMES, start=1)
    ]

    grouped: dict[tuple[str, str], list[str]] = {}
    for wine in wines:
        pair = (
            normalized(wine["color"], COLOR_LABELS),
            normalized(wine["sugar_type"], SUGAR_LABELS),
        )
        grouped.setdefault(pair, []).append(wine["id"])

    preference_pairs = [(color, sugar) for sugar in SUGAR_LABELS for color in COLOR_LABELS]
    likes: list[dict[str, str]] = []
    for index, user in enumerate(users):
        candidates = grouped[preference_pairs[index % len(preference_pairs)]]
        for offset in range(6):
            likes.append(
                {
                    "user_external_id": user["external_id"],
                    "wine_external_id": candidates[(index + offset) % len(candidates)],
                }
            )

    WINES_PATH.write_text(
        json.dumps({"items": wines}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    USERS_PATH.write_text(
        json.dumps({"users": users}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    LIKES_PATH.write_text(
        json.dumps({"likes": likes}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
