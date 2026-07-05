"""粉紫色透明玻璃主题样式 - 全局统一定义"""

# ===== 色彩常量 =====
PURPLE_MAIN = "#C850C0"       # 粉紫主色
PURPLE_DEEP = "#9B5DE5"       # 深紫
PINK_LIGHT = "#FF9ED8"        # 浅粉
PINK_GLOW = "#FF6EC7"         # 高亮粉
LAVENDER = "#E8A0F0"          # 薰衣草紫
GLASS_BG = "rgba(55, 25, 75, 210)"       # 玻璃深紫底
GLASS_BG_LIGHT = "rgba(75, 35, 95, 190)" # 玻璃浅紫底
GLASS_BORDER = "rgba(255, 158, 216, 80)" # 粉色微光边框
GLASS_BORDER_STRONG = "rgba(255, 158, 216, 160)"

# ===== 悬浮窗容器 =====
FLOATING_CONTAINER = f"""
    QFrame#container {{
        background-color: {GLASS_BG};
        border-radius: 18px;
        border: 1.5px solid {GLASS_BORDER};
    }}
"""

# ===== 右键菜单 =====
MENU_STYLE = f"""
    QMenu {{
        background-color: rgba(55, 25, 75, 240);
        color: #ffffff;
        border: 1.5px solid {GLASS_BORDER_STRONG};
        border-radius: 10px;
        padding: 8px;
    }}
    QMenu::item {{
        padding: 8px 28px;
        border-radius: 6px;
        font-size: 13px;
    }}
    QMenu::item:selected {{
        background-color: rgba(200, 80, 192, 120);
        color: #ffffff;
    }}
    QMenu::separator {{
        height: 1px;
        background: rgba(255, 158, 216, 60);
        margin: 4px 12px;
    }}
"""

# ===== 课程卡片 =====
def course_card_style(is_now):
    if is_now:
        return f"""
            QFrame {{
                background-color: rgba(255, 110, 199, 50);
                border-radius: 12px;
                border: 1.5px solid rgba(255, 110, 199, 200);
            }}
        """
    return f"""
        QFrame {{
            background-color: rgba(255, 255, 255, 18);
            border-radius: 12px;
            border: 1px solid rgba(255, 158, 216, 30);
        }}
    """

# ===== 对话框基础样式 =====
DIALOG_BASE = f"""
    QDialog {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(60, 28, 80, 255),
            stop:0.5 rgba(80, 35, 100, 255),
            stop:1 rgba(55, 25, 75, 255));
    }}
    QLabel {{
        color: #f0e6f6;
        font-size: 13px;
    }}
    QGroupBox {{
        color: {PINK_LIGHT};
        font-size: 14px;
        font-weight: bold;
        border: 1.5px solid rgba(255, 158, 216, 50);
        border-radius: 12px;
        margin-top: 16px;
        padding-top: 18px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
    }}
"""

# ===== 输入框 =====
INPUT_STYLE = f"""
    QLineEdit, QSpinBox, QComboBox {{
        background-color: rgba(255, 255, 255, 20);
        color: #ffffff;
        border: 1.5px solid rgba(255, 158, 216, 50);
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 13px;
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 1.5px solid {PINK_GLOW};
        background-color: rgba(255, 255, 255, 30);
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: rgba(55, 25, 75, 250);
        color: #ffffff;
        border: 1px solid {GLASS_BORDER_STRONG};
        border-radius: 6px;
        selection-background-color: rgba(200, 80, 192, 100);
    }}
"""

# ===== 按钮 =====
def button_style(color=PURPLE_MAIN, hover_color=None):
    if hover_color is None:
        hover_color = PURPLE_DEEP
    return f"""
        QPushButton {{
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {color}, stop:1 {hover_color});
            color: #ffffff;
            border: none;
            padding: 8px 24px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {hover_color}, stop:1 {color});
        }}
        QPushButton:pressed {{
            background-color: {hover_color};
        }}
    """

BTN_PRIMARY = button_style(PURPLE_MAIN, PINK_GLOW)
BTN_SUCCESS = button_style("#7B2FBE", "#C850C0")
BTN_DANGER = button_style("#C0336B", "#E8558A")
BTN_CANCEL = """
    QPushButton {
        background-color: rgba(255, 255, 255, 25);
        color: #ddd;
        border: 1.5px solid rgba(255, 158, 216, 40);
        padding: 8px 24px;
        border-radius: 8px;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: rgba(255, 255, 255, 40);
        border: 1.5px solid rgba(255, 158, 216, 80);
    }
"""

# ===== 表格 =====
TABLE_STYLE = f"""
    QTableWidget {{
        background-color: rgba(255, 255, 255, 15);
        alternate-background-color: rgba(255, 255, 255, 8);
        gridline-color: rgba(255, 158, 216, 30);
        color: #f0e6f6;
        font-size: 12px;
        border: 1px solid rgba(255, 158, 216, 40);
        border-radius: 8px;
    }}
    QTableWidget::item {{
        padding: 4px;
    }}
    QTableWidget::item:selected {{
        background-color: rgba(200, 80, 192, 80);
    }}
    QHeaderView::section {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {PURPLE_MAIN}, stop:1 {PURPLE_DEEP});
        color: #ffffff;
        font-weight: bold;
        padding: 8px;
        border: none;
        font-size: 13px;
    }}
"""

# ===== 列表 =====
LIST_STYLE = f"""
    QListWidget {{
        background-color: rgba(255, 255, 255, 15);
        color: #f0e6f6;
        border: 1.5px solid rgba(255, 158, 216, 40);
        border-radius: 8px;
        font-size: 13px;
        padding: 4px;
    }}
    QListWidget::item {{
        padding: 8px 10px;
        border-radius: 6px;
    }}
    QListWidget::item:selected {{
        background-color: rgba(255, 110, 199, 60);
        color: #ffffff;
    }}
    QListWidget::item:hover {{
        background-color: rgba(255, 158, 216, 30);
    }}
"""

# ===== 进度条 =====
PROGRESS_STYLE = f"""
    QProgressBar {{
        background-color: rgba(255, 255, 255, 20);
        border: none;
        border-radius: 3px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {PINK_LIGHT}, stop:1 {PURPLE_MAIN});
        border-radius: 3px;
    }}
"""

# ===== 周课表课程颜色（粉紫系） =====
COURSE_COLORS = [
    "#E891C8",  # 粉红
    "#B98EE8",  # 浅紫
    "#9D6EC8",  # 深紫
    "#E8A0B0",  # 玫粉
    "#C0A0E8",  # 薰衣草
    "#D890E0",  # 粉紫
    "#B080D8",  # 暗紫
    "#E89898",  # 珊瑚粉
]

# ===== 消息框 =====
MESSAGEBOX_STYLE = f"""
    QMessageBox {{
        background-color: rgba(60, 28, 80, 255);
    }}
    QMessageBox QLabel {{
        color: #f0e6f6;
        font-size: 13px;
    }}
    QMessageBox QPushButton {{
        background-color: rgba(200, 80, 192, 60);
        color: #ffffff;
        border: 1px solid rgba(255, 158, 216, 60);
        padding: 6px 20px;
        border-radius: 6px;
        font-size: 13px;
        min-width: 60px;
    }}
    QMessageBox QPushButton:hover {{
        background-color: rgba(200, 80, 192, 100);
    }}
"""

# ===== 全局应用样式 =====
APP_GLOBAL = f"""
    * {{
        font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    }}
    QToolTip {{
        background-color: rgba(55, 25, 75, 240);
        color: #f0e6f6;
        border: 1px solid {GLASS_BORDER_STRONG};
        border-radius: 6px;
        padding: 4px 8px;
    }}
"""
