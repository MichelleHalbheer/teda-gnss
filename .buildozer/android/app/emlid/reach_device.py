import datetime
import glob
import os
import time
import urllib.request
import webbrowser
import json

from zipfile import ZipFile

from main import GnssDevice

TMP_FOLDER = 'tmp_storage'

FILE_ENDINGS = {
    "RINEX-2_11": [".nav", ".obs", ".sbs"],
    "ubx": [".UBX"]
}


class ReachPlusDevice(GnssDevice):

    def __init__(self, url, name, export_format, all_files=False):
        self._url = url
        self._name = name
        self._format = export_format
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

    def rinex_2_11(self, request_time, file):
        """
        Name for exported rinex file
        :param request_time:
        :param file:
        :return:
        """
        return f'{self._name}{request_time.day}{request_time.hour}.{request_time.year}{file[-3]}'

    def download(self, start_time=None, end_time=None, exporters=None, expected_time=None):
        # Define names for temporary storage
        tmp_path = f'tmp_rinex_download_{self._name}.zip'
        tmp_folder = f'tmp_storage_{self._name}'
        # Set default parameters for start_time and end_time, last export and now respectively
        start_time = start_time if start_time else self._last_export
        end_time = end_time if end_time else datetime.datetime.now()
        # If no exporters set empty list
        exporters = exporters if exporters else []

        half_interval = (end_time - start_time) / 2
        # set default for expected time (middle between start and end)
        expected_time = expected_time if expected_time else start_time + half_interval

        logs_json_url = urllib.request.urlopen(f'http://{self._url}/logs')
        logs_json = json.loads(logs_json_url.read())
        logs_json_raw = [log for log in logs_json if log.get('type') == 'raw']
        raw_log_names = [log.get('name')[:-4] for log in logs_json_raw]

        ii = 0
        while abs(ii) < half_interval.seconds // 60:
            # Starting from expected time try all possible download files
            request_time = expected_time + datetime.timedelta(minutes=ii)
            ii = -ii if ii < 0 else -ii - 1
            # filter out times
            if request_time < start_time or request_time > end_time:
                continue  # TODO: Make more efficient
            # create download url
            #  http://terradatabox17.dyndns.org:50013/logs/download/raw_202002210755_RINEX-3_03
            time_str = request_time.strftime('%Y%m%d%H%M')
            log_name = f'reach_raw_{time_str}_{self._format.upper()}'

            try:
                idx = raw_log_names.index(log_name)
                log_id = logs_json_raw[idx].get('id')
            except ValueError as e:
                log_id = ''

            tmp_url = f'http://{self._url}/logs/download/{log_id}'

            # Try download
            try:
                urllib.request.urlretrieve(tmp_url, tmp_path)
            except Exception as e:
                print(str(e))
                continue
            print(f'SUCCESS - {self._name}')

            # Unpack and export files
            zip_file = ZipFile(tmp_path)
            zip_file.extractall(tmp_folder)
            for export_file in glob.glob(tmp_folder + '/*'):
                if any([tmp in export_file for tmp in FILE_ENDINGS.get(self._format)]):
                    for key, exporter in exporters.items():
                        if self._format == "RINEX-2_11":
                            file_name = self.rinex_2_11(request_time, export_file)
                        elif self._format == "ubx":
                            file_name = self.ubx_name(request_time, export_file)
                        else:
                            continue
                        exporter.store(
                            open(export_file, 'rb'),
                            file_name
                        )
                os.remove(export_file)

            self._last_export = request_time
            if not self._all_files:
                break

    @property
    def pause_time(self):
        return -1


class IntervalReachPlusDevice(ReachPlusDevice):

    def __init__(self, url, name, export_format, export_interval, export_start):
        """
        Splits download if for longer time frames
        :param url:
        :param name:
        :param export_format:
        :param export_interval:
        :param export_start:
        """
        super().__init__(url, name, export_format)
        self._export_interval = datetime.timedelta(minutes=export_interval)
        self._last_export = datetime.datetime.strptime(export_start, '%Y-%m-%d %H:%M')

    def download(self, start_time=None, end_time=None, exporters=None, expected_time=None):
        # Set default values
        start_time = start_time if start_time else self._last_export
        end_time = end_time if end_time else datetime.datetime.now() - self._export_interval
        self._last_export = expected_time if expected_time else self._last_export
        # Start device server
        #webbrowser.open(self._url, new=0)  # TODO: Create memory, to prevent unnecessary actions
        #time.sleep(360)

        if self._export_interval and self._last_export:
            ii = 0
            st = self._last_export + datetime.timedelta(minutes=1)
            while st < end_time and self._last_export + self._export_interval < datetime.datetime.now():
                et = self._last_export + 2 * self._export_interval
                if et > start_time:
                    st = max((start_time, self._last_export + datetime.timedelta(minutes=1)))
                    et = min(end_time, et)
                    super().download(st, et, exporters, self._last_export + self._export_interval)
                    if self._last_export < st:
                        self._last_export = et + datetime.timedelta(minutes=1)
                else:
                    self._last_export = et
                ii = ii + 1

    @property
    def pause_time(self):
        return self._last_export + self._export_interval - datetime.datetime.now()
