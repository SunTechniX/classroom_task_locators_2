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

def validate_task_01(locators):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://demoqa.com/buttons", timeout=10000)

        pairs = [
            ("DOUBLE_CLICK", locators["css_double"], locators["xpath_double"]),
            ("RIGHT_CLICK", locators["css_right"], locators["xpath_right"]),
            ("CLICK_ME", locators["css_click"], locators["xpath_click"]),
        ]

        for name, css, xpath in pairs:
            # Проверка CSS
            el_css = page.locator(css)
            assert el_css.count() == 1, f"{name} CSS: найдено {el_css.count()} элементов (ожидается 1)"
            # Проверка XPath
            el_xpath = page.locator(f"xpath={xpath}")
            assert el_xpath.count() == 1, f"{name} XPath: найдено {el_xpath.count()} элементов"
        browser.close()
    return True

def validate_task_02(locators):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://demoqa.com/links", timeout=10000)

        css_loc = locators["css"]
        xpath_loc = locators["xpath"]

        el_css = page.locator(css_loc)
        assert el_css.count() == 1, f"CSS находит {el_css.count()} элементов"
        assert "Home" in el_css.text_content(), "CSS: текст не 'Home'"

        el_xpath = page.locator(f"xpath={xpath_loc}")
        assert el_xpath.count() == 1, f"XPath находит {el_xpath.count()} элементов"
        assert "Home" in el_xpath.text_content(), "XPath: текст не 'Home'"

        browser.close()
    return True

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
        result = {"score": 0, "max_score": max_score, "tests": [{"name": "Файл отсутствует", "status": "fail", "score": 0, "max_score": max_score, "output": "Файл не найден"}]}
        print(f"::set-output name=result::{base64.b64encode(json.dumps(result, ensure_ascii=False).encode()).decode()}")
        return

    try:
        spec = spec_from_file_location(task_id, file_path)
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:
        result = {"score": 0, "max_score": max_score, "tests": [{"name": "Синтаксическая ошибка", "status": "fail", "score": 0, "max_score": max_score, "output": str(e)}]}
        print(f"::set-output name=result::{base64.b64encode(json.dumps(result, ensure_ascii=False).encode()).decode()}")
        return

    try:
        if task_id == "task_01":
            locs = {
                "css_double": getattr(mod, "DOUBLE_CLICK_CSS"),
                "xpath_double": getattr(mod, "DOUBLE_CLICK_XPATH"),
                "css_right": getattr(mod, "RIGHT_CLICK_CSS"),
                "xpath_right": getattr(mod, "RIGHT_CLICK_XPATH"),
                "css_click": getattr(mod, "CLICK_ME_CSS"),
                "xpath_click": getattr(mod, "CLICK_ME_XPATH"),
            }
            validate_task_01(locs)
            total_score = max_score
        elif task_id == "task_02":
            locs = {
                "css": getattr(mod, "SECOND_LINK_CSS"),
                "xpath": getattr(mod, "SECOND_LINK_XPATH"),
            }
            validate_task_02(locs)
            total_score = max_score

        test_result = {"name": "Все локаторы корректны", "status": "pass", "score": total_score, "max_score": max_score, "output": "OK"}
    except Exception as e:
        total_score = 0
        test_result = {"name": "Ошибка валидации", "status": "fail", "score": 0, "max_score": max_score, "output": str(e)}

    result = {"score": total_score, "max_score": max_score, "tests": [test_result]}
    encoded = base64.b64encode(json.dumps(result, ensure_ascii=False).encode("utf-8")).decode("utf-8")
    print(f"::set-output name=result::{encoded}")

if __name__ == "__main__":
    main()