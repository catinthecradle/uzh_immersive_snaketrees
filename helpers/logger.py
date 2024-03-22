#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

import csv
from helpers.converter import Converter
from helpers.file_handler import FileHandler


class Logger:
    def __init__(self, output_folder=""):
        self.__output_folder = output_folder
        self.__logfile = output_folder + "logfile-" + Converter.file_creation_string() + ".csv"

    def write_header(self, header_keys):
        FileHandler.create_folders_if_not_exists(self.__logfile)
        with open(self.__logfile, 'w') as output:
            csv.writer(output).writerow(header_keys)

    def write_entry(self, entry_values):
        with open(self.__logfile, 'a') as output:
            csv.writer(output).writerow(entry_values)


class ExtractionLogger(Logger):
    def __init__(self, output_folder=""):
        super().__init__(output_folder)
        self.__log_entry = {
            'index': "",
            'timestamp': "",
            'media_filepath': "",
            'media_id': "",
            'success': "",
            'details': []
        }
        super().write_header(self.__log_entry.keys())

    def reset_values(self):
        self.__log_entry = {k: "" for k in self.__log_entry}
        self.set_entry_timestamp()
        self.set_value("success", True)
        self.set_value("details", [])

    def set_value(self, key="", value=None):
        if key in self.__log_entry:
            self.__log_entry[key] = value

    def add_detail(self, message):
        self.__log_entry['details'].append(message)

    def add_error(self, message):
        self.set_value("success", False)
        self.add_detail(message)

    def set_entry_timestamp(self):
        self.set_value("timestamp", Converter.current_timestamp())

    def set_media_id_from_media_data(self, media_data):
        if "media_id" in media_data:
            self.set_value("media_id", media_data['media_id'])

    def commit_entry(self, set_timestamp=True):
        if set_timestamp:
            self.set_entry_timestamp()
        super().write_entry(self.__log_entry.values())
