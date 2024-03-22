#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

import sys
import os
import getopt
from helpers.io_handler import IOHandler, Color
from helpers.file_handler import FileHandler
from helpers.timer import Timer
from helpers.converter import Converter
from data_mapping.common import Mapping
from data_mapping.cleaner import Cleaner
from data_mapping.dimensionality_reduction import DimRed
from data_mapping.clustering import Clustering
from data_mapping.combiner import Combiner
from data_mapping.preprocessor import Preprocessor

# Define tasks
mapping_tasks = {
    'clean': 'vec',
    'dr': 'dr',
    'cluster': 'cluster',
    'branching': 'branching',
    'metadata': 'metadata',
    'preprocess': 'preprocess',
}


def read_main_arguments(argv):
    """
    Commands:
        -t --task <single_task>
        -s --start <start_task>
        -e --end <end_task>
        -f --file <input_file>
        -o --ofolder <output_folder>
        -l --limit <limit>

    Tasks:
        clean
        - extract values from exported csv or directly from database
        - separate by model
        - store to separate csv file, one per model
        dr
        - perform dimensionality reduction
        - store csv files with 3-D coordinates per model
        cluster
        - perform hierarchical clustering
        - store csv files with cluster assignments per model
        branching
        - Calculate geometry and feature vectors for branches and leaf clusters and store them into json files
        metadata
        - Read media paths and metadata for all songs from database and store them into a json file
        - Add information about all clusters a song is part of and store this information in a separate file to
        preprocess
        - Calculate distributions of songs in a cluster throughout other features
    
    Examples:
        python create_mappings.py -o 'output'
        python create_mappings.py -t clean -o 'output'
            (if pipeline starts with clean and no input file is given, data is extracted from database)
        python create_mappings.py -s clean -e dr -o 'output' -l 3000
        python create_mappings.py -s clean -e dr -f 'data/exported.csv' -o 'output' -l 3000
        python create_mappings.py -s dr -e cluster -o 'output' -l 1000
            (if pipeline starts after first task (clean), the source file is implicitly given by output folder)
    
    :param argv:
    :return:
    """
    start_task = None
    end_task = None
    input_file = None
    output_folder = None
    limit = None
    usage_string = "python create_mappings.py -o <output_folder> [-l <limit>]"
    try:
        opts, args = getopt.getopt(
            args=argv,
            shortopts="ht:s:e:f:o:l:",
            longopts=["help", "task=", "start=", "end=", "file=", "ofolder=", "limit="]
        )
    except getopt.GetoptError as err:
        IOHandler.show_error(f"Error: {err}")
        IOHandler.show_error(f"Correct usage: {usage_string}")
        sys.exit()
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            IOHandler.print_color(usage_string, enforce=True, color=Color.GREEN)
            sys.exit()
        elif opt in ("-t", "--task"):
            start_task = arg
            end_task = arg
        elif opt in ("-s", "--start"):
            start_task = arg
        elif opt in ("-e", "--end"):
            end_task = arg
        elif opt in ("-f", "--file"):
            input_file = arg
        elif opt in ("-o", "--ofolder"):
            output_folder = arg
        elif opt in ("-l", "--limit"):
            try:
                limit = int(arg)
            except TypeError:
                IOHandler.show_error("ERROR: Provided limit is not an integer value!")
                sys.exit()

    return start_task, end_task, input_file, output_folder, limit


def verified_arguments(parsed_arguments):
    start_task, end_task, input_file, output_folder, limit = parsed_arguments

    # Calculate index of first task
    if start_task:
        if start_task in mapping_tasks.keys():
            start_index = list(mapping_tasks.keys()).index(start_task)
        else:
            IOHandler.show_error("ERROR: Invalid start task!")
            sys.exit()
    else:
        start_index = 0

    # Calculate index of last task
    if end_task:
        if end_task in mapping_tasks.keys():
            end_index = list(mapping_tasks.keys()).index(end_task)
        else:
            IOHandler.show_error("ERROR: Invalid end task!")
            sys.exit()
    else:
        end_index = len(mapping_tasks) - 1

    # Assert correct task order
    if end_index < start_index:
        IOHandler.show_error("ERROR: Wrong task order for pipeline!")
        sys.exit()

    # Assert that input file exists if one was provided
    if input_file and not os.path.isfile(input_file):
        IOHandler.show_error("ERROR: The input csv file does not exist!")
        IOHandler.show_error(input_file)
        sys.exit()

    # Assert that an existing output folder was provided if pipeline starts after first task
    if start_index > 0 and (not output_folder or not os.path.exists(output_folder)):
        IOHandler.show_error("ERROR: Please provide an existing output folder!")
        sys.exit()

    return start_index, end_index, input_file, output_folder, limit


def main(argv):
    program_timer = Timer()
    parsed_arguments = read_main_arguments(argv)
    start_index, end_index, csv_file, output_folder, limit = verified_arguments(parsed_arguments)
    settings = FileHandler.read_config_file()
    database_name = settings['database']['name']
    if output_folder is None:
        output_folder = f"mappings_{Converter.get_file_timestring()}"

    clean_collection = {}
    dr_collection = {}
    cluster_collection = {}
    ue_leaf_clusters = {}
    containing_clusters_dict = {}

    # ====================================
    #   clean
    # ====================================
    if start_index == 0:
        # Clean data from csv or database source
        if csv_file:
            clean_collection = Cleaner.convert_from_csv(csv_file, limit)
        else:
            clean_collection = Cleaner.convert_from_database(database_name, limit)
        Mapping.export_to_multiple_csv(
            model_collection=clean_collection,
            output_folder=output_folder,
            prefix=mapping_tasks['clean'],
            data_name="features"
        )

    if end_index < 1:
        print(f"Overall time: {program_timer.get_seconds()} seconds")
        return    # Abort early

    # ====================================
    #   dr
    # ====================================
    if start_index <= 1:
        # Dimensionality reduction
        if start_index == 1:
            clean_collection = Mapping.import_from_multiple_csv(
                input_folder=output_folder,
                prefix=mapping_tasks['clean'],
                limit=limit
            )
        dr_collection = DimRed.perform_tsne(
            model_collection=clean_collection,
            perplexity=settings['dr']['perplexity'],
            iterations=settings['dr']['iterations']
        )
        Mapping.export_to_multiple_csv(
            model_collection=dr_collection,
            output_folder=output_folder,
            prefix=mapping_tasks['dr'],
            data_name="TSNE Coordinates"
        )

    if end_index < 2:
        print(f"Overall time: {program_timer.get_seconds()} seconds")
        return    # Abort early

    # ====================================
    #   cluster
    # ====================================
    if start_index <= 2:
        # Clustering
        if start_index == 2:
            dr_collection = Mapping.import_from_multiple_csv(
                input_folder=output_folder,
                prefix=mapping_tasks['dr'],
                limit=limit
            )
        cluster_collection = Clustering.hierarchical_spectral_clustering(
            model_collection=dr_collection,
            branching_factors=settings['clustering']['branching_factors']
        )
        Mapping.export_to_multiple_csv(
            model_collection=cluster_collection,
            output_folder=output_folder,
            prefix=mapping_tasks['cluster'],
            data_name="Spectral Clusters"
        )

    if end_index < 3:
        print(f"Overall time: {program_timer.get_seconds()} seconds")
        return    # Abort early

    # ====================================
    #   branching
    # ====================================
    if start_index <= 3:
        # Calculate geometry and feature vectors for branches and leaf clusters and store them into json files
        if start_index == 3:
            cluster_collection = Mapping.import_from_multiple_csv(
                input_folder=output_folder,
                prefix=mapping_tasks['cluster'],
                limit=limit
            )
        if start_index > 0:
            clean_collection = Mapping.import_from_multiple_csv(
                input_folder=output_folder,
                prefix=mapping_tasks['clean'],
                limit=limit
            )
        ue_branch_clusters, ue_leaf_clusters = Combiner.process_all_models(
            cluster_dataframes=cluster_collection,
            vector_dataframes=clean_collection,
            model_full_names=settings['models'],
            tree_structure_yaml="tree_structure.yaml"
        )
        ue_leaf_clusters_extended = Preprocessor.append_stats_to_leaf_clusters(
            leaf_cluster_geometry_dict=ue_leaf_clusters
        )
        # Export to JSON
        print("Exporting json files... ", end="")
        Mapping.export_collection_to_json(
            collection=ue_branch_clusters,
            output_file=os.path.join(output_folder, settings['branching_filenames']['branches_filename'])
        )
        Mapping.export_collection_to_json(
            collection=ue_leaf_clusters_extended,
            output_file=os.path.join(output_folder, settings['branching_filenames']['leaves_filename'])
        )
        print("Done.")

    if end_index < 4:
        print(f"Overall time: {program_timer.get_seconds()} seconds")
        return    # Abort early
    
    # ====================================
    #   metadata
    # ====================================
    if start_index <= 4:
        # Read media paths and metadata for all songs from database and store them into a json file
        if start_index == 4:
            ue_leaf_clusters = Mapping.import_dict_from_json(
                file_name=os.path.join(output_folder, settings['branching_filenames']['leaves_filename']),
            )
        metadata_df = Combiner.read_features_from_database(
            db_name=database_name,
            limit=limit
        )
        Combiner.make_concert_dates_human_readable(metadata_df, 'en')
        # Add information about all clusters a song is part of and store this information in a separate file too
        containing_clusters_dict, metadata_df = Preprocessor.add_containing_clusters(
            metadata_df=metadata_df,
            cluster_geometry_dict=ue_leaf_clusters
        )
        # metadata_df.set_index('media_id', inplace=True)
        Mapping.export_df_to_json(
            df=metadata_df,
            output_file=os.path.join(output_folder, settings['metadata']['metadata_filename'])
        )
        Mapping.export_collection_to_json(
            collection=containing_clusters_dict,
            output_file=os.path.join(output_folder, settings['preprocessor']['containing_clusters_filename'])
        )
    
    if end_index < 5:
        print(f"Overall time: {program_timer.get_seconds()} seconds")
        return  # Abort early
    
    # ====================================
    #   preprocess
    # ====================================
    if start_index <= 5:
        # Calculate distributions of songs in a cluster throughout other features
        if start_index == 5:
            containing_clusters_dict = Mapping.import_dict_from_json(
                file_name=os.path.join(output_folder, settings['preprocessor']['containing_clusters_filename'])
            )
        cluster_relations_df = Preprocessor.calculate_cluster_relations(
            containing_clusters=containing_clusters_dict
        )
        Mapping.export_df_to_csv(
            dataframe=cluster_relations_df,
            output_file=os.path.join(output_folder, settings['preprocessor']['cluster_relations_filename']),
            index=False,
            header=False
        )
    
    print(f"Overall time: {program_timer.get_seconds():.2f} seconds")


if __name__ == '__main__':
    main(sys.argv[1:])
