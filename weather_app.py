"""Weather App with Live OpenWeather API.

A beginner-friendly command-line weather application that connects to the
official OpenWeather API to retrieve real-time weather information and a 5-day forecast.
"""

import os
import sys
from typing import Any, Dict, List, Optional
import requests

# API Endpoints
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
REQUEST_TIMEOUT_SECONDS = 10


# ============================================================================
# Custom Exceptions for Beginner-Friendly Error Handling
# ============================================================================

class WeatherAppError(Exception):
    """Base exception for all weather application errors."""
    pass


class MissingAPIKeyError(WeatherAppError):
    """Raised when the OpenWeather API key is not configured."""
    pass


class AuthenticationError(WeatherAppError):
    """Raised when the OpenWeather API rejects the API key (HTTP 401)."""
    pass


class CityNotFoundError(WeatherAppError):
    """Raised when the requested city cannot be found (HTTP 404)."""
    pass


class NetworkError(WeatherAppError):
    """Raised when connection fails or times out."""
    pass


class InvalidResponseError(WeatherAppError):
    """Raised when API response JSON is corrupted or missing expected fields."""
    pass


# ============================================================================
# Core Functions
# ============================================================================

def get_api_key() -> Optional[str]:
    """Retrieve the OpenWeather API key from environment variables or a local .env file.

    Returns:
        Optional[str]: The API key string if found and non-empty, otherwise None.
    """
    # 1. First, check system environment variables
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if api_key and api_key.strip():
        return api_key.strip()

    # 2. Check for a local .env file in the current working directory or script directory
    env_file_paths = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    ]

    for env_path in env_file_paths:
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        # Ignore comments and empty lines
                        if not line or line.startswith("#"):
                            continue
                        if line.startswith("OPENWEATHER_API_KEY="):
                            parts = line.split("=", 1)
                            val = parts[1].strip().strip("\"'")
                            if val and val != "your_api_key_here":
                                return val
            except Exception:
                # If reading .env fails, continue without crashing
                pass

    return None


def validate_city(city: str) -> str:
    """Validate that the city name is not empty or whitespace only.

    Args:
        city: City name provided by the user.

    Returns:
        str: Stripped city name.

    Raises:
        ValueError: If city name is empty or only whitespace.
    """
    if not city or not city.strip():
        raise ValueError("City name cannot be empty. Please enter a valid city name.")
    return city.strip()


def parse_current_weather(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and extract current weather fields from OpenWeather API response JSON.

    Args:
        data: Raw JSON dictionary from the weather endpoint.

    Returns:
        dict: Clean dictionary with weather details.

    Raises:
        InvalidResponseError: If required JSON fields are missing or malformed.
    """
    if not isinstance(data, dict):
        raise InvalidResponseError("Invalid response format: expected a JSON object.")

    try:
        city_name = data.get("name", "")
        country = data.get("sys", {}).get("country", "")
        main_section = data["main"]
        weather_list = data["weather"]

        if not weather_list or not isinstance(weather_list, list):
            raise KeyError("weather")

        weather_first = weather_list[0]

        temp = float(main_section["temp"])
        feels_like = float(main_section["feels_like"])
        humidity = int(main_section["humidity"])
        condition = str(weather_first.get("main", "N/A"))
        description = str(weather_first.get("description", "N/A"))
        wind_speed = float(data.get("wind", {}).get("speed", 0.0))

        return {
            "city": city_name,
            "country": country,
            "temp": temp,
            "feels_like": feels_like,
            "humidity": humidity,
            "condition": condition,
            "description": description,
            "wind_speed": wind_speed,
        }
    except (KeyError, TypeError, ValueError, IndexError) as err:
        raise InvalidResponseError(f"Missing or invalid data in weather response: {err}") from err


def parse_forecast(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse 5-day / 3-hour forecast response into a daily summary (up to 5 days).

    OpenWeather returns 40 records (every 3 hours for 5 days).
    This function groups records by date and selects a representative slot (around 12:00 PM)
    for each day to create a clean, readable 5-day summary.

    Args:
        data: Raw JSON dictionary from the forecast endpoint.

    Returns:
        list of dict: Daily forecast items containing date, temp, condition, humidity.

    Raises:
        InvalidResponseError: If forecast list is missing or invalid.
    """
    if not isinstance(data, dict):
        raise InvalidResponseError("Invalid response format: expected a JSON object.")

    forecast_items = data.get("list")
    if forecast_items is None or not isinstance(forecast_items, list):
        raise InvalidResponseError("Forecast response missing 'list' entries.")

    daily_groups: Dict[str, List[Dict[str, Any]]] = {}

    for entry in forecast_items:
        dt_txt = entry.get("dt_txt", "")
        if " " in dt_txt:
            date_str = dt_txt.split(" ")[0]
        else:
            date_str = dt_txt[:10] if len(dt_txt) >= 10 else "Unknown"

        if date_str not in daily_groups:
            daily_groups[date_str] = []
        daily_groups[date_str].append(entry)

    daily_summary: List[Dict[str, Any]] = []

    for date_str, entries in daily_groups.items():
        # Pick 12:00:00 entry if available; otherwise pick middle entry
        selected_entry = entries[0]
        for item in entries:
            if "12:00:00" in item.get("dt_txt", ""):
                selected_entry = item
                break
        else:
            selected_entry = entries[len(entries) // 2]

        try:
            temp = float(selected_entry["main"]["temp"])
            humidity = int(selected_entry["main"]["humidity"])
            condition = str(selected_entry["weather"][0].get("main", "N/A"))
            daily_summary.append({
                "date": date_str,
                "temp": temp,
                "condition": condition,
                "humidity": humidity,
            })
        except (KeyError, TypeError, ValueError, IndexError) as err:
            raise InvalidResponseError(f"Malformed forecast record for {date_str}: {err}") from err

        if len(daily_summary) == 5:
            break

    return daily_summary


def get_current_weather(city: str, api_key: str) -> Dict[str, Any]:
    """Fetch current weather data for a city using OpenWeather API.

    Args:
        city: Name of the city.
        api_key: OpenWeather API key.

    Returns:
        dict: Parsed current weather details.

    Raises:
        MissingAPIKeyError: If api_key is missing.
        CityNotFoundError: If city is not found (404).
        AuthenticationError: If API key is invalid (401).
        NetworkError: On connection failure or request timeout.
        WeatherAppError: On unexpected HTTP errors.
        InvalidResponseError: On malformed JSON.
    """
    clean_city = validate_city(city)

    if not api_key or not api_key.strip():
        raise MissingAPIKeyError("OpenWeather API key is missing. Please configure OPENWEATHER_API_KEY.")

    params = {
        "q": clean_city,
        "appid": api_key.strip(),
        "units": "metric",
    }

    try:
        response = requests.get(
            CURRENT_WEATHER_URL,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        if response.status_code == 404:
            raise CityNotFoundError(f"City '{clean_city}' was not found. Please check the spelling and try again.")
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed: Invalid or inactive API key. Check OPENWEATHER_API_KEY.")

        response.raise_for_status()

        try:
            json_data = response.json()
        except ValueError as err:
            raise InvalidResponseError("Failed to decode JSON response from OpenWeather API.") from err

        return parse_current_weather(json_data)

    except requests.exceptions.Timeout as err:
        raise NetworkError("Request timed out: The OpenWeather server took too long to respond.") from err
    except requests.exceptions.ConnectionError as err:
        raise NetworkError("Network error: Unable to connect to OpenWeather API. Check your internet connection.") from err
    except requests.exceptions.HTTPError as err:
        raise WeatherAppError(f"HTTP error occurred: {response.status_code} - {response.reason}") from err
    except requests.exceptions.RequestException as err:
        raise NetworkError(f"Network request error: {err}") from err


def get_forecast(city: str, api_key: str) -> List[Dict[str, Any]]:
    """Fetch 5-day / 3-hour forecast for a city using OpenWeather API.

    Args:
        city: Name of the city.
        api_key: OpenWeather API key.

    Returns:
        list of dict: 5-day forecast summary.

    Raises:
        MissingAPIKeyError: If api_key is missing.
        CityNotFoundError: If city is not found (404).
        AuthenticationError: If API key is invalid (401).
        NetworkError: On connection failure or request timeout.
        WeatherAppError: On unexpected HTTP errors.
        InvalidResponseError: On malformed JSON.
    """
    clean_city = validate_city(city)

    if not api_key or not api_key.strip():
        raise MissingAPIKeyError("OpenWeather API key is missing. Please configure OPENWEATHER_API_KEY.")

    params = {
        "q": clean_city,
        "appid": api_key.strip(),
        "units": "metric",
    }

    try:
        response = requests.get(
            FORECAST_URL,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        if response.status_code == 404:
            raise CityNotFoundError(f"City '{clean_city}' was not found for forecast. Check city spelling.")
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed: Invalid or inactive API key. Check OPENWEATHER_API_KEY.")

        response.raise_for_status()

        try:
            json_data = response.json()
        except ValueError as err:
            raise InvalidResponseError("Failed to decode JSON forecast response.") from err

        return parse_forecast(json_data)

    except requests.exceptions.Timeout as err:
        raise NetworkError("Forecast request timed out: OpenWeather server took too long to respond.") from err
    except requests.exceptions.ConnectionError as err:
        raise NetworkError("Network error: Unable to retrieve forecast. Check your internet connection.") from err
    except requests.exceptions.HTTPError as err:
        raise WeatherAppError(f"HTTP error occurred during forecast fetch: {response.status_code}") from err
    except requests.exceptions.RequestException as err:
        raise NetworkError(f"Network request error: {err}") from err


def display_current_weather(data: Dict[str, Any]) -> None:
    """Format and print current weather information to the terminal.

    Args:
        data: Parsed weather dictionary.
    """
    city_str = f"{data['city']}, {data['country']}" if data.get("country") else data.get("city", "Unknown")
    temp_str = f"{round(data['temp'])}°C"
    feels_str = f"{round(data['feels_like'])}°C"
    humidity_str = f"{data['humidity']}%"
    condition_str = data.get("condition", "N/A")
    description_str = data.get("description", "N/A")
    wind_str = f"{data['wind_speed']} m/s"

    print("\n" + "=" * 40)
    print("WEATHER INFORMATION")
    print("=" * 19)
    print(f"\nCity: {city_str}")
    print(f"Temperature: {temp_str}")
    print(f"Feels Like: {feels_str}")
    print(f"Humidity: {humidity_str}")
    print(f"Condition: {condition_str}")
    print(f"Description: {description_str}")
    print(f"Wind Speed: {wind_str}")
    print("\n" + "=" * 40)


def display_forecast(data: List[Dict[str, Any]]) -> None:
    """Format and print 5-day forecast summary in a clean table.

    Args:
        data: List of parsed daily forecast dictionaries.
    """
    if not data:
        print("\nNo forecast data available.")
        return

    print("\n5-Day Forecast\n")
    print(f"{'Date':<14}{'Temperature':<16}{'Condition':<16}{'Humidity':<10}")
    print("-" * 56)

    for item in data:
        date_val = str(item.get("date", "N/A"))
        temp_val = f"{round(item.get('temp', 0))}°C"
        cond_val = str(item.get("condition", "N/A"))
        hum_val = f"{item.get('humidity', 0)}%"
        print(f"{date_val:<14}{temp_val:<16}{cond_val:<16}{hum_val:<10}")

    print("-" * 56)


def print_missing_key_guide() -> None:
    """Print a helpful, beginner-friendly guide when OPENWEATHER_API_KEY is not set."""
    print("\n" + "!" * 58)
    print(" [!] OPENWEATHER_API_KEY NOT CONFIGURED")
    print("!" * 58)
    print("\nThis application requires a free OpenWeather API key to function.")
    print("To obtain your key:")
    print("  1. Sign up for free at: https://openweathermap.org/api")
    print("  2. Navigate to your API keys section and copy your key.\n")
    print("How to set the environment variable:")
    print("  Windows PowerShell:")
    print('    $env:OPENWEATHER_API_KEY="your_api_key_here"')
    print("\n  Windows Command Prompt (CMD):")
    print("    set OPENWEATHER_API_KEY=your_api_key_here")
    print("\n  macOS / Linux Terminal:")
    print('    export OPENWEATHER_API_KEY="your_api_key_here"')
    print("\n  Alternative (.env file):")
    print("    Create a file named '.env' in this directory containing:")
    print("    OPENWEATHER_API_KEY=your_api_key_here")
    print("\n" + "!" * 58 + "\n")


# ============================================================================
# Main Entry Point
# ============================================================================

def main() -> int:
    """Main application loop."""
    print("=" * 50)
    print("     Weather App with Live OpenWeather API")
    print("=" * 50)

    api_key = get_api_key()
    if not api_key:
        print_missing_key_guide()
        return 1

    while True:
        try:
            city_input = input("\nEnter city name (or 'q' to quit): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nOperation cancelled by user. Goodbye!")
            return 0

        if not city_input:
            print("[Error] City name cannot be empty. Please enter a valid city name.")
            continue

        if city_input.lower() in ("q", "quit", "exit"):
            print("Thank you for using Weather App. Goodbye!")
            return 0

        print(f"\nFetching weather details for '{city_input}'...")

        try:
            current_weather = get_current_weather(city_input, api_key)
            forecast = get_forecast(city_input, api_key)

            display_current_weather(current_weather)
            display_forecast(forecast)

        except WeatherAppError as err:
            print(f"\n[Error] {err}")
        except Exception as err:
            print(f"\n[Unexpected Error] An unexpected error occurred: {err}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
