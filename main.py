import sys
import os
import time
import webbrowser
import requests
import pandas as pd
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QTextEdit, QTabWidget, QGroupBox
)
from PyQt5.QtCore import QThread, pyqtSignal
from dotenv import load_dotenv

import clans_get
import json_analysis
import json_excel_raw
import json_excel_only

matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

load_dotenv()


class PipelineWorker(QThread):

    log_signal = pyqtSignal(str, str)
    step_signal = pyqtSignal(int, str)
    data_ready = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

    def __init__(self, api_token, clan_tag):
        super().__init__()
        self.api_token = api_token
        self.clan_tag = clan_tag
        self._stop = False

    def stop(self):
        self._stop = True

    def _check_stop(self):
        if self._stop:
            self.log_signal.emit("用户已停止操作", "warn")
            self.finished_signal.emit(False)
            return True
        return False

    @staticmethod
    def _is_api_error(e):
        if isinstance(e, (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError,
        )):
            return True
        if isinstance(e, requests.exceptions.RequestException):
            return True
        err_str = str(e).lower()
        api_keywords = ["401", "403", "404", "429", "500", "503", "forbidden",
                        "unauthorized", "api", "token", "clashofclans"]
        return any(kw in err_str for kw in api_keywords)

    def _run_api_diagnostic(self):
        self.log_signal.emit("===== API 连接诊断 =====", "info")
        url = "https://api.clashofclans.com/v1/ip"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }

        self.log_signal.emit(f"测试地址: {url}", "info")
        self.log_signal.emit(f"Token 前20位: {self.api_token[:20]}...", "info")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                ip = response.json().get('ip', '未知')
                self.log_signal.emit("Token 验证通过", "success")
                self.log_signal.emit(f"API 看到的你的 IP: {ip}", "info")
                self.log_signal.emit("提示: 请确认该 IP 已在 developer.clashofclans.com 中加入白名单", "warn")
            else:
                self.log_signal.emit(f"验证失败，状态码: {response.status_code}", "error")
                self.log_signal.emit(f"返回信息: {response.text}", "error")
                if response.status_code == 403:
                    self.log_signal.emit("提示: Token 可能已过期或 IP 未加入白名单，请点击「获取 API Token」更新", "warn")
                elif response.status_code == 401:
                    self.log_signal.emit("提示: Token 无效或格式错误，请检查输入的 Token", "warn")
        except requests.exceptions.ConnectionError:
            self.log_signal.emit("无法连接到 Supercell API 服务器，请检查网络连接", "error")
        except requests.exceptions.Timeout:
            self.log_signal.emit("连接 Supercell API 超时，请检查网络或稍后重试", "error")
        except Exception as diag_e:
            self.log_signal.emit(f"诊断过程出错: {str(diag_e)}", "error")

        self.log_signal.emit("===== 诊断结束 =====", "info")

    def run(self):
        try:
            clans_get.API_TOKEN = self.api_token
            clans_get.HEADERS = {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json"
            }

            self.step_signal.emit(1, "从 API 获取 CWL 数据")
            self.log_signal.emit(f"正在获取部落 {self.clan_tag} 的 CWL 数据...", "info")

            war_tags = clans_get.get_cwl_war_tags(self.clan_tag)
            self.log_signal.emit(f"找到 {len(war_tags)} 场战争", "info")

            wars = {}
            for i, war_tag in enumerate(war_tags):
                if self._check_stop():
                    return
                self.log_signal.emit(f"  获取第 {i + 1}/{len(war_tags)} 场...", "info")
                wars[war_tag] = clans_get.fetch_single_cwl_war(war_tag)
                time.sleep(0.2)

            if self._check_stop():
                return

            clans_get.save_cwl_raw(wars, self.clan_tag)
            self.log_signal.emit("数据获取完成 ✓", "success")

            self.step_signal.emit(2, "校验数据完整性")
            self.log_signal.emit("正在校验数据...", "info")

            valid = json_analysis.validate_cwl_json(wars)
            if valid:
                self.log_signal.emit("数据校验通过 ✓", "success")
            else:
                self.log_signal.emit("数据校验有警告，继续执行...", "warn")

            if self._check_stop():
                return

            self.step_signal.emit(3, "导出己方部落数据")
            self.log_signal.emit("正在导出己方部落数据...", "info")

            members, attacks, defenses = json_excel_only.extract_our_clan_data(wars, self.clan_tag)
            json_excel_only.export_our_clan_excel(members, attacks, defenses)
            self.log_signal.emit("己方数据导出完成 ✓", "success")

            if self._check_stop():
                return

            self.step_signal.emit(4, "生成分析图表")
            self.log_signal.emit("正在生成图表...", "info")
            self.data_ready.emit("cwl_our_clan_only.xlsx")
            self.log_signal.emit("全部完成！✓", "success")

            self.finished_signal.emit(True)

        except Exception as e:
            self.log_signal.emit(f"错误: {str(e)}", "error")
            if self._is_api_error(e):
                self.log_signal.emit("检测到 API 错误，正在运行连接诊断...", "warn")
                self._run_api_diagnostic()
            self.finished_signal.emit(False)


class ChartCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 6), dpi=100)
        super().__init__(self.fig)
        self.setParent(parent)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CWL 联赛数据分析工具")
        self.setMinimumSize(960, 720)
        self.worker = None
        self._init_ui()
        self._load_defaults()
        self._load_cached_charts()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        config_group = QGroupBox("配置")
        config_layout = QFormLayout(config_group)
        config_layout.setSpacing(8)

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("输入 Supercell API Token")
        config_layout.addRow("API Token:", self.token_input)

        self.clan_input = QLineEdit()
        self.clan_input.setPlaceholderText("输入部落标签，如 #2QL2JYJYC")
        config_layout.addRow("部落标签:", self.clan_input)

        main_layout.addWidget(config_group)

        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("开始查询")
        self.start_btn.setFixedHeight(36)
        self.start_btn.clicked.connect(self._start_pipeline)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFixedHeight(36)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_pipeline)
        btn_layout.addWidget(self.stop_btn)

        self.token_btn = QPushButton("获取 API Token")
        self.token_btn.setFixedHeight(36)
        self.token_btn.clicked.connect(
            lambda: webbrowser.open("https://developer.clashofclans.com/")
        )
        btn_layout.addWidget(self.token_btn)

        main_layout.addLayout(btn_layout)

        log_group = QGroupBox("执行日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(160)
        self.log_text.setStyleSheet(
            "QTextEdit { background-color: #1e1e1e; color: #d4d4d4;"
            " font-family: Consolas, 'Courier New', monospace; font-size: 12px; }"
        )
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group)

        from PyQt5.QtWidgets import QLabel
        from PyQt5.QtCore import Qt
        self.query_time_label = QLabel("查询时间: 暂无数据")
        self.query_time_label.setAlignment(Qt.AlignCenter)
        self.query_time_label.setStyleSheet("font-size: 13px; color: #888; padding: 2px;")
        main_layout.addWidget(self.query_time_label)

        self.chart_tabs = QTabWidget()

        self.combo_canvas = ChartCanvas()
        self.attack_canvas = ChartCanvas()
        self.defense_canvas = ChartCanvas()

        self.chart_tabs.addTab(self.combo_canvas, "综合排名")
        self.chart_tabs.addTab(self.attack_canvas, "进攻排名")
        self.chart_tabs.addTab(self.defense_canvas, "防守排名")

        main_layout.addWidget(self.chart_tabs, stretch=1)

    def _load_defaults(self):
        self.token_input.setText(os.getenv("COC_API_TOKEN", ""))
        self.clan_input.setText(os.getenv("COC_CLAN_TAG", ""))

    def _load_cached_charts(self):
        excel_file = "cwl_our_clan_only.xlsx"
        if os.path.exists(excel_file):
            self._append_log(f"检测到本地已有数据文件 {excel_file}，正在加载图表...", "info")
            self._generate_charts(excel_file)
        self._update_query_time()

    def _update_query_time(self):
        import re
        from datetime import datetime
        pattern = re.compile(r"^cwl_raw_.+_(\d{8}_\d{6})\.json$")
        latest_ts = None
        for f in os.listdir("."):
            m = pattern.match(f)
            if m:
                ts_str = m.group(1)
                if latest_ts is None or ts_str > latest_ts:
                    latest_ts = ts_str
        if latest_ts:
            dt = datetime.strptime(latest_ts, "%Y%m%d_%H%M%S")
            display = dt.strftime("%Y-%m-%d %H:%M:%S")
            self.query_time_label.setText(f"查询时间: {display}")
            self.query_time_label.setStyleSheet("font-size: 13px; color: #4ec9b0; padding: 2px;")
        else:
            self.query_time_label.setText("查询时间: 暂无数据")
            self.query_time_label.setStyleSheet("font-size: 13px; color: #888; padding: 2px;")

    def _start_pipeline(self):
        if self.worker and self.worker.isRunning():
            return

        self.log_text.clear()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.token_input.setEnabled(False)
        self.clan_input.setEnabled(False)

        self.worker = PipelineWorker(
            self.token_input.text().strip(),
            self.clan_input.text().strip()
        )
        self.worker.log_signal.connect(self._append_log)
        self.worker.step_signal.connect(self._on_step)
        self.worker.data_ready.connect(self._generate_charts)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _stop_pipeline(self):
        if self.worker:
            self.worker.stop()

    def _append_log(self, msg, level):
        colors = {
            "info": "#d4d4d4",
            "success": "#4ec9b0",
            "warn": "#dcdcaa",
            "error": "#f44747"
        }
        color = colors.get(level, "#d4d4d4")
        self.log_text.append(f'<span style="color:{color}">• {msg}</span>')

    def _on_step(self, step, name):
        self._append_log(f"--- 步骤 {step}: {name} ---", "info")

    def _on_finished(self, success):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.token_input.setEnabled(True)
        self.clan_input.setEnabled(True)
        if success:
            self._update_query_time()

    def _generate_charts(self, excel_file):
        try:
            df_attacks = pd.read_excel(excel_file, sheet_name="Attacks")
            df_defenses = pd.read_excel(excel_file, sheet_name="Defenses")
            df_members = pd.read_excel(excel_file, sheet_name="Members")

            self._plot_combo(df_attacks, df_defenses, df_members)
            self._plot_attack(df_attacks, df_members)
            self._plot_defense(df_defenses, df_members)
            self._append_log("图表生成完成，可切换页签查看", "success")
        except Exception as e:
            self._append_log(f"图表生成失败: {str(e)}", "error")

    def _plot_combo(self, df_attacks, df_defenses, df_members):
        canvas = self.combo_canvas
        canvas.fig.clear()
        ax = canvas.fig.add_subplot(111)

        player_names = df_members["playerName"].tolist()
        summary = pd.DataFrame({
            "playerName": player_names,
            "total_attack_stars": 0,
            "total_attack_destruction": 0.0,
            "total_defense_stars": 0,
            "total_defense_destruction": 0.0
        })

        for _, atk in df_attacks.iterrows():
            name = atk["attackerName"]
            if name in summary["playerName"].values:
                summary.loc[summary["playerName"] == name, "total_attack_stars"] += atk["stars"]
                summary.loc[summary["playerName"] == name, "total_attack_destruction"] += atk["destruction"]

        for _, defe in df_defenses.iterrows():
            name = defe["defenderName"]
            if name in summary["playerName"].values:
                summary.loc[summary["playerName"] == name, "total_defense_stars"] += defe["stars"]
                summary.loc[summary["playerName"] == name, "total_defense_destruction"] += defe["destruction"]

        summary["net_stars"] = summary["total_attack_stars"] - summary["total_defense_stars"]
        summary["net_destruction"] = summary["total_attack_destruction"] - summary["total_defense_destruction"]
        summary.sort_values(by=["net_stars", "net_destruction"], ascending=True, inplace=True)

        ax.barh(summary["playerName"], summary["net_stars"], color='forestgreen', alpha=0.8)
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
        ax.set_title("CWL 联赛综合排名 (净胜星 = 拿星 - 丢星)", fontsize=14)
        ax.set_xlabel("净胜星数 (越往右表现越强)", fontsize=11)
        ax.set_ylabel("玩家名称", fontsize=11)

        canvas.fig.tight_layout()
        canvas.draw()

    def _plot_attack(self, df_attacks, df_members):
        canvas = self.attack_canvas
        canvas.fig.clear()
        ax = canvas.fig.add_subplot(111)

        player_map = {row["playerName"]: row["playerTag"] for _, row in df_members.iterrows()}
        attacker_names = list(player_map.keys())
        summary = pd.DataFrame({
            "attackerName": attacker_names,
            "total_stars": 0,
            "total_destruction": 0.0
        })

        for _, atk in df_attacks.iterrows():
            attacker = atk["attackerName"]
            if attacker in summary["attackerName"].values:
                summary.loc[summary["attackerName"] == attacker, "total_stars"] += atk["stars"]
                summary.loc[summary["attackerName"] == attacker, "total_destruction"] += atk["destruction"]

        summary.sort_values(by=["total_stars", "total_destruction"], ascending=True, inplace=True)

        ax.barh(summary["attackerName"], summary["total_stars"], color='cornflowerblue', alpha=0.8)
        ax.set_title("CWL 联赛进攻排名 (按总星数)", fontsize=14)
        ax.set_xlabel("总获得星数", fontsize=11)
        ax.set_ylabel("玩家名称", fontsize=11)

        for i, val in enumerate(summary["total_stars"]):
            ax.text(val, i, f'{val}', va='center', color='black', fontweight='bold')

        canvas.fig.tight_layout()
        canvas.draw()

    def _plot_defense(self, df_defenses, df_members):
        canvas = self.defense_canvas
        canvas.fig.clear()
        ax = canvas.fig.add_subplot(111)

        player_map = {row["playerName"]: row["playerTag"] for _, row in df_members.iterrows()}
        defender_names = list(player_map.keys())
        summary = pd.DataFrame({
            "defenderName": defender_names,
            "total_attack_stars": 0,
            "total_destruction": 0.0
        })

        for _, defe in df_defenses.iterrows():
            defender = defe["defenderName"]
            if defender in summary["defenderName"].values:
                summary.loc[summary["defenderName"] == defender, "total_attack_stars"] += defe["stars"]
                summary.loc[summary["defenderName"] == defender, "total_destruction"] += defe["destruction"]

        summary.sort_values(by=["total_attack_stars", "total_destruction"], ascending=[False, False], inplace=True)

        ax.barh(summary["defenderName"], summary["total_attack_stars"], color='indianred', alpha=0.8)
        ax.set_title("CWL 联赛防御排名 (被进攻失星数)", fontsize=14)
        ax.set_xlabel("被对手获取的总星数 (越少越好)", fontsize=11)
        ax.set_ylabel("玩家名称", fontsize=11)

        for i, val in enumerate(summary["total_attack_stars"]):
            ax.text(val, i, f'{val}', va='center', color='black', fontweight='bold')

        canvas.fig.tight_layout()
        canvas.draw()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)
        event.accept()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    from PyQt5.QtCore import QLibraryInfo
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(QLibraryInfo.PluginsPath)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
