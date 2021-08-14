#!/usr/bin/env python3

import dpcm
import fti
import midi
import waveform

# python stdlib
import argparse
import io
import os
import wave

def _tuning_error(a):
    return a["error"]

def _tuning_length(a):
    return a["length"]

def ideal_tunings(target_frequency, playback_rate, max_length):
    tunings = []
    for i in range(1,max_length):
        repetitions = dpcm.repetitions(i, target_frequency, playback_rate)
        tuning = {
            "phase_offset": dpcm.phase_offset(i, target_frequency, playback_rate),
            "error": dpcm.tuning_error(i, target_frequency, playback_rate),
            "length": i,
            "size": dpcm.patch_bytes(i),
            "samples": dpcm.patch_samples(i),
            "repetitions": repetitions,
            "effective_frequency": dpcm.effective_frequency(i, repetitions, playback_rate),
        }
        tunings.append(tuning)
    tunings.sort(key=_tuning_error)
    return tunings

def generate_tuning_table(playback_rate, max_length):
    tuning_table = []
    for i in range(0, 94):
        target = midi.frequency[i]
        tuning_table.append(ideal_tunings(target, playback_rate, max_length))
    return tuning_table

def smallest_acceptable(ideal_tunings, threshold):
    acceptable_tunings = [x for x in ideal_tunings if x["error"] < threshold]
    # ensure there is always at least one entry in this list, in case we otherwise don't
    # have any options that would meet the threshold
    acceptable_tunings.append(ideal_tunings[0])
    acceptable_tunings.sort(key=_tuning_length)
    return acceptable_tunings[0]

def generate_pcm(tuning, generator, playback_rate, amplitude, target_bias):
    pcm = []
    for i in range(0, tuning["samples"]):
        sample = waveform.sample(generator, i, tuning["effective_frequency"], playback_rate) * amplitude
        bias = waveform.sample(waveform.bias, i, tuning["effective_frequency"], playback_rate) * target_bias
        #sample_8bit = int(min(255, max(0, (sample + bias) * 256)))
        sample_scaled = (sample + bias) * 256
        pcm.append(sample_scaled)
    return pcm

def write_waveform(filename, pcm_data, playback_rate):
    writer = wave.open(filename, mode="wb")
    writer.setnchannels(1)
    writer.setsampwidth(1)
    writer.setframerate(int(playback_rate))
    writer.writeframes(bytes(pcm_data))
    writer.close()

def write_dmc(filename, pcm_data):
    dmc_data = dpcm.to_dpcm(pcm_data)
    output = io.open(filename, "wb")
    output.write(dmc_data)
    output.close()


def generate_mapping(sample_table, target_note_name, source_sample_name, source_dpcm_pitch):
    mapping = {"midi_index": target_midi_index, "sample_index": sample_index, "pitch": source_dpcm_pitch, "looping": True}
    return mapping

def generate_samples(waveform_generator, note_list, volume=1.0, use_safe_amplitude=True, target_bias=0.0, set_delta=-1,
        playback_rate=33144, error_threshold=0.0, max_length_bytes=255, prefix="", quiet=False):
    tuning_table = generate_tuning_table(playback_rate, 255)
    sample_table = []
    note_mappings = []
    sample_index = 1
    for i in note_list:
        tuning = smallest_acceptable(tuning_table[i], error_threshold)
        target_amplitude = volume
        if use_safe_amplitude:
            target_amplitude = dpcm.safe_amplitude(tuning["effective_frequency"], playback_rate) * volume
        pcm = generate_pcm(tuning, waveform_generator, playback_rate, target_amplitude, target_bias)
        dpcm_data = dpcm.to_dpcm(pcm, 0)
        sample_name = midi.note_name(i)
        sample_table.append({"name": instrument_name+sample_name, "data": dpcm_data})
        note_mappings.append({"midi_index": i + 12, "sample_index": sample_index, "pitch": 0xF, "looping": True, "delta": set_delta})
        sample_index += 1
        bias = dpcm.bias(dpcm_data)
        if not quiet:
            print("{}: Err: {:.2f}, Size: {}, Reps: {}, E. Freq: {:.2f}, E.Ampl {:.2f}, Bias: {}".format(
                midi.note_name(i), tuning["error"], tuning["size"], tuning["repetitions"],
                tuning["effective_frequency"], target_amplitude, bias))
    return sample_table, note_mappings

def parse_note_list(note_list_str):
    entries = note_list_str.split(",")
    note_list = []
    for entry in entries:
        notes = entry.split("-")
        if len(notes) == 1:
            note_list.append(midi.note_index(entry))
        else:
            for i in range(midi.note_index(notes[0]), midi.note_index(notes[1]) + 1):
                note_list.append(i)
    return note_list

def main():
    examples = """
    Examples:
      Sawtooth, Sunsoft style:
        %(prog)s -g sawtooth -i sunsaw.fti as2-d3

      Half-volume triangle, positive bias:
        %(prog)s -g triangle -v 0.5 -b 1 -i tri-50.fti c4-c5

      Custom waveform:
        %(prog)s -g wave -w organ.wav -i organ.fti c4-c5
    """
    generators = {
        "sine": waveform.sine, 
        "square": waveform.square, 
        "triangle": waveform.triangle, 
        "sawtooth": waveform.sawtooth, 
        "wave": waveform.wave_file, 
        "artificial_ramp": waveform.artificial_ramp,
    }
    parser = argparse.ArgumentParser(
        description="Automatically generate looping DPCM samples", 
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=examples)
    parser.add_argument("notes", help="Notes to generate. Ex: gs2,f3-a3")

    generator_group = parser.add_argument_group("Sample Generation")
    generator_group.add_argument("-g", "--generator", metavar="GENERATOR", 
        help="One of: {}".format(", ".join(generators.keys())), 
        choices=generators, default="sine")
    generator_group.add_argument("-w", "--wavefile", help="For the wave generator. Should contain one loop, like N163.")
    generator_group.add_argument("-v", "--volume", help="Linear volume multiplier for generated waveforms", type=float, default=1.0)
    generator_group.add_argument("-e", "--error-threshold", help="Prefer smaller samples within this tuning percentage (default: 0%%)", type=float, default=0.0)
    generator_group.add_argument("-b", "--bias", help="Bias generated samples in this direction. (default: 0)", type=int, default=0)
    generator_group.add_argument("-l", "--max-length", help="Longest sample size to consider. Generally improves tuning, costs more space. (default: 255)", type=int, default=255)
    generator_group.add_argument("--safe-volume", help="Scale volume for high notes, to avoid triangle shape creep.", type=bool, action=argparse.BooleanOptionalAction, default=True)

    instrument_group = parser.add_argument_group("FamiTracker Instruments")
    instrument_group.add_argument("-i", "--instrument", help="FamiTracker instrument filename to generate")
    instrument_group.add_argument("-d", "--delta", help="Set the delta counter when playback begins", type=int, default=-1)
    instrument_group.add_argument("--repitch", help="Fill out an instrument's lower range with repitched samples", type=bool, action=argparse.BooleanOptionalAction, default=True)

    args = parser.parse_args()

    generator = generators[args.generator]
    if args.generator == "wave":
        if args.wavefile:
            generator = waveform.wave_file(args.wavefile)
        else:
            exit("Error: wave generator requires -w, --waveform")

    if args.instrument:
        instrument_name = args.instrument
        note_list = parse_note_list(args.notes)
        sample_table, note_mappings = generate_samples(
            generator,
            note_list,
            volume=args.volume,
            use_safe_amplitude=args.safe_volume,
            target_bias=args.bias,
            error_threshold=args.error_threshold,
            max_length_bytes=args.max_length,
            set_delta=args.delta,
            prefix=instrument_name,
            )
        note_mappings = fti.fill_lower_samples(note_mappings)

        output = io.open(instrument_name, "wb")
        fti.write_dpcm_instrument(output, "DPCM {}".format(instrument_name), note_mappings, sample_table)
        output.close()
    else:
        print("Oops, only instrument generation is supported at the moment")

if __name__ == "__main__":
    # execute only if run as a script
    main()