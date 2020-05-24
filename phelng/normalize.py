from os import path
from pydub import AudioSegment

def match_target_amplitude(sound: AudioSegment, target_dBFS: float) -> AudioSegment:
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)

def normalize_file(filepath: str, output_filepath: str, target_dBFS: float = -20.0):
    file_format = path.splitext(filepath)[1]
    sound = AudioSegment.from_file(filepath, file_format)
    normalized_sound = match_target_amplitude(sound, target_dBFS)
    outfile_format = path.splitext(output_filepath)[1]
    normalized_sound.export(output_filepath, outfile_format)
