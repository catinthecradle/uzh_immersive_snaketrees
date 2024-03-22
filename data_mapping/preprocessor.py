#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

# Import necessary libraries
import pandas as pd
import numpy as np


class Preprocessor:
    @staticmethod
    def add_containing_clusters(metadata_df, cluster_geometry_dict):
        print("Add containing clusters to metadata... ", end="")
        
        clusters_per_leaf = {}
        for cluster_id, cluster_geometry in cluster_geometry_dict.items():
            for media_id in cluster_geometry['songs']:
                if media_id in clusters_per_leaf:
                    clusters_per_leaf[media_id].append(int(cluster_id))
                else:
                    clusters_per_leaf[media_id] = [int(cluster_id)]

        # Convert into dataframe
        relation_df = pd.DataFrame.from_dict(clusters_per_leaf, orient='index')
        relation_df['clusters'] = relation_df.values.tolist()
        relation_df.drop(relation_df.iloc[:, :-1], axis=1, inplace=True)
        relation_df.index.name = "media_id"

        # Merge with metadata
        extended_metadata_df = metadata_df.merge(
            right=relation_df,
            how='right',
            on='media_id'
        )
        # Reset index
        extended_metadata_df.set_index('media_id', inplace=True)

        print("Done.")

        return clusters_per_leaf, extended_metadata_df
    
    @staticmethod
    def calculate_cluster_relations(containing_clusters):
        print("Calculate all cluster relations... ", end="")
        clusters_per_song = np.array(list(containing_clusters.values()))
        # Preparation
        n_clusters = clusters_per_song.max() - clusters_per_song.min() + 1
        n_relations = clusters_per_song.shape[1]
        
        # Count occurrences of songs in pairwise clusters
        relation_matrix = np.zeros((n_clusters, n_clusters), dtype=float)
        for song_clusters in clusters_per_song:
            for i in range(n_relations):
                for j in range(n_relations):
                    relation_matrix[song_clusters[i], song_clusters[j]] += 1
        # Now normalise it
        relation_matrix = np.array([row / max(row) for row in relation_matrix])
        relation_df = pd.DataFrame(relation_matrix)
        
        print("Done.")

        return relation_df

    @staticmethod
    def append_stats_to_leaf_clusters(leaf_cluster_geometry_dict):
        print("Appending statistics to all leaf clusters... ", end="")
        # Create dataframe with cluster id and number of songs as columns
        stats_dict = {}
        for cluster_id, songs in leaf_cluster_geometry_dict.items():
            stats_dict[cluster_id] = len(songs)
        stats_df = pd.DataFrame.from_dict(stats_dict, orient='index', columns=['n_songs'])

        # Get minimum and maximum number of songs in clusters
        songs_min = stats_df['n_songs'].min()
        songs_max = stats_df['n_songs'].max()
        # If minimum == 0, get smallest value > 0 as minimum
        if songs_min == 0:
            songs_min = sorted(list(stats_df['n_songs'].unique()))[1]

        # Get normalising parameters...
        scale = 1 / (songs_max - songs_min)
        # ... and apply them to the stats
        stats_df['lin_scale'] = (stats_df['n_songs'] - songs_min) * scale
        stats_df['cub_scale'] = stats_df['lin_scale'] ** (1.0 / 3)

        # Convert dict back to dataframe and append information to original leaf geometry dataframe
        stats_dict = stats_df.drop('n_songs', axis=1).to_dict(orient='index')
        leaf_cluster_extended_dict = {}
        for cluster_id, songs in leaf_cluster_geometry_dict.items():
            leaf_cluster_extended_dict[cluster_id] = {
                'stats': stats_dict[cluster_id],
                'songs': songs,
            }

        print("Done.")

        return leaf_cluster_extended_dict
