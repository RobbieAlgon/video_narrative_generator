import os
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip, TextClip, ColorClip, VideoFileClip, VideoClip, CompositeAudioClip
import moviepy.video.fx.all as vfx
import moviepy.config as mp_config
import logging
import random
import cv2

# Configurar logging
logger = logging.getLogger(__name__)

# Verificar e configurar o caminho do ImageMagick
if not mp_config.IMAGEMAGICK_BINARY:
    mp_config.IMAGEMAGICK_BINARY = "/usr/bin/convert"  # Caminho padrão no Colab após instalação

def should_use_video():
    """Decide se deve usar vídeo ou imagem para uma cena"""
    return random.random() < 0.3  # 30% de chance de usar vídeo

def generate_video_clip(prompt, duration, final_resolution):
    """Gera um clipe de vídeo usando IA"""
    # TODO: Implementar geração de vídeo com Stable Video Diffusion ou outro modelo
    # Por enquanto, retornamos um clipe de teste
    logger.info(f"Gerando vídeo para o prompt: {prompt}")
    # Aqui você implementaria a chamada para o modelo de geração de vídeo
    # Por exemplo:
    # video_path = stable_video_diffusion.generate(prompt, duration)
    # return VideoFileClip(video_path)
    return None  # Placeholder até implementar a geração real

def apply_ken_burns_effect(img_clip, duration, final_resolution):
    width, height = final_resolution
    
    # Redimensionar a imagem para preencher a resolução final, mantendo proporção
    img_ratio = img_clip.w / img_clip.h
    target_ratio = width / height
    
    # Para shorts (vertical), priorizamos a largura
    if height > width:  # Modo vertical (short)
        new_width = width
        new_height = int(width / img_ratio)
        if new_height < height:  # Se altura for menor que o alvo
            new_height = height
            new_width = int(height * img_ratio)
    else:  # Modo horizontal (longo)
        if img_ratio > target_ratio:
            new_height = height
            new_width = int(height * img_ratio)
        else:
            new_width = width
            new_height = int(width / img_ratio)
    
    # Redimensionar mantendo proporção
    img_clip = img_clip.resize((new_width, new_height))
    
    # Aplicar efeito Ken Burns (zoom e movimento)
    zoom_factor = 1.1
    start_size = (int(new_width * zoom_factor), int(new_height * zoom_factor))
    end_size = (new_width, new_height)
    
    # Calcular posições iniciais e finais para centralizar
    start_pos = ((start_size[0] - width) // 2, (start_size[1] - height) // 2)
    end_pos = ((end_size[0] - width) // 2, (end_size[1] - height) // 2)
    
    clip = (img_clip
            .resize(start_size)
            .set_position(lambda t: (
                start_pos[0] - (start_pos[0] - end_pos[0]) * (t / duration),
                start_pos[1] - (start_pos[1] - end_pos[1]) * (t / duration)
            ))
            .resize(lambda t: (
                start_size[0] - (start_size[0] - end_size[0]) * (t / duration),
                start_size[1] - (start_size[1] - end_size[1]) * (t / duration)
            ))
            .set_duration(duration))
    
    # Garantir que o clipe final tenha a resolução exata
    return clip.crop(x_center=width/2, y_center=height/2, width=width, height=height)

def create_dynamic_subtitles(text, duration, final_resolution):
    """Cria legendas dinâmicas com mudança de cor por palavra"""
    logger.info(f"Gerando legendas para o texto: '{text}' com duração {duration}s")
    width, height = final_resolution
    words = text.split()
    word_duration = duration / len(words)
    
    # Criar clipes de texto para cada palavra
    text_clips = []
    colors = ['yellow', 'cyan', 'magenta', 'white', 'green']
    
    for i, word in enumerate(words):
        start_time = i * word_duration
        end_time = (i + 1) * word_duration
        
        # Criar clipe de texto para cada palavra
        txt_clip = TextClip(
            word,
            fontsize=40,
            font='Arial-Bold',
            color=colors[i % len(colors)],
            stroke_color='black',
            stroke_width=2
        )
        
        # Posicionar o texto na parte inferior da tela
        txt_clip = txt_clip.set_position(('center', height - 100))
        txt_clip = txt_clip.set_start(start_time)
        txt_clip = txt_clip.set_end(end_time)
        txt_clip = txt_clip.set_duration(word_duration)
        
        text_clips.append(txt_clip)
    
    # Combinar apenas os clipes de texto
    subtitle_composite = CompositeVideoClip(text_clips, size=final_resolution)
    return subtitle_composite

def create_scene_clip(item, config):
    """Cria um clipe de cena com efeitos dinâmicos"""
    logger.info(f"Conteúdo do item: {item}")
    
    # Verificar se temos o caminho da imagem
    image_path = item.get("image_path") or item.get("filename", "")
    if not image_path or not os.path.exists(image_path):
        raise FileNotFoundError(f"Arquivo de imagem não encontrado: {image_path}")
    
    logger.info(f"Criando clipe para a cena: {image_path}")
    
    # Criar clipe da imagem
    clip = ImageClip(image_path)
    
    # Garantir que a imagem preencha toda a tela
    clip = clip.resize(width=config.final_resolution[0], height=config.final_resolution[1])
    
    # Aplicar efeitos dinâmicos
    zoom_factor = 1.2  # Zoom de 20%
    zoom_duration = item["duration"]
    
    # Criar função de zoom e movimento
    def zoom_and_move(t):
        # Zoom progressivo
        zoom = 1 + (zoom_factor - 1) * (t / zoom_duration)
        
        # Movimento suave (pan)
        x_offset = (t / zoom_duration) * 0.1  # 10% de movimento horizontal
        y_offset = (t / zoom_duration) * 0.05  # 5% de movimento vertical
        
        return zoom, x_offset, y_offset
    
    # Aplicar os efeitos
    def apply_effects(get_frame, t):
        zoom, x_offset, y_offset = zoom_and_move(t)
        frame = get_frame(t)
        
        # Aplicar zoom
        h, w = frame.shape[:2]
        new_h, new_w = int(h * zoom), int(w * zoom)
        frame = cv2.resize(frame, (new_w, new_h))
        
        # Aplicar movimento
        x = int(x_offset * w)
        y = int(y_offset * h)
        frame = frame[y:y+h, x:x+w]
        
        return frame
    
    # Criar clipe com efeitos
    dynamic_clip = clip.fl(lambda gf, t: apply_effects(gf, t))
    dynamic_clip = dynamic_clip.set_duration(zoom_duration)
    
    return dynamic_clip

def create_narrative_video(config, content_data):
    logger.info(f"Iniciando criação do vídeo com add_subtitles={config.add_subtitles}")
    logger.info(f"Conteúdo recebido: {content_data}")
    clips = []
    
    for i, item in enumerate(content_data):
        try:
            # Verificar se temos todos os dados necessários
            if not item.get("duration"):
                raise ValueError(f"Cena {i+1} não tem duração definida")
            if not item.get("audio_clip"):
                raise ValueError(f"Cena {i+1} não tem áudio definido")
            
            # Criar clipe da cena principal
            scene_clip = create_scene_clip(item, config)
            audio_clip = item["audio_clip"]
            
            # Verificar se os clipes foram criados corretamente
            if not isinstance(scene_clip, (ImageClip, VideoClip)):
                raise ValueError(f"Clipe da cena {i+1} não foi criado corretamente")
            if not isinstance(audio_clip, AudioFileClip):
                raise ValueError(f"Áudio da cena {i+1} não foi criado corretamente")
            
            # Garantir que o clipe principal preencha toda a tela
            scene_clip = scene_clip.resize(config.final_resolution)
            
            # Adicionar áudio apenas à cena atual
            scene = scene_clip.set_audio(audio_clip)
            
            # Adicionar fade in/out suave
            scene = scene.fadein(0.5).fadeout(0.5)
            
            if config.add_subtitles:
                logger.info(f"Adicionando legendas para a cena {i+1}")
                subtitle_clip = create_dynamic_subtitles(item["prompt"], item["duration"], config.final_resolution)
                
                # Combinar cena principal com legendas
                scene = CompositeVideoClip(
                    [scene, subtitle_clip],
                    size=config.final_resolution
                )
            
            clips.append(scene)
        except Exception as e:
            logger.error(f"Erro ao processar cena {i+1}: {e}")
            raise
    
    # Verificar se temos clipes para concatenar
    if not clips:
        raise ValueError("Nenhum clipe válido foi criado")
    
    # Aplicar transições suaves entre cenas
    final_clips = []
    for i, clip in enumerate(clips):
        if i == 0:
            final_clips.append(clip)
        else:
            # Criar transição suave entre cenas
            transition_duration = 0.8  # 0.8 segundos de transição
            clip1 = clips[i-1].crossfadeout(transition_duration)
            clip2 = clip.crossfadein(transition_duration)
            
            # Combinar os clipes com transição
            transition = CompositeVideoClip(
                [clip1, clip2],
                size=config.final_resolution
            ).set_duration(clips[i-1].duration + transition_duration)
            
            final_clips.append(transition)
    
    # Concatenar todos os clipes
    final_video = concatenate_videoclips(final_clips, method="compose")
    
    # Adicionar música de fundo se especificada
    if config.audio_path:
        bg_audio = AudioFileClip(config.audio_path).volumex(0.2).audio_fadeout(2)
        bg_audio = bg_audio.loop(duration=final_video.duration) if bg_audio.duration < final_video.duration else bg_audio.subclip(0, final_video.duration)
        final_audio = CompositeAudioClip([final_video.audio, bg_audio])
        final_video = final_video.set_audio(final_audio)
    
    output_path = os.path.join(config.output_dir, config.output_filename)
    print(f"Renderizando vídeo... Duração total: {final_video.duration:.2f}s")
    final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", bitrate="4000k", threads=4)
    print(f"Vídeo narrativo salvo em: {output_path}")
    return output_path