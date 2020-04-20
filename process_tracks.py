import argparse
import glob
import os

import pretty_midi
from utils import read_json_data, write_json_data

def get_instrument_info(path):
    """
        Read the instrument path and return needed informations about the instrument

        :param path: The instrument path

        :return: The instrument's notes informations
    """
    print (path)
    mini_data = pretty_midi.PrettyMIDI(path)

    # NOTE: The number of instrument MUST be equaled to 1
    # We only export the score of one instrument at a time
    num_instruments = len(mini_data.instruments)
    # print (mini_data.instruments)
    if num_instruments != 1:
        raise Exception(
            f"Number of instruments is {num_instruments}"
            f" which does not equal to 1"
        )

    instrument = mini_data.instruments[0]
    notes = instrument.notes

    if len(notes) <= 0:
        raise Exception(
            f"Number of notes is less than or equivalent to 0"
        )

    # Read notes info, here we transform the notes in which
    # the first note always starts at 0
    notes_info = []
    offset = notes[0].start
    for idx, note in enumerate(notes):
        notes_info.append({
            "index": idx,
            "start": note.start - offset,
            "duration": note.end - note.start,
        })

    return {
        "name": instrument.name,
        "notes": notes_info,
    }

def do_notes(in_dir):
    """
        Read tracks info inside the in_dir folder and write
        tracks info to the tracks.json file

        :param in_dir: Input dir

        :return None
    """
    # create or read tracks json
    out_file = f"{in_dir}/tracks.json"
    if os.path.exists(out_file):
        out_json = read_json_data(out_file)
    else:
        out_json = {
            "instruments": {}
        }

    # we update this object
    instruments_json = out_json["instruments"]

    # get instruments info and update tracks json
    for path in glob.glob(f"{in_dir}/scores/*.mid"):
        instrument_name = path.split("\\")[-1].replace(".mid", "")
        instrument_info = get_instrument_info(path)

        instruments_json[instrument_name] = instrument_info

    # write tracks json
    write_json_data(out_file, out_json)
    print (f"Write file {out_file}")

def bbt_to_second(bpm, ppq, bbt, time_signature):
    """
        Convert bar:beat:tick to second from FL studio

        :param bpm: Number of beats per minute
        :param ppq: Number of pulses per quarter note (one quarter note = one beat)
        :param bbt: Bar:beat:tick from FL studio
        :param time_signature: The time signature numerator:denominator

        :return: Second for the bbt
    """
    # get bbt parts
    parts = bbt.split(":")
    bar = float(parts[0])
    beat = float(parts[1])
    tick = float(parts[2])

    # get time signature parts
    parts = time_signature.split(":")
    numerator = float(parts[0])
    denominator = float(parts[1])

    # calculate the number of beats have passed
    past_beats = (bar - 1) * numerator + (beat - 1) + tick / ppq

    # calcuate into number of seconds
    past_seconds = past_beats * (60 / bpm)

    return past_seconds

def do_mappings(in_dir):
    """
        Update the mappings likes convert bbt to second

        :param in_dir: The input project dir

        :return: None
    """
    tracks_file = f"{in_dir}/tracks.json"

    tracks_json = read_json_data(tracks_file)
    tracks_data = tracks_json["tracks_data"]

    bpm = tracks_data["bpm"]
    ppq = tracks_data["ppq"]
    time_signature = tracks_data["time_signature"]
    mappings = tracks_data["mappings"]

    for mapping in mappings:
        loops_data = mapping.get("loops_data")
        if loops_data:
            between_first_s = bbt_to_second(
                bpm, ppq, loops_data.get("between_first_bbt", "1:01:00"), time_signature
            )
            between_second_s = bbt_to_second(
                bpm, ppq, loops_data.get("between_second_bbt", "1:01:00"), time_signature
            )
            loops_data["between"] = between_second_s - between_first_s

            for loop in loops_data["loops"]:
                print (loop)
                loop["start"] = bbt_to_second(
                    bpm, ppq, loop["start_bbt"], time_signature
                )

    write_json_data(tracks_file, tracks_json)
    print (f"Write file {tracks_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--do_mappings", action="store_true")
    parser.add_argument("--do_notes", action="store_true")
    parser.add_argument("--in_dir", default="scores", required=True)

    args = parser.parse_args()

    if args.do_notes:
        do_notes(args.in_dir)

    if args.do_mappings:
        do_mappings(args.in_dir)
