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
import dataclasses
import json
import os
import time
import uuid
import weakref
from dataclasses import dataclass
from typing import Any

import aiohttp

from livekit import rtc
from livekit.agents import (
    DEFAULT_API_CONNECT_OPTIONS,
    APIConnectionError,
    APIConnectOptions,
    APIStatusError,
    APITimeoutError,
    LanguageCode,
    stt,
    utils,
)
from livekit.agents.types import NOT_GIVEN, NotGivenOr
from livekit.agents.utils import AudioBuffer, is_given
from livekit.agents.voice.io import TimedString

from .auth import build_asr_url, generate_asr_signature
from .log import logger
from .models import TencentSTTModels


@dataclass
class STTOptions:
    model: TencentSTTModels | str
    language: LanguageCode | None
    sample_rate: int
    num_channels: int
    enable_intermediate_result: bool
    enable_word_info: bool
    enable_vad: bool
    filter_dirty: int
    filter_modal: int
    filter_punc: int
    convert_num_mode: int
    hotword_id: str | None
    hotword_list: str | None
    customization_id: str | None
    vad_silence_time: int | None
    max_speak_time: int | None
    need_sentence_end: bool
    endpoint_url: str


class STT(stt.STT):
    def __init__(
        self,
        *,
        appid: NotGivenOr[str | int] = NOT_GIVEN,
        secret_id: NotGivenOr[str] = NOT_GIVEN,
        secret_key: NotGivenOr[str] = NOT_GIVEN,
        model: TencentSTTModels | str = "16k_zh_en",
        language: str = "16k_zh_en",
        sample_rate: int = 16000,
        enable_intermediate_result: bool = True,
        enable_word_info: bool = True,
        enable_vad: bool = True,
        filter_dirty: int = 0,
        filter_modal: int = 0,
        filter_punc: int = 0,
        convert_num_mode: int = 1,
        hotword_id: NotGivenOr[str] = NOT_GIVEN,
        hotword_list: NotGivenOr[str] = NOT_GIVEN,
        customization_id: NotGivenOr[str] = NOT_GIVEN,
        vad_silence_time: NotGivenOr[int] = NOT_GIVEN,
        max_speak_time: NotGivenOr[int] = NOT_GIVEN,
        need_sentence_end: bool = True,
        http_session: aiohttp.ClientSession | None = None,
    ) -> None:
        """
        Create a new instance of Tencent Cloud STT.

        Args:
            appid: Tencent Cloud AppID. Reads from TENCENTCLOUD_APPID env var if not provided.
            secret_id: Tencent Cloud SecretID. Reads from TENCENTCLOUD_SECRET_ID env var if not provided.
            secret_key: Tencent Cloud SecretKey. Reads from TENCENTCLOUD_SECRET_KEY env var if not provided.
            model: Engine model type. Defaults to "16k_zh_en" (Chinese-English-Cantonese large model).
            language: Language/engine code. Defaults to "16k_zh_en".
            sample_rate: Audio sample rate in Hz. Defaults to 16000.
            enable_intermediate_result: Whether to return interim results. Defaults to True.
            enable_word_info: Whether to return word-level timestamps. Defaults to True.
            enable_vad: Whether to enable voice activity detection. Defaults to True.
            filter_dirty: Filter dirty words. 0: no, 1: yes, 2: replace with *. Defaults to 0.
            filter_modal: Filter modal words. 0: no, 1: partial, 2: strict. Defaults to 0.
            filter_punc: Filter ending period. 0: no, 1: yes. Defaults to 0.
            convert_num_mode: Number conversion. 0: no, 1: smart, 3: math. Defaults to 1.
            hotword_id: Hotword table ID.
            hotword_list: Temporary hotword list, e.g. "腾讯云|10,语音识别|5".
            customization_id: Custom model ID.
            vad_silence_time: VAD silence threshold in ms (500-2000).
            max_speak_time: Force sentence break time in ms (5000-90000).
            need_sentence_end: Whether to return sentence end markers. Defaults to True.
            http_session: Optional aiohttp ClientSession.
        """
        super().__init__(
            capabilities=stt.STTCapabilities(
                streaming=True,
                interim_results=enable_intermediate_result,
                aligned_transcript="word" if enable_word_info else False,
            )
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

        self._appid = str(tc_appid)
        self._secret_id = tc_secret_id
        self._secret_key = tc_secret_key

        self._opts = STTOptions(
            model=model,
            language=LanguageCode(language) if language else None,
            sample_rate=sample_rate,
            num_channels=1,
            enable_intermediate_result=enable_intermediate_result,
            enable_word_info=enable_word_info,
            enable_vad=enable_vad,
            filter_dirty=filter_dirty,
            filter_modal=filter_modal,
            filter_punc=filter_punc,
            convert_num_mode=convert_num_mode,
            hotword_id=hotword_id if is_given(hotword_id) else None,
            hotword_list=hotword_list if is_given(hotword_list) else None,
            customization_id=customization_id if is_given(customization_id) else None,
            vad_silence_time=vad_silence_time if is_given(vad_silence_time) else None,
            max_speak_time=max_speak_time if is_given(max_speak_time) else None,
            need_sentence_end=need_sentence_end,
            endpoint_url="wss://asr.cloud.tencent.com/asr/v2",
        )
        self._session = http_session
        self._streams = weakref.WeakSet[SpeechStream]()

    @property
    def model(self) -> str:
        return self._opts.model

    @property
    def provider(self) -> str:
        return "Tencent Cloud"

    def _ensure_session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = utils.http_context.http_session()
        return self._session

    def _build_sign_params(self) -> dict[str, str | int | bool]:
        """Build parameters for signature generation."""
        params: dict[str, str | int | bool] = {
            "engine_model_type": self._opts.model,
            "voice_format": 1,
            "needvad": 1 if self._opts.enable_vad else 0,
            "word_info": 1 if self._opts.enable_word_info else 0,
            "filter_dirty": self._opts.filter_dirty,
            "filter_modal": self._opts.filter_modal,
            "filter_punc": self._opts.filter_punc,
            "convert_num_mode": self._opts.convert_num_mode,
        }
        if self._opts.hotword_id:
            params["hotword_id"] = self._opts.hotword_id
        if self._opts.hotword_list:
            params["hotword_list"] = self._opts.hotword_list
        if self._opts.customization_id:
            params["customization_id"] = self._opts.customization_id
        if self._opts.vad_silence_time is not None:
            params["vad_silence_time"] = self._opts.vad_silence_time
        if self._opts.max_speak_time is not None:
            params["max_speak_time"] = self._opts.max_speak_time
        if not self._opts.need_sentence_end:
            params["filter_empty_result"] = 1
        return params

    def _build_url(self) -> str:
        """Build the complete WebSocket URL with signature."""
        timestamp = int(time.time())
        expired = timestamp + 24 * 3600
        nonce = int(time.time() * 1000) % 10000000000

        sign_params = self._build_sign_params()
        signature = generate_asr_signature(
            secret_key=self._secret_key,
            appid=self._appid,
            secret_id=self._secret_id,
            timestamp=timestamp,
            expired=expired,
            nonce=nonce,
            params=sign_params,
        )

        return build_asr_url(
            appid=self._appid,
            secret_id=self._secret_id,
            timestamp=timestamp,
            expired=expired,
            nonce=nonce,
            signature=signature,
            params=sign_params,
        )

    async def _recognize_impl(
        self,
        buffer: AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> stt.SpeechEvent:
        """Batch recognition: send entire audio via WebSocket and wait for result."""
        config = self._sanitize_options(language=language)
        frame = rtc.combine_audio_frames(buffer)

        voice_id = uuid.uuid4().hex
        url = self._build_url()

        try:
            ws = await asyncio.wait_for(
                self._ensure_session().ws_connect(url),
                timeout=conn_options.timeout,
            )
        except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as e:
            raise APIConnectionError("failed to connect to Tencent Cloud ASR") from e

        try:
            resp = await asyncio.wait_for(ws.receive_json(), timeout=10.0)
            if resp.get("code", -1) != 0:
                raise APIStatusError(
                    message=f"Tencent Cloud ASR handshake failed: {resp.get('message')}",
                    status_code=resp.get("code", -1),
                )

            chunk_size = int(config.sample_rate * 0.2 * 2)
            audio_data = frame.data.tobytes()
            for i in range(0, len(audio_data), chunk_size):
                await ws.send_bytes(audio_data[i : i + chunk_size])
                await asyncio.sleep(0.2)

            await ws.send_json({"type": "end"})

            final_text = ""
            confidence = 0.0
            words_list = []

            while True:
                msg = await asyncio.wait_for(ws.receive(), timeout=60.0)
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data.get("final") == 1:
                        break
                    result = data.get("result", {})
                    if result.get("voice_text_str"):
                        final_text = result["voice_text_str"]
                        if "word_list" in result and result["word_list"]:
                            words_list = result["word_list"]
                elif msg.type in (
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSING,
                ):
                    break

            lang = config.language or LanguageCode("cmn-Hans-CN")
            return stt.SpeechEvent(
                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                alternatives=[
                    stt.SpeechData(
                        language=lang,
                        text=final_text,
                        confidence=confidence,
                        words=[
                            TimedString(
                                text=w.get("word", ""),
                                start_time=w.get("start_time", 0) / 1000.0,
                                end_time=w.get("end_time", 0) / 1000.0,
                            )
                            for w in words_list
                        ] if words_list else None,
                    )
                ],
            )
        except asyncio.TimeoutError as e:
            raise APITimeoutError() from e
        except aiohttp.ClientResponseError as e:
            raise APIStatusError(message=e.message, status_code=e.status) from e
        except Exception as e:
            raise APIConnectionError() from e
        finally:
            await ws.close()

    def stream(
        self,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> SpeechStream:
        config = self._sanitize_options(language=language)
        stream = SpeechStream(
            stt=self,
            opts=config,
            conn_options=conn_options,
            appid=self._appid,
            secret_id=self._secret_id,
            secret_key=self._secret_key,
            http_session=self._ensure_session(),
        )
        self._streams.add(stream)
        return stream

    def update_options(
        self,
        *,
        model: NotGivenOr[TencentSTTModels | str] = NOT_GIVEN,
        language: NotGivenOr[str] = NOT_GIVEN,
        enable_intermediate_result: NotGivenOr[bool] = NOT_GIVEN,
        enable_word_info: NotGivenOr[bool] = NOT_GIVEN,
        enable_vad: NotGivenOr[bool] = NOT_GIVEN,
        hotword_list: NotGivenOr[str] = NOT_GIVEN,
    ) -> None:
        if is_given(model):
            self._opts.model = model
        if is_given(language):
            self._opts.language = LanguageCode(language)
        if is_given(enable_intermediate_result):
            self._opts.enable_intermediate_result = enable_intermediate_result
        if is_given(enable_word_info):
            self._opts.enable_word_info = enable_word_info
        if is_given(enable_vad):
            self._opts.enable_vad = enable_vad
        if is_given(hotword_list):
            self._opts.hotword_list = hotword_list

        for stream in self._streams:
            stream.update_options(
                model=model,
                language=language,
                enable_intermediate_result=enable_intermediate_result,
                enable_word_info=enable_word_info,
                enable_vad=enable_vad,
                hotword_list=hotword_list,
            )

    def _sanitize_options(self, *, language: NotGivenOr[str] = NOT_GIVEN) -> STTOptions:
        config = dataclasses.replace(self._opts)
        if is_given(language):
            config.language = LanguageCode(language)
        return config

    async def aclose(self) -> None:
        await super().aclose()


class SpeechStream(stt.SpeechStream):
    """Streaming speech recognition using Tencent Cloud WebSocket API."""

    def __init__(
        self,
        *,
        stt: STT,
        opts: STTOptions,
        conn_options: APIConnectOptions,
        appid: str,
        secret_id: str,
        secret_key: str,
        http_session: aiohttp.ClientSession,
    ) -> None:
        super().__init__(stt=stt, conn_options=conn_options, sample_rate=opts.sample_rate)
        self._opts = opts
        self._appid = appid
        self._secret_id = secret_id
        self._secret_key = secret_key
        self._session = http_session
        self._speaking = False
        self._request_id = ""
        self._reconnect_event = asyncio.Event()

    def update_options(
        self,
        *,
        model: NotGivenOr[TencentSTTModels | str] = NOT_GIVEN,
        language: NotGivenOr[str] = NOT_GIVEN,
        enable_intermediate_result: NotGivenOr[bool] = NOT_GIVEN,
        enable_word_info: NotGivenOr[bool] = NOT_GIVEN,
        enable_vad: NotGivenOr[bool] = NOT_GIVEN,
        hotword_list: NotGivenOr[str] = NOT_GIVEN,
    ) -> None:
        if is_given(model):
            self._opts.model = model
        if is_given(language):
            self._opts.language = LanguageCode(language)
        if is_given(enable_intermediate_result):
            self._opts.enable_intermediate_result = enable_intermediate_result
        if is_given(enable_word_info):
            self._opts.enable_word_info = enable_word_info
        if is_given(enable_vad):
            self._opts.enable_vad = enable_vad
        if is_given(hotword_list):
            self._opts.hotword_list = hotword_list
        self._reconnect_event.set()

    def _build_url(self) -> str:
        """Build the WebSocket URL with signature."""
        timestamp = int(time.time())
        expired = timestamp + 24 * 3600
        nonce = int(time.time() * 1000) % 10000000000

        params: dict[str, str | int | bool] = {
            "engine_model_type": self._opts.model,
            "voice_format": 1,
            "needvad": 1 if self._opts.enable_vad else 0,
            "word_info": 1 if self._opts.enable_word_info else 0,
            "filter_dirty": self._opts.filter_dirty,
            "filter_modal": self._opts.filter_modal,
            "filter_punc": self._opts.filter_punc,
            "convert_num_mode": self._opts.convert_num_mode,
        }
        if self._opts.hotword_id:
            params["hotword_id"] = self._opts.hotword_id
        if self._opts.hotword_list:
            params["hotword_list"] = self._opts.hotword_list
        if self._opts.customization_id:
            params["customization_id"] = self._opts.customization_id
        if self._opts.vad_silence_time is not None:
            params["vad_silence_time"] = self._opts.vad_silence_time
        if self._opts.max_speak_time is not None:
            params["max_speak_time"] = self._opts.max_speak_time

        signature = generate_asr_signature(
            secret_key=self._secret_key,
            appid=self._appid,
            secret_id=self._secret_id,
            timestamp=timestamp,
            expired=expired,
            nonce=nonce,
            params=params,
        )

        return build_asr_url(
            appid=self._appid,
            secret_id=self._secret_id,
            timestamp=timestamp,
            expired=expired,
            nonce=nonce,
            signature=signature,
            params=params,
        )

    async def _run(self) -> None:
        closing_ws = False

        @utils.log_exceptions(logger=logger)
        async def send_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            nonlocal closing_ws
            samples_200ms = self._opts.sample_rate // 5
            audio_bstream = utils.audio.AudioByteStream(
                sample_rate=self._opts.sample_rate,
                num_channels=1,
                samples_per_channel=samples_200ms,
            )

            async for data in self._input_ch:
                frames: list[rtc.AudioFrame] = []
                if isinstance(data, rtc.AudioFrame):
                    frames.extend(audio_bstream.write(data.data.tobytes()))
                elif isinstance(data, self._FlushSentinel):
                    frames.extend(audio_bstream.flush())

                for frame in frames:
                    await ws.send_bytes(frame.data.tobytes())
                    await asyncio.sleep(0.2)

            closing_ws = True
            await ws.send_json({"type": "end"})

        @utils.log_exceptions(logger=logger)
        async def recv_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            nonlocal closing_ws
            while True:
                msg = await ws.receive()
                if msg.type in (
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSING,
                ):
                    if closing_ws or self._session.closed:
                        return
                    raise APIStatusError(
                        message="Tencent Cloud ASR connection closed unexpectedly",
                        status_code=ws.close_code or -1,
                    )

                if msg.type != aiohttp.WSMsgType.TEXT:
                    logger.warning("unexpected Tencent Cloud ASR message type: %s", msg.type)
                    continue

                try:
                    self._process_event(json.loads(msg.data))
                except Exception:
                    logger.exception("failed to process Tencent Cloud ASR message")

        ws: aiohttp.ClientWebSocketResponse | None = None

        while True:
            try:
                url = self._build_url()
                ws = await asyncio.wait_for(
                    self._session.ws_connect(url),
                    self._conn_options.timeout,
                )

                resp = await asyncio.wait_for(ws.receive_json(), timeout=10.0)
                if resp.get("code", -1) != 0:
                    raise APIStatusError(
                        message=f"Tencent Cloud ASR handshake failed: {resp.get('message')}",
                        status_code=resp.get("code", -1),
                    )

                self._request_id = resp.get("voice_id", "")

                tasks = [
                    asyncio.create_task(send_task(ws)),
                    asyncio.create_task(recv_task(ws)),
                ]
                tasks_group = asyncio.gather(*tasks)
                wait_reconnect_task = asyncio.create_task(self._reconnect_event.wait())

                try:
                    done, _ = await asyncio.wait(
                        (tasks_group, wait_reconnect_task),
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    for task in done:
                        if task != wait_reconnect_task:
                            task.result()
                    if wait_reconnect_task not in done:
                        break
                    self._reconnect_event.clear()
                finally:
                    await utils.aio.gracefully_cancel(*tasks, wait_reconnect_task)
            finally:
                if ws is not None:
                    await ws.close()

    def _process_event(self, data: dict) -> None:
        code = data.get("code", -1)
        if code != 0:
            logger.error(f"Tencent Cloud ASR error: code={code}, message={data.get('message')}")
            return

        result = data.get("result", {})
        slice_type = result.get("slice_type", -1)
        voice_text = result.get("voice_text_str", "")
        word_list = result.get("word_list", [])

        if data.get("final") == 1:
            if self._speaking:
                self._speaking = False
                self._event_ch.send_nowait(stt.SpeechEvent(type=stt.SpeechEventType.END_OF_SPEECH))
            return

        lang = self._opts.language or LanguageCode("cmn-Hans-CN")

        if slice_type == 0:
            if not self._speaking:
                self._speaking = True
                self._event_ch.send_nowait(
                    stt.SpeechEvent(type=stt.SpeechEventType.START_OF_SPEECH)
                )

        elif slice_type == 1:
            if voice_text:
                if not self._speaking:
                    self._speaking = True
                    self._event_ch.send_nowait(
                        stt.SpeechEvent(type=stt.SpeechEventType.START_OF_SPEECH)
                    )
                self._event_ch.send_nowait(
                    stt.SpeechEvent(
                        type=stt.SpeechEventType.INTERIM_TRANSCRIPT,
                        alternatives=[
                            stt.SpeechData(
                                language=lang,
                                text=voice_text,
                            )
                        ],
                    )
                )

        elif slice_type == 2:
            if voice_text:
                words = None
                if word_list:
                    words = [
                        TimedString(
                            text=w.get("word", ""),
                            start_time=w.get("start_time", 0) / 1000.0,
                            end_time=w.get("end_time", 0) / 1000.0,
                        )
                        for w in word_list
                    ]
                self._event_ch.send_nowait(
                    stt.SpeechEvent(
                        type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                        alternatives=[
                            stt.SpeechData(
                                language=lang,
                                text=voice_text,
                                words=words,
                            )
                        ],
                    )
                )
            if self._speaking:
                self._speaking = False
                self._event_ch.send_nowait(
                    stt.SpeechEvent(type=stt.SpeechEventType.END_OF_SPEECH)
                )
