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


########################################################################3
#########################################################################

# 1. Primeiro, garanta que estamos no diretório /content
!### COMO RODAR O PROGRAMA
# 3. Clone o repositório novamente
!git clone https://github.com/RobbieAlgon/video_narrative_generator.git

# 4. Entre no diretório do projeto (usando %cd para garantir que funcione)
%cd /content/video_narrative_generator

# 5. Instale as dependências
!pip install -r requirements.txt

# 6. Liste os arquivos para verificar se main.py está presente
!ls -la

# Instalar ImageMagick
!apt-get update -qq
!apt-get install -y imagemagick

# Verificar instalação do ImageMagick
!convert --version

# Instalar espeak-ng (necessário para Kokoro)
!apt-get -qq -y install espeak-ng > /dev/null 2>&1

# Criar um novo policy.xml com permissões relaxadas
policy_content = """
<policymap>
  <policy domain="coder" rights="read|write" pattern="PS" />
  <policy domain="coder" rights="read|write" pattern="PNG" />
  <policy domain="coder" rights="read|write" pattern="TEXT" />
  <policy domain="path" rights="read|write" pattern="@*" />
  <policy domain="path" rights="read|write" pattern="/tmp/*" />
  <policy domain="resource" name="memory" value="2GiB"/>
  <policy domain="resource" name="map" value="2GiB"/>
  <policy domain="resource" name="area" value="1GB"/>
  <policy domain="resource" name="disk" value="4GiB"/>
</policymap>
"""

# Escrever o novo policy.xml e substituir o original
with open("/content/custom_policy.xml", "w") as f:
    f.write(policy_content)
!sudo cp /content/custom_policy.xml /etc/ImageMagick-6/policy.xml

# Verificar se a política foi aplicada
print("Política de 'path' após substituição:")
!cat /etc/ImageMagick-6/policy.xml | grep "path"

# Testar o ImageMagick com um comando simples
!echo "Teste" | convert label:@- test.png && ls test.png || echo "Erro ao criar test.png"

# 7. Execute o programa
!python main.py
