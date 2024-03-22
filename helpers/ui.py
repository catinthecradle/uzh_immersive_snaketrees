#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

from helpers.io_handler import IOHandler, Color
from helpers.converter import Converter


class UI:
    @staticmethod
    def start_line():
        IOHandler.print_text_line(text="START", color=Color.BLUE, enforce=True)

    @staticmethod
    def end_line():
        IOHandler.print_text_line(text="END", color=Color.BLUE, enforce=True)

    @staticmethod
    def spacer():
        IOHandler.print_spacer()

    @staticmethod
    def metadata_information(db_num_media, db_totals):
        # Print database and metadata information
        IOHandler.print_title_line(color=Color.BLUE)
        IOHandler.print_color(
            message=f"There are {db_num_media} media entries in the database",
            color=Color.BLUE
        )
        IOHandler.print_color(
            message=f"- with a total size of {db_totals['size_gb']:.3f} GB",
            color=Color.BLUE
        )
        IOHandler.print_color(
            message=f"- and a total duration of {Converter.seconds_to_dhms_str(db_totals['duration_sec'])}",
            color=Color.BLUE
        )
        IOHandler.print_title_line(color=Color.BLUE)

    @staticmethod
    def overall_information(db_totals, db_num_media, overall_time, num_counter, duration_counter):
        # Print info for overall execution time
        IOHandler.print_title_line(color=Color.BLUE, enforce=True)
        # Skips, if num_counter or duration_counter are zero
        if num_counter * duration_counter <= 0:
            IOHandler.print_color(
                message="Did not execute a single song => cannot give any estimations.",
                color=Color.BLUE,
                enforce=True
            )
            return
        avg_time_per_song = overall_time / num_counter
        estimate_from_duration = Converter.seconds_to_dhms_str(
            db_totals['duration_sec'] / duration_counter * overall_time)
        IOHandler.print_color(
            message=Converter.overall_song_execution_time_str(num_counter, overall_time),
            color=Color.BLUE,
            enforce=True
        )
        IOHandler.print_color(
            message=f"On average {avg_time_per_song:.3f} seconds per song",
            color=Color.BLUE,
            enforce=True
        )
        IOHandler.print_color(
            message=f"This estimates an overall execution time of {estimate_from_duration} "
                    f"for all {db_num_media} songs",
            color=Color.BLUE,
            enforce=True
        )

    @staticmethod
    def song_process_time(duration):
        IOHandler.print_color(
            message=f"==> Process time for current song: {duration:.3f} seconds"
        )

    @staticmethod
    def db_metadata_not_found_error(media_path) -> str:
        message = f"No data for {media_path} received from database!"
        IOHandler.print_color(
            message=f"{message}\n",
            color=Color.RED,
            enforce=True
        )
        return message
