import subprocess

models = [
    # --- 1. 범용 / 대화형 (General Purpose & Multi-language) ---
    "qwen2.5:0.5b",
    "qwen2.5:1.5b",
    "qwen2.5:3b",
    "qwen2.5:7b",
    "qwen2.5:14b",
    "qwen2.5:32b",
    "qwen2.5:72b",
    "llama3.2:1b",
    "llama3.2:3b",
    "llama3.1:8b",
    "llama3.1:70b",
    "llama3.3:70b",
    "gemma2:2b",
    "gemma2:9b",
    "gemma2:27b",
    "phi3:3.8b",
    "phi3.5:3.8b",
    "mistral:7b",
    "mixtral:8x7b",
    "mixtral:8x22b",
    "command-r:35b",
    "command-r-plus:104b",
    "yi:6b",
    "yi:34b",

    # --- 2. 한국어 특화 모델 (Korean Focused) ---
    "exaone3.5:2.4b",
    "exaone3.5:7.8b",
    "solar:10.7b",
    "yanolja-eeve:10.8b",

    # --- 3. 코딩 특화 (Coding & Autocomplete) ---
    "qwen2.5-coder:0.5b",
    "qwen2.5-coder:1.5b",
    "qwen2.5-coder:3b",
    "qwen2.5-coder:7b",
    "qwen2.5-coder:14b",
    "qwen2.5-coder:32b",
    "deepseek-coder:6.7b",
    "deepseek-coder-v2:16b",
    "codestral:22b",
    "codegeex4:9b",
    "starcoder2:3b",
    "starcoder2:7b",
    "starcoder2:15b",
    "codellama:7b",
    "codellama:13b",
    "codellama:34b",
    "codegemma:2b",
    "codegemma:7b",

    # --- 4. 심층 추론 및 수학 특화 (Reasoning / Math / CoT) ---
    "deepseek-r1:1.5b",
    "deepseek-r1:7b",
    "deepseek-r1:8b",
    "deepseek-r1:14b",
    "deepseek-r1:32b",
    "deepseek-r1:70b",
    "qwq:32b",
    "marco-o1:7b",
    "qwen2.5-math:1.5b",
    "qwen2.5-math:7b",
    "qwen2.5-math:72b",

    # --- 5. 시각 / 멀티모달 (Vision & Multimodal) ---
    "llava:7b",
    "llava:13b",
    "llava:34b",
    "llava-llama3:8b",
    "llama3.2-vision:11b",
    "llama3.2-vision:90b",
    "pixtral:12b",
    "minicpm-v:8b",
    "moondream:1.8b",
    "bakllava:7b",

    # --- 6. 임베딩 & 검색 (Embedding & RAG) ---
    "nomic-embed-text",
    "bge-m3",
    "bge-large",
    "snowflake-arctic-embed:137m",
    "snowflake-arctic-embed:335m",
    "all-minilm",
    "mxbai-embed-large",

    # --- 7. 오디오 / 도구 사용 특화 (Audio / Function Calling / Uncensored) ---
    "whisper:tiny",
    "whisper:base",
    "whisper:small",
    "whisper:medium",
    "whisper:large-v3",
    "hermes3:8b",
    "hermes3:70b",
    "wizardlm2:7b",
    "wizardlm2:8x22b"
]

print("==========================================")
print(" Starting Ollama Batch Model Download")
print("==========================================")

for model in models:
    print(f"\n[+] Pulling model: {model} ...")
    try:
        # 실시간 진행상황 출력을 위해 check=True 사용
        subprocess.run(["ollama", "pull", model], check=True)
        print(f" -> [SUCCESS] {model}")
    except subprocess.CalledProcessError:
        print(f" -> [ERROR] Failed to pull {model}")
    except FileNotFoundError:
        print(" -> [CRITICAL ERROR] 'ollama' CLI was not found in system PATH.")
        break

print("\n==========================================")
print(" All tasks completed!")
print("==========================================")