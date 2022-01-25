import datetime
import glob
from logging import error
import os
import json

from zipfile import ZipFile
import zipfile

from android.storage import app_storage_path, primary_external_storage_path

from gnss_device import GnssDevice
from export_handler import FileExporter


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
        return os.path.join(f'{self._name}', f'{request_time.year - 2000}{request_time.month:02d}{request_time.day:02d}{self._name}.{self._export_id - 1:03d}')

    def parse_file(self, file_path, config, recording_time, antenna_height, project_number):
        extract_path = config.get('tmp_path')

        # Unpack and export files
        zip_file = ZipFile(file_path)
        zip_file.extractall(extract_path)
        for export_file in glob.glob(extract_path + '/*'):
            exporter = FileExporter(os.path.dirname(os.path.abspath(file_path)))

            file_name = self.ubx_name(recording_time, export_file)
            meta_name = f'{file_name[:-4]}.json'

            meta_dict = {
                'project_number': project_number,
                'point_name': self._name,
                'antenna_height': antenna_height
            }
            
            exporter.store(
                open(export_file, 'rb'),
                file_name
            )
            self._last_export = recording_time
            os.remove(export_file)

            with open(os.path.join(app_storage_path(), meta_name), 'w+') as meta_file:
                json.dump(meta_dict, meta_file)


    def zip_exports(self, config, project_number, obs_date):
        export_dir = os.path.join(app_storage_path(), self._name)
        
        date_string = datetime.datetime.strftime(obs_date, '%y%m%d')
        zip_dir = os.path.join(primary_external_storage_path(), 'Documents', 'Terradata_GNNS_Parser_Exports')
        if not os.path.exists(zip_dir):
            os.makedirs(zip_dir)
        zip_archive = os.path.join(zip_dir, f'teda_parser-{project_number}_{self._name}_{date_string}.zip')

        zip_file = ZipFile(zip_archive, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(export_dir):
            for file in files:
                zip_file.write(os.path.join(root, file),
                    os.path.relpath(os.path.join(root, file),
                        os.path.join(export_dir, '..')
                    )
                )


