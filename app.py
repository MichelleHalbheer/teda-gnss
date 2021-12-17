from kivy.lang import Builder
from kivy.properties import ObjectProperty

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.tab import MDTabsBase
from kivymd.icon_definitions import md_icons
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.textfield import MDTextField
from kivymd.toast import toast
from kivy.factory import Factory
from kivy.uix.modalview import ModalView
from kivy.core.window import Window
from kivymd.uix.filemanager import MDFileManager
from kivymd.theming import ThemeManager
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivymd.uix.picker import MDDatePicker

from datetime import datetime
import sys
import json
import os

from file_handler import ReachHandler

from app_config.theming import *

class ConversionForm(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._on_enter_trig = trig = Clock.create_trigger(self._my_on_enter)
        self.bind(on_enter=trig)

    def _my_on_enter(self, *args):
            print(self.ids)

class AcknowledgeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._on_enter_trig = trig = Clock.create_trigger(self._my_on_enter)
        self.bind(on_enter=trig)

    def _my_on_enter(self, *args):
            print(self.ids)

class WindowManager(ScreenManager):
    pass

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class TEDAGNSS(MDApp):
    title = "Terradata GNSS Converter"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._file_path = None
        self.file_name = None
        self._obs_date = None
        self._recording_date = None

        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            ext=['.zip']
        )

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        
        self.root = Builder.load_file(os.path.join(os.path.dirname(__file__), 'teda_gnss.kv'))
        pass

    def file_manager_open(self):
        self.file_manager.show(os.path.dirname(__file__))  # output manager to the screen
        self.manager_open = True

    def select_path(self, path):
        '''It will be called when you click on the file name
        or the catalog selection button.

        :type path: str;
        :param path: path to the selected directory or file;
        '''

        self._file_path = path
        self._file_name = self._file_path[self._file_path.rindex('\\')+1:]
        self.root.current_screen.ids.select_file.text = self._file_name
        self.exit_manager()
        toast(path)

    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''

        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        '''Called when buttons are pressed on the mobile device.'''

        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True
    

    ### DATE PICKER BUGGED. TAKING DATE FROM DOWNLOADED DIRECTORY ###
    # def get_date(self, date):
    #     self._recording_date = date

    # def show_date_picker(self):
    #     date_dialog = MDDatePicker(callback=self.get_date,)
    #     date_dialog.open()

    def parse_file(self):
        if not self._file_path:
            pass

        self._obs_date = datetime.strptime(self._file_name[9:17],'%Y%m%d') 

def main(config_file):
    root = os.path.dirname(__file__)
    config_file = os.path.join(root, config_file)

    # Open configuration file
    f = open(config_file)
    config = json.load(f)
    f.close()
    
    TEDAGNSS().run()
    
    # file_path = input('Enter path of file to be parsed:\t')
    # name = input('Enter receiver name:\t')
    # recording_time = datetime.strptime(input('Enter recording date (DD.MM.YYYY):\t'), '%d.%m.%Y')

    # handler = ReachHandler(name=name)

    # handler.parse_file(file_path, config, recording_time)

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'config_template.json')