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

# Mapeamento de idiomas e vozes disponíveis
IDIOMAS = {
    'a': {'nome': 'inglês americano', 'vozes': ['af_heart', 'af_alloy', 'af_aoede', 'af_bella', 'af_jessica', 'af_korean', 'af_nicole', 'af_nova', 'af_river', 'af_sarah', 'af_sky', 'am_adam', 'am_echo', 'am_eric', 'am_fenrir', 'am_liam', 'am_michael', 'am_onyx', 'am_rhythm', 'am_santa']},
    'b': {'nome': 'inglês britânico', 'vozes': ['bf_alice', 'bf_emma', 'bf_isabella', 'bf_lily', 'bm_daniel', 'bm_fable', 'bm_george', 'bm_lewis']},
    'j': {'nome': 'japonês', 'vozes': ['jf_alpha', 'jf_gongitsune', 'jf_nezumi', 'jf_tebukuro', 'jm_kumo']},
    'z': {'nome': 'chinês mandarim', 'vozes': ['zf_xiaobei', 'zf_xiaoni', 'zf_xiaoxiao', 'zf_xiaoyi', 'zm_yunjian', 'zm_yunxi', 'zm_yunxia', 'zm_yunyang']},
    'e': {'nome': 'espanhol', 'vozes': ['ef_dora', 'em_alex', 'em_santa']},
    'f': {'nome': 'francês', 'vozes': ['ff_siwis']},
    'h': {'nome': 'hindi', 'vozes': ['hf_alpha', 'hf_beta', 'hm_omega', 'hm_psi']},
    'i': {'nome': 'italiano', 'vozes': ['if_sara', 'im_nicola']},
    'p': {'nome': 'português do Brasil', 'vozes': ['pf_dora', 'pm_alex', 'pm_santa']}
}

def contar_tokens(texto):
    """Conta tokens aproximados (1 token ≈ 1 palavra em inglês)"""
    return len(texto.split())

def limitar_tokens(texto, max_tokens):
    """Garante que o texto não exceda o limite de tokens"""
    tokens = texto.split()
    return " ".join(tokens[:max_tokens])

def gerar_prompt(historia, num_cenas, estilo, tipo, lang_code='p'):
    """Gera um prompt que enfatiza consistência extrema e narração adequada"""
    idioma_nome = IDIOMAS.get(lang_code, IDIOMAS['p'])['nome']
    return f"""
    Gere EXATAMENTE {num_cenas} cenas em JSON para um vídeo {tipo}.
    HISTÓRIA: {historia}
    ESTILO: {estilo}

    REGRAS ABSOLUTAS:
    1. EXTREMA CONSISTÊNCIA VISUAL ENTRE CENAS:
       - Personagens devem ter EXATAMENTE a mesma aparência em todas as cenas
       - Cenários devem manter os mesmos elementos visuais
       - Use os MESMOS TERMOS para descrever os mesmos elementos visuais

    2. DIFERENCIAÇÃO ENTRE IMAGEM E ÁUDIO:
       - 'prompt_image': Descrição visual detalhada EM INGLÊS para gerar a imagem, focada em elementos visuais consistentes
       - 'prompt_audio': Narração narrativa em {idioma_nome} que avança a história de forma natural, NÃO descreva a cena visual, mas sim o contexto, emoções ou eventos da narrativa

    3. LIMITE DE TOKENS:
       - prompt_image + style deve ter NO MÁXIMO 77 tokens no total
       - Seja conciso mas descritivo no prompt_image

    4. FORMATO EXIGIDO (retorne APENAS JSON):
    {{
      "scenes": [
        {{
          "prompt_image": "descrição visual EM INGLÊS com elementos consistentes",
          "prompt_audio": "narração em {idioma_nome} que avança a história",
          "filename": "scene_001.png",
          "audio_filename": "audio_scene_001.wav",
          "style": "{estilo}"
        }}
      ]
    }}

    EXEMPLO:
    - prompt_image: "A man in a red jacket walking through a dense forest, cinematic"
    - prompt_audio: "Ele sentia o peso da aventura ao entrar na floresta." (em português)
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

def gerar_storyboard_grok(historia, num_cenas, estilo, tipo, lang_code='p'):
    """Gera um storyboard ultra-consistente com o Grok"""
    logger.info("Chamando a API do Grok para gerar o storyboard...")
    prompt = gerar_prompt(historia, num_cenas, estilo, tipo, lang_code)
    resposta = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="meta-llama/llama-4-scout-17b-16e-instruct",
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
    """Função para gerar um vídeo narrativo com ordem de inputs ajustada"""
    print("\n=== Novo Vídeo ===")
    print("Escolha o idioma da narração (a: inglês americano, b: inglês britânico, j: japonês, z: chinês, e: espanhol, f: francês, h: hindi, i: italiano, p: português): ")
    lang_code = input().lower()
    if lang_code not in IDIOMAS:
        print(f"Idioma '{lang_code}' não suportado. Usando português (p) como padrão.")
        lang_code = 'p'
    
    video_type = input("Escolha o tipo de vídeo (short/longo): ").lower()
    project_name = input("Nome do projeto: ").replace(" ", "_")
    historia = input("📖 Tema/Narrativa: ").strip()
    num_cenas = int(input("🎬 Número de cenas: "))
    estilo = input("🎨 Estilo visual (ex: 'cyberpunk detailed', padrão 'cinematic'): ").strip() or "cinematic"
    
    # Mostrar vozes disponíveis e escolher
    vozes = IDIOMAS[lang_code]['vozes']
    idioma_nome = IDIOMAS[lang_code]['nome']
    print(f"Vozes disponíveis para {idioma_nome}: {', '.join(vozes)}")
    voice = input(f"Escolha a voz para {idioma_nome} (padrão '{vozes[0]}'): ") or vozes[0]
    if voice not in vozes:
        print(f"Voz '{voice}' não disponível. Usando {vozes[0]} como padrão.")
        voice = vozes[0]
    
    # Música de fundo
    add_music = input("Adicionar música de fundo? (sim/não): ").lower() in ["sim", "s"]
    audio_path = input("Caminho do arquivo de áudio (ex: '/content/musica.mp3'): ") if add_music else None
    
    # Legendas dinâmicas
    add_subtitles = input("Adicionar legendas dinâmicas? (sim/não): ").lower() in ["sim", "s"]
    logger.info(f"Opção de legendas escolhida: {add_subtitles}")
    
    # Geração de vídeo
    enable_video = input("Habilitar geração de vídeos dinâmicos? (sim/não): ").lower() in ["sim", "s"]
    logger.info(f"Opção de geração de vídeo escolhida: {enable_video}")
    
    # Criar pasta para o projeto
    pasta_projeto = criar_pasta_projeto(project_name)
    json_file_path = os.path.join(pasta_projeto, f"{project_name}_prompts.json")
    
    logger.info("Iniciando geração do storyboard...")
    print("\n⏳ Gerando storyboard ultra-consistente com Grok...")
    json_data = gerar_storyboard_grok(historia, num_cenas, estilo, video_type, lang_code)
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON salvo em: {json_file_path}")
    print(f"JSON gerado e salvo em: {json_file_path}")

    logger.info("Iniciando o gerador de vídeo narrativo...")
    print("Iniciando gerador de vídeo narrativo...")
    config = VideoConfig(video_type, project_name, json_file_path, audio_path, voice, output_dir=pasta_projeto, lang_code=lang_code, add_subtitles=add_subtitles, enable_video_generation=enable_video)
    logger.info(f"Configuração de legendas no VideoConfig: {config.add_subtitles}")
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
    pipe, kokoro_pipeline = None, None
    
    while True:
        try:
            if pipe is None or kokoro_pipeline is None:
                print("Carregando modelos pela primeira vez ou após mudança de idioma...")
                lang_code_temp = input("Escolha o idioma inicial (a: inglês americano, b: inglês britânico, j: japonês, z: chinês, e: espanhol, f: francês, h: hindi, i: italiano, p: português): ").lower()
                if lang_code_temp not in IDIOMAS:
                    lang_code_temp = 'p'
                pipe, kokoro_pipeline = load_models(lang_code_temp)
            
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
