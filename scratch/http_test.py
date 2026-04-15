import requests

# 1. http 로 테스트 (https에서 403이 날 경우를 대비)
url = 'http://apis.data.go.kr/1471000/MdvUdiInfoService/getMdvUdiInfo' 
# 만약 명세서 확인 결과 오퍼레이션명이 다르다면 위 주소 끝부분을 꼭 수정해 주세요.

# 2. requests는 params로 넘길 때 무조건 'Decoding' 키를 사용해야 합니다.
decoding_key = "4KxwtGJszCv/RTFVhRm4kOs2UCoxj+Kpnfl849syl2KyB8wLYZ+H7Kyjpe4QtUmfYTJNzWeIRheY/DD3hw6yQw=="

# 3. WAF 차단 방지용 User-Agent 추가
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

params = {
    'serviceKey': decoding_key,
    'pageNo': '1',
    'numOfRows': '500',
    'type': 'json'
}

response = requests.get(url, params=params, headers=headers)

print(f"상태 코드: {response.status_code}")
print(f"응답 내용:\n{response.text}")