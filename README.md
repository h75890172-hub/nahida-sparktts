# Nahida Spark-TTS

Local text-to-speech deployment for the Chinese Nahida voice using Spark-TTS.
The application accepts text directly and returns a mono 44.1 kHz WAV file.
Model weights are downloaded separately and are not committed to this
repository.

## Features

- Direct text-to-speech without a separate base TTS or SVC conversion step.
- Web UI and command line interfaces.
- Automatic sentence splitting for long text.
- 16 kHz native audio resampled to 44.1 kHz, mono PCM output.
- GPU and CPU Docker Compose configurations.
- Reproducible model downloader with size and SHA-256 verification.
- Audio feature comparison report for multiple public reference samples.

## Architecture

```text
Text
  -> Spark-TTS tokenizer
  -> fine-tuned causal language model
  -> BiCodec semantic and global tokens
  -> BiCodec waveform decoder
  -> WAV
```

The repository contains application code only. The base model and character
weights remain external and are mounted into Docker at `/models`.

## Model Layout

```text
genshin/
├─ Spark-TTS-0.5B/
│  ├─ BiCodec/
│  ├─ LLM/
│  └─ wav2vec2-large-xlsr-53/
└─ 纳西妲/
   ├─ config.json
   ├─ generation_config.json
   ├─ model.safetensors
   └─ tokenizer files
```

Download and verify the models:

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
python -m pip install requests
python download_nahida.py
```

The downloader supports resumed and parallel transfers.

## Local Windows Setup

Create the environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install torch==2.7.1 torchaudio==2.7.1 `
  --index-url https://download.pytorch.org/whl/cu118
.\.venv\Scripts\python.exe -m pip install -r requirements.txt `
  -r requirements-docker.txt
```

Start the Web UI:

```powershell
.\Start-Nahida-TTS.bat
```

Open:

```text
http://127.0.0.1:7861
```

Generate from the command line:

```powershell
.\Generate-Nahida.bat "你好，旅行者。欢迎来到须弥。" `
  -OutputPath ".\outputs\nahida.wav"
```

## Docker

GPU:

```powershell
docker compose up --build
```

CPU:

```powershell
docker compose -f docker-compose.cpu.yml up --build
```

GPU runs on `http://127.0.0.1:7861`; CPU runs on
`http://127.0.0.1:7862`.

The GPU configuration requires Docker Desktop with the WSL2 backend and NVIDIA
GPU support. The container mounts:

```text
./genshin -> /models:ro
./outputs -> /app/outputs
```

The GitHub Actions workflow builds and publishes the image to GitHub Container
Registry on pushes to `main`, version tags, or manual runs.

## Audio Feature Comparison

The comparison uses the first 30 seconds of each public reference sample with
the same silence removal and feature extraction settings.

| Metric | pure | full | hit |
|---|---:|---:|---:|
| Median F0 | 272.52 Hz | 272.52 Hz | 541.90 Hz |
| F0 std, semitones | 2.33 | 2.40 | 4.28 |
| Voiced ratio | 74.83% | 73.71% | 15.84% |
| Spectral flatness | 0.000607 | 0.000861 | 0.000232 |
| Spectral centroid | 3293.61 Hz | 3368.17 Hz | 2625.92 Hz |

`pure` is the normal-dialogue baseline. `full` adds more noise and loudness.
`hit` is a separate high-pitch emotional distribution and should not be mixed
with normal dialogue without separate labeling.

See [audio_feature_comparison.md](audio_feature_comparison.md) and
[voice_feature_report_30s.json](voice_feature_report_30s.json).

## Verification

```text
Python compile: passed
PowerShell syntax parse: passed
pip check: passed
Local CLI generation: passed
Local WebUI API generation: passed
Docker Compose YAML parse: passed
```

## License And Usage

The application code is distributed under the Apache License 2.0. Spark-TTS
components retain their original copyright and license notices.

The repository does not include game audio, voice weights, or character assets.
Use this project only for personal learning and experimentation. Do not use it
to impersonate people, commit fraud, bypass identity checks, or distribute
unauthorized voice models.
