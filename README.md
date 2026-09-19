# Nahida Spark-TTS

一个面向本地部署的纳西妲中文文本转语音项目。输入文字即可直接生成语音，
不需要先调用基础 TTS，也不需要再经过 So-VITS-SVC 或 RVC 音色转换。

项目提供 WebUI、命令行、Windows 一键脚本、GPU/CPU Docker Compose，以及
GitHub Actions 自动构建 GHCR 镜像。

> 模型权重、游戏音频和角色素材不包含在本仓库中。请自行下载，仅用于个人
> 学习和实验，不得用于冒充、诈骗、绕过身份验证或未经授权的内容分发。

## 项目状态

| 功能 | 状态 |
|---|---|
| 文本直接生成语音 | 已实现 |
| WebUI | 已实现并通过推理测试 |
| 命令行 | 已实现并通过推理测试 |
| 长文本分句 | 已实现 |
| 44.1 kHz WAV 输出 | 已实现 |
| NVIDIA GPU Docker | 已配置，支持 `nvidia-container-runtime` |
| CPU Docker | 已配置 |
| 多连接模型下载与 SHA-256 校验 | 已实现 |
| GitHub Actions | 已配置 |
| GHCR 镜像发布 | 推送 `main` 或标签后自动构建 |

## 工作原理

```text
输入文字
  -> Spark-TTS tokenizer
  -> 纳西妲微调后的 Causal LM
  -> BiCodec semantic / global tokens
  -> BiCodec waveform decoder
  -> 44.1 kHz 单声道 WAV
```

模型原生输出采样率为 16 kHz。项目会统一重采样到 44.1 kHz、单声道、
PCM 16-bit，并对超过 0.95 的峰值做安全缩放。

## 主要功能

- 直接输入中文文本并生成纳西妲风格语音。
- WebUI 支持按句分段生成较长文本。
- 命令行支持指定输出路径、分句长度、温度和 Top-K。
- 下载器支持断点续传、多连接下载和 SHA-256 校验。
- Docker 只打包程序与依赖，模型通过只读卷挂载，不复制进镜像。
- GPU 构建默认使用国内可达的 Docker 镜像源，网络可用时也可切换官方源。
- GitHub Actions 可自动构建并推送 `ghcr.io/<owner>/nahida-sparktts`。

## 目录结构

```text
nahida_sparktts/
├─ Dockerfile
├─ docker-compose.yml
├─ docker-compose.cpu.yml
├─ requirements.txt
├─ requirements-docker.txt
├─ download_nahida.py
├─ nahida_tts.py
├─ nahida_webui.py
├─ Start-Nahida-TTS.bat
├─ Stop-Nahida-TTS.bat
├─ Generate-Nahida.bat
├─ Push-To-GitHub.bat
├─ audio_feature_comparison.md
├─ voice_feature_report_30s.json
├─ sparktts/
├─ genshin/                 # 模型目录，默认被 Git 忽略
└─ outputs/                 # 音频输出，默认被 Git 忽略
```

模型目录结构：

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

## 环境要求

### 推荐配置

```text
Windows 11
Python 3.12
<gpu> 或更高
NVIDIA 驱动支持 CUDA 11.8 及以上
Docker Desktop 4.91 或更高
WSL2
至少 15 GB 可用空间
```

CPU 模式可以运行，但生成速度会明显变慢。

## 仓库地址

```text
https://github.com/project-maintainer/nahida-sparktts
```

## 快速开始

### 1. 克隆项目

```powershell
git clone https://github.com/project-maintainer/nahida-sparktts.git
cd nahida-sparktts
```

### 2. 下载模型

模型约 `4.64 GB`。下载器优先使用 `aria2c` 进行多连接和断点续传，没有
`aria2c` 时回退到 `curl`。

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
python -m pip install requests
python download_nahida.py
```

下载完成后会自动校验文件大小。模型文件存在 SHA-256 元数据时还会校验哈希。

### 3. 启动 GPU Docker

```powershell
docker compose up -d --build
```

打开：

```text
http://127.0.0.1:7861
```

查看日志：

```powershell
docker compose logs -f
```

停止：

```powershell
docker compose down
```

### 4. 启动 CPU Docker

```powershell
docker compose -f docker-compose.cpu.yml up -d --build
```

打开：

```text
http://127.0.0.1:7862
```

## Docker 挂载

Compose 会挂载：

```text
./genshin  -> /models:ro
./outputs  -> /app/outputs
```

因此重建镜像不会复制或删除模型，生成的 WAV 文件会直接出现在宿主机
`outputs` 目录。

## 国内网络配置

部分网络无法直连 Docker Hub。Compose 默认使用：

```text
Docker 镜像：docker.m.daocloud.io
PyPI 镜像：https://pypi.tuna.tsinghua.edu.cn/simple
```

切换到官方源：

```powershell
$env:PYTORCH_IMAGE = "pytorch/pytorch:2.7.1-cuda11.8-cudnn9-runtime"
$env:PIP_INDEX_URL = "https://pypi.org/simple"
docker compose up -d --build
```

## Windows 原生运行

### 创建环境

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install torch==2.7.1 torchaudio==2.7.1 `
  --index-url https://download.pytorch.org/whl/cu118
.\.venv\Scripts\python.exe -m pip install -r requirements.txt `
  -r requirements-docker.txt
```

### 启动 WebUI

```powershell
.\Start-Nahida-TTS.bat
```

默认地址：

```text
http://127.0.0.1:7861
```

停止 WebUI：

```powershell
.\Stop-Nahida-TTS.bat
```

### 命令行生成

```powershell
.\Generate-Nahida.bat "你好，旅行者。欢迎来到须弥。" `
  -OutputPath ".\outputs\nahida.wav"
```

直接调用 Python：

```powershell
.\.venv\Scripts\python.exe nahida_tts.py `
  --text "你好，旅行者。" `
  --output ".\outputs\nahida.wav"
```

支持的主要参数：

```text
--max-chars          单段最大字符数，默认 90
--max-new-tokens     单段最大音频 token 数，默认 1024
--temperature        采样温度，默认 0.65
--top-k              Top-K，默认 50
--top-p              Top-P，默认 1.0
--target-sample-rate 默认 44100
--seed               随机种子，默认 42
```

## 长文本处理

```text
长文本
-> 按句号、问号、感叹号、分号和换行切分
-> 过长句子继续按逗号和冒号切分
-> 每段单独推理
-> 插入约 160 ms 静音
-> 拼接、重采样、峰值保护
-> 输出 WAV
```

按 90 字左右切分可以降低单次自回归生成过长导致的重复、漏字和显存峰值。

## 参考音频特征对比

统一截取公开参考音频的前 30 秒，去除静音后计算：

| 指标 | pure | full | hit |
|---|---:|---:|---:|
| 中位 F0 | 272.52 Hz | 272.52 Hz | 541.90 Hz |
| F0 半音标准差 | 2.33 | 2.40 | 4.28 |
| 有声比例 | 74.83% | 73.71% | 15.84% |
| F1 | 741.44 Hz | 752.13 Hz | 925.91 Hz |
| F2 | 1783.51 Hz | 1812.74 Hz | 1987.45 Hz |
| F3 | 2951.04 Hz | 2936.90 Hz | 3078.72 Hz |
| 频谱平坦度 | 0.000607 | 0.000861 | 0.000232 |
| 频谱质心 | 3293.61 Hz | 3368.17 Hz | 2625.92 Hz |
| RMS | 0.0698 | 0.0946 | 0.0657 |

结论：

- `pure` 更适合作为正常对白的声线和韵律基线。
- `full` 的响度和噪声更高，应先做去伴奏、降噪和响度统一。
- `hit` 的中位音高约为普通对白的 1.99 倍，属于独立的高强度情绪数据。

详细数据：

- [audio_feature_comparison.md](audio_feature_comparison.md)
- [voice_feature_report_30s.json](voice_feature_report_30s.json)

## GHCR 镜像

GitHub Actions 在以下情况自动构建并推送镜像：

```text
push 到 main
push v* 标签
手动运行 workflow_dispatch
```

构建成功后，工作流会额外启动一个临时容器，验证 PyTorch、TorchAudio、
Transformers、Gradio、Spark-TTS 和 `nahida_tts` 模块可以正常导入。

镜像地址格式：

```text
ghcr.io/project-maintainer/nahida-sparktts:main
```

私有镜像使用一键脚本完成登录、拉取和启动：

```powershell
.\Deploy-GHCR.bat up
```

停止、查看日志或仅拉取镜像：

```powershell
.\Deploy-GHCR.bat down
.\Deploy-GHCR.bat logs
.\Deploy-GHCR.bat pull
```

## 常见问题

### Docker Hub 连接超时

确认 Compose 使用了 `docker.m.daocloud.io`。也可以切换为企业代理或官方源。

### Docker Desktop 报 `sailor-ingest.sock` 或 `engine.sock`

这是 Docker Desktop 在 Windows 上处理 AF_UNIX socket 重解析点的已知问题。
先完全退出 Docker Desktop，然后移走以下两个运行目录：

```text
%LOCALAPPDATA%\Docker\run
%LOCALAPPDATA%\docker-secrets-engine
```

再次启动 Docker Desktop。官方维护者确认，在部分主机上还需要重启 Windows
才能彻底释放旧 socket。不要执行 Clean/Purge data，容器、镜像和卷可以保留。

相关 issue：

```text
https://github.com/docker/for-win/issues/15063
```

### Docker 无法使用 GPU

```powershell
docker info --format '{{json .Runtimes}}'
```

输出中应包含：

```text
nvidia
```

同时确认 Docker Desktop 设置中已启用 WSL2 和 NVIDIA GPU 支持。

### 7861 端口被占用

```powershell
Get-NetTCPConnection -LocalPort 7861 -State Listen
```

可以先停止本地 WebUI：

```powershell
.\Stop-Nahida-TTS.bat
```

或者修改 `docker-compose.yml` 中的宿主机端口。

### 模型目录不存在

确认以下目录存在：

```text
genshin/Spark-TTS-0.5B
genshin/纳西妲
```

### 首次生成很慢

第一次请求需要把模型加载到显存，通常比后续请求慢。模型加载完成后，WebUI
会复用已加载的模型。

## 开发验证

```powershell
.\.venv\Scripts\python.exe -m py_compile `
  nahida_tts.py nahida_webui.py download_nahida.py infer.py

.\.venv\Scripts\python.exe -m pip check

docker compose config --quiet
```

## 许可证和使用边界

应用代码使用 Apache License 2.0。Spark-TTS 组件保留其原始版权和许可证
声明，详见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。

仓库不包含游戏音频、角色语音权重或角色素材。生成内容请明确标注为 AI
合成语音。不得用于冒充真人、欺诈、骚扰、绕过身份验证、传播违法内容或
未经授权分发声音模型。
