#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

import os
import errno
import essentia.standard as es
import matplotlib.pyplot as plt
import numpy as np
from helpers.timer import Timer
from helpers.file_handler import FileHandler
from helpers.converter import Converter
from helpers.io_handler import IOHandler, Color
from helpers.errors import NoAudioException


class Media:
    def __init__(self, media_data, media_file_path):
        self.media_data = media_data
        self.media_file_path = media_file_path
        self.metadata = media_data['metadata']
        self.media_info = media_data['media_info']
        self.media_id = media_data['media_id']
        self.sample_rate = self.media_info['audio']['sample_rate']
        self.title = f"'{self.metadata['title']}' by {self.metadata['concert_name']} [{self.media_id}]"
        self.audio = {}
        self.timer = Timer()

    def get_audio_version(self, sample_rate=None):
        if sample_rate is None:
            sample_rate = self.sample_rate
        if sample_rate not in self.audio:
            self.__load_audio(sample_rate)
        return self.audio[sample_rate]

    def export_waveform(self, output_folder="", sample_rate=None) -> (bool, str):
        if sample_rate is None:
            sample_rate = self.sample_rate
        # Load audio file if it has not already been loaded
        try:
            audio_to_plot = self.get_audio_version(sample_rate=sample_rate)
            if audio_to_plot is not None:
                IOHandler.print_color(message="Plotting audio... ", end="")
                self.timer.reset()
                fig, ax = plt.subplots(1, 1, figsize=(15, 6))
                song_time = np.linspace(0, len(audio_to_plot) / float(sample_rate), len(audio_to_plot))
                ax.set_title('Waveform for ' + self.title)
                ax.set_xlabel('time [seconds]')
                ax.xaxis.set_ticks_position('bottom')
                ax.plot(song_time, audio_to_plot)
                out_file_path = f"{output_folder}{self.media_id}-waveform.png"
                FileHandler.create_folders_if_not_exists(out_file_path)
                fig.savefig(out_file_path)
                plt.close(fig)
                self.timer.print_seconds()
                return True, ""
            else:
                IOHandler.print_color(
                    message="ERROR: Could not export waveform because audio was not available!",
                    color=Color.RED
                )
                return False, "Audio not available"
        except OSError:
            return False, "Could not load audio"
        except NoAudioException:
            IOHandler.print_color(
                message="ERROR: Could not export waveform because file contains no audio!",
                color=Color.RED,
                enforce=True,
            )
            return False, "File contains no audio"

    def export_metadata_txt(self, output_folder=""):
        IOHandler.print_color(message="Writing metadata to txt file... ", end="")
        self.timer.reset()
        out_file_path = f"{output_folder}{self.media_id}-metadata.txt"
        song_info = Converter.song_info_textblock(self.media_data)
        FileHandler.write_to_txt(out_file_path, song_info)
        self.timer.print_seconds()

    def get_duration_secs(self):
        return self.media_info['duration']

    def __load_audio(self, sample_rate):
        # Load an audio file using the MonoLoader with down-sampling
        IOHandler.print_color(message=f"Loading audio with sample rate {sample_rate} Hz... ", end="")
        if not os.path.exists(self.media_file_path):
            IOHandler.print_color(
                message="ERROR: Could not load audio, file not found!",
                color=Color.RED,
                enforce=True,
            )
            raise OSError(errno.ENOENT, "File not found", self.media_file_path)
        self.timer.reset()
        try:
            audio_signal = es.MonoLoader(sampleRate=sample_rate, filename=self.media_file_path)()
            # Verify that audio signal is not null
            if audio_signal.any():
                self.audio[sample_rate] = audio_signal
            else:
                raise NoAudioException(self.media_file_path)
        except RuntimeError as error:
            IOHandler.print_color(
                message=f"An error occurred while trying to use essentia MonoLoader: {error}",
                color=Color.RED,
                enforce=True,
            )
            raise OSError(errno.ENOENT, "Could not load audio file", self.media_file_path)
        finally:
            self.timer.print_seconds()
