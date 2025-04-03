import torch
from diffusers import StableDiffusionXLPipeline
from kokoro import KPipeline

def load_models():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Usando dispositivo: {device}")
    print("Carregando Stable Diffusion XL...")
    pipe = StableDiffusionXLPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, variant="fp16", use_safetensors=True
    ).to(device)
    if torch.cuda.is_available():
        pipe.enable_attention_slicing()
    print("Carregando modelo Kokoro...")
    kokoro_pipeline = KPipeline(lang_code='pt')
    print("Modelos carregados com sucesso!")
    return pipe, kokoro_pipeline