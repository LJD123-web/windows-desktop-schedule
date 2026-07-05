"""图片课程表 OCR 识别导入模块 - 粉紫色玻璃风格

支持三种 OCR 引擎（按优先级）：
1. PaddleOCR（中文识别效果最好）
2. EasyOCR（兼容性好，PyTorch 后端）
3. Tesseract（备选，需单独安装）
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

# ===== 后处理纠错 =====

# 常见大学课程名词典（用于 OCR 识别纠错）
COURSE_DICT = [
    "操作系统", "移动应用程序开发", "通讯与网络", "计算机网络",
    "软件项目管理", "软件构造", "软件工程", "跨文化交际",
    "高等数学", "大学物理", "大学物理实验", "线性代数", "概率论",
    "数据结构", "C语言程序设计", "英语", "体育", "思政",
    "Java程序设计", "Python程序设计", "数据库原理", "编译原理",
    "计算机组成原理", "人工智能", "机器学习", "深度学习",
    "软件测试", "软件需求分析", "软件体系结构", "面向对象程序设计",
    "算法设计与分析", "离散数学", "数值分析", "运筹学",
    "马克思主义基本原理", "毛泽东思想", "形式与政策",
    "数字逻辑", "电子商务", "网络安全", "云计算",
]


def _edit_distance(s1, s2):
    """计算两个字符串的编辑距离"""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n]


def _fix_location(text):
    """地点纠错：修复 OCR 常见误识
    - 1号带/裁/提/搬 → 1号楼
    - 1号110教室 → 1号楼110教室（"楼"被漏识）
    - 数室/款室/软室 → 教室
    """
    # "号"后面如果不是"楼"且后面跟数字，替换为"楼"
    text = re.sub(r'(\d+号)([^\d楼])(\d+)', r'\1楼\3', text)
    # "号"后面直接跟数字（"楼"被漏识）：1号110 → 1号楼110
    text = re.sub(r'(\d+)号(\d+(?:教室|机房|实验室))', r'\1号楼\2', text)
    # 数字后面非"教"+室 → 教室
    text = re.sub(r'(\d+)([^教\n])室', r'\1教室', text)
    return text


def _match_course_prefix(text):
    """前缀匹配：从文本开头找最匹配的课程名

    策略：
    1. 精确前缀匹配（文本以某课程名开头，优先最长）
    2. 模糊前缀匹配（编辑距离 <= 阈值）
    返回 (课程名, 剩余文本)
    """
    text = text.strip()
    if not text:
        return "", ""

    # 1. 精确前缀匹配（优先最长）
    for course in sorted(COURSE_DICT, key=len, reverse=True):
        if text.startswith(course):
            return course, text[len(course):].strip()

    # 2. 模糊前缀匹配
    best_match = None
    best_dist = 999
    best_prefix_len = 0

    for course in COURSE_DICT:
        for extra in range(0, 3):
            prefix_len = len(course) + extra
            if prefix_len > len(text):
                prefix_len = len(text)
            prefix = text[:prefix_len]
            # 前缀长度至少是课程名长度的 60%
            if prefix_len < len(course) * 0.6:
                continue
            dist = _edit_distance(prefix, course)
            # 短课程名（<=3字）只允许1个编辑距离
            if len(course) <= 3:
                threshold = 1
            else:
                threshold = max(2, len(course) * 0.5)
            if dist <= threshold and dist < best_dist:
                best_dist = dist
                best_match = course
                best_prefix_len = prefix_len

    if best_match:
        return best_match, text[best_prefix_len:].strip()

    # 3. 兜底：返回原文
    return text, ""


def _extract_teacher(remaining):
    """从剩余文本提取教师名，清理前导噪声字"""
    remaining = remaining.strip()
    if not remaining:
        return ""
    # 教师名通常是2-3个中文字，取末尾
    m = re.search(r'([\u4e00-\u9fa5]{2,3})$', remaining)
    if m:
        teacher = m.group(1)
        # 清理前导噪声字（OCR 把"考查"识成"考宣"等残留）
        teacher_noise = set('宣造始络栋晚患款软考试为')
        while teacher and teacher[0] in teacher_noise and len(teacher) > 2:
            teacher = teacher[1:]
        return teacher
    return ""

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
        from rapidocr_onnxruntime import RapidOCR
        _ocr_engine = "rapidocr"
        return _ocr_engine
    except ImportError:
        pass

    try:
        import easyocr
        _ocr_engine = "easyocr"
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
                "  pip install rapidocr-onnxruntime（推荐）\n"
                "  pip install paddleocr paddlepaddle\n"
                "  pip install easyocr\n"
                "  或安装 Tesseract + pip install pytesseract"
            )
            return

        try:
            if engine == "paddle":
                results = self._run_paddle()
            elif engine == "rapidocr":
                results = self._run_rapidocr()
            elif engine == "easyocr":
                results = self._run_easyocr()
            else:
                results = self._run_tesseract()
            self.finished_ocr.emit(results)
        except Exception as e:
            self.error.emit(f"识别失败：{e}")

    def _run_rapidocr(self):
        self.progress.emit("正在加载 RapidOCR 模型...")
        from rapidocr_onnxruntime import RapidOCR

        engine = RapidOCR()
        self.progress.emit("正在识别图片...")
        result, elapse = engine(self.image_path)

        texts = []
        if result:
            for item in result:
                box = item[0]
                text = item[1]
                if text and text.strip():
                    # 后处理纠错：修复地点常见 OCR 误识
                    text = _fix_location(text.strip())
                    box = [[float(p[0]), float(p[1])] for p in box]
                    texts.append((text, box))
        return texts

    def _run_paddle(self):
        self.progress.emit("正在加载 PaddleOCR 模型...")
        from paddleocr import PaddleOCR
        # PaddleOCR 3.x 新 API：show_log 被移除，use_angle_cls 改为 use_textline_orientation
        try:
            ocr = PaddleOCR(use_textline_orientation=True, lang="ch")
        except Exception:
            # 兜底：尝试旧版 API
            try:
                ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
            except TypeError:
                ocr = PaddleOCR(use_angle_cls=True, lang="ch")

        self.progress.emit("正在识别图片...")
        try:
            result = ocr.ocr(self.image_path, cls=True)
        except TypeError:
            # PaddleOCR 3.x：cls 参数已移除，方向识别由 use_textline_orientation 控制
            result = ocr.ocr(self.image_path)

        texts = []
        # PaddleOCR 3.x 返回结构：[{ "rec_texts": [...], "rec_scores": [...], "dt_polys": [...] }, ...]
        if result:
            page = result[0] if isinstance(result, list) else result
            if isinstance(page, dict):
                rec_texts = page.get("rec_texts", []) or []
                polys = page.get("dt_polys", []) or []
                for text, box in zip(rec_texts, polys):
                    if text:
                        # 转换 numpy array 为 list
                        try:
                            box = [[float(p[0]), float(p[1])] for p in box]
                        except Exception:
                            continue
                        texts.append((text, box))
            else:
                # 旧版返回结构
                for line in page:
                    try:
                        box = line[0]
                        text = line[1][0]
                        texts.append((text, box))
                    except Exception:
                        continue
        return texts

    def _run_easyocr(self):
        self.progress.emit("正在加载 EasyOCR 模型（首次需下载）...")
        import easyocr

        # 支持中文简体+英文，GPU 不可用时自动 CPU
        reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)

        self.progress.emit("正在识别图片...")
        result = reader.readtext(self.image_path)

        texts = []
        for item in result:
            # EasyOCR 返回格式: (bbox, text, confidence)
            # bbox 是 4 个点的列表 [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
            box = item[0]
            text = item[1]
            if text and text.strip():
                box = [[float(p[0]), float(p[1])] for p in box]
                texts.append((text.strip(), box))
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

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(["课程名", "地点", "星期", "节次", "教师", "周次"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
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
                f"{c.get('start_period','')}-{c.get('end_period','')}",
                c.get("teacher", ""),
                c.get("weeks", "")
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
        """解析 OCR 识别结果为课程列表（v3）

        支持两种课表格式：
        1. 分行格式：课程名和地点在不同行（标准课表）
        2. 紧凑单行格式：课程名+考试类型+教师+周次+节次+地点 全在一行（高校教务系统常见）
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
        period_range_re = re.compile(r'第?\s*(\d{1,2})\s*[-~～]\s*(\d{1,2})\s*节')
        period_single_re = re.compile(r'第?\s*(\d{1,2})\s*节')
        # 紧凑格式专用：[1-16]周 里的节次 3-4节
        compact_period_re = re.compile(r'(\d{1,2})\s*[-~～]\s*(\d{1,2})\s*节')
        # 周次 [1-16]周 / [1-16]周双周
        week_range_re = re.compile(r'\[(\d{1,2})\s*[-~～]\s*(\d{1,2})\]\s*周(单周|双周|单同|双同)?')
        # 地点：1号楼121教室 / 1号楼121机房 / 1号楼230数室(OCR误识)
        location_re = re.compile(r'(\d+号楼\d+(?:教室|机房|实验室|\S{1,2}))')
        # 宽松：1号X230Y室 (OCR把"楼"误识为"带/裁/提/搬"等)
        location_re2 = re.compile(r'(\d+号[\u4e00-\u9fa5]\d+[\u4e00-\u9fa5]{1,2})')
        # 考试类型：只匹配"考试"和"考查"整体词，不匹配单字"考"/"试"避免误删课程名
        exam_type_re = re.compile(r'[★]?(考试|考查)')
        location_keywords = ["教", "楼", "室", "号", "区", "层", "机房", "实验楼", "实验室", "操场", "体育馆", "线上"]

        all_sorted = sorted(texts, key=lambda t: t[1][0][1])

        # ===== 1. 检测表头 + 列区间 =====
        col_ranges = {}
        header_y = -999
        day_x_centers = []
        for text, box in all_sorted:
            for kw, day in day_keywords.items():
                if kw in text:
                    x_center = (box[0][0] + box[1][0]) / 2
                    day_x_centers.append((day, x_center))
                    if header_y < 0:
                        header_y = box[0][1]
                    break

        # 自适应列宽：取相邻列 X 间距的最小值 / 2（防止列间空隙被分到两列）
        day_x_centers.sort(key=lambda x: x[1])
        if len(day_x_centers) >= 2:
            gaps = [day_x_centers[i + 1][1] - day_x_centers[i][1]
                    for i in range(len(day_x_centers) - 1)]
            col_half_width = min(gaps) / 2 if gaps else 50
        else:
            col_half_width = 50

        for day, x_center in day_x_centers:
            col_ranges[day] = (x_center - col_half_width, x_center + col_half_width)

        if not col_ranges:
            return []

        # ===== 2. 尝试紧凑格式解析 =====
        # 紧凑格式特征：文本块中同时包含 节次正则 和 周次正则
        compact_texts = []
        for text, box in all_sorted:
            if compact_period_re.search(text) and week_range_re.search(text):
                compact_texts.append((text, box))

        if compact_texts:
            courses = OCRImportDialog._parse_compact_format(
                compact_texts, col_ranges, day_keywords,
                compact_period_re, week_range_re, location_re, location_re2, exam_type_re
            )
            # 去重：同一 (name, day, start_period, end_period) 只保留第一条
            seen = set()
            deduped = []
            for c in courses:
                key = (c["name"], c["day"], c["start_period"], c["end_period"])
                if key not in seen:
                    seen.add(key)
                    deduped.append(c)
            return deduped

        # ===== 3. 分行格式解析（原逻辑） =====
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

        if period_col_x is None:
            return []

        # 用节次列定义行边界
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

        # 逐行分配文本
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

                # 兜底：如果只识别到地点没识别到课程名，用第一个文本做课程名
                if not name and texts_in_col:
                    name = texts_in_col[0]
                    if not location and len(texts_in_col) > 1:
                        location = texts_in_col[1]

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

    @staticmethod
    def _parse_compact_format(compact_texts, col_ranges, day_keywords,
                               compact_period_re, week_range_re, location_re, location_re2, exam_type_re):
        """解析紧凑单行格式：课程名+考试类型+教师+周次+节次+地点 全在一行"""
        courses = []
        for text, box in compact_texts:
            # 1. 提取星期（根据 X 坐标分配列）
            x_center = (box[0][0] + box[1][0]) / 2
            assigned_day = 0
            for day, (x_min, x_max) in col_ranges.items():
                if x_min <= x_center <= x_max:
                    assigned_day = day
                    break
            if assigned_day == 0:
                continue

            # 2. 提取节次
            sp, ep = 0, 0
            m = compact_period_re.search(text)
            if m:
                sp, ep = int(m.group(1)), int(m.group(2))
                if sp > 20 or ep > 20:
                    sp, ep = 0, 0
            # 节次合理性：结束节次不应小于开始节次（OCR 把 8 误识为 6 等）
            if sp > 0 and ep < sp:
                ep = sp + 1

            # 3. 提取周次
            weeks = ""
            m = week_range_re.search(text)
            if m:
                week_start = m.group(1)
                week_end = m.group(2)
                week_mod = m.group(3) or ""
                weeks = f"{week_start}-{week_end}周"
                if "双" in week_mod:
                    weeks += "(双周)"
                elif "单" in week_mod:
                    weeks += "(单周)"

            # 4. 提取地点
            location = ""
            m = location_re.search(text)
            if m:
                location = m.group(1)
            else:
                m = location_re2.search(text)
                if m:
                    location = m.group(1)
                else:
                    # 号后面直接跟数字：1号110教室
                    m = re.search(r'(\d+号\d+[\u4e00-\u9fa5]{1,2})', text)
                    if m:
                        location = m.group(1)

            # 5. 提取课程名 + 教师（前缀匹配策略）
            # 去掉已提取的部分，剩余的就是 课程名+教师+考试类型
            remaining = text
            remaining = compact_period_re.sub('', remaining)
            remaining = week_range_re.sub('', remaining)
            remaining = location_re.sub('', remaining)
            remaining = location_re2.sub('', remaining)
            remaining = re.sub(r'(\d+号\d+[\u4e00-\u9fa5]{1,2})', '', remaining)
            remaining = exam_type_re.sub('', remaining)
            # 去掉多余符号和首尾噪声字
            remaining = re.sub(r'[★\[\]]', '', remaining)
            noise_chars = set('四★女男')
            while remaining and remaining[0] in noise_chars and len(remaining) > 3:
                remaining = remaining[1:]
            while remaining and remaining[-1] in noise_chars and len(remaining) > 3:
                remaining = remaining[:-1]
            remaining = remaining.strip()

            # 6. 前缀匹配课程名，剩余的提取教师名
            name, teacher_part = _match_course_prefix(remaining)
            teacher = _extract_teacher(teacher_part)

            if name:
                courses.append({
                    "name": name,
                    "location": location,
                    "day": assigned_day,
                    "start_period": sp if sp else 1,
                    "end_period": ep if ep else sp if sp else 1,
                    "teacher": teacher,
                    "weeks": weeks,
                })

        return courses

    def _add_table_row(self, name, loc, day, period, teacher="", weeks=""):
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
        self._table.setItem(row, 4, QTableWidgetItem(teacher))
        self._table.setItem(row, 5, QTableWidgetItem(weeks))

    def _add_empty_row(self):
        self._add_table_row("", "", "周一", "1-2", "", "")

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
            teacher_item = self._table.item(row, 4)
            weeks_item = self._table.item(row, 5)

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

            teacher = teacher_item.text().strip() if teacher_item else ""
            weeks = weeks_item.text().strip() if weeks_item else ""

            courses.append({
                "name": name,
                "location": loc,
                "day": day,
                "start_period": sp,
                "end_period": ep,
                "teacher": teacher,
                "weeks": weeks,
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
