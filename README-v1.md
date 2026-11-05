# Qwen3 로컬 설치 가이드

> **생성일:** 2026-09-07  
> **최종 업데이트:** 2026-09-12  
> **대상 시스템:** Ubuntu 22.04 LTS | RTX 5090 24GB | 64GB RAM | 24 Cores

---

## 목차

| 섹션 | 내용 |
|------|------|
| [1. 시스템 환경 요약](#1-시스템-환경-요약) | 하드웨어/소프트웨어 확인 |
| [2. Qwen3란?](#2-qwen3란) | 모델 소개 |
| [3. Qwen3 전체 모델 라인업](#3-qwen3-전체-모델-라인업) | 0.6B~235B 전체 목록 |
| [4. Qwen3 공통 기능](#4-qwen3-공통-기능) | Think, 도구호출 등 |
| [5. 사전 점검: 기존 버전 확인 및 분기 처리](#5-사전-점검-기존-버전-확인-및-분기-처리) | **[추가]** 이전 버전 검증 및 스킵/진행 조건 |
| [6. 설치 방법 (4가지 경로)](#6-설치-방법-4가지-경로) | Ollama, vLLM, Transformers, llama.cpp |
| [7. 설치 방법 비교](#7-설치-방법-비교) | 4가지 방법 비교표 |
| [8. 추천 양자화 가이드](#8-추천-양자화-quantization-가이드) | BF16~Q4 선택 |
| [9. Think 모드](#9-think-모드-추론-모드-사용법) | 추론 모드 활용 |
| [10. 검증 및 테스트](#10-검증-및-테스트) | 동작 확인 |
| [11. 문제 해결](#11-문제-해결-트러블슈팅) | DNS, 404, 속도 문제 |
| [12. 유용한 명령어](#12-유용한-명령어-모음) | Ollama/vLLM/GPU |
| [13. 전체 모델 다운로드](#13-qwen3-전체-모델-다운로드) | 7개 모델 53GB |
| [14. 디렉토리 구조](#14-디렉토리-구조-권장) | 폴더 배치 |
| [15. 빠른 시작](#15-빠른-시작) | 3줄 요약 |

---

## 1. 시스템 환경 요약

| 항목 | 현재 상태 | 권장 사항 | 판정 |
|------|-----------|-----------|------|
| OS | Ubuntu 22.04.5 LTS | Ubuntu 22.04+ | ✅ |
| GPU | NVIDIA RTX 5090 24GB (CUDA 13.0) | 8GB+ VRAM | ✅ 여유 |
| RAM | 62GB | 16GB+ | ✅ 여유 |
| CPU | 24 cores | 4+ cores | ✅ 여유 |
| 디스크 | 2.5TB 사용 가능 | 20GB+ | ✅ 여유 |
| Python | 3.10.12 / 3.13.2 | 3.9+ | ✅ |
| NVIDIA Driver | 580.159.04 | 535+ | ✅ |

> **결론:** 하드웨어가 매우 여유롭습니다. RTX 5090 24GB에서는 BF16(전정밀도)으로도 실행 가능하며, 양자화 없이도 ~150-180 tok/s 예상됩니다.

---

## 2. Qwen3란?

Qwen3는 Alibaba Qwen 팀이 개발한 오픈소스 대규모 언어 모델 패밀리입니다.  
36조 개의 토큰으로 학습되었으며, 119개 언어를 지원합니다.

- **라이선스:** Apache 2.0 (상업적 사용 가능)
- **특징:** Think/No-Think 하이브리드 추론 모드 (모든 모델 공통)
- **컨텍스트:** 32K~128K 토큰 지원

---

## 3. Qwen3 전체 모델 라인업

### 3.1 Dense (밀집) 모델

| 모델 | 파라미터 수 | 컨텍스트 | Q4 VRAM | BF16 VRAM | Ollama 명령어 | 추천 용도 |
|------|-------------|----------|---------|-----------|---------------|-----------|
| **Qwen3-0.6B** | 0.6B | 32K | ~1GB | ~1.2GB | `ollama run qwen3:0.6b` | 엣지/IoT, 라즈베리파이 |
| **Qwen3-1.7B** | 1.7B | 32K | ~1.5GB | ~3.4GB | `ollama run qwen3:1.7b` | 모바일, 빠른 프로토타입 |
| **Qwen3-4B** | 4B | 128K | ~3GB | ~8GB | `ollama run qwen3:4b` | 소비자 GPU, 가벼운 에이전트 |
| **Qwen3-8B** | 8.2B | 128K | ~5-6GB | ~16GB | `ollama run qwen3:8b` | 개발 워크스테이션 (추천) |
| **Qwen3-14B** | 14B | 128K | ~10GB | ~28GB | `ollama run qwen3:14b` | 중급 서버, 고품질 추론 |
| **Qwen3-32B** | 32.8B | 128K | ~20GB | ~64GB | `ollama run qwen3:32b` | 고성능 서버, 크리에이티브 |

### 3.2 MoE (혼합 전문가) 모델

| 모델 | 총 파라미터 | 활성 파라미터 | 컨텍스트 | Q4 VRAM | Ollama 명령어 | 추천 용도 |
|------|-------------|---------------|----------|---------|---------------|-----------|
| **Qwen3-30B-A3B** | 30.5B | ~3.3B | 128K | ~20GB | `ollama run qwen3:30b-a3b` | 빠른 추론, 30B급 품질 |
| **Qwen3-235B-A22B** | 235B | ~22B | 128K | ~120GB+ | `ollama run qwen3:235b-a22b` | 오픈소스 플래그십 |

### 3.3 2507 업데이트 모델 (2025년 7월)

일정 크기에 대해 성능이 개선된 2507 버전이 출시되었습니다:

| 모델 | 변형 | 특징 |
|------|------|------|
| Qwen3-4B-Thinking-2507 | Think 모드 특화 | AIME25에서 81.3점 (Qwen2.5-72B 수준) |
| Qwen3-30B-A3B-2507 | MoE 개선版 | 더 정확한 추론 |
| Qwen3-235B-A22B-2507 | 플래그십 개선版 | 벤치마크 전체 상향 |

> **팁:** 2507 버전이 존재하는 모델은 반드시 2507 버전을 사용하세요.

### 3.4 하드웨어별 추천 모델

| GPU / 환경 | 추천 모델 | Q4 시 예상 속도 |
|------------|-----------|-----------------|
| **CPU only (16GB RAM)** | Qwen3-4B Q4 | 5-8 tok/s |
| **GTX 1660 / 6GB VRAM** | Qwen3-1.7B | 30-45 tok/s |
| **RTX 3060 12GB** | Qwen3-8B Q4 | 25-35 tok/s |
| **RTX 3090 / 4080 16GB+** | Qwen3-14B Q4 | 20-30 tok/s |
| **RTX 4090 / 5090 24GB** | Qwen3-32B Q4 또는 Qwen3-8B BF16 | 15-25 tok/s / 150+ tok/s |
| **A100 40GB** | Qwen3-30B-A3B BF16 | 40-60 tok/s |
| **4x A100 80GB / H100** | Qwen3-235B-A22B | 10-20 tok/s |

### 3.5 RTX 5090 24GB에서 실행 가능한 모델

| 모델 | 양자화 | VRAM 사용 | 예상 성능 | 추천도 |
|------|--------|-----------|-----------|--------|
| Qwen3-8B | BF16 (전정밀도) | ~16GB | ~150-180 tok/s | ⭐⭐⭐ **최고 추천** |
| Qwen3-8B | Q4_K_M | ~5-6GB | ~100-130 tok/s | ⭐⭐ |
| Qwen3-14B | BF16 | ~28GB | 메모리 초과 | ❌ |
| Qwen3-14B | Q4_K_M | ~10GB | ~50-70 tok/s | ⭐⭐⭐ **추천** |
| Qwen3-32B | Q4_K_M | ~20GB | ~25-35 tok/s | ⭐⭐ 가능 |
| Qwen3-30B-A3B | Q4_K_M | ~20GB | ~30-45 tok/s | ⭐⭐ 가능 |

> **RTX 5090 24GB에서는 Qwen3-8B를 BF16으로 실행하는 것이 최고의 선택입니다.**  
> 더 높은 품질이 필요하면 Qwen3-14B Q4를, 더 빠른 속도가 필요하면 Qwen3-4B BF16을 고려하세요.

### 3.6 모델별 벤치마크 비교

| 모델 | MMLU-Redux | MATH-500 | Think 모드 품질 |
|------|------------|----------|-----------------|
| Qwen3-4B | 83.7 | 97.0 | 양호 |
| Qwen3-8B | 84.9 | 97.4 | 우수 |
| Qwen3-14B | 86.7 | 97.4 | 매우 우수 |
| Qwen3-32B | 87.8 | 97.4 | 최고 |
| Qwen3-235B-A22B | - | - | 플래그십 (DeepSeek-R1 상회) |

---

## 4. Qwen3 공통 기능

모든 Qwen3 모델(0.6B~235B)에 공통으로 적용되는 기능:

| 기능 | 0.6B / 1.7B | 4B~32B Dense | 30B-A3B / 235B-A22B MoE |
|------|-------------|--------------|-------------------------|
| Think 모드 | ✅ | ✅ | ✅ |
| 도구 호출 (Tool Calling) | ✅ | ✅ | ✅ |
| 컨텍스트 윈도우 | 32K | 128K | 128K |
| 언어 지원 | 119개 | 119개 | 119개 |
| JSON/구조화된 출력 | ✅ | ✅ | ✅ |
| 라이선스 | Apache 2.0 | Apache 2.0 | Apache 2.0 |

---

## 5. 사전 점검: 기존 버전 확인 및 분기 처리

새로운 모델이나 실행 패키지를 설치하기 전에 **이전 버전이 이미 존재하거나 설치 진행 예정 버전과 동일한지 확인**하면 불필요한 재다운로드 및 충돌을 방지할 수 있습니다.

### 5.1 점검 흐름도

1. **기존 버전 확인:** 시스템 내 설치된 런타임(Ollama, vLLM, llama.cpp) 및 로컬 GGUF/HF 모델 파일 존재 유무 확인.
2. **버전 일치 확인:** 
   - **동일 버전 존재 시:** 추가 다운로드 없이 다음 과정(실행 및 서비스 시작)으로 바로 진입.
   - **이전/다른 버전 존재 시:** 기존 버전을 구동에 사용하거나, 필요시 삭제/재다운로드 수행 후 설치 진행.
   - **미설치 시:** 신규 설치 및 모델 다운로드 진행.

### 5.2 빠른 검증 스크립트 (Bash)

```bash
# 1) Ollama 모델 존재 여부 및 태그 확인
ollama list | grep "qwen3:8b" && echo "✅ Ollama에 동일 버전이 이미 존재합니다. 추가 설치 없이 실행 단계로 진행하세요."

# 2) 로컬 GGUF 파일 무결성 및 크기 확인 (Q4_K_M 약 4.68GB 기준)
GGUF_FILE="$HOME/Desktop/qwen3-8b-gguf/Qwen3-8B-Q4_K_M.gguf"
if [ -f "$GGUF_FILE" ]; then
    echo "✅ 기존 GGUF 모델 파일 존재: $GGUF_FILE"
    # 다운로드 재개 조건 (동일 파일이 완전한 경우 다운로드 건너뜀)
    aria2c -c --dry-run -d ~/Desktop/qwen3-8b-gguf -o "Qwen3-8B-Q4_K_M.gguf" \
      "[https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf](https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf)"
fi
```

6. 설치 방법 (4가지 경로)

방법 1: Ollama (가장 간단, 5분)

```Bash
# Step 1: Ollama 설치 상태 확인

if command -v ollama &> /dev/null; then
    echo "Ollama가 이미 설치되어 있습니다: $(ollama --version)"
else
    curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh
fi

# Step 2: 기존 모델 버전 검증
# 만약 다운로드하려는 버전(qwen3:8b)과 동일하다면 바로 실행 단계로 넘어갑니다.
if ollama list | grep -q "qwen3:8b"; then
    echo "[안내] 이미 지정된 버전(qwen3:8b)이 존재합니다. 다운로드를 건너뛰고 바로 대화를 시작합니다."
    ollama run qwen3:8b
else
    echo "[안내] 동일 버전이 존재하지 않습니다. 신규 다운로드 및 실행을 진행합니다."
    ollama run qwen3:8b
fi
```

Ollama 태그 옵션:

| 태그 | 크기 | 설명 | 
|:------:|:------:|:------:|
| qwen3:8b | ~5.2GB | 기본 Q4_K_M 양자화 (권장) | 
| qwen3:8b-q8_0 | ~8.5GB | Q8 양자화 (더 정확) | 
| qwen3:8b-fp16 | ~16GB | 전정밀도 (최고 품질) | 

API 서버로 실행:

```Bash
ollama serve

# 기본 포트: http://localhost:11434
curl http://localhost:11434/api/chat -d '{
  "model": "qwen3:8b",
  "messages": [{"role": "user", "content": "Hello!"}]
}'
```

방법 2: vLLM (프로덕션 서빙, OpenAI 호환 API)

```Bash
# 1) 가상환경 확인 및 생성

if [ -d "~/qwen3-env" ]; then
    echo "[안내] 기존 가상환경(~/qwen3-env)이 존재합니다. 기존 환경을 활성화합니다."
    source ~/qwen3-env/bin/activate
else
    python3.10 -m venv ~/qwen3-env
    source ~/qwen3-env/bin/activate
fi

# 2) PyTorch 및 vLLM 버전에 맞춰 설치/업데이트
pip install --upgrade "vllm>=0.9.0"

# 3) vLLM 서버 시작 (OpenAI 호환 API)
vllm serve Qwen/Qwen3-8B --host 0.0.0.0 --port 8000
```

방법 3: HuggingFace Transformers (개발용)

```Bash
# 1) 가상환경 및 패키지 점검
source ~/qwen3-env/bin/activate
pip install --upgrade transformers>=4.51.0 accelerate torch

# 2) Python 스크립트로 실행
```


```Python
# test_qwen3.py
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen3-8B"

# 토크나이저 및 모델 로드 (캐시된 모델이 존재하면 재다운로드 없이 해당 버전을 바로 사용)
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",        # GPU 자동 감지
    torch_dtype="auto",       # 자동 타입 선택
)

# 대화 템플릿 적용
messages = [
    {"role": "user", "content": "대한민국의 수도는 어디인가요?"}
]
inputs = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
).to(model.device)

# 텍스트 생성
outputs = model.generate(
    **inputs,
    max_new_tokens=256,
    temperature=0.7,
    top_p=0.9,
)
response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
print(response)
```

방법 4: llama.cpp (GGUF 양자화 모델)

```Bash
# 1) 기존 빌드 존재 여부 점검
cd ~/Desktop
if [ -d "llama.cpp" ]; then
    echo "[안내] 기존 llama.cpp 저장소가 존재합니다. 최신 코드로 업데이트합니다."
    cd llama.cpp && git pull
else
    git clone [https://github.com/ggerganov/llama.cpp.git](https://github.com/ggerganov/llama.cpp.git)
    cd llama.cpp
fi

# 2) 빌드 (CUDA 지원)
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j$(nproc)

# 3) 기존 다운로드 모델 파일 확인 후 진행
MODEL_PATH="$HOME/Desktop/qwen3-8b-gguf/Qwen3-8B-Q4_K_M.gguf"

if [ -f "$MODEL_PATH" ]; then
    echo "[안내] 동일한 GGUF 모델 파일이 이미 존재합니다. 다운로드를 건너뛰고 즉시 실행합니다."
else
    echo "[안내] 모델 파일이 없습니다. 다운로드를 진행합니다."
    mkdir -p ~/Desktop/qwen3-8b-gguf
    aria2c -x 16 -s 16 -k 1M -c \
      -d ~/Desktop/qwen3-8b-gguf \
      -o "Qwen3-8B-Q4_K_M.gguf" \
      "[https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf](https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf)"
fi

# 4) 실행
./build/bin/llama-cli -m "$MODEL_PATH" \
  -p "안녕하세요!" \
  -n 256 \
  -ngl 99 \
  --temp 0.7 \
  --top-p 0.9
```


6.1 빠른 다운로드 방법 (25Mbps 제한적 네트워크 환경)
다운로드전 이전 버전 및 이어받기 처리 (-c 옵션)

aria2c 사용 시 -c (continue) 옵션을 추가하면 기존에 일부 다운로드된 파일의 크기와 체크섬을 확인한 후 동일한 파일 버전이면 재다운로드를 자동으로 방지하거나 남아있는 부분부터 계속 진행합니다.

```Bash
# 동일 버전 존재 시 이어받기 및 무결성 확인 예시
aria2c -x 16 -s 16 -k 1M -c \
  -d ~/Desktop/qwen3-8b-gguf \
  -o "Qwen3-8B-Q4_K_M.gguf" \
  "[https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf](https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf)"
```

7. 설치 방법 비교

항목OllamavLLMTransformersllama.cpp설치 난이도⭐ 매우 쉬움⭐⭐ 보통⭐⭐ 보통⭐⭐⭐ 어려움시작 시간5분15분15분30분+API 서버✅ 내장✅ OpenAI 호환❌ 별도 구현✅ 내장양자화 선택태그로 선택자동자동자유도 높음GPU 활용도우수최적우수우수프로덕션적합최적개발용적합추천 대상초보자/개인서버/서비스연구/개발고급 사용자



8. 추천 양자화 (Quantization) 가이드
RTX 5090 24GB 기준:

양자화VRAM 사용속도품질추천BF16 (FP16)~16GB최고최고✅ 추천 (24GB이므로 여유)Q8_0~9GB빠름매우 높음좋음Q6_K~7GB빠름높음좋음Q4_K_M~5GB매우 빠름양호기본값Q4_K_S~5GB매우 빠름보통RAM 부족 시



10. Think 모드 (추론 모드) 사용법

Qwen3-8B는 추론(Chain-of-Thought) 모드를 지원합니다:

```
# Think 모드 활성화 (복잡한 수학, 코딩 문제용)
/think
1 + 1은 얼마인가요? 내 풀이 과정을 보여주세요.

# No-Think 모드 (빠른 일반 대화용)
/no_think
서울 날씨 알려줘.
```

10. 검증 및 테스트
10.1 기본 동작 확인

```Bash
# Ollama 설치 확인
ollama list

# vLLM 헬스 체크
curl http://localhost:8000/health

# GPU 사용량 확인
watch -n 1 nvidia-smi
```

11. 문제 해결 (트러블슈팅)
11.1 DNS 오류 (가장 흔한 문제)

```Bash
# 해결 방법: Google DNS 추가
sudo bash -c 'echo "nameserver 8.8.8.8" > /etc/resolv.conf'
13. 유용한 명령어 모음Bash# === Ollama ===
ollama list                    # 설치된 모델 목록
ollama show qwen3:8b           # 모델 정보
ollama rm qwen3:8b             # 모델 삭제
```

13. Qwen3 전체 모델 다운로드
13.1 중복 다운로드 예방을 적용한 다운로드 예시

```Bash
# 기존에 동일 파일 존재 시 자동으로 확인 후 다음 단계로 패스(-c 옵션 사용)
aria2c -x 16 -s 16 -k 1M -c \
  -d ~/Desktop/qwen3-all-models \
  "[https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q8_0.gguf](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q8_0.gguf)"
```

14. 디렉토리 구조 (권장)

```
/home/gotree94/Desktop/
├── README.md                          ← 이 파일
├── download_all_qwen3.sh              ← 전체 다운로드 스크립트
├── qwen3-env/                         ← Python 가상환경
├── llama.cpp/                         ← llama.cpp 소스
├── qwen3-8b-gguf/                     ← 개별 GGUF
├── qwen3-all-models/                  ← 전체 모델 GGUF
└── test_qwen3.py                      ← 테스트 스크립트
```

15. 빠른 시작

```Bash
# 설치 전 기존 모델 확인 후 바로 시작하는 자동 1줄 명령어
ollama list | grep -q "qwen3:8b" && ollama run qwen3:8b || (curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh && ollama run qwen3:8b)
```

---

### 주요 변경 사항 요약

1. **사전 점검 섹션 추가 (`5. 사전 점검: 기존 버전 확인 및 분기 처리`):**
   - 기존 모델 파일이나 런타임의 존재 유무 및 설치 버전 일치 여부를 검증하는 절차를 명시했습니다.
2. **설치 방법별 분기 처리 구문 도입:**
   - **Ollama:** `ollama list`로 동일 모델 태그 존재 확인 시 설치/다운로드를 건너뛰고 바로 `ollama run`으로 진입하도록 수정했습니다.
   - **llama.cpp / GGUF:** 파일 유무(`[ -f "$MODEL_PATH" ]`) 및 `aria2c -c` 옵션을 적용하여 동일 파일이 이미 존재하거나 완결된 상태면 재다운로드 없이 바로 구동하도록 변경했습니다.
   - **vLLM / Transformers:** 기존 Python 가상환경(`~/qwen3-env`) 존재 시 재활용 및 HuggingFace 캐시 재사용 로직을 안내에 반영했습니다.

<ElicitationsGroup message="설치 가이드 수정본과 관련하여 추가 조치가 필요하신 부분이 있으신가요?">
  <Elicitation label="Google Doc으로 생성" query="이 수정된 README.md 내용을 Google Doc 문서로 새로 생성해줘."/>
  <Elicitation label="Ollama 자동화 스크립트" query="이전 버전을 체크하고 업데이트 또는 실행을 자동으로 진행해주는 Bash 스크립트를 작성해줘."/>
</ElicitationsGroup>







