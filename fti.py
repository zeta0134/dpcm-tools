# VERY restricted .fti writer, specifically for DPCM instrument files with almost
# no other supported variations

import dpcm
import midi

# python stdlib
import struct

INST_HEADER = "FTI"
INST_VERSION = "2.4"
INST_2A03 = 1

def write_char(file, value):
  file.write(struct.pack("b", value))

def write_uchar(file, value):
  file.write(struct.pack("B", value))

def write_int(file, value):
  file.write(struct.pack("i", value))

def write_string(file, str):
  file.write(bytes(str, "ascii"))

def write_instrument_header(file, name):
  assert(len(name) < 128)
  write_string(file, INST_HEADER)
  write_string(file, INST_VERSION)
  write_char(file, INST_2A03)
  write_int(file, len(name))
  write_string(file, name)

# We're creating a DPCM instrument, so the
# sequence data is not useful; blank it out for
# this purpose.
def write_empty_sequence_data(file):
  write_char(file, 0) # zero sequences

def write_sample_attributes(file, note_index, sample_index, dpcm_pitch, looping=False, delta=-1):
  pitch_byte = dpcm_pitch & 0xF
  if looping:
    pitch_byte |= 0x80

  write_char(file, note_index)
  write_char(file, sample_index)
  write_uchar(file, pitch_byte)
  write_char(file, delta)

def midi_to_note_index(midi_index):
  note_index = midi_index - 12
  assert(note_index > 0 and note_index < 127)
  return note_index

def write_sample_data(file, name, raw_data):
  write_int(file, len(name))
  write_string(file, name)
  write_int(file, len(raw_data))
  file.write(bytes(raw_data))

def write_dpcm_instrument(file, instrument_name, note_mappings, samples):
  write_instrument_header(file, instrument_name)
  write_empty_sequence_data(file)
  write_int(file, len(note_mappings))
  for note_mapping in note_mappings:
    write_sample_attributes(file, midi_to_note_index(note_mapping["midi_index"]), note_mapping["sample_index"], note_mapping["pitch"], note_mapping["looping"], note_mapping["delta"])
  write_int(file, len(samples))
  for sample_index in range(0, len(samples)):
    sample = samples[sample_index]
    write_int(file, sample_index)
    write_sample_data(file, sample["name"], sample["data"])

def note_by_index(note_mappings, index):
  for note_mapping in note_mappings:
    if note_mapping["midi_index"] == index:
      return note_mapping
  return None

def fill_lower_samples(note_mappings):
  for midi_index in range(12, 127, 1):
    note_mapping = note_by_index(note_mappings, midi_index)
    if note_mapping:
      target_midi_index = midi_index
      for dpcm_pitch in range(note_mapping["pitch"], 0x0, -1):
        target_midi_index = target_midi_index - dpcm.equivalency[dpcm_pitch - 1]
        if target_midi_index > 12:
          # check to see if this note mapping already exists
          target_note_mapping = note_by_index(note_mappings, target_midi_index)
          if target_note_mapping == None:
            # create a new note mapping, with the lower pitch
            print("Will map ", midi.note_name(midi_index), " with dpcm rate ", note_mapping["pitch"], " to lower note ", midi.note_name(target_midi_index), " with dpcm rate ", dpcm_pitch - 1)
            target_note_mapping = {"midi_index": target_midi_index, "sample_index": note_mapping["sample_index"], "pitch": dpcm_pitch - 1, "looping": note_mapping["looping"], "delta": note_mapping["delta"]}
            note_mappings.append(target_note_mapping)
  return note_mappings
