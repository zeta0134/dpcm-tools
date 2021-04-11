import midi
import math

# note: sensible indexes here range from 0-255
def patch_bytes(length_index):
	return 16 * length_index + 1

def patch_samples(length_index):
	return patch_bytes(length_index) * 8

def phase_offset(length_index, target_frequency, playback_rate):
	patch_delta = patch_samples(length_index) / playback_rate
	frequency_delta = 1 / target_frequency
	return (patch_delta % frequency_delta) * target_frequency

def tuning_error(length_index, target_frequency, playback_rate):
    return 0.5 - abs(phase_offset(length_index, target_frequency, playback_rate) - 0.5)

def repetitions(length_index, target_frequency, playback_rate):
    samples = patch_samples(length_index)
    return round(samples / (playback_rate / target_frequency), 0)

def effective_frequency(length_index, repetitions, playback_rate):
    samples = patch_samples(length_index)
    return playback_rate / (samples / max(repetitions,1))