#!/usr/bin/env python3

import dpcm
import fti
import midi

# python stdlib
import io
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
    scaled_frames = [(sample - min_sample) / scale for sample in mono_frames]
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
    
def samplerate_conversion_speed(source_rate, target_rate):
    return source_rate / target_rate

# quite possibly the worst quality. Aliasing abounds, but it's quick
# and *probably* quieter than DPCM noise, so... maybe it's fine?
def resample_nearest(source_samples, speed):
    resampled_samples = []
    new_length = int(len(source_samples) / speed)
    for i in range(0, new_length):
        resampled_samples.append(source_samples[int(i * speed)])
    return resampled_samples

def main():
    print("Will do a thing")
    filename = "abass-A2.wav"
    quality = 0xF
    source_note = "A2"
    target_note = "D3"

    data, samplerate = read_wave(filename)
    print("Read {} samples from {} at {} Hz".format(len(data), filename, samplerate))

    target_rate = dpcm.playback_rate[quality]
    conversion_speed = samplerate / target_rate
    print("Will sample at {:.4g} speed to target {} Hz".format(conversion_speed, target_rate))
    source_frequency = midi.frequency[midi.note_index(source_note)]
    target_frequency = midi.frequency[midi.note_index(target_note)]
    repitch_speed = target_frequency / source_frequency
    print("To repitch from {} to {}, will adjust speed by {:.4g}%".format(source_note, target_note, repitch_speed))
    combined_speed = conversion_speed * repitch_speed
    print("Combined adjustment: {:.4g}%".format(combined_speed))

    resampled_data = resample_nearest(data, combined_speed)
    print("Resampled data to new length: {}".format((len(resampled_data))))

    if len(resampled_data) > 4081 * 8:
        print("Data is too long, truncating to 4081*8 samples")
        resampled_data = resampled_data[0:(4081*8)]

    # sure, let's just spit it out
    dpcm_data = dpcm.to_dpcm(resampled_data)
    output = io.open("abass-D3.dmc", "wb")
    output.write(dpcm_data)
    output.close()



if __name__ == "__main__":
    # execute only if run as a script
    main()