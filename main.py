import logging
import os
import shutil
import subprocess
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction

import os , gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk # type: ignore

logger = logging.getLogger(__name__)
icon_theme = Gtk.IconTheme.get_default()


def try_lookup_icon(iconname, size, flags, fallback=None):
    if icon_theme.has_icon(iconname):
        return icon_theme.lookup_icon(iconname, size, flags).get_filename()
    else:
        logger.debug(f'Icon "{iconname}" not found')
        return None
    if icon_theme.has_icon(fallback):
        return icon_theme.lookup_icon(fallback, size, flags).get_filename()
    else:
        logger.debug(f'Fallback icon "{fallback}" not found')
        return None

document_open_icon = try_lookup_icon('document-open', 48, 0)
terminal_icon = try_lookup_icon('utilities-terminal', 48, 0)
gnome_saved_search_icon = try_lookup_icon('application-x-gnome-saved-search', 48, 0)
document_duplicate_icon = try_lookup_icon('document-duplicate', 48, 0, 'edit-copy')
folder_important_icon = try_lookup_icon('document-duplicate', 48, 0, 'important')
executable_icon = try_lookup_icon('application-x-executable', 48, 0)

def get_icon_filename(filename,size):

    final_filename = executable_icon
    if os.path.exists(filename):
        file = Gio.File.new_for_path(filename)
        info = file.query_info('standard::icon' , 0 , Gio.Cancellable())
        icon = info.get_icon().get_names()[0]
        final_filename = try_lookup_icon(icon, size, 0, 'application-x-executable')
    return final_filename
        
def FileActionResults(extension, file):
    logger.info('Actions for file %s' % file)
    return [
            ExtensionResultItem(
                icon=document_open_icon,
                name='Open file',
                on_enter=OpenAction(file)
            ),
            ExtensionResultItem(
                icon=document_duplicate_icon,
                name='Copy path',
                on_enter=CopyToClipboardAction(file)
            ),
            ExtensionResultItem(
                icon=terminal_icon,
                name='Open terminal here',
                on_enter=extension.get_open_in_terminal_script(file)
            )
        ]

class BalooIndexExtension(Extension):

    def __init__(self):
        super(BalooIndexExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        
    def get_open_in_terminal_script(self, path):
        """ Returns the script based on the type of terminal """
        terminal_emulator = self.preferences['terminal_emulator']
        return RunScriptAction(terminal_emulator,
                                   [path, '--working-directory', path])
    
    def get_baloo_executable(self):
        executable = self.preferences['baloo_executable']
        if executable and not shutil.which(executable):
            logger.error('Executable not found: %s' % executable)
        if not executable or not shutil.which(executable):
            # try different names like baloosearch, baloosearch5, baloosearch6
            executable_names = ['baloosearch', 'baloosearch5', 'baloosearch6']
            for name in executable_names:
                if shutil.which(name):
                    executable = name
                    break
        return executable

class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):

        items = []
        file_results = []

        folder_results = []

        if not event.get_argument():
            return RenderResultListAction([ExtensionResultItem(icon='images/icon.png',
                                                               name='bs <query>',
                                                               on_enter=HideWindowAction())])
        # Get the results from baloo search
        max_results = int(extension.preferences["max_results"])
        executable_name = extension.get_baloo_executable()

        result = subprocess.run([executable_name, '-l', '30', event.get_argument()], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        results = result.stdout.decode('utf-8').split('\n')


        for i, result in enumerate(results[:max_results-1] if len(results) > max_results else results[:max_results]):
            if not result:
                continue
            
            icon = get_icon_filename(result, 48)
            name = result.split('/')[-1]

            description = result
            if not os.path.exists(result):
                icon = folder_important_icon
                logger.error('File not found: %s' % result)

            if(os.path.isfile(result)):
                
                file_results.append(ExtensionResultItem(icon=icon,
                                                name=name,
                                                description=description,
                                                on_enter=RenderResultListAction(FileActionResults(extension, result))))
                
            elif(os.path.isdir(result)):
                
                folder_results.append(ExtensionResultItem(icon=icon,
                                name=name,
                                description=description,
                                on_enter=RenderResultListAction(FileActionResults(extension, result))))
                
            items.append(ExtensionResultItem(icon=icon,
                                name=name,
                                description=description,
                                on_enter=RenderResultListAction(FileActionResults(extension, result))))

            

        # If no results found show a message
        if not items:
            items.append(ExtensionResultItem(icon=gnome_saved_search_icon,
                                             name='No results found',
                                             on_enter=HideWindowAction()))
        if len(results) > max_results:
            items.append(ExtensionResultItem(icon=gnome_saved_search_icon,
                                             name='Please refine your search',
                                             description='Too many results'))


        if(extension.preferences["results_order"] == "Folders First"):
            items = folder_results + file_results
        elif(extension.preferences["results_order"] == "Files First"):
            items = file_results + folder_results
        

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        data = event.get_data()
        return RenderResultListAction([ExtensionResultItem(icon='images/icon.png',
                                                           name=data['new_name'],
                                                           on_enter=HideWindowAction())])


if __name__ == '__main__':
    BalooIndexExtension().run()
