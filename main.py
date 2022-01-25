from logging import error
from kivy.lang import Builder
from kivy.properties import ObjectProperty

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.uix.screenmanager import ScreenManager
from kivymd.toast import toast
from kivy.core.window import Window
from kivymd.uix.filemanager import MDFileManager
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.picker import MDDatePicker
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from android.storage import primary_external_storage_path
from android.permissions import request_permissions, Permission

from datetime import datetime
import sys
import json
import os

from file_handler import ReachHandler

## Define Screen for the app to use
class ConversionForm(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

## Define Window Manager which will manage Screen
class WindowManager(ScreenManager):
    pass

#
# class LoadDialog(FloatLayout):
#     load = ObjectProperty(None)
#     cancel = ObjectProperty(None)

## Define App. This class includes everything the app does
class TEDAGNSS(MDApp):
    title = "Terradata GNSS Converter"

    def __init__(self, **kwargs):
        # Initializing app
        super().__init__(**kwargs)

        # Define necessary variables
        self._point_name = None
        self._antenna_height = None
        self._file_path = None
        self._file_name = None
        self._obs_date = None
        self._recording_date = None
        self._handler = None
        self._project_number = None

        # Load config file
        f = open(os.path.join(os.path.dirname(__file__), 'config_template.json'))
        self._config = json.load(f)
        f.close()

        # Bind for opening file manager
        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            ext=['.zip']
        )

        # Define error dialog
        self.error_dialog = MDDialog(
                text='', # Define empty text since it will be filled dynamically
                buttons=[
                    MDFlatButton(
                        text="SCHLIESSEN",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=self.dismiss_error_dialog
                    )
                ],
            )
        
        # Define success dialog
        self.success_dialog = MDDialog(
                text='Konversion erfolgreich.',
                buttons=[
                    # Finish conversion for one point
                    MDFlatButton(
                        text="FERTIG",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=self.dismiss_success_dialog
                    ),
                    # Add more observations for the same point
                    MDFlatButton(
                        text="WEITERE MESSUNGEN",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=self.dismiss_success_dialog_add_more
                    )
                ],
            )
        
        # Android specific: Request permissions to read and write files
        request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
        # Define storage path where app have writing rights on Android
        self.primary_external_storage_path = primary_external_storage_path()

    # Build the app
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        
        # Load the app from the separate kivy definition file
        self.root = Builder.load_file(os.path.join(os.path.dirname(__file__), 'teda_gnss.kv'))

    # Open the file manager
    def file_manager_open(self):
        '''
        Function to open the file manager
        '''

        self.file_manager.show(self.primary_external_storage_path) # output manager to the screen
        self.manager_open = True

    # Function to be called when a file is selected in the file manager
    def select_path(self, path):
        '''It will be called when you click on the file name
        or the catalog selection button.

        :type path: str;
        :param path: path to the selected directory or file;
        '''

        self._file_path = path
        self._file_name = os.path.basename(self._file_path)
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

        error_dict = {}
        error_messages = {
            'project_number': 'eine gültige Projektnummer',
            'point_name': 'einen Punktnamen',
            'antenna_height': 'eine gültige Antennenhöhe',
            'obs_date': 'ein gültiges Beobachtungsdatum',
            'file_path': 'und wähle eine Beobachtungsdatei aus'
        }

        if self.root.current_screen.ids.project_number.text:
            self._project_number = self.root.current_screen.ids.project_number.text
        else:
            error_dict['project_number'] = error_messages['project_number']

        if self.root.current_screen.ids.point_name.text:
            self._point_name = self.root.current_screen.ids.point_name.text
        else:
            error_dict['point_name'] = error_messages['point_name']
        
        if self.root.current_screen.ids.antenna_height.text:
            try:
                self._antenna_height = float(self.root.current_screen.ids.antenna_height.text)
            except ValueError:
                error_dict['antenna_height'] = error_messages['antenna_height']
        else:
            error_dict['antenna_height'] = error_messages['antenna_height']
            
        if self.root.current_screen.ids.observation_date.text:
            try:
                self._obs_date = datetime.strptime(
                    self.root.current_screen.ids.observation_date.text,
                    '%Y-%m-%d'    
                )
            except ValueError:
                error_dict['obs_date'] = error_messages['obs_date']
        else:
            error_dict['obs_date'] = error_messages['obs_date']

        if not self._file_path:
            error_dict['file_path'] = error_messages['file_path']

        if not error_dict:
            if not self._handler:
                self._handler = ReachHandler(name=self._point_name)
            self._handler.parse_file(self._file_path, self._config, self._obs_date, self._antenna_height, self._project_number)
            self.success_dialog.open()
        else:
            self.show_error_dialog(error_dict)

    def show_error_dialog(self, error_dict):
        error_list = [value for key, value in error_dict.items() if key is not 'file_path']
        error_text = f'Gib {", ".join(error_list)} ein {error_dict["file_path"] if "file_path" in error_dict.keys() else ""}.'
        self.error_dialog.text = error_text
        self.error_dialog.open()

    def dismiss_error_dialog(self, *args):
        self.error_dialog.dismiss()

    def dismiss_success_dialog(self, *args):
        self._handler.zip_exports(self._config, self._project_number, self._obs_date)

        self._file_name, self._obs_date, self._antenna_height, self._point_name = [None]*4
        
        self.root.current_screen.ids.point_name.text = 'Punktname eingeben'
        self.root.current_screen.ids.antenna_height.text = 'Antennenhöhe eingeben [m]'
        self.root.current_screen.ids.observation_date.text = 'Beobachtungsdatum (YYYY-MM-DD)'
        self.root.current_screen.ids.select_file.text = 'Beobachtungsdatei auswählen'

        self._handler = None

        self.success_dialog.dismiss()

    def dismiss_success_dialog_add_more(self, *args):
        self._file_name = None

        self.root.current_screen.ids.select_file.text = 'Beobachtungsdatei auswählen'

        self.success_dialog.dismiss()

def main(config_file):
    root = os.path.dirname(__file__)
    config_file = os.path.join(root, config_file)

    # Open configuration file
    f = open(config_file)
    config = json.load(f)
    f.close()
    
    TEDAGNSS().run()

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'config_template.json')
