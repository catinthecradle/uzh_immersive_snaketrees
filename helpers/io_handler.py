#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.
import os.path
import sys
import getopt
from enum import Enum


class IOHandler:
    __verbose_mode = False

    @staticmethod
    def set_verbose_mode(mode: bool):
        IOHandler.__verbose_mode = mode

    @staticmethod
    def read_main_arguments(argv, input_folder="", output_folder="", limit=None):
        opts, args = getopt.getopt(
            args=argv,
            shortopts="hvi:o:l:s:",
            longopts=["help", "ifolder=", "ofolder=", "limit=", "skip=", "verbose"]
        )
        skip = 0
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print('main.py -i <input folder> -o <output folder> [-l <limit>] [-s <skip>] [-v]')
                sys.exit()
            elif opt in ("-i", "--ifolder"):
                input_folder = arg
            elif opt in ("-o", "--ofolder"):
                output_folder = arg
            elif opt in ("-l", "--limit"):
                limit = int(arg)
            elif opt in ("-s", "--skip"):
                skip = int(arg)
            elif opt in ("-v", "--verbose"):
                IOHandler.set_verbose_mode(True)
        return input_folder, output_folder, limit, skip
    
    @staticmethod
    def verify_folder_exists(path):
        if not os.path.isdir(path):
            IOHandler.print_color(
                message=f"ERROR: Input folder does not exist: {path}",
                color=Color.RED,
                enforce=True
            )
            sys.exit(0)
        
    @staticmethod
    def confirm_no_limit():
        print("========")
        print("You did not set a limit. This might take a while... Are you sure you want to proceed?")
        confirm = input("Please confirm [y/n]: ")
        while True:
            if confirm in ("y", "Y"):
                print("You said 'yes', I will proceed without limit")
                return None
            elif confirm in ("n", "N"):
                # Set limit
                while True:
                    new_limit = input("Set limit or type q to exit: ")
                    if new_limit == 'q':
                        sys.exit()
                    try:
                        limit = int(new_limit)
                        return limit
                    except ValueError:
                        print("This is not a valid number!")
            confirm = input("Please confirm if you want to proceed by typing y (yes) or n (no): ")

    @staticmethod
    def read_and_confirm_main_arguments(argv, input_folder="", output_folder="", limit=None):
        input_folder, output_folder, limit, skip = (IOHandler.read_main_arguments(
            argv, input_folder, output_folder, limit))
        IOHandler.verify_folder_exists(input_folder)
        if not limit:
            limit = IOHandler.confirm_no_limit()
        return input_folder, output_folder, limit, skip

    @staticmethod
    def print_spacer(color=None, enforce=False):
        IOHandler.print_color(
            message="-----------------------------------------------------------------------",
            color=color,
            enforce=enforce,
        )

    @staticmethod
    def print_title_line(color=None, enforce=False):
        IOHandler.print_color(
            message="=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=",
            color=color,
            enforce=enforce,
        )

    @staticmethod
    def print_text_line(text="", color=None, enforce=False):
        blank = "======================================================================="
        if text != "":
            text = f" {text} "
        delta = len(blank) - len(text)
        if delta > 0:
            start_pos = delta // 2
            end_pos = start_pos + len(text)
            text_line = blank[0:start_pos] + text + blank[end_pos:]
        else:
            text_line = text
        IOHandler.print_color(
            message=text_line,
            color=color,
            enforce=enforce,
        )
        
    @staticmethod
    def set_text_color(color):
        if color == Color.RED:
            print('\033[91m', end="")
        elif color == Color.GREEN:
            print('\033[92m', end="")
        elif color == Color.BLUE:
            print('\033[94m', end="")
        elif color == Color.YELLOW:
            print('\033[93m', end="")

    @staticmethod
    def reset_colors():
        print('\033[0m', end="")
    
    @staticmethod
    def print_color(message, color=None, end=None, enforce=False):
        if enforce or IOHandler.__verbose_mode:
            IOHandler.set_text_color(color)
            print(message, end=end)
            IOHandler.reset_colors()
    
    @staticmethod
    def show_error(message):
        IOHandler.print_color(
            message=message,
            color=Color.RED,
            enforce=True
        )


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3
    YELLOW = 4
