#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

import datetime
import locale

locale_codes = {
    'de': 'de_CH.UTF-8',
    'fr': 'fr_CH.UTF-8',
    'it': 'it_CH.UTF-8',
    'en': 'en_GB.UTF-8'
}


class Converter:
    
    @staticmethod
    def datetime_to_timestring(dt):
        datetime_object = datetime.datetime.strptime(dt, '%Y-%m-%d')
        return datetime_object.strftime("%d.%m.%Y")
    
    @staticmethod
    def datetime_to_localized_timestring(dt, language='en'):
        datetime_object = datetime.datetime.strptime(dt, '%Y-%m-%d')
        if language in locale_codes:
            lc = locale_codes[language]
        else:
            lc = locale_codes['en']
        previous = locale.getlocale(locale.LC_TIME)
        locale.setlocale(locale.LC_TIME, lc)
        local_date = datetime_object.strftime('%A, %e. %B %Y')
        locale.setlocale(locale.LC_TIME, previous)
        return local_date

    @staticmethod
    def file_creation_string(datetime_object=None):
        if datetime_object is None:
            datetime_object = Converter.current_timestamp()
        return datetime_object.strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def current_timestamp():
        return datetime.datetime.now()

    @staticmethod
    def song_info_textblock(song_data):
        metadata = song_data['metadata']
        perf_date = Converter.datetime_to_timestring(metadata['date'])

        song_info = [f"Concert info for {song_data['media_id']} ({song_data['media_path']})",
                     f"'{metadata['title']}' from concert '{metadata['concert_name']}'",
                     f"performed by: {', '.join(metadata['musicians'])}", f"{perf_date} at {metadata['location']}"]
        return "\n".join(song_info)

    @staticmethod
    def overall_song_execution_time_str(counter, duration):
        plurality = "songs" if counter > 1 else "song"
        return f"Overall execution time for {counter} {plurality}: {duration:.3f} seconds"

    @staticmethod
    def seconds_to_dhms_str(seconds):
        duration = datetime.timedelta(seconds=seconds)
        d = duration.days
        m, s = divmod(duration.seconds, 60)
        h, m = divmod(m, 60)
        return f"{d} days, {h} hours, {m} minutes and {s} seconds"
    
    @staticmethod
    def get_file_timestring():
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
