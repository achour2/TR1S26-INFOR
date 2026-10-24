"""Clients serveur pour Open-Meteo et l'API Countries GraphQL."""

import json
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


TIMEOUT_SECONDS = 5
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
COUNTRIES_GRAPHQL_URL = "https://countries.trevorblades.com/"


class ServiceError(Exception):
    """Erreur contrôlée lors d'un appel à un service tiers."""


def _request_json(url, *, params=None, payload=None):
    if params:
        url = f"{url}?{urlencode(params)}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=data,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "TravelHub/1.0",
        },
        method="POST" if data is not None else "GET",
    )
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise ServiceError("Le service externe est temporairement indisponible.") from exc
    if not isinstance(result, dict):
        raise ServiceError("Le service externe a retourné une réponse invalide.")
    return result


def _geocode(destination):
    result = _request_json(
        GEOCODING_URL,
        params={
            "name": f"{destination.ville}, {destination.pays}",
            "count": 10,
            "language": "fr",
            "format": "json",
        },
    )
    locations = result.get("results") or []
    if not locations:
        return None

    city = destination.ville.casefold().strip()
    location = next(
        (item for item in locations if item.get("name", "").casefold() == city),
        locations[0],
    )
    if "latitude" not in location or "longitude" not in location:
        raise ServiceError("Aucune coordonnée n'a été fournie pour cette destination.")
    return {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "country_code": location.get("country_code", "").upper(),
        "timezone": location.get("timezone"),
        "locality": location.get("name", destination.ville),
    }


WEATHER_CODES = {
    0: "Ciel dégagé",
    1: "Principalement dégagé",
    2: "Partiellement nuageux",
    3: "Couvert",
    45: "Brouillard",
    48: "Brouillard givrant",
    51: "Bruine légère",
    53: "Bruine modérée",
    55: "Bruine dense",
    56: "Bruine verglaçante légère",
    57: "Bruine verglaçante dense",
    61: "Pluie légère",
    63: "Pluie modérée",
    65: "Forte pluie",
    66: "Pluie verglaçante légère",
    67: "Forte pluie verglaçante",
    71: "Faibles chutes de neige",
    73: "Chutes de neige modérées",
    75: "Fortes chutes de neige",
    77: "Grains de neige",
    80: "Averses légères",
    81: "Averses modérées",
    82: "Fortes averses",
    85: "Averses de neige légères",
    86: "Fortes averses de neige",
    95: "Orage",
    96: "Orage avec grêle légère",
    99: "Orage avec forte grêle",
}


def _weather(destination, coordinates):
    today = date.today()
    first_available_day = today - timedelta(days=92)
    last_available_day = today + timedelta(days=15)
    start = max(destination.date_Arrive, first_available_day)
    end = min(destination.date_Depart, last_available_day)
    if start > end:
        return {
            "status": "unavailable",
            "message": "Les prévisions ne sont pas encore disponibles pour ces dates. Open-Meteo fournit des prévisions jusqu'à 16 jours.",
            "days": [],
        }

    result = _request_json(
        WEATHER_URL,
        params={
            "latitude": coordinates["latitude"],
            "longitude": coordinates["longitude"],
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "timezone": coordinates.get("timezone") or "auto",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        },
    )
    daily = result.get("daily") or {}
    dates = daily.get("time") or []
    days = []
    for index, day in enumerate(dates):
        if not (destination.date_Arrive.isoformat() <= day <= destination.date_Depart.isoformat()):
            continue
        code = _value_at(daily, "weather_code", index)
        days.append({
            "date": day,
            "condition": WEATHER_CODES.get(code, "Conditions variables"),
            "temperature_max": _value_at(daily, "temperature_2m_max", index),
            "temperature_min": _value_at(daily, "temperature_2m_min", index),
            "precipitation": _value_at(daily, "precipitation_sum", index),
            "wind_speed": _value_at(daily, "wind_speed_10m_max", index),
        })
    return {
        "status": "ok" if days else "unavailable",
        "message": "" if days else "Aucune donnée météo n'est disponible pour les dates du séjour.",
        "temperature_unit": result.get("daily_units", {}).get("temperature_2m_max", "°C"),
        "precipitation_unit": result.get("daily_units", {}).get("precipitation_sum", "mm"),
        "wind_unit": result.get("daily_units", {}).get("wind_speed_10m_max", "km/h"),
        "days": days,
    }


def _value_at(data, key, index):
    values = data.get(key) or []
    return values[index] if index < len(values) else None


def _country_info(country_code):
    if not country_code:
        return None
    query = """
    query CountryDetails($code: ID!) {
      country(code: $code) {
        name
        capital
        continent { name }
        currency
        languages { name }
      }
    }
    """
    result = _request_json(
        COUNTRIES_GRAPHQL_URL,
        payload={"query": query, "variables": {"code": country_code}},
    )
    if result.get("errors"):
        raise ServiceError("Les informations du pays ne sont pas disponibles.")
    country = (result.get("data") or {}).get("country")
    if not country:
        return None
    continent = country.get("continent") or {}
    return {
        "name": country.get("name"),
        "capital": country.get("capital"),
        "continent": continent.get("name"),
        "currency": country.get("currency"),
        "languages": [language.get("name") for language in country.get("languages", []) if language.get("name")],
    }


def destination_enrichment(destination):
    """Combine les données locales, le géocodage, la météo et les données du pays."""
    enrichment = {
        "coordinates": None,
        "weather": {"status": "error", "message": "Informations météo indisponibles.", "days": []},
        "country_info": None,
        "country_error": "",
        "location_error": "",
    }
    try:
        coordinates = _geocode(destination)
        if coordinates is None:
            enrichment["location_error"] = "Destination introuvable dans le service de géocodage."
            enrichment["weather"] = {
                "status": "unavailable",
                "message": "La météo ne peut pas être recherchée sans coordonnées.",
                "days": [],
            }
            return enrichment
        enrichment["coordinates"] = coordinates
    except ServiceError as exc:
        enrichment["location_error"] = str(exc)
        enrichment["weather"]["message"] = str(exc)
        return enrichment

    try:
        enrichment["weather"] = _weather(destination, coordinates)
    except ServiceError as exc:
        enrichment["weather"] = {"status": "error", "message": str(exc), "days": []}

    try:
        enrichment["country_info"] = _country_info(coordinates["country_code"])
        if enrichment["country_info"] is None:
            enrichment["country_error"] = "Pays non trouvé dans le service Countries GraphQL."
    except ServiceError as exc:
        enrichment["country_error"] = str(exc)
    return enrichment
