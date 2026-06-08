"""
硬件控制接口（预留）

为后续接入物理设备提供统一抽象层：
- LED 状态指示灯
- 小型显示屏（e-Paper / LCD）
- 物理按钮输入
- 蜂鸣器

当前为 Mock 实现，可在树莓派等平台上替换为真实 GPIO 控制。
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class LEDPattern(Enum):
    """LED 灯效模式"""
    OFF = "off"
    ON = "on"
    BLINK_SLOW = "blink_slow"      # 慢闪 - 系统正常运行
    BLINK_FAST = "blink_fast"      # 快闪 - 有重要通知
    PULSE = "pulse"                # 呼吸灯 - 比赛进行中
    DOUBLE_BLINK = "double_blink"  # 双闪 - 比赛结果已出


class HardwareController:
    """硬件控制器"""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self._led = LEDMock() if not enabled else None
        self._screen = ScreenMock() if not enabled else None
        self._buzzer = BuzzerMock() if not enabled else None
        self._buttons = ButtonMock() if not enabled else None

    # ── LED 控制 ───────────────────────────────

    def set_led(self, pattern: LEDPattern, color: str = "white"):
        """设置 LED 灯效"""
        if not self.enabled:
            self._led.set_pattern(pattern, color)
            return
        
        # 真实 GPIO 控制（树莓派）
        # import gpiozero
        # led = gpiozero.LED(self.led_pin)
        pass

    def notify_match_start(self):
        """比赛开始通知 - 呼吸灯"""
        self.set_led(LEDPattern.PULSE, "green")

    def notify_match_end(self):
        """比赛结束通知 - 双闪"""
        self.set_led(LEDPattern.DOUBLE_BLINK, "blue")

    def notify_important(self):
        """重要通知 - 快闪"""
        self.set_led(LEDPattern.BLINK_FAST, "red")

    # ── 屏幕控制 ───────────────────────────────

    def display_match(self, match_info: dict):
        """在屏幕上显示比赛信息"""
        if not self.enabled:
            self._screen.show(match_info)
            return
        
        # 真实屏幕控制
        pass

    def clear_screen(self):
        """清屏"""
        if not self.enabled:
            self._screen.clear()

    # ── 蜂鸣器 ───────────────────────────────

    def beep(self, duration: float = 0.2, times: int = 1):
        """蜂鸣器提示"""
        if not self.enabled:
            self._buzzer.beep(duration, times)
            return

    # ── 按钮监听 ───────────────────────────────

    def register_button_callback(self, button_id: int, callback):
        """注册按钮回调"""
        if not self.enabled:
            self._buttons.register_callback(button_id, callback)
            return


# ── Mock 实现（无硬件时使用）──────────────────

class LEDMock:
    def set_pattern(self, pattern: LEDPattern, color: str):
        print(f"[LED] {pattern.value} ({color})")


class ScreenMock:
    def show(self, data: dict):
        print(f"[Screen] {data}")
    
    def clear(self):
        print("[Screen] cleared")


class BuzzerMock:
    def beep(self, duration: float, times: int):
        print(f"[Buzzer] beep x{times} ({duration}s)")


class ButtonMock:
    def __init__(self):
        self._callbacks = {}
    
    def register_callback(self, button_id: int, callback):
        self._callbacks[button_id] = callback
        print(f"[Button] Registered callback for button {button_id}")
