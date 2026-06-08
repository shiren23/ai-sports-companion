"""
语音输出模块 (TTS)

支持多种 TTS 引擎：
- edge_tts: 免费，基于微软 Edge，质量高
- gtts: Google TTS，需要网络
- pyttsx3: 本地，无需网络
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Literal


class VoiceOutput:
    """语音播报器"""

    def __init__(
        self,
        engine: Literal["edge_tts", "gtts", "pyttsx3"] = "edge_tts",
        language: str = "zh-CN",
        speed: str = "+0%",
    ):
        self.engine = engine
        self.language = language
        self.speed = speed
        self.enabled = True

    def speak(self, text: str) -> None:
        """
        语音播报文本
        
        Args:
            text: 要播报的文本（会自动截断过长内容）
        """
        if not self.enabled:
            return

        # 截断过长文本（保留前300字）
        if len(text) > 300:
            text = text[:300] + "..."

        if self.engine == "edge_tts":
            asyncio.run(self._speak_edge_tts(text))
        elif self.engine == "gtts":
            self._speak_gtts(text)
        elif self.engine == "pyttsx3":
            self._speak_pyttsx3(text)
        else:
            print(f"[TTS] {text}")

    async def _speak_edge_tts(self, text: str):
        """使用 edge-tts"""
        try:
            import edge_tts
            import playsound3

            voice = "zh-CN-XiaoxiaoNeural" if self.language == "zh-CN" else "en-US-AriaNeural"
            communicate = edge_tts.Communicate(text, voice, rate=self.speed)
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                temp_path = fp.name
            
            await communicate.save(temp_path)
            playsound3.playsound(temp_path)
            os.unlink(temp_path)
        except ImportError:
            print("[TTS] 未安装 edge-tts 或 playsound3，使用文本输出")
            print(f"🗣️  {text}")
        except Exception as e:
            print(f"[TTS] 播报失败: {e}")

    def _speak_gtts(self, text: str):
        """使用 gTTS"""
        try:
            from gtts import gTTS
            import playsound3

            tts = gTTS(text=text, lang="zh" if self.language == "zh-CN" else "en")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                temp_path = fp.name
            tts.save(temp_path)
            playsound3.playsound(temp_path)
            os.unlink(temp_path)
        except ImportError:
            print("[TTS] 未安装 gTTS")
            print(f"🗣️  {text}")
        except Exception as e:
            print(f"[TTS] 播报失败: {e}")

    def _speak_pyttsx3(self, text: str):
        """使用 pyttsx3（本地）"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except ImportError:
            print("[TTS] 未安装 pyttsx3")
            print(f"🗣️  {text}")
        except Exception as e:
            print(f"[TTS] 播报失败: {e}")

    def enable(self):
        """启用语音"""
        self.enabled = True

    def disable(self):
        """禁用语音"""
        self.enabled = False
