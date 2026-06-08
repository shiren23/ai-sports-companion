#!/usr/bin/env python3
"""
AI Sports Companion - CLI 入口

命令行交互模式，启动后可以通过文字与智能体对话。
支持语音播报（如已配置）。

用法:
    python main.py              # 启动交互模式
    python main.py --voice      # 启用语音播报
    python main.py --query "今晚有什么比赛？"  # 单次查询
"""

import argparse
import sys

from agent.core import SportsAgent
from interfaces.voice_output import VoiceOutput


def print_banner():
    """打印启动 banner"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║    🏆  AI Sports Companion  -  你的赛事智能伙伴            ║
║                                                           ║
║    用自然语言查询电竞 & 体育比赛 · 主动推送 · 语音播报       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    print("输入 'help' 查看帮助，'quit' 退出\n")


def print_help():
    """打印帮助信息"""
    print("""
📖 可用指令:
  help          - 显示帮助
  quit / exit   - 退出程序
  voice on      - 开启语音播报
  voice off     - 关闭语音播报
  prefs         - 查看当前偏好设置
  clear         - 清空对话历史

💡 你可以这样提问:
  "今晚有什么比赛？"
  "帮我盯着T1的比赛"
  "利物浦最近的战绩怎么样？"
  "周末别推送，但BLG的比赛要叫我"
    """)


def run_interactive(voice_enabled: bool = False):
    """运行交互模式"""
    print_banner()
    
    agent = SportsAgent()
    voice = VoiceOutput()
    voice.enabled = voice_enabled

    while True:
        try:
            user_input = input("你: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 再见！")
            break

        if not user_input:
            continue

        # 内置指令
        if user_input.lower() in ("quit", "exit", "q"):
            print("👋 再见！")
            break
        
        if user_input.lower() == "help":
            print_help()
            continue
        
        if user_input.lower() == "voice on":
            voice.enabled = True
            print("🎙️ 语音播报已开启")
            continue
        
        if user_input.lower() == "voice off":
            voice.enabled = False
            print("🔇 语音播报已关闭")
            continue
        
        if user_input.lower() == "prefs":
            prefs = agent.memory.get_user_preferences("default")
            print(f"\n⚙️ 当前偏好:")
            for k, v in prefs.items():
                print(f"  {k}: {v}")
            print()
            continue
        
        if user_input.lower() == "clear":
            agent.memory.clear_conversation_history("default")
            print("🧹 对话历史已清空\n")
            continue

        # 调用 Agent
        try:
            result = agent.chat(user_input)
            reply = result["reply"]
            
            print(f"\n🤖 {reply}\n")
            
            # 语音播报
            voice.speak(reply)
            
        except Exception as e:
            print(f"\n❌ 出错了: {e}\n")


def run_single_query(query: str, voice_enabled: bool = False):
    """单次查询模式"""
    agent = SportsAgent()
    voice = VoiceOutput()
    voice.enabled = voice_enabled

    try:
        result = agent.chat(query)
        reply = result["reply"]
        print(reply)
        voice.speak(reply)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="AI Sports Companion")
    parser.add_argument("--voice", action="store_true", help="启用语音播报")
    parser.add_argument("--query", type=str, help="单次查询模式")
    args = parser.parse_args()

    if args.query:
        run_single_query(args.query, voice_enabled=args.voice)
    else:
        run_interactive(voice_enabled=args.voice)


if __name__ == "__main__":
    main()
