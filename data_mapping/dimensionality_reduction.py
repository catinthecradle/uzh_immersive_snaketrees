#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

# Import necessary libraries
from sklearn.manifold import TSNE
from helpers.timer import Timer
import pandas as pd


class DimRed:
    
    @staticmethod
    def perform_tsne(model_collection, perplexity=30, iterations=1000):
        print(f"Perform t-SNE for all {len(model_collection)} models:")
        tsne_collection = {}
        for model_name, feature_df in model_collection.items():
            print(f"Perform t-SNE in 3-D for {model_name}...")
            tsne_timer = Timer()
            # Separate index column and data columns
            index_column = feature_df.iloc[:, 0]
            df_values = feature_df.iloc[:, 1:]
            # Perform t-SNE in 3-D
            tsne = TSNE(n_components=3, verbose=1, perplexity=perplexity, n_iter=iterations)
            tsne_result = tsne.fit_transform(df_values)
            # Attach index column to tsne data
            tsne_result = pd.concat([index_column, pd.DataFrame(tsne_result, columns=['X', 'Y', 'Z'])], axis=1)
            # and store dataframe in collection
            tsne_collection[model_name] = tsne_result
            print(f"Done. Time elapsed: {tsne_timer.get_seconds()} seconds")
        return tsne_collection
    