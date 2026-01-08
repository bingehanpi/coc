import json
import os

def load_cwl_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_single_war(war_tag, war):
    required_top_keys = {
        "state", "teamSize",
        "preparationStartTime",
        "startTime", "endTime",
        "clan", "opponent"
    }

    missing = required_top_keys - war.keys()
    if missing:
        print(f"[WAR {war_tag}] Missing top-level keys: {missing}")
        return False

    for side in ("clan", "opponent"):
        side_obj = war.get(side, {})
        required_side_keys = {
            "tag", "name",
            "stars", "destructionPercentage",
            "members"
        }

        side_missing = required_side_keys - side_obj.keys()
        if side_missing:
            print(f"[WAR {war_tag}] {side} missing keys: {side_missing}")
            return False

        if not isinstance(side_obj["members"], list):
            print(f"[WAR {war_tag}] {side}.members is not a list")
            return False

    return True

def validate_members(war_tag, war):
    for side in ("clan", "opponent"):
        for m in war[side]["members"]:
            required_member_keys = {
                "tag", "name",
                "townhallLevel",
                "mapPosition"
            }

            missing = required_member_keys - m.keys()
            if missing:
                print(f"[WAR {war_tag}] member {m.get('tag')} missing: {missing}")
                return False

            if "attacks" in m:
                for atk in m["attacks"]:
                    required_attack_keys = {
                        "attackerTag",
                        "defenderTag",
                        "stars",
                        "destructionPercentage",
                        "order"
                    }
                    atk_missing = required_attack_keys - atk.keys()
                    if atk_missing:
                        print(
                            f"[WAR {war_tag}] attack missing keys: {atk_missing}"
                        )
                        return False
    return True

def validate_cwl_json(cwl_data):
    ok = True

    for war_tag, war in cwl_data.items():
        if not validate_single_war(war_tag, war):
            ok = False
        if not validate_members(war_tag, war):
            ok = False

    return ok



def find_latest_cwl_json(prefix="cwl_raw_", suffix=".json"):
    files = [
        f for f in os.listdir(".")
        if f.startswith(prefix) and f.endswith(suffix)
    ]

    if not files:
        raise FileNotFoundError("当前目录下未找到 CWL 原始 JSON 文件")

    # 按文件名排序，取最新的一个
    files.sort()
    return files[-1]


if __name__ == "__main__":
    json_file = find_latest_cwl_json()
    print(f"Using CWL data file: {json_file}")

    data = load_cwl_json(json_file)
    result = validate_cwl_json(data)

    if result:
        print("✓ CWL JSON 数据结构完整，字段齐全")
    else:
        print("✗ CWL JSON 存在结构问题，请检查输出")
