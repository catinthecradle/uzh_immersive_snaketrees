#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

# Import necessary libraries
import pandas as pd
from pandas import json_normalize
import json
import os
from database.db_agent import DBAgent


class Cleaner:
    
    @staticmethod
    def split_by_model(df, data_is_json=False):
        # Sort dataframe
        df['sort_index'] = df['media_id'].apply(lambda x: x.split("mjf-")[1]).astype('int')
        df.sort_values('sort_index', inplace=True)
        df.drop('sort_index', axis=1, inplace=True)

        # Split rows per feature into different dataframes
        model_dfs = df.groupby(df['model_name'])
        print(f"There are {len(model_dfs)} models in the dataset.")
        
        # Create a new dataframe for each model with all attribute values distributed to columns
        print("Clean the dataset:")
        model_collection = {}
        for group_name, df_group in model_dfs:
            print(f"Cleaning {group_name}...")
            # Remove redundant model_name column and reset index
            feature_df = df_group.drop('model_name', axis=1).reset_index(drop=True)
            
            # Convert json values to columns of a new, temporary dataframe
            if not data_is_json:
                feature_df['data'] = feature_df['data'].apply(json.loads)
            expanded_data = json_normalize(feature_df['data'])

            # Concat the temporary dataframe to the original one and remove the former data column
            feature_df_expanded = pd.concat([feature_df, expanded_data], axis=1).drop('data', axis=1)
            # Add this dataframe to the model_collection
            model_collection[group_name] = feature_df_expanded
        
        return model_collection
    
    @staticmethod
    def convert_from_csv(csv_file, limit=None):
        # Prepare file names and info
        filename = os.path.basename(csv_file)
        # Import data
        print("Reading data from {}...".format(filename))
        df = pd.read_csv(csv_file)
        # Reduce size if limit was provided
        if limit is not None:
            df = df.head(limit)
        return Cleaner.split_by_model(df, data_is_json=False)
    
    @staticmethod
    def convert_from_database(db_name, limit=None):
        # Connect to database
        database = DBAgent(db_name)
        database.open_connection()
        # Read all data
        print("Fetching all features from database. This could take a while...")
        df = database.fetch_all_feature_entries_to_dataframe(limit=limit)
        print("DONE")
        # Close connection
        database.close_connection()
        return Cleaner.split_by_model(df, data_is_json=True)
