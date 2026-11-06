# Personal Local AI Coding Agent — 클린 재구축 가이드

> 대상: Ubuntu 22.04.5 LTS + RTX 5090 Laptop GPU 24GB / RAM 64GB / Core Ultra 9 275HX
> 목표: 기존 Ollama·Hermes 환경을 **완전히 제거** 후 **검증된 구성으로 신규 설치**
> 작성일: 2026-11-06

---

## 1. 목표 구성 요약

| 역할 | 모델 | 컨텍스트 | 용도 |
|---|---|---|---|
| **주력 에이전트** | qwen2.5-coder:14b | 64K | 파일 읽기·수정, 터미널, Git 작업 |
| 코드 기준선 | qwen2.5-coder:7b | 64K | 가볍고 빠른 코드 작업, 폴백 |
| 순수 추론 (툴콜 없음) | deepseek-r1:8b | 64K | 설계 검토, 로직 검증 |
| 한국어 번역 전용 | exaone3.5 | 32K | 기술 문서 번역 파이프라인 |
| 에이전트 (제외) | llama3.1, exaone | - | 코드 에이전트 툴콜로 부적합 → 설치 생략 가능 |

시스템 서비스:

- `ollama` — systemd 서비스, 64K 컨텍스트 환경변수 고정
- Hermes Agent — 설정: model qwen2.5-coder-14b-k, provider custom, `http://127.0.0.1:11434/v1`

VRAM 여유 확인: 14B 가중치 (~9.2GB) + 64K KV 캐시 (q8_0, ~9GB) = **18GB < 24GB** ✅

---

## 2. Step 0 — 백업 (삭제 전 필수)

```bash
# 기존 Hermes 설정 백업
cp -r ~/.hermes ~/hermes-backup-$(date +%Y%m%d)

# 기존 모델 목록 백업 (재다운로드 판단용)
ollama list > ~/ollama-models-backup-$(date +%Y%m%d).txt
ollama show qwen2.5-coder-64k >> ~/ollama-models-backup-$(date +%Y%m%d).txt
```

---

## 3. Step 1 — 기존 환경 완전 제거

### 3-1. 실행 중인 프로세스/서비스 중지

```bash
sudo systemctl stop ollama 2>/dev/null
sudo systemctl disable ollama 2>/dev/null
pkill -f hermes 2>/dev/null
```

### 3-2. Ollama 모델/설정 삭제

```bash
# 모델 저장소 전체 삭제 (~/.ollama/models)
rm -rf ~/.ollama
```

### 3-3. Ollama 자체 제거

```bash
# 설치 방식에 따라 선택 ──

# (a) tarball/스크립트로 설치한 경우
sudo rm -rf /usr/local/lib/ollama       # 라이브러리
sudo systemctl uninstall ollama 2>/dev/null || \
sudo rm /etc/systemd/system/ollama.service
sudo rm /usr/local/bin/ollama           # CLI

# (b) deb/app 패키지로 설치한 경우
sudo apt purge -y ollama 2>/dev/null
sudo apt autoremove -y
```

### 3-4. systemd 설정 및 환경변수 제거

```bash
sudo systemctl daemon-reload
sudo systemctl reset-failed
# 예전 OLLAMA_CONTEXT_LENGTH 등 override 복구 방지
sudo rm -f /etc/systemd/system/ollama.service.d/override.conf
```

### 3-5. Hermes Agent 제거

```bash
# 설치 방식(pip / npm / 바이너리)에 따라 실행 ──
rm -rf ~/.hermes
# pip 으로 설치했다면: pip uninstall hermes-agent
# npm 으로 설치했다면: npm uninstall -g hermes-agent
```

### 3-6. 잔존물 확인 (남아있는 것 조사)

```bash
which ollama ; should return nothing
systemctl status ollama ; should be not-found
ls ~/.ollama ~/.hermes ; should not exist
ps aux | grep -E 'ollama|hermes' | grep -v grep ; should be empty
```

---

## 4. Step 2 — 신규 설치

### 4-1. NVIDIA 드라이버 확인 (이미 580.159.04 → skip)

```bash
nvidia-smi   # RTX 5090, driver 580.x 확인
```

### 4-2. Ollama 신규 설치

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 4-3. systemd 환경변수 설정 (핵심)

```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<'EOF'
[Service]
Environment="OLLAMA_CONTEXT_LENGTH=64000"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_KEEP_ALIVE=-1"        # 모델 즉시 언로드 방지
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now ollama
```

| 변수 | 이유 |
|---|---|
| `OLLAMA_CONTEXT_LENGTH=64000` | 64K 컨텍스트 기본값 |
| `OLLAMA_FLASH_ATTENTION=1` | 64K 이상에서 **필수** (긴 컨텍스트 attention 수치 안정성) |
| `OLLAMA_KV_CACHE_TYPE=q8_0` | KV 캐시 절반. 14B+64K 조합을 24GB에 수용 가능하게 |
| `OLLAMA_KEEP_ALIVE=-1` | 에이전트 반복 호출 시 리로드 지연 제거 |

### 4-4. 검증

```bash
systemctl is-active ollama          # active
curl -s http://127.0.0.1:11434/api/tags | head -c 200
```

---

## 5. Step 3 — 모델 다운로드 및 64K 컨텍스트 재정의

### 5-1. 다운로드

```bash
ollama pull qwen2.5-coder:14b      # 주력 에이전트 (~9GB)
ollama pull qwen2.5-coder:7b       # 폴백 (~4.7GB)
ollama pull deepseek-r1:8b         # 추론 (~5.2GB)
ollama pull exaone3.5:7.8b         # 번역 (~4.8GB)
```

### 5-2. Modelfile로 64K 컨텍스트 버전 생성

> ⚠️ **핵심**: `OLLAMA_CONTEXT_LENGTH`는 기본값일 뿐, 다운로드받은 모델 내부의
> 기존 `num_ctx`(대부분 32768/16384)가 **override**합니다.
> 반드시 Modelfile로 재생성해야 64K가 실제 적용됩니다.

```bash
mkdir -p ~/ollama-modelfiles && cd ~/ollama-modelfiles

for M in 14b 7b; do
  printf "FROM qwen2.5-coder:%s\nPARAMETER num_ctx 64000\n" "$M" > Modelfile-coder-$M
  ollama create qwen2.5-coder-$M-k -f Modelfile-coder-$M
done

printf "FROM deepseek-r1:8b\nPARAMETER num_ctx 64000\n" > Modelfile-r1
ollama create deepseek-r1-64k -f Modelfile-r1
```

### 5-3. 검증 — **여기서 무조건 실제 로드 값 확인**

```bash
ollama show qwen2.5-coder-14b-k | grep -i num_ctx   # 64000 이어야 함
ollama show qwen2.5-coder-7b-k   | grep -i num_ctx   # 64000 이어야 함
ollama show deepseek-r1-64k      | grep -i num_ctx   # 64000 이어야 함

# 실제 로드 테스트: 컨텍스트가 64000으로 표시되어야 정상
ollama run qwen2.5-coder-14b-k "hi" --verbose 2>&1 | head -20
ollama ps                                  # CONTEXT 컬럼 확인
```

`ollama ps`에서 `CONTEXT: 64000`이 안 보이면 Modelfile 생성이 실패한 것 — 5-2 부터 재실행.

---

## 6. Step 4 — Hermes Agent 신규 설치

### 6-1. 설치

```bash
# 설치 방식은 사용 버전에 맞게 ──
# 각자 다운로드 경 확인 후 (pip / npm / binary)
# 예: pip install hermes-agent
```

### 6-2. 설정 (`~/.hermes/config.yaml`)

```yaml
model: qwen2.5-coder-14b-k
provider: custom
base_url: http://127.0.0.1:11434/v1
context_length: 64000
```

### 6-3. 통합 검증 (실제 툴콜 흐름 테스트)

```bash
hermes "현재 디렉터리의 파일 목록을 보여준 후, test.md 파일을 새로 만들고 'hello'를 작성해줘"
```

→ **파일 읽기(ls) → 파일 쓰기(Write)** 두 개의 툴콜이 정상 작동해야 성공.
실패 시: Hermes의 context_length가 Ollama 실제 컨텍스트보다 작거나 같은지 확인.

---

## 7. 일상 운영 팁

| 상황 | 대응 |
|---|---|
| 대형 리포지토리 diff 분석/URL 대상 리팩토링 | qwen2.5-coder-14b-k (64K 담당) |
| 단순 편집, 터미널, Git 커밋 | qwen2.5-coder-7b-k (속도 우선 폴백) |
| 설계 검토 / 논리 회로 검증 Q&A | deepseek-r1-64k (thinking, 툴콜 없음) |
| 기술 문서 한영 번역 | exaone3.5 (별도 파이프라인, 에이전트에서 못 씀) |
| VRAM OOM 발생 | 14b → 7b-k로 전환, 또는 num_ctx 32000으로 하향 |
| 32K를 넘는 초장문 문맥 | 설치 모델로 불가 → llama3.1:8b 재추가는 별도 결정 |

---

## 8. 문제 복구용 명령 모음

```bash
# 컨텍스트 실제 적용 확인
ollama ps
journalctl -u ollama -f          # 서버 로그 실시간
ollama show <모델> --modelfile   # Modelfile 역추적

# 서비스 재시작
sudo systemctl restart ollama

# VRAM/메모리 사용량 확인
nvidia-smi
```

---

## 9. 최종 체크리스트

- [ ] Step 1 완료: `which ollama`, `systemctl status ollama`가 모두 비어 있음
- [ ] Step 2 완료: `systemctl is-active ollama` = `active`, `/api/tags` 응답
- [ ] Step 3 완료: `ollama ps`에서 `qwen2.5-coder-14b-k`의 `CONTEXT`가 `64000`
- [ ] Step 4 완료: Hermes가 실제 파일 읽기/쓰기/터미널 툴콜 성공
- [ ] nvidia-smi에서 14B 로드 시 VRAM 사용량 18~20GB 이하
