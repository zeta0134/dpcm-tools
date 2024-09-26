#!/usr/bin/env python3

import dpcm
import fti

import argparse
import math
import os
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
    min_sample = -32768
    max_sample = 32767
    scale = (max_sample - min_sample) / 256
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

# because doing this by hand in famitracker's UI is AWFUL on Wine
def compile_instrument(file, instrument_name, chunks):
    sample_table = []
    note_mappings = []
    for i in range(0, len(chunks)):
        sample_table.append({"name": f"{instrument_name}_{i:03d}", "data": chunks[i]})
        note_mappings.append({"midi_index": i+12, "sample_index": i, "pitch": 0xF, "looping": False, "delta": 0})
    fti.write_dpcm_instrument(file, instrument_name, note_mappings, sample_table)

def main():
    parser = argparse.ArgumentParser(
        description="Split a long .wav into many smaller .dmc samples", 
        formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("source", help="Path to a source .wav file. Accepts unsigned 8bit, signed 16bit, mono or stereo.")
    parser.add_argument("length", help="Split length in seconds")
    parser.add_argument("-s", "--directory", help="Directory to store generated samples as .dmc")
    parser.add_argument("-i", "--instrument", help="DnFamiTracker Instrument to write, as .fti")

    instrument_group = parser.add_argument_group("FamiTracker Instruments")
    instrument_group.add_argument("--fullname", help="The full name of this instrument, show in FamiTracker's UI")

    args = parser.parse_args()
    length_in_seconds = float(args.length)
    length_in_dpcm_samples = length_in_seconds * dpcm.playback_rate[0xF]
    split_length_in_dpcm_bytes = math.floor(length_in_dpcm_samples / 8)
    actual_split_duration = (math.floor(split_length_in_dpcm_bytes / 16) + 5) * 16 + 1

    print(f"Split length will be at {split_length_in_dpcm_bytes} byte boundaries")
    print(f"Sample length will be {actual_split_duration}, including ~16ms extra length each")

    data, samplerate = read_wave(args.source)
    print("Read {} samples from {} at {} Hz".format(len(data), args.source, samplerate))

    print("Performing conversion (may take a minute)...")
    dpcm_bytes = dpcm.to_dpcm(data)

    print("Splitting converted bytes along chunk boundaries...")
    dpcm_chunks = []
    while len(dpcm_bytes) > 0:
        chunk = bytearray(dpcm_bytes[0:actual_split_duration])
        dpcm_bytes = dpcm_bytes[split_length_in_dpcm_bytes:]
        # if we don't pad to the full length famitracker will complain, so do that
        # (in practice we'll rarely use the last chunk)
        if len(chunk) != actual_split_duration:
            chunk.extend([0]*actual_split_duration)
            chunk = chunk[:actual_split_duration]
        dpcm_chunks.append(chunk)

    print(f"After conversion, got {len(dpcm_chunks)} chunks in total, will proceed to output...")    

    if args.directory != None:
        for i in range(0, len(dpcm_chunks)):
            chunk_data = dpcm_chunks[i]

            chunk_filename = f"{args.directory}/thing_{i:03d}.dmc"

            os.makedirs(args.directory, exist_ok=True)
            output = io.open(chunk_filename, "wb")
            output.write(chunk_data)
            output.close()
    if args.instrument != None:
        instrument_filename = args.instrument
        (nicename, ext) = os.path.splitext(os.path.basename(instrument_filename))
        full_instrument_name = args.fullname or "DPCM {}".format(nicename)

        output = io.open(instrument_filename, "wb")
        truncated_chunks = dpcm_chunks[0:64]
        compile_instrument(output, full_instrument_name, truncated_chunks)
        output.close()

if __name__ == "__main__":
    # execute only if run as a script
    main()