import pandas as pd
import matplotlib

matplotlib.use('TkAgg')

import matplotlib.pyplot as plt

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False


def analyze_attacks_and_show_chart(excel_file="cwl_our_clan_only.xlsx"):
    try:
        df_attacks = pd.read_excel(excel_file, sheet_name="Attacks")
        df_members = pd.read_excel(excel_file, sheet_name="Members")
    except FileNotFoundError:
        print(f"错误：找不到文件 {excel_file}，请确认文件路径正确。")
        return

    player_map = {row["playerName"]: row["playerTag"] for _, row in df_members.iterrows()}

    attacker_names = list(player_map.keys())
    attack_summary = pd.DataFrame({
        "attackerName": attacker_names,
        "total_stars": [0] * len(attacker_names),
        "total_destruction": [0] * len(attacker_names)
    })

    for _, attack in df_attacks.iterrows():
        attacker = attack["attackerName"]
        if attacker in attack_summary["attackerName"].values:
            attack_summary.loc[attack_summary["attackerName"] == attacker, "total_stars"] += attack["stars"]
            attack_summary.loc[attack_summary["attackerName"] == attacker, "total_destruction"] += attack["destruction"]

    # 升序排列，这样图表里第一名在最上面
    attack_summary.sort_values(by=["total_stars", "total_destruction"], ascending=True, inplace=True)

    plt.figure(figsize=(10, 8))
    plt.barh(attack_summary["attackerName"], attack_summary["total_stars"], color='cornflowerblue', alpha=0.8)

    plt.title("CWL 联赛进攻排名 (按总星数)", fontsize=16)
    plt.xlabel("总获得星数", fontsize=12)
    plt.ylabel("玩家名称", fontsize=12)

    for index, value in enumerate(attack_summary["total_stars"]):
        plt.text(value, index, f'{value}', va='center', color='black', fontweight='bold')

    plt.tight_layout()

    print("正在显示排名柱状图（请查看弹出的窗口）...")
    plt.show()


if __name__ == "__main__":
    analyze_attacks_and_show_chart()