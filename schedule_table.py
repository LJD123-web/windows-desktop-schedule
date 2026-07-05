"""周课表完整显示对话框 - 粉紫色玻璃风格表格"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QHeaderView, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

import storage
import theme


class WeekScheduleDialog(QDialog):
    """完整周课表弹窗 - 粉紫玻璃风"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("周课表")
        self.setModal(True)
        self.resize(920, 620)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(theme.DIALOG_BASE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        title = QLabel("📋 完整周课表")
        title.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {theme.PINK_LIGHT};"
        )
        layout.addWidget(title)

        courses, periods = storage.get_week_courses()

        # 计算最大节次
        max_period = 0
        for c in courses:
            max_period = max(max_period, c.get("end_period", 0))
        max_period = max(max_period, 8)

        days = storage.DAYS
        col_count = len(days) + 1

        table = QTableWidget(max_period, col_count)
        table.setHorizontalHeaderLabels(["节次"] + days)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet(theme.TABLE_STYLE)
        table.setAlternatingRowColors(True)
        table.setShowGrid(True)

        # 设置节次列
        for row in range(max_period):
            time_str = ""
            if row < len(periods):
                time_str = f"{row+1}\n{periods[row]['start']}"
            item = QTableWidgetItem(time_str)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            bg = QColor(120, 50, 130, 200)
            item.setBackground(bg)
            item.setForeground(QColor(theme.PINK_LIGHT))
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
                color = self._course_color(c.get("name", ""))
                item.setBackground(color)
                item.setForeground(QColor("#ffffff"))
                font = QFont()
                font.setBold(True)
                font.setPointSize(10)
                item.setFont(font)
                table.setItem(row, day_col, item)

        # 合并连续节次
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
        table.verticalHeader().setDefaultSectionSize(64)
        table.setGridStyle(Qt.NoPen)

        layout.addWidget(table)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("✕  关闭")
        close_btn.setStyleSheet(theme.BTN_PRIMARY)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _course_color(self, name):
        """根据课程名生成粉紫色系背景色"""
        colors = [QColor(c) for c in theme.COURSE_COLORS]
        idx = sum(ord(ch) for ch in name) % len(colors)
        c = colors[idx]
        c.setAlpha(180)
        return c
