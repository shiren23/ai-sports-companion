"""
比赛监控任务

后台持续监控用户关注的比赛状态，在关键节点主动推送通知：
- 比赛即将开始
- 比赛正式开始
- 比分变化
- 比赛结束 + 结果
"""

import time
from datetime import datetime
from threading import Thread

from agent.memory import AgentMemory


class MatchMonitor:
    """比赛监控器"""

    def __init__(self, check_interval: int = 300):
        """
        Args:
            check_interval: 检查间隔（秒），默认5分钟
        """
        self.check_interval = check_interval
        self.memory = AgentMemory()
        self.running = False
        self._thread: Thread | None = None
        self._callbacks: list[callable] = []

    def start(self):
        """启动监控循环"""
        if self.running:
            return
        
        self.running = True
        self._thread = Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print(f"[Monitor] 比赛监控已启动，检查间隔 {self.check_interval} 秒")

    def stop(self):
        """停止监控"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[Monitor] 比赛监控已停止")

    def register_callback(self, callback: callable):
        """注册通知回调函数"""
        self._callbacks.append(callback)

    def _monitor_loop(self):
        """监控主循环"""
        while self.running:
            try:
                self._check_monitors()
            except Exception as e:
                print(f"[Monitor] 检查出错: {e}")
            
            time.sleep(self.check_interval)

    def _check_monitors(self):
        """检查所有活跃的监控任务"""
        monitors = self.memory.get_active_monitors()
        
        for monitor in monitors:
            # TODO: 调用 API 查询比赛最新状态
            # 对比上次状态，如果有变化则触发通知
            
            # 简化演示：模拟检测
            match_id = monitor["match_id"]
            match_name = monitor["match_name"]
            
            # 这里应该查询真实 API 获取比赛状态
            # 目前先打印日志
            pass

    def _notify(self, user_id: str, event_type: str, match_name: str, detail: str):
        """触发通知"""
        message = f"[{event_type}] {match_name}: {detail}"
        
        for callback in self._callbacks:
            try:
                callback(user_id, event_type, match_name, detail)
            except Exception as e:
                print(f"[Monitor] 回调执行失败: {e}")
        
        print(f"[Notify → {user_id}] {message}")


# 全局监控实例
_default_monitor: MatchMonitor | None = None


def get_monitor() -> MatchMonitor:
    """获取全局监控实例"""
    global _default_monitor
    if _default_monitor is None:
        _default_monitor = MatchMonitor()
    return _default_monitor
