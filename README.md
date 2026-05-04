# Meteo Insight — Backend

> FastAPI 기반 날씨 조회 및 의류 추천 API 서버

---

## 📁 파일 구조

```
backend/
├── main.py            # FastAPI 서버 (메인 로직)
├── weather.py         # 날씨 API 테스트 스크립트
├── requirements.txt   # 패키지 목록
├── railway.toml       # Railway 배포 설정
├── .env               # API 키 (git 제외)
└── .env.example       # 환경변수 템플릿
```

---

## ⚙️ 환경변수

`backend/` 폴더 안에 `.env` 파일을 만들고 아래 키를 입력하세요.

```env
OPENWEATHER_KEY=발급받은_OpenWeatherMap_API_키
GOOGLE_KEY=발급받은_Google_Geocoding_API_키
```

| 변수명 | 설명 | 발급처 |
|--------|------|--------|
| `OPENWEATHER_KEY` | 날씨 데이터 조회 | [openweathermap.org](https://openweathermap.org/api) (무료) |
| `GOOGLE_KEY` | 한국어 도시명 → 위도/경도 변환 | [Google Cloud Console](https://console.cloud.google.com) (Geocoding API 활성화 필요) |

---

## 🚀 로컬 실행

```bash
# 패키지 설치
pip install -r requirements.txt

# 서버 실행
uvicorn main:app --reload
# → http://127.0.0.1:8000
```

---

## 🌐 API 엔드포인트

### `GET /recommend?city={도시명}`

현재 날씨와 복합 조건 기반 의류 추천을 반환해요.  
한국어(`서울`), 영어(`Seoul`) 모두 지원해요.

**응답 예시**
```json
{
  "city": "Seoul",
  "country": "KR",
  "temp": 17.4,
  "feels_like": 16.2,
  "humidity": 38,
  "wind_speed": 7.3,
  "description": "clear sky",
  "condition": "Mild",
  "recommend": "얇은 가디건이나 긴팔을 추천해요!",
  "base_outfit": "얇은 가디건이나 긴팔",
  "tips": [
    "바람이 꽤 불어요. 가디건이나 여밀 수 있는 겉옷을 하나 챙기면 좋아요. 🍃",
    "햇빛이 맑아요. 자외선 차단제를 잊지 마세요. 🌤️"
  ]
}
```

### `GET /forecast?city={도시명}`

3시간 간격 시간별 예보(24시간)를 반환해요.

**응답 예시**
```json
{
  "city": "Seoul",
  "forecasts": [
    { "time": "3 PM", "temp": 18.2, "weather_type": "clear", "description": "clear sky" },
    { "time": "6 PM", "temp": 15.1, "weather_type": "cloud", "description": "few clouds" }
  ]
}
```

---

## 🧠 추천 로직

온도 하나만 보는 게 아니라 아래 조건을 복합적으로 판단해요.

| 조건 | 추천 내용 |
|------|-----------|
| 온도 | 6단계로 기본 옷차림 결정 (민소매 → 패딩) |
| 강수 (weather_id) | 이슬비·비·폭우·눈·천둥 각각 다른 우산/방수 조언 |
| 풍속 6m/s 이상 | 여밀 수 있는 겉옷 추천 |
| 풍속 10m/s 이상 | 모자 주의 경고 |
| 맑음 + 오전 10시~오후 4시 | 선크림·양산 추천 |
| 황사·안개 | 마스크 착용 권고 |

---

## ☁️ Railway 배포

1. [railway.app](https://railway.app) → GitHub 연동
2. `New Project` → `Deploy from GitHub repo` → 이 저장소 선택
3. Root Directory를 `backend`로 설정
4. `Variables` 탭에서 환경변수 등록
   ```
   OPENWEATHER_KEY = 실제키값
   GOOGLE_KEY      = 실제키값
   ```
5. 자동 배포 완료 후 `Settings → Domains`에서 HTTPS 주소 확인
