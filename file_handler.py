import datetime
import glob
import os

from zipfile import ZipFile

from gnss_device import GnssDevice
from export_handler import Exporter


class ReachHandler(GnssDevice):
    def __init__(self, name, all_files=False):
        self._name = name
        self._all_files = all_files
        self._export_id = 0
        self._last_export = datetime.datetime.now() - datetime.timedelta(days=30000)

    def ubx_name(self, request_time: datetime.datetime, file):
        """
        TODO: Make naming system more flexible
        Name for exported ubx file
        :param request_time:
        :param file:
        :return:
        """
        # If new day, set index 0, otherwise increase index
        self._export_id = 1 if self._last_export.day != request_time.day else self._export_id + 1
        return f'{self._name}\\{request_time.year - 2000}{request_time.month:02d}{request_time.day:02d}{self._name}.{self._export_id - 1:03d}'

    def parse_file(self, file_path, config, recording_time):
        exporters = {key: Exporter.forge(item) for key, item in config.get('exporter').items()}

        extract_path = config.get('tmp_path')

        # Unpack and export files
        zip_file = ZipFile(file_path)
        zip_file.extractall(extract_path)
        for export_file in glob.glob(extract_path + '/*'):
            for key, exporter in exporters.items():
                file_name = self.ubx_name(recording_time, export_file)

                exporter.store(
                    open(export_file, 'rb'),
                    file_name
                )
            os.remove(export_file)

