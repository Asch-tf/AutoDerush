class VideoExporter:
    FORMATS = {
        "MP4": {
            "extension": "mp4",
            "video_codec": "libx264",
            "audio_codec": "aac"
        },
        "AVI": {
            "extension": "avi",
            "video_codec": "libx264",
            "audio_codec": "pcm_s16le"
        },
        "MKV": {
            "extension": "mkv",
            "video_codec": "libx264",
            "audio_codec": "aac"
        },
        "WebM": {
            "extension": "webm",
            "video_codec": "libvpx",
            "audio_codec": "libvorbis"
        }
    }
