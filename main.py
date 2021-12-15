import datetime
import errno
import json
import subprocess
import sys
import time
from ftplib import FTP
import os

from forge import forge_function
from gnss_device import GnssDevice
from emlid.reach_device import *

root = os.path.dirname(__file__)
print(root)

class Exporter:
    """
    Exports a given file
    """
    subclasses = {}  # Contains reference to all implementation

    @staticmethod
    def forge(config, config_type=None):
        """
        Factory for subclasses
        :param config:
        :param config_type:
        :return:
        """
        return forge_function(Exporter, config, config_type)

    def store(self, file, file_name):
        pass


class FileExporter(Exporter):

    def __init__(self, folder):
        """
        Exports file to OS directory
        :param folder:
        """
        self._folder = folder

    def store(self, file, file_name):
        # Define file path
        file_path = self._folder + "\\" + file_name
        # create directories if not exist
        if not os.path.exists(os.path.dirname(file_path)):
            try:
                os.makedirs(os.path.dirname(file_path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        # Store in file
        f = open(file_path, 'wb')
        f.write(file.read())
        f.close()


class FtpExporter(Exporter):

    def __init__(self, folder, url, user, account=None, pw=None, port=21):
        """
        Stores file on ftp server
        :param folder: directory on fpt
        :param url:
        :param user:
        :param account:
        :param pw:
        :param port: default 21
        """
        self._folder = folder
        self._url = url
        self._user = user
        self._account = account if account else user
        self._pw = pw
        self._port = port

    def store(self, file, file_name):
        # Create connection
        ftp = FTP(file)
        ftp.login(user=self._user, passwd=self._pw, acct=self._account)
        # Navigate to directory
        ftp.cwd(self._folder)
        # Store file
        ftp.storbinary(f'STOR {file_name}', file)
        ftp.close()


def main(config_file, device_key=None):
    """
    Process, main process is defined by device_key = None
    :param config_file: path to configuration file
    :param device_key: key for device the process is for, Main process has no key
    :return:
    """

    # Open configuration file
    f = open(config_file)
    config = json.load(f)
    f.close()

    if device_key is None:
        # Start process for each device, first device uses main process
        first = True
        for key in config.get('devices').keys():
            # define key for first device
            if first:
                device_key = key
                first = False
            else:
                # start process for other devices
                p = subprocess.Popen([sys.executable, __file__, config_file, key])
    # Create exporter classes
    exporters = {key: Exporter.forge(item) for key, item in config.get('exporter').items()}
    # Define start of process
    end_time = datetime.datetime.now()-datetime.timedelta(minutes=config.get('interval'))
    start_time = end_time
    """
    prev_check defines start time:
    if integer, minutes before now
    if "today", from this morning 00:00
    """
    prev_check = config.get('prev_check')
    if isinstance(prev_check, str):
        if prev_check == 'today':
            start_time = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
    elif isinstance(prev_check, int):
        start_time = end_time - datetime.timedelta(minutes=config.get('prev_check'))
    # Create device class
    device = GnssDevice.forge(config.get('devices').get(device_key))
    # for ever:
    while True:
        # find file from start_time/last_download until now
        device.download(start_time=start_time, exporters=exporters)
        start_time = None
        # sleep from last download until next expected download, at least one minute
        time.sleep(max(device.pause_time.seconds, 60))


if __name__ == "__main__":
    main(
        sys.argv[1] if len(sys.argv) > 1 else os.path.join(root,'config_template.json'),
        sys.argv[2] if len(sys.argv) > 2 else None
    )


    