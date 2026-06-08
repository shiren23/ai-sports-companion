#!/usr/bin/env python3
"""
AI Sports Companion - Web 界面入口

基于 FastAPI + WebSocket 的实时对话界面。
打开浏览器访问 http://localhost:8000 即可使用。

用法:
    python web_app.py             # 启动服务
    python web_app.py --port 8080 # 指定端口
"""

import argparse
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from agent.core import SportsAgent

# ── HTML 前端 ─────────────────────────────────

CHAT_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Sports Companion</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            padding: 16px 24px;
            background: rgba(0,0,0,0.3);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 { font-size: 20px; display: flex; align-items: center; gap: 8px; }
        .header .subtitle { font-size: 12px; opacity: 0.6; margin-top: 4px; }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .message {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 16px;
            line-height: 1.5;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user {
            align-self: flex-end;
            background: #4a90d9;
            border-bottom-right-radius: 4px;
        }
        .message.bot {
            align-self: flex-start;
            background: rgba(255,255,255,0.1);
            border-bottom-left-radius: 4px;
        }
        .message .role {
            font-size: 11px;
            opacity: 0.7;
            margin-bottom: 4px;
        }
        .input-area {
            padding: 16px 24px;
            background: rgba(0,0,0,0.3);
            border-top: 1px solid rgba(255,255,255,0.1);
            display: flex;
            gap: 12px;
        }
        .input-area input {
            flex: 1;
            padding: 12px 16px;
            border: none;
            border-radius: 24px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 14px;
            outline: none;
        }
        .input-area input::placeholder { color: rgba(255,255,255,0.4); }
        .input-area button {
            padding: 12px 24px;
            border: none;
            border-radius: 24px;
            background: #4a90d9;
            color: #fff;
            font-size: 14px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .input-area button:hover { background: #357abd; }
        .input-area button:disabled { opacity: 0.5; cursor: not-allowed; }
        .typing {
            align-self: flex-start;
            padding: 12px 16px;
            opacity: 0.6;
            font-style: italic;
        }
        .hint {
            text-align: center;
            padding: 40px 20px;
            opacity: 0.5;
        }
        .hint p { margin: 8px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 AI Sports Companion</h1>
        <div class="subtitle">用自然语言查询赛事 · 语音播报 · 主动推送</div>
    </div>
    
    <div class="chat-container" id="chat">
        <div class="hint">
            <p>👋 你好！我是你的赛事智能助手</p>
            <p>试试问我："今晚有什么比赛？"</p>
        </div>
    </div>
    
    <div class="input-area">
        <input type="text" id="messageInput" placeholder="输入消息..." autocomplete="off">
        <button id="sendBtn" onclick="sendMessage()">发送</button>
    </div>

    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        const chat = document.getElementById('chat');
        const input = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');

        ws.onopen = () => console.log('Connected');
        ws.onclose = () => addMessage('bot', '连接已断开，请刷新页面重试');
        ws.onerror = (e) => console.error('WebSocket error:', e);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            removeTyping();
            addMessage(data.role, data.content);
        };

        function addMessage(role, content) {
            const div = document.createElement('div');
            div.className = `message ${role}`;
            div.innerHTML = `<div class="role">${role === 'user' ? '你' : '🤖 SportMate'}</div>${escapeHtml(content)}`;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        function addTyping() {
            const div = document.createElement('div');
            div.className = 'typing';
            div.id = 'typing';
            div.textContent = '🤖 思考中...';
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        function removeTyping() {
            const el = document.getElementById('typing');
            if (el) el.remove();
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML.replace(/\\n/g, '<br>');
        }

        function sendMessage() {
            const text = input.value.trim();
            if (!text) return;
            
            addMessage('user', text);
            input.value = '';
            addTyping();
            
            ws.send(JSON.stringify({message: text}));
        }

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        input.focus();
    </script>
</body>
</html>
"""

# ── FastAPI 应用 ─────────────────────────────

app = FastAPI(title="AI Sports Companion")
agents: dict[str, SportsAgent] = {}


@app.get("/", response_class=HTMLResponse)
async def index():
    """聊天页面"""
    return CHAT_HTML


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 对话"""
    await websocket.accept()
    
    # 每个连接创建一个独立的 Agent 实例（带记忆）
    session_id = str(id(websocket))
    if session_id not in agents:
        agents[session_id] = SportsAgent()
    agent = agents[session_id]

    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "").strip()
            
            if not user_message:
                continue
            
            # 调用 Agent
            try:
                result = agent.chat(user_message)
                reply = result["reply"]
            except Exception as e:
                reply = f"抱歉，处理出错了: {str(e)}"
            
            await websocket.send_json({"role": "bot", "content": reply})
    
    except WebSocketDisconnect:
        # 清理
        if session_id in agents:
            del agents[session_id]
    except Exception as e:
        await websocket.send_json({"role": "bot", "content": f"连接异常: {str(e)}"})
        await websocket.close()


def main():
    parser = argparse.ArgumentParser(description="AI Sports Companion Web")
    parser.add_argument("--host", default="0.0.0.0", help="绑定地址")
    parser.add_argument("--port", type=int, default=8000, help="端口")
    args = parser.parse_args()

    import uvicorn
    print(f"""
🏆 AI Sports Companion Web 已启动！

打开浏览器访问: http://localhost:{args.port}
    """)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
