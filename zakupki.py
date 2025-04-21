import requests
from bs4 import BeautifulSoup
import urllib.parse
import re


def parse_user_query(user_input):
    parts = user_input.strip().split()
    query_parts = []
    numbers = []

    for part in parts:
        if part.isdigit():
            numbers.append(int(part))
        else:
            query_parts.append(part)

    query = " ".join(query_parts)
    price_from = None
    price_to = None
    limit = 5

    if len(numbers) == 1:
        price_from = numbers[0]
    elif len(numbers) == 2:
        price_from, price_to = numbers
    elif len(numbers) >= 3:
        price_from, price_to, limit = numbers[:3]

    return query, price_from, price_to, limit


def build_url(query, price_from=None, price_to=None, page=1, limit=5):
    base_url = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html"
    params = {
        "searchString": query,
        "morphology": "on",
        "search-filter": "Дата размещения",
        "monitoringFilter": "off",
        "sortBy": "DATE_CREATED",
        "sortDirection": "false",
        "recordsPerPage": f"_{limit}",
        "showLotsInfoHidden": "false",
        "pageNumber": str(page),
        "fz44": "on",
        "af": "on",
        "currencyIdGeneral": "-1"
    }

    if price_from is not None:
        params["priceFromGeneral"] = str(price_from)
    if price_to is not None:
        params["priceToGeneral"] = str(price_to)

    full_url = f"{base_url}?{urllib.parse.urlencode(params, encoding='utf-8')}"
    return full_url


def fetch_results(url, limit):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Ошибка при загрузке страницы:", response.status_code)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    blocks = soup.find_all("div", class_="search-registry-entry-block")[:limit]
    for block in blocks:
        title_elem = block.find("div", class_="registry-entry__body-href")
        price_elem = block.find("div", class_="price-block__value")
        customer_elem = block.find("div", class_="registry-entry__body-value")

        title = title_elem.get_text(strip=True) if title_elem else "Без названия"
        price = price_elem.get_text(strip=True) if price_elem else "Цена не указана"
        customer = customer_elem.get_text(strip=True) if customer_elem else "Заказчик не указан"

        # Вытаскиваем regNumber из блока с помощью регулярки
        reg_number_match = re.search(r'regNumber=(\d+)', str(block))
        reg_number = reg_number_match.group(1) if reg_number_match else None

        if reg_number:
            link = f"https://zakupki.gov.ru/epz/order/notice/ea20/view/common-info.html?regNumber={reg_number}"
        else:
            link = "Регистрационный номер не найден"

        results.append({
            "Наименование": title,
            "Цена": price,
            "Заказчик": customer,
            "Ссылка": link
        })

    return results


def search_purchases(user_input):
    query, price_from, price_to, limit = parse_user_query(user_input)
    url = build_url(query, price_from, price_to, page=1, limit=limit)
    print("🔎 Поиск по ссылке:", url)
    results = fetch_results(url, limit)

    if not results:
        print("❌ Ничего не найдено.")
        return

    for i, res in enumerate(results, 1):
        print(f"\n📌 Результат {i}:")
        print(f"🔹 Наименование: {res['Наименование']}")
        print(f"💰 Цена: {res['Цена']}")
        print(f"🏢 Заказчик: {res['Заказчик']}")
        print(f"🔗 Ссылка: {res['Ссылка']}")


# Пример запуска:
if __name__ == "__main__":
    user_input = input("Введите запрос: ")
    search_purchases(user_input)
