from config import VideoConfig
from models import load_models
from content import process_json_prompts, generate_content, clear_gpu_memory
from video import create_narrative_video
import json
from groq import Groq
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configurar o cliente Grok
API_KEY = "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"
client = Groq(api_key=API_KEY)

def contar_tokens(texto):
    """Conta tokens aproximados (1 token ≈ 1 palavra em inglês)"""
    return len(texto.split())

def limitar_tokens(texto, max_tokens):
    """Garante que o texto não exceda o limite de tokens"""
    tokens = texto.split()
    return " ".join(tokens[:max_tokens])

def gerar_prompt(historia, num_cenas, estilo, tipo):
    """Gera um prompt que enfatiza consistência extrema"""
    return f"""
    Gere EXATAMENTE {num_cenas} cenas em JSON para um vídeo {tipo}.
    HISTÓRIA: {historia}
    ESTILO: {estilo}

    REGRAS ABSOLUTAS:
    1. EXTREMA CONSISTÊNCIA VISUAL ENTRE CENAS:
       - Personagens devem ter EXATAMENTE a mesma aparência em todas as cenas
       - Cenários devem manter os mesmos elementos visuais
       - Use os MESMOS TERMOS para descrever os mesmos elementos

    2. LIMITE DE TOKENS:
       - prompt_image + style deve ter NO MÁXIMO 77 tokens no total
       - Seja conciso mas descritivo

    3. FORMATO EXIGIDO (retorne APENAS JSON):
    {{
      "scenes": [
        {{
          "prompt_image": "descrição visual EM INGLÊS com elementos consistentes",
          "prompt_audio": "narração em português",
          "filename": "scene_001.png",
          "audio_filename": "audio_scene_001.wav",
          "style": "{estilo}"
        }}
      ]
    }}
    """

def aplicar_consistencia(storyboard):
    """Garante consistência e limite de tokens"""
    primeiro_prompt = storyboard["scenes"][0]["prompt_image"]
    termos_chave = []
    for termo in ["woman", "man", "child", "wearing", "holding", "in a"]:
        if termo in primeiro_prompt:
            termos_chave.append(termo)
    
    for i, cena in enumerate(storyboard["scenes"]):
        if i > 0:
            for termo in termos_chave:
                if termo not in cena["prompt_image"]:
                    cena["prompt_image"] += f", {termo}"
        
        combined = f"{cena['prompt_image']}, {cena['style']}"
        if contar_tokens(combined) > 77:
            combined = limitar_tokens(combined, 77)
        parts = combined.rsplit(",", 1)
        cena["prompt_image"] = parts[0].strip()
        if len(parts) > 1:
            cena["style"] = parts[1].strip()
    
    return storyboard

def gerar_storyboard_grok(historia, num_cenas, estilo, tipo):
    """Gera um storyboard ultra-consistente com o Grok"""
    logger.info("Chamando a API do Grok para gerar o storyboard...")
    prompt = gerar_prompt(historia, num_cenas, estilo, tipo)
    resposta = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-70b-8192",
        response_format={"type": "json_object"},
        temperature=0.3
    ).choices[0].message.content
    storyboard = aplicar_consistencia(json.loads(resposta))
    logger.info("Storyboard gerado com sucesso.")
    return storyboard

def criar_pasta_projeto(project_name):
    """Cria uma pasta para o projeto e retorna o caminho"""
    pasta_projeto = os.path.join("projetos", project_name)
    os.makedirs(pasta_projeto, exist_ok=True)
    logger.info(f"Pasta do projeto criada em: {pasta_projeto}")
    return pasta_projeto

def gerar_video(pipe, kokoro_pipeline):
    """Função para gerar um vídeo narrativo"""
    video_type = input("Você quer criar um short ou um vídeo longo? (short/longo): ").lower()
    project_name = input("Nome do projeto: ").replace(" ", "_")
    historia = input("📖 Tema/Narrativa: ").strip()
    num_cenas = int(input("🎬 Número de cenas: "))
    estilo = input("🎨 Estilo visual (ex: 'cyberpunk detailed'): ").strip() or "cinematic"
    
    # Criar pasta para o projeto
    pasta_projeto = criar_pasta_projeto(project_name)
    json_file_path = os.path.join(pasta_projeto, f"{project_name}_prompts.json")
    
    logger.info("Iniciando geração do storyboard ultra-consistente...")
    print("\n⏳ Gerando storyboard ultra-consistente com Grok...")
    json_data = gerar_storyboard_grok(historia, num_cenas, estilo, video_type)
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON salvo em: {json_file_path}")
    print(f"JSON gerado e salvo em: {json_file_path}")

    add_music = input("Adicionar música de fundo? (sim/não): ").lower() in ["sim", "s"]
    audio_path = input("Caminho do arquivo de áudio: ") if add_music else None
    voice = input("Escolha a voz (ex.: pm_alex, pm_santa, pf_dora): ") or "pm_alex"

    logger.info("Iniciando o gerador de vídeo narrativo...")
    print("Iniciando gerador de vídeo narrativo...")
    config = VideoConfig(video_type, project_name, json_file_path, audio_path, voice, output_dir=pasta_projeto)
    prompts = process_json_prompts(config.json_file_path)
    content_data = generate_content(pipe, kokoro_pipeline, prompts, config)
    output_path = create_narrative_video(config, content_data)
    logger.info(f"Vídeo narrativo concluído e salvo em: {output_path}")
    print(f"✅ História narrativa concluída! Vídeo salvo em: {output_path}")
    return output_path

def main():
    logger.info("Iniciando o Video Narrative Generator...")
    print("Bem-vindo ao Video Narrative Generator!")
    
    # Carregar modelos uma vez no início
    pipe, kokoro_pipeline = load_models()
    
    while True:
        try:
            gerar_video(pipe, kokoro_pipeline)
            continuar = input("\nDeseja gerar outro vídeo? (sim/não): ").lower()
            if continuar not in ["sim", "s"]:
                logger.info("Encerrando o programa...")
                print("Encerrando o programa...")
                break
            clear_gpu_memory()
        except Exception as e:
            logger.error(f"Erro durante a execução: {e}", exc_info=True)
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            continuar = input("\nOcorreu um erro. Deseja tentar novamente? (sim/não): ").lower()
            if continuar not in ["sim", "s"]:
                logger.info("Encerrando o programa após erro...")
                print("Encerrando o programa após erro...")
                break
    del pipe
    clear_gpu_memory()

if __name__ == "__main__":
    main()