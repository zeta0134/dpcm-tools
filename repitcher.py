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


def resample_note(source_data, source_samplerate, target_samplerate, source_frequency, target_frequency, resampler=resample_nearest):
    # first deal with differences in our source PCM and our target PCM playback rate
    conversion_speed = source_samplerate / target_samplerate
    # next deal with differences between the two MIDI frequencies, and come up with a speed correction
    repitch_speed = target_frequency / source_frequency
    # Put it all together and perform the resample
    combined_speed = conversion_speed * repitch_speed
    resampled_data = resampler(source_data, combined_speed)
    return resampled_data

def generate_repitched_instrument(source_data, source_samplerate, source_note, target_notes, target_quality=0xF, max_length=4081, prefix=None, set_delta=-1,):
    note_mappings = []
    sample_table = []
    sample_prefix = ""
    sample_index = 1
    target_rate = dpcm.playback_rate[target_quality]
    note_list = midi.parse_note_list(target_notes)
    source_frequency = midi.frequency[midi.note_index(source_note)]

    if prefix:
        sample_prefix = prefix + "-"

    for target_note in note_list:
        target_frequency = midi.frequency[target_note]
        resampled_pcm = resample_note(source_data, source_samplerate, target_rate, source_frequency, target_frequency)
        if len(resampled_pcm) > max_length * 8:
            print("Data is too long, truncating to {} bytes".format(max_length))
            resampled_pcm = resampled_pcm[0:(max_length*8)]
        dpcm_data = dpcm.to_dpcm(resampled_pcm, 0)
        sample_name = midi.note_name(target_note)
        sample_table.append({"name": sample_prefix+sample_name, "data": dpcm_data})
        note_mappings.append({"midi_index": target_note + 12, "sample_index": sample_index, "pitch": 0xF, "looping": False, "delta": set_delta})
        sample_index += 1
    return sample_table, note_mappings

def main():
    print("Will do a thing")
    filename = "synthbass-C3.wav"
    quality = 0xF
    source_note = "C3"
    target_note = "D3-D4"

    data, samplerate = read_wave(filename)
    print("Read {} samples from {} at {} Hz".format(len(data), filename, samplerate))

    (sample_table, note_mappings) = generate_repitched_instrument(data, samplerate, source_note, target_note, set_delta=32, max_length=512)
    note_mappings = fti.fill_lower_samples(note_mappings)

    output = io.open("test.fti", "wb")
    fti.write_dpcm_instrument(output, "TEST", note_mappings, sample_table)
    output.close()



if __name__ == "__main__":
    # execute only if run as a script
    main()