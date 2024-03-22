#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

import json
import os.path
import essentia.standard as es
from helpers.timer import Timer
from helpers.io_handler import IOHandler

model_data_folder = os.path.dirname(__file__) + "/model_data/"

AVAILABLE_MODELS = [
    "discogs-effnet-bs64-1",
    "mtg_jamendo_genre-discogs-effnet-1",
    "mtg_jamendo_instrument-discogs-effnet-1",
    "mtg_jamendo_moodtheme-discogs-effnet-1",
]


class Model:
    
    model_collection = {}
    
    def __init__(self, model_name):
        json_filename = model_data_folder + model_name + ".json"
        pb_filename = model_data_folder + model_name + ".pb"

        if not os.path.exists(json_filename):
            raise KeyError(f"No JSON file '{json_filename}' found!")
        if not os.path.exists(pb_filename):
            raise KeyError(f"No PB file '{pb_filename}' found!")

        # Load metadata from json
        with open(json_filename, 'r') as json_file:
            self.metadata = json.load(json_file)

        # Assign model parameters
        self.shortname = model_name
        self.display_name = self.metadata['name']
        self.algorithm = self.metadata['inference']['algorithm']
        self.sample_rate = self.metadata['inference']['sample_rate']
        self.TensorFlowAlgorithm = getattr(es, self.algorithm)
        self.pb_filename = pb_filename
        self.input = self.metadata['schema']['inputs'][0]['name']
        self.output_prediction, self.output_embedding = self.__get_output_names()
        self.embedding_model = None

    def __get_output_names(self):
        output = {
            'predictions': None,
            'embeddings': None,
        }
        for o in self.metadata['schema']['outputs']:
            if o['output_purpose'] in output.keys():
                output[o['output_purpose']] = o['name']
        return output['predictions'], output['embeddings']
    
    def __attach_embedding_model(self):
        if 'embedding_model' in self.metadata['inference']:
            # Create new model if not already existing and attach it
            embedding_model_name = self.metadata['inference']['embedding_model']['model_name']
            if embedding_model_name not in Model.model_collection.keys():
                Model.model_collection[embedding_model_name] = Model(embedding_model_name)
            self.embedding_model = Model.model_collection[embedding_model_name]

    def needs_embedding(self):
        return self.embedding_model is not None

    def embedding_shortname(self):
        return self.embedding_model.shortname if self.needs_embedding() else None
        
    def extract_features_from(self, media, embeddings=None):
        prediction_model = self.TensorFlowAlgorithm(
            graphFilename=self.pb_filename,
            input=self.input,
            output=self.output_prediction
        )
        if self.embedding_model is not None:
            if embeddings is None:
                embeddings = self.embedding_model.extract_embeddings_from(media)
            predictions = prediction_model(embeddings)
        else:
            audio = media.get_audio_version(self.sample_rate)
            predictions = prediction_model(audio)
        return predictions, embeddings
    
    def extract_embeddings_from(self, media):
        audio = media.get_audio_version(self.sample_rate)
        embedding_model = self.TensorFlowAlgorithm(
            graphFilename=self.pb_filename,
            input=self.input,
            output=self.output_embedding
        )
        return embedding_model(audio)

    @staticmethod
    def init():
        IOHandler.print_color(
            message="Loading model files... ",
            end=""
        )
        model_timer = Timer()
        Model.model_collection.clear()
        # Init all models
        for mp in AVAILABLE_MODELS:
            Model.model_collection[mp] = Model(mp)
        # Attach embedding models
        for model in Model.model_collection.values():
            model.__attach_embedding_model()
        model_timer.print_seconds()
        IOHandler.print_spacer()

    @staticmethod
    def get_model(model_name):
        if model_name in Model.model_collection.keys():
            return Model.model_collection[model_name]
        return None
