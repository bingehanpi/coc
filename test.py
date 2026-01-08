import requests

# 1. 填入你的 Token
API_TOKEN = ""

def test_auth():
    url = "https://api.clashofclans.com/v1/ip"  # 这个接口可以用来测试鉴权
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("✅ 验证通过！你的授权信息正确。")
        print("API 看到的你的 IP 是:", response.json().get('ip'))
    else:
        print(f"❌ 依然失败。状态码: {response.status_code}")
        print("返回信息:", response.text)


test_auth()
