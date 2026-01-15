#!/usr/bin/env python3
import os
import sys
import base64
import json
from datetime import datetime


def decode_result(encoded):
    if not encoded or encoded in ("null", "undefined", ""):
        return {"score": 0, "max_score": 0}
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
        return json.loads(decoded)
    except Exception as e:
        print(f"⚠️ Decode error: {e}", file=sys.stderr)
        return {"score": 0, "max_score": 0}


def main():
    # Загружаем max_score из tasks.json
    with open(".github/tasks.json", "r", encoding="utf-8") as f:
        tasks = {t["id"]: t for t in json.load(f)["tasks"]}

    task_ids = sys.argv[1:]
    total_score = 0
    max_total = 0
    lines = []

    for task_id in task_ids:
        # Читаем результат из окружения
        encoded = os.environ.get(
            f"TASK_{task_id[-2:]}_RESULT")  # TASK_01_RESULT
        if not encoded:
            # Альтернативное имя: TASK_01_RESULT → task_01
            encoded = os.environ.get(f"{task_id.upper()}_RESULT")

        res = decode_result(encoded)
        score = res.get("score", 0)
        max_score = tasks[task_id]["max_score"]
        name = tasks[task_id]["name"]

        total_score += score
        max_total += max_score

        status = "✅" if score == max_score else ("⚠️" if score > 0 else "❌")
        lines.append(f"| **{name}** | {score} | {max_score} | {status} |")

    percentage = int(100 * total_score / max_total) if max_total else 0

    report = []
    report.append("## 📊 ИТОГОВЫЙ ОТЧЕТ ПО ВСЕМ ЗАДАНИЯМ\n")
    report.append("### 📈 Сводная таблица\n")
    report.append("| Задание | Баллы | Максимум | Статус |")
    report.append("|---------|-------|----------|--------|")
    report.extend(lines)
    report.append(
        f"| **ВСЕГО** | **{total_score}** | **{max_total}** | **{percentage}%** |")
    report.append("")
    report.append("### 📁 Найденные файлы:\n")
    for task_id in task_ids:
        f = tasks[task_id]["file"]
        exists = "✅" if os.path.exists(f) else "❌"
        report.append(
            f"{exists} **{f}** - {'найден' if exists == '✅' else 'не найден'}")
    report.append("")
    report.append(f"### 🏆 Итоговая оценка: **{total_score} / {max_total}**")
    report.append("")
    if total_score == max_total:
        report.append("🎉 **ПОЗДРАВЛЯЕМ! Все задачи выполнены на 100%!**")
    else:
        report.append("💡 **Есть что улучшить! Смотри детали тестов.**")
    report.append("")
    report.append(f"**GitHub Classroom: {total_score}/{max_total} баллов**")
    report.append("")
    report.append(
        f"*Автоматическая проверка завершена* • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY", "/dev/stdout")
    with open(summary_file, "a") as f:
        f.write("\n".join(report))


if __name__ == "__main__":
    main()
