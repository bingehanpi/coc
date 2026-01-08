import pandas as pd
import matplotlib

matplotlib.use('TkAgg')

import matplotlib.pyplot as plt

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False


def analyze_defenses_and_show_chart(excel_file="cwl_our_clan_only.xlsx"):
    # 读取 Excel 文件
    try:
        df_defenses = pd.read_excel(excel_file, sheet_name="Defenses")
        df_members = pd.read_excel(excel_file, sheet_name="Members")
    except FileNotFoundError:
        print(f"错误：找不到文件 {excel_file}，请确认文件路径正确。")
        return

    # 创建映射
    player_map = {row["playerName"]: row["playerTag"] for _, row in df_members.iterrows()}

    # 初始化 DataFrame
    defender_names = list(player_map.keys())
    defense_summary = pd.DataFrame({
        "defenderName": defender_names,
        "total_attack_stars": [0] * len(defender_names),
        "total_destruction": [0] * len(defender_names)
    })

    # 统计数据
    for _, defense in df_defenses.iterrows():
        defender = defense["defenderName"]
        if defender in defense_summary["defenderName"].values:
            defense_summary.loc[defense_summary["defenderName"] == defender, "total_attack_stars"] += defense["stars"]
            defense_summary.loc[defense_summary["defenderName"] == defender, "total_destruction"] += defense[
                "destruction"]

    defense_summary.sort_values(by=["total_attack_stars", "total_destruction"], ascending=[False, False], inplace=True)

    # 创建柱状图
    plt.figure(figsize=(10, 8))

    # 生成水平柱状图 (红色代表防御/被攻击)
    plt.barh(defense_summary["defenderName"], defense_summary["total_attack_stars"], color='indianred', alpha=0.8)

    # 添加标题和标签
    plt.title("CWL 联赛防御排名 (被进攻失星数)", fontsize=16)
    plt.xlabel("被对手获取的总星数 (越少越好)", fontsize=12)
    plt.ylabel("玩家名称", fontsize=12)

    # 显示数值
    for index, value in enumerate(defense_summary["total_attack_stars"]):
        plt.text(value, index, f'{value}', va='center', color='black', fontweight='bold')

    plt.tight_layout()

    print("正在显示防御排名柱状图...")
    plt.show()


if __name__ == "__main__":
    analyze_defenses_and_show_chart()
