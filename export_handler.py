import errno
from ftplib import FTP
import os

from android.storage import app_storage_path#primary_external_storage_path
from android.permissions import request_permissions, Permission

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
        #request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
        self._folder = app_storage_path()
        print(self._folder)


    def store(self, file, file_name):
        # Define file path
        print(self._folder, file_name)
        file_path = os.path.join(self._folder, file_name)
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
