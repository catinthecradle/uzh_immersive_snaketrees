#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

class NoAudioException(Exception):
    """
    Exception raised if video file contains no audio.

    Parameters:
        file(str): path to the video file
    """
    def __init__(self, file):
        self.message = f"File {file} contains no audio"
        super().__init__(self.message)


class UnknownTaggerException(Exception):
    """
    Exception raised if tagger in config file is unknown.
    
    Parameters:
        tagger(str): Name of the tagger from config file
    """
    def __init__(self, tagger):
        self.message = f"Unknown tagger: {tagger}"
        super().__init__(self.message)
