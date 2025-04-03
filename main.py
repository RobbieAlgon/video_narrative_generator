from config import VideoConfig
from models import load_models
from content import process_json_prompts, generate_content, clear_gpu_memory
from video import create_narrative_video

def main():
    try:
        video_type = input("Você quer criar um short ou um vídeo longo? (short/longo): ").lower()
        project_name = input("Nome do projeto: ").replace(" ", "_")
        json_file_path = input("Caminho do arquivo JSON com prompts: ") or "narrative_prompts.json"
        add_music = input("Adicionar música de fundo? (sim/não): ").lower() in ["sim", "s"]
        audio_path = input("Caminho do arquivo de áudio: ") if add_music else None
        voice = input("Escolha a voz (ex.: pm_alex, pm_santa, pf_dora): ") or "pm_alex"

        print("Iniciando gerador de vídeo narrativo...")
        config = VideoConfig(video_type, project_name, json_file_path, audio_path, voice)
        prompts = process_json_prompts(config.json_file_path)
        pipe, kokoro_pipeline = load_models()
        content_data = generate_content(pipe, kokoro_pipeline, prompts, config)
        del pipe
        clear_gpu_memory()
        output_path = create_narrative_video(config, content_data)
        print("✅ História narrativa concluída!")
        return output_path
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()