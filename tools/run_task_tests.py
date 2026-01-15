#!/usr/bin/env python3
import json
import sys
import os
import base64
from importlib.util import spec_from_file_location, module_from_spec

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ Playwright не установлен")
    sys.exit(1)

def validate_task_01(mod):
    tests = []
    total_score = 0
    max_total = 60

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://demoqa.com/buttons", timeout=10000)

        checks = [
            ("DOUBLE_CLICK_CSS", getattr(mod, "DOUBLE_CLICK_CSS", ""), True),
            ("DOUBLE_CLICK_XPATH", getattr(mod, "DOUBLE_CLICK_XPATH", ""), False),
            ("RIGHT_CLICK_CSS", getattr(mod, "RIGHT_CLICK_CSS", ""), True),
            ("RIGHT_CLICK_XPATH", getattr(mod, "RIGHT_CLICK_XPATH", ""), False),
            ("CLICK_ME_CSS", getattr(mod, "CLICK_ME_CSS", ""), True),
            ("CLICK_ME_XPATH", getattr(mod, "CLICK_ME_XPATH", ""), False),
        ]

        for name, locator, is_css in checks:
            score = 0
            max_score = 10
            output = ""
            status = "fail"
            try:
                if not locator:
                    raise ValueError("Локатор пустой")
                if is_css:
                    el = page.locator(locator)
                else:
                    el = page.locator(f"xpath={locator}")
                if el.count() != 1:
                    raise AssertionError(f"Найдено {el.count()} элементов (ожидается 1)")
                # Доп: проверим, что это кнопка
                tag = el.evaluate("el => el.tagName.toLowerCase()")
                if tag != "button":
                    raise AssertionError(f"Элемент не является <button>, а {tag}")
                score = max_score
                status = "pass"
                output = "OK"
            except Exception as e:
                output = str(e)

            tests.append({
                "name": name,
                "score": score,
                "max_score": max_score,
                "status": status,
                "output": output
            })
            total_score += score

        browser.close()

    return {
        "score": total_score,
        "max_score": max_total,
        "tests": tests
    }

def validate_task_02(mod):
    tests = []
    total_score = 0
    max_total = 40

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://demoqa.com/links", timeout=10000)

        checks = [
            ("SECOND_LINK_CSS", getattr(mod, "SECOND_LINK_CSS", ""), True),
            ("SECOND_LINK_XPATH", getattr(mod, "SECOND_LINK_XPATH", ""), False),
        ]

        for name, locator, is_css in checks:
            score = 0
            max_score = 20
            output = ""
            status = "fail"
            try:
                if not locator:
                    raise ValueError("Локатор пустой")
                if is_css:
                    el = page.locator(locator)
                else:
                    el = page.locator(f"xpath={locator}")
                if el.count() != 1:
                    raise AssertionError(f"Найдено {el.count()} элементов")
                text = el.text_content().strip()
                if "Home" not in text:
                    raise AssertionError(f"Текст не 'Home', а '{text}'")
                score = max_score
                status = "pass"
                output = "OK"
            except Exception as e:
                output = str(e)

            tests.append({
                "name": name,
                "score": score,
                "max_score": max_score,
                "status": status,
                "output": output
            })
            total_score += score

        browser.close()

    return {
        "score": total_score,
        "max_score": max_total,
        "tests": tests
    }

VALIDATORS = {
    "task_01": validate_task_01,
    "task_02": validate_task_02,
}

def main():
    if len(sys.argv) != 2:
        print("Usage: run_task_tests.py <task_id>")
        sys.exit(1)

    task_id = sys.argv[1]
    config_path = ".github/tasks.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    task = next((t for t in config["tasks"] if t["id"] == task_id), None)
    if not task:
        print(f"Task {task_id} not found")
        sys.exit(1)

    file_path = task["file"]
    max_score = task["max_score"]

    if not os.path.exists(file_path):
        result = {
            "score": 0,
            "max_score": max_score,
            "tests": [{"name": "Файл отсутствует", "status": "fail", "score": 0, "max_score": max_score, "output": "Файл не найден"}]
        }
        print(f"::set-output name=result::{base64.b64encode(json.dumps(result, ensure_ascii=False).encode()).decode()}")
        return

    try:
        spec = spec_from_file_location(task_id, file_path)
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:
        result = {
            "score": 0,
            "max_score": max_score,
            "tests": [{"name": "Синтаксическая ошибка", "status": "fail", "score": 0, "max_score": max_score, "output": str(e)}]
        }
        print(f"::set-output name=result::{base64.b64encode(json.dumps(result, ensure_ascii=False).encode()).decode()}")
        return

    try:
        result = VALIDATORS[task_id](mod)
    except Exception as e:
        result = {
            "score": 0,
            "max_score": max_score,
            "tests": [{"name": "Критическая ошибка валидатора", "status": "fail", "score": 0, "max_score": max_score, "output": str(e)}]
        }

    encoded = base64.b64encode(json.dumps(result, ensure_ascii=False).encode("utf-8")).decode("utf-8")
    print(f"::set-output name=result::{encoded}")

if __name__ == "__main__":
    main()
