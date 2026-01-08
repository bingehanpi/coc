import requests

# 1. 填入你的 Token
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjA5N2EwN2NhLTY0Y2UtNDY4YS1hNmEzLTcxNTQ0MDMxMDE3MiIsImlhdCI6MTc2Nzc3NzcyOSwic3ViIjoiZGV2ZWxvcGVyLzFlYTBiNjIxLTJmNTgtNTAxMC02ZTM2LTM3M2QyNWNlNDQ2YSIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjE2Ny4yMzQuMjEwLjExNyJdLCJ0eXBlIjoiY2xpZW50In1dfQ.k6o0C7M58zotPd_d2JA0x6u01DRak-NqzEpano2Eq7pgBxSJsBNBtuksg5t_FzB_sB3wgTB-cnTA62GNnEYcSA"

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