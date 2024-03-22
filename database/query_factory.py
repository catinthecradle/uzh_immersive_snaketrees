#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

from psycopg import sql
from psycopg.types.json import Jsonb
from helpers.file_handler import FileHandler

# Read config file
settings = FileHandler.read_config_file()
DATABASE = settings['database']['name']

# Database tables and columns
TABLE_MEDIA = settings['database']['tables']['media']['name']
TABLE_MEDIA_KEYS = settings['database']['tables']['media']['keys']
TABLE_FEATURES = settings['database']['tables']['features']['name']
TABLE_FEATURES_KEYS = settings['database']['tables']['features']['keys']

# Query structures
BASE_SELECT_QUERY = "SELECT * FROM {table} WHERE {key} = {value}"
BASE_INSERT_QUERY = "INSERT INTO {table} ({params}) VALUES ({values})"
CHECK_IF_PRESENT_FROM_2_KEYS = "SELECT COUNT(*) > 0 AS present FROM {table} WHERE {k1}={v1} AND {k2}={v2}"
UPDATE_FROM_2_KEYS = "UPDATE {table} SET {params} WHERE {k1} = {v1} AND {k2} = {v2}"
FETCH_ALL_ORDERED_QUERY = "SELECT {multiple_features} FROM {table} ORDER BY {order_by} ASC"


class QueryFactory:

    # *************************
    # Read
    # **************************
    @staticmethod
    def fetch_entry_for_media_path(media_path):
        return sql.SQL(BASE_SELECT_QUERY).format(
            table=sql.Identifier(TABLE_MEDIA),
            key=sql.Identifier(TABLE_MEDIA_KEYS['path_to_file']),
            value=media_path,
        )

    @staticmethod
    def fetch_feature_entries_for_media(media_id):
        return sql.SQL(BASE_SELECT_QUERY).format(
            table=sql.Identifier(TABLE_FEATURES),
            key=sql.Identifier(TABLE_FEATURES_KEYS['media_id']),
            value=media_id,
        )

    @staticmethod
    def feature_for_model_and_media_exists(model_name, media_id):
        return sql.SQL(CHECK_IF_PRESENT_FROM_2_KEYS).format(
            table=sql.Identifier(TABLE_FEATURES),
            k1=sql.Identifier(TABLE_FEATURES_KEYS['model_name']),
            v1=model_name,
            k2=sql.Identifier(TABLE_FEATURES_KEYS['media_id']),
            v2=media_id
        )
    
    @staticmethod
    def fetch_all_feature_entries():
        feature_keys = sql.SQL(', ').join([
            sql.Identifier(TABLE_FEATURES_KEYS['media_id']),
            sql.Identifier(TABLE_FEATURES_KEYS['model_name']),
            sql.Identifier(TABLE_FEATURES_KEYS['data'])
        ])
        return sql.SQL(FETCH_ALL_ORDERED_QUERY).format(
            table=sql.Identifier(TABLE_FEATURES),
            multiple_features=feature_keys,
            order_by=sql.Identifier(TABLE_FEATURES_KEYS['media_id'])
        )
    
    @staticmethod
    def fetch_all_metadata():
        return ("SELECT media_id, media_path, json_build_object("
                "'title', metadata->'title',"
                "'concert_name', metadata->'concert_name',"
                "'date', (metadata->>'date')::date,"
                "'location', metadata->'location',"
                "'duration', (media_info->>'duration')::float,"
                "'musicians', metadata->'musicians'"
                f") AS metadata FROM {TABLE_MEDIA} ORDER BY media_id")

    # *************************
    # Calculate
    # **************************
    @staticmethod
    def count_entries_in_table_media():
        return f"SELECT COUNT(*) FROM {TABLE_MEDIA}"

    @staticmethod
    def calculate_summary_values():
        return "WITH fileinfo AS (SELECT (media_info->'filesize')::float/1000000000 AS size_gb, " + \
            "(media_info->'duration')::float AS duration_sec FROM public.media) " + \
            "SELECT SUM(size_gb) AS size_gb, SUM(duration_sec) AS duration_sec FROM fileinfo"

    # *************************
    # Write
    # **************************
    @staticmethod
    def add_feature_entry(params):
        query_params, query_values = QueryFactory.__extract_key_values(params)
        query = sql.SQL(BASE_INSERT_QUERY).format(
            table=sql.Identifier(TABLE_FEATURES),
            params=sql.SQL(', ').join(map(sql.Identifier, query_params)),
            values=sql.SQL(', ').join(sql.Placeholder() * len(query_values)),
        )
        return query, query_values
    
    @staticmethod
    def update_feature_entry_for(params, model_name, media_id):
        query_params, query_values = QueryFactory.__extract_update_key_value_pairs(params)
        query = sql.SQL(UPDATE_FROM_2_KEYS).format(
            table=sql.Identifier(TABLE_FEATURES),
            k1=sql.Identifier(TABLE_FEATURES_KEYS['model_name']),
            v1=model_name,
            k2=sql.Identifier(TABLE_FEATURES_KEYS['media_id']),
            v2=media_id,
            params=sql.SQL(', ').join(query_params)
        )
        return query, query_values
    
    # *************************
    # Internal helper functions
    # **************************
    @staticmethod
    def __extract_key_values(params):
        query_params = []
        query_values = []
        for k, v in params.items():
            query_params.append(k)
            query_values.append(Jsonb(v) if type(v) is dict or type(v) is list else v)
        return query_params, query_values
    
    @staticmethod
    def __extract_update_key_value_pairs(params):
        query_params = [sql.SQL("created_at = now()")]
        query_values = []
        for k, v in params.items():
            new_param = sql.SQL("{key} = {value}").format(
                key=sql.Identifier(k),
                value=sql.Placeholder(),
            )
            query_params.append(new_param)
            query_values.append(Jsonb(v) if type(v) is dict or type(v) is list else v)
        return query_params, query_values
