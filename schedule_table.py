"""周课表完整显示对话框 - 表格形式展示整周课程"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QHeaderView, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

import storage


class WeekScheduleDialog(QDialog):
    """完整周课表弹窗"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("周课表")
        self.setModal(True)
        self.resize(900, 600)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("📋 完整周课表")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        courses, periods = storage.get_week_courses()

        # 计算最大节次
        max_period = 0
        for c in courses:
            max_period = max(max_period, c.get("end_period", 0))
        max_period = max(max_period, 8)  # 至少显示 8 节

        days = storage.DAYS
        col_count = len(days) + 1  # 节次列 + 7 天

        table = QTableWidget(max_period, col_count)
        table.setHorizontalHeaderLabels(["节次"] + days)
        table.verticalHeader().setVisible(False)

        # 设置节次列
        for row in range(max_period):
            time_str = ""
            if row < len(periods):
                time_str = f"{row+1}\n{periods[row]['start']}"
            item = QTableWidgetItem(time_str)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            bg = QColor("#f0f0f5")
            item.setBackground(bg)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            table.setItem(row, 0, item)

        # 填充课程
        for c in courses:
            day_col = c.get("day", 0)
            if day_col < 1 or day_col > 7:
                continue
            sp = c.get("start_period", 1)
            ep = c.get("end_period", sp)
            sp = max(1, sp)
            ep = min(max_period, ep)

            text = c.get("name", "")
            loc = c.get("location", "")
            teacher = c.get("teacher", "")
            if loc:
                text += f"\n@{loc}"
            if teacher:
                text += f"\n{teacher}"

            for row in range(sp - 1, ep):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                # 课程背景色 - 根据课程名 hash 生成柔和颜色
                color = self._course_color(c.get("name", ""))
                item.setBackground(color)
                font = QFont()
                font.setBold(True)
                item.setFont(font)
                table.setItem(row, day_col, item)

        # 合并连续节次的单元格
        for c in courses:
            day_col = c.get("day", 0)
            if day_col < 1 or day_col > 7:
                continue
            sp = c.get("start_period", 1)
            ep = c.get("end_period", sp)
            if ep > sp:
                table.setSpan(sp - 1, day_col, ep - sp + 1, 1)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.verticalHeader().setDefaultSectionSize(60)
        table.setGridStyle(Qt.SolidLine)
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #4a90d9;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
        """)

        layout.addWidget(table)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3a7bc8;
            }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _course_color(self, name):
        """根据课程名生成柔和的背景色"""
        colors = [
            QColor("#FFB3BA"),  # 粉红
            QColor("#BAFFC9"),  # 浅绿
            QColor("#BAE1FF"),  # 浅蓝
            QColor("#FFFFBA"),  # 浅黄
            QColor("#FFD9BA"),  # 橙
            QColor("#D4BAFF"),  # 浅紫
            QColor("#BAFFFF"),  # 青
            QColor("#FFBAE1"),  # 玫红
        ]
        idx = sum(ord(ch) for ch in name) % len(colors)
        return colors[idx]
