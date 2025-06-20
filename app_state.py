from Voice import Voice
import feature_support
from video import Video
import sys

platform = sys.platform
video: Video = None

default_voice_type = Voice.VoiceType.SYSTEM # Fallback default
default_name = "Sample"

if feature_support.google_cloud_supported:
    default_voice_type = Voice.VoiceType.GOOGLE_CLOUD
    # GoogleCloudVoice initializes with its own sensible defaults (en-US, en-US-Standard-C)
    # No need to call set_voice_params here unless we want a different default GCloud voice.
    speakers = [Voice(default_voice_type, name=default_name)]
elif feature_support.coqui_supported:
    default_voice_type = Voice.VoiceType.COQUI
    speakers = [Voice(default_voice_type, name=default_name)]
    # speakers[0].set_voice_params('tts_models/en/vctk/vits', 'p326') # Example Coqui default
    # For Coqui, it's better to let user pick model due to downloads.
    # Or, ensure the default model here is small or commonly available.
    # For now, let CoquiVoice initialize with its default model if any, or await user selection.
else:
    # default_voice_type remains SYSTEM
    speakers = [Voice(default_voice_type, name=default_name)]

current_speaker = speakers[0]
sample_speaker = current_speaker
