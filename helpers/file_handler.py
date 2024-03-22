#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

import os
import re
import yaml
from helpers.timer import Timer
from helpers.io_handler import IOHandler

# Define config file
script_dir = os.path.dirname(__file__)
CONFIG_FILE = os.path.normpath(os.path.join(script_dir, '../config.yaml'))


class FileHandler:
    pass

    @staticmethod
    def create_file_list_from(path, limit=None):
        IOHandler.print_color(message="Creating media files list... ", end="")
        media_timer = Timer()
        omit_pattern = re.compile('^[.]|^(?!.*[.]mp4$)')
        file_list = []
        for (dir_path, subdirectories, file_names) in os.walk(path):
            for file_name in file_names:
                if omit_pattern.search(file_name):
                    continue
                abs_media_path = os.path.join(dir_path, file_name)
                rel_media_path = os.path.relpath(abs_media_path, path)
                rel_output_prefix = re.sub("[.]mp4$", "", rel_media_path)
                file_params = abs_media_path, rel_media_path, rel_output_prefix
                file_list.append(file_params)
        file_list.sort(key=FileHandler.sort_by_video_name)
        if limit is not None:
            file_list = file_list[:limit]
        media_timer.print_seconds()
        return file_list

    @staticmethod
    def sort_by_video_name(x):
        name = x[2].split("/")[-1]
        try:
            name = int(name)
        except ValueError:
            name = 0
        return name

    @staticmethod
    def create_folders_if_not_exists(filename):
        directory = os.path.dirname(filename)
        if directory != "":
            os.makedirs(directory, exist_ok=True)

    @staticmethod
    def write_to_txt(filename, content):
        FileHandler.create_folders_if_not_exists(filename)
        with open(filename, "w") as f:
            f.write(content)
    
    @staticmethod
    def read_config_file():
        with open(CONFIG_FILE, 'r') as yaml_file:
            return yaml.safe_load(yaml_file)
