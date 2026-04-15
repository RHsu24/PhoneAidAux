import csv
import os
import glob
import wave
import numpy as np
import math
from pathlib import Path

def truncate_name(namelist):
    new_name = [0 for i in range(len(namelist))]
    new_dir = []
    for n in range(len(namelist)):
            rubbish = namelist[n].split("_corrected",1)
            new_dir = rubbish[0].split("_",1)
            make_dir(new_dir[0])
            if len(rubbish) == 2:
                new_name[n] = rubbish[0]
    # print(new_name)
    return new_name

def make_dir(directory_name):
     # Create the directory for segmented .wav files
    try:
        os.mkdir(directory_name)
        print(f"Directory '{directory_name}' created successfully.")
    except FileExistsError:
        print(f"Directory '{directory_name}' already exists.")
    except PermissionError:
        print(f"Permission denied: Unable to create '{directory_name}'.")
    except Exception as e:
        print(f"An error occurred: {e}") 

def wav_manip(wav_file, dict, namelist):
    word_count = 1
    new_dir = namelist.split("_",1)
    write_folder = Path("C:/Users/ricky/Desktop/Jobs/UCanSay66/First Week/Task1/Task1/PhonAid_to_be_scored/PhonAid_to_be_scored")
    id_path = write_folder / new_dir[0]
    try: 
        with wave.open(wav_file,'rb') as wav_file:
            # print(f'Channels: {wav_file.getnchannels()}')
            # print(f'Sample width: {wav_file.getsampwidth()}')
            # print(f'Frame rate: {wav_file.getframerate()}')
            # print(f'Frames: {wav_file.getnframes()}')

            channels = wav_file.getnchannels()  # Mono or Stereo
            sample_width = wav_file.getsampwidth()  # Bytes
            frame_rate = wav_file.getframerate()    # Sampling Frequency
            frames_tot = wav_file.getnframes()
            comp_type = wav_file.getcomptype()
            comp_name = wav_file.getcompname()
            t_sec = wav_file.getnframes()/wav_file.getframerate()

            

            for row in dict:
                txt_count =  f"{word_count:03d}"
                new_wav_name = str(txt_count) + '_' + row['text'] + '.wav'
                t_start =   float(row['tmin'])
                t_end = float(row['tmax'])
                # print(f'{new_wav_name}, {t_start}, {t_end}')
                word_count += 1
                start_frame = math.floor(t_start*frame_rate)
                end_frame = math.ceil(t_end*frame_rate)
                word_frames_tot = end_frame - start_frame
                wav_file.setpos(start_frame)
                word_bytes = wav_file.readframes(word_frames_tot)
                
                # Prepare to write to specific directory with patient ID
                write_path = id_path / new_wav_name

                print("new Write path success:,")

                with wave.open(str(write_path),'wb') as wav_word:
                    wav_word.setparams((channels, sample_width, frame_rate, word_frames_tot,comp_type,comp_name))
                    wav_word.writeframes(word_bytes)

    except FileNotFoundError:
        print(f"Error: The file {wav_file} was not found.")
    except wave.Error as e:
        # Catches invalid formats, corrupt files, or non-WAV files
        print(f"Error: Could not read WAV file. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None



def append_filename(namelist):
    wav_name = [0 for i in range(len(namelist))]
    for n in range(len(namelist)):
           wav_name = namelist[n].append(".wav")
    #print(wav_name)
    return wav_name


def main():

    file_dir = r'C:\Users\ricky\Desktop\Jobs\UCanSay66\First Week\Task1\Task1\PhonAid_to_be_scored\PhonAid_to_be_scored' # this can be changed to user input
    os.chdir(file_dir)

    # Find all files of csv type
    labfiles = []
    for files in glob.glob("*.csv"):
        labfiles.append(files)
    
    if len(labfiles) == 0:
        print('There are no files with these extensions')
    #else:
        #print(labfiles)
        #new_labfiles = truncate_labfile(labfiles)

    namelist = glob.glob("*.csv")
    # Truncate the filename(s) to access .wav file

    set_name = truncate_name(namelist)
    #print(set_name)
    
    # try get row number
    for n in range(len(set_name)):
        if set_name[n] != 0:
            wav_name = (set_name[n] + '.wav')
            #print(wav_name)
            with open(namelist[n],newline='') as csvfile:
                print(namelist[n])
                reader = csv.DictReader(csvfile)
                wav_manip(wav_name,reader,namelist[n])
                        
        else:
            print(f"Index {n} does not have a filename")
            break

if __name__ == '__main__':

    welcome_msg = "This is here to show it is running\n"
    print(welcome_msg)
    
    main()