#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.
#
#  Usage:
#  python main.py -i <input folder> -o <output folder>

import sys
from essentia_handlers.tagger import Tagger
from database.db_agent import DBAgent
from models.models import Model
from helpers.timer import Timer
from helpers.file_handler import FileHandler
from helpers.io_handler import IOHandler
from helpers.ui import UI
from helpers.logger import ExtractionLogger
from helpers.errors import UnknownTaggerException


# Read presets from config file
settings = FileHandler.read_config_file()
MEDIA_PATH_ROOT = settings['defaults']['media_path_root']
OUTPUT_FOLDER = settings['defaults']['output_folder']
DATABASE = settings['database']['name']

# Additional parameters
FILE_LIMIT = None

# Get tagger instance according to tagger type specified in config file
try:
    tagger = Tagger.get_instance(settings['tagger'])
except KeyError as error:
    IOHandler.show_error(f"Key not found in config file: {error}")
    sys.exit()
except UnknownTaggerException as error:
    IOHandler.show_error(error)
    sys.exit()


# ----------------------------------
# MAIN
# ----------------------------------
def main(argv):

    input_folder, output_folder, limit, skip = IOHandler.read_and_confirm_main_arguments(
        argv, MEDIA_PATH_ROOT, OUTPUT_FOLDER, FILE_LIMIT)

    program_timer = Timer()
    UI.start_line()

    # Connect to database
    db_agent = DBAgent(DATABASE)
    db_agent.open_connection()

    # Get summary information from database for statistical information
    db_num_media = db_agent.count_entries_in_table_media()
    db_totals = db_agent.calculate_summary_values()

    # Print database and metadata information
    UI.metadata_information(db_num_media, db_totals)

    # Create list of all media files on disk and sort it
    media_file_list = FileHandler.create_file_list_from(input_folder, limit=limit)

    # Prepare ML models
    Model.init()

    num_counter = 0
    duration_counter = 0.0
    iteration_counter = 0

    # Prepare Logger
    logger = ExtractionLogger(output_folder)
    tagger.attach_logger(logger)

    for (abs_media_path, rel_media_path, rel_output_prefix) in media_file_list:
        # Skip iteration if skip value was provided
        iteration_counter += 1
        if iteration_counter <= skip:
            continue
        # Prepare log
        logger.reset_values()
        logger.set_value("index", iteration_counter)
        logger.set_value("media_filepath", rel_media_path)
        # Gather db info for media file and process it
        song_media_data = db_agent.fetch_entry_for_media_path(rel_media_path)
        if song_media_data:
            logger.set_media_id_from_media_data(song_media_data)
            # Process one song
            song_timer = Timer()
            tagger.init(
                media_file_path=abs_media_path,
                media_data=song_media_data,
                output_folder=output_folder,
                db_agent=db_agent
            )
            num_counter += 1
            tagger.process_song(counter=iteration_counter)
            duration_counter += tagger.get_media_duration_secs()
            UI.song_process_time(song_timer.get_seconds())
            UI.spacer()
        else:
            error_message = UI.db_metadata_not_found_error(rel_media_path)
            logger.add_error(error_message)
        # Write to logfile
        logger.commit_entry()

    # Close database connections
    db_agent.close_connection()

    # Print info for overall execution time
    overall_time = program_timer.get_seconds()
    UI.overall_information(db_totals, db_num_media, overall_time, num_counter, duration_counter)

    UI.end_line()


if __name__ == '__main__':
    main(sys.argv[1:])
