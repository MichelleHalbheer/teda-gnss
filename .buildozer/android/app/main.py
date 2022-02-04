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
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from android.storage import primary_external_storage_path, app_storage_path
from android.permissions import request_permissions, Permission

from datetime import datetime
import json
import os
import shutil

from file_handler import ReachHandler

## Define Screen for the app to use
class ConversionForm(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

## Define Window Manager which will manage Screen
class WindowManager(ScreenManager):
    pass

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
                text='Konversion erfolgreich. Zum abschliessen des Punktes "Fertig" drücken. Um weitere Messungen für denselben Punkt am selben Datum hinzuzufügen "Weitere Messungen" drücken.',
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

        # Define confirmation and reset dialog
        self.confirm_finish_reset_dialog = MDDialog(
                text='Soll der Punkt wirklick abgeschlossen und die konvertierten Daten abgelegt werden?',
                buttons=[
                    MDFlatButton(
                        text="ABBRECHEN",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=self.dismiss_confirm_reset_dialog_return
                    ),
                    MDRaisedButton(
                        text="WEITER",
                        theme_text_color="Custom",
                        on_release=self.dismiss_confirm_reset_dialog_finish
                    )
                ],
            )

        # Define dialog to prompt if point should be closed when input changed
        self.input_changed_dialog = MDDialog(
                text='Eine oder mehrere Eingaben haben sich geändert. Wenn du fortfährst wird der bisherige Punkt abgeschlossen und die Daten abgelegt. Möchtest du frotfahren',
                buttons=[
                    MDFlatButton(
                        text="ABBRECHEN",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=self.dismiss_input_changed_dialog_return
                    ),
                    MDRaisedButton(
                        text="WEITER",
                        theme_text_color="Custom",
                        on_release=self.dismiss_input_changed_dialog_finish
                    )
                ],
            )
        
        # Android specific: Request permissions to read and write files
        request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
        # Define storage path where app have writing rights on Android
        self.primary_external_storage_path = primary_external_storage_path()    	
        
    
    def on_pause(self):
        '''
        Kivy function enabling the app to be paused when closing
        '''
        return True

    def build(self):
        '''
        Kivy function called to build the app
        '''

        # Define theme colors
        self.theme_cls.primary_palette = "Blue"
        
        # Load the app from the separate kivy definition file
        self.root = Builder.load_file(os.path.join(os.path.dirname(__file__), 'teda_gnss.kv'))

    def file_manager_open(self) -> None:
        '''
        Function to open the file manager
        Provided by the KivyMD documentation.

        Parameters
        ----------
        None

        Returns
        -------
        None
        '''

        self.file_manager.show(self.primary_external_storage_path) # output manager to the screen
        self.manager_open = True


    def select_path(self, path: str) -> None:
        '''
        Function called when a file is clicked in the file manager.

        Parameters
        ----------
        path : String
            path of the selected file as passed by kivy
        
        Returns
        -------
        None
        '''

        # Set the fiel path variable
        self._file_path = path

        # Get the file name out of the path for display on the file manager button
        self._file_name = os.path.basename(self._file_path)
        self.root.current_screen.ids.select_file.text = self._file_name # Set the text of the file manager button

        # Close manager and display the selected file path
        self.exit_manager()
        toast(path)

    def exit_manager(self, *args) -> None:
        '''
        Function called to close the file manager.
        Provided by the KivyMD documentation.
        '''

        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        '''
        Called when buttons are pressed on the mobile device.
        Provided by the KivyMD documentation.
        '''

        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True
    

    ### DATE PICKER BUGGED. HAVING USER ENTER DATE MANUALLY. ###
    ### TO BE REIMPLEMENTED AT SOME POINT ###

    # def get_date(self, date):
    #     self._recording_date = date

    # def show_date_picker(self):
    #     date_dialog = MDDatePicker(callback=self.get_date,)
    #     date_dialog.open()

    
    def parse_file(self):
        '''
        Take the file inidicated by the file manager and parse it to the Bernese Server format.
        Write any metadata into a JSON file.
        If not everything was entered create error message.
        '''

        # Create dictionary for error message
        error_list = {}

        # List of possible errors per entry field
        error_messages = {
            'project_number': 'Projektnummer',
            'point_name': 'Punktname',
            'antenna_height': 'Antennenhöhe',
            'obs_date': 'Beobachtungsdatum',
            'file_path': 'Beobachtungsdatei'
        }

        ## Check all the entries for validity
        ## If the field is empty add the error text to the dict

        # Check the project number
        if self.root.current_screen.ids.project_number.text:
            if isinstance(self._project_number, str) and self._project_number != self.root.current_screen.ids.project_number.text:
                self.input_change_confirmation()
                return
            else:
                self._project_number = self.root.current_screen.ids.project_number.text
        else:
            error_list.append(error_messages['project_number'])

        # Check the point name
        if self.root.current_screen.ids.point_name.text:
            if isinstance(self._point_name, str) and self._point_name != self.root.current_screen.ids.point_name.text:
                self.input_change_confirmation()
                return
            else:
                self._point_name = self.root.current_screen.ids.point_name.text
        else:
            error_list.append(error_messages['point_name'])

        # Check the antenna height
        if self.root.current_screen.ids.antenna_height.text:
                # Check the antenna height is a number
                try:
                    antenna_height = float(self.root.current_screen.ids.antenna_height.text)
                    if isinstance(self._antenna_height, float) and self._antenna_height != antenna_height:
                        self.input_change_confirmation()
                        return
                    else:
                        self._antenna_height = antenna_height
                except ValueError:
                    error_list.append(error_messages['antenna_height'])
        else:
            error_list.append(error_messages['antenna_height'])

        # Check the observation date
        if self.root.current_screen.ids.observation_date.text:
            # Check if the date can be parsed to a date.
            # Currently only ISO8601 format is supported.
            try:
                obs_date = datetime.strptime(
                    self.root.current_screen.ids.observation_date.text,
                    '%Y-%m-%d'
                )
                if isinstance(self._obs_date, datetime) and self._obs_date != obs_date:
                    self.input_change_confirmation()
                    return
                else:
                    self._obs_date = obs_date
            except ValueError:
                error_list.append(error_messages['obs_date'])
        else:
            error_list.append(error_messages['obs_date'])

        # Check if an observation directory has been selected
        if not self._file_path:
            error_list.append(error_messages['file_path'])

        # If the error dict is empty, parse the file and create the meta json
        if not error_list:
            # If no file handler has been created before, create a new one
            if not self._handler:
                self._handler = ReachHandler(name=self._point_name)
            self._handler.parse_file(self._file_path, self._obs_date, self._antenna_height, self._project_number)
            self.success_dialog.open()
        else:
            # If any error has been detected, show a dialog
            self.show_error_dialog(error_list)

    def input_change_confirmation(self) -> None:
        '''
        Function to  prompt wether input change was on purpose
        '''

        self.input_changed_dialog.open()

    def show_error_dialog(self, error_list: list) -> None:
        '''
        Builds the error message and displays it in a dialog

        Parameters
        ----------
        error_dict : list
            List containing the errors that occured when parsing

        Returns
        -------
        None
        '''

        # Create error text
        error_text = f'{", ".join(error_list)} {"sind" if len(error_list > 1) else "ist"} ungültig.'

        # Set the text of the dialog
        self.error_dialog.text = error_text

        self.error_dialog.open()

    def dismiss_error_dialog(self, *args) -> None:
        '''
        Function to dismiss the error dialog.
        Provided by the KivyMD documentation.
        '''

        self.error_dialog.dismiss()

    def dismiss_success_dialog(self, *args) -> None:
        '''
        Function to dismiss the success dialog without adding more observation files.
        '''

        self.finish_point_reset()

        self.success_dialog.dismiss()

    def show_confirm_reset_dialog(self) -> None:
        '''
        Builds the error message and displays it in a dialog

        Parameters
        ----------
        None

        Returns
        -------
        None
        '''

        self.confirm_finish_reset_dialog.open()

    def dismiss_confirm_reset_dialog_return(self, *args) -> None:
        '''
        Function to close the confirmation dialog and return to the same screen
        '''
        
        self.confirm_finish_reset_dialog.dismiss()

    def dismiss_confirm_reset_dialog_finish(self, *args) -> None:
        '''
        Function to close the confirmation dialgo and finish the point.
        Will reset the screen.
        '''

        self.finish_point_reset()

        self.confirm_finish_reset_dialog.dismiss()

    def finish_point_reset(self) -> None:
        '''
        Function to finish conversion for a given point and date.
        This creates a zip archive from the previously parsed files and stores it in a persistent directory.
        '''

        # Create the zip archive
        self._handler.zip_exports(self._project_number, self._obs_date)

        # Reset the variables storing the information
        self._file_name, self._obs_date, self._antenna_height, self._point_name, self._project_number = [None]*5
        
        # Reset the screen so a new point can be parsed        
        self.root.current_screen.ids.point_name.text = ''
        self.root.current_screen.ids.antenna_height.text = ''
        self.root.current_screen.ids.observation_date.text = ''
        self.root.current_screen.ids.select_file.text = 'Beobachtungsdatei auswählen'

        # Remove the file handler as it is specific for any given point
        self._handler = None

    def finish_point(self) -> None:
        '''
        Function to finish conversion for a given point and date.
        This creates a zip archive from the previously parsed files and stores it in a persistent directory.
        '''

        # Create zip archive
        self._handler.zip_exports(self._project_number, self._obs_date)

        # Reset the variables storing the information
        self._file_name, self._obs_date, self._antenna_height, self._point_name, self._project_number = [None] * 5

        # Remove the file handler as it is specific for any given point
        self._handler = None

        self.parse_file()

    def dismiss_success_dialog_add_more(self, *args) -> None:
        '''
        Function to dismiss the success dialog with the option to add more measurements for the same point.
        '''

        # Reset the observation file
        self._file_name = None
        self.root.current_screen.ids.select_file.text = 'Beobachtungsdatei auswählen'
        
        # Show finish button and enable it
        self.root.current_screen.ids.finish_point.opacity = 100
        self.root.current_screen.ids.finish_point.disabled = False

        self.success_dialog.dismiss()

    def dismiss_input_changed_dialog_return(self, *args) -> None:
        '''
        Function to dismiss confirmation dialog if user decides not to continue
        '''

        self.input_changed_dialog.dismiss()

    def dismiss_input_changed_dialog_finish(self, *args) -> None:
        '''
        Function to dismiss confirmation dialog and end point
        '''

        self.finish_point()
        
        self.input_changed_dialog.dismiss()

def main():
    TEDAGNSS().run()

if __name__ == '__main__':
    main()
