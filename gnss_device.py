from forge import forge_function


class GnssDevice:
    """
    Base class for GnssDevice
    """

    subclasses = {}

    @staticmethod
    def forge(config, config_type=None):
        """
        Factory method for gnss devices
        :param config:
        :param config_type:
        :return:
        """
        return forge_function(GnssDevice, config, config_type)

    def download(self, start_time, end_time, exporters):
        """
        Download file(s) in epoch start_time to end_time, use exporters for export
        :param start_time:
        :param end_time:
        :param exporters:
        :return:
        """
        pass

    @property
    def pause_time(self):
        """
        Time to wait, till next download
        :return:
        """
        return 0
