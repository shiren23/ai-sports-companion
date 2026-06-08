"""
AI Agent 核心引擎

采用 ReAct (Reasoning + Acting) 模式：
Thought → Action → Observation → ... → Answer

Agent 接收用户输入，理解意图，规划任务，调用工具，生成回复。
"""

import json
import os
from typing import Any

from dotenv import load_dotenv

from .memory import AgentMemory
from .planner import TaskPlanner
from .tools import ToolRegistry

load_dotenv()


class SportsAgent:
    """赛事智能体主类"""

    SYSTEM_PROMPT = """你是一个专业的体育赛事智能助手，名叫 "SportMate"。

## 核心能力
1. 查询电竞和体育比赛的赛程、比分、结果
2. 根据用户偏好主动推送比赛信息
3. 理解自然语言指令，无需用户适应固定界面

## 交互原则
- 用自然、口语化的中文回复，像朋友聊天一样
- 主动理解用户意图，不要让用户反复解释
- 记住用户偏好，越用越懂用户
- 可以主动提问澄清需求，但不要过度追问

## 可用工具
你有以下工具可以使用（通过 function calling）：
- search_matches: 搜索比赛（支持按时间、队伍、游戏类型筛选）
- get_match_detail: 获取单场比赛详情
- get_team_info: 获取队伍信息
- get_live_score: 获取实时比分
- set_reminder: 设置比赛提醒
- start_monitor: 开始监控比赛状态
- get_user_preferences: 获取用户偏好
- update_user_preferences: 更新用户偏好

## 回复风格
- 简洁但有信息量，不要冗长
- 对关键信息加粗或高亮
- 多场比赛时用列表展示
- 适当使用emoji增加亲和力
"""

    def __init__(self, memory: AgentMemory | None = None):
        self.memory = memory or AgentMemory()
        self.tools = ToolRegistry()
        self.planner = TaskPlanner()
        self._init_llm()

    def _init_llm(self):
        """初始化 LLM 客户端"""
        provider = os.getenv("LLM_PROVIDER", "openai")
        
        if provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL") or None,
            )
            self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        elif provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        self.provider = provider

    def chat(self, user_input: str, user_id: str = "default") -> dict[str, Any]:
        """
        主对话入口
        
        Args:
            user_input: 用户输入
            user_id: 用户标识（用于记忆隔离）
            
        Returns:
            {"reply": str, "actions": list, "data": dict}
        """
        # 1. 获取用户记忆和对话历史
        user_prefs = self.memory.get_user_preferences(user_id)
        history = self.memory.get_conversation_history(user_id, limit=10)

        # 2. 构建 messages
        messages = self._build_messages(user_input, history, user_prefs)

        # 3. 调用 LLM（支持 function calling）
        tools = self.tools.get_openai_tools()
        
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=2048,
            )
        else:
            # Anthropic 格式转换
            response = self._call_anthropic(messages, tools)

        # 4. 处理回复
        message = response.choices[0].message
        result = {
            "reply": "",
            "actions": [],
            "data": {},
        }

        # 处理 function calling
        if hasattr(message, "tool_calls") and message.tool_calls:
            # 执行工具调用
            tool_results = self._execute_tool_calls(message.tool_calls)
            
            # 将工具结果返回给 LLM，生成最终回复
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [tc.model_dump() for tc in message.tool_calls]
            })
            for tr in tool_results:
                messages.append(tr)
            
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
            )
            result["reply"] = final_response.choices[0].message.content
            result["actions"] = [tc.function.name for tc in message.tool_calls]
            result["data"] = {
                tc.function.name: json.loads(tc.function.arguments)
                for tc in message.tool_calls
            }
        else:
            result["reply"] = message.content or "收到！"

        # 5. 保存对话历史
        self.memory.add_conversation(user_id, "user", user_input)
        self.memory.add_conversation(user_id, "assistant", result["reply"])

        return result

    def _build_messages(
        self, 
        user_input: str, 
        history: list[dict], 
        user_prefs: dict
    ) -> list[dict]:
        """构建 LLM 消息列表"""
        # 用户偏好摘要
        prefs_summary = self._format_preferences(user_prefs)
        
        system_msg = self.SYSTEM_PROMPT
        if prefs_summary:
            system_msg += f"\n\n## 当前用户偏好\n{prefs_summary}"

        messages = [{"role": "system", "content": system_msg}]

        # 添加历史对话
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})

        # 添加当前输入
        messages.append({"role": "user", "content": user_input})

        return messages

    def _format_preferences(self, prefs: dict) -> str:
        """格式化用户偏好为文本"""
        if not prefs:
            return ""
        
        lines = []
        if prefs.get("favorite_teams"):
            lines.append(f"关注队伍: {', '.join(prefs['favorite_teams'])}")
        if prefs.get("favorite_games"):
            lines.append(f"关注赛事: {', '.join(prefs['favorite_games'])}")
        if prefs.get("quiet_hours"):
            lines.append(f"勿扰时段: {prefs['quiet_hours']}")
        if prefs.get("notification_style"):
            lines.append(f"通知风格: {prefs['notification_style']}")
        
        return "\n".join(lines) if lines else ""

    def _execute_tool_calls(self, tool_calls) -> list[dict]:
        """执行工具调用"""
        results = []
        for tc in tool_calls:
            func_name = tc.function.name
            func_args = json.loads(tc.function.arguments)
            
            try:
                result = self.tools.execute(func_name, func_args)
                results.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })
            except Exception as e:
                results.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps({"error": str(e)}),
                })
        
        return results

    def _call_anthropic(self, messages: list, tools: list):
        """Anthropic API 调用（简化版，后续完善）"""
        # TODO: 实现 Anthropic 的 tools 调用
        # 先走 text 模式 fallback
        import anthropic
        
        system_msg = ""
        clean_messages = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                clean_messages.append(m)
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_msg,
            messages=clean_messages,
        )
        
        # 包装成类似 OpenAI 的格式
        class FakeChoice:
            def __init__(self, content):
                self.message = type("obj", (object,), {
                    "content": content,
                    "tool_calls": None,
                })()
        
        class FakeResponse:
            def __init__(self, choices):
                self.choices = choices
        
        return FakeResponse([FakeChoice(response.content[0].text)])


if __name__ == "__main__":
    # 简单测试
    agent = SportsAgent()
    result = agent.chat("今晚有什么比赛？")
    print(result["reply"])
