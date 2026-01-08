import pandas as pd
import matplotlib

matplotlib.use('TkAgg')

import matplotlib.pyplot as plt

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False


def analyze_final_rankings_and_show_chart(excel_file="cwl_our_clan_only.xlsx"):
    # 读取 Excel 文件
    try:
        df_attacks = pd.read_excel(excel_file, sheet_name="Attacks")
        df_defenses = pd.read_excel(excel_file, sheet_name="Defenses")
        df_members = pd.read_excel(excel_file, sheet_name="Members")
    except FileNotFoundError:
        print(f"错误：找不到文件 {excel_file}")
        return
    except Exception as e:
        print(f"读取文件出错: {e}")
        return

    # 获取成员名单并初始化
    player_names = df_members["playerName"].tolist()
    final_summary = pd.DataFrame({
        "playerName": player_names,
        "total_attack_stars": 0,
        "total_attack_destruction": 0,
        "total_defense_stars": 0,
        "total_defense_destruction": 0
    })

    # 统计进攻数据
    for _, attack in df_attacks.iterrows():
        name = attack["attackerName"]
        if name in final_summary["playerName"].values:
            final_summary.loc[final_summary["playerName"] == name, "total_attack_stars"] += attack["stars"]
            final_summary.loc[final_summary["playerName"] == name, "total_attack_destruction"] += attack["destruction"]

    # 统计防御数据
    for _, defense in df_defenses.iterrows():
        name = defense["defenderName"]
        if name in final_summary["playerName"].values:
            final_summary.loc[final_summary["playerName"] == name, "total_defense_stars"] += defense["stars"]
            final_summary.loc[final_summary["playerName"] == name, "total_defense_destruction"] += defense[
                "destruction"]

    # 计算净星数 (进攻星 - 防御星) 和 净摧毁率
    final_summary["net_stars"] = final_summary["total_attack_stars"] - final_summary["total_defense_stars"]
    final_summary["net_destruction"] = final_summary["total_attack_destruction"] - final_summary[
        "total_defense_destruction"]

    final_summary.sort_values(by=["net_stars", "net_destruction"], ascending=True, inplace=True)

    # 创建柱状图
    plt.figure(figsize=(12, 8))

    # 生成水平柱状图 (绿色代表综合表现)
    plt.barh(final_summary["playerName"], final_summary["net_stars"], color='forestgreen', alpha=0.8)

    # 添加辅助线 (0星线，区分正负贡献)
    plt.axvline(x=0, color='black', linestyle='-', linewidth=0.8)

    # 添加标题和标签
    plt.title("CWL 联赛综合排名 (净胜星 = 拿星 - 丢星)", fontsize=16)
    plt.xlabel("净胜星数 (越往右表现越强)", fontsize=12)
    plt.ylabel("玩家名称", fontsize=12)

    plt.tight_layout()

    # --- 关键修改 3: 直接显示 ---
    print("正在显示最终综合排名图表...")
    plt.show()


if __name__ == "__main__":
    analyze_final_rankings_and_show_chart()