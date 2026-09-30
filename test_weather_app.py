"""Unit and Integration Tests for Weather App with Live OpenWeather API.

Uses Python's built-in unittest and unittest.mock to test all application functionality
without exposing secrets or requiring external network calls during unit testing.
"""

import io
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import requests

from weather_app import (
    AuthenticationError,
    CityNotFoundError,
    InvalidResponseError,
    MissingAPIKeyError,
    NetworkError,
    WeatherAppError,
    display_current_weather,
    display_forecast,
    get_api_key,
    get_current_weather,
    get_forecast,
    main,
    parse_current_weather,
    parse_forecast,
    print_missing_key_guide,
    validate_city,
)


# Sample Mock Payloads based on official OpenWeather API v2.5
MOCK_CURRENT_WEATHER_RAW = {
    "coord": {"lon": 78.4744, "lat": 17.3753},
    "weather": [
        {
            "id": 802,
            "main": "Clouds",
            "description": "scattered clouds",
            "icon": "03d",
        }
    ],
    "base": "stations",
    "main": {
        "temp": 28.4,
        "feels_like": 30.1,
        "temp_min": 28.0,
        "temp_max": 29.0,
        "pressure": 1012,
        "humidity": 65,
    },
    "visibility": 6000,
    "wind": {"speed": 3.5, "deg": 120},
    "clouds": {"all": 40},
    "dt": 1727770000,
    "sys": {
        "type": 1,
        "id": 9214,
        "country": "IN",
        "sunrise": 1727743200,
        "sunset": 1727786400,
    },
    "timezone": 19800,
    "id": 1269843,
    "name": "Hyderabad",
    "cod": 200,
}

MOCK_FORECAST_RAW = {
    "cod": "200",
    "message": 0,
    "cnt": 8,
    "list": [
        {
            "dt": 1727784000,
            "main": {"temp": 27.2, "humidity": 68},
            "weather": [{"main": "Clouds", "description": "broken clouds"}],
            "dt_txt": "2026-10-01 09:00:00",
        },
        {
            "dt": 1727794800,
            "main": {"temp": 28.0, "humidity": 60},
            "weather": [{"main": "Clouds", "description": "scattered clouds"}],
            "dt_txt": "2026-10-01 12:00:00",
        },
        {
            "dt": 1727881200,
            "main": {"temp": 29.5, "humidity": 50},
            "weather": [{"main": "Clear", "description": "clear sky"}],
            "dt_txt": "2026-10-02 12:00:00",
        },
        {
            "dt": 1727967600,
            "main": {"temp": 26.1, "humidity": 80},
            "weather": [{"main": "Rain", "description": "moderate rain"}],
            "dt_txt": "2026-10-03 12:00:00",
        },
        {
            "dt": 1728054000,
            "main": {"temp": 25.0, "humidity": 75},
            "weather": [{"main": "Rain", "description": "light rain"}],
            "dt_txt": "2026-10-04 12:00:00",
        },
        {
            "dt": 1728140400,
            "main": {"temp": 27.8, "humidity": 55},
            "weather": [{"main": "Clouds", "description": "few clouds"}],
            "dt_txt": "2026-10-05 12:00:00",
        },
        {
            "dt": 1728226800,
            "main": {"temp": 30.1, "humidity": 45},
            "weather": [{"main": "Clear", "description": "clear sky"}],
            "dt_txt": "2026-10-06 12:00:00",
        },
    ],
    "city": {
        "id": 1269843,
        "name": "Hyderabad",
        "coord": {"lat": 17.3753, "lon": 78.4744},
        "country": "IN",
    },
}


class TestWeatherApp(unittest.TestCase):
    """Unit test suite for Weather App."""

    # ------------------------------------------------------------------------
    # 1. Missing API Key Tests
    # ------------------------------------------------------------------------
    def test_get_api_key_missing(self):
        """Verify get_api_key returns None when OPENWEATHER_API_KEY is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.isfile", return_value=False):
                api_key = get_api_key()
                self.assertIsNone(api_key)

    def test_get_current_weather_missing_api_key(self):
        """Verify get_current_weather raises MissingAPIKeyError if key is empty."""
        with self.assertRaises(MissingAPIKeyError):
            get_current_weather("London", "")

    def test_get_forecast_missing_api_key(self):
        """Verify get_forecast raises MissingAPIKeyError if key is whitespace only."""
        with self.assertRaises(MissingAPIKeyError):
            get_forecast("London", "   ")

    # ------------------------------------------------------------------------
    # 2. Empty City Input Tests
    # ------------------------------------------------------------------------
    def test_validate_city_empty_string(self):
        """Verify validate_city raises ValueError on empty input."""
        with self.assertRaises(ValueError):
            validate_city("")

    def test_validate_city_whitespace(self):
        """Verify validate_city raises ValueError on whitespace only."""
        with self.assertRaises(ValueError):
            validate_city("   ")

    def test_get_current_weather_empty_city(self):
        """Verify get_current_weather rejects empty city name before network call."""
        with self.assertRaises(ValueError):
            get_current_weather("   ", "dummy_key")

    # ------------------------------------------------------------------------
    # 3. Successful Current Weather Response
    # ------------------------------------------------------------------------
    @patch("requests.get")
    def test_get_current_weather_success(self, mock_get):
        """Verify get_current_weather parses valid response into expected dictionary."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_CURRENT_WEATHER_RAW
        mock_get.return_value = mock_response

        result = get_current_weather("Hyderabad", "mock_key_123")

        self.assertEqual(result["city"], "Hyderabad")
        self.assertEqual(result["country"], "IN")
        self.assertAlmostEqual(result["temp"], 28.4)
        self.assertAlmostEqual(result["feels_like"], 30.1)
        self.assertEqual(result["humidity"], 65)
        self.assertEqual(result["condition"], "Clouds")
        self.assertEqual(result["description"], "scattered clouds")
        self.assertEqual(result["wind_speed"], 3.5)

    # ------------------------------------------------------------------------
    # 4. Successful Forecast Response
    # ------------------------------------------------------------------------
    @patch("requests.get")
    def test_get_forecast_success(self, mock_get):
        """Verify get_forecast returns 5-day daily forecast summary."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_FORECAST_RAW
        mock_get.return_value = mock_response

        forecast_list = get_forecast("Hyderabad", "mock_key_123")

        self.assertIsInstance(forecast_list, list)
        self.assertEqual(len(forecast_list), 5)  # Capped at 5 days
        self.assertEqual(forecast_list[0]["date"], "2026-10-01")
        self.assertEqual(forecast_list[0]["condition"], "Clouds")
        self.assertEqual(forecast_list[1]["date"], "2026-10-02")
        self.assertEqual(forecast_list[1]["condition"], "Clear")

    # ------------------------------------------------------------------------
    # 5. City Not Found / HTTP 404
    # ------------------------------------------------------------------------
    @patch("requests.get")
    def test_city_not_found_current_weather(self, mock_get):
        """Verify 404 response raises CityNotFoundError for current weather."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with self.assertRaises(CityNotFoundError):
            get_current_weather("NonExistentCityXYZ", "mock_key_123")

    @patch("requests.get")
    def test_city_not_found_forecast(self, mock_get):
        """Verify 404 response raises CityNotFoundError for forecast."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with self.assertRaises(CityNotFoundError):
            get_forecast("NonExistentCityXYZ", "mock_key_123")

    # ------------------------------------------------------------------------
    # 6. Invalid API Key / HTTP 401
    # ------------------------------------------------------------------------
    @patch("requests.get")
    def test_invalid_api_key_current_weather(self, mock_get):
        """Verify 401 response raises AuthenticationError for current weather."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        with self.assertRaises(AuthenticationError):
            get_current_weather("Paris", "invalid_api_key_example")

    @patch("requests.get")
    def test_invalid_api_key_forecast(self, mock_get):
        """Verify 401 response raises AuthenticationError for forecast."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        with self.assertRaises(AuthenticationError):
            get_forecast("Paris", "invalid_api_key_example")

    # ------------------------------------------------------------------------
    # 7. Network Connection Error
    # ------------------------------------------------------------------------
    @patch("requests.get")
    def test_network_connection_error(self, mock_get):
        """Verify ConnectionError raises user-friendly NetworkError."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with self.assertRaises(NetworkError) as context:
            get_current_weather("Tokyo", "mock_key_123")
        self.assertIn("internet connection", str(context.exception).lower())

    # ------------------------------------------------------------------------
    # 8. Request Timeout
    # ------------------------------------------------------------------------
    @patch("requests.get")
    def test_request_timeout(self, mock_get):
        """Verify request Timeout raises user-friendly NetworkError."""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        with self.assertRaises(NetworkError) as context:
            get_current_weather("Tokyo", "mock_key_123")
        self.assertIn("timed out", str(context.exception).lower())

    # ------------------------------------------------------------------------
    # 9. Invalid / Unexpected JSON Response
    # ------------------------------------------------------------------------
    @patch("requests.get")
    def test_invalid_json_decode_error(self, mock_get):
        """Verify JSON decoding failure raises InvalidResponseError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        with self.assertRaises(InvalidResponseError):
            get_current_weather("Berlin", "mock_key_123")

    def test_missing_json_fields_current_weather(self):
        """Verify missing 'main' or 'weather' raises InvalidResponseError."""
        malformed_data = {"name": "TestCity"}
        with self.assertRaises(InvalidResponseError):
            parse_current_weather(malformed_data)

    def test_missing_json_fields_forecast(self):
        """Verify missing 'list' in forecast raises InvalidResponseError."""
        malformed_data = {"cod": "200"}
        with self.assertRaises(InvalidResponseError):
            parse_forecast(malformed_data)

    # ------------------------------------------------------------------------
    # 10. Temperature and Humidity Extraction
    # ------------------------------------------------------------------------
    def test_temperature_and_humidity_extraction(self):
        """Verify exact temperature and humidity numerical extraction."""
        data = {
            "name": "Mumbai",
            "sys": {"country": "IN"},
            "main": {"temp": 32.7, "feels_like": 36.2, "humidity": 78},
            "weather": [{"main": "Haze", "description": "haze"}],
            "wind": {"speed": 4.1},
        }
        parsed = parse_current_weather(data)
        self.assertAlmostEqual(parsed["temp"], 32.7)
        self.assertAlmostEqual(parsed["feels_like"], 36.2)
        self.assertEqual(parsed["humidity"], 78)
        self.assertEqual(parsed["city"], "Mumbai")

    # ------------------------------------------------------------------------
    # 11. Forecast Data Parsing
    # ------------------------------------------------------------------------
    def test_forecast_parsing_representative_slot(self):
        """Verify that parse_forecast picks the 12:00:00 midday slot when available."""
        forecast_payload = {
            "list": [
                {
                    "dt_txt": "2026-10-10 06:00:00",
                    "main": {"temp": 18.0, "humidity": 90},
                    "weather": [{"main": "Mist", "description": "mist"}],
                },
                {
                    "dt_txt": "2026-10-10 12:00:00",
                    "main": {"temp": 24.0, "humidity": 55},
                    "weather": [{"main": "Sun", "description": "clear"}],
                },
                {
                    "dt_txt": "2026-10-10 18:00:00",
                    "main": {"temp": 20.0, "humidity": 70},
                    "weather": [{"main": "Clear", "description": "clear"}],
                },
            ]
        }
        daily = parse_forecast(forecast_payload)
        self.assertEqual(len(daily), 1)
        self.assertEqual(daily[0]["date"], "2026-10-10")
        self.assertAlmostEqual(daily[0]["temp"], 24.0)
        self.assertEqual(daily[0]["humidity"], 55)
        self.assertEqual(daily[0]["condition"], "Sun")

    # ------------------------------------------------------------------------
    # 12. Application Display and Main Functions
    # ------------------------------------------------------------------------
    def test_display_current_weather_output(self):
        """Verify display_current_weather produces clean formatted output."""
        data = {
            "city": "Hyderabad",
            "country": "IN",
            "temp": 28.0,
            "feels_like": 30.0,
            "humidity": 65,
            "condition": "Clouds",
            "description": "scattered clouds",
            "wind_speed": 3.5,
        }
        buffer = io.StringIO()
        with patch("sys.stdout", buffer):
            display_current_weather(data)
        output = buffer.getvalue()

        self.assertIn("WEATHER INFORMATION", output)
        self.assertIn("City: Hyderabad, IN", output)
        self.assertIn("Temperature: 28°C", output)
        self.assertIn("Feels Like: 30°C", output)
        self.assertIn("Humidity: 65%", output)
        self.assertIn("Wind Speed: 3.5 m/s", output)

    def test_display_forecast_output(self):
        """Verify display_forecast prints table with headers."""
        data = [
            {"date": "2026-10-01", "temp": 27.0, "condition": "Clouds", "humidity": 65},
            {"date": "2026-10-02", "temp": 29.0, "condition": "Clear", "humidity": 50},
        ]
        buffer = io.StringIO()
        with patch("sys.stdout", buffer):
            display_forecast(data)
        output = buffer.getvalue()

        self.assertIn("5-Day Forecast", output)
        self.assertIn("Date", output)
        self.assertIn("Temperature", output)
        self.assertIn("Condition", output)
        self.assertIn("2026-10-01", output)
        self.assertIn("27°C", output)

    def test_main_missing_key_exit(self):
        """Verify main() exits with code 1 when API key is missing."""
        with patch("weather_app.get_api_key", return_value=None):
            buffer = io.StringIO()
            with patch("sys.stdout", buffer):
                exit_code = main()
            self.assertEqual(exit_code, 1)
            self.assertIn("OPENWEATHER_API_KEY NOT CONFIGURED", buffer.getvalue())

    def test_main_quit_command(self):
        """Verify main() quits gracefully when user enters 'q'."""
        with patch("weather_app.get_api_key", return_value="dummy_key_123"):
            with patch("builtins.input", return_value="q"):
                buffer = io.StringIO()
                with patch("sys.stdout", buffer):
                    exit_code = main()
                self.assertEqual(exit_code, 0)
                self.assertIn("Goodbye", buffer.getvalue())


# ============================================================================
# Live API Integration Test (Conditionally Executed)
# ============================================================================

class TestLiveOpenWeatherAPI(unittest.TestCase):
    """Live API test executed only when a real OPENWEATHER_API_KEY is configured in the environment.

    NEVER logs or exposes the API key.
    """

    @unittest.skipUnless(
        os.environ.get("OPENWEATHER_API_KEY") and os.environ.get("OPENWEATHER_API_KEY").strip(),
        "Live OpenWeather API key not found in environment. Skipping live test.",
    )
    def test_live_api_call(self):
        """Validate live API integration against OpenWeather service."""
        api_key = os.environ.get("OPENWEATHER_API_KEY").strip()
        # Query a well-known city
        test_city = "London"

        current = get_current_weather(test_city, api_key)
        self.assertIsInstance(current, dict)
        self.assertEqual(current["city"].lower(), "london")
        self.assertIn("temp", current)
        self.assertIn("humidity", current)

        forecast = get_forecast(test_city, api_key)
        self.assertIsInstance(forecast, list)
        self.assertGreater(len(forecast), 0)
        self.assertIn("temp", forecast[0])
        self.assertIn("condition", forecast[0])


if __name__ == "__main__":
    unittest.main()
