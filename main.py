import time
import cv2
import pygetwindow
import numpy as np
import pyautogui as pg
import keyboard
from PIL import ImageGrab
import sys

# Состояния программы
recording = False
should_exit = False

# Целевой цвет для обнаружения [R, G, B]
TARGET_GREEN = np.array([64, 183, 56])
TARGET_WHITE = np.array([255, 255, 255])

# Получаем окно игры
try:
    windows = pygetwindow.getWindowsWithTitle('Schedule I')
    if not windows:
        print("❌ Окно 'Schedule I' не найдено!")
        print("Запустите игру и убедитесь, что окно видимо")
        sys.exit()

    win = windows[0]
    print(f"✅ Окно найдено: {win.title}")
    print(f"Размеры: {win.width}x{win.height}")
    print(f"Позиция: ({win.left}, {win.top})")

    # Корректировки для окон Windows 10/11
    winleft = win.left + 8
    wintop = win.top + 31
    winright = win.right - 8
    winbottom = win.bottom - 8

    print(f"Корректированные границы: {winleft}, {wintop}, {winright}, {winbottom}")

except Exception as e:
    print(f"❌ Ошибка при получении окна: {e}")
    sys.exit()

print("\n" + "=" * 50)
print("Управление (работает в любом окне):")
print("Ctrl+B - начать/остановить запись")
print("Ctrl+Q - экстренная остановка")
print("Ctrl+p - выход")
print("=" * 50)

# Глобальные горячие клавиши
keyboard.add_hotkey('ctrl+b', lambda: toggle_recording())
keyboard.add_hotkey('ctrl+q', lambda: emergency_stop())
keyboard.add_hotkey('ctrl+p', lambda: exit_program())

MINIGAME_LEFT = winleft + 733
MINIGAME_TOP = wintop + 635
MINIGAME_RIGHT = winleft + 1170
MINIGAME_BOTTOM = wintop + 670

green_zones = []
white_zones = []

prev_white_x = None
prev_time = None
direction_right = None
base_movement_prediction = 3
absalute_movement_prediction = base_movement_prediction
movement_speed = 0

def toggle_recording():
    """Переключает режим записи"""
    global recording
    recording = not recording
    status = "начата" if recording else "остановлена"
    print(f"Запись {status}")


def emergency_stop():
    """Экстренная остановка"""
    global recording
    recording = False
    print("⚠️ Экстренная остановка!")


def exit_program():
    """Выход из программы"""
    global should_exit
    should_exit = True
    print("Выход из программы...")
    cv2.destroyAllWindows()

img = None

while not should_exit:
    if recording:
        current_time = time.time()

        pg.click(win.left + 50, win.top + 50)
        time.sleep(0.0001)
        screenshot = ImageGrab.grab()
        screenshot = screenshot.crop((MINIGAME_LEFT, MINIGAME_TOP, MINIGAME_RIGHT, MINIGAME_BOTTOM))
        img = np.array(screenshot)

        if img is not None:
            green_zones.clear()
            white_zones.clear()

            hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
            lower_green = np.array([35, 50, 50])  # Широкий диапазон зеленого
            upper_green = np.array([85, 255, 255])
            mask = cv2.inRange(hsv, lower_green, upper_green)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            print(f"Найдено зеленых контуров: {len(contours)}")

            for contour in contours:
                if cv2.contourArea(contour) >= 1:
                    x,y,w,h = cv2.boundingRect(contour)

                    center_x = x + w // 2
                    center_y = y + h // 2

                    print(f"X: {center_x}, Y: {center_y}, W: {w}, H: {h}")

                    green_zones.append([center_x, center_y, w, h])

            lower_white = np.array([0, 0, 200])  # Широкий диапазон белого
            upper_white = np.array([180, 30, 255])
            mask = cv2.inRange(hsv, lower_white, upper_white)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                if cv2.contourArea(contour) > 5:
                    x,y,w,h = cv2.boundingRect(contour)

                    center_x = x + w // 2
                    center_y = y + h // 2

                    print(f"X: {center_x}, Y: {center_y}")

                    white_zones.append([center_x, center_y])

                    break

            if white_zones and green_zones:
                white_x = white_zones[0][0]

                if prev_white_x is not None and prev_time is not None:
                    time_diff = current_time - prev_time
                    if time_diff > 0:
                        movement = white_x - prev_white_x
                        movement_speed = movement / time_diff

                        absalute_movement_prediction = int(base_movement_prediction + (movement_speed * 0.0489))
                        print(f"Скорость: {movement_speed:.1f} px/s, Предсказание: {absalute_movement_prediction:.1f}")

                if prev_white_x is None:
                    prev_white_x = white_x
                    continue
                else:
                    if prev_white_x < white_x:
                        direction_right = True
                    else:
                        direction_right = False

                    prev_white_x = white_x
                    prev_time = current_time

                    if direction_right:
                        green_zones_x = []
                        green_zones_w = []

                        for green_zone in green_zones:
                            if green_zone[0] > white_x:
                                green_zones_x.append(green_zone[0])
                                green_zones_w.append([green_zone[0], green_zone[2]])

                        green_zones_w_dict = dict(green_zones_w)

                        if green_zones_x:
                            green_zones_x.sort()

                            left_bound = green_zones_x[0] - (green_zones_w_dict.get(green_zones_x[0]) // 2)
                            right_bound = green_zones_x[0] + (green_zones_w_dict.get(green_zones_x[0]) // 2)

                            if left_bound <= (white_x + absalute_movement_prediction) <= right_bound:
                                keyboard.send(' ')
                                toggle_recording()
                    else:
                        green_zones_x = []
                        green_zones_w = []

                        for green_zone in green_zones:
                            if green_zone[0] < white_x:
                                green_zones_x.append(green_zone[0])
                                green_zones_w.append([green_zone[0], green_zone[2]])

                        green_zones_w_dict = dict(green_zones_w)

                        if green_zones_x:
                            green_zones_x.sort()
                            green_zones_x = green_zones_x[::-1]

                            left_bound = green_zones_x[0] - (green_zones_w_dict.get(green_zones_x[0]) // 2)
                            right_bound = green_zones_x[0] + (green_zones_w_dict.get(green_zones_x[0]) // 2)

                            if left_bound <= (white_x - absalute_movement_prediction) <= right_bound:
                                keyboard.send(' ')
                                toggle_recording()

    time.sleep(0.01)