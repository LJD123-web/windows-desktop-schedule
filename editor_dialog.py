"""课程编辑对话框 - 粉紫色玻璃风格"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QPushButton, QListWidget, QFormLayout,
    QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt

import storage
import theme


class EditorDialog(QDialog):
    """课程编辑器 - 粉紫玻璃风"""

    def __init__(self, parent=None, edit_mode=False):
        super().__init__(parent)
        self.setWindowTitle("编辑课程表" if edit_mode else "添加课程")
        self.setModal(True)
        self.resize(540, 620)
        self._edit_mode = edit_mode
        self._init_ui()
        if edit_mode:
            self._load_courses()

    def _init_ui(self):
        self.setStyleSheet(theme.DIALOG_BASE + theme.INPUT_STYLE + theme.MESSAGEBOX_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # === 添加/编辑表单 ===
        form_group = QGroupBox("🌸 课程信息")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(10)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("如：高等数学")
        form_layout.addRow("课程名：", self._name_input)

        self._teacher_input = QLineEdit()
        self._teacher_input.setPlaceholderText("如：张老师")
        form_layout.addRow("教师：", self._teacher_input)

        self._location_input = QLineEdit()
        self._location_input.setPlaceholderText("如：教1-101")
        form_layout.addRow("地点：", self._location_input)

        self._day_combo = QComboBox()
        for d in storage.DAYS:
            self._day_combo.addItem(d)
        form_layout.addRow("星期：", self._day_combo)

        period_layout = QHBoxLayout()
        self._start_spin = QSpinBox()
        self._start_spin.setRange(1, 20)
        self._start_spin.setValue(1)
        self._end_spin = QSpinBox()
        self._end_spin.setRange(1, 20)
        self._end_spin.setValue(2)
        period_layout.addWidget(self._start_spin)
        period_layout.addWidget(QLabel("~"))
        period_layout.addWidget(self._end_spin)
        period_layout.addStretch()
        form_layout.addRow("节次：", period_layout)

        self._weeks_input = QLineEdit()
        self._weeks_input.setPlaceholderText("如：1-16 或 1,3,5,7-16（留空=全周）")
        form_layout.addRow("周次：", self._weeks_input)

        layout.addWidget(form_group)

        # 添加按钮
        add_btn = QPushButton("➕  添加课程")
        add_btn.setStyleSheet(theme.BTN_PRIMARY)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._on_add)
        layout.addWidget(add_btn)

        # === 课程列表（编辑模式）===
        if self._edit_mode:
            list_group = QGroupBox("📝 已有课程")
            list_layout = QVBoxLayout(list_group)
            self._course_list = QListWidget()
            self._course_list.setStyleSheet(theme.LIST_STYLE)
            list_layout.addWidget(self._course_list)

            del_btn = QPushButton("🗑  删除选中课程")
            del_btn.setStyleSheet(theme.BTN_DANGER)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.clicked.connect(self._on_delete)
            list_layout.addWidget(del_btn)

            layout.addWidget(list_group)

        # 底部
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("✓  完成")
        ok_btn.setStyleSheet(theme.BTN_SUCCESS)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    def _load_courses(self):
        courses, _ = storage.get_week_courses()
        self._course_list.clear()
        for i, c in enumerate(courses):
            text = (f"[{storage.DAYS[c.get('day',0)-1]}] "
                    f"第{c.get('start_period','')}-{c.get('end_period','')}节 "
                    f"{c.get('name','')} "
                    f"@{c.get('location','')}")
            self._course_list.addItem(text)
            item = self._course_list.item(self._course_list.count() - 1)
            item.setData(Qt.UserRole, i)

    def _on_add(self):
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入课程名")
            return

        course = {
            "name": name,
            "teacher": self._teacher_input.text().strip(),
            "location": self._location_input.text().strip(),
            "day": self._day_combo.currentIndex() + 1,
            "start_period": self._start_spin.value(),
            "end_period": self._end_spin.value(),
            "weeks": self._weeks_input.text().strip(),
        }
        storage.add_course(course)
        QMessageBox.information(self, "成功", f"已添加：{name}")

        self._name_input.clear()
        self._teacher_input.clear()
        self._location_input.clear()
        self._weeks_input.clear()

        if self._edit_mode:
            self._load_courses()

    def _on_delete(self):
        if not hasattr(self, "_course_list"):
            return
        current = self._course_list.currentRow()
        if current < 0:
            QMessageBox.warning(self, "提示", "请先选中要删除的课程")
            return
        item = self._course_list.item(current)
        idx = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定删除该课程吗？\n{item.text()}",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            storage.delete_course(idx)
            self._load_courses()

    def get_course(self):
        """获取输入的课程数据"""
        return {
            "name": self._name_input.text().strip() or "未命名",
            "teacher": self._teacher_input.text().strip(),
            "location": self._location_input.text().strip(),
            "day": self._day_combo.currentIndex() + 1,
            "start_period": self._start_spin.value(),
            "end_period": self._end_spin.value(),
            "weeks": self._weeks_input.text().strip(),
        }
