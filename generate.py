import dpcm
import fti
import midi
import waveform

# python stdlib
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


# DEBUG
playback_rate = 33144
error_threshold = 0.005
sample_table = []
note_mappings = []
tuning_table = generate_tuning_table(playback_rate, 255)
sample_index = 1
generator = waveform.triangle
instrument_name = "triangle-bias"
amplitude = 1.0
target_bias = -1.0
delta_counter = -1

for i in range(midi.note_index("c2"), midi.note_index("c3") + 1):
    tuning = smallest_acceptable(tuning_table[i], error_threshold)
    adjusted_amplitude = dpcm.safe_amplitude(tuning["effective_frequency"], playback_rate) * amplitude
    pcm = generate_pcm(tuning, generator, playback_rate, adjusted_amplitude, target_bias)
    dpcm_data = dpcm.to_dpcm(pcm)
    sample_name = midi.note_name(i)
    sample_table.append({"name": instrument_name+sample_name, "data": dpcm_data})
    note_mappings.append({"midi_index": i + 12, "sample_index": sample_index, "pitch": 0xF, "looping": True, "delta": delta_counter})
    sample_index += 1
    bias = dpcm.bias(dpcm_data)

    print("{}: Err: {:.2f}, Size: {}, Reps: {}, E. Freq: {:.2f}, E.Ampl {:.2f}, Bias: {}".format(
        midi.note_name(i),
        tuning["error"],
        tuning["size"],
        tuning["repetitions"],
        tuning["effective_frequency"],
        adjusted_amplitude,
        bias
        ))

note_mappings = fti.fill_lower_samples(note_mappings)

output = io.open("dpcm-{}.fti".format(instrument_name), "wb")
fti.write_dpcm_instrument(output, "DPCM {}".format(instrument_name), note_mappings, sample_table)
output.close()
