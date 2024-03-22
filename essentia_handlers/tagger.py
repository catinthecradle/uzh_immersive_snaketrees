#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

import os
from essentia_handlers.media import Media
from essentia_handlers.extractor import Extractor
from database.db_agent import DBAgent
from models.models import Model
from abc import ABC, abstractmethod
from helpers.timer import Timer
from helpers.io_handler import IOHandler, Color
from helpers.logger import Logger
from helpers.errors import NoAudioException, UnknownTaggerException


class Tagger(ABC):
    def __init__(self):
        self.media_file_path = None
        self.media = None
        self.ml_models = []
        self.ml_models_dict = {}
        self.db_agent = None
        self.extractor = None
        self.output_folder = None
        self.logger = None
    
    @staticmethod
    def get_instance(tagger_type: str) -> 'Tagger':
        """
        Factory method for creating an instance of the specified tagger type
        :param tagger_type: Name of the tagger type
        :return: the instance of the specified tagger type
        """
        import essentia_handlers.tagger_versions as tagger_versions
        if tagger_type == "performance":
            return tagger_versions.PerformanceTagger()
        if tagger_type == "pooling_demo":
            return tagger_versions.PoolingDemo()
        if tagger_type == "new_process":
            return tagger_versions.NewProcess()
        raise UnknownTaggerException(tagger_type)
    
    @abstractmethod
    def process_song(self, **kwargs):
        pass
    
    def init(self, media_file_path: str, media_data: dict, output_folder: str, db_agent: DBAgent):
        """
        Define behaviour of and attach data to the tagger
        :param media_file_path: Path to media file that will be examined
        :param media_data: Metadata for embedded media, received from database query
        :param output_folder: Path to folder where output data shall be stored
        :param db_agent: Database agent that handles queries
        """
        self.media_file_path = media_file_path
        self.media = Media(media_data, media_file_path)
        self.ml_models = []
        self.ml_models_dict = {}
        self.db_agent = db_agent
        self.extractor = Extractor(self.media)
        self.output_folder = os.path.join(output_folder, os.path.dirname(media_data['media_path']),
                                          self.media.media_id, "./")

    def attach_logger(self, logger: Logger):
        """
        Attach a logger to this tagger in order to write log entries
        :param logger: Logger to add
        """
        self.logger = logger

    def attach_model(self, model_name: str) -> Model:
        """
        Attach selected ML model to the tagger
        :param model_name: file name of model to add
        :return: attached model
        """
        if model_name not in self.ml_models_dict:
            self.ml_models_dict[model_name] = Model.get_model(model_name)
        return self.ml_models_dict[model_name]

    def get_media_duration_secs(self):
        """
        Return duration of the embedded audio
        :return: Duration in seconds
        :rtype: int
        """
        return self.media.get_duration_secs()

    def inform_user(self, **kwargs):
        """
        Print processing info for current media
        :param kwargs: Additional information to print
        """
        counter_message = ""
        if "counter" in kwargs:
            total_message = f" of {kwargs.get('total')}" if "total" in kwargs else ""
            counter_message = f" [{kwargs.get('counter')}{total_message}]"
        IOHandler.print_color(message=f"Processing {self.media.title}{counter_message}", enforce=True)

    def plot_waveform(self):
        """
        Plot waveform for audio of media file and store it as an image
        """
        success, message = self.media.export_waveform(self.output_folder)
        if not success:
            self.__add_error_to_logger(message)

    def export_metadata_txt(self):
        """
        Store metadata of media file in a txt file
        """
        self.media.export_metadata_txt(self.output_folder)

    def plot_features_for(self, model_name: str, max_pooling=False, sorted_means=False, skip_if_in_db=False):
        """
        Plot extracted features for a certain model and save plot as image file
        :param model_name: Short name of the model to use
        :param skip_if_in_db: If set to True, skip execution if feature entry for model is already in database
        :param max_pooling: Whether to apply max-pooling on ML activations
        :param sorted_means: Whether to sort features by mean values over whole song (descending)
        """
        model = self.attach_model(model_name)
        if model:
            if (skip_if_in_db and
                    self.db_agent.check_if_model_feature_exists_for(model.display_name, self.media.media_id)):
                IOHandler.print_color(message=f"Skipped plotting for '{model.display_name}' on "
                                              f"'{self.media.media_id}' because it is already in database",
                                      color=Color.YELLOW)
                self.__add_message_to_logger(f"Skipped plotting for {model.display_name}, already in database")
            else:
                success, message = self.extractor.plot_features_for(
                    model=model,
                    output_folder=self.output_folder,
                    max_pooling=max_pooling,
                    sorted_means=sorted_means
                )
                if not success:
                    self.__add_error_to_logger(message)
        else:
            IOHandler.print_color(message=f"Could not plot features because the model '{model_name}' does not exist!",
                                  color=Color.RED)
            self.__add_error_to_logger(f"Model '{model_name}' does not exist")

    def extract_features_to_csv_for(self, model_name: str, max_pooling=False, sorted_means=False, skip_if_in_db=False):
        """
        Store extracted features for a certain model as csv file
        :param model_name: Short name of the model to use
        :param skip_if_in_db: If set to True, skip execution if feature entry for model is already in database
        :param max_pooling: Whether to apply max-pooling on ML activations
        :param sorted_means: Whether to sort features by mean values over whole song (descending)
        """
        model = self.attach_model(model_name)
        if model:
            if (skip_if_in_db and
                    self.db_agent.check_if_model_feature_exists_for(model.display_name, self.media.media_id)):
                IOHandler.print_color(message=f"Skipped csv extraction for '{model.display_name}' on "
                                              f"'{self.media.media_id}' because it is already in database",
                                      color=Color.YELLOW)
                self.__add_message_to_logger(f"Skipped csv extraction for {model.display_name}, already in database")
            else:
                success, message = self.extractor.export_csv_for(
                    model=model,
                    output_folder=self.output_folder,
                    max_pooling=max_pooling,
                    sorted_means=sorted_means
                )
                if not success:
                    self.__add_error_to_logger(message)
        else:
            IOHandler.print_color(message=f"Could not export features because the model '{model_name}' does not exist!",
                                  color=Color.RED)
            self.__add_error_to_logger(f"Model '{model_name}' does not exist")

    def write_features_to_database_for(self, model_name: str, max_pooling=False, sorted_means=False,
                                       skip_if_in_db=False, overwrite=True):
        """
        Write extracted features for a certain model to the database
        :param model_name: Short name of the model to use
        :param skip_if_in_db: If set to True, skip execution if feature entry for model is already in database
        :param overwrite: If set to True, overwrite existing entries in database
        :param max_pooling: Whether to apply max-pooling on ML activations
        :param sorted_means: Whether to sort features by mean values over whole song (descending)
        """
        model = self.attach_model(model_name)
        if model:
            if (skip_if_in_db and
                    self.db_agent.check_if_model_feature_exists_for(model.display_name, self.media.media_id)):
                IOHandler.print_color(message=f"Skipped database export for '{model.display_name}' on "
                                              f"'{self.media.media_id}' because it is already in database",
                                      color=Color.YELLOW)
                self.__add_message_to_logger(f"Skipped database export for {model.display_name}, already in database")
            else:
                IOHandler.print_color("Writing features to database... ")
                db_timer = Timer()
                query_success = False

                try:
                    if self.db_agent.check_if_model_feature_exists_for(model.display_name, self.media.media_id):
                        # Feature is already in database => Update or skip
                        if overwrite:
                            feature = self.extractor.get_db_features_for(model, max_pooling, sorted_means)
                            query_success = self.db_agent.update_feature_entry_for(feature, model.display_name,
                                                                                   self.media.media_id)
                        else:
                            IOHandler.print_color(
                                message=f"Skipped database writing for '{model.display_name}' on {self.media.media_id} "
                                        f"because it was already present",
                                color=Color.YELLOW)
                            self.__add_message_to_logger(
                                f"Skipped database writing for {model.display_name}, already in database")
                    else:
                        feature = self.extractor.get_db_features_for(model, max_pooling, sorted_means)
                        query_success = self.db_agent.add_feature_entry(feature)
                except OSError:
                    IOHandler.print_color(
                        message="ERROR: Could not extract features due to an OSError!",
                        color=Color.RED,
                        enforce=True,
                    )
                    self.__add_error_to_logger("Could not extract features due to an OSError")
                except NoAudioException:
                    IOHandler.print_color(
                        message="ERROR: Could not extract features because file contains no audio!",
                        color=Color.RED,
                        enforce=True,
                    )
                    self.__add_error_to_logger("Could not extract features because file contains no audio")

                if query_success:
                    IOHandler.print_color("Features successfully written to database.")
                db_timer.print_seconds()
        else:
            IOHandler.print_color(message=f"Could not write features to database "
                                          f"because the model '{model_name}' does not exist!",
                                  color=Color.RED)
            self.__add_error_to_logger(f"Could not write features to database, model '{model_name}' does not exist")

    def __add_error_to_logger(self, message):
        if self.logger is not None:
            self.logger.add_error(message)

    def __add_message_to_logger(self, message):
        if self.logger is not None:
            self.logger.add_detail(message)
