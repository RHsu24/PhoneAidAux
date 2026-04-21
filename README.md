speech_segment.py is designed to segment complete audio (.wav) files into single words as listed in a 
corresponding .csv file. It will also create a corresponding directory if it does not already exist.

word_send.py is designed to run requests to the PhoneAid server by evaluating single words
at a time and writing the output returned directly to an .xlsx file. The script can take multiple IDs
to evaluate at a time, by specifying the # of IDs to evaluate, and the ID### itself.

How to run:

By default, both scripts are designed to be placed one (1) directory level above the complete (unsegmented)
audio files and annotated .csv files, and two (2) directory levels above the resultant segmented .wav files 
and output .xlsx files.

Example:

py speech_segment.py [folder]
where [folder] is the directory holding the unsegmented audio file and corresponding .csv file

py word_send.py [folder]
where [folder] is the directory holding the unsegmented audio file and corresponding .csv file

Both are not intended to be run on a server, and rather on a local directory. It is possible it may work on 
server files, but I have not tested it and is up to user to modify code to fit the use, notably in:
speech_segment.py:
- modifying [cwd] and [rw_folder] on Line 90 & 91 to match filepath [cwd/rw_folder]
- modifying Line 13 "_corrected" to match end part of annotated .csv file name (e.g. annotated file name has
000_task1_kaldi.csv, adjust it to "_kaldi"). If no end part, then adjust it to "."

word_send.py:
- modifying [cwd] and [rw_folder] on Line 116 & 117 to match filepath [cwd/rw_folder]
