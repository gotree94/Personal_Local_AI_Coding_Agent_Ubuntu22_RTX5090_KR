# Personal Local AI Coding Agent
## Ubuntu 22.04 + RTX 5090 Laptop GPU 24GB 구축 및 사용 가이드

- 목표: OpenCode 없이 독립적으로 실행되는 개인용 로컬 AI 코딩 에이전트
- 하드웨어: Intel Core Ultra 9 275HX (24 threads) / RAM 64GB / RTX 5090 Laptop GPU 24GB / Ubuntu 22.04 LTS
- 주요 업무: C, Verilog, VHDL, SystemVerilog, 기술 문서 번역, Git 프로젝트 관리
- 기본 아키텍처: **Ollama + Hermes Agent** (권장)
- 대안: **Roo Code / Cline / Aider + Ollama**
- 문서 기준일: 2026-11-06 (현재 PC 실측 기준)

> 중요: Ollama는 LLM 추론 서버이고, 파일 읽기·수정·터미널 명령은 에이전트(Hermes, Roo Code 등)가 수행한다.
> 따라서 로컬 파일 접근 권한은 모델이 아니라 에이전트 프로세스의 Linux 사용자 권한과 도구 승인 정책으로 결정된다.

> Ollama + Hermes 조합은 필수가 아니다. 핵심은 **모델 서버(Ollama)와 에이전트(Hermes/Roo Code/Cline/Aider)를 분리**하는 것이다.
> 그러면 에이전트를 바꿔도 모델을 다시 받을 필요가 없고, 모델을 바꿔도 에이전트 설정만 수정하면 된다.

---

# 0. 현재 설치 상태 (2026-11-06 실측)

이 문서는 아래 실측 상태를 기준으로 한다. **새로 다운로드하지 않고도 바로 에이전트를 사용할 수 있는 상태**다.

| 항목 | 실측값 |
|---|---|
| OS | Ubuntu 22.04.5 LTS, kernel 6.8 |
| CPU | Intel Core Ultra 9 275HX, 24 threads |
| RAM | 62Gi (64GB) |
| GPU | NVIDIA RTX 5090 Laptop GPU, 24463 MiB, driver 580.159.04 |
| Ollama | 0.33.3, systemd `ollama` 서비스 active |
| Ollama 컨텍스트 env | `OLLAMA_CONTEXT_LENGTH=64000` |
| Hermes Agent | v0.22.4 (2026.9.24), `~/.hermes/config.yaml` 존재 |
| Hermes 현재 설정 | model `qwen2.5-coder-64k`, provider `custom`, base_url `http://127.0.0.1:11434/v1` |

설치된 모델:

| 모델 | 크기 | 모델 네이티브 컨텍스트 | 도구 호출 | 권장 역할 |
|---|---:|---:|---|---|
| `qwen2.5-coder:7b` | 4.7GB | 32K | 지원 | 코드 기준선 |
| `qwen2.5-coder-local:latest` | 4.7GB | 32K (`num_ctx 16384`) | 지원 | 짧은 코드 작업 |
| `qwen2.5-coder-64k:latest` | 4.7GB | 32K (`num_ctx 64000` 설정) | 지원 | 코드 작업, 단 실제 실행은 32K |
| `deepseek-r1:8b` | 5.2GB | 128K | 지원 (thinking) | 추론, 긴 문맥 |
| `llama3.1:8b` | 4.9GB | 128K | 지원 | 긴 문맥 에이전트 |
| `exaone3.5:7.8b` | 4.8GB | 32K | **미지원** | 한국어 번역/문서 전용 |

실측으로 확인된 주의사항:

- `qwen2.5-coder-64k`는 이름과 Modelfile의 `num_ctx 64000`에도 불구하고 **Ollama 0.33.3에서 실제로는 32768 컨텍스트로 실행된다.** Ollama 로그에 `requested context size too large for model num_ctx=64000 n_ctx_train=32768` 경고가 남고, `ollama ps`의 CONTEXT도 32768로 표시된다. 즉 "이름만 64K"인 상태다.
- 64K가 실제로 필요한 Hermes 작업에는 `llama3.1:8b` 또는 `deepseek-r1:8b`를 사용한다. 둘 다 네이티브 128K다. 실측에서 `llama3.1:8b`를 `num_ctx 65536`으로 실행하면 `ollama ps`에 CONTEXT=65536, VRAM 약 13GB로 표시됐다.
- `exaone3.5:7.8b`는 capabilities에 `completion`만 있고 tool calling이 없어 Hermes/Roo/Cline의 에이전트 모델로는 부적합하다. 번역/요약용으로만 사용한다.
- `deepseek-r1:8b`는 현재 설치본 기준 architecture `qwen3`, 128K 컨텍스트, `tools`와 `thinking`을 지원한다. 다만 thinking 때문에 응답이 느릴 수 있다.
- Hermes v0.22.4는 32K 모델로도 응답했지만, 공식 요구사항은 최소 64K이므로 긴 다단계 작업에서는 32K 모델이 불안정할 수 있다.

---

# 1. 완성 목표와 구성

## 1.1 최종 기능

| 요구사항 | 구현 구성 |
|---|---|
| OpenCode 없이 독립 실행 | Hermes Agent CLI / 선택적으로 Roo Code |
| 외부 API 토큰 비용 0원 | Ollama 로컬 모델만 연결 |
| 오프라인 추론 | 모델 다운로드와 패키지 설치 후 네트워크 차단 상태에서도 추론 |
| 로컬 파일 읽기/생성/수정 | Hermes 파일 도구 또는 IDE 에이전트의 workspace 도구 |
| C 개발 | GCC, Clang, CMake, Make |
| Verilog/SystemVerilog | Icarus Verilog, Verilator |
| VHDL | GHDL |
| 논리 합성 | Yosys |
| 파형 확인 | GTKWave |
| Git | Git CLI |
| 번역 및 문서화 | 별도 번역 프롬프트 + 로컬 범용 모델 |
| 웹 UI | Roo Code/Cline은 VS Code 내부 UI, Hermes는 CLI 및 지원 UI 구성 선택 |

## 1.2 권장 아키텍처

```text
┌───────────────────────────────────────────────────────┐
│                 사용자 / 개발자                       │
└──────────────────────────┬────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
       Hermes Agent CLI          VS Code (선택)
       로컬 에이전트              Roo Code / Cline
              │                         │
              └────────────┬────────────┘
                           │ OpenAI-compatible API
                           │ localhost only
                    ┌──────▼──────┐
                    │   Ollama   │
                    │ 11434/tcp  │
                    └──────┬──────┘
                           │
                ┌──────────▼──────────┐
                │  Local LLM models   │
                │ Qwen Coder / GLM    │
                └──────────┬──────────┘
                           │
             ┌─────────────▼────────────────┐
             │ Local project workspace     │
             │ C / RTL / docs / Git        │
             └─────────────┬────────────────┘
                           │
        ┌──────────────────┼────────────────────┐
        │                  │                    │
    GCC/Clang         HDL toolchain          Git
    C/C++             Icarus/Verilator       diff/commit
                      GHDL/Yosys/GTKWave
```

**추천 운영 방식**

1. 1차 구현은 Hermes Agent를 메인 에이전트로 설치한다.
2. 로컬 추론은 Hermes Local Models가 현재 Linux 환경에서 지원되면 먼저 시험하고, 그렇지 않거나 여러 앱에서 모델을 공유하려면 Ollama를 연결한다.
3. CLI에서 파일 생성·수정·테스트·Git 작업이 제대로 되는지 검증한다.
4. GUI가 중요하면 같은 로컬 모델 서버를 Roo Code 또는 Cline에 연결한다.
5. 모델과 에이전트를 분리해 두면 추후 에이전트를 교체해도 모델 설치를 반복할 필요가 없다.

---

# 2. 하드웨어 및 용량 계획

## 2.1 GPU 메모리

RTX 5090 Laptop GPU의 VRAM은 24GB다. 30B급 MoE 모델의 Q4 양자화 파일이 약 19GB라고 해도, 실행 시 KV cache, 런타임 버퍼, CUDA 컨텍스트가 추가로 필요하다. 따라서 모델 파일 크기만 보고 24GB에 여유 있게 들어간다고 판단하면 안 된다.

권장 시작값:

- 일반 Ollama 단독 테스트: 16K~32K부터 시작 가능
- **Hermes Agent 연결 시: 최소 64K 컨텍스트가 필요**하므로 64K를 기준으로 메모리 적합성을 확인
- 동시 실행 모델: 1개
- 동시 요청: 1개부터 시작
- GPU 메모리 부족 시: 더 작은 모델/양자화 또는 CPU 오프로딩을 검토
- 64GB 시스템 RAM: 일부 CPU 오프로딩에 도움은 되지만 속도가 느려질 수 있음
- **중요:** 컨텍스트를 64K로 늘리려면 모델 자체의 네이티브 컨텍스트가 64K 이상이어야 한다. Ollama 0.33.3은 네이티브보다 큰 `num_ctx`를 받으면 `requested context size too large for model` 경고를 남기고 네이티브 값으로 클램프한다. `qwen2.5-coder` 계열은 네이티브가 32K라서 64K로 늘릴 수 없다.

중요한 현실적 제약: Qwen3-Coder 30B Q4 파일은 약 19GB다. 여기에 64K 컨텍스트의 KV cache와 런타임 메모리가 더해지므로 RTX 5090 Laptop 24GB에서 항상 전부 GPU에 상주한다고 보장할 수 없다. Hermes가 요구하는 64K를 맞춘 상태에서 실제 `ollama ps`와 `nvidia-smi`로 GPU/CPU 분할을 확인해야 한다. 메모리 부족이나 과도한 CPU 오프로딩이 발생하면 14B급 모델 또는 더 작은 양자화를 우선 사용한다.

## 2.2 지금 사용할 모델 (이미 설치됨)

현재 네트워크가 좋지 않으므로 **추가 다운로드 없이 설치된 모델로 에이전트를 먼저 완성**한다. 아래는 이 PC에서 실제 확인한 값이다.

| 역할 | 모델 | 실제 컨텍스트 | 도구 호출 | 운용 |
|---|---|---:|---|---|
| 코드/에이전트 기본 | `qwen2.5-coder-64k:latest` | 32K (64K 이름이지만 클램프됨) | 지원 | 코드 품질 우선, 짧은~중간 작업 |
| 긴 문맥 에이전트 | `llama3.1:8b` | 128K (64K 실행 확인) | 지원 | Hermes 메인 권장 |
| 추론/설계 검토 | `deepseek-r1:8b` | 128K | 지원 (thinking) | 복잡한 원인 분석 |
| 한국어 번역/문서 | `exaone3.5:7.8b` | 32K | **미지원** | Hermes가 아닌 일반 채팅/번역 전용 |
| 빠른 코드 보조 | `qwen2.5-coder-local:latest` | 16K | 지원 | 짧은 코드 생성 |

권장 조합:

1. **Hermes 메인 모델은 `llama3.1:8b`**로 시작한다. 실제 64K가 보장되고 VRAM도 약 13GB로 24GB에 여유가 있다.
2. 코드 품질이 더 중요한 짧은 작업은 `qwen2.5-coder-64k`를 쓴다. 단, 실제 컨텍스트는 32K라는 점을 감안한다.
3. 번역/문서 작업은 `exaone3.5:7.8b`를 별도 채팅으로 사용한다. 도구 호출이 없으므로 에이전트로 쓰지 않는다.
4. 모델을 동시에 여러 개 올리지 않는다. 24GB GPU에서는 하나씩 전환한다.

## 2.3 나중에 설치할 고성능 모델 (네트워크 회복 후)

모델 태그와 양자화는 시점에 따라 바뀐다. 설치 전에 Ollama Library에서 정확한 태그, 크기, 컨텍스트, 도구 호출 지원을 확인한다. 아래는 2026-11 기준 24GB VRAM을 고려한 후보이다.

| 모델 | 파일 크기 | 네이티브 컨텍스트 | 24GB + 64K 적합성 | 특징 |
|---|---:|---:|---|---|
| `qwen3.5:9b` | 6.6~7.6GB | 256K | **여유 있음** | 최신 범용, vision/tools/thinking, 가장 안전한 업그레이드 |
| `qwen3-coder:30b` | 19GB | 256K | 64K 시 일부 CPU 오프로딩 가능 | 에이전트 코딩 특화, 코드 품질 최우선 |
| `glm-4.7-flash` | 19GB | 198K | 64K 시 일부 CPU 오프로딩 가능 | 30B-A3B MoE, SWE-bench 강점 |
| `qwen3.5:27b` | 17~20GB | 256K | 64K 시 빠듯/오프로딩 | 고품질 범용 |
| `qwen3.5:35b` | 22GB | 256K | 64K 전체 GPU 적재 어려움 | 권장하지 않음 |

선택 기준:

- **품질과 안정성의 균형:** `qwen3.5:9b` (24GB에서 64K를 넉넉히 확보)
- **코딩 에이전트 최우선:** `qwen3-coder:30b` (속도보다 품질, 일부 CPU 오프로딩 감수)
- **대안 코딩/추론:** `glm-4.7-flash`
- 30B급 MoE는 파일이 19GB이고 64K KV cache가 추가되어 24GB를 넘을 수 있다. 이때는 `ollama ps`의 PROCESSOR가 `100% GPU`인지 확인하고, CPU 오프로딩이 크면 `qwen3.5:9b`로 낮춘다.

모든 모델을 동시에 메모리에 올리지 않는다. 24GB GPU에서는 모델 하나씩 전환하는 운영을 권장한다.

모델 선정 시 확인할 항목:
- OpenAI 호환 API 또는 Ollama 네이티브 연동 여부
- Tool calling / function calling 지원
- 긴 코드 문맥에서의 정확성
- 한글 번역 품질
- C 및 HDL 컴파일 테스트 통과율
- 실제 VRAM 점유량과 tokens/s

> 모델 이름에 'Coder'가 붙어 있어도 Verilog/VHDL 문법과 시뮬레이터 오류를 정확히 처리한다는 보장은 없다. 반드시 이 문서의 HDL 평가 프로젝트로 비교한다.

---

# 3. 기존 시스템 백업 및 사전 점검

기존 Ollama/Hermes를 바로 삭제하거나 재설치하지 않는다.

```bash
mkdir -p ~/local-ai-backup
cp -a ~/.hermes ~/local-ai-backup/hermes-$(date +%Y%m%d) 2>/dev/null || true
cp -a ~/.config/opencode ~/local-ai-backup/opencode-$(date +%Y%m%d) 2>/dev/null || true

ollama --version
ollama list
ollama show qwen2.5-coder-64k
ollama ps
nvidia-smi
hermes --version
hermes doctor
```

현재 Hermes 설정 확인:

```bash
grep -nE '^(model|providers|local_runtime):|^  (default|provider|base_url|context_length|ollama_num_ctx):' ~/.hermes/config.yaml
```

GPU 드라이버 확인:

```bash
nvidia-smi
```

CUDA Toolkit 전체 설치가 반드시 필요한 것은 아니다. Ollama가 지원하는 NVIDIA 드라이버가 정상 동작하는지 먼저 확인한다. CUDA 개발/컴파일을 별도로 할 때만 Toolkit을 추가한다.

권장 여유 공간:
- 모델 파일용 100GB 이상
- 프로젝트 및 데이터셋 공간 별도 확보
- 모델 다운로드 중에는 수십 GB 추가 공간이 필요할 수 있음

---

# 4. Ollama 설치 및 설정

## 4.1 설치

공식 설치 안내를 확인한 뒤 설치한다.

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

서비스 상태:

```bash
systemctl status ollama
ollama --version
```

서비스가 자동으로 시작되지 않으면:

```bash
sudo systemctl enable --now ollama
```

Ollama API 확인:

```bash
curl http://127.0.0.1:11434/api/tags
```

정상 응답이면 JSON 형식으로 설치된 모델 목록이 표시된다.

## 4.2 API를 로컬에서만 사용

외부 네트워크에 Ollama API를 공개하지 않는 것이 기본 원칙이다. 기본 주소인 `127.0.0.1:11434`를 유지한다.

환경 변수 확인:

```bash
systemctl show ollama --property=Environment
```

기본 설치에서는 별도의 `OLLAMA_HOST` 변경을 하지 않는다. `0.0.0.0`으로 바꾸지 않는다.

## 4.3 지금 사용할 모델 확인 (다운로드 없이)

현재 네트워크가 좋지 않으므로 새 모델을 받지 말고 **이미 설치된 모델**을 사용한다.

```bash
ollama list
ollama show qwen2.5-coder-64k
ollama show llama3.1:8b
ollama show deepseek-r1:8b
```

확인 포인트:

- `ollama show`의 `context length`는 모델의 **네이티브 컨텍스트**다.
- `Parameters`의 `num_ctx`는 Modelfile 기본값이다.
- **실제 실행 컨텍스트는 `ollama ps`의 CONTEXT 열로 확인한다.** 요청한 `num_ctx`가 네이티브보다 크면 Ollama가 클램프한다.

간단한 추론 테스트(모델 하나만 로드):

```bash
ollama run llama3.1:8b
```

프롬프트:

```text
Write a portable C function that calculates the parity of a uint32_t.
Explain the algorithm briefly and provide a small test program.
```

다른 터미널에서 GPU 사용량 확인:

```bash
watch -n 1 nvidia-smi
ollama ps
```

정상 예시 (실측):

```text
NAME           SIZE    PROCESSOR    CONTEXT
llama3.1:8b    13 GB   100% GPU     65536
```

### 대표 예시: 설치된 `qwen2.5-coder-64k`로 바로 시작

현재 Hermes 설정도 이 모델을 가리키고 있으므로 추가 설치 없이 바로 쓸 수 있다.

```bash
ollama run qwen2.5-coder-64k
```

```text
현재 디렉토리의 C 프로젝트 구조를 읽기 전용으로 분석해줘.
파일을 수정하지 말고 빌드 방법과 테스트 방법만 정리해줘.
```

단, 이 모델의 실제 컨텍스트는 32K다. 64K가 필요한 긴 작업은 아래 `llama3.1:8b` 예시로 바꾼다.

## 4.4 컨텍스트 설정 (실측 기준)

Ollama는 기본 컨텍스트가 낮고(VRAM에 따라 4K/32K), Hermes Agent는 공식적으로 최소 64,000 tokens를 요구한다. 서버 기본값을 올리는 방법과 모델별로 고정하는 방법이 있다.

### 방법 A: Ollama 서비스 전체 기본값

```bash
sudo systemctl edit ollama.service
```

```ini
[Service]
Environment="OLLAMA_CONTEXT_LENGTH=64000"
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
systemctl show ollama --property=Environment
```

이 PC에는 이미 `OLLAMA_CONTEXT_LENGTH=64000`이 설정되어 있다.

### 방법 B: 모델별 Modelfile

```text
FROM llama3.1:8b
PARAMETER num_ctx 65536
```

```bash
ollama create llama3.1-64k -f Modelfile
ollama run llama3.1-64k
```

> **중요:** `qwen2.5-coder:7b` 계열은 네이티브가 32K이므로 Modelfile에 `num_ctx 65536`을 넣어도 실제 실행은 32768로 클램프된다. 실측 로그:
> `requested context size too large for model num_ctx=64000 n_ctx_train=32768`.
> 따라서 진짜 64K가 필요하면 `llama3.1:8b` 또는 `deepseek-r1:8b`(둘 다 네이티브 128K)를 사용한다.

### Hermes 설정 맞추기

Hermes가 자동 감지한 값이 모델의 네이티브 값(예: 32768)이면, 64K 모델에서는 아래처럼 명시한다.

```yaml
model:
  default: "llama3.1:8b"
  provider: "custom"
  base_url: "http://127.0.0.1:11434/v1"
  ollama_num_ctx: 65536
  context_length: 65536
```

- `ollama_num_ctx`: Hermes가 Ollama에 매 요청마다 보내는 `num_ctx`
- `context_length`: Hermes가 대화 압축을 결정할 때 쓰는 전체 컨텍스트

설정 후 실제 실행 컨텍스트 확인:

```bash
hermes -z "Reply with exactly: READY"
ollama ps
```

CONTEXT가 65536으로 표시되어야 한다. 32768로 표시되면 모델 네이티브 컨텍스트가 부족한 것이므로 64K 이상 모델로 바꾼다.

## 4.5 나중에 고성능 모델 설치 (네트워크 회복 후)

지금은 설치된 모델로 작업하고, 네트워크가 회복되면 아래 순서로 업그레이드한다. **한 번에 하나씩** 설치하고, 각 단계마다 `ollama ps`와 `nvidia-smi`로 VRAM을 확인한다.

### 1) 후보 선택

- 안정적인 균형: `qwen3.5:9b` (약 7GB, 256K, tools/vision/thinking)
- 코딩 에이전트 최우선: `qwen3-coder:30b` (약 19GB, 256K, tools)
- 대안: `glm-4.7-flash` (약 19GB, 198K, tools/thinking)

### 2) 다운로드

```bash
ollama pull qwen3.5:9b
ollama show qwen3.5:9b
```

30B급을 선택한 경우:

```bash
ollama pull qwen3-coder:30b
ollama show qwen3-coder:30b
```

> 네트워크가 불안정하면 중간에 끊겨도 `ollama pull`을 다시 실행하면 이어받는다. 디스크 여유 공간은 모델 크기의 2배 이상을 확보한다.

### 3) 64K 모델 생성

```bash
printf 'FROM qwen3.5:9b\nPARAMETER num_ctx 65536\n' > Modelfile.qwen35
ollama create qwen3.5-9b-64k -f Modelfile.qwen35
ollama run qwen3.5-9b-64k
```

```bash
printf 'FROM qwen3-coder:30b\nPARAMETER num_ctx 65536\n' > Modelfile.qwen3coder
ollama create qwen3-coder-64k -f Modelfile.qwen3coder
ollama run qwen3-coder-64k
```

> 256K 네이티브 모델이므로 `num_ctx 65536`이 정상적으로 적용된다. `ollama ps`의 CONTEXT가 65536인지 확인한다.

### 4) 메모리 적합성 확인

```bash
watch -n 1 nvidia-smi
ollama ps
```

- `PROCESSOR`가 `100% GPU`이면 쾌적하다.
- `100% GPU`가 아니거나 CPU 비중이 크면 64K 컨텍스트의 KV cache가 VRAM을 초과한 것이다. 다음 순서로 조정한다.
  1. `num_ctx`를 32768로 낮춘다.
  2. 더 작은 모델(`qwen3.5:9b`)로 내린다.
  3. 다른 GPU 프로세스를 종료한다.
  4. KV cache 양자화(`OLLAMA_KV_CACHE_TYPE=q8_0`)를 지원하는 버전이면 적용을 검토한다.

### 5) Hermes 모델 전환

대화형으로 전환:

```bash
hermes model
```

또는 `~/.hermes/config.yaml` 수정:

```yaml
model:
  default: "qwen3.5-9b-64k"
  provider: "custom"
  base_url: "http://127.0.0.1:11434/v1"
  ollama_num_ctx: 65536
  context_length: 65536
```

이전 모델은 삭제하지 말고 남겨 둔다. 새 모델이 느리거나 품질이 낮으면 `hermes model`로 즉시 되돌린다.

---

# 5. Hermes Agent 설치 및 Ollama 연결

## 5.1 설치 전 주의

Hermes는 범용 에이전트이며 파일·터미널 도구를 사용할 수 있다. 다만 도구 이름, 설정 파일 형식, provider 설정 절차는 릴리스마다 달라질 수 있다. 반드시 현재 공식 설치 가이드와 `hermes --help`를 기준으로 진행한다.

**중요한 최신 요구사항:** Hermes Agent Quickstart는 로컬 모델을 포함해 최소 64,000 tokens 컨텍스트를 요구한다고 안내한다. 따라서 앞서 모델 단독 테스트에서 사용한 16K/32K 설정을 그대로 Hermes에 연결하면 긴 작업에서 불안정할 수 있다. Hermes용 Ollama 모델은 실제 유효 컨텍스트를 64K 이상으로 설정하고, Hermes에도 같은 값을 지정한다.

이 PC에는 Hermes Agent v0.22.4가 이미 설치되어 있으므로 새로 설치하지 않아도 된다. 가장 간단한 시험 경로는 Ollama 0.33.3의 통합 런처다.

```bash
ollama launch hermes --model llama3.1:8b
```

실행 후 다른 터미널에서 `ollama ps`로 CONTEXT가 65536인지 확인한다. 런처가 기대한 컨텍스트를 잡지 못하면 아래 5.2의 `~/.hermes/config.yaml`을 직접 설정한다.

## 5.1.1 대안: Hermes 자체 Local Models 런타임

최근 Hermes에는 Ollama를 별도로 설치하지 않고도 로컬 모델을 실행하는 관리형 Local Models 기능이 제공된다. Hermes가 하드웨어에 맞는 llama.cpp 런타임을 설치·관리하고, 모델 다운로드 및 실행을 담당한다.

- Hermes Desktop: Settings → Providers → Local Models에서 런타임 설치 → 모델 선택/다운로드 → Use
- CLI: `hermes model`에서 Local models 항목을 확인
- Linux x64 NVIDIA: 공식 문서상 CUDA backend 지원 조건을 확인한다. 문서에는 CUDA 13 드라이버 요구사항이 안내되어 있다.
- 장점: 엔진, 모델, GPU 메모리 구성을 Hermes가 관리하므로 Ollama endpoint를 수동 연결하는 단계가 줄어든다.
- 주의: 현재 설치한 Hermes 릴리스와 Linux 환경에서 해당 기능이 제공되는지 먼저 확인한다. Desktop UI가 없는 CLI 설치에서는 Ollama/custom endpoint 방식이 더 명확할 수 있다.

**선택 기준**
- 가장 단순하게 Hermes 안에서 로컬 모델을 관리하고 싶으면 Hermes Local Models를 먼저 시험한다.
- 기존 Ollama를 계속 사용하거나 모델 서버를 여러 앱에서 공유하려면 Ollama + custom endpoint를 사용한다.
- 두 런타임을 동시에 같은 모델로 실행할 필요는 없다. 하나를 선택해 먼저 검증한다.

기존 설치가 있다면 우선 상태를 확인한다.

```bash
hermes --version
hermes doctor
hermes --help
```

설치되지 않은 경우 공식 Hermes Agent 설치 문서의 최신 명령을 사용한다. 기존 `~/.hermes` 설정이 있으면 백업한 후 설치/업데이트한다.

## 5.2 Ollama 연결 원칙

Hermes 공식 Quickstart의 최소 컨텍스트 요구사항은 64K다. Ollama Modelfile에서 `PARAMETER num_ctx 65536`을 설정하고, Hermes의 모델 설정에서도 context length를 65536으로 맞춘다. 모델의 최대 지원 컨텍스트가 256K라고 표시되어 있어도 서버의 실제 실행 컨텍스트가 자동으로 256K가 되는 것은 아니다.

Hermes 설정에서 다음 연결 정보를 사용한다.

- Provider: `custom` (Ollama는 OpenAI-compatible custom endpoint로 연결)
- Base URL: `http://127.0.0.1:11434/v1`
- Model: 실제 `ollama list`에 표시되는 모델 식별자
- API key: 비워 두거나 `ollama`를 placeholder로 사용한다. Ollama는 키를 요구하지 않는다.
- Context length: 모델의 네이티브 컨텍스트가 64K 이상일 때만 65536으로 설정한다.

현재 설정과 동일한 예시 (`~/.hermes/config.yaml`):

```yaml
model:
  default: "llama3.1:8b"
  provider: "custom"
  base_url: "http://127.0.0.1:11434/v1"
  ollama_num_ctx: 65536
  context_length: 65536
```

- `qwen2.5-coder`처럼 네이티브가 32K인 모델에 `ollama_num_ctx: 65536`을 줘도 Ollama가 32768로 클램프한다. 이 경우 `hermes doctor`는 통과해도 실제 컨텍스트는 32K다.
- 실제 실행 컨텍스트는 항상 `ollama ps`의 CONTEXT 열로 확인한다.

### 대표 예시: `llama3.1:8b`로 실제 64K Hermes 구성

```bash
# 1) 모델 단독 확인
ollama run llama3.1:8b

# 2) Hermes 모델 선택 (Custom endpoint)
hermes model
#   Base URL : http://127.0.0.1:11434/v1
#   API key  : 비움 또는 ollama
#   Model    : llama3.1:8b
#   Context  : 65536

# 3) 실제 실행 컨텍스트 확인
cd ~/AI-Workspace/02_FPGA/Verilog
hermes -z "Reply with exactly: READY"
ollama ps
```

`ollama ps`에 `CONTEXT 65536`이 보이면 정상이다.

설정은 대화형 설정 마법사를 우선 사용한다.

```bash
hermes model
```

또는 현재 릴리스에서 제공하는 설정 명령을 확인한다.

```bash
hermes --help
hermes config --help
```

모델 선택 후 provider endpoint를 확인한다. Hermes가 모델 목록을 가져오지 못하면 다음을 순서대로 확인한다.

```bash
curl http://127.0.0.1:11434/v1/models
ollama list
ollama ps
```

문제가 지속되면:
- 모델 ID가 `ollama list`와 정확히 일치하는지 확인
- Base URL 끝의 `/v1` 필요 여부 확인
- Hermes의 OpenAI-compatible provider 설정 예시 확인
- 모델이 Tool Calling을 지원하는지 확인
- Ollama 로그와 Hermes doctor 결과 확인

## 5.3 파일 접근과 작업 디렉토리

에이전트를 실행하기 전에 작업 디렉토리로 이동한다.

```bash
cd ~/AI-Workspace/02_FPGA/Verilog
hermes
```

에이전트에게 첫 작업으로 다음을 요청한다.

```text
현재 디렉토리의 파일과 하위 디렉토리를 읽기 전용으로 분석해줘.
아직 어떤 파일도 수정하지 마.
프로젝트 구조, 주요 소스 파일, 빌드 방법, 테스트 방법을 정리해줘.
```

그 다음 작은 테스트 디렉토리에서 파일 생성/수정 기능을 검증한다.

```text
현재 테스트 디렉토리에 hello.c와 Makefile을 생성해줘.
컴파일하고 실행한 뒤 결과를 설명해줘.
기존 파일을 덮어쓰기 전에는 반드시 확인해줘.
```

**중요:** 에이전트가 실행하는 명령은 현재 Linux 사용자 권한을 가진다. `sudo` 권한을 무심코 부여하지 말고, 작업 디렉토리를 분리하며, 파괴적 명령은 승인하도록 설정한다.

## 5.4 Hermes 도구 권한 권장

초기에는 아래 정책으로 시작한다.

| 기능 | 권장 |
|---|---|
| 작업 디렉토리 파일 읽기 | 허용 |
| 파일 생성 | 허용 또는 승인 |
| 기존 파일 수정/삭제 | 승인 |
| 터미널 명령 | 승인 |
| Git diff/status | 허용 |
| Git commit/push | 승인 |
| sudo | 금지 |
| 홈 전체 및 시스템 디렉토리 | 제한 |
| 네트워크 접근 | 기본 제한 |

Hermes의 실제 도구별 승인 설정은 현재 릴리스의 설정 스키마를 확인하고 적용한다. 존재하지 않는 설정 키를 임의로 추가하지 않는다.

---

# 6. VS Code GUI 대안: Roo Code 또는 Cline

Hermes CLI가 목표에 맞더라도, IDE 안에서 코드 편집과 에이전트 작업을 한 화면에서 하고 싶다면 Roo Code 또는 Cline을 별도로 설치할 수 있다.

이들은 OpenCode 자체에 종속되지 않는다. Ollama를 공통 로컬 추론 서버로 사용한다.

## 6.1 VS Code 설치

Ubuntu에서 이미 VS Code를 사용한다면 생략한다. 공식 Microsoft 설치 방법을 사용한다.

```bash
code --version
```

## 6.2 Roo Code

- VS Code 확장 마켓플레이스에서 `Roo Code` 설치
- Provider를 Ollama 또는 OpenAI-compatible로 설정
- Base URL: `http://127.0.0.1:11434`
- 모델: Ollama에 설치한 실제 모델명
- Tool calling을 지원하는 모델 사용
- Workspace trust 및 파일/터미널 승인 정책 확인

공식 문서에서 현재 provider 설정 UI와 Ollama 연결 절차를 확인한다.

## 6.3 Cline

- VS Code 확장 마켓플레이스에서 `Cline` 설치
- API Provider에서 Ollama를 선택하거나 OpenAI-compatible provider를 설정
- Base URL과 모델명을 Ollama 설정에 맞춘다.
- 모델 컨텍스트와 tool-use 지원 여부를 확인한다.
- 파일 편집과 터미널 실행 요청은 승인 기반으로 시작한다.

## 6.4 무엇을 메인으로 쓸 것인가?

| 상황 | 권장 |
|---|---|
| 터미널 중심 자율 작업 | Hermes Agent |
| IDE에서 코드와 diff를 보며 작업 | Roo Code |
| IDE에서 단계별 승인 중심 작업 | Cline |
| Git 변경을 작게 나눠 관리 | Aider(선택) |

초기에는 Hermes와 Roo Code를 동시에 복잡하게 구성하지 않는다. 먼저 Hermes의 파일/터미널 기능을 검증하고, GUI가 필요할 때 Roo Code를 추가한다.

---

# 7. 개발 도구 설치

## 7.1 C/C++

```bash
sudo apt update
sudo apt install -y \
  build-essential gcc g++ clang lldb gdb \
  cmake ninja-build make pkg-config \
  git git-lfs
```

확인:

```bash
gcc --version
clang --version
cmake --version
gdb --version
git --version
```

## 7.2 Verilog 및 SystemVerilog

```bash
sudo apt install -y iverilog verilator gtkwave
```

확인:

```bash
iverilog -V
verilator --version
gtkwave --version
```

간단한 Verilog 테스트:

```verilog
// hello.v
module hello;
  initial begin
    $display("HELLO_VERILOG");
    $finish;
  end
endmodule
```

```bash
iverilog -g2012 -o hello_sim hello.v
vvp hello_sim
```

SystemVerilog 테스트에서는 `iverilog -g2012`를 사용하되, 고급 SystemVerilog 기능은 Verilator 또는 상용 시뮬레이터에서 별도 검증한다.

## 7.3 VHDL

Ubuntu 저장소 버전이 필요한 기능을 지원하는지 확인한다.

```bash
sudo apt install -y ghdl
ghdl --version
```

간단한 VHDL 테스트:

```vhdl
-- hello.vhd
entity hello is
end entity;

architecture sim of hello is
begin
  process
  begin
    report "HELLO_VHDL";
    wait;
  end process;
end architecture;
```

```bash
ghdl -a --std=08 hello.vhd
ghdl -e --std=08 hello
ghdl -r --std=08 hello
```

## 7.4 Yosys

```bash
sudo apt install -y yosys
yosys -V
```

Ubuntu 22.04 저장소의 Yosys 버전은 최신 버전보다 낮을 수 있다. 필요한 FPGA/ASIC flow 기능이 없다면 공식 설치 문서 또는 별도 최신 빌드 방식을 검토한다.

---

# 8. 표준 작업 디렉토리 구성

```bash
mkdir -p ~/AI-Workspace/{01_C,02_FPGA,03_SoC,04_Translation,05_Documentation,06_Experiments}

mkdir -p ~/AI-Workspace/01_C/{Embedded,STM32,Algorithms}
mkdir -p ~/AI-Workspace/02_FPGA/{Verilog,VHDL,SystemVerilog,RISC-V}
mkdir -p ~/AI-Workspace/03_SoC/{AHB,AXI,APB,Verification}
mkdir -p ~/AI-Workspace/04_Translation/{Datasheets,Papers,Manuals}
```

권장 원칙:
- 개인 비밀키, `.env`, 암호, 인증 토큰을 workspace에 두지 않는다.
- 원본 데이터시트/논문은 별도 `originals` 디렉토리에 보관하고 덮어쓰지 않는다.
- 번역 결과는 `translated` 디렉토리에 저장한다.
- 프로젝트마다 Git 저장소를 만든다.
- AI가 수정하기 전 `git status`와 diff를 확인한다.

---

# 9. Git 작업 흐름

프로젝트 시작:

```bash
cd ~/AI-Workspace/02_FPGA/Verilog
git init
printf "# Verilog Project\n" > README.md
git add README.md
git commit -m "Initial project"
```

AI에게 작업을 맡기기 전:

```bash
git status
git add -A
git commit -m "Checkpoint before AI changes"
```

AI 작업 후:

```bash
git status
git diff
git diff --check
```

문제가 없을 때만 커밋:

```bash
git add -A
git commit -m "Add ALU and testbench"
```

AI에게 처음부터 자동 `git push` 권한을 주지 않는다.

---

# 10. 실제 검증 프로젝트

에이전트와 모델의 실력을 동일한 조건으로 평가할 수 있도록 아래 테스트를 순서대로 진행한다.

## Test 1: C 언어

요청 프롬프트:

```text
현재 디렉토리에 portable C11 프로젝트를 만들어줘.
32-bit unsigned integer의 parity를 계산하는 함수와 테스트 프로그램을 작성해.
CMakeLists.txt와 README.md를 포함해.
-Wall -Wextra -Werror로 컴파일하고 테스트해.
기존 파일은 덮어쓰지 마.
```

검증:

```bash
cmake -S . -B build
cmake --build build
```

## Test 2: Verilog ALU

```text
32-bit ALU를 Verilog-2001로 구현해줘.
ADD, SUB, AND, OR, XOR, SLT 연산을 지원해.
모듈, self-checking testbench, 실행 스크립트, README를 생성해.
iverilog로 컴파일하고 vvp로 테스트해.
테스트 실패가 있으면 원인을 분석하고 수정해.
```

검증:

```bash
iverilog -g2001 -o alu_tb alu.v alu_tb.v
vvp alu_tb
```

## Test 3: SystemVerilog

```text
동일한 ALU를 SystemVerilog로 구현해줘.
self-checking testbench와 assertion을 포함해.
Verilator lint 및 지원되는 시뮬레이션으로 검증해.
지원되지 않는 문법은 임의로 제거하지 말고 제한 사항을 보고해.
```

## Test 4: VHDL

```text
32-bit ALU를 VHDL-2008로 작성해줘.
entity, architecture, testbench를 분리하고
GHDL로 분석, elaboration, simulation을 수행해.
```

## Test 5: 기술 문서 번역

```text
현재 디렉토리의 영문 기술 문서를 한국어로 번역해줘.

규칙:
1. 기술 용어는 원문을 괄호 안에 병기한다.
2. 레지스터명, 비트 필드, 주소, 수식, 코드, 신호명은 변경하지 않는다.
3. 표의 행과 열 구조를 유지한다.
4. 경고, 주의, Note를 누락하지 않는다.
5. 원문을 덮어쓰지 말고 translated/에 결과를 저장한다.
6. 불확실한 문장은 임의로 의역하지 말고 표시한다.
```

## Test 6: 프로젝트 분석

```text
현재 Git 저장소를 분석해줘.
파일을 수정하지 말고 다음을 보고해.
- 프로젝트 목적
- 디렉토리 구조
- 모듈 의존 관계
- 빌드 및 시뮬레이션 방법
- 미완성 코드와 잠재적 문제
- 개선 제안
근거가 되는 파일 경로와 코드 위치를 함께 제시해.
```

---

# 11. 오프라인 운영

완전 오프라인으로 쓰려면 먼저 온라인 상태에서 다음을 준비한다.

1. Ollama 바이너리와 필요한 패키지 설치
2. 모든 모델 다운로드 완료
3. Hermes Agent 및 Python 패키지 설치
4. VS Code 및 확장 설치(선택)
5. GCC/HDL 도구 설치
6. 프로젝트 의존 패키지와 문서 확보
7. 설치 파일 및 모델 목록 기록

오프라인 확인:

```bash
ollama list
curl http://127.0.0.1:11434/api/tags
```

그 후 네트워크를 끊고 간단한 로컬 추론을 시험한다.

주의:
- 추론 자체는 오프라인 가능하지만 모델/패키지 다운로드는 온라인이 필요하다.
- 에이전트가 웹 검색, 외부 API, 원격 Git 저장소를 사용하면 오프라인 작업이 중단될 수 있다.
- 로컬 모델이 외부 API를 호출하지 않는지 에이전트 provider 설정을 확인한다.
- 모델 실행 서버는 localhost에만 바인딩한다.

---

# 12. 문제 해결

## Ollama가 GPU를 사용하지 않는 경우

```bash
nvidia-smi
ollama ps
journalctl -u ollama -n 100 --no-pager
```

확인:
- NVIDIA 드라이버 정상 여부
- Ollama가 GPU를 인식하는지
- 다른 프로세스가 VRAM을 점유하는지
- 모델/컨텍스트가 VRAM에 비해 너무 큰지

## Hermes가 모델을 찾지 못하는 경우

```bash
curl http://127.0.0.1:11434/v1/models
ollama list
hermes doctor
```

확인:
- Base URL이 `http://127.0.0.1:11434/v1`인지
- 모델 ID가 실제 Ollama 모델명과 일치하는지
- Hermes provider 유형이 OpenAI-compatible 또는 Ollama에 맞는지
- Tool calling이 모델에서 지원되는지

## 파일을 수정하지 못하는 경우

```bash
pwd
whoami
ls -ld .
touch ./agent_write_test.tmp
rm ./agent_write_test.tmp
```

확인:
- 에이전트 실행 위치가 프로젝트 폴더인지
- Linux 사용자에게 쓰기 권한이 있는지
- 에이전트의 파일 편집 도구가 승인/차단 상태인지
- 보호 디렉토리 정책에 막히지 않았는지

## Agent가 명령을 실행하지 않는 경우

- 모델이 tool calling을 지원하는지 확인
- Hermes/Roo/Cline의 터미널 도구가 활성화되어 있는지 확인
- 명령 실행 승인 대기 상태인지 확인
- 단순 텍스트 응답 모드가 아니라 Agent 모드인지 확인

## 64K로 설정했는데 실제 CONTEXT가 32K인 경우

증상:

```bash
ollama ps
# CONTEXT 열이 32768로 표시됨

journalctl -u ollama --since "10 minutes ago" --no-pager | grep -i "requested context"
# requested context size too large for model num_ctx=64000 n_ctx_train=32768
```

원인: 모델 자체의 네이티브 컨텍스트가 32K다. Modelfile의 `num_ctx`를 올려도 Ollama가 네이티브 값으로 클램프한다. 현재 설치된 모델 중 `qwen2.5-coder` 계열이 여기에 해당한다.

해결:

1. `ollama show <모델>`의 `context length`가 64K 이상인지 확인한다.
2. 64K 이상 네이티브 모델로 바꾼다: `llama3.1:8b`, `deepseek-r1:8b`, `qwen3.5:9b`, `qwen3-coder:30b`, `glm-4.7-flash`.
3. Hermes 설정에 `ollama_num_ctx`와 `context_length`를 65536으로 명시한다.
4. `hermes -z "Reply with exactly: READY"` 실행 후 `ollama ps`에서 CONTEXT=65536을 확인한다.

## 컨텍스트가 부족한 경우

- 불필요한 빌드 산출물, 바이너리, 대형 로그를 컨텍스트에서 제외
- 프로젝트 요약 문서와 모듈별 README 작성
- 한 번에 전체 프로젝트를 수정하지 말고 모듈 단위로 나눔
- 컨텍스트를 늘리기 전에 VRAM 사용량 확인

---

# 13. 권장 운영 규칙

1. 프로젝트별 Git 저장소를 사용한다.
2. AI 작업 전 커밋 또는 백업을 만든다.
3. 처음에는 파일 읽기와 분석부터 허용한다.
4. 기존 파일 수정은 diff를 검토한다.
5. `sudo`, 삭제, 시스템 설정 변경은 사용자가 직접 승인한다.
6. C/HDL 코드는 컴파일 및 시뮬레이션으로 검증한다.
7. 모델 응답만으로 기능이 맞다고 판단하지 않는다.
8. 번역은 원문과 결과를 별도 파일로 보존한다.
9. 오프라인 모델과 패키지 버전을 기록한다.
10. 모델을 바꿀 때는 동일한 테스트 세트를 사용한다.

---

# 14. 설치 완료 체크리스트

- [ ] NVIDIA 드라이버 및 RTX 5090 인식
- [ ] Ollama 설치 및 서비스 실행
- [ ] 기존 모델 확인 또는 코딩 모델 다운로드
- [ ] Ollama 로컬 API 응답
- [ ] Hermes Agent 설치/업데이트
- [ ] Hermes에서 Ollama 모델 연결
- [ ] `ollama ps`에서 실제 CONTEXT 64K 확인 (필요 시)
- [ ] 작업 폴더에서 파일 읽기 성공
- [ ] 테스트 파일 생성 및 수정 성공
- [ ] 터미널 명령 실행 성공
- [ ] C 컴파일 및 실행 성공
- [ ] Verilog 시뮬레이션 성공
- [ ] SystemVerilog lint/검증 성공
- [ ] VHDL GHDL 시뮬레이션 성공
- [ ] Git diff 및 commit 성공
- [ ] 영문 기술 문서 번역 성공
- [ ] 네트워크 차단 상태에서 로컬 추론 성공
- [ ] 외부 API provider 비활성화 확인

---

# 15. 최종 권장안

현재 하드웨어와 주요 업무를 고려한 첫 번째 구현은 다음과 같다.

| 구성 | 선택 |
|---|---|
| OS | Ubuntu 22.04 LTS |
| GPU | RTX 5090 Laptop 24GB |
| LLM Runtime | Ollama 0.33.3 |
| Primary Agent | Hermes Agent v0.22.4 |
| GUI 대안 | VS Code + Roo Code |
| **지금 쓸 모델** | **`llama3.1:8b` (64K 에이전트) + `qwen2.5-coder-64k` (코드, 32K)** |
| 번역 모델 | `exaone3.5:7.8b` (도구 호출 없음, 별도 채팅) |
| 나중에 업그레이드 | `qwen3.5:9b` (안정) / `qwen3-coder:30b` (코딩 최우선) / `glm-4.7-flash` (대안) |
| C Toolchain | GCC / Clang / CMake |
| Verilog | Icarus Verilog / Verilator |
| VHDL | GHDL |
| Synthesis | Yosys |
| Waveform | GTKWave |
| Version Control | Git |

**구축 순서 요약**

```text
1. 기존 환경 백업
       ↓
2. Ollama 상태 점검
       ↓
3. 설치된 모델 확인 (지금은 다운로드 불필요)
       ↓
4. Hermes Agent 상태 확인 / 필요 시 업데이트
       ↓
5. Ollama API 연결 (llama3.1:8b, 64K)
       ↓
6. 로컬 파일 읽기/쓰기 검증
       ↓
7. C/HDL 도구 설치 및 테스트
       ↓
8. Git 통합
       ↓
9. 번역 작업 검증 (exaone3.5)
       ↓
10. 오프라인 테스트
       ↓
11. 필요하면 Roo Code GUI 추가
       ↓
12. 네트워크 회복 후 고성능 모델로 교체
```

**핵심 원칙:** 에이전트(Hermes/Roo Code)와 모델 서버(Ollama)를 분리한다. 그래야 나중에 모델 또는 에이전트를 바꾸더라도 나머지 환경을 유지할 수 있다.

---

# 16. 공식 참고 링크

설치 명령과 설정 화면은 업데이트될 수 있으므로 실행 직전에 공식 문서를 확인한다.

- Ollama: https://ollama.com/
- Ollama Linux 설치: https://github.com/ollama/ollama/blob/main/docs/linux.md
- Ollama 모델 라이브러리: https://ollama.com/library
- Ollama OpenAI 호환 API: https://docs.ollama.com/api/openai-compatibility
- Ollama Qwen2.5-Coder 모델: https://ollama.com/library/qwen2.5-coder
- Ollama Qwen3-Coder 모델: https://ollama.com/library/qwen3-coder
- Ollama Qwen3.5 모델: https://ollama.com/library/qwen3.5
- Ollama GLM-4.7-Flash 모델: https://ollama.com/library/glm-4.7-flash
- Ollama + Roo Code 연동: https://github.com/ollama/ollama/blob/main/docs/integrations/roo-code.mdx
- Hermes Agent 저장소: https://github.com/NousResearch/hermes-agent
- Hermes Agent 문서: https://hermes-agent.nousresearch.com/
- Hermes Agent Quickstart (64K minimum context): https://hermes-agent.nousresearch.com/docs/getting-started/quickstart
- Hermes + Ollama 로컬 설정 가이드: https://hermes-agent.nousresearch.com/docs/guides/local-ollama-setup
- Hermes Local Models: https://hermes-agent.nousresearch.com/docs/user-guide/local-models
- Roo Code 저장소: https://github.com/RooCodeInc/Roo-Code
- Roo Code 문서: https://docs.roocode.com/
- Cline 저장소: https://github.com/cline/cline
- Cline 문서: https://docs.cline.bot/
- Icarus Verilog: https://steveicarus.github.io/iverilog/
- Verilator: https://verilator.org/guide/latest/
- GHDL: https://ghdl.github.io/ghdl/
- Yosys: https://yosyshq.net/yosys/
- GTKWave: https://gtkwave.sourceforge.net/
- Git: https://git-scm.com/doc

---

*이 문서는 개인용 로컬 AI 코딩 에이전트 구축을 위한 실행 가이드다. 모델 태그, 설치 명령, 설정 키, 확장 UI는 릴리스에 따라 달라질 수 있으므로 공식 문서와 실제 `--help` 출력을 기준으로 확인한다.*
