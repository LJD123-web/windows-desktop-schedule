"""模拟课程表 OCR 导入测试脚本

模拟一张真实课程表图片经 OCR 识别后的结果，
测试解析逻辑、数据存储、以及各种边界情况。
"""
import sys
import os
import json

# 修复 Windows 控制台编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import storage
from ocr_import import OCRImportDialog

# ===== 模拟 OCR 识别结果 =====
# 模拟一张典型的大学课程表截图，OCR 返回 (文字, 四点坐标) 列表
# 坐标格式: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] (左上、右上、右下、左下)

MOCK_OCR_RESULTS = [
    # === 表头行 (y≈30) ===
    ("节次",       [[20, 25], [80, 25], [80, 55], [20, 55]]),
    ("周一",       [[180, 25], [240, 25], [240, 55], [180, 55]]),
    ("周二",       [[340, 25], [400, 25], [400, 55], [340, 55]]),
    ("周三",       [[500, 25], [560, 25], [560, 55], [500, 55]]),
    ("周四",       [[660, 25], [720, 25], [720, 55], [660, 55]]),
    ("周五",       [[820, 25], [880, 25], [880, 55], [820, 55]]),

    # === 第1-2节 (y≈90) ===
    ("1-2",        [[30, 80], [70, 80], [70, 105], [30, 105]]),
    ("高等数学",    [[180, 80], [280, 80], [280, 105], [180, 105]]),
    ("教1-101",    [[180, 110], [260, 110], [260, 135], [180, 135]]),
    ("大学英语",    [[340, 80], [440, 80], [440, 105], [340, 105]]),
    ("教2-201",    [[340, 110], [420, 110], [420, 135], [340, 135]]),
    ("高等数学",    [[500, 80], [600, 80], [600, 105], [500, 105]]),
    ("教1-101",    [[500, 110], [580, 110], [580, 135], [500, 135]]),
    ("大学物理",    [[660, 80], [760, 80], [760, 105], [660, 105]]),
    ("教3-301",    [[660, 110], [740, 110], [740, 135], [660, 135]]),
    ("高等数学",    [[820, 80], [920, 80], [920, 105], [820, 105]]),
    ("教1-101",    [[820, 110], [900, 110], [900, 135], [820, 135]]),

    # === 第3-4节 (y≈170) ===
    ("3-4",        [[30, 160], [70, 160], [70, 185], [30, 185]]),
    ("大学物理",    [[180, 160], [280, 160], [280, 185], [180, 185]]),
    ("教3-301",    [[180, 190], [260, 190], [260, 215], [180, 215]]),
    ("程序设计基础", [[340, 160], [460, 160], [460, 185], [340, 185]]),
    ("机房A-201",  [[340, 190], [440, 190], [440, 215], [340, 215]]),
    ("体育",       [[500, 160], [560, 160], [560, 185], [500, 185]]),
    ("操场",       [[500, 190], [560, 190], [560, 215], [500, 215]]),
    ("程序设计基础", [[660, 160], [780, 160], [780, 185], [660, 185]]),
    ("机房A-201",  [[660, 190], [760, 190], [760, 215], [660, 215]]),
    ("大学英语",    [[820, 160], [920, 160], [920, 185], [820, 185]]),
    ("教2-201",    [[820, 190], [900, 190], [900, 215], [820, 215]]),

    # === 第5-6节 (y≈250) ===
    ("5-6",        [[30, 240], [70, 240], [70, 265], [30, 265]]),
    ("思想政治理论", [[180, 240], [300, 240], [300, 265], [180, 265]]),
    ("教4-401",    [[180, 270], [260, 270], [260, 295], [180, 295]]),
    # 周二空
    ("线性代数",    [[500, 240], [600, 240], [600, 265], [500, 265]]),
    ("教1-201",    [[500, 270], [580, 270], [580, 295], [500, 295]]),
    # 周四空
    ("数据结构",    [[820, 240], [920, 240], [920, 265], [820, 265]]),
    ("机房B-105",  [[820, 270], [920, 270], [920, 295], [820, 295]]),

    # === 第7-8节 (y≈330) ===
    ("7-8",        [[30, 320], [70, 320], [70, 345], [30, 345]]),
    # 周一空
    ("大学物理实验", [[340, 320], [460, 320], [460, 345], [340, 345]]),
    ("实验楼301",  [[340, 350], [440, 350], [440, 375], [340, 350]]),
    # 周三空
    ("高等数学",    [[660, 320], [760, 320], [760, 345], [660, 345]]),
    ("教1-101",    [[660, 350], [740, 350], [740, 375], [660, 350]]),
    # 周五空

    # === 第9-10节 (y≈410) ===
    ("9-10",       [[30, 400], [75, 400], [75, 425], [30, 425]]),
    ("程序设计实践", [[180, 400], [320, 400], [320, 425], [180, 425]]),
    ("机房A-201",  [[180, 430], [280, 430], [280, 455], [180, 430]]),
    # 其余空
]


def test_parsing():
    """测试 OCR 解析逻辑"""
    print("=" * 60)
    print("📋 测试 OCR 解析逻辑")
    print("=" * 60)
    print(f"模拟识别到 {len(MOCK_OCR_RESULTS)} 个文本块")
    print()

    # 用 OCRImportDialog 的解析方法（不弹窗）
    dlg = OCRImportDialog.__new__(OCRImportDialog)
    courses = dlg._parse_courses(MOCK_OCR_RESULTS)

    print(f"解析出 {len(courses)} 门课程：")
    print("-" * 60)
    for i, c in enumerate(courses):
        day_name = storage.DAYS[c.get("day", 0) - 1] if 0 < c.get("day", 0) <= 7 else "?"
        print(f"  [{i+1}] {day_name} 第{c.get('start_period','?')}-{c.get('end_period','?')}节 "
              f"| {c.get('name','?'):8s} @ {c.get('location','?')}")

    print("-" * 60)

    # === 期望结果 ===
    expected = [
        # (day, start, end, name, location)
        (1, 1, 2, "高等数学", "教1-101"),
        (2, 1, 2, "大学英语", "教2-201"),
        (3, 1, 2, "高等数学", "教1-101"),
        (4, 1, 2, "大学物理", "教3-301"),
        (5, 1, 2, "高等数学", "教1-101"),
        (1, 3, 4, "大学物理", "教3-301"),
        (2, 3, 4, "程序设计基础", "机房A-201"),
        (3, 3, 4, "体育", "操场"),
        (4, 3, 4, "程序设计基础", "机房A-201"),
        (5, 3, 4, "大学英语", "教2-201"),
        (1, 5, 6, "思想政治理论", "教4-401"),
        (3, 5, 6, "线性代数", "教1-201"),
        (5, 5, 6, "数据结构", "机房B-105"),
        (2, 7, 8, "大学物理实验", "实验楼301"),
        (4, 7, 8, "高等数学", "教1-101"),
        (1, 9, 10, "程序设计实践", "机房A-201"),
    ]

    print(f"\n期望: {len(expected)} 门课程")
    print(f"实际: {len(courses)} 门课程")

    # 对比
    issues = []
    for exp in expected:
        exp_day, exp_sp, exp_ep, exp_name, exp_loc = exp
        found = False
        for c in courses:
            if (c.get("day") == exp_day
                    and c.get("start_period") == exp_sp
                    and c.get("end_period") == exp_ep
                    and c.get("name") == exp_name):
                found = True
                if c.get("location") != exp_loc:
                    issues.append(
                        f"⚠️ 地点不匹配: {exp_name}({storage.DAYS[exp_day-1]}第{exp_sp}-{exp_ep}节) "
                        f"期望='{exp_loc}' 实际='{c.get('location')}'"
                    )
                break
        if not found:
            issues.append(
                f"❌ 缺失课程: {exp_name}({storage.DAYS[exp_day-1]}第{exp_sp}-{exp_ep}节)"
            )

    # 检查多余课程
    for c in courses:
        found = False
        for exp in expected:
            if (c.get("day") == exp[0]
                    and c.get("start_period") == exp[1]
                    and c.get("end_period") == exp[2]
                    and c.get("name") == exp[3]):
                found = True
                break
        if not found:
            issues.append(
                f"➕ 多余课程: {c.get('name','?')}({storage.DAYS[c.get('day',0)-1]})"
                f"第{c.get('start_period','?')}-{c.get('end_period','?')}节)"
            )

    if issues:
        print(f"\n🔴 发现 {len(issues)} 个问题：")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ 解析结果完全正确！")

    return courses, issues


def test_storage():
    """测试数据存储"""
    print("\n" + "=" * 60)
    print("💾 测试数据存储")
    print("=" * 60)

    # 备份原始数据
    original = storage.load_data()

    # 写入测试课程
    test_courses = [
        {"name": "高等数学", "location": "教1-101", "day": 1, "start_period": 1, "end_period": 2, "teacher": "", "weeks": ""},
        {"name": "大学英语", "location": "教2-201", "day": 2, "start_period": 1, "end_period": 2, "teacher": "", "weeks": ""},
        {"name": "大学物理", "location": "教3-301", "day": 1, "start_period": 3, "end_period": 4, "teacher": "", "weeks": ""},
    ]
    storage.replace_all_courses(test_courses)

    # 读回验证
    data = storage.load_data()
    loaded = data["courses"]

    if len(loaded) == 3:
        print("✅ 存储读写正确 (3门课程)")
    else:
        print(f"❌ 存储异常: 写入3门，读回{len(loaded)}门")

    # 测试今日课程
    today_courses, periods = storage.get_today_courses()
    today = __import__("datetime").datetime.now().weekday() + 1
    today_names = [c["name"] for c in today_courses if c["day"] == today]
    print(f"✅ 今日(星期{today})课程: {today_names if today_names else '无'}")
    print(f"✅ 节次时间表: {len(periods)} 个时段")

    # 恢复原始数据
    storage.save_data(original)
    print("✅ 已恢复原始数据")

    return len(loaded) == 3


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 60)
    print("🔍 测试边界情况")
    print("=" * 60)

    dlg = OCRImportDialog.__new__(OCRImportDialog)

    issues = []

    # 1. 空输入
    result = dlg._parse_courses([])
    if result == []:
        print("✅ 空输入处理正确")
    else:
        issues.append("空输入返回非空结果")

    # 2. 只有表头
    header_only = [("周一", [[180, 25], [240, 25], [240, 55], [180, 55]])]
    result = dlg._parse_courses(header_only)
    if len(result) == 0:
        print("✅ 只有表头处理正确")
    else:
        issues.append(f"只有表头时返回了 {len(result)} 条课程")

    # 3. 无表头（直接是课程数据）
    no_header = [
        ("高等数学", [[180, 80], [280, 80], [280, 105], [180, 105]]),
        ("教1-101", [[180, 110], [260, 110], [260, 135], [180, 110]]),
    ]
    result = dlg._parse_courses(no_header)
    print(f"⚠️ 无表头情况: 返回 {len(result)} 条（可能需要改进）")

    # 5. 课程名包含特殊字符
    special = [
        ("节次", [[20, 25], [80, 25], [80, 55], [20, 55]]),
        ("周一", [[180, 25], [240, 25], [240, 55], [180, 55]]),
        ("1-2",  [[30, 80], [70, 80], [70, 105], [30, 105]]),
        ("C++程序设计", [[180, 80], [280, 80], [280, 105], [180, 105]]),
        ("机房@1-101", [[180, 110], [260, 110], [260, 135], [180, 135]]),
    ]
    result = dlg._parse_courses(special)
    if result:
        print(f"✅ 特殊字符课程名: '{result[0].get('name','')}'")
    else:
        issues.append("特殊字符课程名未被解析")

    # 5. 节次为单个数字
    single = [
        ("节次", [[20, 25], [80, 25], [80, 55], [20, 55]]),
        ("周一", [[180, 25], [240, 25], [240, 55], [180, 55]]),
        ("第3节", [[30, 80], [80, 80], [80, 105], [30, 105]]),
        ("线性代数", [[180, 80], [280, 80], [280, 105], [180, 105]]),
        ("教1-201", [[180, 110], [260, 110], [260, 135], [180, 135]]),
    ]
    result = dlg._parse_courses(single)
    if result and result[0].get("start_period") == 3:
        print(f"✅ 单节次格式: 第{result[0]['start_period']}节")
    else:
        issues.append("单节次格式解析失败")

    if issues:
        print(f"\n🔴 边界测试发现 {len(issues)} 个问题：")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ 边界测试全部通过")

    return issues


if __name__ == "__main__":
    print("🧪 悬浮窗课程表 - 模拟导入测试")
    print()

    # 清空现有数据
    storage.replace_all_courses([])

    # 1. 测试 OCR 解析
    courses, parse_issues = test_parsing()

    # 2. 测试存储
    storage_ok = test_storage()

    # 3. 测试边界情况
    edge_issues = test_edge_cases()

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    total_issues = len(parse_issues) + len(edge_issues) + (0 if storage_ok else 1)
    if total_issues == 0:
        print("🎉 全部测试通过！")
    else:
        print(f"⚠️ 共发现 {total_issues} 个问题需要修复")

    # 写入模拟课程数据供 UI 展示
    print("\n📝 写入模拟课程数据供 UI 展示...")
    # 直接用期望的课程数据
    test_courses = [
        {"name": "高等数学", "location": "教1-101", "day": 1, "start_period": 1, "end_period": 2, "teacher": "张教授", "weeks": "1-16"},
        {"name": "大学物理", "location": "教3-301", "day": 1, "start_period": 3, "end_period": 4, "teacher": "李教授", "weeks": "1-16"},
        {"name": "思想政治理论", "location": "教4-401", "day": 1, "start_period": 5, "end_period": 6, "teacher": "王老师", "weeks": "1-16"},
        {"name": "程序设计实践", "location": "机房A-201", "day": 1, "start_period": 9, "end_period": 10, "teacher": "陈教授", "weeks": "1-16"},
        {"name": "大学英语", "location": "教2-201", "day": 2, "start_period": 1, "end_period": 2, "teacher": "刘老师", "weeks": "1-16"},
        {"name": "程序设计基础", "location": "机房A-201", "day": 2, "start_period": 3, "end_period": 4, "teacher": "陈教授", "weeks": "1-16"},
        {"name": "大学物理实验", "location": "实验楼301", "day": 2, "start_period": 7, "end_period": 8, "teacher": "李教授", "weeks": "3-14"},
        {"name": "高等数学", "location": "教1-101", "day": 3, "start_period": 1, "end_period": 2, "teacher": "张教授", "weeks": "1-16"},
        {"name": "体育", "location": "操场", "day": 3, "start_period": 3, "end_period": 4, "teacher": "赵老师", "weeks": "1-16"},
        {"name": "线性代数", "location": "教1-201", "day": 3, "start_period": 5, "end_period": 6, "teacher": "孙教授", "weeks": "1-16"},
        {"name": "大学物理", "location": "教3-301", "day": 4, "start_period": 1, "end_period": 2, "teacher": "李教授", "weeks": "1-16"},
        {"name": "程序设计基础", "location": "机房A-201", "day": 4, "start_period": 3, "end_period": 4, "teacher": "陈教授", "weeks": "1-16"},
        {"name": "高等数学", "location": "教1-101", "day": 4, "start_period": 7, "end_period": 8, "teacher": "张教授", "weeks": "1-16"},
        {"name": "高等数学", "location": "教1-101", "day": 5, "start_period": 1, "end_period": 2, "teacher": "张教授", "weeks": "1-16"},
        {"name": "大学英语", "location": "教2-201", "day": 5, "start_period": 3, "end_period": 4, "teacher": "刘老师", "weeks": "1-16"},
        {"name": "数据结构", "location": "机房B-105", "day": 5, "start_period": 5, "end_period": 6, "teacher": "陈教授", "weeks": "1-16"},
    ]
    storage.replace_all_courses(test_courses)
    print(f"✅ 已写入 {len(test_courses)} 门模拟课程")
    print("现在可以运行 main.py 查看悬浮窗效果")
