#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

import csv
import os
import matplotlib.pyplot as plt
from helpers.timer import Timer
from helpers.file_handler import FileHandler
from helpers.io_handler import IOHandler, Color
from helpers.errors import NoAudioException
from models.models import Model
import numpy as np

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Define window size for max-pooling
WINDOW_SIZE = 6


class Extractor:
    def __init__(self, media):
        self.media = media
        self.features = {}
        self.embeddings = {}
        self.timer = Timer()

    def plot_features_for(self, model: Model, output_folder="", max_pooling=False, sorted_means=False) -> (bool, str):
        self.timer.reset()
        message_part, out_file_path = Extractor.__generate_message_and_filename(
            output_folder=output_folder, media_id=self.media.media_id, model_shortname=model.shortname,
            max_pooling=max_pooling, sorted_means=sorted_means, suffix="png")
        message = f"Plotting features for {message_part}... "
        IOHandler.print_color(message=message, end="")

        try:
            model_params = self.__get_model_params(model)
            if max_pooling:
                activations = self.__get_activations_max_pooling(model)
            else:
                activations = self.__get_activations(model)

            # Sort features on request
            if sorted_means:
                if max_pooling:
                    means = self.__get_activations_max_pooling_means(model)
                else:
                    means = self.__get_activation_means(model)
                activations, model_params = Extractor.__sort_by_means(means, activations, model_params)

            # Plot features
            fig, ax = plt.subplots(1, 1, figsize=(10, 10))
            ax.matshow(activations.T, aspect='auto')
            ax.set_yticks(range(len(model_params)))
            ax.set_yticklabels(model_params)
            ax.set_xlabel('patch number')
            ax.xaxis.set_ticks_position('bottom')
            ax.set_title('Tag activation for ' + self.media.title)
            FileHandler.create_folders_if_not_exists(out_file_path)
            fig.savefig(out_file_path)
            plt.close(fig)
            self.timer.print_seconds()
            # Success
            return True, ""
        except OSError:
            IOHandler.print_color(
                message="ERROR: Could not plot features due to a file error!",
                color=Color.RED,
                enforce=True,
            )
            return False, "Could not plot features due to a file error"
        except NoAudioException:
            IOHandler.print_color(
                message="ERROR: Could not export waveform because file contains no audio!",
                color=Color.RED,
                enforce=True,
            )
            return False, "File contains no audio"

    def export_csv_for(self, model: Model, output_folder="", max_pooling=False, sorted_means=False) -> (bool, str):
        self.timer.reset()
        message_part, out_file_path = Extractor.__generate_message_and_filename(
            output_folder=output_folder, media_id=self.media.media_id, model_shortname=model.shortname,
            max_pooling=max_pooling, sorted_means=sorted_means, suffix="csv")
        message = f"Writing csv file for {message_part}... "
        IOHandler.print_color(message=message, end="")

        try:
            means_list = self.__zip_features(model=model, max_pooling=max_pooling, sorted_means=sorted_means)
            FileHandler.create_folders_if_not_exists(out_file_path)
            with open(out_file_path, 'w') as output:
                csv_output = csv.writer(output)
                csv_output.writerow(['classifier', 'probability'])
                csv_output.writerows(means_list)
            self.timer.print_seconds()
            # Success
            return True, ""
        except OSError:
            IOHandler.print_color(
                message="ERROR: Could not export features to csv due to a file error!",
                color=Color.RED,
                enforce=True,
            )
            return False, "Could not export features to csv due to a file error"
        except NoAudioException:
            IOHandler.print_color(
                message="ERROR: Could not export features to csv because file contains no audio!",
                color=Color.RED,
                enforce=True,
            )
            return False, "File contains no audio"

    def get_db_features_for(self, model: Model, max_pooling=False, sorted_means=False):
        self.__add_model_metadata(model)
        means_list = self.__zip_features(model=model, max_pooling=max_pooling, sorted_means=sorted_means)
        return {
            'feature_type': model.metadata['type'],
            'version': model.metadata['framework_version'],
            'model_name': model.metadata['name'],
            'model_params': model.metadata['classes'],
            'media_id': self.media.media_id,
            'data': dict(means_list),
        }

    def __feature_exists(self, model: Model, key: str = None):
        return model.shortname in self.features and (key is None or key in self.features[model.shortname])

    def __add_model_metadata(self, model: Model):
        if not self.__feature_exists(model):
            self.features[model.shortname] = {
                'feature_type': model.metadata['type'],
                'version': model.metadata['framework_version'],
                'model_name': model.metadata['name'],
                'model_params': model.metadata['classes'],
                'media_id': self.media.media_id,
            }

    def __get_model_params(self, model: Model):
        if not self.__feature_exists(model,  'model_params'):
            self.__add_model_metadata(model)
        return self.features[model.shortname]['model_params']

    def __get_activations(self, model: Model):
        if not self.__feature_exists(model,  'activations'):
            self.__add_model_metadata(model)
            self.features[model.shortname]['activations'] = self.__extract_activations(model)
        return self.features[model.shortname]['activations']

    def __get_activation_means(self, model: Model):
        if not self.__feature_exists(model, 'activation_means'):
            activations = self.__get_activations(model)
            self.features[model.shortname]['activation_means'] = activations.mean(axis=0)
        return self.features[model.shortname]['activation_means']

    def __get_activations_max_pooling(self, model: Model):
        if not self.__feature_exists(model, 'max-pooling'):
            activations = self.__get_activations(model)
            self.features[model.shortname]['max-pooling'] = Extractor.apply_max_pooling(activations)
        return self.features[model.shortname]['max-pooling']

    def __get_activations_max_pooling_means(self, model: Model):
        if not self.__feature_exists(model, 'max-pooling_means'):
            mp_activations = self.__get_activations_max_pooling(model)
            self.features[model.shortname]['max-pooling_means'] = mp_activations.mean(axis=0)
        return self.features[model.shortname]['max-pooling_means']

    def __extract_activations(self, model: Model):
        # Load audio file if necessary
        self.media.get_audio_version(model.sample_rate)

        IOHandler.print_color(f"Perform TensorFlow predictions using {model.metadata['name']}... ")
        cached_embeddings = None
        ems = model.embedding_shortname()
        if ems and ems in self.embeddings.keys():
            IOHandler.print_color(f"Saving time for {ems}", color=Color.YELLOW)
            cached_embeddings = self.embeddings[ems]
        predictions, embeddings = model.extract_features_from(self.media, cached_embeddings)
        if ems:
            self.embeddings[ems] = embeddings
        return predictions

    def __zip_features(self, model: Model, max_pooling: bool, sorted_means: bool):
        model_params = self.__get_model_params(model)
        if max_pooling:
            means = self.__get_activations_max_pooling_means(model)
        else:
            means = self.__get_activation_means(model)
        means_list = list(zip(model_params, means))
        if sorted_means:
            means_list = sorted(means_list, key=lambda x: x[1], reverse=True)
        means_list = [(k, float(v)) for (k, v) in means_list]
        return means_list

    @staticmethod
    def __sort_by_means(means, activations=None, params=None):
        sorting = means.argsort()[::-1]
        sorted_activations = activations[:, sorting] if activations is not None else None
        sorted_params = [params[i] for i in sorting] if params is not None else None
        return sorted_activations, sorted_params

    @staticmethod
    def __generate_message_and_filename(output_folder, media_id, model_shortname, max_pooling, sorted_means, suffix):
        mp_message = ", using max-pooling" if max_pooling else ""
        sm_message = ", order by means" if sorted_means else ""
        mp_suffix = "-mp" if max_pooling else ""
        sm_suffix = "-sm" if sorted_means else ""
        message = f"{model_shortname}{mp_message}{sm_message}"
        out_file_path = f"{output_folder}{media_id}-{model_shortname}{mp_suffix}{sm_suffix}.{suffix}"
        return message, out_file_path

    @staticmethod
    def apply_max_pooling(activations):
        # Return original input array if size is smaller than max-pooling window
        if activations.shape[0] < WINDOW_SIZE:
            return activations
        window_hop = WINDOW_SIZE // 2
        padded_activations = activations
        overhead = padded_activations.shape[0] % window_hop
        if overhead > 0:
            pad_size = window_hop - overhead
            pl = pad_size // 2
            pr = pad_size - pl
            # noinspection PyTypeChecker
            padded_activations = np.pad(array=padded_activations, pad_width=((pl, pr), (0, 0)), mode='constant')

        # Create sliding window
        slide_dim = padded_activations.shape[1]
        mp_windows = np.lib.stride_tricks.sliding_window_view(
            padded_activations,
            window_shape=(WINDOW_SIZE, slide_dim))
        # Remove redundant dimension
        mp_windows = mp_windows[:, 0, :, :]
        # Skip windows by hop-size
        mp_windows = mp_windows[::window_hop, :]

        # Apply max-pooling => Calculate local maxima for all windows
        max_pooling = np.amax(mp_windows, axis=1)
        return max_pooling
