import os
import numpy as np
from moviepy.editor import (
    ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip,
    TextClip, ColorClip, VideoFileClip, VideoClip, CompositeAudioClip,
    TransitionVideo, vfx
)
import moviepy.video.fx.all as vfx
import moviepy.audio.fx.all as afx
import moviepy.config as mp_config
import logging
import random
import cv2
from scipy.interpolate import interp1d

# Configurar logging
logger = logging.getLogger(__name__)

# Verificar e configurar o caminho do ImageMagick
if not mp_config.IMAGEMAGICK_BINARY:
    mp_config.IMAGEMAGICK_BINARY = "/usr/bin/convert"  # Caminho padrão no Colab após instalação

# Efeitos cinematográficos avançados
class CinematicEffects:
    @staticmethod
    def film_grain(clip, intensity=0.05):
        """Adiciona grão de filme cinematográfico"""
        def add_grain(image):
            grain = np.random.normal(0, intensity, image.shape)
            noisy_image = np.clip(image + grain, 0, 255).astype('uint8')
            return noisy_image
        
        return clip.fl_image(add_grain)
    
    @staticmethod
    def cinematic_color_grading(clip, style="drama"):
        """Aplicar color grading cinematográfico"""
        styles = {
            "drama": {"contrast": 1.2, "saturation": 0.85, "brightness": 0.95, "temp": 0.95},
            "thriller": {"contrast": 1.3, "saturation": 0.7, "brightness": 0.8, "temp": 0.8},
            "romance": {"contrast": 1.1, "saturation": 1.1, "brightness": 1.05, "temp": 1.05},
            "sci_fi": {"contrast": 1.15, "saturation": 0.9, "brightness": 0.9, "temp": 1.2}
        }
        
        params = styles.get(style, styles["drama"])
        
        # Aplicar ajustes de cor
        graded_clip = clip.fx(vfx.colorx, params["contrast"])  # Contraste
        
        # Ajuste de saturação
        def adjust_saturation(image):
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(float)
            hsv[:,:,1] = hsv[:,:,1] * params["saturation"]
            hsv[:,:,1] = np.clip(hsv[:,:,1], 0, 255)
            return cv2.cvtColor(hsv.astype('uint8'), cv2.COLOR_HSV2RGB)
        
        # Ajuste de brilho
        def adjust_brightness(image):
            return np.clip(image * params["brightness"], 0, 255).astype('uint8')
        
        # Ajuste de temperatura
        def adjust_temp(image):
            # Aumenta o azul (mais frio) ou vermelho (mais quente)
            b, g, r = cv2.split(image)
            if params["temp"] < 1:  # Mais frio (azulado)
                b = np.clip(b * (2 - params["temp"]), 0, 255).astype('uint8')
            else:  # Mais quente (avermelhado)
                r = np.clip(r * params["temp"], 0, 255).astype('uint8')
            return cv2.merge([b, g, r])
        
        # Aplicar efeitos em sequência
        graded_clip = graded_clip.fl_image(adjust_saturation)
        graded_clip = graded_clip.fl_image(adjust_brightness)
        graded_clip = graded_clip.fl_image(adjust_temp)
        
        return graded_clip
    
    @staticmethod
    def vignette_effect(clip, intensity=0.3):
        """Adiciona efeito de vinheta cinematográfica"""
        def add_vignette(image):
            height, width = image.shape[:2]
            x = np.linspace(-1, 1, width)
            y = np.linspace(-1, 1, height)
            X, Y = np.meshgrid(x, y)
            radius = np.sqrt(X**2 + Y**2)
            
            # Criar máscara de vinheta
            vignette = np.clip(1 - intensity * radius, 0, 1)
            vignette = np.dstack([vignette] * 3)  # Aplicar aos 3 canais RGB
            
            # Aplicar vinheta
            return np.clip(image * vignette, 0, 255).astype('uint8')
        
        return clip.fl_image(add_vignette)
    
    @staticmethod
    def depth_of_field(clip, focus_point=(0.5, 0.5), blur_intensity=5):
        """Simula profundidade de campo com desfoque gradual"""
        def apply_dof(image):
            height, width = image.shape[:2]
            focus_x, focus_y = int(width * focus_point[0]), int(height * focus_point[1])
            
            # Criar máscara de distância do ponto focal
            Y, X = np.ogrid[:height, :width]
            dist_from_focus = np.sqrt((X - focus_x)**2 + (Y - focus_y)**2)
            max_dist = np.sqrt(width**2 + height**2) / 2
            blur_amount = np.clip(dist_from_focus / max_dist, 0, 1) * blur_intensity
            
            # Aplicar desfoque variável baseado na distância
            result = image.copy()
            for blur in range(1, int(blur_intensity) + 1, 2):
                mask = (blur_amount >= blur - 1) & (blur_amount < blur + 1)
                if not np.any(mask):
                    continue
                    
                blurred = cv2.GaussianBlur(image, (blur * 2 + 1, blur * 2 + 1), 0)
                result[mask] = blurred[mask]
                
            return result
            
        return clip.fl_image(apply_dof)

def create_cinematic_transitions(clip1, clip2, transition_type="fade", duration=1.0):
    """Cria transições cinematográficas entre cenas"""
    if transition_type == "fade":
        # Crossfade clássico do cinema
        return clip1.crossfadeout(duration).crossfadein(clip2, duration)
    
    elif transition_type == "wipe":
        # Transição de varredura, estilo Star Wars
        def make_frame(t):
            if t < duration:
                progress = t / duration
                width = clip1.w
                height = clip1.h
                
                frame1 = clip1.get_frame(clip1.duration - duration + t)
                frame2 = clip2.get_frame(t)
                
                wipeX = int(width * progress)
                result = frame1.copy()
                result[:, :wipeX] = frame2[:, :wipeX]
                return result
            else:
                return clip2.get_frame(t)
                
        new_clip = VideoClip(make_frame, duration=duration)
        return concatenate_videoclips([clip1.subclip(0, clip1.duration - duration), 
                                      new_clip, 
                                      clip2.subclip(duration)])
    
    elif transition_type == "dissolve":
        # Dissolução com textura de filme
        def make_frame(t):
            progress = t / duration
            texture_noise = np.random.rand(clip1.h, clip1.w, 3) * 0.15
            
            frame1 = clip1.get_frame(clip1.duration - duration + t) * (1 - progress)
            frame2 = clip2.get_frame(t) * progress
            
            result = frame1 + frame2 + texture_noise
            return np.clip(result, 0, 255).astype('uint8')
                
        new_clip = VideoClip(make_frame, duration=duration)
        return concatenate_videoclips([clip1.subclip(0, clip1.duration - duration), 
                                      new_clip, 
                                      clip2.subclip(duration)])
    
    elif transition_type == "zoom":
        # Transição com zoom
        clip1_end = clip1.subclip(clip1.duration - duration).fx(vfx.resize, lambda t: 1 + t/duration)
        clip2_start = clip2.subclip(0, duration).fx(vfx.resize, lambda t: 2 - t/duration)
        
        def make_frame(t):
            progress = t / duration
            frame1 = clip1_end.get_frame(t) * (1 - progress)
            frame2 = clip2_start.get_frame(t) * progress
            return np.clip(frame1 + frame2, 0, 255).astype('uint8')
                
        new_clip = VideoClip(make_frame, duration=duration)
        return concatenate_videoclips([clip1.subclip(0, clip1.duration - duration), 
                                      new_clip, 
                                      clip2.subclip(duration)])
    
    else:
        # Fallback para crossfade
        return clip1.crossfadeout(duration).crossfadein(clip2, duration)

def apply_dynamic_camera_movement(clip, duration, movement_type="dolly", final_resolution=(1920, 1080)):
    """Aplica movimentos de câmera cinematográficos"""
    width, height = final_resolution
    
    # Redimensionar para ter espaço para movimento
    scale_factor = 1.5
    clip = clip.resize(width=int(width * scale_factor), height=int(height * scale_factor))
    
    # Ponto de partida (centro da imagem redimensionada)
    start_x = (clip.w - width) // 2
    start_y = (clip.h - height) // 2
    
    # Movimentos de câmera
    if movement_type == "dolly":
        # Dolly zoom (Efeito Vertigo)
        def dolly_pos(t):
            # Move em direção ao objeto enquanto amplia
            prog = t / duration
            zoom = 1 + 0.15 * prog  # Zoom aumenta 15%
            
            # Ajustar posição para centralizar durante o zoom
            x = start_x - (zoom - 1) * width/2
            y = start_y - (zoom - 1) * height/2
            
            return (x, y)
            
        def dolly_size(t):
            prog = t / duration
            zoom = 1 + 0.15 * prog
            return (width * zoom, height * zoom)
            
        clip = clip.set_position(dolly_pos).resize(dolly_size)
    
    elif movement_type == "pan":
        # Pan horizontal
        amplitude = width * 0.15  # 15% da largura
        
        def pan_pos(t):
            prog = t / duration
            # Movimento suave usando função seno
            move_x = start_x + amplitude * np.sin(prog * np.pi)
            return (move_x, start_y)
            
        clip = clip.set_position(pan_pos)
    
    elif movement_type == "tilt":
        # Tilt vertical
        amplitude = height * 0.15  # 15% da altura
        
        def tilt_pos(t):
            prog = t / duration
            # Movimento suave usando função seno
            move_y = start_y + amplitude * np.sin(prog * np.pi)
            return (start_x, move_y)
            
        clip = clip.set_position(tilt_pos)
    
    elif movement_type == "arc":
        # Movimento em arco
        radius_x = width * 0.1
        radius_y = height * 0.1
        
        def arc_pos(t):
            prog = t / duration
            angle = prog * np.pi
            move_x = start_x + radius_x * np.cos(angle)
            move_y = start_y + radius_y * np.sin(angle)
            return (move_x, move_y)
            
        clip = clip.set_position(arc_pos)
    
    else:  # "push" - Movimento para frente/zoom suave
        def push_zoom(t):
            prog = t / duration
            # Interpolação suave para o efeito de aceleração/desaceleração
            ease = interp1d([0, 0.5, 1], [0, 0.7, 1], kind='quadratic')(prog)
            zoom = 1 + 0.2 * ease
            return zoom
            
        clip = clip.fx(vfx.resize, push_zoom)
        
        # Ajustar posição para manter centralizado durante o zoom
        def push_pos(t):
            prog = t / duration
            ease = interp1d([0, 0.5, 1], [0, 0.7, 1], kind='quadratic')(prog)
            zoom = 1 + 0.2 * ease
            
            x = start_x - (zoom - 1) * width/2
            y = start_y - (zoom - 1) * height/2
            
            return (x, y)
            
        clip = clip.set_position(push_pos)
    
    # Recortar para garantir a resolução final exata
    return clip.crop(x1=0, y1=0, width=width, height=height)

def create_dynamic_subtitles(text, duration, final_resolution):
    """Cria legendas cinematográficas com animação suave"""
    logger.info(f"Gerando legendas para o texto: '{text}' com duração {duration}s")
    width, height = final_resolution
    words = text.split()
    word_duration = duration / len(words)
    
    # Criar clipes de texto para cada palavra
    text_clips = []
    
    # Definir cores elegantes para as palavras (tons mais suaves e cinematográficos)
    colors = ['#F5F5DC', '#E6E6FA', '#F0FFF0', '#FFF5EE', '#F0FFFF']
    
    font_size = min(40, int(width / 25))  # Tamanho de fonte adaptativo
    
    for i, word in enumerate(words):
        start_time = i * word_duration
        end_time = (i + 1) * word_duration
        
        # Criar clipe de texto com uma fonte mais cinematográfica
        txt_clip = TextClip(
            word,
            fontsize=font_size,
            font='Arial-Bold',
            color=colors[i % len(colors)],
            stroke_color='black',
            stroke_width=1.5,
            method='label'
        )
        
        # Adicionar fade in/out suave
        fade_duration = min(0.3, word_duration / 3)
        txt_clip = txt_clip.fx(vfx.fadein, fade_duration).fx(vfx.fadeout, fade_duration)
        
        # Animar a entrada da palavra (leve movimento para cima)
        def word_pos(t):
            # Movimento suave para a posição final
            prog = min(1, t / (word_duration * 0.4))
            y_offset = 20 * (1 - prog)
            return ('center', height - 120 - y_offset)
            
        txt_clip = txt_clip.set_position(word_pos)
        
        # Definir duração e tempo
        txt_clip = txt_clip.set_start(start_time)
        txt_clip = txt_clip.set_end(end_time)
        txt_clip = txt_clip.set_duration(word_duration)
        
        text_clips.append(txt_clip)
    
    # Adicionar sombra cinematográfica para as legendas
    shadow_bg = ColorClip(
        size=(width, 100),
        color=(0, 0, 0)
    ).set_opacity(0.5).set_position(('center', height - 100))
    shadow_bg = shadow_bg.set_duration(duration)
    
    # Combinar legendas com sombra
    subtitle_clips = [shadow_bg] + text_clips
    subtitle_composite = CompositeVideoClip(subtitle_clips, size=final_resolution)
    
    return subtitle_composite

def create_scene_clip(item, config):
    """Cria um clipe de cena com movimento de câmera cinematográfico"""
    logger.info(f"Criando clipe cinematográfico para a cena: {item.get('image_path', 'desconhecido')}")
    
    # Verificar se temos o caminho da imagem
    image_path = item.get("image_path") or item.get("filename", "")
    if not image_path or not os.path.exists(image_path):
        raise FileNotFoundError(f"Arquivo de imagem não encontrado: {image_path}")
    
    # Criar clipe da imagem
    clip = ImageClip(image_path)
    
    # Selecionar movimento de câmera aleatório para variedade
    camera_movements = ["dolly", "pan", "tilt", "arc", "push"]
    movement_type = random.choice(camera_movements)
    
    # Aplicar movimento de câmera cinematográfico
    clip = apply_dynamic_camera_movement(
        clip, 
        item["duration"], 
        movement_type=movement_type,
        final_resolution=config.final_resolution
    )
    
    # Aplicar efeitos cinematográficos
    # Selecionar estilo de color grading baseado na cena
    styles = ["drama", "thriller", "romance", "sci_fi"]
    style = item.get("mood", random.choice(styles))
    
    # Aplicar color grading
    clip = CinematicEffects.cinematic_color_grading(clip, style=style)
    
    # Adicionar grão de filme sutil
    clip = CinematicEffects.film_grain(clip, intensity=0.03)
    
    # Adicionar vinheta
    clip = CinematicEffects.vignette_effect(clip, intensity=0.25)
    
    # Definir duração
    clip = clip.set_duration(item["duration"])
    
    return clip

def create_narrative_video(config, content_data):
    logger.info(f"Iniciando criação de vídeo cinematográfico")
    clips = []
    
    # Processar cada cena com efeitos cinematográficos
    for i, item in enumerate(content_data):
        try:
            # Verificar dados necessários
            if not item.get("duration"):
                raise ValueError(f"Cena {i+1} não tem duração definida")
            if not item.get("audio_clip"):
                raise ValueError(f"Cena {i+1} não tem áudio definido")
            
            # Criar clipe da cena com efeitos cinematográficos
            scene_clip = create_scene_clip(item, config)
            audio_clip = item["audio_clip"]
            
            # Verificar se os clipes foram criados corretamente
            if not isinstance(scene_clip, (ImageClip, VideoClip)):
                raise ValueError(f"Clipe da cena {i+1} não foi criado corretamente")
            if not isinstance(audio_clip, AudioFileClip):
                raise ValueError(f"Áudio da cena {i+1} não foi criado corretamente")
            
            # Aplicar equalização cinematográfica ao áudio (realce sutil)
            audio_clip = audio_clip.fx(afx.volumex, 1.2)  # Leve boost no volume
            
            # Adicionar áudio à cena
            scene = scene_clip.set_audio(audio_clip)
            
            # Adicionar legendas se necessário
            if config.add_subtitles:
                logger.info(f"Adicionando legendas cinematográficas para a cena {i+1}")
                subtitle_clip = create_dynamic_subtitles(
                    item["prompt"], 
                    item["duration"], 
                    config.final_resolution
                )
                
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
    
    # Criar vídeo final com transições cinematográficas entre cenas
    final_clips = []
    transition_duration = 1.0  # 1 segundo para transições
    
    # Tipos de transição para alternar
    transition_types = ["fade", "dissolve", "wipe", "zoom"]
    
    for i in range(len(clips)):
        # Adicionar o clipe atual
        if i > 0:
            # Reduzir a duração do clipe anterior e atual para acomodar a transição
            clips[i-1] = clips[i-1].subclip(0, clips[i-1].duration - transition_duration/2)
            clips[i] = clips[i].subclip(transition_duration/2)
            
            # Criar transição entre clipes
            transition_type = transition_types[i % len(transition_types)]
            transition = create_cinematic_transitions(
                final_clips[-1], 
                clips[i], 
                transition_type=transition_type,
                duration=transition_duration
            )
            
            # Substituir o último clipe pela transição
            final_clips[-1] = transition
        else:
            final_clips.append(clips[i])
    
    # Concatenar todos os clipes com as transições
    final_video = concatenate_videoclips(final_clips, method="compose")
    
    # Adicionar música de fundo se especificada
    if config.audio_path:
        bg_audio = AudioFileClip(config.audio_path).volumex(0.15)  # Volume mais baixo para não competir
        
        # Aplicar fade in/out na música
        bg_audio = bg_audio.audio_fadein(3).audio_fadeout(3)
        
        # Ajustar duração da música
        if bg_audio.duration < final_video.duration:
            # Loop com crossfade para evitar cortes bruscos
            loops_needed = int(np.ceil(final_video.duration / bg_audio.duration))
            audio_pieces = []
            
            for j in range(loops_needed):
                start_time = j * bg_audio.duration
                end_time = min((j+1) * bg_audio.duration, final_video.duration)
                duration = end_time - start_time
                
                if duration > 0:
                    piece = bg_audio.subclip(0, duration)
                    piece = piece.set_start(start_time)
                    audio_pieces.append(piece)
            
            bg_audio = CompositeAudioClip(audio_pieces)
        else:
            bg_audio = bg_audio.subclip(0, final_video.duration)
        
        # Mixar áudio original com música de fundo
        final_audio = CompositeAudioClip([final_video.audio, bg_audio])
        final_video = final_video.set_audio(final_audio)
    
    # Aplicar efeitos finais ao vídeo completo
    final_video = CinematicEffects.film_grain(final_video, intensity=0.02)  # Leve grão em todo vídeo
    
    # Renderizar vídeo final com alta qualidade
    output_path = os.path.join(config.output_dir, config.output_filename)
    print(f"Renderizando vídeo cinematográfico... Duração total: {final_video.duration:.2f}s")
    
    # Usar configurações de alta qualidade para renderização
    final_video.write_videofile(
        output_path, 
        fps=24,  # Padrão cinematográfico
        codec="libx264", 
        audio_codec="aac", 
        bitrate="8000k",  # Alta qualidade
        threads=4,
        preset="slow"  # Compressão mais lenta mas com melhor qualidade
    )
    
    print(f"Vídeo cinematográfico salvo em: {output_path}")
    return output_path