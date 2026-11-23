import requests


def fetch_weather(city: str) -> None:
    # Step 1: Convert city name to latitude and longitude using requests.get()
    geo_response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=10,
    )
    geo_response.raise_for_status()
    geo_data = geo_response.json()

    if not geo_data.get("results"):
        print(f"City not found: {city}")
        return

    place = geo_data["results"][0]
    lat = place["latitude"]
    lon = place["longitude"]
    city_name = place["name"]
    country = place.get("country", "")

    # Step 2: Fetch current weather for those coordinates using requests.get()
    weather_response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "timezone": "auto",
        },
        timeout=10,
    )
    weather_response.raise_for_status()
    current = weather_response.json()["current"]

    print(f"\nWeather in {city_name}, {country}")
    print(f"Temperature : {current['temperature_2m']} °C")
    print(f"Humidity    : {current['relative_humidity_2m']}%")
    print(f"Wind Speed  : {current['wind_speed_10m']} km/h")


if __name__ == "__main__":
    city_input = input("Enter city name: ").strip()
    if city_input:
        try:
            fetch_weather(city_input)
        except requests.exceptions.RequestException as error:
            print(f"Request failed: {error}")
    else:
        print("Please enter a valid city name.")