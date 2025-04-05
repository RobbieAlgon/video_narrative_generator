import os
import torch

class VideoConfig:
    def __init__(self, video_type, project_name, json_file_path, audio_path=None, voice="pm_alex", output_dir=None, lang_code='p', add_subtitles=False, enable_video_generation=False):
        self.video_type = video_type.lower()
        self.gen_resolution = (1024, 1024)  # Resolução fixa para Playground V2.5
        self.final_resolution = (1080, 1920) if video_type == "short" else (1920, 1080)
        self.duration_min = 15 if video_type == "short" else 60
        self.duration_max = 60 if video_type == "short" else 600
        self.output_filename = f"{'short' if video_type == 'short' else 'video'}_{project_name.replace(' ', '_')}.mp4"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.audio_path = audio_path if audio_path and os.path.exists(audio_path) else None
        self.voice = voice
        self.output_dir = output_dir or "narrative_output"
        self.json_file_path = json_file_path
        self.lang_code = lang_code
        self.add_subtitles = add_subtitles
        self.enable_video_generation = enable_video_generation  # Nova opção para habilitar geração de vídeo