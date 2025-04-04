import json
from groq import Groq
from datetime import datetime

# Configurações
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

    DICAS:
    - Descreva personagens UMA ÚNICA FORMA em todas as cenas
    - Use cores e iluminação consistentes
    - Mantenha o mesmo nível de detalhe
    - Exemplo de consistência:
      Cena 1: "young woman with long black hair, blue eyes, red jacket in futuristic city"
      Cena 2: "young woman with long black hair, blue eyes, red jacket now running..."
    """

def aplicar_consistencia(storyboard):
    """Garante consistência e limite de tokens"""
    primeiro_prompt = storyboard["scenes"][0]["prompt_image"]
    
    # Identifica termos recorrentes na primeira cena
    termos_chave = []
    for termo in ["woman", "man", "child", "wearing", "holding", "in a"]:
        if termo in primeiro_prompt:
            termos_chave.append(termo)
    
    # Aplica consistência nas cenas subsequentes
    for i, cena in enumerate(storyboard["scenes"]):
        # Mantém os termos chave consistentes
        if i > 0:
            for termo in termos_chave:
                if termo not in cena["prompt_image"]:
                    cena["prompt_image"] += f", {termo}"
        
        # Combina prompt_image + style e limita tokens
        combined = f"{cena['prompt_image']}, {cena['style']}"
        if contar_tokens(combined) > 77:
            combined = limitar_tokens(combined, 77)
        
        # Separa novamente
        parts = combined.rsplit(",", 1)
        cena["prompt_image"] = parts[0].strip()
        if len(parts) > 1:
            cena["style"] = parts[1].strip()
    
    return storyboard

def gerar_storyboard():
    print("\n⚡ GERADOR DE STORYBOARD ULTRA-CONSISTENTE ⚡")
    print("(Otimizado para SDXL com 77 tokens max)\n")
    
    try:
        # Entrada do usuário
        historia = input("📖 Tema/Narrativa: ").strip()
        num_cenas = int(input("🎬 Número de cenas: "))
        estilo = input("🎨 Estilo visual (ex: 'cyberpunk detailed'): ").strip()
        tipo = input("📺 Tipo de vídeo: ").strip()
        
        # Gera prompt com ênfase em consistência
        prompt = gerar_prompt(historia, num_cenas, estilo, tipo)
        
        print("\n⏳ Gerando storyboard ultra-consistente...")
        
        # Chamada à API
        resposta = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192",
            response_format={"type": "json_object"},
            temperature=0.3  # Baixa temperatura = mais consistência
        ).choices[0].message.content
        
        # Processamento
        dados = json.loads(resposta)
        storyboard = aplicar_consistencia(dados)
        
        # Salvamento
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"ultra_consistent_{timestamp}.json"
        
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            json.dump(storyboard, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ Storyboard gerado em '{nome_arquivo}'")
        print(f"👉 Tokens por cena: {contar_tokens(storyboard['scenes'][0]['prompt_image'] + ' ' + storyboard['scenes'][0]['style'])}/77")
        
        # Preview
        print("\n🔍 Preview da primeira cena:")
        print(f"Imagem: {storyboard['scenes'][0]['prompt_image'][:60]}...")
        print(f"Estilo: {storyboard['scenes'][0]['style']}")
        print(f"Áudio: {storyboard['scenes'][0]['prompt_audio'][:60]}...")
        
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")

if __name__ == "__main__":
    gerar_storyboard()