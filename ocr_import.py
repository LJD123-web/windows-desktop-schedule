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

        hint = QLabel(
            "📷 选择课程表截图，自动识别并导入\n"
            "提示：截图越清晰、排版越规整，识别效果越好"
        )
        hint.setStyleSheet(
            f"font-size: 13px; color: {theme.LAVENDER}; padding: 4px;"
        )
        layout.addWidget(hint)

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

        result_group = QGroupBox("🔍 识别结果（可直接编辑修正）")
        result_layout = QVBoxLayout(result_group)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["课程名", "地点", "星期", "节次"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(theme.TABLE_STYLE)
        result_layout.addWidget(self._table)

        layout.addWidget(result_group)

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
        """解析 OCR 识别结果为课程列表（改进版 v2）

        策略：用节次列的 Y 坐标定义行边界，避免行聚类混乱
        """
        if not texts:
            return []

        day_keywords = {
            "周一": 1, "星期一": 1, "Mon": 1, "MON": 1,
            "周二": 2, "星期二": 2, "Tue": 2, "TUE": 2,
            "周三": 3, "星期三": 3, "Wed": 3, "WED": 3,
            "周四": 4, "星期四": 4, "Thu": 4, "THU": 4,
            "周五": 5, "星期五": 5, "Fri": 5, "FRI": 5,
            "周六": 6, "星期六": 6, "Sat": 6, "SAT": 6,
            "周日": 7, "星期日": 7, "星期天": 7, "Sun": 7, "SUN": 7,
        }
        period_range_re = re.compile(r'第?\s*(\d{1,2})\s*[-~～]\s*(\d{1,2})\s*节?')
        period_single_re = re.compile(r'第?\s*(\d{1,2})\s*节')
        location_keywords = ["教", "楼", "室", "号", "区", "层", "机房", "实验楼", "实验室", "操场", "体育馆", "线上"]

        all_sorted = sorted(texts, key=lambda t: t[1][0][1])

        # ===== 1. 检测表头 + 列区间 =====
        col_ranges = {}
        header_y = -999
        for text, box in all_sorted:
            for kw, day in day_keywords.items():
                if kw in text:
                    x_center = (box[0][0] + box[1][0]) / 2
                    col_ranges[day] = (x_center - 80, x_center + 80)
                    header_y = box[0][1]
                    break

        # 找节次列 X
        period_col_x = None
        for text, box in all_sorted:
            if "节" in text and len(text) <= 4:
                period_col_x = (box[0][0] + box[1][0]) / 2
                break
        if period_col_x is None:
            for text, box in all_sorted:
                if period_range_re.search(text) or period_single_re.search(text):
                    period_col_x = (box[0][0] + box[1][0]) / 2
                    break

        if not col_ranges or period_col_x is None:
            return []

        # ===== 2. 用节次列定义行边界 =====
        period_markers = []
        for text, box in all_sorted:
            x_center = (box[0][0] + box[1][0]) / 2
            if abs(x_center - period_col_x) > 60:
                continue
            sp, ep = 0, 0
            m = period_range_re.search(text)
            if m:
                sp, ep = int(m.group(1)), int(m.group(2))
                if sp > 20 or ep > 20 or sp > ep:
                    continue
            else:
                m = period_single_re.search(text)
                if m:
                    sp = ep = int(m.group(1))
                    if sp > 20:
                        continue
            if sp:
                y_center = (box[0][1] + box[2][1]) / 2
                period_markers.append((sp, ep, y_center))

        if not period_markers:
            return []
        period_markers.sort(key=lambda x: x[2])

        # ===== 3. 逐行分配文本 =====
        courses = []
        for idx, (sp, ep, row_y) in enumerate(period_markers):
            if idx + 1 < len(period_markers):
                y_max = (row_y + period_markers[idx + 1][2]) / 2
            else:
                y_max = row_y + 80
            y_min = row_y - 30

            col_texts = {}
            for text, box in all_sorted:
                y_center = (box[0][1] + box[2][1]) / 2
                if y_center < y_min or y_center > y_max:
                    continue
                if abs(y_center - header_y) < 40:
                    continue

                x_center = (box[0][0] + box[1][0]) / 2
                if abs(x_center - period_col_x) < 60:
                    continue
                if text.strip().isdigit():
                    continue
                if any(kw in text for kw in day_keywords):
                    continue

                assigned_day = 0
                for day, (x_min, x_max) in col_ranges.items():
                    if x_min <= x_center <= x_max:
                        assigned_day = day
                        break
                if assigned_day == 0:
                    continue

                if assigned_day not in col_texts:
                    col_texts[assigned_day] = []
                col_texts[assigned_day].append(text.strip())

            for day, texts_in_col in col_texts.items():
                name = ""
                location = ""
                for text in texts_in_col:
                    is_location = any(k in text for k in location_keywords)
                    if not is_location and re.match(r'^[\d]+[-‐－]?[\d]*[号室楼]?$', text.strip()):
                        is_location = True
                    if is_location:
                        if not location:
                            location = text.strip()
                    else:
                        if not name:
                            name = text.strip()
                        elif not location:
                            location = text.strip()

                if name:
                    courses.append({
                        "name": name,
                        "location": location,
                        "day": day,
                        "start_period": sp,
                        "end_period": ep if ep else sp,
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
