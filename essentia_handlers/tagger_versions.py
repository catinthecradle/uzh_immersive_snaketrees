#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

from essentia_handlers.tagger import Tagger

ALL_MODELS = [
    "discogs-effnet-bs64-1",
    "mtg_jamendo_genre-discogs-effnet-1",
    "mtg_jamendo_instrument-discogs-effnet-1",
    "mtg_jamendo_moodtheme-discogs-effnet-1",
]


class PerformanceTagger(Tagger):
    def process_song(self, **kwargs):
        self.inform_user(**kwargs)

        # Instrument Recognition
        self.write_features_to_database_for(
            model_name="mtg_jamendo_instrument-discogs-effnet-1",
            max_pooling=True, sorted_means=False, skip_if_in_db=True, overwrite=False)

        # Genre Recognition
        self.write_features_to_database_for(
            model_name="mtg_jamendo_genre-discogs-effnet-1",
            max_pooling=False, sorted_means=False, skip_if_in_db=True, overwrite=False)

        # Mood Recognition
        self.write_features_to_database_for(
            model_name="mtg_jamendo_moodtheme-discogs-effnet-1",
            max_pooling=True, sorted_means=False, skip_if_in_db=True, overwrite=False)


class PoolingDemo(Tagger):
    def process_song(self, **kwargs):
        self.inform_user(**kwargs)
        self.plot_waveform()
        self.export_metadata_txt()

        # Instrument Recognition
        model_name = "mtg_jamendo_instrument-discogs-effnet-1"
        self.plot_features_for(
            model_name=model_name, max_pooling=False, sorted_means=True, skip_if_in_db=False)
        self.plot_features_for(
            model_name=model_name, max_pooling=True, sorted_means=True, skip_if_in_db=False)

        # Genre Recognition
        model_name = "mtg_jamendo_genre-discogs-effnet-1"
        self.plot_features_for(
            model_name=model_name, max_pooling=False, sorted_means=True, skip_if_in_db=False)

        # Mood Recognition
        model_name = "mtg_jamendo_moodtheme-discogs-effnet-1"
        self.plot_features_for(
            model_name=model_name, max_pooling=False, sorted_means=True, skip_if_in_db=False)
        self.plot_features_for(
            model_name=model_name, max_pooling=True, sorted_means=True, skip_if_in_db=False)


class NewProcess(Tagger):
    def process_song(self, **kwargs):
        self.inform_user(**kwargs)
        self.plot_waveform()
        self.export_metadata_txt()

        # Instrument Recognition
        model_name = "mtg_jamendo_instrument-discogs-effnet-1"
        self.plot_features_for(
            model_name=model_name, max_pooling=True, sorted_means=True, skip_if_in_db=False)
        self.extract_features_to_csv_for(
            model_name=model_name, max_pooling=True, sorted_means=True, skip_if_in_db=False)
        self.write_features_to_database_for(
            model_name=model_name, max_pooling=True, sorted_means=False, skip_if_in_db=False, overwrite=True)

        # Genre Recognition
        model_name = "mtg_jamendo_genre-discogs-effnet-1"
        self.plot_features_for(
            model_name=model_name, max_pooling=False, sorted_means=True, skip_if_in_db=False)
        self.extract_features_to_csv_for(
            model_name=model_name, max_pooling=False, sorted_means=True, skip_if_in_db=False)
        self.write_features_to_database_for(
            model_name=model_name, max_pooling=False, sorted_means=False, skip_if_in_db=False, overwrite=True)

        # Mood Recognition
        model_name = "mtg_jamendo_moodtheme-discogs-effnet-1"
        self.plot_features_for(
            model_name=model_name, max_pooling=True, sorted_means=True, skip_if_in_db=False)
        self.extract_features_to_csv_for(
            model_name=model_name, max_pooling=True, sorted_means=True, skip_if_in_db=False)
        self.write_features_to_database_for(
            model_name=model_name, max_pooling=True, sorted_means=False, skip_if_in_db=False, overwrite=True)
