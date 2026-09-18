from sparktts.models.audio_tokenizer import BiCodecTokenizer
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from infer import infer
import os

device = "cuda" if torch.cuda.is_available() else "cpu"
max_seq_length = 1024

charactor = os.getenv("CHARACTOR", "furina")
input_text = os.getenv("INPUT_TEXT", "你好吗，今天过得怎么样呢？")
model_path = os.getenv("MODEL_PATH", "genshin")

audio_tokenizer_path = os.path.join(model_path, "Spark-TTS-0.5B")
character_model_path = os.path.join(model_path, charactor)

print(f"Loading model for character: {charactor} on {device}...")
model = AutoModelForCausalLM.from_pretrained(character_model_path, device_map=device)
tokenizer = AutoTokenizer.from_pretrained(character_model_path)
audio_tokenizer = BiCodecTokenizer(audio_tokenizer_path, device)

infer(model, tokenizer, audio_tokenizer, input_text, max_seq_length=max_seq_length, device=device)
