from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import requests
import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")
GOOGLE_KEY = os.getenv("GOOGLE_KEY")


# ───────────────────────────────────────────
# 한국어 도시명 → 위도/경도 변환
# ───────────────────────────────────────────
def geocode_city(city: str) -> dict:
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": city, "key": GOOGLE_KEY, "language": "en"}
    resp = requests.get(url, params=params)
    data = resp.json()

    status = data.get("status")
    if status != "OK" or not data.get("results"):
        print(f"[Geocoding 실패] status={status}, input={city}, message={data.get('error_message', '')}")
        raise HTTPException(status_code=404, detail=f"도시를 찾을 수 없어요: {city} (status={status})")

    result = data["results"][0]
    location = result["geometry"]["location"]
    lat = location["lat"]
    lng = location["lng"]

    city_name = None
    country = ""
    for component in result["address_components"]:
        types = component["types"]
        if "locality" in types and not city_name:
            city_name = component["long_name"]
        if "administrative_area_level_1" in types and not city_name:
            city_name = component["long_name"]
        if "country" in types:
            country = component["short_name"]

    if not city_name:
        city_name = result.get("formatted_address", city).split(",")[0].strip()

    print(f"[Geocoding 성공] input={city} → city={city_name}, country={country}, lat={lat}, lng={lng}")
    return {"lat": lat, "lng": lng, "city": city_name, "country": country}


# ───────────────────────────────────────────
# 복합 조건 기반 의류 추천
# ───────────────────────────────────────────
def get_detailed_recommendations(
    temp: float,
    wind_speed: float,
    clouds: int,
    weather_id: int,
    timezone_offset: int,  # UTC 오프셋 (초 단위)
) -> dict:
    """
    온도 · 바람 · 강수(weather_id) · 구름량 · 현지 시간대를 복합 고려해
    기본 옷차림 + 추가 조언 목록을 반환합니다.

    weather_id 분류:
      2xx = 천둥번개, 3xx = 이슬비, 5xx = 비, 6xx = 눈, 7xx = 안개/황사, 800 = 맑음, 8xx = 구름
    """

    # 현지 시각 계산
    local_time = datetime.now(timezone.utc) + timedelta(seconds=timezone_offset)
    current_hour = local_time.hour

    # ── 기본 옷차림 (온도 기반) ──
    if temp >= 28:
        base = "민소매나 반팔"
        icon = "shirt"
    elif temp >= 23:
        base = "반팔"
        icon = "shirt"
    elif temp >= 17:
        base = "얇은 가디건이나 긴팔"
        icon = "jacket"
    elif temp >= 12:
        base = "자켓이나 가벼운 코트"
        icon = "jacket"
    elif temp >= 5:
        base = "두꺼운 코트와 목도리"
        icon = "coat"
    else:
        base = "패딩과 장갑"
        icon = "coat"

    tips = []

    # ── 강수 조건 ──
    if 200 <= weather_id < 300:
        tips.append("천둥번개가 예보돼 있어요. 우산을 꼭 챙기고 가급적 실내에 머무르세요!")
    elif 300 <= weather_id < 400:
        tips.append("이슬비가 내리고 있어요. 접이식 우산이나 방수 재킷을 챙기세요.")
    elif 500 <= weather_id < 600:
        if weather_id in (502, 503, 504, 522):
            tips.append("강한 비가 예보돼 있어요. 우산과 방수 신발을 꼭 챙기세요!")
        else:
            tips.append("비가 내리고 있어요. 우산을 챙기세요.")
    elif 600 <= weather_id < 700:
        tips.append("눈이 내리고 있어요. 미끄럼에 주의하고 방한 장갑을 꼭 챙기세요.")
    elif weather_id in (711, 721, 731, 741, 751, 761, 762):
        tips.append("황사나 안개가 끼어 있어요. 마스크를 착용하는 것을 추천해요.")

    # ── 바람 조건 ──
    if wind_speed >= 10:
        tips.append("바람이 매우 강해요. 여밀 수 있는 겉옷을 입고 모자는 날아가지 않게 조심하세요!")
    elif wind_speed >= 6:
        if temp >= 17:
            tips.append("바람이 꽤 불어요. 가디건이나 여밀 수 있는 겉옷을 하나 챙기면 좋아요.")
        else:
            tips.append("바람이 꽤 불어 체감온도가 더 낮을 수 있어요. 겉옷을 단단히 여미세요.")

    # ── 자외선·햇빛 (구름량 + 현지 시간대로 추정) ──
    is_strong_sun_time = 10 <= current_hour <= 16  # 자외선이 강한 시간대
    is_daytime = 7 <= current_hour <= 19

    if is_daytime and weather_id == 800:  # 완전 맑음
        if is_strong_sun_time:
            tips.append("햇빛이 매우 강한 시간대예요. 선크림·선글라스·양산을 챙기세요.")
        else:
            tips.append("맑은 날씨예요. 자외선 차단제를 잊지 마세요.")
    elif is_strong_sun_time and clouds < 30:
        tips.append("구름이 적어 자외선이 강할 수 있어요. 선크림을 바르는 걸 추천해요.")

    # ── 추가 조언이 없으면 기본 문구 ──
    if not tips:
        tips.append("오늘 날씨는 무난해요. 편안하게 외출하세요!")

    return {
        "base_outfit": base,
        "tips": tips,
        "recommend": f"{base}을 추천해요!",
        "icon": icon,
    }


def get_condition_label(temp: float, description: str) -> str:
    desc = description.lower()
    if "thunder" in desc:
        return "Stormy"
    elif "rain" in desc or "drizzle" in desc:
        return "Rainy"
    elif "snow" in desc:
        return "Snowy"
    elif "fog" in desc or "mist" in desc:
        return "Foggy"
    elif "cloud" in desc:
        return "Cloudy"
    elif temp >= 28:
        return "Hot"
    elif temp >= 20:
        return "Warm"
    elif temp >= 12:
        return "Mild"
    else:
        return "Cold"


# ───────────────────────────────────────────
# 엔드포인트
# ───────────────────────────────────────────
@app.get("/recommend")
def get_weather_recommendation(city: str = "서울"):
    geo = geocode_city(city)

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": geo["lat"],
        "lon": geo["lng"],
        "appid": OPENWEATHER_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        temp            = data["main"]["temp"]
        feels_like      = data["main"]["feels_like"]
        humidity        = data["main"]["humidity"]
        wind_speed      = data["wind"]["speed"]
        description     = data["weather"][0]["description"]
        weather_id      = data["weather"][0]["id"]
        clouds          = data["clouds"]["all"]
        timezone_offset = data["timezone"]  # UTC 오프셋 (초)

        outfit    = get_detailed_recommendations(temp, wind_speed, clouds, weather_id, timezone_offset)
        condition = get_condition_label(temp, description)

        return {
            "city":           geo["city"],
            "country":        geo["country"],
            "temp":           round(temp, 1),
            "feels_like":     round(feels_like, 1),
            "humidity":       humidity,
            "wind_speed":     round(wind_speed, 1),
            "description":    description,
            "condition":      condition,
            "recommend":      outfit["recommend"],
            "recommend_icon": outfit["icon"],
            "base_outfit":    outfit["base_outfit"],
            "tips":           outfit["tips"],   # 추가 조언 목록 (배열)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/forecast")
def get_hourly_forecast(city: str = "서울"):
    geo = geocode_city(city)

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": geo["lat"],
        "lon": geo["lng"],
        "appid": OPENWEATHER_KEY,
        "units": "metric",
        "cnt": 8,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        forecasts = []
        for item in data["list"]:
            dt_txt    = item["dt_txt"]
            time_part = dt_txt.split(" ")[1][:5]
            hour      = int(time_part.split(":")[0])

            if hour == 0:
                time_label = "12 AM"
            elif hour < 12:
                time_label = f"{hour} AM"
            elif hour == 12:
                time_label = "12 PM"
            else:
                time_label = f"{hour - 12} PM"

            desc = item["weather"][0]["description"].lower()
            if "rain" in desc or "drizzle" in desc:
                weather_type = "rain"
            elif "snow" in desc:
                weather_type = "snow"
            elif "thunder" in desc:
                weather_type = "rain"
            elif "cloud" in desc:
                weather_type = "cloud"
            else:
                weather_type = "clear"

            forecasts.append({
                "time":         time_label,
                "temp":         round(item["main"]["temp"], 1),
                "weather_type": weather_type,
                "description":  item["weather"][0]["description"],
            })

        return {"city": geo["city"], "forecasts": forecasts}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
