import os
import torch
import json
import numpy as np
from PIL import Image
from moviepy.editor import AudioFileClip
import soundfile as sf
from tqdm import tqdm
import random

def clear_gpu_memory():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def process_json_prompts(json_file_path):
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"Arquivo JSON não encontrado em: {json_file_path}")
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        prompts = data.get("scenes", data if isinstance(data, list) else [])
        if not prompts:
            raise ValueError("Nenhuma cena encontrada no JSON.")
    for i, prompt in enumerate(prompts):
        if "prompt_image" not in prompt or "prompt_audio" not in prompt:
            raise ValueError(f"Prompt #{i+1} precisa de 'prompt_image' e 'prompt_audio'")
        prompt["filename"] = prompt.get("filename", f"scene_{i+1:03d}.png")
        prompt["audio_filename"] = prompt.get("audio_filename", f"audio_scene_{i+1:03d}.wav")
        prompt["style"] = prompt.get("style", "cinematic, high quality")
    return prompts

def generate_content(pipe, kokoro_pipeline, prompts, config):
    os.makedirs(config.output_dir, exist_ok=True)  # Usar output_dir em vez de output_folder
    content_data = []
    global_seed = random.randint(1, 2147483647)
    for idx, item in enumerate(tqdm(prompts, desc="Gerando conteúdo")):
        full_prompt = f"{item['prompt_image']}, {item['style']}"
        image_path = os.path.join(config.output_dir, item["filename"])
        if not os.path.exists(image_path):
            generator = torch.Generator(config.device).manual_seed(global_seed + idx)
            image = pipe(
                full_prompt,
                width=config.gen_resolution[0],
                height=config.gen_resolution[1],
                num_inference_steps=30,
                guidance_scale=7.5,
                generator=generator
            ).images[0]
            image.save(image_path)
        audio_path = os.path.join(config.output_dir, item["audio_filename"])
        if not os.path.exists(audio_path):
            voice = config.voice
            generator = kokoro_pipeline(item["prompt_audio"], voice=voice)
            for i, (gs, ps, audio) in enumerate(generator):
                sf.write(audio_path, audio, 24000)
                break
        audio_clip = AudioFileClip(audio_path)
        content_data.append({
            "image_path": image_path,
            "audio_path": audio_path,
            "duration": audio_clip.duration,
            "prompt": item["prompt_audio"],
            "audio_clip": audio_clip
        })
        clear_gpu_memory()
    return content_data