import os
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip
import moviepy.video.fx.all as vfx

def apply_ken_burns_effect(img_clip, duration, final_resolution):
    width, height = final_resolution
    img_clip = img_clip.resize(height=height) if img_clip.w > img_clip.h else img_clip.resize(width=width)
    zoom_factor = 1.2
    start_size = (int(img_clip.w * zoom_factor), int(img_clip.h * zoom_factor))
    end_size = (img_clip.w, img_clip.h)
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
    return clip.crop(x_center=width/2, y_center=height/2, width=width, height=height)

def create_narrative_video(config, content_data):
    clips = []
    total_duration = 0
    for item in content_data:
        if not os.path.exists(item["image_path"]):
            raise FileNotFoundError(f"Imagem não encontrada: {item['image_path']}")
        img_clip = ImageClip(item["image_path"])
        if img_clip is None:
            raise ValueError(f"Falha ao carregar imagem: {item['image_path']}")
        img_clip_with_effect = apply_ken_burns_effect(img_clip, item["duration"], config.final_resolution)
        audio_clip = item["audio_clip"]
        scene = img_clip_with_effect.set_audio(audio_clip)
        clips.append(scene)
        total_duration += item["duration"]
    for i, clip in enumerate(clips):
        if i == 0:
            clips[i] = vfx.fadein(clip, 0.5)
        if i == len(clips) - 1:
            clips[i] = vfx.fadeout(clip, 0.8)
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