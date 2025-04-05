import os
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip, TextClip, ColorClip, VideoFileClip, VideoClip
import moviepy.video.fx.all as vfx
import moviepy.config as mp_config
import logging
import random

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
    """Cria um clipe de cena com zoom e efeitos"""
    logger.info(f"Conteúdo do item: {item}")  # Log para debug
    
    # Verificar se temos o caminho da imagem
    image_path = item.get("image_path") or os.path.join(config.output_dir, item.get("filename", ""))
    if not image_path or not os.path.exists(image_path):
        raise FileNotFoundError(f"Arquivo de imagem não encontrado: {image_path}")
    
    logger.info(f"Criando clipe para a cena: {image_path}")
    
    # Criar clipe da imagem
    clip = ImageClip(image_path)
    
    # Garantir que a imagem preencha toda a tela
    clip = clip.resize(width=config.final_resolution[0], height=config.final_resolution[1])
    
    # Aplicar zoom suave
    zoom_factor = 1.1
    zoom_duration = item["duration"]
    
    def make_frame(t):
        current_zoom = 1 + (zoom_factor - 1) * (t / zoom_duration)
        return clip.resize(width=int(config.final_resolution[0] * current_zoom),
                          height=int(config.final_resolution[1] * current_zoom))
    
    # Criar clipe com zoom
    zoom_clip = VideoClip(make_frame, duration=zoom_duration)
    
    # Garantir que o clipe final tenha a resolução correta
    zoom_clip = zoom_clip.resize(config.final_resolution)
    
    return zoom_clip

def create_narrative_video(config, content_data):
    logger.info(f"Iniciando criação do vídeo com add_subtitles={config.add_subtitles}")
    logger.info(f"Conteúdo recebido: {content_data}")  # Log para debug
    clips = []
    
    for i, item in enumerate(content_data):
        try:
            # Criar clipe da cena principal
            scene_clip = create_scene_clip(item, config)
            audio_clip = item["audio_clip"]
            
            # Garantir que o clipe principal preencha toda a tela
            scene_clip = scene_clip.resize(config.final_resolution)
            scene = scene_clip.set_audio(audio_clip)
            
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
    
    # Aplicar transições
    for i, clip in enumerate(clips):
        if i == 0:
            clips[i] = clip.fadein(0.5)
        if i == len(clips) - 1:
            clips[i] = clip.fadeout(0.8)
        elif i < len(clips) - 1:
            crossfade_duration = min(0.5, clips[i].duration / 4, clips[i+1].duration / 4)
            if crossfade_duration > 0:
                clips[i] = clips[i].crossfadeout(crossfade_duration)
                clips[i+1] = clips[i+1].crossfadein(crossfade_duration)
    
    # Concatenar todos os clipes
    final_video = concatenate_videoclips(clips, method="compose")
    
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