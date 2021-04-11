import midi
import dpcm
import waveform

# python stdlib
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

def generate_pcm(tuning, generator, playback_rate):
    pcm = []
    for i in range(0, tuning["samples"]):
        sample = waveform.sample(generator, i, tuning["effective_frequency"], playback_rate)
        sample_8bit = int(min(255, max(0, sample * 256)))
        pcm.append(sample_8bit)
    return pcm

def write_waveform(filename, pcm_data, playback_rate):
    writer = wave.open(filename, mode="wb")
    writer.setnchannels(1)
    writer.setsampwidth(1)
    writer.setframerate(int(playback_rate))
    writer.writeframes(bytes(pcm_data))
    writer.close()

# DEBUG
playback_rate = 33144
error_threshold = 0.01
tuning_table = generate_tuning_table(playback_rate, 255)
for i in range(midi.note_index("c0"), midi.note_index("c5")):
    tuning = smallest_acceptable(tuning_table[i], error_threshold)
    pcm = generate_pcm(tuning, waveform.triangle, playback_rate)
    makedirs("samples/triangle",exist_ok=True)
    filename = "samples/triangle/{:03d}-{}-triangle.wav".format(i, midi.note_name(i))
    print(filename)
    write_waveform(filename, pcm, playback_rate)



    #print("{}: Phase: {:.2f}, Error: {:.2f}, Bytes: {}, Repetitions: {}, E. Freq: {:.2f}".format(
    #    midi.note_name(i),
    #    tuning["phase_offset"],
    #    tuning["error"],
    #    tuning["size"],
    #    tuning["repetitions"],
    #    tuning["effective_frequency"]
    #    ))




