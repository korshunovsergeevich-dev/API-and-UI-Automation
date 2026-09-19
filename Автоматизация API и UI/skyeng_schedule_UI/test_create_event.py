from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)


def test_create_personal_event(driver, auth_data: dict) -> None:
    """
    UI-тест: создание личного события, редактирование даты и времени.
    """
    wait = WebDriverWait(driver, 20, poll_frequency=0.5)
    short_wait = WebDriverWait(driver, 5, poll_frequency=0.5)

    def safe_click(element: WebElement) -> None:
        try:
            element.click()
        except ElementClickInterceptedException:
            driver.execute_script(
                "arguments[0].scrollIntoView("
                "{block: 'center', behavior: 'smooth'});",
                element,
            )
            WebDriverWait(driver, 3).until(lambda d: True)
            driver.execute_script("arguments[0].click();", element)
        except StaleElementReferenceException:
            raise TimeoutException("Элемент устарел после попытки клика")

    def safe_click_robust(element: WebElement) -> None:
        for attempt in range(3):
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView("
                    "{block: 'center', inline: 'center'});",
                    element,
                )
                WebDriverWait(driver, 1).until(lambda d: True)
                element.click()
                return
            except (ElementClickInterceptedException,
                    ElementNotInteractableException):
                driver.execute_script("arguments[0].click();", element)
                return
            except StaleElementReferenceException:
                if attempt == 2:
                    raise TimeoutException("Элемент устарел")
                WebDriverWait(driver, 1).until(lambda d: True)

    def remove_overlays() -> None:
        script = (
            "var o = document.querySelectorAll("
            "'.cdk-overlay-backdrop,.overlay,"
            ".backdrop,.cdk-global-overlay-wrapper'"
            ");"
            "o.forEach(function(e) {"
            " if (e && e.style) {"
            " e.style.opacity = '0';"
            " e.style.pointerEvents = 'none';"
            " e.style.display = 'none';"
            " }"
            "});"
        )
        driver.execute_script(script)
        WebDriverWait(driver, 1).until(lambda d: True)

    def wait_for_button_ready(locator: tuple) -> WebElement:
        def condition(d):
            try:
                elem = d.find_element(*locator)
                if not elem.is_displayed():
                    return False
                styles = driver.execute_script(
                    """
                    var el = arguments[0];
                    var style = window.getComputedStyle(el);
                    return {
                        width: parseFloat(style.width) || 0,
                        height: parseFloat(style.height) || 0,
                        opacity: parseFloat(style.opacity) || 1,
                        pointerEvents: style.pointerEvents
                    };
                    """,
                    elem,
                )
                if (
                    styles["width"] > 10
                    and styles["height"] > 10
                    and styles["opacity"] > 0.5
                    and styles["pointerEvents"] != "none"
                ):
                    return elem
                return False
            except Exception:
                return False
        return WebDriverWait(driver, 15, poll_frequency=0.5).until(condition)

    def open_time_picker(picker_index: int = 0) -> None:
        pickers = driver.find_elements(
            By.CSS_SELECTOR, "teachers-time-picker.time-select")
        if picker_index >= len(pickers):
            raise IndexError(
                f"Не найдено достаточно компонентов time-picker. Найдено: {len(
                    pickers)}")
        picker = pickers[picker_index]
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", picker)
        try:
            picker.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", picker)
        WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.times_item.ng-star-inserted"))
        )
        print(f"[TimePicker] Список времени открыт для поля #{picker_index}")

    def select_time_by_minutes(minutes_value: int) -> None:
        locator = (
            By.CSS_SELECTOR, f"div.times_item[data-minutes='{minutes_value}']")
        try:
            element = short_wait.until(EC.element_to_be_clickable(locator))
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", element)
            WebDriverWait(driver, 0.5).until(lambda d: True)
            try:
                element.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", element)
            WebDriverWait(driver, 1).until(lambda d: True)
            print(f"[TimePicker] Выбрано время: {minutes_value} минут")
        except TimeoutException:
            all_options = driver.find_elements(
                By.CSS_SELECTOR, "div.times_item.ng-star-inserted")
            print(f"[Debug] Целевое значение: {minutes_value}")
            print("[Debug] Доступные минуты:", [el.get_attribute(
                "data-minutes") for el in all_options[:15]])
            driver.save_screenshot(f"debug_time_picker_{minutes_value}.png")
            raise TimeoutException(
                f"Не найдено время с data-minutes='{minutes_value}'")

    # ================================================================
    # ЧАСТЬ 1: СОЗДАНИЕ СОБЫТИЯ
    # ================================================================

    # --- 1. Авторизация ---
    driver.get("https://id.skyeng.ru/login")
    try:
        wait.until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, ".loader, .overlay, .preloader")))
    except TimeoutException:
        pass

    btn_login_link = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Войти с помощью пароля')]"))
    )
    safe_click(btn_login_link)
    wait.until(EC.url_contains("id.skyeng.ru"))

    email_input = wait.until(
        EC.visibility_of_element_located((By.NAME, "username")))
    email_input.clear()
    email_input.send_keys(auth_data["username"])

    password_input = wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[type='password']")))
    password_input.clear()
    password_input.send_keys(auth_data["password"])

    login_btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[normalize-space(text())='Войти']")))
    safe_click(login_btn)

    # --- 2. Переход на расписание ---
    wait.until(EC.url_contains("teacher.skyeng.ru"))
    driver.get("https://teacher.skyeng.ru/schedule")
    try:
        wait.until(EC.invisibility_of_element_located(
            (By.CSS_SELECTOR, ".overlay, "
             " .backdrop, .cdk-overlay-backdrop, .loader")))
    except TimeoutException:
        pass

    # --- 3. Клик «+Создать» ---
    create_button: Optional[WebElement] = None
    locators = [
        (By.CSS_SELECTOR, "ds-button[type='primary-blue']"),
        (By.XPATH, "//ds-button[contains(., '+Создать')]"),
        (By.CSS_SELECTOR, "ds-button"),
    ]
    for loc in locators:
        try:
            create_button = short_wait.until(EC.element_to_be_clickable(loc))
            if "Создать" in create_button.text:
                break
        except TimeoutException:
            continue

    if not create_button:
        create_button = driver.execute_script(
            "return document.querySelector('ds-button, button')")
    if not create_button:
        driver.save_screenshot("debug_no_create.png")
        raise TimeoutException("Кнопка +Создать не найдена")

    safe_click(create_button)

    # --- 4. Выбор «Личное событие» ---
    wait.until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR,
         ".cdk-overlay-pane, [role='menu'], [role='listbox']")))

    menu_item: Optional[WebElement] = None
    menu_locators = [
        (By.XPATH,
         "//*[@role='menu']//*[normalize-space(text())='Личное событие']"),
        (By.XPATH,
         "//*[contains(@class, 'cdk-overlay')]//*[normalize-space(text("
         "))='Личное событие']"),
        (By.XPATH,
         "//*[normalize-space(text("
         "))='Личное событие']"),
    ]
    for loc in menu_locators:
        try:
            menu_item = short_wait.until(EC.element_to_be_clickable(loc))
            break
        except TimeoutException:
            continue

    if not menu_item:
        driver.save_screenshot("debug_no_menu_item.png")
        raise TimeoutException("Пункт 'Личное событие' в меню не найден")

    safe_click(menu_item)

    # --- 5. Ожидание модального окна ---
    print("Ожидаем появления модального окна 'Создать событие'...")
    try:
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//*[normalize-space(text())='Создать событие']")))
        wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input, textarea")))
    except TimeoutException:
        driver.save_screenshot("debug_modal_not_opened.png")
        raise TimeoutException(
            "Модальное окно не открылось после выбора типа события")

    # --- 6. Заполнение формы ---
    event_name = "Тестовый вебинар Selenium"
    name_input: Optional[WebElement] = None
    input_locators = [
        (By.XPATH, "//input[contains(@placeholder, 'посмотреть вебинар')]"),
        (By.CSS_SELECTOR, "input[type='text'], input[name='title']"),
        (By.XPATH, "//*[contains(@class, 'input')]//input"),
    ]
    for loc in input_locators:
        try:
            name_input = short_wait.until(EC.element_to_be_clickable(loc))
            if name_input.is_displayed():
                break
        except TimeoutException:
            continue

    if not name_input:
        driver.save_screenshot("debug_no_input_field.png")
        raise TimeoutException("Поле названия события не найдено")

    name_input.clear()
    name_input.send_keys(event_name)
    wait.until(lambda d: name_input.get_attribute("value") == event_name)

    driver.execute_script(
        """
        var element = arguments[0];
        element.value = arguments[1];
        var event = new Event('input', { bubbles: true });
        element.dispatchEvent(event);
        """,
        name_input,
        event_name,
    )
    driver.execute_script("arguments[0].blur();", name_input)

    errors = driver.find_elements(
        By.CSS_SELECTOR, ".error, .has-error, [aria-invalid='true']")
    if errors:
        driver.save_screenshot("debug_validation_errors.png")
        raise AssertionError(
            f"Обнаружены ошибки валидации:{[e.text for e in errors if e.text]}"
            )

    # --- 7. Поиск кнопки «Сохранить» ---
    save_button: Optional[WebElement] = None
    save_locators = [
        (By.XPATH, "//ds-button[contains(., 'Сохранить')]//button"),
        (By.XPATH, "//button[normalize-space(text())='Сохранить']"),
        (By.CSS_SELECTOR,
         "ds-button[type='primary-blue'], button[type='submit']"),
        (By.XPATH, "//*[contains(@class, 'save')]//button"),
    ]

    for loc in save_locators:
        try:
            save_button = short_wait.until(EC.element_to_be_clickable(loc))
            if "Сохранить" in save_button.text:
                break
        except TimeoutException:
            continue

    if not save_button:
        driver.save_screenshot("debug_no_save_button_final.png")
        raise TimeoutException("Кнопка 'Сохранить' не найдена")

    save_ds_button = driver.execute_script(
        """
        var el = arguments[0];
        while (el && el.tagName !== 'DS-BUTTON') {
            el = el.parentElement;
        }
        return el;
        """,
        save_button,
    )

    print("Ждём, пока кнопка 'Сохранить' станет активной (enabled)...")
    try:
        WebDriverWait(
            driver, 10, poll_frequency=0.5).until(
                lambda d: save_button.is_enabled())
        print("Кнопка 'Сохранить' активна.")
    except TimeoutException:
        driver.save_screenshot("debug_save_button_still_disabled.png")
        raise TimeoutException(
            "Кнопка 'Сохранить' не стала активной после ввода названия события"
            )

    # --- 8. Убираем оверлеи ---
    print("Удаляем оверлеи через JS...")
    driver.execute_script(
        """
        var overlays = document.querySelectorAll(
        '.cdk-overlay-backdrop, .overlay, .backdrop');
        overlays.forEach(function(o) {
            if (o && o.style) {
                o.style.opacity = '0';
                o.style.pointerEvents = 'none';
                o.style.display = 'none';
            }
        });
        """
    )
    WebDriverWait(driver, 2).until(lambda d: True)

    # --- 9. Клик «Сохранить» ---
    print("Выполняем клик по кнопке 'Сохранить'...")
    click_target = save_ds_button if save_ds_button else save_button
    try:
        click_target.click()
        print("Обычный клик выполнен.")
    except (ElementClickInterceptedException, ElementNotInteractableException,
            Exception) as e:
        print(f"Обычный клик не сработал ({e}), пробуем JS-клик...")
        driver.execute_script("arguments[0].click();", click_target)

    # --- 10. Верификация закрытия модалки ---
    print("Ждём исчезновения модального окна...")
    try:
        WebDriverWait(driver, 12, poll_frequency=0.5).until(
            EC.invisibility_of_element_located(
                (By.XPATH, "//*[normalize-space(text())='Создать событие']")))
        print("Модальное окно успешно закрыто.")
    except TimeoutException:
        modals = driver.find_elements(
            By.CSS_SELECTOR, ".cdk-overlay-container, .modal, .dialog")
        if modals:
            print("Найдено модальных контейнеров:", len(modals))
        driver.save_screenshot("debug_modal_still_open_after_click.png")
        raise TimeoutException(
            "Модальное окно НЕ закрылось после клика на 'Сохранить'")

    # --- 11. Верификация появления события ---
    print(f"Ждём появления события '{event_name}' в расписании...")
    assert wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, f"//*[contains(text(), '{event_name}')]"))
    ).is_displayed(), f"Событие '{event_name}' не найдено в расписании."

    # ================================================================
    # ЧАСТЬ 2: ИЗМЕНЕНИЕ ДАТЫ
    # ================================================================

    # --- 12. Клик на событие ---
    print("Кликаем на созданное событие в расписании...")
    event_element = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, f"//*[contains(text(), '{event_name}')]"))
    )
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
        event_element,
    )
    WebDriverWait(driver, 1).until(lambda d: True)
    remove_overlays()

    try:
        event_element.click()
    except (ElementClickInterceptedException, ElementNotInteractableException):
        driver.execute_script("arguments[0].click();", event_element)
    except StaleElementReferenceException:
        event_element = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, f"//*[contains(text(), '{event_name}')]"))
        )
        driver.execute_script("arguments[0].click();", event_element)

    # --- 13. Клик «Редактировать» ---
    print("Ждём появления и полной отрисовки кнопки «Редактировать»...")
    edit_btn_locator = (
        By.XPATH,
        "//ds-button[.//*[normalize-space(text())='Редактировать']]//button")
    edit_btn_mini = wait_for_button_ready(edit_btn_locator)

    if not edit_btn_mini:
        driver.save_screenshot("debug_edit_btn_not_ready.png")
        raise TimeoutException(
            "Кнопка 'Редактировать' не стала интерактивной за 15 сек")

    print(
        f"Кнопка={edit_btn_mini.size},displayed={edit_btn_mini.is_displayed()}"
        )
    remove_overlays()
    safe_click_robust(edit_btn_mini)
    WebDriverWait(driver, 3).until(lambda d: True)

    # --- 14. Ожидание окна «Редактировать событие» ---
    print("Ждём открытия полного окна редактирования...")
    wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//*[normalize-space(text())='Редактировать событие']")))

    # --- 15. Выбор новой даты ---
    print("Выбираем новую дату...")
    result = driver.execute_script("""
        var option = document.querySelector("select option[value*='T']");
        if (!option) return {success: false, error: "select_not_found"};
        var select = option.parentElement;
        var oldValue = select.value;
        var targetValue = null;
        var targetIdx = -1;
        for (var i = 0; i < select.options.length; i++) {
            var v = select.options[i].value;
            if (v && v !== oldValue) {
                targetValue = v;
                targetIdx = i;
                break;
            }
        }
        if (!targetValue) return {success: false, error: "no_alt_date"};
        select.selectedIndex = targetIdx;
        try {
            var nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLSelectElement.prototype, 'value').set;
            nativeSetter.call(select, targetValue);
        } catch(e) {}
        for (var i = 0; i < select.options.length; i++) {
            select.options[i].selected = (i === targetIdx);
        }
        select.dispatchEvent(new Event('change', {bubbles: true}));
        select.dispatchEvent(new Event('input', {bubbles: true}));
        return {
            success: true,
            oldValue: oldValue,
            newValue: select.value,
            targetValue: targetValue
        };
    """)

    if not result or not result.get("success"):
        driver.save_screenshot("debug_select_failed.png")
        raise TimeoutException(f"Ошибка: {result}")

    print(f"Старое: {result['oldValue']}")
    print(f"Новое (DOM): {result['newValue']}")
    print(f"Целевое: {result['targetValue']}")
    WebDriverWait(driver, 5).until(lambda d: True)

    # --- 16. Сохранение изменений даты ---
    print("Ищем и кликаем «Сохранить»...")
    save_btn: Optional[WebElement] = None
    save_locators_edit = [
        (By.XPATH, "//ds-button[contains(., 'Сохранить')]//button"),
        (By.XPATH, "//button[normalize-space(text())='Сохранить']"),
        (By.CSS_SELECTOR,
         "ds-button[type='primary-blue'], button[type='submit']"),
        (By.XPATH, "//*[contains(@class, 'save')]//button"),
    ]
    for loc in save_locators_edit:
        try:
            save_btn = short_wait.until(EC.element_to_be_clickable(loc))
            if "Сохранить" in save_btn.text:
                break
        except TimeoutException:
            continue

    if not save_btn:
        driver.save_screenshot("debug_no_save_in_edit.png")
        raise TimeoutException("Кнопка 'Сохранить' не найдена")

    save_btn_parent = driver.execute_script(
        """
        var el = arguments[0];
        while (el && el.tagName !== 'DS-BUTTON') { el = el.parentElement; }
        return el;
        """,
        save_btn,
    )

    print("Ждём активации кнопки 'Сохранить'...")
    try:
        WebDriverWait(
            driver, 10, poll_frequency=0.5).until(
                lambda d: save_btn.is_enabled())
        print("Кнопка 'Сохранить' активна.")
    except TimeoutException:
        driver.save_screenshot("debug_save_in_edit_disabled.png")
        raise TimeoutException("Кнопка 'Сохранить' не активна")

    remove_overlays()
    click_target = save_btn_parent if save_btn_parent else save_btn
    safe_click_robust(click_target)

    # --- 17. Верификация закрытия ---
    print("Ждём закрытия окна редактирования...")
    try:
        WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located(
                (By.XPATH,
                 "//*[normalize-space(text())='Редактировать событие']")))
        print("Окно редактирования успешно закрыто.")
    except TimeoutException:
        driver.save_screenshot("debug_edit_window_still_open.png")
        raise TimeoutException(
            "Окно редактирования не закрылось после сохранения")

    # ================================================================
    # ЧАСТЬ 3: ПОВТОРНОЕ ОТКРЫТИЕ ДЛЯ РЕДАКТИРОВАНИЯ ВРЕМЕНИ
    # ================================================================

    print(f"Ищем событие '{event_name}' для повторного клика...")
    event_element = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, f"//*[contains(text(), '{event_name}')]"))
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
        event_element,
    )
    WebDriverWait(driver, 1).until(lambda d: True)
    remove_overlays()

    try:
        event_element.click()
        print("Клик по событию выполнен.")
    except (ElementClickInterceptedException,
            ElementNotInteractableException) as e:
        print(f"Обычный клик не сработал ({e}), пробуем JS-клик...")
        driver.execute_script("arguments[0].click();", event_element)
    except StaleElementReferenceException:
        event_element = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, f"//*[contains(text(), '{event_name}')]"))
        )
        driver.execute_script("arguments[0].click();", event_element)
        print("Клик выполнен после повторного поиска элемента.")

    print("Ждём появления кнопки «Редактировать»...")
    edit_btn_locator = (By.XPATH,
                        "//ds-button[.//*[normalize-space(text())="
                        "'Редактировать']]//button")
    edit_btn = wait_for_button_ready(edit_btn_locator)

    if not edit_btn:
        driver.save_screenshot("debug_edit_btn_not_found_second_time.png")
        raise TimeoutException(
            "Кнопка «Редактировать» не появилась "
            "при повторном открытии события")

    print(
        f"Редактировать={edit_btn.size}, displayed={edit_btn.is_displayed()}")
    remove_overlays()
    print("Кликаем на кнопку «Редактировать»...")
    safe_click_robust(edit_btn)

    print("Ждём открытия окна «Редактировать событие»...")
    try:
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//*[normalize-space(text())='Редактировать событие']"))
            )
        print("Окно редактирования успешно открыто.")
    except TimeoutException:
        driver.save_screenshot("debug_edit_window_not_opened_second_time.png")
        raise TimeoutException(
            "Окно редактирования не открылось после клика на «Редактировать»")

    # --- 3. Поиск компонентов выбора времени (начало и конец) ---
    print("Ищем компоненты выбора времени (teachers-time-picker)...")
    time_pickers = driver.find_elements(
        By.CSS_SELECTOR, "teachers-time-picker.time-select")
    if len(time_pickers) < 2:
        driver.save_screenshot("debug_time_pickers_not_found.png")
        print(f"[Debug] Найдено компонентов time-picker: {len(time_pickers)}")
        raise TimeoutException(
            "Не найдено достаточно компонентов выбора времени ("
            "ожидается минимум 2: начало и конец)")

    print(f"Найдено компонентов выбора времени: {len(time_pickers)}")

    # --- 4. Функция выбора времени с улучшенной обработкой оверлеев ---

    def set_time_on_picker(
            picker_index: int, minutes_value: int, label: str) -> None:
        print(
            f"[{label}] Пикер #{picker_index}, цель: {minutes_value} минут")
        picker = time_pickers[picker_index]

        driver.execute_script(
            "arguments[0].scrollIntoView("
            "{block: 'center', inline: 'center'});",
            picker
        )
        WebDriverWait(driver, 1).until(lambda d: True)

        try:
            picker.click()
        except (ElementClickInterceptedException,
                ElementNotInteractableException):
            driver.execute_script("arguments[0].click();", picker)

        # Ждём появления элементов
        time_items_locator = (By.CSS_SELECTOR, "[data-minutes]")
        try:
            WebDriverWait(driver, 15, poll_frequency=0.5).until(
                EC.presence_of_all_elements_located(time_items_locator)
            )
            print(f"[{label}] Список времени открыт.")
        except TimeoutException:
            driver.save_screenshot(f"debug_time_list_not_opened_{label}.png")
            raise TimeoutException(
                f"Не удалось открыть список времени для {label}")

        # Ищем ВИДИМЫЙ элемент с нужным data-minutes
        all_items = driver.find_elements(
            By.CSS_SELECTOR, f"[data-minutes='{minutes_value}']")
        target_element = None
        for el in all_items:
            if el.is_displayed():
                target_element = el
                break

        if not target_element:
            # Если не нашли видимый — берём любой (fallback)
            target_element = short_wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, f"[data-minutes='{minutes_value}']")))

        # Скроллим целевой элемент в центр списка
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", target_element)
        WebDriverWait(driver, 0.5).until(lambda d: True)

        # Кликаем через ActionChains — точный клик в центр элемента
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(driver)
            actions.move_to_element(target_element).click().perform()
            print(f"[{label}] Клик через ActionChains выполнен.")
        except Exception as e:
            print(
                f"[{label}] ActionChains не сработал({e}), пробуем JS-клик...")
            driver.execute_script("arguments[0].click();", target_element)

        WebDriverWait(driver, 5).until(lambda d: True)
        print(f"[{label}] Время {minutes_value} минут выбрано.")

    # --- 5. Выбираем новое время для начала и конца события ---
    # Пример: начало 17:00 (1020 минут), конец 18:00 (1080 минут)
    # Подберите значения под ваши тестовые данные
    start_minutes = 1040  # 17:00
    end_minutes = 1090    # 18:00

    print(f"Устанавливаем время начала: {start_minutes} минут...")
    set_time_on_picker(0, start_minutes, "Start Time")

    print(f"Устанавливаем время конца: {end_minutes} минут...")
    set_time_on_picker(1, end_minutes, "End Time")

    # --- 6. Сохранение изменений времени ---
    print("Ищем и кликаем «Сохранить» после изменения времени...")
    save_btn: Optional[WebElement] = None
    save_locators_time = [
        (By.XPATH, "//ds-button[contains(., 'Сохранить')]//button"),
        (By.XPATH, "//button[normalize-space(text())='Сохранить']"),
        (By.CSS_SELECTOR,
         "ds-button[type='primary-blue'], button[type='submit']"),
    ]
    for loc in save_locators_time:
        try:
            save_btn = short_wait.until(EC.element_to_be_clickable(loc))
            if "Сохранить" in save_btn.text:
                break
        except TimeoutException:
            continue

    if not save_btn:
        driver.save_screenshot("debug_no_save_after_time_edit.png")
        raise TimeoutException(
            "Кнопка 'Сохранить' не найдена после редактирования времени")

    save_btn_parent = driver.execute_script(
        """
        var el = arguments[0];
        while (el && el.tagName !== 'DS-BUTTON') { el = el.parentElement; }
        return el;
        """,
        save_btn,
    )

    print("Ждём активации кнопки 'Сохранить'...")
    try:
        WebDriverWait(
            driver, 10, poll_frequency=0.5).until(
                lambda d: save_btn.is_enabled())
        print("Кнопка 'Сохранить' активна.")
    except TimeoutException:
        driver.save_screenshot("debug_save_after_time_edit_disabled.png")
        raise TimeoutException(
            "Кнопка 'Сохранить' не активна после редактирования времени")

    remove_overlays()
    click_target = save_btn_parent if save_btn_parent else save_btn
    safe_click_robust(click_target)

    # --- 7. Верификация закрытия окна редактирования ---
    print("Ждём закрытия окна редактирования после сохранения времени...")
    try:
        WebDriverWait(driver, 10, poll_frequency=0.5).until(
            EC.invisibility_of_element_located(
                (By.XPATH,
                 "//*[normalize-space(text())='Редактировать событие']")))
        print("Окно редактирования успешно закрыто после изменения времени.")
    except TimeoutException:
        driver.save_screenshot(
            "debug_edit_window_still_open_after_time_edit.png")
        raise TimeoutException(
            "Окно редактирования не закрылось после сохранения времени")

        # ================================================================
    # ЧАСТЬ 4: ИЗМЕНЕНИЕ НАЗВАНИЯ СОБЫТИЯ
    # ================================================================

    new_event_name = "Тестовый вебинар Selenium (изменён)"
    print(f"Готовимся изменить название события на '{new_event_name}'...")

    # --- 1. Повторный клик по событию в расписании ---
    print(f"Ищем событие '{event_name}' для повторного клика...")
    event_element = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, f"//*[contains(text(), '{event_name}')]"))
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
        event_element,
    )
    WebDriverWait(driver, 1).until(lambda d: True)
    remove_overlays()

    try:
        event_element.click()
        print("Клик по событию выполнен.")
    except (ElementClickInterceptedException,
            ElementNotInteractableException) as e:
        print(f"Обычный клик не сработал ({e}), пробуем JS-клик...")
        driver.execute_script("arguments[0].click();", event_element)
    except StaleElementReferenceException:
        event_element = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, f"//*[contains(text(), '{event_name}')]"))
        )
        driver.execute_script("arguments[0].click();", event_element)
        print("Клик выполнен после повторного поиска элемента.")

    # --- 2. Клик «Редактировать» ---
    print("Ждём появления кнопки «Редактировать»...")
    edit_btn_locator = (
        By.XPATH, "//ds-button[.//*[normalize-space(text("
        "))='Редактировать']]//button")
    edit_btn = wait_for_button_ready(edit_btn_locator)

    if not edit_btn:
        driver.save_screenshot("debug_edit_btn_not_found_name_edit.png")
        raise TimeoutException(
            "Кнопка «Редактировать» не появилась при открытии "
            "события для смены названия")

    print(f"Редактировать={edit_btn.size}, displayed={edit_btn.is_displayed()}"
          )
    remove_overlays()
    print("Кликаем на кнопку «Редактировать»...")
    safe_click_robust(edit_btn)

    print("Ждём открытия окна «Редактировать событие»...")
    try:
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//*[normalize-space(text())='Редактировать событие']"))
            )
        print("Окно редактирования успешно открыто.")
    except TimeoutException:
        driver.save_screenshot("debug_edit_window_not_opened_name_edit.png")
        raise TimeoutException(
            "Окно редактирования не открылось для смены названия")

    # --- 3. Ожидание появления поля ввода названия и активация фокуса ---
    print("Ищем поле ввода названия события...")
    name_input: Optional[WebElement] = None
    input_locators_edit = [
        (By.XPATH, "//input[contains(@placeholder, 'посмотреть вебинар')]"),
        (By.CSS_SELECTOR, "input[name='title'], input[type='text']"),
        (By.XPATH, "//*[contains(@class, 'input')]//input"),
    ]
    for loc in input_locators_edit:
        try:
            name_input = short_wait.until(EC.element_to_be_clickable(loc))
            if name_input.is_displayed():
                break
        except TimeoutException:
            continue

    if not name_input:
        driver.save_screenshot("debug_no_name_input_in_edit.png")
        raise TimeoutException(
            "Поле ввода названия события не найдено в окне редактирования")

    # Запоминаем текущее значение
    # (для проверки, что оно действительно изменилось)
    old_value = name_input.get_attribute("value") or ""
    print(f"Текущее название события в поле: '{old_value}'")

    # --- 4. Очистка поля и ввод нового названия ---
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
        name_input,
    )
    WebDriverWait(driver, 0.5).until(lambda d: True)

    # Клик по полю для фокуса
    try:
        name_input.click()
    except (ElementClickInterceptedException, ElementNotInteractableException):
        driver.execute_script("arguments[0].click();", name_input)

    # Очистка: сначала штатный clear(),
    # потом JS fallback, потом Ctrl+A + Delete
    try:
        name_input.clear()
    except Exception as e:
        print(f"clear() не сработал ({e}), очищаем через JS...")
    driver.execute_script("arguments[0].value = '';", name_input)

    try:
        from selenium.webdriver.common.keys import Keys
        name_input.send_keys(Keys.CONTROL, "a")
        name_input.send_keys(Keys.DELETE)
    except Exception as e:
        print(f"Ctrl+A/Delete не сработали ({e}), продолжаем с JS-очисткой")

    WebDriverWait(driver, 0.5).until(lambda d: True)

    # Ввод нового названия
    name_input.send_keys(new_event_name)

    # Ждём, пока в поле появится новое значение
    try:
        WebDriverWait(driver, 5, poll_frequency=0.5).until(
            lambda d: name_input.get_attribute("value") == new_event_name
        )
        print(f"Поле содержит новое название: '{new_event_name}'")
    except TimeoutException:
        driver.save_screenshot("debug_new_name_not_typed.png")
        raise TimeoutException(
            f"Не удалось ввести новое название. Ожидалось: '{new_event_name}',"
            f"текущее: '{name_input.get_attribute('value')}'"
        )

    # Дублируем через JS на случай, если Angular не подхватил значение
    driver.execute_script(
        """
        var element = arguments[0];
        element.value = arguments[1];
        var event = new Event('input', { bubbles: true });
        element.dispatchEvent(event);
        """,
        name_input,
        new_event_name,
    )
    driver.execute_script("arguments[0].blur();", name_input)

    WebDriverWait(driver, 1).until(lambda d: True)

    # Проверяем отсутствие ошибок валидации
    errors = driver.find_elements(
        By.CSS_SELECTOR, ".error, .has-error, [aria-invalid='true']")
    if errors:
        driver.save_screenshot("debug_validation_errors_name_edit.png")
        raise AssertionError(
            f"Ошибки после смены: {[e.text for e in errors if e.text]}")

    # --- 5. Поиск и клик по кнопке «Сохранить» ---
    print("Ищем и кликаем «Сохранить» после смены названия...")
    save_btn: Optional[WebElement] = None
    save_locators_name = [
        (By.XPATH, "//ds-button[contains(., 'Сохранить')]//button"),
        (By.XPATH, "//button[normalize-space(text())='Сохранить']"),
        (By.CSS_SELECTOR, "ds-button[type='primary-blue'], "
         "button[type='submit']"),
        (By.XPATH, "//*[contains(@class, 'save')]//button"),
    ]
    for loc in save_locators_name:
        try:
            save_btn = short_wait.until(EC.element_to_be_clickable(loc))
            if "Сохранить" in save_btn.text:
                break
        except TimeoutException:
            continue

    if not save_btn:
        driver.save_screenshot("debug_no_save_after_name_edit.png")
        raise TimeoutException(
            "Кнопка 'Сохранить' не найдена после редактирования названия")

    save_btn_parent = driver.execute_script(
        """
        var el = arguments[0];
        while (el && el.tagName !== 'DS-BUTTON') { el = el.parentElement; }
        return el;
        """,
        save_btn,
    )

    print("Ждём активации кнопки 'Сохранить'...")
    try:
        WebDriverWait(
            driver, 10, poll_frequency=0.5).until(
                lambda d: save_btn.is_enabled())
        print("Кнопка 'Сохранить' активна.")
    except TimeoutException:
        driver.save_screenshot("debug_save_after_name_edit_disabled.png")
        raise TimeoutException(
            "Кнопка 'Сохранить' не активна после редактирования названия")

    remove_overlays()
    click_target = save_btn_parent if save_btn_parent else save_btn
    safe_click_robust(click_target)

    # --- 6. Верификация закрытия окна редактирования ---
    print("Ждём закрытия окна редактирования после смены названия...")
    try:
        WebDriverWait(driver, 10, poll_frequency=0.5).until(
            EC.invisibility_of_element_located(
                (By.XPATH,
                 "//*[normalize-space(text())='Редактировать событие']")))
        print("Окно редактирования успешно закрыто после смены названия.")
    except TimeoutException:
        driver.save_screenshot(
            "debug_edit_window_still_open_after_name_edit.png")
        raise TimeoutException(
            "Окно редактирования не закрылось после сохранения нового названия"
            )

        # --- 7. ДИАГНОСТИКА: что реально в DOM после сохранения названия ---
    print(
        f"Проверяем, что событие с новым названием '{new_event_name}'...")

    # Дадим Angular/Angular-роутеру шанс обновить список
    WebDriverWait(driver, 3).until(lambda d: True)

    def dump_state(tag: str) -> None:
        print(f"\n===== DIAGNOSTIC: {tag} =====")
        try:
            print(f"[url] {driver.current_url}")
        except Exception:
            pass

        # 1. Есть ли вообще в DOM ключевая часть нового названия
        for key in ["изменён", "изменен", "Selenium", "вебинар"]:
            try:
                els = driver.find_elements(
                    By.XPATH, f"//*[contains(normalize-space(.), '{key}')]")
                visible = [e for e in els if e.is_displayed()]
                print(
                    f"[key='{key}'] всего={len(els)}, видимых={len(visible)}")
                for e in visible[:3]:
                    try:
                        txt = (e.text or "").replace("\n", " ")[:150]
                        print(f"    tag={e.tag_name}, text='{txt}'")
                    except Exception:
                        pass
            except Exception as ex:
                print(f"[key='{key}'] ошибка поиска: {ex}")

        # 2. Есть ли старое название
        try:
            old_els = driver.find_elements(
                By.XPATH, f"//*[contains(normalize-space(.), '{event_name}')]"
            )
            old_visible = [e for e in old_els if e.is_displayed()]
            print(
             f"[OLD NAME '{event_name}'] всего={len(
                 old_els)}, видимых={len(old_visible)}")
        except Exception as ex:
            print(f"[OLD NAME] ошибка: {ex}")

        # 3. Что видно в body
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            print("[body.text первые 1500 символов]")
            print(body_text[:1500])
        except Exception as ex:
            print(f"[body.text] ошибка: {ex}")

        # 4. Открыт ли ещё модал редактирования
        try:
            modal = driver.find_elements(
                By.XPATH,
                "//*[normalize-space(text())='Редактировать событие']"
            )
            modal_visible = [m for m in modal if m.is_displayed()]
            print(f"['Редактировать событие' видимых] = {len(modal_visible)}")
        except Exception:
            pass

        driver.save_screenshot(f"debug_{tag}.png")
        print(f"[screenshot] debug_{tag}.png")
        print("===== END DIAGNOSTIC =====\n")

    dump_state("after_save_name_initial")

    # Пробуем найти новое название РАЗНЫМИ способами
    xpath_variants = [
        f"//*[contains(text(), '{new_event_name}')]",
        f"//*[contains(normalize-space(.), '{new_event_name}')]",
        f"//*[contains(@title, '{new_event_name}')]",
        f"//*[contains(@aria-label, '{new_event_name}')]",
        "//*[contains(normalize-space(.), 'изменён')]",
        "//*[contains(normalize-space(.), 'изменен')]",
    ]

    def find_new(d):
        for xp in xpath_variants:
            try:
                for el in d.find_elements(By.XPATH, xp):
                    if el.is_displayed():
                        return el
            except Exception:
                continue
        return False

    new_event_element = None
    try:
        new_event_element = WebDriverWait(
            driver, 15, poll_frequency=0.5).until(find_new)
        print(f"[OK] Новое название найдено: '{new_event_element.text[:150]}'")
    except TimeoutException:
        print("[WARN] Новое название не найдено за 15с. Делаем refresh...")

    # Если не нашли — пробуем refresh
    if not new_event_element:
        try:
            driver.refresh()
            try:
                wait.until(EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".overlay, .backdrop, .loader")))
            except TimeoutException:
                pass
            WebDriverWait(driver, 3).until(lambda d: True)
        except Exception as ex:
            print(f"[refresh] ошибка: {ex}")

        dump_state("after_save_name_refreshed")

        try:
            new_event_element = WebDriverWait(
                driver, 20, poll_frequency=0.5).until(find_new)
            print(
                f"[OK после refresh] Новое название:'{new_event_element.text[
                    :150]}'")
        except TimeoutException:
            dump_state("after_save_name_final_fail")
            raise TimeoutException(
                f"Событие с новым названием '{
                    new_event_name}' не появилось в расписании. "
                f"См. debug_after_save_name_*.png"
            )

    # Финальная верификация
    assert new_event_element.is_displayed(), \
        f"Событие с новым названием '{
            new_event_name}' найдено, но не отображается."
    print(f"===Событие с новым названием '{new_event_name}' успешно найдено==="
          )
    print("=== ТЕСТ ЗАВЕРШЁН УСПЕШНО ===")

    # ================================================================
    # ЧАСТЬ 5: УДАЛЕНИЕ ИЗМЕНЁННОГО СОБЫТИЯ
    # ================================================================

    print(f"Ищем событие '{new_event_name}' для клика перед удалением...")

    # Дадим UI время на обновление
    WebDriverWait(driver, 3).until(lambda d: True)

    # Диагностика: что реально в DOM
    print("[Debug] Ищем в DOM возможные упоминания события:")
    for key in [new_event_name, "изменён",
                "изменен", event_name, "Selenium", "вебинар"]:
        try:
            els = driver.find_elements(
                By.XPATH, f"//*[contains(normalize-space(.), '{key}')]"
            )
            visible = [e for e in els if e.is_displayed()]
            print(f"  key='{key}': всего={len(els)}, видимых={len(visible)}")
            for e in visible[:3]:
                try:
                    txt = (e.text or "").replace("\n", " ")[:120]
                    print(f"      tag={e.tag_name}, text='{txt}'")
                except Exception:
                    pass
        except Exception as ex:
            print(f"  key='{key}': ошибка {ex}")

    # Пробуем найти событие РАЗНЫМИ способами
    xpath_variants_delete = [
        f"//*[contains(text(), '{new_event_name}')]",
        f"//*[contains(normalize-space(.), '{new_event_name}')]",
        f"//*[contains(@title, '{new_event_name}')]",
        f"//*[contains(@aria-label, '{new_event_name}')]",
        "//*[contains(normalize-space(.), 'изменён')]",
        "//*[contains(normalize-space(.), 'изменен')]",
        f"//*[contains(normalize-space(.), '{event_name}')]",
    ]

    event_element = None
    used_xpath = None
    for xp in xpath_variants_delete:
        try:
            candidates = short_wait.until(
                EC.presence_of_all_elements_located((By.XPATH, xp))
            )
            for el in candidates:
                if el.is_displayed():
                    event_element = el
                    used_xpath = xp
                    break
            if event_element:
                break
        except TimeoutException:
            continue

    if not event_element:
        driver.save_screenshot("debug_event_not_found_before_delete.png")
        try:
            print("[Debug] body.text (первые 1500):")
            print(driver.find_element(By.TAG_NAME, "body").text[:1500])
        except Exception:
            pass
        raise TimeoutException(
            f"Событие '{
                new_event_name}' не найдено в расписании перед удалением. "
            f"См. debug_event_not_found_before_delete.png"
        )

    print(f"[OK] Событие найдено по XPath: {used_xpath}")
    print(f"tag={event_element.tag_name}, text='{(event_element.text or '')[
        :120]}'")

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
        event_element,
    )
    WebDriverWait(driver, 1).until(lambda d: True)
    remove_overlays()

    try:
        event_element.click()
        print("Клик по событию выполнен.")
    except (ElementClickInterceptedException,
            ElementNotInteractableException) as e:
        print(f"Обычный клик не сработал ({e}), пробуем JS-клик...")
        driver.execute_script("arguments[0].click();", event_element)
    except StaleElementReferenceException:
        event_element = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, f"//*[contains(text(), '{new_event_name}')]")
            )
        )
        driver.execute_script("arguments[0].click();", event_element)
        print("Клик выполнен после повторного поиска элемента.")

    # --- 2. Ждём появления кнопки «Удалить» ---
    print("Ждём появления кнопки «Удалить»...")
    delete_btn_locator = (
        By.XPATH,
        "//ds-button[.//*[normalize-space(text())='Удалить']]//button"
        " | //button[normalize-space(text())='Удалить']"
        " | //ds-button[contains(., 'Удалить')]//button",
    )

    delete_btn: Optional[WebElement] = None
    try:
        delete_btn = wait_for_button_ready(delete_btn_locator)
    except TimeoutException:
        driver.save_screenshot("debug_delete_btn_not_found.png")
        raise TimeoutException(
            "Кнопка 'Удалить' не появилась после клика по событию")

    print(
        f"Кнопка Удалить={delete_btn.size}, displayed={delete_btn.is_displayed(
            )}")
    remove_overlays()
    print("Кликаем на кнопку «Удалить»...")
    safe_click_robust(delete_btn)

    WebDriverWait(driver, 1).until(lambda d: True)

    # --- 3. Подтверждение удаления (в модалке или меню) ---
    # У Skyeng часто появляется модалка подтверждения с кнопкой
    # «Удалить» / «Да, удалить» / «Подтвердить».
    print("Проверяем, есть ли окно/меню подтверждения удаления...")

    confirm_locators = [
        # Кнопка во всплывающем меню (popover/menu) с текстом "Удалить"
        (By.XPATH, "//*[@role='menu']//*[normalize-space(text())='Удалить']"),
        (By.XPATH,
         "//*[contains(@class,'cdk-overlay')]"
         "//*[normalize-space(text())='Удалить']"),
        # Модалка подтверждения
        (By.XPATH,
         "//ds-button[.//*[normalize-space(text())='Удалить']]//button"),
        (By.XPATH, "//button[normalize-space(text())='Удалить']"),
        (By.XPATH, "//*[contains(normalize-space(text()), 'Да, удалить')]"),
        (By.XPATH, "//*[contains(normalize-space(text()), 'Подтвердить')]"),
    ]

    confirm_btn: Optional[WebElement] = None
    for loc in confirm_locators:
        try:
            candidates = short_wait.until(
                EC.presence_of_all_elements_located(loc)
            )
            for el in candidates:
                if el.is_displayed() and el.is_enabled():
                    confirm_btn = el
                    break
            if confirm_btn:
                print(f"Найдена кнопка подтверждения по локатору: {loc}")
                break
        except TimeoutException:
            continue

    if confirm_btn:
        print("Кликаем на подтверждение удаления...")
        remove_overlays()
        safe_click_robust(confirm_btn)
        WebDriverWait(driver, 1).until(lambda d: True)
    else:
        print(
            "Окно подтверждения не найдено — возможно, удаление произошло"
            " сразу.")

    # --- 4. Верификация: окно редактирования/подтверждения закрыто ---
    print("Ждём закрытия окна редактирования/подтверждения...")
    try:
        WebDriverWait(driver, 10, poll_frequency=0.5).until(
            EC.invisibility_of_element_located(
                (By.XPATH,
                 "//*[normalize-space(text())='Редактировать событие']")
            )
        )
        print("Окно редактирования закрыто.")
    except TimeoutException:
        driver.save_screenshot("debug_edit_window_still_open_after_delete.png")
        raise TimeoutException(
            "Окно редактирования не закрылось после удаления")

    # --- 5. Верификация: событие пропало из расписания ---
    print(
        f"Проверяем, что событие '{new_event_name}' исчезло из расписания...")

    # Дадим UI обновиться
    WebDriverWait(driver, 2).until(lambda d: True)

    def event_disappeared(d) -> bool:
        # Проверяем и по полному названию, и по ключевой части "изменён"
        for xp in (
            f"//*[contains(text(), '{new_event_name}')]",
            "//*[contains(normalize-space(.), 'изменён')]",
            "//*[contains(normalize-space(.), 'изменен')]",
        ):
            try:
                for el in d.find_elements(By.XPATH, xp):
                    if el.is_displayed():
                        return False
            except Exception:
                continue
        return True

    try:
        WebDriverWait(driver, 10, poll_frequency=0.5).until(event_disappeared)
        print("Событие успешно удалено — в расписании его больше нет.")
    except TimeoutException:
        driver.save_screenshot("debug_event_not_deleted.png")
        # Диагностика: что осталось в DOM
        try:
            leftovers = driver.find_elements(
                By.XPATH, "//*[contains(normalize-space(.), 'изменён')]"
            )
            print(f"[Debug] Осталось видимых упоминаний 'изменён': "
                  f"{len([e for e in leftovers if e.is_displayed()])}")
            print("[Debug] body.text (первые 1000):")
            print(driver.find_element(By.TAG_NAME, "body").text[:1000])
        except Exception:
            pass
        raise TimeoutException(
            f"Событие '{
                new_event_name
                }' всё ещё отображается в расписании после удаления. "
            f"См. debug_event_not_deleted.png"
        )

    # --- 6. Дополнительно: refresh и повторная проверка ---
    print("Обновляем страницу и проверяем ещё раз...")
    try:
        driver.refresh()
        wait.until(EC.invisibility_of_element_located(
            (By.CSS_SELECTOR, ".overlay, .backdrop, .loader")))
    except TimeoutException:
        pass
    WebDriverWait(driver, 2).until(lambda d: True)

    assert event_disappeared(driver), \
        f"После refresh событие '{new_event_name}"
    print("После refresh событие также отсутствует. Удаление подтверждено.")

    print("=== ТЕСТ ПОЛНОСТЬЮ ЗАВЕРШЁН УСПЕШНО ===")
