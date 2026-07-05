"""图片课程表 OCR 识别导入模块 - 粉紫色玻璃风格

支持两种 OCR 引擎：
1. PaddleOCR（优先，中文识别效果好）
2. Tesseract（备选，需单独安装）
"""

import re
import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QProgressBar, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QColor, QFont

import storage
import theme

# ===== OCR 引擎检测 =====

_ocr_engine = None

def _detect_ocr_engine():
    global _ocr_engine
    if _ocr_engine is not None:
        return _ocr_engine

    try:
        from paddleocr import PaddleOCR
        _ocr_engine = "paddle"
        return _ocr_engine
    except ImportError:
        pass

    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        _ocr_engine = "tesseract"
        return _ocr_engine
    except Exception:
        pass

    _ocr_engine = "none"
    return _ocr_engine


class OCRWorker(QThread):
    finished_ocr = Signal(list)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def run(self):
        engine = _detect_ocr_engine()
        if engine == "none":
            self.error.emit(
                "未检测到 OCR 引擎。\n\n"
                "请安装以下任一引擎：\n"
                "  pip install paddleocr paddlepaddle\n"
                "  或安装 Tesseract + pip install pytesseract"
            )
            return

        try:
            if engine == "paddle":
                results = self._run_paddle()
            else:
                results = self._run_tesseract()
            self.finished_ocr.emit(results)
        except Exception as e:
            self.error.emit(f"识别失败：{e}")

    def _run_paddle(self):
        self.progress.emit("正在加载 PaddleOCR 模型...")
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)

        self.progress.emit("正在识别图片...")
        result = ocr.ocr(self.image_path, cls=True)

        texts = []
        if result and result[0]:
            for line in result[0]:
                box = line[0]
                text = line[1][0]
                texts.append((text, box))
        return texts

    def _run_tesseract(self):
        self.progress.emit("正在使用 Tesseract 识别...")
        import pytesseract
        from PIL import Image

        img = Image.open(self.image_path)
        data = pytesseract.image_to_data(
            img, lang="chi_sim+eng", output_type=pytesseract.Output.DICT
        )

        texts = []
        for i in range(len(data["text"])):
            t = data["text"][i].strip()
            if t:
                x = data["left"][i]
                y = data["top"][i]
                w = data["width"][i]
                h = data["height"][i]
                box = [[x, y], [x+w, y], [x+w, y+h], [x, y+h]]
                texts.append((t, box))
        return texts


class OCRImportDialog(QDialog):
    """图片导入对话框 - 粉紫玻璃风"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("从图片导入课程表")
        self.setModal(True)
        self.resize(820, 620)
        self._image_path = None
        self._ocr_texts = []
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(
            theme.DIALOG_BASE + theme.INPUT_STYLE + theme.TABLE_STYLE + theme.MESSAGEBOX_STYLE
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # 说明
        hint = QLabel(
            "📷 选择课程表截图，自动识别并导入\n"
            "提示：截图越清晰、排版越规整，识别效果越好"
        )
        hint.setStyleSheet(
            f"font-size: 13px; color: {theme.LAVENDER}; padding: 4px;"
        )
        layout.addWidget(hint)

        # 选择图片按钮
        btn_layout = QHBoxLayout()
        self._select_btn = QPushButton("📁  选择图片")
        self._select_btn.setStyleSheet(theme.BTN_PRIMARY)
        self._select_btn.setCursor(Qt.PointingHandCursor)
        self._select_btn.clicked.connect(self._on_select_image)
        btn_layout.addWidget(self._select_btn)

        self._path_label = QLabel("未选择图片")
        self._path_label.setStyleSheet(
            f"color: rgba(255,158,216,150); font-size: 11px;"
        )
        btn_layout.addWidget(self._path_label)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 进度条
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(6)
        self._progress.setStyleSheet(theme.PROGRESS_STYLE)
        layout.addWidget(self._progress)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(
            f"color: {theme.PINK_LIGHT}; font-size: 12px;"
        )
        layout.addWidget(self._status_label)

        # 识别结果表格
        result_group = QGroupBox("🔍 识别结果（可直接编辑修正）")
        result_layout = QVBoxLayout(result_group)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["课程名", "地点", "星期", "节次"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(theme.TABLE_STYLE)
        result_layout.addWidget(self._table)

        layout.addWidget(result_group)

        # 操作按钮
        op_layout = QHBoxLayout()
        add_row_btn = QPushButton("+ 添加一行")
        add_row_btn.setStyleSheet(theme.BTN_CANCEL)
        add_row_btn.setCursor(Qt.PointingHandCursor)
        add_row_btn.clicked.connect(self._add_empty_row)
        op_layout.addWidget(add_row_btn)

        del_row_btn = QPushButton("🗑 删除选中行")
        del_row_btn.setStyleSheet(theme.BTN_DANGER)
        del_row_btn.setCursor(Qt.PointingHandCursor)
        del_row_btn.clicked.connect(self._del_row)
        op_layout.addWidget(del_row_btn)

        op_layout.addStretch()
        layout.addLayout(op_layout)

        # 底部
        bottom = QHBoxLayout()
        bottom.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(theme.BTN_CANCEL)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        bottom.addWidget(cancel_btn)

        import_btn = QPushButton("✓  导入课程表")
        import_btn.setStyleSheet(theme.BTN_SUCCESS)
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.clicked.connect(self._on_import)
        bottom.addWidget(import_btn)
        layout.addLayout(bottom)

    def _on_select_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择课程表图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not path:
            return

        self._image_path = path
        self._path_label.setText(os.path.basename(path))
        self._start_ocr()

    def _start_ocr(self):
        self._select_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._status_label.setText("准备识别...")

        self._worker = OCRWorker(self._image_path)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ocr.connect(self._on_ocr_done)
        self._worker.error.connect(self._on_ocr_error)
        self._worker.start()

    def _on_progress(self, msg):
        self._status_label.setText(msg)
        self._progress.setRange(0, 0)

    def _on_ocr_done(self, texts):
        self._progress.setVisible(False)
        self._select_btn.setEnabled(True)
        self._ocr_texts = texts

        if not texts:
            self._status_label.setText("未识别到文字，请手动添加或换张图")
            return

        self._status_label.setText(
            f"识别到 {len(texts)} 个文本块，正在解析课程..."
        )
        courses = self._parse_courses(texts)

        self._table.setRowCount(0)
        for c in courses:
            self._add_table_row(
                c.get("name", ""),
                c.get("location", ""),
                storage.DAYS[c.get("day", 0) - 1] if 0 < c.get("day", 0) <= 7 else "",
                f"{c.get('start_period','')}-{c.get('end_period','')}"
            )

        self._status_label.setText(
            f"解析完成！共 {len(courses)} 条课程，请检查后点击「导入」"
        )

    def _on_ocr_error(self, msg):
        self._progress.setVisible(False)
        self._select_btn.setEnabled(True)
        self._status_label.setText("")
        QMessageBox.warning(self, "识别失败", msg)

    def _parse_courses(self, texts):
        if not texts:
            return []

        sorted_texts = sorted(texts, key=lambda t: t[1][0][1])
        rows = []
        current_row = [sorted_texts[0]]
        current_y = sorted_texts[0][1][0][1]
        row_height = 30

        for text, box in sorted_texts[1:]:
            y = box[0][1]
            if abs(y - current_y) < row_height:
                current_row.append((text, box))
            else:
                rows.append(current_row)
                current_row = [(text, box)]
                current_y = y
        rows.append(current_row)

        for r in rows:
            r.sort(key=lambda t: t[1][0][0])

        courses = []
        day_keywords = {
            "周一": 1, "星期一": 1, "一": 1, "Mon": 1, "MON": 1,
            "周二": 2, "星期二": 2, "二": 2, "Tue": 2, "TUE": 2,
            "周三": 3, "星期三": 3, "三": 3, "Wed": 3, "WED": 3,
            "周四": 4, "星期四": 4, "四": 4, "Thu": 4, "THU": 4,
            "周五": 5, "星期五": 5, "五": 5, "Fri": 5, "FRI": 5,
            "周六": 6, "星期六": 6, "六": 6, "Sat": 6, "SAT": 6,
            "周日": 7, "星期日": 7, "星期天": 7, "日": 7, "Sun": 7, "SUN": 7,
        }

        col_days = {}
        if rows:
            header = rows[0]
            for text, box in header:
                for kw, day in day_keywords.items():
                    if kw in text:
                        col_days[box[0][0]] = day
                        break

        period_pattern = re.compile(r'第?\s*(\d+)\s*[-~～]\s*(\d+)\s*节?')
        single_period = re.compile(r'第?\s*(\d+)\s*节')

        for row in rows[1:] if col_days else rows:
            row_x = row[0][1][0][0] if row else 0
            day = 0
            for col_x, col_day in sorted(col_days.items()):
                if row_x >= col_x - 20:
                    day = col_day

            full_text = " ".join(t for t, _ in row)

            sp, ep = 0, 0
            m = period_pattern.search(full_text)
            if m:
                sp, ep = int(m.group(1)), int(m.group(2))
            else:
                m = single_period.search(full_text)
                if m:
                    sp = ep = int(m.group(1))

            name = ""
            location = ""
            for text, box in row:
                if text.strip().isdigit():
                    continue
                if any(kw in text for kw in day_keywords):
                    continue
                if period_pattern.search(text) or single_period.search(text):
                    continue
                if any(k in text for k in ["教", "楼", "室", "号", "区", "层"]):
                    location = text.strip()
                elif not name:
                    name = text.strip()

            if name or day:
                if not day:
                    day = 1
                if not sp:
                    sp = 1
                if not ep:
                    ep = sp
                courses.append({
                    "name": name or "未命名",
                    "location": location,
                    "day": day,
                    "start_period": sp,
                    "end_period": ep,
                    "teacher": "",
                    "weeks": "",
                })

        return courses

    def _add_table_row(self, name, loc, day, period):
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(name))
        self._table.setItem(row, 1, QTableWidgetItem(loc))

        day_combo = QComboBox()
        for d in storage.DAYS:
            day_combo.addItem(d)
        if day in storage.DAYS:
            day_combo.setCurrentText(day)
        self._table.setCellWidget(row, 2, day_combo)

        self._table.setItem(row, 3, QTableWidgetItem(period))

    def _add_empty_row(self):
        self._add_table_row("", "", "周一", "1-2")

    def _del_row(self):
        row = self._table.currentRow()
        if row >= 0:
            self._table.removeRow(row)

    def _on_import(self):
        courses = []
        for row in range(self._table.rowCount()):
            name_item = self._table.item(row, 0)
            loc_item = self._table.item(row, 1)
            day_widget = self._table.cellWidget(row, 2)
            period_item = self._table.item(row, 3)

            name = name_item.text().strip() if name_item else ""
            if not name:
                continue

            loc = loc_item.text().strip() if loc_item else ""
            day_text = day_widget.currentText() if day_widget else "周一"
            day = storage.DAYS.index(day_text) + 1 if day_text in storage.DAYS else 1

            period_text = period_item.text().strip() if period_item else "1"
            sp, ep = 1, 1
            m = re.match(r'(\d+)\s*[-~～]\s*(\d+)', period_text)
            if m:
                sp, ep = int(m.group(1)), int(m.group(2))
            elif period_text.isdigit():
                sp = ep = int(period_text)

            courses.append({
                "name": name,
                "location": loc,
                "day": day,
                "start_period": sp,
                "end_period": ep,
                "teacher": "",
                "weeks": "",
            })

        if not courses:
            QMessageBox.warning(self, "提示", "没有有效的课程数据")
            return

        reply = QMessageBox.question(
            self, "确认导入",
            f"将导入 {len(courses)} 门课程。\n"
            "这会替换当前所有课程，是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            storage.replace_all_courses(courses)
            QMessageBox.information(
                self, "成功",
                f"已导入 {len(courses)} 门课程！"
            )
            self.accept()
