"""测试记忆系统"""

import os
import tempfile
import unittest

from agent.memory import AgentMemory


class TestAgentMemory(unittest.TestCase):
    """AgentMemory 测试"""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.memory = AgentMemory(db_path=self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_create_default_preferences(self):
        """测试创建默认偏好"""
        prefs = self.memory.get_user_preferences("test_user")
        self.assertEqual(prefs["user_id"], "test_user")
        self.assertEqual(prefs["favorite_games"], ["LoL", "CS2", "足球", "篮球"])
        self.assertEqual(prefs["quiet_hours"], "00:00-08:00")

    def test_update_preferences(self):
        """测试更新偏好"""
        self.memory.update_user_preferences(
            "test_user",
            favorite_teams=["T1", "BLG"],
            quiet_hours="23:00-09:00"
        )
        prefs = self.memory.get_user_preferences("test_user")
        self.assertEqual(prefs["favorite_teams"], ["T1", "BLG"])
        self.assertEqual(prefs["quiet_hours"], "23:00-09:00")

    def test_conversation_history(self):
        """测试对话历史"""
        self.memory.add_conversation("test_user", "user", "你好")
        self.memory.add_conversation("test_user", "assistant", "你好！")
        
        history = self.memory.get_conversation_history("test_user")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")

    def test_match_monitor(self):
        """测试比赛监控"""
        monitor_id = self.memory.add_match_monitor(
            "test_user",
            "match_123",
            "T1 vs GEN",
            notify_start=True,
            notify_end=True
        )
        self.assertIsInstance(monitor_id, int)
        
        monitors = self.memory.get_active_monitors("test_user")
        self.assertEqual(len(monitors), 1)
        self.assertEqual(monitors[0]["match_name"], "T1 vs GEN")


if __name__ == "__main__":
    unittest.main()
