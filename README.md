# 🏆 AI Sports Companion

> AI Native 赛事智能体 —— 用自然语言与赛事对话

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**AI Sports Companion** 是一个 AI Native 的开源项目，旨在用自然语言交互取代传统体育/电竞资讯 App 的死板界面。它不是"带 AI 功能的体育网站"，而是一个真正以 AI 为核心、以对话为交互方式的赛事智能体。

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🗣️ **自然语言交互** | "今晚有什么值得看的比赛？" 而不是点点点筛选 |
| 🧠 **意图理解** | 理解模糊表达，如"帮我盯着 T1"、"周末别吵我" |
| 💾 **记忆系统** | 记住你的偏好、关注的队伍、安静时段 |
| 🔔 **主动推送** | 比赛开始、关键时刻、意外结果主动通知你 |
| 🔊 **语音播报** | 支持 TTS 语音输出，闭眼也能听赛况 |
| 🔌 **硬件预留** | 内置硬件控制接口，可接 LED、小屏幕、按钮等 |
| 🎮 **电竞+体育** | 覆盖 LoL、CS2、Dota2、足球、篮球等 |

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/shiren23/ai-sports-companion.git
cd ai-sports-companion
```

### 2. 安装依赖

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

### 4. 运行

```bash
# 命令行交互模式
python main.py

# Web 界面模式
python web_app.py
```

---

## 🏗️ 架构设计

```
ai-sports-companion/
├── agent/                    # AI Agent 核心引擎
│   ├── core.py              # ReAct 循环：推理 → 行动 → 观察
│   ├── memory.py            # 用户记忆与偏好
│   ├── tools.py             # 工具注册与调度
│   └── planner.py           # 任务规划器
├── api_clients/             # 数据源客户端
│   ├── pandascore.py        # 电竞数据 (LoL/CS2/Dota2...)
│   ├── football_api.py      # 足球数据 (API-Football)
│   └── base.py              # 抽象基类
├── interfaces/              # 交互接口层
│   ├── voice_input.py       # 语音输入 (ASR)
│   ├── voice_output.py      # 语音输出 (TTS)
│   ├── web_chat.py          # Web 对话界面
│   ├── cli_chat.py          # 命令行界面
│   └── hardware_ctrl.py     # 硬件控制预留
├── memory/                  # 持久化存储
│   └── sqlite_store.py      # SQLite 记忆数据库
├── tasks/                   # 后台任务
│   └── match_monitor.py     # 比赛监控与主动推送
├── tests/                   # 测试
├── config.yaml              # 项目配置
├── main.py                  # CLI 入口
└── web_app.py               # Web 入口
```

---

## 🎮 使用示例

### CLI 交互

```
🤖 AI Sports Companion 已启动！

你: 今晚有什么比赛？
🤖: 今晚有 3 场值得关注的比赛：
   1. 23:00 利物浦 vs 曼城（英超争冠关键战）
   2. 02:00 T1 vs GEN（LCK 春季赛决赛）
   3. 08:00 湖人 vs 掘金（NBA 季后赛）
   要我帮你设置提醒吗？

你: 帮我盯着 T1 那场，开打了叫我，结束了告诉我结果
🤖: 好的，已为你启动对「T1 vs GEN」的监控。
   • 比赛开始时会通知你
   • 每局结束会推送比分
   • 全场比赛结束后会发送战报

你: 我周末想睡个懒觉，早上别推送
🤖: 明白！已更新你的勿扰时段：周六日 00:00-10:00。
   但如果有你特别关注的比赛开始，还是会叫醒你，可以吗？

你: 行
```

### Web 界面

启动 `python web_app.py` 后访问 `http://localhost:8000`，打开对话式 Web 界面：

- 💬 自然语言查询比赛
- 🔔 一键设置比赛提醒
- 📝 查看对话历史

---

## 🔧 配置说明

编辑 `config.yaml`：

```yaml
# LLM 配置
llm:
  provider: openai          # openai / anthropic / ollama
  model: gpt-4o-mini        # 或 claude-3-5-sonnet / qwen2.5
  api_key: ${OPENAI_API_KEY}
  base_url: null            # 可选，用于第三方中转

# 数据源配置
data_sources:
  pandascore:
    enabled: true
    api_key: ${PANDASCORE_API_KEY}
    free_tier: true         # 使用免费版 (1000 req/h)
  football_api:
    enabled: true
    api_key: ${FOOTBALL_API_KEY}

# 语音配置
voice:
  input_enabled: false      # 是否开启语音输入（需麦克风）
  output_enabled: true      # 是否开启语音播报
  tts_engine: edge_tts      # edge_tts / pyttsx3

# 硬件配置（预留）
hardware:
  enabled: false
  led_pin: 18               # GPIO 引脚
  screen_type: null         # e-paper / lcd / null

# 用户偏好默认值
user_defaults:
  favorite_teams: []
  favorite_games: ["LoL", "CS2", "足球"]
  quiet_hours: "00:00-08:00"
  notification_style: "normal"  # aggressive / normal / silent
```

---

## 🔌 数据源

| 数据源 | 类型 | 免费额度 | 说明 |
|--------|------|----------|------|
| [PandaScore](https://pandascore.co/) | 电竞 | 1000 req/h | 赛程免费，赛果需付费 |
| [API-Football](https://www.api-football.com/) | 足球 | 100 req/day | $19/月 解锁更多 |
| [TheSportsDB](https://www.thesportsdb.com/) | 综合 | 免费 | 个人项目友好 |

> 💡 **提示**：如果你只需要基础赛程和关注提醒，免费版完全够用！

---

## 🔮 硬件扩展（预留接口）

项目内置硬件控制接口，可轻松接入：

| 硬件 | 用途 | 状态 |
|------|------|------|
| LED 状态灯 | 比赛进行中/有结果闪烁 | 🔜 预留接口 |
| 小型显示屏 | 显示当前比赛/比分 | 🔜 预留接口 |
| 物理按钮 | 快捷触发查询/静音 | 🔜 预留接口 |
| 智能音箱 | 语音交互入口 | 🔜 预留接口 |

---

## 🤝 贡献指南

欢迎提交 Issue 和 PR！

1. Fork 本仓库
2. 创建你的分支 (`git checkout -b feature/amazing`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing`)
5. 打开 Pull Request

---

## 📄 许可证

[MIT License](LICENSE) © 2025 shiren23

---

## 🙏 致谢

- [PandaScore](https://pandascore.co/) - 电竞数据支持
- [API-Football](https://www.api-football.com/) - 体育数据支持
- 所有开源贡献者

---

> 🎯 **愿景**：让获取赛事信息像和朋友聊天一样自然。
