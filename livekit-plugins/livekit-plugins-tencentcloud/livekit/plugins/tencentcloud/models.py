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

from typing import Literal

# STT engine models
# See: https://cloud.tencent.com/document/product/1093/48982
TencentSTTModels = Literal[
    # Non-phone large models
    "16k_zh_en",           # Chinese-English-Cantonese + 9 dialects large model (recommended)
    "16k_zh_large",        # Mandarin-dialect-English large model
    "16k_multi_lang",      # Multi-language large model (15 languages)
    "16k_en_large",        # English large model
    # Non-phone standard models
    "16k_zh",              # Chinese general
    "16k_zh-TW",           # Chinese traditional
    "16k_zh_edu",          # Chinese education
    "16k_zh_medical",      # Chinese medical
    "16k_zh_court",        # Chinese court
    "16k_yue",             # Cantonese
    "16k_en",              # English general
    "16k_en_game",         # English game
    "16k_en_edu",          # English education
    "16k_ko",              # Korean
    "16k_ja",              # Japanese
    "16k_th",              # Thai
    "16k_id",              # Indonesian
    "16k_vi",              # Vietnamese
    "16k_ms",              # Malay
    "16k_fil",             # Filipino
    "16k_pt",              # Portuguese
    "16k_tr",              # Turkish
    "16k_ar",              # Arabic
    "16k_es",              # Spanish
    "16k_hi",              # Hindi
    "16k_fr",              # French
    "16k_de",              # German
    # Phone models
    "8k_zh",               # Chinese phone general
    "8k_en",               # English phone general
    "8k_zh_large",         # Chinese phone large model (supports 27 dialects)
]

# TTS voice types
# See: https://cloud.tencent.com/document/product/1073/92668
TencentTTSVoices = Literal[
    # Premium voices (精品音色)
    "101001",  # 智晓白 (Zhixiaobai) - Male, general
    "101002",  # 智晓夏 (Zhixiaxia) - Female, general
    "101003",  # 智晓秋 (Zhixiaoqiu) - Female, general
    "101004",  # 智晓冬 (Zhixiaodong) - Male, general
    "101005",  # 智晓萌 (Zhixiaomeng) - Female, customer service
    "101006",  # 智晓帅 (Zhixiaoshuai) - Male, customer service
    # Large model voices (大模型音色)
    "1001001",  # 智晓颜 (Zhixiaoyan) - Female, emotional
    "1001002",  # 智晓美 (Zhixiaomei) - Female, emotional
    "1001003",  # 智晓智 (Zhixiaozhi) - Male, emotional
    "1001004",  # 智晓慧 (Zhixiaohui) - Female, emotional
    "1001005",  # 智晓达 (Zhixiaoda) - Male, emotional
    "1001006",  # 智晓柔 (Zhixiaorou) - Female, emotional
    "1001007",  # 智晓刚 (Zhixiaogang) - Male, emotional
    "1001008",  # 智晓甜 (Zhixiaotian) - Female, emotional
    "1001009",  # 智晓酷 (Zhixiaoku) - Male, emotional
    "1001010",  # 智晓丽 (Zhixiaoli) - Female, emotional
    # Super-natural large model voices (超自然大模型音色)
    "1005001",  # 智晓云 (Zhixiaoyun) - Female
    "1005002",  # 智晓风 (Zhixiaofeng) - Male
    "1005003",  # 智晓雨 (Zhixiaoyu) - Female
    "1005004",  # 智晓雷 (Zhixiaolei) - Male
    "1005005",  # 智晓雪 (Zhixiaoxue) - Female
    "1005006",  # 智晓电 (Zhixiaodian) - Male
    "1005007",  # 智晓光 (Zhixiaoguang) - Female
    "1005008",  # 智晓影 (Zhixiaoying) - Male
    "1005009",  # 智晓音 (Zhixiaoyin) - Female
    "1005010",  # 智晓乐 (Zhixiaole) - Male
    # Voice clone (一句话复刻)
    "200000000",  # Voice clone fixed value
]

# TTS emotion categories
TencentTTSEmotions = Literal[
    "neutral",     # Neutral
    "sad",         # Sad
    "happy",       # Happy
    "angry",       # Angry
    "fear",        # Fear
    "news",        # News
    "story",       # Story
    "radio",       # Radio
    "poetry",      # Poetry
    "call",        # Customer service
    "sajiao",      # Coquettish
    "disgusted",   # Disgusted
    "amaze",       # Amazed
    "peaceful",    # Peaceful
    "exciting",    # Exciting
    "aojiao",      # Tsundere
    "jieshuo",     # Commentary
]

# TTS audio codecs
TencentTTSCodecs = Literal[
    "pcm",   # PCM 16-bit
    "mp3",   # MP3
]
