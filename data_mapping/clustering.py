#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

# Import necessary libraries
from sklearn.cluster import SpectralClustering
import pandas as pd
from helpers.timer import Timer


class Clustering:
    
    @staticmethod
    def hierarchical_spectral_clustering(model_collection, branching_factors):
        print(f"Perform hierarchical Spectral Clustering for all {len(model_collection)} models:")
        cluster_collection = {}
        cluster_columns = []
        for i in range(len(branching_factors)):
            cluster_columns.append(f"b_{i}")
        
        for model_name, feature_df in model_collection.items():
            print(f"Calculate clusters for {model_name}...")
            cluster_timer = Timer()
            # Copy model dataframe, append columns for each depth and preset all values to -1
            df_original = feature_df.copy()
            for i in range(len(branching_factors)):
                df_original[cluster_columns[i]] = -1
            # Perform Spectral Clustering recursively to obtain a cluster hierarchy
            # df_original will be updated in the process!
            Clustering.__update_cluster_labels(df_original, df_original, branching_factors[0], cluster_columns[0])
            Clustering.__create_subclusters(df_original, df_original, 0, branching_factors, cluster_columns)
            # Store dataframe in collection
            cluster_collection[model_name] = df_original
            print(f"Done. Time elapsed: {cluster_timer.get_seconds()} seconds")
        return cluster_collection
    
    @staticmethod
    def __update_cluster_labels(df_original, df_cluster, num_clusters, cluster_column):
        # Check if there are enough samples in df_cluster for spectral clustering
        if df_cluster.shape[0] >= 2:
            df_values = df_cluster.iloc[:, 1:4]
            n_neighbors = min(df_cluster.shape[0], 10)
            # Choose one of the following clustering methods.
            # Both versions use the cluster_qr strategy for assigning labels in the embedding space.
            # 1. Construct the affinity matrix by computing a graph of nearest neighbors
            spectral_nn = SpectralClustering(
                n_clusters=num_clusters,
                eigen_solver='amg',
                affinity='nearest_neighbors',
                n_neighbors=n_neighbors,
                assign_labels='cluster_qr'
            )
            # 2. Construct the affinity matrix using a radial basis function (RBF) kernel
            spectral_rbf = SpectralClustering(
                n_clusters=num_clusters,
                eigen_solver='amg',
                affinity='rbf',
                assign_labels='cluster_qr'
            )
            spectral = spectral_rbf.fit(df_values)
            labels = pd.DataFrame(spectral.labels_, index=df_cluster.index)
        else:
            # Fill with zeroes
            labels = pd.DataFrame([0 for _ in range(df_cluster.shape[0])], index=df_cluster.index)
        # Update original dataframe and recursive sub-dataframe
        labels = labels.rename(columns={0: cluster_column})
        df_original.update(labels)
        df_cluster.update(labels)
    
    @staticmethod
    def __create_subclusters(df_original, df_cluster, depth, br_factors, cluster_columns):
        if depth == len(br_factors) - 1:
            return
        df_subclusters = df_cluster.groupby(cluster_columns[depth])
        depth += 1
        for subcluster_name, df_subcluster in df_subclusters:
            Clustering.__update_cluster_labels(df_original, df_subcluster, br_factors[depth], cluster_columns[depth])
            # Recursion
            Clustering.__create_subclusters(df_original, df_subcluster, depth, br_factors, cluster_columns)
