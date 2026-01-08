import requests
import time
import json
from datetime import datetime

API_TOKEN = ""
BASE_URL = "https://api.clashofclans.com/v1"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json"
}

def coc_get(endpoint):
    url = BASE_URL + endpoint
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def get_cwl_war_tags(clan_tag):
    clan_tag = clan_tag.replace("#", "%23")
    data = coc_get(f"/clans/{clan_tag}/currentwar/leaguegroup")

    war_tags = []
    for rnd in data["rounds"]:
        for war_tag in rnd["warTags"]:
            if war_tag != "#0":  # #0 = 轮空
                war_tags.append(war_tag.replace("#", "%23"))

    return war_tags

def fetch_single_cwl_war(war_tag):
    data = coc_get(f"/clanwarleagues/wars/{war_tag}")
    return data

def fetch_all_cwl_wars(war_tags, sleep_sec=0.2):
    wars = {}
    for war_tag in war_tags:
        print(f"Fetching war: {war_tag}")
        wars[war_tag] = fetch_single_cwl_war(war_tag)
        time.sleep(sleep_sec)
    return wars

def save_cwl_raw(wars, clan_tag):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cwl_raw_{clan_tag.replace('#','')}_{ts}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(wars, f, ensure_ascii=False, indent=2)

    print(f"Saved CWL raw data to: {filename}")


if __name__ == "__main__":
    CLAN_TAG = "#2QL2JYJYC"

    war_tags = get_cwl_war_tags(CLAN_TAG)
    wars = fetch_all_cwl_wars(war_tags)
    save_cwl_raw(wars, CLAN_TAG)
