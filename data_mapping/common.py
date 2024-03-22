#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

# Import necessary libraries
import os
import json
import pandas as pd
from typing import Dict
from helpers.file_handler import FileHandler


class Mapping:

    prefix_delimiter = "-"
    csv_suffix = ".csv"

    @staticmethod
    def import_df_from_single_csv(input_file, limit=None, random=False) -> pd.DataFrame:
        """
        Read a single csv file and store contents to a pandas dataframe.
        If limit is provided, reduce dataframe size to limit either randomly or starting from top.
        :param input_file: Path to csv file
        :type input_file: str
        :param limit: If a limit is provided, reduce dataframe size.
        :type limit: int | None
        :param random: Whether to select samples randomly if a limit is set.
        :return: dataframe
        """
        print(f"Read csv file: {input_file}")
        df = pd.read_csv(input_file)
        if limit is not None:
            if random:
                df = df.sample(limit, ignore_index=True)
            else:
                df = df.head(limit)
        return df

    @staticmethod
    def import_from_multiple_csv(input_folder, prefix, limit=None) -> Dict[str, pd.DataFrame]:
        """
        Read multiple csv files and store contents as pandas dataframe in a collection.
        :param input_folder: Path to folder containing csv files
        :type input_folder: str
        :param prefix: Identifier for csv files: method reads all files whose filename starts with prefix.
        :type prefix: str
        :param limit: If a limit is provided, reduce dataframe size.
        :type limit: int | None
        :return: Dictionary of dataframes with model names as keys.
        """
        print(f"Read csv files with prefix {prefix} from {input_folder}:")
        prefix = prefix + Mapping.prefix_delimiter
        model_collection = {}
        suffix = Mapping.csv_suffix
        for filename in os.listdir(input_folder):
            if filename.startswith(prefix) and filename.endswith(suffix):
                file_path = os.path.join(input_folder, filename)
                model_name = filename[len(prefix):-len(suffix)]
                # Import data
                print(f"Reading data from {filename}...")
                df = pd.read_csv(file_path)
                # Reduce size if limit was provided
                if limit is not None:
                    df = df.head(limit)
                model_collection[model_name] = df.copy()
        return model_collection

    @staticmethod
    def import_dict_from_json(file_name) -> dict:
        """
        Read json file into a dictionary
        :param file_name: Json file path
        :type file_name: LiteralString
        :return:
        """
        with open(file_name, 'r') as file:
            imported_dict = json.load(file)
        return imported_dict

    @staticmethod
    def export_to_multiple_csv(model_collection, output_folder, prefix, data_name):
        """
        Store collection of pandas dataframes into several csv files.
        :param model_collection: Dictionary of dataframes with model names as keys.
        :type model_collection: dict[str, pd.DataFrame]
        :param output_folder: Where to store the files.
        :type output_folder: str
        :param prefix: Identifier for csv files: all files will have this as a prefix in the filename.
        :type prefix: str
        :param data_name: Identifier for user feedback only.
        :type data_name: str
        :return:
        """
        print(f"Export {data_name} to csv files for each model:")
        prefix = prefix + Mapping.prefix_delimiter
        suffix = Mapping.csv_suffix
        for model_name, df in model_collection.items():
            print(f"Exporting csv file for {model_name}...")
            export_filename = f"{output_folder}/{prefix}{model_name}{suffix}"
            FileHandler.create_folders_if_not_exists(export_filename)
            df.to_csv(export_filename, index=False)
        print("DONE")

    @staticmethod
    def export_df_to_csv(dataframe, output_file, index=False, header=True):
        """
        Store a single dataframe into a csv. Create parent folders if not existing.
        :param dataframe: Dataframe to export
        :type dataframe: pd.Dataframe
        :param output_file:
        :type output_file: LiteralString
        :param index: Whether to export index or not
        :type index: bool
        :param header: Whether to export header or not
        :type header: bool
        :return:
        """
        print(f"Exporting csv file to {output_file}...")
        FileHandler.create_folders_if_not_exists(output_file)
        dataframe.to_csv(output_file, index=index, header=header)

    @staticmethod
    def export_collection_to_json(collection, output_file):
        """
        Store a collection as JSON file
        :param collection:
        :param output_file:
        :return:
        """
        FileHandler.create_folders_if_not_exists(output_file)
        with open(output_file, 'w') as file:
            json.dump(collection, file)
    
    @staticmethod
    def export_df_to_json(df, output_file):
        """
        Store a dataframe as JSON file
        :param df:
        :param output_file:
        :return:
        """
        FileHandler.create_folders_if_not_exists(output_file)
        with open(output_file, 'w') as file:
            df.to_json(file, orient='index')
