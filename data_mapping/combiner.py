#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

# Import necessary libraries
import yaml
from sklearn import preprocessing
from helpers.timer import Timer
from helpers.converter import Converter
from database.db_agent import DBAgent

# Default values
DEFAULT_BESTOF = 7
DEFAULT_TANGENT = {
    'X': 0.0,
    'Y': 0.0,
    'Z': 100.0
}


class Combiner:
    @staticmethod
    def __normalise_data(cluster_data):
        df = cluster_data.copy()
        min_max_scaler = preprocessing.MinMaxScaler()
        df[['X', 'Y', 'Z']] = min_max_scaler.fit_transform(df[['X', 'Y', 'Z']])
        return df
    
    @staticmethod
    def __determine_params(geometry, num_branches, branch_index):
        if 'DB_Length' in geometry:
            # Knot has straight branch
            rot_z_delta = 360.0 / (num_branches - 1) if num_branches > 1 else 0.0
        else:
            rot_z_delta = 360.0 / num_branches
        if 'DB_Length' in geometry and branch_index == num_branches - 1:
            length = geometry['DB_Length']
            start_tangent = DEFAULT_TANGENT
            end_tangent = DEFAULT_TANGENT
            rot_y = 0.0
            rot_z = 0.0
            rot_children = geometry['DB_Rotate']
        else:
            length = geometry['Length']
            start_tangent = geometry['StartTangent']
            end_tangent = geometry['EndTangent']
            rot_y = geometry['Y-Angle']
            rot_z = branch_index * rot_z_delta
            rot_children = geometry['RotateSideBranches'][branch_index % len(geometry['RotateSideBranches'])]
        start_width = geometry['StartWidth']
        end_width = geometry['EndWidth']
        return {
            'length': length,
            'start_tangent': start_tangent,
            'end_tangent': end_tangent,
            'start_width': start_width,
            'end_width': end_width,
            'rot_y': rot_y,
            'rot_z': rot_z,
            'rot_children': rot_children
        }

    @staticmethod
    def __create_ue_cluster_data(cluster, group_indices, depth, max_depth, tree_structure,
                                 leaf_clusters=None, leaf_cluster_counter=0, best_of=DEFAULT_BESTOF):
        if leaf_clusters is None:
            leaf_clusters = {}
        cluster_groups = cluster.groupby(group_indices[depth])
        cluster_list = []
        branch_counter = 0
        for sub_index, sub_df in cluster_groups:
            cluster_means = sub_df.iloc[:, 8:].mean(axis=0)
            top_shots = cluster_means.sort_values(ascending=False).head(best_of)

            # Combine data to JSON
            node_json = {
                "metadata": " | ".join([f"{k}: {100 * v:.1f} %" for k, v in top_shots.items()]),
                "elements": sub_df.shape[0],
            }
            # Add geometry info for non-leave nodes
            if depth + 2 < len(tree_structure):
                node_json["params"] = Combiner.__determine_params(
                    geometry=tree_structure[depth + 2],
                    num_branches=len(cluster_groups),
                    branch_index=branch_counter
                )
                branch_counter += 1

            # Recursion or leaf cluster?
            if depth < max_depth:
                node_json["children"], leaf_clusters, leaf_cluster_counter = Combiner.__create_ue_cluster_data(
                    cluster=sub_df,
                    group_indices=group_indices,
                    depth=depth + 1,
                    max_depth=max_depth,
                    tree_structure=tree_structure,
                    leaf_clusters=leaf_clusters,
                    leaf_cluster_counter=leaf_cluster_counter,
                    best_of=best_of
                )
            else:
                node_json["leaf_uid"] = leaf_cluster_counter
                leaf_clusters[leaf_cluster_counter] = Combiner.__create_leaf_cluster_data(
                    cluster_df=sub_df,
                    best_of=best_of
                )
                leaf_cluster_counter += 1
            cluster_list.append(node_json)
        return cluster_list, leaf_clusters, leaf_cluster_counter

    @staticmethod
    def __create_leaf_cluster_data(cluster_df, best_of):
        leaf_df = cluster_df.copy()
        # Extract normalised geometry
        normalised_geometry = Combiner.__normalise_data(leaf_df.iloc[:, 0:4])
        # Extract top features
        leaf_df['features'] = leaf_df.apply(
            lambda row: Combiner.__feature_top_shots(row[8:], best_of), axis=1)
        leaf_df.drop(leaf_df.iloc[:, 1:-1], axis=1, inplace=True)
        # Join dataframes
        combined_leaf_df = normalised_geometry.merge(
            right=leaf_df,
            how='right',
            on='media_id'
        )
        combined_leaf_df.set_index('media_id', inplace=True)
        combined_leaf_dict = combined_leaf_df.to_dict(orient='index')
        leaf_dict = {}
        for leaf_id, leaf_data in combined_leaf_dict.items():
            features = leaf_data['features']
            geometry = {k: leaf_data[k] for k in leaf_data if k in ['X', 'Y', 'Z']}
            leaf_dict[leaf_id] = {
                'geometry': geometry,
                'features': features
            }
        return leaf_dict

    @staticmethod
    def process_all_models(cluster_dataframes, vector_dataframes, model_full_names, tree_structure_yaml):
        print(f"Combine metadata for all {len(model_full_names)} models:")
        meta_timer = Timer()

        # Read tree structure file for tree geometry
        print("Reading tree structure file...")
        with open(tree_structure_yaml, 'r') as stream:
            tree_structure = yaml.safe_load(stream)
        # Combine feature data to JSON
        cluster_json = {
            "metadata": "",
            "params": Combiner.__determine_params(
                geometry=tree_structure[0],
                num_branches=1,
                branch_index=0
            )
        }

        # Process data
        print("Processing geometry and features data...")
        cluster_data = []
        leaf_cluster_collection = {}
        leaf_cluster_counter = 0
        model_counter = 0
        for model_name in cluster_dataframes:
            if model_name not in vector_dataframes:
                continue
            cluster_df = cluster_dataframes[model_name]
            vector_df = vector_dataframes[model_name]

            # Join dataframes
            full_df = cluster_df.merge(
                right=vector_df,
                how='right',
                on='media_id'
            )

            # Combine feature data to JSON
            feature_json = {
                "metadata": f"Feature: {model_full_names[model_name]}",
                "elements": full_df.shape[0],
                "params": Combiner.__determine_params(
                    geometry=tree_structure[1],
                    num_branches=len(cluster_dataframes),
                    branch_index=model_counter
                )
            }
            model_counter += 1

            # Run
            group_indices = full_df.columns[4:7].to_list()
            model_cluster_data, leaf_clusters, leaf_cluster_counter = Combiner.__create_ue_cluster_data(
                cluster=full_df,
                group_indices=group_indices,
                depth=0,
                max_depth=len(group_indices) - 1,
                tree_structure=tree_structure,
                leaf_cluster_counter=leaf_cluster_counter,
                best_of=DEFAULT_BESTOF
            )
            # Append to cluster data
            feature_json['children'] = model_cluster_data
            cluster_data.append(feature_json)
            leaf_cluster_collection.update(leaf_clusters)

        cluster_json["children"] = cluster_data
        print(f"Done. Time elapsed: {meta_timer.get_seconds()} seconds")
        return cluster_json, leaf_cluster_collection
    
    @staticmethod
    def read_features_from_database(db_name, limit=None):
        # Connect to database
        database = DBAgent(db_name)
        database.open_connection()
        # Read all data
        print("Fetching metadata from database. This could take a while...")
        metadata_df = database.fetch_all_metadata_to_dataframe(limit=limit)
        print("Done.")
        # Close connection
        database.close_connection()
        return metadata_df

    @staticmethod
    def __transform_metadata_date(metadata, language):
        metadata['date'] = Converter.datetime_to_localized_timestring(metadata['date'], language)
        return metadata
    
    @staticmethod
    def make_concert_dates_human_readable(metadata_df, language='en'):
        # Convert dates and re-set index
        print("Convert concert dates to human-readable format... ", end="")
        metadata_df['metadata'] = metadata_df['metadata'].apply(
            lambda row: Combiner.__transform_metadata_date(metadata=row, language=language))
        print("Done.")

    @staticmethod
    def __feature_top_shots(row, best_of):
        top_shots = row.sort_values(ascending=False).head(best_of)
        return " | ".join([f"{k}: {100 * v:.1f} %" for k, v in top_shots.items()])
