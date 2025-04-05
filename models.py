import torch
from diffusers import DiffusionPipeline
from kokoro import KPipeline

def load_models(lang_code='p'):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Usando dispositivo: {device}")
    print("Carregando Playground V2.5...")
    pipe = DiffusionPipeline.from_pretrained(
        "playgroundai/playground-v2.5-1024px-aesthetic",
        torch_dtype=torch.float16,
        use_safetensors=True
    ).to(device)
    if torch.cuda.is_available():
        pipe.enable_attention_slicing()
    print(f"Carregando modelo Kokoro com idioma '{lang_code}'...")
    kokoro_pipeline = KPipeline(lang_code=lang_code)
    print("Modelos carregados com sucesso!")
    return pipe, kokoro_pipeline