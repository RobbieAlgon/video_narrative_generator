import os
import numpy as np
from moviepy.editor import (
    ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip,
    TextClip, ColorClip, VideoFileClip, VideoClip, CompositeAudioClip, concatenate_audioclips
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
            grain = np.random.normal(0, intensity * 255, image.shape)
            noisy_image = np.clip(image.astype(float) + grain, 0, 255).astype('uint8')
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
            return np.clip(image.astype(float) * params["brightness"], 0, 255).astype('uint8')
        
        # Ajuste de temperatura
        def adjust_temp(image):
            # Aumenta o azul (mais frio) ou vermelho (mais quente)
            b, g, r = cv2.split(image)
            if params["temp"] < 1:  # Mais frio (azulado)
                b = np.clip(b.astype(float) * (2 - params["temp"]), 0, 255).astype('uint8')
            else:  # Mais quente (avermelhado)
                r = np.clip(r.astype(float) * params["temp"], 0, 255).astype('uint8')
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
            return np.clip(image.astype(float) * vignette, 0, 255).astype('uint8')
        
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

def create_cinematic_transition(clip1, clip2, transition_type="fade", duration=1.0):
    """Cria transições cinematográficas entre cenas"""
    # Garantir que ambos os clipes existam e tenham duração adequada
    if clip1.duration < duration or clip2.duration < duration:
        # Se algum clipe for menor que a duração da transição, usar crossfade simples
        transition_type = "fade"
    
    if transition_type == "fade":
        # Usar crossfadein e crossfadeout nativos do moviepy
        return concatenate_videoclips([
            clip1.subclip(0, clip1.duration - duration/2),
            CompositeVideoClip([
                clip1.subclip(clip1.duration - duration, clip1.duration).crossfadeout(duration),
                clip2.subclip(0, duration).crossfadein(duration)
            ])
        ])
    
    elif transition_type == "wipe":
        # Transição de varredura, estilo Star Wars
        def make_frame(t):
            progress = t / duration
            width = clip1.w
            height = clip1.h
            
            # Obter frames dos clipes originais
            t1 = clip1.duration - duration + t
            t2 = t
            
            if t1 <= clip1.duration and t2 <= clip2.duration:
                frame1 = clip1.get_frame(t1)
                frame2 = clip2.get_frame(t2)
                
                wipeX = int(width * progress)
                result = frame1.copy()
                if wipeX > 0:
                    result[:, :wipeX] = frame2[:, :wipeX]
                return result
            elif t2 <= clip2.duration:
                return clip2.get_frame(t2)
            else:
                return np.zeros((height, width, 3), dtype='uint8')
                
        # Criar um clipe para a transição
        transition_clip = VideoClip(make_frame, duration=duration)
        transition_clip = transition_clip.set_audio(CompositeAudioClip([
            clip1.audio.subclip(clip1.duration - duration, clip1.duration).volumex(lambda t: 1-t/duration),
            clip2.audio.subclip(0, duration).volumex(lambda t: t/duration)
        ]) if clip1.audio is not None and clip2.audio is not None else None)
        
        # Concatenar os clipes
        result = concatenate_videoclips([
            clip1.subclip(0, clip1.duration - duration),
            transition_clip,
            clip2.subclip(duration)
        ], method="compose")
        
        return result
    
    elif transition_type == "dissolve":
        # Dissolução com textura de filme
        def make_frame(t):
            progress = t / duration
            texture_noise = np.random.rand(clip1.h, clip1.w, 3) * 0.15
            
            # Obter frames dos clipes originais
            t1 = clip1.duration - duration + t
            t2 = t
            
            if t1 <= clip1.duration and t2 <= clip2.duration:
                frame1 = clip1.get_frame(t1).astype(float) * (1 - progress)
                frame2 = clip2.get_frame(t2).astype(float) * progress
                
                result = frame1 + frame2 + texture_noise
                return np.clip(result, 0, 255).astype('uint8')
            elif t2 <= clip2.duration:
                return clip2.get_frame(t2)
            else:
                return np.zeros((clip1.h, clip1.w, 3), dtype='uint8')
                
        # Criar um clipe para a transição
        transition_clip = VideoClip(make_frame, duration=duration)
        transition_clip = transition_clip.set_audio(CompositeAudioClip([
            clip1.audio.subclip(clip1.duration - duration, clip1.duration).volumex(lambda t: 1-t/duration),
            clip2.audio.subclip(0, duration).volumex(lambda t: t/duration)
        ]) if clip1.audio is not None and clip2.audio is not None else None)
        
        # Concatenar os clipes
        result = concatenate_videoclips([
            clip1.subclip(0, clip1.duration - duration),
            transition_clip,
            clip2.subclip(duration)
        ], method="compose")
        
        return result
    
    elif transition_type == "zoom":
        # Transição com zoom
        def make_frame(t):
            progress = t / duration
            
            # Obter frames dos clipes originais
            t1 = clip1.duration - duration + t
            t2 = t
            
            if t1 <= clip1.duration and t2 <= clip2.duration:
                # Calcular tamanhos de zoom
                zoom1 = 1 + 0.2 * progress  # Zoom out
                zoom2 = 1.2 - 0.2 * progress  # Zoom in
                
                # Redimensionar frames
                h, w = clip1.h, clip1.w
                frame1 = clip1.get_frame(t1)
                frame2 = clip2.get_frame(t2)
                
                # Redimensionar (simulação simplificada)
                # Em uma implementação real, usaríamos cv2.resize aqui
                frame1_zoomed = frame1
                frame2_zoomed = frame2
                
                # Misturar os frames com cross dissolve
                result = frame1_zoomed.astype(float) * (1 - progress) + frame2_zoomed.astype(float) * progress
                return np.clip(result, 0, 255).astype('uint8')
            elif t2 <= clip2.duration:
                return clip2.get_frame(t2)
            else:
                return np.zeros((clip1.h, clip1.w, 3), dtype='uint8')
        
        # Criar um clipe para a transição
        transition_clip = VideoClip(make_frame, duration=duration)
        transition_clip = transition_clip.set_audio(CompositeAudioClip([
            clip1.audio.subclip(clip1.duration - duration, clip1.duration).volumex(lambda t: 1-t/duration),
            clip2.audio.subclip(0, duration).volumex(lambda t: t/duration)
        ]) if clip1.audio is not None and clip2.audio is not None else None)
        
        # Concatenar os clipes
        result = concatenate_videoclips([
            clip1.subclip(0, clip1.duration - duration),
            transition_clip,
            clip2.subclip(duration)
        ], method="compose")
        
        return result
    
    else:
        # Fallback para crossfade simples
        return concatenate_videoclips([
            clip1.subclip(0, clip1.duration - duration/2),
            CompositeVideoClip([
                clip1.subclip(clip1.duration - duration, clip1.duration).crossfadeout(duration),
                clip2.subclip(0, duration).crossfadein(duration)
            ])
        ])

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
            return (int(width * zoom), int(height * zoom))
            
        clip = clip.set_position(dolly_pos)
        clip = clip.resize(lambda t: dolly_size(t))
    
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
            # Suavizar a curva de progresso para aceleração/desaceleração
            ease = 0.5 - 0.5 * np.cos(prog * np.pi)  # Função easing
            zoom = 1 + 0.2 * ease
            return zoom
            
        clip = clip.fx(vfx.resize, lambda t: push_zoom(t))
        
        # Ajustar posição para manter centralizado durante o zoom
        def push_pos(t):
            prog = t / duration
            ease = 0.5 - 0.5 * np.cos(prog * np.pi)
            zoom = 1 + 0.2 * ease
            
            x = start_x - (zoom - 1) * width/2
            y = start_y - (zoom - 1) * height/2
            
            return (x, y)
            
        clip = clip.set_position(push_pos)
    
    # Recortar para garantir a resolução final exata
    clip = clip.set_duration(duration)
    clip = clip.crop(x1=0, y1=0, width=width, height=height)
    
    return clip

def create_dynamic_subtitles(text, duration, final_resolution):
    """Cria legendas dinâmicas word-by-word sem fundo"""
    logger.info(f"Gerando legendas dinâmicas para o texto: '{text}' com duração {duration}s")
    width, height = final_resolution
    words = text.split()
    word_duration = duration / len(words)
    
    # Criar clipes de texto para cada palavra
    text_clips = []
    
    # Definir cores elegantes para as palavras
    colors = ['#FFFFFF', '#F5F5F5', '#FAFAFA', '#F0F0F0', '#EFEFEF']
    
    font_size = min(40, int(width / 25))  # Tamanho de fonte adaptativo
    
    for i, word in enumerate(words):
        start_time = i * word_duration
        
        # Criar clipe de texto com uma fonte elegante
        txt_clip = TextClip(
            word,
            fontsize=font_size,
            font='Arial-Bold',
            color=colors[i % len(colors)],
            stroke_color='black',
            stroke_width=1.5,
            method='label'
        )
        
        # Definir duração do clipe
        txt_clip = txt_clip.set_duration(word_duration)
        
        # Adicionar fade in/out suave
        fade_duration = min(0.3, word_duration / 3)
        txt_clip = txt_clip.fx(vfx.fadein, fade_duration)
        txt_clip = txt_clip.fx(vfx.fadeout, fade_duration)
        
        # Animar a entrada da palavra (leve movimento para cima)
        def word_pos(t):
            # Movimento suave para a posição final
            prog = min(1, t / (word_duration * 0.4))
            y_offset = 20 * (1 - prog)
            return ('center', height - 120 - y_offset)
            
        txt_clip = txt_clip.set_position(word_pos)
        
        # Definir tempo de início
        txt_clip = txt_clip.set_start(start_time)
        
        text_clips.append(txt_clip)
    
    # Criar um clipe composto apenas com as palavras (sem fundo)
    subtitle_composite = CompositeVideoClip(text_clips, size=final_resolution)
    
    return subtitle_composite

def create_scene_clip(item, config):
    """Cria um clipe de cena com zoom suave e garantindo preenchimento total da tela"""
    logger.info(f"Criando clipe para a cena: {item.get('image_path')}")
    
    # Verificar se temos o caminho da imagem
    image_path = item.get("image_path") or item.get("filename", "")
    if not image_path or not os.path.exists(image_path):
        raise FileNotFoundError(f"Arquivo de imagem não encontrado: {image_path}")
    
    width, height = config.final_resolution
    
    # Criar clipe da imagem
    img_clip = ImageClip(image_path)
    
    # Calcular proporções para garantir que a imagem cubra toda a tela
    img_width, img_height = img_clip.size
    
    # Determinar o fator de escala para garantir que a imagem cubra toda a tela
    width_ratio = width / img_width
    height_ratio = height / img_height
    scale_factor = max(width_ratio, height_ratio) * 1.1  # Adiciona 10% extra para garantir cobertura
    
    # Redimensionar a imagem para garantir cobertura total
    img_clip = img_clip.resize(width=img_width*scale_factor, height=img_height*scale_factor)
    
    # Centralizar a imagem
    img_clip = img_clip.set_position("center")
    
    # Aplicar efeito de zoom suave e lento
    duration = item["duration"]
    
    def zoom_effect(t):
        # Zoom aumenta de 1.0 até 1.15 (15% de zoom) ao longo da duração
        zoom_factor = 1.0 + (0.15 * t / duration)
        return zoom_factor
    
    # Aplicar efeito de zoom à imagem
    zoomed_clip = img_clip.fx(
        vfx.resize, 
        lambda t: zoom_effect(t)
    )
    
    # Cortar para garantir que estamos exatamente no tamanho desejado
    result_clip = zoomed_clip.set_duration(duration).crop(
        x_center=zoomed_clip.w/2,
        y_center=zoomed_clip.h/2,
        width=width,
        height=height
    )
    
    return result_clip

def create_narrative_video(config, content_data):
    logger.info(f"Iniciando criação do vídeo com add_subtitles={config.add_subtitles}")
    logger.info(f"Conteúdo recebido: {len(content_data)} cenas")
    
    clips = []
    
    for i, item in enumerate(content_data):
        try:
            # Verificar se temos todos os dados necessários
            if not item.get("duration"):
                raise ValueError(f"Cena {i+1} não tem duração definida")
            if not item.get("audio_clip"):
                raise ValueError(f"Cena {i+1} não tem áudio definido")
            
            logger.info(f"Processando cena {i+1} com duração {item['duration']}s")
            
            # Criar clipe da cena principal
            scene_clip = create_scene_clip(item, config)
            audio_clip = item["audio_clip"]
            
            # Adicionar áudio à cena
            scene = scene_clip.set_audio(audio_clip)
            
            # Adicionar legendas dinâmicas se solicitado
            if config.add_subtitles:
                logger.info(f"Adicionando legendas dinâmicas para a cena {i+1}")
                try:
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
                except Exception as e:
                    logger.error(f"Erro ao criar legendas: {e}")
            
            clips.append(scene)
        except Exception as e:
            logger.error(f"Erro ao processar cena {i+1}: {e}")
            raise
    
    # Verificar se temos clipes para concatenar
    if not clips:
        raise ValueError("Nenhum clipe válido foi criado")
    
    # Criar transições dinâmicas entre cenas
    final_clips = []
    
    if len(clips) == 1:
        final_clips = clips
    else:
        # Primeiro clipe permanece como está
        final_clips.append(clips[0])
        
        # Criar transições para cada par de clipes subsequentes
        for i in range(1, len(clips)):
            prev_clip = clips[i-1]
            current_clip = clips[i]
            
            # Usar vários tipos de transição de forma alternada para variedade
            transition_types = ["dissolve", "crossfade", "fade"]
            transition_type = transition_types[i % len(transition_types)]
            
            # Duração da transição - mais curta para clipes curtos
            min_duration = min(prev_clip.duration, current_clip.duration)
            transition_duration = min(1.0, min_duration / 4)
            
            try:
                if transition_type == "crossfade" or transition_type == "fade":
                    # Usar o crossfadein nativo da MoviePy
                    transition_clip = vfx.crossfadein(current_clip, transition_duration)
                    final_clips.append(transition_clip)
                    
                elif transition_type == "dissolve":
                    # Transição com dissolução
                    # Calcular o ponto inicial de transição no clipe anterior
                    overlap_start = max(0, prev_clip.duration - transition_duration)
                    
                    # Recortar o final do clipe anterior para a transição
                    clip1_part = prev_clip.subclip(0, overlap_start)
                    
                    # Criar uma região de sobreposição
                    overlap = CompositeVideoClip([
                        prev_clip.subclip(overlap_start).set_opacity(lambda t: 1 - t/transition_duration),
                        current_clip.subclip(0, transition_duration).set_opacity(lambda t: t/transition_duration)
                    ])
                    
                    # Adicionar o resto do clipe atual
                    clip2_part = current_clip.subclip(transition_duration)
                    
                    # Concatenar as partes sem transição
                    composite = concatenate_videoclips([clip1_part, overlap, clip2_part], method="compose")
                    final_clips[-1] = composite
                else:
                    # Fallback para adição simples se a transição falhar
                    final_clips.append(current_clip)
            except Exception as e:
                logger.error(f"Erro ao aplicar transição: {e}")
                # Adicionar o clipe atual sem transição em caso de erro
                final_clips.append(current_clip)
    
    # Concatenar os clipes finais
    final_video = concatenate_videoclips(final_clips, method="compose")
    
    # Adicionar música de fundo se especificada
    if hasattr(config, 'audio_path') and config.audio_path and os.path.exists(config.audio_path):
        try:
            bg_audio = AudioFileClip(config.audio_path)
            bg_audio = bg_audio.volumex(0.2)  # Volume baixo para não competir com a narração
            
            # Ajustar duração da música
            if bg_audio.duration < final_video.duration:
                # Repetir o áudio para cobrir todo o vídeo
                repeats = int(np.ceil(final_video.duration / bg_audio.duration))
                bg_audio_parts = [bg_audio] * repeats
                bg_audio_extended = concatenate_audioclips(bg_audio_parts)
                bg_audio = bg_audio_extended.subclip(0, final_video.duration)
            else:
                bg_audio = bg_audio.subclip(0, final_video.duration)
            
            # Misturar com o áudio existente
            if final_video.audio is not None:
                final_audio = CompositeAudioClip([final_video.audio, bg_audio])
                final_video = final_video.set_audio(final_audio)
            else:
                final_video = final_video.set_audio(bg_audio)
        except Exception as e:
            logger.error(f"Erro ao adicionar música de fundo: {e}")
    
    # Renderizar vídeo final
    output_path = os.path.join(config.output_dir, config.output_filename)
    print(f"Renderizando vídeo... Duração total: {final_video.duration:.2f}s")
    
    final_video.write_videofile(
        output_path, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac", 
        bitrate="5000k",
        threads=4
    )
    
    print(f"Vídeo narrativo salvo em: {output_path}")
    return output_path