import requests
from pathlib import Path
import json
import xlsxwriter
import os
import glob
import argparse

def simple_split(namelist, slice):
    
    word_extr = []
    rubbish = namelist.rpartition("_")
    if slice == 0: #cuts out the number at the end
        word_extr = rubbish[0]
    if slice == 1: #keeps word_id as of files
        word_id = rubbish[2].split(".")
        word_extr = word_id[0]
    return word_extr

def simple_truncate(namelist):
    new_dir = []
    rubbish = namelist.split("_",1)
    new_dir = rubbish[0]
    # print(new_name)
    return new_dir

def send_speech_analysis_request(
    speech_file_path,
    target_word,
    lang,
    age_cat,
    server_url="http://127.0.0.1:8000/analyze/",
):
    
    with open(speech_file_path, "rb") as f:
        files = {"speech_signal": f}
        data = {
            "target_word": target_word,
            "lang": lang,
            "age_cat": age_cat,
        }
        response = requests.post(server_url, files=files, data=data, timeout=120)
    if response.status_code == 200:
        return response.json()
    raise Exception(f"Error: {response.status_code}, {response.text}")


def request_write(child_id):
    #change rw_folder to path with segmented .wav files you want to analyse
    rw_folder = Path.cwd()
    child_files = rw_folder / str(child_id)

    os.chdir(child_files)
    wb_name = str(child_id) +'_results.xlsx'
    #Excel spreadsheet initialisation, do only once
    workbook = xlsxwriter.Workbook(wb_name)
    worksheet = workbook.add_worksheet()
    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': True})
    worksheet.write('A1', 'Child_ID', bold)
    worksheet.write('B1', 'word_id', bold)
    worksheet.write('C1', 'word', bold)
    worksheet.write('D1','Sound_ID', bold)
    worksheet.write('E1','Phoneme_expected', bold)
    worksheet.write('F1','Phoneme_recognised', bold)
    worksheet.write('G1','PhoneAid_Evaluation', bold)
    worksheet.write('H1','PhoneAid_binary', bold)

    # Start from the first cell below the headers.
    row = 1
    col = 0
    word_count = 0
    print("Outputting Request Arguments...")
    for files in glob.glob("*.wav"):

        speech_file_path = files
        result = send_speech_analysis_request(
        speech_file_path=speech_file_path,
        target_word=simple_split(speech_file_path,0),
        lang="en_aus",
        age_cat="c",
        server_url="https://phoneaid-service-948892252068.australia-southeast1.run.app/analyze/",
        )

        test = json.dumps(result, ensure_ascii= False)
        parsing = json.loads(json.loads(test))
        phoneme = parsing["Phoneme"]
        exp = phoneme["Assess"]["Expected_aligned"]
        rec = phoneme["Assess"]["Recognized_aligned"]
        err = phoneme["Assess"]["Errors"]

        target_word = simple_split(speech_file_path,0)
        word_id = simple_split(speech_file_path,1)
        
        for ph_count, (e, r, tag) in enumerate(zip(exp, rec, err), start=1):
            #print(f"{i:02d}. {e} -> {r} [{tag}]")
            phn_list = 'Ph' + str(ph_count)
            worksheet.write(row,col,child_id)
            worksheet.write(row,col+1, word_id) # check if this needs to be included
            worksheet.write(row,col+2, target_word)
            worksheet.write(row,col+3,phn_list)
            worksheet.write(row,col+4, e) #expected
            worksheet.write(row,col+5, r) #recognised
            worksheet.write(row,col+6,tag)  # H/S/I/D
            if tag == 'H':
                worksheet.write(row,col+7,'1')
            else:
                worksheet.write(row,col+7,'0')
            row+=1
        word_count += 1

    workbook.close()
    print(f"Speech Analysis Done! There were {word_count} words analysed")

def main():
    cwd = Path.cwd()
    rw_folder = cwd / 'task1'
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=str, default=rw_folder,
                        help="Relative file path to the .wav and annotation files.")
    args = parser.parse_args()

    rd_folder = cwd / args.data_dir
    # Output dir
    if not os.path.exists(rd_folder):
        os.chdir(rw_folder)
        print(rw_folder)
    else:
        os.chdir(rd_folder)

    for i in range(b):
        print(f'Evaluating files for Patient {a[i]}')
        request_write(a[i])

if __name__ == '__main__':


    welcome_msg = "This is here to show it is running\n"
    print(welcome_msg)
    # Create an empty list to store the inputs
    a = []

    # Ask the user for how many items they want to input
    b = int(input("How many IDs do you want to enter? "))

    # Loop to collect multiple inputs
    for i in range(b):
        val = input(f"Enter Child ID #{i + 1}: ")
        a.append(val)
    main()