"""课程表数据存储模块 - JSON 持久化"""

import json
import os
from datetime import datetime

# 数据文件路径（放在用户目录下，确保数据不丢）
DATA_DIR = os.path.join(os.path.expanduser("~"), ".floating-schedule")
DATA_FILE = os.path.join(DATA_DIR, "schedule.json")

# 默认节次时间表（可自定义）
DEFAULT_PERIODS = [
    {"start": "08:00", "end": "08:45"},
    {"start": "08:55", "end": "09:40"},
    {"start": "10:00", "end": "10:45"},
    {"start": "10:55", "end": "11:40"},
    {"start": "14:00", "end": "14:45"},
    {"start": "14:55", "end": "15:40"},
    {"start": "16:00", "end": "16:45"},
    {"start": "16:55", "end": "17:40"},
    {"start": "19:00", "end": "19:45"},
    {"start": "19:55", "end": "20:40"},
    {"start": "20:50", "end": "21:35"},
    {"start": "21:45", "end": "22:30"},
]

DAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _ensure_dir():
    """确保数据目录存在"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_data():
    """加载课程表数据，不存在则返回空数据"""
    _ensure_dir()
    if not os.path.exists(DATA_FILE):
        return {"courses": [], "periods": DEFAULT_PERIODS.copy()}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"courses": [], "periods": DEFAULT_PERIODS.copy()}


def save_data(data):
    """保存课程表数据"""
    _ensure_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_today_courses():
    """获取今天的课程，按节次排序"""
    data = load_data()
    today = datetime.now().weekday() + 1  # Monday=1 ... Sunday=7
    courses = [c for c in data["courses"] if c.get("day", 0) == today]
    courses.sort(key=lambda c: c.get("start_period", 0))
    return courses, data.get("periods", DEFAULT_PERIODS)


def get_week_courses():
    """获取整周课程"""
    data = load_data()
    return data["courses"], data.get("periods", DEFAULT_PERIODS)


def add_course(course):
    """添加一门课程"""
    data = load_data()
    data["courses"].append(course)
    save_data(data)


def update_course(index, course):
    """更新一门课程"""
    data = load_data()
    if 0 <= index < len(data["courses"]):
        data["courses"][index] = course
        save_data(data)


def delete_course(index):
    """删除一门课程"""
    data = load_data()
    if 0 <= index < len(data["courses"]):
        data["courses"].pop(index)
        save_data(data)


def replace_all_courses(courses, periods=None):
    """替换全部课程（用于 OCR 导入）"""
    data = load_data()
    data["courses"] = courses
    if periods:
        data["periods"] = periods
    save_data(data)


def get_current_period():
    """根据当前时间判断现在是第几节课"""
    data = load_data()
    periods = data.get("periods", DEFAULT_PERIODS)
    now = datetime.now().strftime("%H:%M")
    for i, p in enumerate(periods):
        if p["start"] <= now <= p["end"]:
            return i + 1
    return None
