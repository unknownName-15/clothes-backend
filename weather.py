import requests

# 1. 아까 받은 본인의 API 키를 여기에 넣으세요 (따옴표 유지)
API_KEY = "7c44272cbf92f7b13acc779385b401d2"
CITY_NAME = "Seoul"

# 2. 날씨 정보를 요청할 주소
url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY_NAME}&appid={API_KEY}&units=metric"

try:
    # 3. 실제로 인터넷을 통해 데이터를 가져옵니다
    response = requests.get(url)
    data = response.json()

    # 4. 데이터가 잘 왔는지 확인하고 화면에 출력합니다
    if response.status_code == 200:
        temp = data['main']['temp']      # 현재 온도
        weather = data['weather'][0]['description']  # 날씨 상태
        
        print(f"{CITY_NAME}의 현재 온도는 {temp}도이며, 날씨는 '{weather}'입니다.")
        
        # 5. 옷차림 추천 로직 (맛보기)
        if temp > 20:
            print("추천 옷차림: 셔츠나 반팔티를 추천해요!")
        else:
            print("추천 옷차림: 겉옷이나 따뜻한 긴팔을 챙기세요!")
    else:
        print("데이터를 가져오는 데 실패했어요. API 키를 확인해 보세요.")

except Exception as e:
    print(f"에러가 발생했습니다: {e}")