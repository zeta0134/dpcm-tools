#!/usr/bin/env python3

import dpcm
import fti
import midi

# python stdlib
import wave
import struct

def mix_stereo_to_mono(combined_stereo_frames):
    mono_frames = []
    for i in range(0, len(combined_stereo_frames), 2):
        mono_frames.append((combined_stereo_frames[i] + combined_stereo_frames[i+1]) / 2.0)
    return mono_frames

def fix_16bit_pcm(raw_bytes, nframes):
    combined_frames = [x[0] for x in struct.iter_unpack("<h", raw_bytes)]
    return combined_frames

def fix_sample_width(mono_frames, sample_width):
    min_sample = 0
    max_sample = 255
    if sample_width == 2:
        min_sample = -32768
        max_sample = 32767
    scale = (max_sample - min_sample) / 127
    scaled_frames = [int((sample - min_sample) / scale) for sample in mono_frames]
    return scaled_frames

def read_wave(filename):
    reader = wave.open(filename, "rb")
    sample_count = reader.getnframes()
    sample_width = reader.getsampwidth()
    channel_count = reader.getnchannels()
    samplerate = reader.getframerate()
    data = reader.readframes(sample_count)
    reader.close()
    if sample_width == 2:
        data = fix_16bit_pcm(data, sample_count)
    if channel_count == 2:
        data = mix_stereo_to_mono(data)
    data = fix_sample_width(data, sample_width)
    return data, samplerate
    

def main():
    print("Will do a thing")
    filename = "abass-A2.wav"
    quality = 0xF
    source_note = "A2"
    target_note = "D3"

    data, samplerate = read_wave(filename)
    print("Read {} samples from {} at {} Hz".format(len(data), filename, samplerate))



if __name__ == "__main__":
    # execute only if run as a script
    main()