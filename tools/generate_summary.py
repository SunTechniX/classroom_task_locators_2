#!/usr/bin/env python3
import os
import sys
import base64
import json
from datetime import datetime

def decode_result(encoded):
    if not encoded or encoded in ("null", "undefined", ""):
        return {"score": 0, "max_score": 0, "tests": []}
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
        return json.loads(decoded)
    except Exception as e:
        print(f"⚠️ Decode error: {e}", file=sys.stderr)
        return {"score": 0, "max_score": 0, "tests": []}

def main():
    with open(".github/tasks.json", "r", encoding="utf-8") as f:
        tasks = {t["id"]: t for t in json.load(f)["tasks"]}

    task_ids = sys.argv[1:]
    total_score = 0
    max_total = 0
    report_lines = []

    report_lines.append("## 📊 ИТОГОВЫЙ ОТЧЕТ ПО ВСЕМ ЗАДАНИЯМ\n")
    report_lines.append("### 📈 Сводная таблица\n")
    report_lines.append("| Задание | Баллы | Максимум | Статус |")
    report_lines.append("|---------|-------|----------|--------|")

    for task_id in task_ids:
        encoded = os.environ.get(f"{task_id.upper()}_RESULT") or os.environ.get(f"TASK_{task_id[-2:]}_RESULT")
        res = decode_result(encoded)

        score = res.get("score", 0)
        max_score = tasks[task_id]["max_score"]
        name = tasks[task_id]["name"]
        total_score += score
        max_total += max_score

        status = "✅" if score == max_score else ("⚠️" if score > 0 else "❌")
        report_lines.append(f"| **{name}** | {score} | {max_score} | {status} |")

        # Детализация подтестов
        tests = res.get("tests", [])
        if tests:
            report_lines.append(f"\n#### 🔍 Детали по **{name}**\n")
            report_lines.append("| Подтест | Баллы | Максимум | Статус |")
            report_lines.append("|---------|-------|----------|--------|")
            for test in tests:
                t_name = test.get("name", "—")
                t_score = test.get("score", 0)
                t_max = test.get("max_score", 0)
                t_status = "✅" if t_score == t_max else ("⚠️" if t_score > 0 else "❌")
                output = test.get("output", "").replace("\n", " \\n ")[:100]  # укоротить
                report_lines.append(f"| `{t_name}` | {t_score} | {t_max} | {t_status} |")
                if t_status != "✅" and output.strip():
                    report_lines.append(f"> 💬 `{output}`")

    percentage = int(100 * total_score / max_total) if max_total else 0
    report_lines.append(f"\n| **ВСЕГО** | **{total_score}** | **{max_total}** | **{percentage}%** |")

    report_lines.append("\n### 📁 Найденные файлы:")
    for task_id in task_ids:
        f = tasks[task_id]["file"]
        exists = "✅" if os.path.exists(f) else "❌"
        report_lines.append(f"{exists} **{f}** - {'найден' if exists == '✅' else 'не найден'}")

    report_lines.append(f"\n### 🏆 Итоговая оценка: **{total_score} / {max_total}**")
    if total_score == max_total:
        report_lines.append("\n🎉 **ПОЗДРАВЛЯЕМ! Все задачи выполнены на 100%!**")
    else:
        report_lines.append("\n💡 **Есть что улучшить! Смотри детали тестов выше.**")

    report_lines.append(f"\n**GitHub Classroom: {total_score}/{max_total} баллов**")
    report_lines.append(f"\n*Автоматическая проверка завершена* • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY", "/dev/stdout")
    with open(summary_file, "a") as f:
        f.write("\n".join(report_lines))

if __name__ == "__main__":
    main()
