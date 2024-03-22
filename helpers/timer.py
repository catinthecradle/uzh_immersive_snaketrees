#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

import time
from helpers.io_handler import IOHandler


class Timer:
    def __init__(self):
        self.timestamp = time.time()

    def reset(self):
        self.timestamp = time.time()

    def get_seconds(self):
        return self.__time_delta()

    def print_seconds(self, color=None):
        IOHandler.print_color(message=f"{self.__time_delta():.3f} seconds", color=color)

    def __time_delta(self):
        return time.time() - self.timestamp
