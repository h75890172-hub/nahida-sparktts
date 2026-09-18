import argparse
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio
from transformers import AutoModelForCausalLM, AutoTokenizer

from infer import generate_speech_from_text
from sparktts.models.audio_tokenizer import BiCodecTokenizer


PROJECT_ROOT = Path(__file__).resolve().parent
CHARACTER_FOLDER = "纳西妲"
DEFAULT_MODEL_ROOT = PROJECT_ROOT / "genshin"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"
NATIVE_SAMPLE_RATE = 16000


@dataclass(frozen=True)
class GenerationResult:
    output_path: Path
    duration_seconds: float
    sample_rate: int
    chunk_count: int
    elapsed_seconds: float


def split_text(text: str, max_chars: int) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        raise ValueError("Text cannot be empty")

    sentences = [
        item.strip()
        for item in re.split(r"(?<=[。！？!?；;\n])", normalized)
        if item.strip()
    ]
    chunks = []
    for sentence in sentences:
        if len(sentence) <= max_chars:
            chunks.append(sentence)
            continue

        clauses = [
            item.strip()
            for item in re.split(r"(?<=[，,、：:])", sentence)
            if item.strip()
        ]
        for clause in clauses:
            if len(clause) <= max_chars:
                chunks.append(clause)
            else:
                chunks.extend(
                    clause[index : index + max_chars]
                    for index in range(0, len(clause), max_chars)
                )
    return chunks


class NahidaTTS:
    def __init__(
        self,
        model_root: Path | None = None,
        device: str | None = None,
    ):
        self.model_root = Path(
            model_root or os.getenv("MODEL_PATH", DEFAULT_MODEL_ROOT)
        )
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self.audio_tokenizer = None

    @property
    def loaded(self) -> bool:
        return self.model is not None

    def load(self) -> None:
        if self.loaded:
            return

        character_path = self.model_root / CHARACTER_FOLDER
        audio_tokenizer_path = self.model_root / "Spark-TTS-0.5B"
        if not character_path.is_dir():
            raise FileNotFoundError(f"Character model not found: {character_path}")
        if not audio_tokenizer_path.is_dir():
            raise FileNotFoundError(f"Base model not found: {audio_tokenizer_path}")

        if self.device.startswith("cuda"):
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True

        model_dtype = torch.float16 if self.device.startswith("cuda") else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(
            character_path,
            device_map=self.device,
            low_cpu_mem_usage=True,
            torch_dtype=model_dtype,
        ).eval()
        self.tokenizer = AutoTokenizer.from_pretrained(character_path)
        self.audio_tokenizer = BiCodecTokenizer(audio_tokenizer_path, self.device)
        if self.device.startswith("cuda"):
            self.audio_tokenizer.feature_extractor.to("cpu")
            torch.cuda.empty_cache()

    @torch.inference_mode()
    def generate(
        self,
        text: str,
        output_path: Path,
        max_chars: int = 90,
        max_new_tokens: int = 512,
        temperature: float = 0.65,
        top_k: int = 50,
        top_p: float = 1.0,
        target_sample_rate: int = 44100,
        seed: int = 42,
    ) -> GenerationResult:
        self.load()
        torch.manual_seed(seed)
        if self.device.startswith("cuda"):
            torch.cuda.manual_seed_all(seed)

        chunks = split_text(text, max_chars)
        started_at = time.perf_counter()
        waveforms = []
        silence = np.zeros(int(NATIVE_SAMPLE_RATE * 0.16), dtype=np.float32)

        for index, chunk in enumerate(chunks):
            waveform = generate_speech_from_text(
                chunk,
                self.model,
                self.tokenizer,
                self.audio_tokenizer,
                max_seq_length=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                device=self.device,
            )
            if waveform.size == 0:
                raise RuntimeError(f"Generation produced no audio for: {chunk}")
            waveforms.append(np.asarray(waveform, dtype=np.float32))
            if index < len(chunks) - 1:
                waveforms.append(silence)

        waveform = np.concatenate(waveforms)
        if target_sample_rate != NATIVE_SAMPLE_RATE:
            tensor = torch.from_numpy(waveform).unsqueeze(0)
            waveform = torchaudio.functional.resample(
                tensor,
                NATIVE_SAMPLE_RATE,
                target_sample_rate,
            ).squeeze(0).numpy()

        peak = float(np.max(np.abs(waveform))) if waveform.size else 0.0
        if peak > 0.95:
            waveform = waveform * (0.95 / peak)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(
            output_path,
            waveform,
            target_sample_rate,
            subtype="PCM_16",
        )
        return GenerationResult(
            output_path=output_path,
            duration_seconds=len(waveform) / target_sample_rate,
            sample_rate=target_sample_rate,
            chunk_count=len(chunks),
            elapsed_seconds=time.perf_counter() - started_at,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Nahida speech from text.")
    text_group = parser.add_mutually_exclusive_group(required=True)
    text_group.add_argument("--text")
    text_group.add_argument("--input-file", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model-root", type=Path, default=DEFAULT_MODEL_ROOT)
    parser.add_argument("--max-chars", type=int, default=90)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.65)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--target-sample-rate", type=int, default=44100)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    text = args.text if args.text is not None else args.input_file.read_text("utf-8")
    output_path = args.output or (
        DEFAULT_OUTPUT_DIR / f"nahida_{time.strftime('%Y%m%d_%H%M%S')}.wav"
    )

    engine = NahidaTTS(model_root=args.model_root)
    result = engine.generate(
        text=text,
        output_path=output_path,
        max_chars=args.max_chars,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        top_p=args.top_p,
        target_sample_rate=args.target_sample_rate,
        seed=args.seed,
    )
    print(f"Output: {result.output_path}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    print(f"Sample rate: {result.sample_rate} Hz")
    print(f"Chunks: {result.chunk_count}")
    print(f"Elapsed: {result.elapsed_seconds:.2f}s")


if __name__ == "__main__":
    main()
