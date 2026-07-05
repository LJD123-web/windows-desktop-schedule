"""悬浮窗主界面 - 粉紫色透明玻璃风格、无边框、置顶、可拖动"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QMenu, QHBoxLayout, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QMouseEvent

import storage
import theme
from schedule_table import WeekScheduleDialog
from editor_dialog import EditorDialog
from ocr_import import OCRImportDialog


class FloatingWindow(QWidget):
    """悬浮窗主组件 - 粉紫玻璃风"""

    request_quit = Signal()

    def __init__(self):
        super().__init__()
        self._drag_pos = None
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._fade_out)

        self._init_ui()
        self._refresh()

        # 每 60 秒刷新一次（更新当前课程高亮）
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(60000)

    def _init_ui(self):
        """初始化界面"""
        # 无边框 + 置顶 + 工具窗口（不在任务栏显示）
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(280)

        # 主容器 - 粉紫玻璃
        self._container = QFrame(self)
        self._container.setObjectName("container")
        self._container.setStyleSheet(theme.FLOATING_CONTAINER)

        # 外发光阴影效果
        shadow = QGraphicsDropShadowEffect(self._container)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(200, 80, 192, 120))
        shadow.setOffset(0, 0)
        self._container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._container)

        inner = QVBoxLayout(self._container)
        inner.setContentsMargins(18, 14, 18, 14)
        inner.setSpacing(8)

        # 标题栏 - 渐变文字效果
        header = QHBoxLayout()
        self._title_label = QLabel("✦ 课程表")
        self._title_label.setStyleSheet(
            f"color: {theme.PINK_LIGHT}; font-size: 15px; font-weight: bold;"
        )
        self._date_label = QLabel("")
        self._date_label.setStyleSheet(
            f"color: rgba(255, 158, 216, 200); font-size: 11px;"
        )
        self._date_label.setAlignment(Qt.AlignRight)
        header.addWidget(self._title_label)
        header.addStretch()
        header.addWidget(self._date_label)
        inner.addLayout(header)

        # 分隔线
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(
            "background-color: rgba(255, 158, 216, 50); border: none; max-height: 1px;"
        )
        inner.addWidget(sep)

        # 课程列表区域（可滚动，防止课程过多时窗口太高）
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet("QScrollArea { background: transparent; }"
                                    "QScrollBar:vertical { width: 4px; background: transparent; }"
                                    "QScrollBar::handle:vertical { background: rgba(255,158,216,80); border-radius: 2px; }"
                                    "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }")

        self._courses_container = QWidget()
        self._courses_container.setStyleSheet("background: transparent;")
        self._courses_layout = QVBoxLayout(self._courses_container)
        self._courses_layout.setSpacing(6)
        self._courses_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll.setWidget(self._courses_container)
        self._scroll.setMaximumHeight(320)
        inner.addWidget(self._scroll)

        self._no_course_label = QLabel("今天没有课程 ✨")
        self._no_course_label.setStyleSheet(
            f"color: rgba(255, 158, 216, 150); font-size: 13px;"
        )
        self._no_course_label.setAlignment(Qt.AlignCenter)
        self._no_course_label.setFixedHeight(48)
        inner.addWidget(self._no_course_label)

        inner.addStretch()

        # 底部提示
        hint = QLabel("右键菜单  ·  双击周课表")
        hint.setStyleSheet(
            "color: rgba(255, 158, 216, 80); font-size: 10px;"
        )
        hint.setAlignment(Qt.AlignCenter)
        inner.addWidget(hint)

    def _refresh(self):
        """刷新显示内容"""
        from datetime import datetime
        now = datetime.now()
        days = storage.DAYS
        self._date_label.setText(
            f"{now.month}月{now.day}日 {days[now.weekday()]}"
        )

        # 清空旧的课程标签
        while self._courses_layout.count():
            item = self._courses_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        courses, periods = storage.get_today_courses()
        current_period = storage.get_current_period()

        if not courses:
            self._no_course_label.show()
        else:
            self._no_course_label.hide()
            for c in courses:
                sp = c.get("start_period", 0)
                ep = c.get("end_period", sp)
                time_str = ""
                if 0 < sp <= len(periods) and 0 < ep <= len(periods):
                    time_str = f"{periods[sp-1]['start']}-{periods[ep-1]['end']}"

                is_now = (current_period is not None
                          and sp <= current_period <= ep)

                card = self._make_course_card(c, time_str, is_now)
                self._courses_layout.addWidget(card)

        self.adjustSize()

    def _make_course_card(self, course, time_str, is_now):
        """创建单个课程卡片 - 粉紫玻璃风（两行布局避免文字重叠）"""
        card = QFrame()
        card.setStyleSheet(theme.course_card_style(is_now))

        # 外层：左侧高亮条 + 右侧内容
        outer = QHBoxLayout(card)
        outer.setContentsMargins(10, 8, 12, 8)
        outer.setSpacing(8)

        # 当前课程左侧发光条
        if is_now:
            bar = QFrame()
            bar.setFixedWidth(3)
            bar.setStyleSheet(
                f"background-color: {theme.PINK_GLOW}; border-radius: 1.5px;"
            )
            outer.addWidget(bar)

        # 右侧：上下两行
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(2)

        # 第一行：课程名
        name_label = QLabel(course.get("name", "未命名"))
        name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        if is_now:
            name_label.setStyleSheet(
                f"color: {theme.PINK_GLOW}; font-size: 14px; font-weight: bold;"
            )
        else:
            name_label.setStyleSheet(
                "color: #ffffff; font-size: 13px; font-weight: bold;"
            )
        right.addWidget(name_label)

        # 第二行：地点 + 时间（同一行，地点在前）
        second_row = QHBoxLayout()
        second_row.setContentsMargins(0, 0, 0, 0)
        second_row.setSpacing(8)

        loc = course.get("location", "")
        if loc:
            loc_label = QLabel(f"📍 {loc}")
            loc_label.setStyleSheet(
                f"color: {theme.LAVENDER}; font-size: 11px;"
            )
            loc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            second_row.addWidget(loc_label)
        else:
            second_row.addStretch()

        if time_str:
            time_label = QLabel(f"🕐 {time_str}")
            color = theme.PINK_GLOW if is_now else "rgba(255,158,216,150)"
            time_label.setStyleSheet(f"color: {color}; font-size: 11px;")
            time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            second_row.addWidget(time_label)

        right.addLayout(second_row)
        outer.addLayout(right)

        return card

    # ===== 鼠标交互 =====

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """双击展开周课表"""
        if event.button() == Qt.LeftButton:
            self._show_week_table()

    def enterEvent(self, event):
        """鼠标进入 - 恢复不透明"""
        self._hover_timer.stop()
        self.setWindowOpacity(1.0)

    def leaveEvent(self, event):
        """鼠标离开 - 延迟半透明"""
        self._hover_timer.start(800)

    def _fade_out(self):
        self.setWindowOpacity(0.78)

    # ===== 右键菜单 =====

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(theme.MENU_STYLE)

        act_refresh = QAction("🔄  刷新", self)
        act_refresh.triggered.connect(self._refresh)
        menu.addAction(act_refresh)

        menu.addSeparator()

        act_week = QAction("📋  查看周课表", self)
        act_week.triggered.connect(self._show_week_table)
        menu.addAction(act_week)

        act_add = QAction("➕  添加课程", self)
        act_add.triggered.connect(self._add_course)
        menu.addAction(act_add)

        act_edit = QAction("✏️  编辑课程", self)
        act_edit.triggered.connect(self._edit_courses)
        menu.addAction(act_edit)

        menu.addSeparator()

        act_ocr = QAction("📷  从图片导入", self)
        act_ocr.triggered.connect(self._import_from_image)
        menu.addAction(act_ocr)

        menu.addSeparator()

        act_quit = QAction("❌  退出", self)
        act_quit.triggered.connect(self.request_quit.emit)
        menu.addAction(act_quit)

        menu.exec(event.globalPos())

    # ===== 菜单动作 =====

    def _show_week_table(self):
        dlg = WeekScheduleDialog(self)
        dlg.exec()

    def _add_course(self):
        dlg = EditorDialog(self)
        if dlg.exec():
            storage.add_course(dlg.get_course())
            self._refresh()

    def _edit_courses(self):
        dlg = EditorDialog(self, edit_mode=True)
        if dlg.exec():
            self._refresh()

    def _import_from_image(self):
        dlg = OCRImportDialog(self)
        if dlg.exec():
            self._refresh()
