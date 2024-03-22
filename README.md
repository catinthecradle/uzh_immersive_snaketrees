# Immersive SnakeTrees

Part of the Bachelor’s Project «Immersive SnakeTrees» by Jonas Zellweger  
March 2024, University of Zurich

## Description

Contains the source code for the Data Wrangling Pipeline:

### Feature Extraction
- Classification
- Aggregation

### Embedding
- Dimensionality Reduction
- Clustering
- Building the Hierarchy

## Getting Started

### Dependencies

* See [requirements.txt](./requirements.txt) for a complete list of all required pip libraries

### Installing
- Create a new python environment
- Use the package manager [pip](https://pip.pypa.io/en/stable/) to install all dependencies:
```zsh
python -m venv envsnaketrees
source envsnaketrees/bin/activate
pip install -r requirements.txt
```

## Usage

### Feature Extraction
Options:
```
python main.py [-i | --ifolder=<input_folder>] [-o | --ofolder=<output_folder>]
               [-s | --skip=<nof_files_to_skip>] [-l | --limit=<max_nof_files>]
               [-v | --verbose] [-h | --help]
```
Examples:
```zsh
# To run the complete feature extraction pipeline
$ python main.py -i '/path_to/media_folder/' -o '/where_to_store/output_files/'

# To start from #101 and execute 50 files:
python main.py -i '/media_folder/' -o '/output_files/' -s 100 -l 50
```


### Embedding
Options
```
python create_mappings.py [-t | task=<single_task>] [-f | file=<database_export>]
                          [-s | start=<start_task>] [-e | end=<end_task>] [-h | --help]
                          [-o | ofolder=<embeding_folder>] [-l | limit=<data_limit>]
```
Examples
```zsh
# To run the complete embedding pipeline
python create_mappings.py -o '/embedding_files/'

# To run parts of the pipeline from one stage to another
python create_mappings.py -s cluster -e metadata -o '/embedding_files/'

# To run individual stages
python create_mappings.py -t dr -o '/embedding_files/'
```

## Author

Jonas Zellweger  
[Follow on GitHub](https://github.com/catinthecradle)

University of Zurich, Department of Informatics  
Visualization and Multimedia Lab  
[Website](https://www.ifi.uzh.ch/en/vmml.html)

## Version History

* 1.0
    * Final Release for Bachelor’s Thesis
 
## License

**Immersive SnakeTrees**  
© 2024 by Jonas Zellweger, University of Zurich is licensed under CC BY-SA 4.0.  
To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/

The included libraries are licensed as follows:
- [Essentia](https://essentia.upf.edu/licensing_information.html) is available under [Affero GPLv3](http://www.gnu.org/licenses/agpl.html) for non-commercial applications
- The pre-trained machine learning models are available under the [CC BY-NC-ND 4.0 license](https://creativecommons.org/licenses/by-nc-nd/4.0/) for non-commercial use
- All the models created by the MTG are licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)
