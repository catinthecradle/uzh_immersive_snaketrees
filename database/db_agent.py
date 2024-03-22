#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

import pandas as pd
from database.postgres_db import Database
from database.query_factory import QueryFactory
from helpers.timer import Timer
from helpers.io_handler import IOHandler, Color


class DBAgent:

    def __init__(self, db_name):
        self.database = Database(db_name)

    # *************************
    # General
    # **************************
    def open_connection(self):
        IOHandler.print_color("Connecting to database... ")
        db_timer = Timer()
        self.database.open()
        db_timer.print_seconds()

    def close_connection(self):
        self.database.close()

    # *************************
    # Read
    # **************************
    def fetch_entry_for_media_path(self, rel_media_path):
        query = QueryFactory.fetch_entry_for_media_path(rel_media_path)
        return self.database.fetch_one(query)
    
    def fetch_feature_entries_for_media(self, media_id):
        query = QueryFactory.fetch_feature_entries_for_media(media_id)
        return self.database.fetch_all(query)

    def check_if_model_feature_exists_for(self, model_name, media_id):
        query = QueryFactory.feature_for_model_and_media_exists(model_name, media_id)
        return self.database.fetch_one(query)['present']
    
    def fetch_many_feature_entries(self, size=100):
        query = QueryFactory.fetch_all_feature_entries()
        self.database.execute(query)
        return self.database.fetch_many(size)
    
    def fetch_all_feature_entries_to_dataframe(self, batch_size=10000, limit=None):
        query = QueryFactory.fetch_all_feature_entries()
        return self.__fetch_all_to_dataframe(query, batch_size, limit)
    
    def fetch_all_metadata_to_dataframe(self, batch_size=10000, limit=None):
        query = QueryFactory.fetch_all_metadata()
        return self.__fetch_all_to_dataframe(query, batch_size, limit)
    
    # Read Helpers
    def __fetch_all_to_dataframe(self, query, batch_size, limit):
        df = pd.DataFrame()
        self.database.execute(query)
        counter = 0
        while True and (limit is None or counter < limit):
            if limit:
                n_fetch = min(batch_size, limit - counter)
            else:
                n_fetch = batch_size
            rows = self.database.fetch_many(n_fetch)
            if not rows:
                break
            df_temp = pd.DataFrame.from_records(rows)
            df = pd.concat([df, df_temp])
            counter += batch_size
        return df
    
    # *************************
    # Calculate
    # **************************
    def count_entries_in_table_media(self):
        query = QueryFactory.count_entries_in_table_media()
        return self.database.fetch_one(query)['count']

    def calculate_summary_values(self):
        query = QueryFactory.calculate_summary_values()
        return self.database.fetch_one(query)

    # *************************
    # Write
    # **************************

    def add_feature_entry(self, feature):
        (query, values) = QueryFactory.add_feature_entry(feature)
        (success, message) = self.database.execute(query, values)
        if not success:
            IOHandler.print_color(message=f"ERROR: {message}", color=Color.RED)
        return success

    def update_feature_entry_for(self, feature, model_name, media_id):
        (query, values) = QueryFactory.update_feature_entry_for(feature, model_name, media_id)
        (success, message) = self.database.execute(query, values)
        if not success:
            IOHandler.print_color(message=f"ERROR: {message}", color=Color.RED)
        return success
