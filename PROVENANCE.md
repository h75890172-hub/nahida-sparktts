# 模型、数据与第三方来源披露

本文档记录项目使用的模型、训练数据、参考音频、代码与容器来源。仓库不包含
游戏原声、模型权重、训练数据或参考音频。

## 1. 代码来源

部署代码基于以下公开项目整理：

| 项目 | 来源 | 固定版本 | 声明许可证 |
|---|---|---|---|
| Genshin Spark-TTS | `https://github.com/nonwesjoe/genshin-sparktts` | `ca6a106799e4295103d2a466f1f23f67479f1207` | 见上游仓库 |
| Spark-TTS | `https://github.com/SparkAudio/Spark-TTS` | `2f1ea9082400547242641f5271b6f941c9f439d1` | Apache-2.0 |
| 上游训练 notebook | `https://www.kaggle.com/code/suziwsz/genshin-sparktts/` | 未固定 | 见 Kaggle 页面 |

本仓库增加的内容包括 Docker 部署、WebUI 包装、CLI、长文本切分、模型下载
校验、运行文档和隐私策略。

## 2. 基础模型来源

实际下载来源：

```text
Repository: wesjos/spark-tts-genshin-charactors
Revision:   f22c47a417ca8379c70e1388331e25bd0407a61f
Path:       Spark-TTS-0.5B/*
URL:        https://huggingface.co/wesjos/spark-tts-genshin-charactors
```

模型卡声明：

```text
Base model: SparkAudio/Spark-TTS-0.5B
License:    Apache-2.0
```

基础模型包含 Spark-TTS LLM、BiCodec 和 Wav2Vec2 相关文件。模型原生产物为
16 kHz 音频，本仓库在输出阶段转换为单声道 44.1 kHz WAV。

## 3. 纳西妲角色权重来源

实际下载来源：

```text
Repository: wesjos/spark-tts-genshin-charactors-new
Revision:   15d4ca3dc31389edd906e6f52bc2c56b2563c57b
Path:       纳西妲/*
URL:        https://huggingface.co/wesjos/spark-tts-genshin-charactors-new
```

模型卡声明：

```text
Task:          Text-to-Speech
Language:      Chinese
Base model:    SparkAudio/Spark-TTS-0.5B
Training data: simon3000/genshin-voice
License field: Apache-2.0
```

该角色权重是第三方全量微调模型。本仓库没有参与训练，也未修改权重。
上游模型卡同时致谢 Unsloth，但模型卡未提供足以独立验证全部训练命令和参数的
完整实验记录。

## 4. 训练数据集来源

模型卡声明的数据集：

```text
Dataset:      simon3000/genshin-voice
Revision:     68950dc52d799876d1e64c1ab6c47955502e79a1
URL:          https://huggingface.co/datasets/simon3000/genshin-voice
Examples:     654252
Dataset size: 约 371 GB
Languages:    Chinese, English, Japanese, Korean
```

数据集卡披露：

- 数据来自解包后的 Genshin Impact 游戏语音文件。
- 数据生产者是游戏开发及发行相关权利方。
- 包含游戏内标注、说话人名称和转写。
- 部分条目标注或转写缺失。
- 数据集卡自身没有声明开放许可证。
- 数据集卡版权声明为 `Copyright © COGNOSPHERE. All Rights Reserved.`。

因此：

```text
角色模型卡中的 Apache-2.0 字段
不能替代或覆盖底层游戏语音、角色和配音的权利归属。
```

本仓库不重新分发该数据集或训练得到的模型权重。

## 5. 参考音频来源

音频特征对比和调音过程使用了以下公开 Bilibili 视频的音频：

| 内容 | 视频 |
|---|---|
| 纳西妲部分语音素材 | `https://www.bilibili.com/video/BV1JG4y147fC` |
| 草神全语音，CV：花玲 | `https://www.bilibili.com/video/BV1bd4y1C7ot` |
| 纳西妲受击语音纯享版 | `https://www.bilibili.com/video/BV1jLbBzZEHt` |

仓库只保留特征统计结果：

```text
voice_feature_report_30s.json
audio_feature_comparison.md
```

仓库不包含原视频、完整参考音频或可直接重建原语音的素材。参考音频中的角色
声音、游戏内容和配音权利归相应权利人所有。

## 6. Docker 与运行环境来源

```text
Base image: pytorch/pytorch:2.7.1-cuda11.8-cudnn9-runtime
Registry:   Docker Hub
```

国内网络配置中的 `docker.m.daocloud.io` 是镜像缓存服务，不是模型或软件的
原始发布者。

基础镜像包含 PyTorch、CUDA runtime 和 cuDNN 等第三方组件。其许可证、导出
和再分发条件以对应项目及 NVIDIA 的官方条款为准。

## 7. 主要依赖来源

依赖版本见 `requirements.txt` 和 `requirements-docker.txt`。主要组件包括：

| 组件 | 上游 | 常见许可证 |
|---|---|---|
| PyTorch | `https://github.com/pytorch/pytorch` | BSD-3-Clause |
| TorchAudio | `https://github.com/pytorch/audio` | BSD-2-Clause |
| Transformers | `https://github.com/huggingface/transformers` | Apache-2.0 |
| Gradio | `https://github.com/gradio-app/gradio` | Apache-2.0 |
| NumPy | `https://github.com/numpy/numpy` | BSD-3-Clause |
| SoundFile | `https://github.com/bastibe/python-soundfile` | BSD-3-Clause |
| Safetensors | `https://github.com/huggingface/safetensors` | Apache-2.0 |
| Accelerate | `https://github.com/huggingface/accelerate` | Apache-2.0 |

最终发布镜像应通过 SBOM 或 `pip-licenses` 等工具生成完整依赖清单。本文档
列出主要来源，不替代各依赖包中的许可证原文。

## 8. 未包含与本仓库不分发的内容

```text
游戏原声和视频
simon3000/genshin-voice 数据集
第三方角色微调权重
Voice actor recordings
个人录音和未公开音频
```

使用者需要自行从原始来源下载模型，并自行确认当地法律、平台条款、角色版权、
配音权利和模型许可证是否允许其预期用途。

## 9. 使用限制

本项目与游戏、角色或模型的上游权利方无隶属或背书关系。生成内容应标记为
AI 合成语音，不得用于冒充、欺诈、骚扰、绕过身份验证、侵权传播或未经授权
的商业用途。
