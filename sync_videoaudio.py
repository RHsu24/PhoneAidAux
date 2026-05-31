import subprocess
import wave
import csv
import io
import os
import argparse
from scipy import signal
import numpy as np
import pandas as pd

AUDIO_SR = 16000 

def read_transcript(word_ts):
    ts_data = []
    try:
        with open(word_ts, mode='r',newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            ts_data = list(reader)
    except FileNotFoundError:
        print(f"Error: The file {word_ts} was not found.")
    except PermissionError:
        # Catches invalid formats, corrupt files, or non-WAV files
        print(f"Error: Insufficient permission to read CSV file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return ts_data

def parse_transcript_info(word_ts):
# Transcript -> CSV file with timestamps of sentences
# Parse through CSV and return only necessary data
    try:
        df = pd.read_csv(word_ts, usecols=['tmin', 'tier', 'text', 'tmax'], 
                             on_bad_lines='error')
        df.dropna(how='any',inplace=True)
    except pd.errors.ParserError:
        print(f"Error: There was a parsing error (e.g., malformed data).")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return df

def wav_read(wav): 
    wav_info = None
    try: 
        #print(f"Checking file: {wav}, Size: {os.path.getsize(wav)} bytes")
        with wave.open(wav,'rb') as wav_file:
            # Extract specific data to return
            wav_info = wav_file.getparams()

    except FileNotFoundError:
        print(f"Error: The file {wav_file} was not found.")
    except wave.Error as e:
        # Catches invalid formats, corrupt files, or non-WAV files
        print(f"Error: Could not read WAV file. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    print(f"Parsed Audio into Memory")
    return wav_info

def extract_audio_from_mp4(video_path, wav_info):
    # Extract audio from the mp4, and match the .wav metadata
    command = [
        'ffmpeg',
        '-i', video_path,
        '-vn',                          # Disable video
        '-acodec', 'pcm_s16le',         # 16-bit PCM WAV
        '-ar', str(AUDIO_SR),           # match .wav track rate
        '-ac', str(wav_info.nchannels), # Downmix to 1 Channel (Mono)
        '-f', 'wav',                    # WAV container format
        'pipe:1'                        # Output directly to memory
    ]
    
    process = subprocess.run(command, stdout= subprocess.PIPE, stderr= subprocess.DEVNULL, check=True)
    return io.BytesIO(process.stdout)

def ffmpeg_resample(audio):
    command = [
        'ffmpeg',
        '-i', audio,
        '-ar', str(AUDIO_SR),       # match .wav track rate
        '-f', 'wav',                # WAV container format
        'pipe:1'                    # Output directly to memory
    ]
    process = subprocess.run(command, stdout= subprocess.PIPE, stderr= subprocess.DEVNULL, check=True)
    return io.BytesIO(process.stdout)

def perform_ccorr(wav_filtered, search_region):
    match_pt = signal.correlate(wav_filtered, search_region, mode='full')
    lags = signal.correlation_lags(len(wav_filtered), len(search_region), mode='full')

    corr_max = np.argmax(np.abs(match_pt))
    frame_offset = lags[corr_max]
    match_pt_t = frame_offset / AUDIO_SR # should always be -ve aka .mp4 starts "late" vs .wav file 
    # print(f'The audio file matches to .mp4 at frame {frame_offset}, which corresponds to an offset of {match_pt_t} seconds')

    return frame_offset, match_pt_t


def find_offset(wav_16k, slice_data, mp4_audio):
    """
    Finds the offset between 16kHz WAV and MP4 audio arrays.
    Positive result: mp4_data starts LATER than wav_data.
    Negative result: mp4_data starts EARLIER than wav_data.
    """

    # For simplicity, audio from .wav file is prefixed wav, 
    # while audio extracted from .mp4 file is prefixed mp4
    first_word = slice_data[0]
    start_cut = float(first_word['tmin'])
    last_word = slice_data[-1]
    last_word_end = float(last_word['tmax']) 
    total_frames = round((last_word_end - start_cut)  * AUDIO_SR)
    print(f"Total span of speech audio: {start_cut}s to {last_word_end}s: total {total_frames} frames.")

    wav_16k.seek(0)
    mp4_audio.seek(0)
    mp4_params = wav_params = mp4_data = wav_data = None

    # not actually .mp4, but .wav extracted from .mp4
    with wave.open(mp4_audio, "rb") as mp4_file:
        mp4_params = mp4_file.getparams()

        # Read non-zero frames (FFmpeg has unterminated buffer)
        raw_mp4 = mp4_file.readframes(-1)
        mp4_data = np.frombuffer(raw_mp4, dtype=np.int16) # PCM16

        with wave.open(wav_16k, "rb") as wav_file:
            raw_wav = wav_file.readframes(-1)
            # Find entire audio file
            wav_data = np.frombuffer(raw_wav, dtype = np.int16)
            wav_params = wav_file.getparams()


        assert mp4_params.framerate == wav_params.framerate

        # Because we have same audio waveform from two different sources, assuming the data types
        # are the same (bitrate, sr, channels, lossless) we know there will be an exact waveform
        # match as long as we can scale the amplitude (raw PCM data) and filter noise

        # Filter out source-specific noise (Bandpass 300Hz - 4kHz)
        # Should isolate speech audio and drops low hums and high hiss
        b, a = signal.butter(4, [300, 4000], btype='bandpass', fs=AUDIO_SR)
        wav_filtered = signal.filtfilt(b, a, wav_data)
        mp4_filtered = signal.filtfilt(b, a, mp4_data)

        # Normalize amplitude to eliminate recording volume differences
        wav_filtered = (wav_filtered - np.mean(wav_filtered)) / (np.std(wav_filtered) + 1e-8)
        mp4_filtered = (mp4_filtered - np.mean(mp4_filtered)) / (np.std(mp4_filtered) + 1e-8)

        ###  Compute cross-correlation 
        frame_offset, match_t = perform_ccorr(wav_filtered, mp4_filtered)
   
        print(f'Cross-correlation shows first aligned speech in .wav starts in the .mp4 at frame {abs(frame_offset)} , i.e. {abs(match_t)} secs in to .mp4 file')

        return abs(match_t)
    
def apply_offset(match_t, csv_file):
    df = parse_transcript_info(csv_file)
    df_tmin = df['tmin'].to_numpy()
    df_tmax = df['tmax'].to_numpy()

    mp4_tmin = np.empty(len(df_tmin))
    mp4_tmax = np.empty(len(df_tmax))
    first_min = df_tmin[0]

    for i, (min, max) in enumerate(zip(df_tmin, df_tmax)):
        mp4_tmin[i] = (min - first_min) + match_t 
        mp4_tmax[i] = mp4_tmin[i] + (max - min)

    df_new = df.copy()
    df_new["video_min"] = mp4_tmin
    df_new["video_max"] = mp4_tmax

    # Save to csv
    print(f'Saved to .csv in current directory')
    df_new.to_csv("750.csv", index=False)

def process_input(transcript_dir, data_dir, mp4_dir):
        # Transcript PATH is not optional
    if transcript_dir is not None:
        if not os.path.exists(transcript_dir):
            raise FileNotFoundError(f'Please input valid .csv file PATH before running the following code.')
        path_ts = transcript_dir
        transcriptions = read_transcript(path_ts)

    else:
        raise FileNotFoundError(f'Please input transcription .csv file PATH before running the following code.')
    
    if data_dir is not None:
        if not os.path.exists(data_dir):
               raise FileNotFoundError(f'Please prepare the .wav file before running the following code.')

    if mp4_dir is not None:
        if not os.path.exists(mp4_dir):
               raise FileNotFoundError(f'Please prepare the .mp4 file before running the following code.')

    return transcriptions

def main():
    # Parse Cmd line arguments
    script_name = os.path.basename(__file__)
    parser = argparse.ArgumentParser()
    parser.add_argument('transcript_dir', type=str, default = None,
                        help="Absolute or Relative file path to the .csv transcription file")
    # Arg for task 1 and testing purposes
    parser.add_argument('wav_dir', type=str, default = None,
                        help="Absolute or Relative file PATH to the .wav file.")
    parser.add_argument('mp4_dir', type=str, default = None,
                        help="Absolute or Relative file PATH to the .wav file.")
    args = parser.parse_args()
    slice_data = process_input(args.transcript_dir, args.wav_dir, args.mp4_dir)

    # Load files
    wav_track = args.wav_dir 
    mp4_track = args.mp4_dir 
    csv_file = args.transcript_dir 

    # Process audio
    wav_16k = ffmpeg_resample(wav_track)
    wav_info = wav_read(wav_16k)
    mp4_audio = extract_audio_from_mp4(mp4_track, wav_info)

    # Find and apply alignment
    offset_t = find_offset(wav_16k, slice_data, mp4_audio)
    apply_offset(offset_t,csv_file)

if __name__ == '__main__':
    main()
