import os
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip, TextClip, ColorClip
import moviepy.video.fx.all as vfx
import moviepy.config as mp_config
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Verificar e configurar o caminho do ImageMagick
if not mp_config.IMAGEMAGICK_BINARY:
    mp_config.IMAGEMAGICK_BINARY = "/usr/bin/convert"  # Caminho padrão no Colab após instalação

def apply_ken_burns_effect(img_clip, duration, final_resolution):
    width, height = final_resolution
    
    # Redimensionar a imagem para preencher a resolução final, mantendo proporção
    if width > height:  # Modo longo (1920x1080)
        img_clip = img_clip.resize(height=height)  # Ajusta altura primeiro
        if img_clip.w < width:  # Se largura ainda for menor, ajusta
            img_clip = img_clip.resize(width=width)
    else:  # Modo short (1080x1920)
        img_clip = img_clip.resize(height=height)  # Ajusta altura primeiro
        if img_clip.w < width:  # Se largura for menor, ajusta
            img_clip = img_clip.resize(width=width)
    
    # Garantir que a imagem preencha a tela inteira (corta excesso se necessário)
    img_clip = img_clip.resize((width, height)) if img_clip.w != width or img_clip.h != height else img_clip
    
    # Aplicar efeito Ken Burns (zoom e movimento)
    zoom_factor = 1.2
    start_size = (int(width * zoom_factor), int(height * zoom_factor))
    end_size = (width, height)
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
    
    subtitle_clips = []
    colors = ['yellow', 'cyan', 'magenta', 'white', 'green']
    
    # Posicionar legendas a 10% da altura a partir da base
    subtitle_y = height * 0.9  # 90% da altura (perto da base)
    
    for i, word in enumerate(words):
        start_time = i * word_duration
        end_time = (i + 1) * word_duration
        logger.info(f"Criando TextClip para '{word}' ({start_time}s - {end_time}s)")
        
        try:
            txt_clip = (TextClip(word, fontsize=70, font='Arial-Bold', color=colors[i % len(colors)], 
                                 stroke_color='black', stroke_width=2)
                        .set_position(('center', subtitle_y - 50))  # Ajuste relativo
                        .set_start(start_time)
                        .set_end(end_time)
                        .set_duration(word_duration))
            subtitle_clips.append(txt_clip)
        except Exception as e:
            logger.error(f"Erro ao criar TextClip para '{word}': {e}")
            raise
    
    # Fundo semi-transparente
    bg_clip = (ColorClip(size=(width, 100), color=(0, 0, 0))
               .set_opacity(0.6)
               .set_position(('center', subtitle_y - 75))
               .set_duration(duration))
    
    composite_clip = CompositeVideoClip([bg_clip] + subtitle_clips)
    logger.info(f"Legendas criadas com {len(subtitle_clips)} palavras")
    return composite_clip

def create_narrative_video(config, content_data):
    logger.info(f"Iniciando criação do vídeo com add_subtitles={config.add_subtitles}")
    clips = []
    total_duration = 0
    
    for i, item in enumerate(content_data):
        if not os.path.exists(item["image_path"]):
            raise FileNotFoundError(f"Imagem não encontrada: {item['image_path']}")
        img_clip = ImageClip(item["image_path"])
        if img_clip is None:
            raise ValueError(f"Falha ao carregar imagem: {item['image_path']}")
        img_clip_with_effect = apply_ken_burns_effect(img_clip, item["duration"], config.final_resolution)
        audio_clip = item["audio_clip"]
        scene = img_clip_with_effect.set_audio(audio_clip)
        
        if config.add_subtitles:
            logger.info(f"Adicionando legendas para a cena {i+1} com prompt: '{item['prompt']}'")
            subtitle_clip = create_dynamic_subtitles(item["prompt"], item["duration"], config.final_resolution)
            scene = CompositeVideoClip([scene, subtitle_clip])
            logger.info(f"Legendas adicionadas à cena {i+1}")
        
        clips.append(scene)
        total_duration += item["duration"]
    
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
    
    final_video = concatenate_videoclips(clips, method="compose")
    if config.audio_path:
        bg_audio = AudioFileClip(config.audio_path).volumex(0.2).audio_fadeout(2)
        bg_audio = bg_audio.loop(duration=final_video.duration) if bg_audio.duration < final_video.duration else bg_audio.subclip(0, final_video.duration)
        final_audio = CompositeVideoClip([final_video.audio, bg_audio])
        final_video = final_video.set_audio(final_audio)
    
    output_path = os.path.join(config.output_dir, config.output_filename)
    print(f"Renderizando vídeo... Duração total: {final_video.duration:.2f}s")
    final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", bitrate="4000k", threads=4)
    print(f"Vídeo narrativo salvo em: {output_path}")
    return output_path