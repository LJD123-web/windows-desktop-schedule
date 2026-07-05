"""悬浮窗课程表 - 主入口

功能：
- 悬浮窗常驻桌面，显示今日课程
- 半透明置顶，鼠标悬停恢复
- 右键菜单：刷新 / 周课表 / 添加 / 编辑 / 图片导入 / 退出
- 双击展开完整周课表
- 系统托盘图标
"""

import sys
import os

# 确保能 import 同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PySide6.QtCore import Qt

from floating_window import FloatingWindow


def create_tray_icon():
    """创建一个简易的托盘图标（程序生成，不依赖外部图片）"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#4a90d9"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(8, 8, 48, 48, 12, 12)
    painter.setPen(QColor("white"))
    font = painter.font()
    font.setPixelSize(28)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "课")
    painter.end()
    return QIcon(pixmap)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("悬浮窗课程表")

    # 高 DPI 支持
    app.setAttribute(Qt.AA_EnableHighDpiScaling)

    # === 悬浮窗 ===
    window = FloatingWindow()
    window.show()

    # 初始位置：屏幕右上角
    screen = app.primaryScreen().geometry()
    window.move(screen.width() - window.width() - 20, 80)

    # === 系统托盘 ===
    tray_icon = create_tray_icon()
    tray = QSystemTrayIcon(tray_icon, app)
    tray.setToolTip("悬浮窗课程表")

    tray_menu = QMenu()
    act_show = QAction("显示/隐藏", tray_menu)
    act_show.triggered.connect(
        lambda: window.show() if window.isHidden() else window.hide()
    )
    tray_menu.addAction(act_show)

    act_quit = QAction("退出", tray_menu)
    act_quit.triggered.connect(app.quit)
    tray_menu.addAction(act_quit)

    tray.setContextMenu(tray_menu)
    tray.show()

    # 托盘点击切换显示
    def on_tray_activated(reason):
        if reason == QSystemTrayIcon.Trigger:
            if window.isVisible():
                window.hide()
            else:
                window.show()

    tray.activated.connect(on_tray_activated)

    # 悬浮窗退出信号
    window.request_quit.connect(app.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
