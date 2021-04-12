# VERY restricted .fti writer, specifically for DPCM instrument files with almost
# no other supported variations

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

def write_sample_data(file, name, bytes):
  write_int(file, len(name))
  write_string(file, name)
  write_int(file, len(bytes))
  file.write(bytes)

def write_dpcm_instrument(file, instrument_name, note_mappings, samples):
  write_instrument_header(file, instrument_name)
  write_empty_sequence_data(file)
  write_int(file, len(note_mappings))
  for note_mapping in note_mappings:
    write_sample_attributes(file, midi_to_note_index(note_mapping["midi_index"]), note_mapping["sample_index"], note_mapping["pitch"], note_mapping["looping"])
  write_int(file, len(samples))
  for sample_index in range(0, len(samples)):
    sample = samples[sample_index]
    write_int(file, sample_index)
    write_sample_data(file, instrument_name + "-" + sample["name"], sample["data"])