# LiveKit Agents Plugin for Tencent Cloud

[Tencent Cloud](https://cloud.tencent.com/) speech services plugin for the LiveKit Agents framework. Provides real-time speech-to-text (ASR) and streaming text-to-speech (TTS) capabilities.

## Installation

```bash
pip install livekit-agents livekit-plugins-tencentcloud
```

## Prerequisites

1. Create a [Tencent Cloud](https://cloud.tencent.com/) account
2. [Activate the ASR service](https://console.cloud.tencent.com/asr)
3. [Activate the TTS service](https://console.cloud.tencent.com/tts)
4. Create API keys at [API Key Management](https://console.cloud.tencent.com/cam/capi) to get `SecretId`, `SecretKey`, and your `AppId`

## Usage

### Environment Variables

```bash
export TENCENTCLOUD_APPID="your-app-id"
export TENCENTCLOUD_SECRET_ID="your-secret-id"
export TENCENTCLOUD_SECRET_KEY="your-secret-key"
```

### Speech-to-Text (ASR)

```python
from livekit.plugins.tencentcloud import STT

stt = STT(
    model="16k_zh_en",  # Chinese-English-Cantonese large model
    enable_intermediate_result=True,
    enable_word_info=True,
    enable_vad=True,
)
```

#### Supported Models

| Model | Description |
|-------|-------------|
| `16k_zh_en` | Chinese-English-Cantonese + 9 dialects large model (recommended) |
| `16k_zh_large` | Mandarin-dialect-English large model |
| `16k_multi_lang` | Multi-language large model (15 languages) |
| `16k_en_large` | English large model |
| `16k_zh` | Chinese general |
| `16k_yue` | Cantonese |
| `16k_en` | English general |
| `8k_zh_large` | Phone scenario large model (supports 27 dialects) |

### Text-to-Speech (TTS)

```python
from livekit.plugins.tencentcloud import TTS

tts = TTS(
    voice="101001",  # 智晓白 (Zhixiaobai)
    codec="pcm",
    sample_rate=16000,
    volume=0.0,
    speed=0.0,
    enable_subtitle=True,
)
```

#### Supported Voices

| Voice ID | Name | Gender | Scene |
|----------|------|--------|-------|
| `101001` | 智晓白 | Male | General |
| `101002` | 智晓夏 | Female | General |
| `101003` | 智晓秋 | Female | General |
| `101004` | 智晓冬 | Male | General |
| `101005` | 智晓萌 | Female | Customer Service |
| `101006` | 智晓帅 | Male | Customer Service |
| `1001001` | 智晓颜 | Female | Emotional |
| `1001002` | 智晓美 | Female | Emotional |
| `1005001` | 智晓云 | Female | Super-natural |
| `1005002` | 智晓风 | Male | Super-natural |

#### Emotion Control (Multi-emotion voices only)

```python
tts = TTS(
    voice="1001001",  # Multi-emotion voice
    emotion_category="happy",  # neutral, sad, happy, angry, fear, news, story, etc.
    emotion_intensity=100,  # [50, 200]
)
```

### Complete Agent Example

```python
import asyncio
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.plugins import tencentcloud
from livekit.agents.voice import Agent

class MyAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a helpful assistant.",
            stt=tencentcloud.STT(model="16k_zh_en"),
            llm=...,  # Your preferred LLM
            tts=tencentcloud.TTS(voice="101001"),
        )

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    agent = MyAgent()
    agent.session.start(ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

## Features

### STT Features
- Real-time streaming speech recognition
- Support for Chinese, English, Cantonese, and 27+ dialects
- Intermediate results (interim transcripts)
- Word-level timestamps
- Voice activity detection (VAD)
- Hotword boosting
- Custom model support
- Smart number conversion

### TTS Features
- Streaming text-to-speech synthesis
- 100+ Chinese and English voices
- Premium, large model, and super-natural voice qualities
- Emotion control (for multi-emotion voices)
- Adjustable speed, volume
- Word-level timestamps
- PCM and MP3 output formats

## API Reference

### STT Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | `"16k_zh_en"` | Engine model type |
| `language` | str | `"16k_zh_en"` | Language/engine code |
| `sample_rate` | int | `16000` | Audio sample rate in Hz |
| `enable_intermediate_result` | bool | `True` | Return interim results |
| `enable_word_info` | bool | `True` | Return word-level timestamps |
| `enable_vad` | bool | `True` | Enable voice activity detection |
| `filter_dirty` | int | `0` | Filter dirty words (0/1/2) |
| `filter_modal` | int | `0` | Filter modal words (0/1/2) |
| `filter_punc` | int | `0` | Filter ending period (0/1) |
| `convert_num_mode` | int | `1` | Number conversion (0/1/3) |
| `hotword_id` | str | `None` | Hotword table ID |
| `hotword_list` | str | `None` | Temporary hotword list |
| `customization_id` | str | `None` | Custom model ID |

### TTS Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voice` | str | `"101001"` | Voice ID |
| `codec` | str | `"pcm"` | Audio format (pcm/mp3) |
| `sample_rate` | int | `16000` | Audio sample rate in Hz |
| `volume` | float | `0.0` | Volume [-10, 10] |
| `speed` | float | `0.0` | Speech rate [-2, 6] |
| `enable_subtitle` | bool | `True` | Enable word-level timestamps |
| `emotion_category` | str | `None` | Emotion category |
| `emotion_intensity` | int | `None` | Emotion intensity [50, 200] |

## Documentation

- [Tencent Cloud ASR Documentation](https://cloud.tencent.com/document/product/1093/48982)
- [Tencent Cloud TTS Documentation](https://cloud.tencent.com/document/product/1073/108595)
- [LiveKit Agents Documentation](https://docs.livekit.io)

## License

Apache 2.0
