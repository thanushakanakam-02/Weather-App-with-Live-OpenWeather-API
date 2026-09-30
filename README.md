# Weather App with Live OpenWeather API

A clean, beginner-friendly Python command-line application that integrates with the official OpenWeather REST API to retrieve real-time weather metrics and 5-day weather forecasts for any city across the globe.

---

## 📌 Project Overview

This project was developed as an online internship demonstration of core backend engineering skills in Python:
* Integrating with third-party RESTful APIs using HTTP requests.
* Securely handling API authentication credentials using environment variables.
* Parsing structured JSON payloads using dictionary and list data structures.
* Designing user-friendly command-line interfaces (CLI) with defensive error handling.
* Writing modular, testable code accompanied by unit tests using mocking techniques.

---

## 🎯 Objectives

* Connect Python to the official **OpenWeather API** via HTTP `GET` requests.
* Query both the **Current Weather API** and the **5-Day / 3-Hour Forecast API**.
* Prevent security vulnerabilities by keeping API keys out of source code, test files, and Git history.
* Gracefully catch and handle network issues, invalid user input, expired/invalid keys, and non-existent cities without crashing.
* Present live weather data and forecast summaries in clean terminal tables.

---

## ✨ Features

1. **City Input & Validation**:
   * Prompts the user to enter any city name (e.g., `Hyderabad`, `London`, `Tokyo`).
   * Validates input to prevent blank or whitespace-only submissions.
   * Offers a simple `'q'` command to quit the program cleanly at any time.

2. **Current Weather Retrieval**:
   * **City & Country**: City name and international country code (e.g., `Hyderabad, IN`).
   * **Temperature**: Live temperature converted and displayed in Celsius (°C).
   * **Feels Like**: Apparent temperature accounting for humidity and wind.
   * **Humidity**: Relative atmospheric humidity percentage (%).
   * **Condition & Description**: Primary condition (e.g., `Clouds`) and descriptive detail (e.g., `scattered clouds`).
   * **Wind Speed**: Wind velocity measured in meters per second (`m/s`).

3. **5-Day Weather Forecast**:
   * Groups 3-hour forecast data records by date.
   * Extracts a representative midday (12:00 PM) forecast for up to 5 consecutive days.
   * Formats the forecast into a structured, readable terminal summary table showing Date, Temperature, Condition, and Humidity.

4. **Robust Error Handling**:
   * Handles missing API keys before making unnecessary API calls.
   * Gracefully alerts the user if an invalid API key is provided (`HTTP 401`).
   * Informs the user when a city cannot be found (`HTTP 404`) and prompts for another try.
   * Catches network connection drops, timeouts (10-second threshold), and malformed responses.

---

## 🛠️ Technologies Used

* **Language**: Python 3.8+
* **HTTP Library**: `requests` (for REST API communication)
* **Testing Framework**: `unittest` and `unittest.mock` (Python standard library)
* **Configuration**: `os` and `os.environ` for secure environment variable management

---

## 🌐 OpenWeather API Endpoints

This application connects to the official OpenWeather API v2.5:

1. **Current Weather Endpoint**:
   ```
   https://api.openweathermap.org/data/2.5/weather
   ```
   * Parameters:
     * `q`: Target city name (e.g., `London`).
     * `appid`: User's private OpenWeather API key.
     * `units`: Set to `metric` for temperatures in Celsius and wind speed in m/s.

2. **5-Day / 3-Hour Forecast Endpoint**:
   ```
   https://api.openweathermap.org/data/2.5/forecast
   ```
   * Parameters:
     * `q`: Target city name.
     * `appid`: User's private OpenWeather API key.
     * `units`: Set to `metric`.

---

## 💡 How REST API Integration Works

1. **Client-Server Architecture**:
   The Python application acts as an HTTP client. It initiates an HTTP `GET` request to OpenWeather's servers with the city name, metric unit preferences, and API key.

2. **Status Codes & Response Handling**:
   * `200 OK`: Request succeeded; JSON response is parsed and rendered.
   * `401 Unauthorized`: API key is invalid or pending activation.
   * `404 Not Found`: OpenWeather has no data for the requested city.
   * Network Timeouts / Connection Errors: Caught via `requests.exceptions.RequestException`.

---

## 🔍 How JSON Response Parsing Works

OpenWeather returns structured JSON responses that Python deserializes into native dictionaries and lists:

### Current Weather Response Structure
```json
{
  "name": "Hyderabad",
  "sys": { "country": "IN" },
  "main": {
    "temp": 28.4,
    "feels_like": 30.1,
    "humidity": 65
  },
  "weather": [
    {
      "main": "Clouds",
      "description": "scattered clouds"
    }
  ],
  "wind": {
    "speed": 3.5
  }
}
```

The application extracts fields defensively:
* City name: `data.get("name")`
* Country: `data.get("sys", {}).get("country")`
* Temperature: `data["main"]["temp"]`
* Condition: `data["weather"][0]["main"]`
* Wind Speed: `data.get("wind", {}).get("speed")`

### Forecast Parsing Logic
The forecast API returns 40 records (every 3 hours over 5 days). Rather than flooding the terminal, the `parse_forecast()` function:
1. Groups records by calendar date (`YYYY-MM-DD`).
2. Selects the 12:00 PM entry (or the nearest representative daytime entry) for each date.
3. Produces a 5-row summary table for the week.

---

## 🔒 API Key & Environment Variable Setup

> **IMPORTANT**: A personal OpenWeather API key is required to query live data. **Never** hardcode or commit your API key to Git!

### Step 1: Obtain a Free API Key
1. Visit [OpenWeather Sign Up](https://openweathermap.org/appid) and create a free account.
2. Go to **API keys** in your account dashboard and copy your generated key.
3. *(Note: New OpenWeather keys typically take 10 to 60 minutes to activate on their servers).*

### Step 2: Configure the Environment Variable

#### Option A: Windows PowerShell (Recommended on Windows)
```powershell
$env:OPENWEATHER_API_KEY="your_actual_api_key_here"
```

#### Option B: Windows Command Prompt (CMD)
```cmd
set OPENWEATHER_API_KEY=your_actual_api_key_here
```

#### Option C: macOS / Linux Terminal
```bash
export OPENWEATHER_API_KEY="your_actual_api_key_here"
```

#### Option D: Using a `.env` file
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` in an editor and replace `your_api_key_here` with your real key:
   ```ini
   OPENWEATHER_API_KEY=your_actual_api_key_here
   ```
   *(The `.gitignore` file is pre-configured to ensure `.env` is never committed).*

---

## 🚀 Installation & Running

### 1. Clone or Open the Repository
```bash
cd "weather app"
```

### 2. (Optional) Create and Activate a Virtual Environment
```bash
# On Windows:
python -m venv venv
.\venv\Scripts\activate

# On macOS/Linux:
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python weather_app.py
```

---

## 🖥️ Example Output

### Live Weather & Forecast Run
```text
==================================================
     Weather App with Live OpenWeather API
==================================================

Enter city name (or 'q' to quit): Hyderabad

Fetching weather details for 'Hyderabad'...

========================================
WEATHER INFORMATION
===================

City: Hyderabad, IN
Temperature: 28°C
Feels Like: 30°C
Humidity: 65%
Condition: Clouds
Description: scattered clouds
Wind Speed: 3.5 m/s

========================================

5-Day Forecast

Date          Temperature     Condition       Humidity  
--------------------------------------------------------
2026-10-01    27°C            Clouds          68%       
2026-10-02    29°C            Clear           50%       
2026-10-03    26°C            Rain            80%       
2026-10-04    25°C            Rain            75%       
2026-10-05    28°C            Clouds          55%       
--------------------------------------------------------

Enter city name (or 'q' to quit): q
Thank you for using Weather App. Goodbye!
```

### Missing API Key Prompt
If the application is launched without an API key configured:
```text
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
 [!] OPENWEATHER_API_KEY NOT CONFIGURED
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

This application requires a free OpenWeather API key to function.
To obtain your key:
  1. Sign up for free at: https://openweathermap.org/api
  2. Navigate to your API keys section and copy your key.

How to set the environment variable:
  Windows PowerShell:
    $env:OPENWEATHER_API_KEY="your_api_key_here"
...
```

---

## 🧪 Running Unit Tests

The test suite in [test_weather_app.py](test_weather_app.py) uses Python's built-in `unittest` framework and mocks all API responses so tests run completely offline and never expose secrets.

Run the test suite:
```bash
python -m unittest test_weather_app.py -v
```

### Test Coverage Highlights
* Missing API key handling.
* Empty and whitespace-only city validation.
* Successful current weather JSON parsing.
* 5-day / 3-hour forecast aggregation and midday selection.
* HTTP 404 (City Not Found) response handling.
* HTTP 401 (Invalid/Unauthorized API Key) response handling.
* Network connection failure and timeout handling.
* Malformed JSON decoding and missing field validation.
* Extraction accuracy for temperatures, humidity, and wind speed.
* Terminal formatting and clean interactive loop exits.
* Conditional live test that only executes if a real API key is configured.

---

## 🛡️ Security Best Practices

* **No Hardcoded Secrets**: Secrets are never hardcoded in source code or documentation.
* **Ignored Environment Files**: The `.gitignore` file excludes `.env`, `*.pyc`, `venv/`, and cache directories.
* **Offline Mocked Tests**: Unit tests use `unittest.mock.patch` to simulate API behavior without making network calls or exposing keys.

---

## 📚 Learning Outcomes

Through building this project, the following skills were practiced and demonstrated:
1. **API Integration**: Using Python's `requests` library to interact with real-world RESTful web services.
2. **Data Manipulation**: Parsing nested dictionaries and lists in JSON format.
3. **Defensive Programming**: Managing edge cases like invalid input, HTTP errors, timeouts, and network outages.
4. **Application Security**: Safely handling API credentials with environment variables and Git protections.
5. **Software Testing**: Implementing unit tests with `unittest.mock` to ensure software reliability and test isolation.
