#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

import os
import sys
import getopt
from helpers.file_handler import FileHandler
from helpers.io_handler import IOHandler

WINDOW_SIZE = 100


def read_main_arguments(argv):
    opts, args = getopt.getopt(
        args=argv,
        shortopts="ho:i:f:l:",
        longopts=["help", "ofolder=", "ifolder=", "first=", "last="]
    )
    input_folder = "/Volumes/MJF Videos/MP4"
    output_folder = ""
    first = 1
    last = 0
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('memory_safe_runner.py [-i <input folder> -o <output folder> -f <first> -l <last>]')
            sys.exit()
        elif opt in ("-o", "--ofolder"):
            output_folder = arg
        elif opt in ("-i", "--ifolder"):
            input_folder = arg
        elif opt in ("-f", "--first"):
            first = int(arg)
        elif opt in ("-l", "--last"):
            last = int(arg)
    return input_folder, output_folder, first, last


def get_command_params(first, last):
    skip = first - 1
    limit = min(skip + WINDOW_SIZE, last)
    return skip, limit


def main(argv):
    input_folder, output_folder, first, last = read_main_arguments(argv)

    # Assert that input_folder exists
    if not os.path.exists(input_folder):
        IOHandler.show_error(f"ERROR: Input folder does not exist: {input_folder}")
        sys.exit()

    # Create command template
    command_template = f"python main.py -i '{input_folder}' -o '{output_folder}' " + "-s {} -l {}"

    # Floor first to 1
    first = max(first, 1)

    # Ceil last to the actual number of files in the input_folder
    media_file_list = FileHandler.create_file_list_from(input_folder)
    files_count = len(media_file_list)
    if last > 0:
        last = min(last, files_count)
    else:
        last = files_count

    os.system("echo STARTING...")

    # Loop from first to last using window size
    while first <= last:
        skip, limit = get_command_params(first, last)
        command = command_template.format(skip, limit)
        print(command)
        os.system(command)
        first += WINDOW_SIZE

    os.system("echo ...DONE!")


if __name__ == '__main__':
    main(sys.argv[1:])
