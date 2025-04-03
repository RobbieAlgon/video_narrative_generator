# Video Narrative Generator

Este projeto é um gerador de vídeos narrativos que utiliza inteligência artificial para criar vídeos a partir de prompts de texto. Ele combina imagens geradas pelo **Stable Diffusion XL** com narração em áudio gerada pelo **Kokoro**, aplicando efeitos como o Ken Burns para criar vídeos curtos ou longos.

## Funcionalidades
- Geração de imagens a partir de prompts de texto.
- Síntese de voz em português com o modelo Kokoro.
- Montagem de vídeos com transições suaves e efeito Ken Burns.
- Suporte para música de fundo opcional.

## Pré-requisitos
Antes de usar o projeto, você precisa:
- Python 3.8 ou superior instalado.
- Git instalado para clonar o repositório.
- Uma GPU é recomendada para acelerar a geração de imagens (opcional, funciona em CPU também).
- Sistema operacional: Windows, macOS ou Linux.

## Instalação
Siga os passos abaixo para instalar e configurar o projeto localmente:

### 1. Clonar o Repositório
Clone este repositório para o seu computador:
```bash
git clone https://github.com/RobbieAlgon/video_narrative_generator.git
cd video_narrative_generator

pip install -r requirements.txt

Para o Kokoro funcionar corretamente, instale também o espeak-ng:
Linux: sudo apt-get install espeak-ng

Windows: Baixe e instale o eSpeak NG.

macOS: brew install espeak (se tiver Homebrew instalado).


##GOOGLE COLAB

# Clonar o repositório
!git clone https://github.com/RobbieAlgon/video_narrative_generator.git
%cd video_narrative_generator

# Instalar dependências
!pip install -r requirements.txt
!apt-get -qq -y install espeak-ng > /dev/null 2>&1

# Rodar o main.py
!python main.py
