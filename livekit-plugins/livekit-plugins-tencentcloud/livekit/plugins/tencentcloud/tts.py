# Copyright 2025 LiveKit, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
import weakref
from collections import deque
from dataclasses import dataclass, replace
from typing import Any, cast

import aiohttp

from livekit.agents import (
    APIConnectionError,
    APIConnectOptions,
    APIError,
    APIStatusError,
    APITimeoutError,
    tokenize,
    tts,
    utils,
)
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, NOT_GIVEN, NotGivenOr
from livekit.agents.utils import is_given
from livekit.agents.voice.io import TimedString

from .auth import build_tts_url, generate_tts_signature
from .log import logger
from .models import TencentTTSCodecs, TencentTTSEmotions, TencentTTSVoices


@dataclass
class _TTSOptions:
    voice: str
    codec: TencentTTSCodecs
    sample_rate: int
    volume: float
    speed: float
    enable_subtitle: bool
    emotion_category: str | None
    emotion_intensity: int | None
    segment_rate: int | None
    secret_id: str
    secret_key: str
    appid: int


class TTS(tts.TTS):
    def __init__(
        self,
        *,
        appid: NotGivenOr[int] = NOT_GIVEN,
        secret_id: NotGivenOr[str] = NOT_GIVEN,
        secret_key: NotGivenOr[str] = NOT_GIVEN,
        voice: TencentTTSVoices | str = "101001",
        codec: TencentTTSCodecs = "pcm",
        sample_rate: int = 16000,
        volume: float = 0.0,
        speed: float = 0.0,
        enable_subtitle: bool = True,
        emotion_category: NotGivenOr[TencentTTSEmotions | str] = NOT_GIVEN,
        emotion_intensity: NotGivenOr[int] = NOT_GIVEN,
        segment_rate: NotGivenOr[int] = NOT_GIVEN,
        http_session: aiohttp.ClientSession | None = None,
        tokenizer: NotGivenOr[tokenize.SentenceTokenizer] = NOT_GIVEN,
        text_pacing: tts.SentenceStreamPacer | bool = False,
    ) -> None:
        """
        Create a new instance of Tencent Cloud TTS.

        Args:
            appid: Tencent Cloud AppID. Reads from TENCENTCLOUD_APPID env var if not provided.
            secret_id: Tencent Cloud SecretID. Reads from TENCENTCLOUD_SECRET_ID env var if not provided.
            secret_key: Tencent Cloud SecretKey. Reads from TENCENTCLOUD_SECRET_KEY env var if not provided.
            voice: Voice ID. Defaults to "101001" (智晓白).
            codec: Audio encoding format. "pcm" or "mp3". Defaults to "pcm".
            sample_rate: Audio sample rate in Hz. Defaults to 16000.
            volume: Volume [-10, 10]. Defaults to 0.
            speed: Speech rate [-2, 6]. 0=1.0x, 1=1.2x, 2=1.5x, 6=2.5x. Defaults to 0.
            enable_subtitle: Enable word-level timestamps. Defaults to True.
            emotion_category: Emotion category (only for multi-emotion voices).
            emotion_intensity: Emotion intensity [50, 200]. Default 100.
            segment_rate: Sentence break sensitivity [0, 1, 2]. Default 0.
            http_session: Optional aiohttp ClientSession.
            tokenizer: Sentence tokenizer for streaming.
            text_pacing: Stream pacer for TTS.
        """
        super().__init__(
            capabilities=tts.TTSCapabilities(
                streaming=True,
                aligned_transcript=enable_subtitle,
            ),
            sample_rate=sample_rate,
            num_channels=1,
        )

        tc_appid = appid if is_given(appid) else os.environ.get("TENCENTCLOUD_APPID")
        tc_secret_id = secret_id if is_given(secret_id) else os.environ.get("TENCENTCLOUD_SECRET_ID")
        tc_secret_key = secret_key if is_given(secret_key) else os.environ.get("TENCENTCLOUD_SECRET_KEY")

        if not tc_appid:
            raise ValueError(
                "Tencent Cloud AppID is required, either as argument or set "
                "TENCENTCLOUD_APPID environment variable"
            )
        if not tc_secret_id:
            raise ValueError(
                "Tencent Cloud SecretID is required, either as argument or set "
                "TENCENTCLOUD_SECRET_ID environment variable"
            )
        if not tc_secret_key:
            raise ValueError(
                "Tencent Cloud SecretKey is required, either as argument or set "
                "TENCENTCLOUD_SECRET_KEY environment variable"
            )

        if not -10 <= volume <= 10:
            logger.warning("volume must be between -10 and 10, got %s", volume)
        if not -2 <= speed <= 6:
            logger.warning("speed must be between -2 and 6, got %s", speed)

        self._opts = _TTSOptions(
            voice=voice,
            codec=codec,
            sample_rate=sample_rate,
            volume=volume,
            speed=speed,
            enable_subtitle=enable_subtitle,
            emotion_category=emotion_category if is_given(emotion_category) else None,
            emotion_intensity=emotion_intensity if is_given(emotion_intensity) else None,
            segment_rate=segment_rate if is_given(segment_rate) else None,
            secret_id=tc_secret_id,
            secret_key=tc_secret_key,
            appid=int(tc_appid),
        )
        self._session = http_session
        self._streams = weakref.WeakSet[SynthesizeStream]()
        self._pool = utils.ConnectionPool[aiohttp.ClientWebSocketResponse](
            connect_cb=self._connect_ws,
            close_cb=self._close_ws,
            max_session_duration=300,
            mark_refreshed_on_get=True,
        )
        self._sentence_tokenizer = (
            tokenizer if is_given(tokenizer) else tokenize.blingfire.SentenceTokenizer()
        )
        self._stream_pacer: tts.SentenceStreamPacer | None = None
        if text_pacing is True:
            self._stream_pacer = tts.SentenceStreamPacer()
        elif isinstance(text_pacing, tts.SentenceStreamPacer):
            self._stream_pacer = text_pacing

    @property
    def model(self) -> str:
        return self._opts.voice

    @property
    def provider(self) -> str:
        return "Tencent Cloud"

    def _ensure_session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = utils.http_context.http_session()
        return self._session

    def _build_sign_params(self, session_id: str) -> dict[str, str | int | bool]:
        """Build parameters for TTS signature generation."""
        params: dict[str, str | int | bool] = {
            "Action": "TextToStreamAudioWSv2",
            "AppId": self._opts.appid,
            "SessionId": session_id,
            "VoiceType": self._opts.voice,
            "Codec": self._opts.codec,
            "SampleRate": self._opts.sample_rate,
            "Volume": self._opts.volume,
            "Speed": self._opts.speed,
            "EnableSubtitle": self._opts.enable_subtitle,
        }
        if self._opts.emotion_category:
            params["EmotionCategory"] = self._opts.emotion_category
        if self._opts.emotion_intensity is not None:
            params["EmotionIntensity"] = self._opts.emotion_intensity
        if self._opts.segment_rate is not None:
            params["SegmentRate"] = self._opts.segment_rate
        return params

    def _build_url(self, session_id: str) -> str:
        """Build the complete TTS WebSocket URL with signature."""
        timestamp = int(time.time())
        expired = timestamp + 24 * 3600

        sign_params = self._build_sign_params(session_id)
        signature = generate_tts_signature(
            secret_key=self._opts.secret_key,
            secret_id=self._opts.secret_id,
            timestamp=timestamp,
            expired=expired,
            params=sign_params,
        )

        return build_tts_url(
            secret_id=self._opts.secret_id,
            timestamp=timestamp,
            expired=expired,
            signature=signature,
            params=sign_params,
        )

    async def _connect_ws(self, timeout: float) -> aiohttp.ClientWebSocketResponse:
        session_id = uuid.uuid4().hex
        url = self._build_url(session_id)
        session = self._ensure_session()
        ws = await asyncio.wait_for(session.ws_connect(url), timeout)
        logger.debug("Established new Tencent Cloud TTS WebSocket connection")
        return ws

    async def _close_ws(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        await ws.close()

    def prewarm(self) -> None:
        self._pool.prewarm()

    def update_options(
        self,
        *,
        voice: NotGivenOr[TencentTTSVoices | str] = NOT_GIVEN,
        codec: NotGivenOr[TencentTTSCodecs] = NOT_GIVEN,
        sample_rate: NotGivenOr[int] = NOT_GIVEN,
        volume: NotGivenOr[float] = NOT_GIVEN,
        speed: NotGivenOr[float] = NOT_GIVEN,
        enable_subtitle: NotGivenOr[bool] = NOT_GIVEN,
        emotion_category: NotGivenOr[TencentTTSEmotions | str | None] = NOT_GIVEN,
        emotion_intensity: NotGivenOr[int | None] = NOT_GIVEN,
        segment_rate: NotGivenOr[int | None] = NOT_GIVEN,
    ) -> None:
        """
        Update the Text-to-Speech (TTS) configuration options.

        This method allows updating the TTS settings, including voice, codec, volume, speed,
        and emotion. If any parameter is not provided, the existing value will be retained.
        """
        if is_given(voice):
            self._opts.voice = voice
        if is_given(codec):
            self._opts.codec = codec
        if is_given(sample_rate):
            self._opts.sample_rate = sample_rate
        if is_given(volume):
            self._opts.volume = cast(float, volume)
        if is_given(speed):
            self._opts.speed = cast(float, speed)
        if is_given(enable_subtitle):
            self._opts.enable_subtitle = enable_subtitle
        if is_given(emotion_category):
            self._opts.emotion_category = emotion_category
        if is_given(emotion_intensity):
            self._opts.emotion_intensity = emotion_intensity
        if is_given(segment_rate):
            self._opts.segment_rate = segment_rate

        for stream in self._streams:
            stream.update_options(
                voice=voice,
                codec=codec,
                sample_rate=sample_rate,
                volume=volume,
                speed=speed,
                enable_subtitle=enable_subtitle,
                emotion_category=emotion_category,
                emotion_intensity=emotion_intensity,
                segment_rate=segment_rate,
            )

    def synthesize(
        self, text: str, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS
    ) -> ChunkedStream:
        return ChunkedStream(tts=self, input_text=text, conn_options=conn_options)

    def stream(
        self, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS
    ) -> SynthesizeStream:
        stream = SynthesizeStream(tts=self, conn_options=conn_options)
        self._streams.add(stream)
        return stream

    async def aclose(self) -> None:
        for stream in list(self._streams):
            await stream.aclose()
        self._streams.clear()
        await self._pool.aclose()


class ChunkedStream(tts.ChunkedStream):
    """Synthesize text using streaming WebSocket (non-streaming chunked wrapper)."""

    def __init__(self, *, tts: TTS, input_text: str, conn_options: APIConnectOptions) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._tts: TTS = tts

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        session_id = uuid.uuid4().hex
        request_id = utils.shortuuid()
        output_emitter.initialize(
            request_id=request_id,
            sample_rate=self._tts._opts.sample_rate,
            num_channels=1,
            mime_type=f"audio/{self._tts._opts.codec}",
        )

        url = self._tts._build_url(session_id)

        try:
            ws = await asyncio.wait_for(
                self._tts._ensure_session().ws_connect(url),
                timeout=self._conn_options.timeout,
            )
        except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as e:
            raise APIConnectionError("failed to connect to Tencent Cloud TTS") from e

        try:
            resp = await asyncio.wait_for(ws.receive_json(), timeout=10.0)
            if resp.get("code", -1) != 0:
                raise APIError(f"Tencent Cloud TTS handshake failed: {resp.get('message')}")

            ready_msg = await asyncio.wait_for(ws.receive(), timeout=10.0)
            if ready_msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(ready_msg.data)
                if data.get("ready") != 1:
                    raise APIError(f"Expected READY event, got: {data}")

            synthesis_cmd = {
                "session_id": session_id,
                "message_id": uuid.uuid4().hex,
                "action": "ACTION_SYNTHESIS",
                "data": self._input_text,
            }
            await ws.send_json(synthesis_cmd)

            complete_cmd = {
                "session_id": session_id,
                "message_id": uuid.uuid4().hex,
                "action": "ACTION_COMPLETE",
                "data": "",
            }
            await ws.send_json(complete_cmd)

            while True:
                msg = await asyncio.wait_for(ws.receive(), timeout=60.0)
                if msg.type == aiohttp.WSMsgType.BINARY:
                    output_emitter.push(msg.data)
                elif msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data.get("code", -1) != 0:
                        raise APIError(f"Tencent Cloud TTS error: {data.get('message')}")
                    if data.get("final") == 1:
                        break
                    subtitles = data.get("result", {}).get("subtitles")
                    if subtitles:
                        for sub in subtitles:
                            text_val = sub.get("Text", "")
                            if text_val:
                                output_emitter.push_timed_transcript(
                                    TimedString(
                                        text=text_val,
                                        start_time=sub.get("BeginTime", 0) / 1000.0,
                                        end_time=sub.get("EndTime", 0) / 1000.0,
                                    )
                                )
                elif msg.type in (
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSING,
                ):
                    break

            output_emitter.flush()
        except asyncio.TimeoutError as e:
            raise APITimeoutError() from e
        except aiohttp.ClientResponseError as e:
            raise APIStatusError(message=e.message, status_code=e.status) from e
        except Exception as e:
            raise APIConnectionError() from e
        finally:
            await ws.close()


class SynthesizeStream(tts.SynthesizeStream):
    """Streaming text-to-speech using Tencent Cloud WebSocket API."""

    def __init__(self, *, tts: TTS, conn_options: APIConnectOptions):
        super().__init__(tts=tts, conn_options=conn_options)
        self._tts: TTS = tts
        self._opts = replace(tts._opts)
        self._reconnect_event = asyncio.Event()

    def update_options(
        self,
        *,
        voice: NotGivenOr[TencentTTSVoices | str] = NOT_GIVEN,
        codec: NotGivenOr[TencentTTSCodecs] = NOT_GIVEN,
        sample_rate: NotGivenOr[int] = NOT_GIVEN,
        volume: NotGivenOr[float] = NOT_GIVEN,
        speed: NotGivenOr[float] = NOT_GIVEN,
        enable_subtitle: NotGivenOr[bool] = NOT_GIVEN,
        emotion_category: NotGivenOr[TencentTTSEmotions | str | None] = NOT_GIVEN,
        emotion_intensity: NotGivenOr[int | None] = NOT_GIVEN,
        segment_rate: NotGivenOr[int | None] = NOT_GIVEN,
    ) -> None:
        if is_given(voice):
            self._opts.voice = voice
        if is_given(codec):
            self._opts.codec = codec
        if is_given(sample_rate):
            self._opts.sample_rate = sample_rate
        if is_given(volume):
            self._opts.volume = cast(float, volume)
        if is_given(speed):
            self._opts.speed = cast(float, speed)
        if is_given(enable_subtitle):
            self._opts.enable_subtitle = enable_subtitle
        if is_given(emotion_category):
            self._opts.emotion_category = emotion_category
        if is_given(emotion_intensity):
            self._opts.emotion_intensity = emotion_intensity
        if is_given(segment_rate):
            self._opts.segment_rate = segment_rate
        self._reconnect_event.set()

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        request_id = utils.shortuuid()
        session_id = uuid.uuid4().hex
        output_emitter.initialize(
            request_id=request_id,
            sample_rate=self._opts.sample_rate,
            num_channels=1,
            mime_type=f"audio/{self._opts.codec}",
            stream=True,
        )

        input_sent_event = asyncio.Event()
        sent_tokens = deque[str]()

        sent_tokenizer_stream = self._tts._sentence_tokenizer.stream()
        flush_on_chunk = isinstance(self._tts._sentence_tokenizer, tokenize.SentenceTokenizer)
        if self._tts._stream_pacer:
            sent_tokenizer_stream = self._tts._stream_pacer.wrap(
                sent_stream=sent_tokenizer_stream,
                audio_emitter=output_emitter,
            )

        async def _sentence_stream_task(
            ws: aiohttp.ClientWebSocketResponse, tc_session_id: str
        ) -> None:
            async for ev in sent_tokenizer_stream:
                synthesis_cmd = {
                    "session_id": tc_session_id,
                    "message_id": uuid.uuid4().hex,
                    "action": "ACTION_SYNTHESIS",
                    "data": ev.token,
                }
                sent_tokens.append(ev.token)
                self._mark_started()
                await ws.send_json(synthesis_cmd)
                input_sent_event.set()

            # Send final empty synthesis to signal end
            end_cmd = {
                "session_id": tc_session_id,
                "message_id": uuid.uuid4().hex,
                "action": "ACTION_SYNTHESIS",
                "data": "",
            }
            await ws.send_json(end_cmd)
            input_sent_event.set()

        async def _input_task() -> None:
            async for data in self._input_ch:
                if isinstance(data, self._FlushSentinel):
                    sent_tokenizer_stream.flush()
                    continue
                sent_tokenizer_stream.push_text(data)
            sent_tokenizer_stream.end_input()

        async def _recv_task(
            ws: aiohttp.ClientWebSocketResponse, tc_session_id: str
        ) -> None:
            await input_sent_event.wait()
            while True:
                msg = await ws.receive(timeout=self._conn_options.timeout)
                if msg.type in (
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSING,
                ):
                    if self._tts._session.closed:
                        return
                    raise APIStatusError(
                        message="Tencent Cloud TTS connection closed unexpectedly",
                        status_code=ws.close_code or -1,
                    )

                if msg.type == aiohttp.WSMsgType.BINARY:
                    output_emitter.push(msg.data)
                elif msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data.get("code", -1) != 0:
                        raise APIError(f"Tencent Cloud TTS error: {data.get('message')}")
                    if data.get("final") == 1:
                        if sent_tokenizer_stream.closed:
                            output_emitter.end_input()
                            return
                        continue
                    if data.get("heartbeat") == 1:
                        continue
                    subtitles = data.get("result", {}).get("subtitles")
                    if subtitles:
                        for sub in subtitles:
                            text_val = sub.get("Text", "")
                            if text_val:
                                output_emitter.push_timed_transcript(
                                    TimedString(
                                        text=text_val,
                                        start_time=sub.get("BeginTime", 0) / 1000.0,
                                        end_time=sub.get("EndTime", 0) / 1000.0,
                                    )
                                )

        while True:
            try:
                async with self._tts._pool.connection(timeout=self._conn_options.timeout) as ws:
                    self._acquire_time = self._tts._pool.last_acquire_time
                    self._connection_reused = self._tts._pool.last_connection_reused

                    resp = await asyncio.wait_for(ws.receive_json(), timeout=10.0)
                    if resp.get("code", -1) != 0:
                        raise APIError(
                            f"Tencent Cloud TTS handshake failed: {resp.get('message')}"
                        )

                    ready_msg = await asyncio.wait_for(ws.receive(), timeout=10.0)
                    if ready_msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(ready_msg.data)
                        if data.get("ready") != 1:
                            raise APIError(f"Expected READY event, got: {data}")

                    output_emitter.start_segment(segment_id=session_id)

                    tasks = [
                        asyncio.create_task(_input_task()),
                        asyncio.create_task(_sentence_stream_task(ws, session_id)),
                        asyncio.create_task(_recv_task(ws, session_id)),
                    ]

                    try:
                        await asyncio.gather(*tasks)
                    finally:
                        input_sent_event.set()
                        await sent_tokenizer_stream.aclose()
                        await utils.aio.gracefully_cancel(*tasks)
                    break
            except asyncio.TimeoutError:
                raise APITimeoutError() from None
            except Exception as e:
                logger.exception("Tencent Cloud TTS connection error")
                raise APIConnectionError() from e
