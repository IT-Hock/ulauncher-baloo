import logging
import os
import subprocess
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction

import os , gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk

logger = logging.getLogger(__name__)
icon_theme = Gtk.IconTheme.get_default()

document_open_icon = icon_theme.lookup_icon('document-open', 48, 0).get_filename()
terminal_icon = icon_theme.lookup_icon('utilities-terminal', 48, 0).get_filename()
gnome_saved_search_icon = icon_theme.lookup_icon('application-x-gnome-saved-search', 48, 0).get_filename()

if icon_theme.has_icon('document-duplicate'):
    document_duplicate_icon = icon_theme.lookup_icon('document-duplicate', 48, 0).get_filename()
else:
    logger.error('Icon document-duplicate not found')
    document_duplicate_icon = icon_theme.lookup_icon('edit-copy', 48, 0).get_filename()

if icon_theme.has_icon('folder-important'):
    folder_important_icon = icon_theme.lookup_icon('folder-important', 48, 0).get_filename()
else:
    logger.error('Icon folder-important not found')
    folder_important_icon = icon_theme.lookup_icon('important', 48, 0).get_filename()

def get_icon_filename(filename,size):
    
    final_filename = "images/icon.png"
    if os.path.exists(filename):
        file = Gio.File.new_for_path(filename)
        info = file.query_info('standard::icon' , 0 , Gio.Cancellable())
        icon = info.get_icon().get_names()[0]

        icon_file = icon_theme.lookup_icon(icon , size , 0)
        if icon_file != None:
            final_filename = icon_file.get_filename()
        else:
            final_filename = icon_theme.lookup_icon('application-x-executable' , size , 0).get_filename()
    else:
        final_filename = icon_theme.lookup_icon('application-x-executable' , size , 0).get_filename()
    
    return final_filename

def get_default_terminal():
    terminal = 'gnome-terminal'
    if os.path.exists('/usr/bin/alacritty'):
        terminal = 'alacritty'
    elif os.path.exists('/usr/bin/konsole'):
        terminal = 'konsole'
    elif os.path.exists('/usr/bin/xfce4-terminal'):
        terminal = 'xfce4-terminal'
    elif os.path.exists('/usr/bin/terminator'):
        terminal = 'terminator'
    elif os.path.exists('/usr/bin/tilix'):
        terminal = 'tilix'
    elif os.path.exists('/usr/bin/urxvt'):
        terminal = 'urxvt'
    elif os.path.exists('/usr/bin/roxterm'):
        terminal = 'roxterm'
    elif os.path.exists('/usr/bin/lxterminal'):
        terminal = 'lxterminal'
    elif os.path.exists('/usr/bin/st'):
        terminal = 'st'
    return terminal
        
def FileActionResults(file):
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
                on_enter=RunScriptAction(get_default_terminal(), file)
            )
        ]

class BalooIndexExtension(Extension):

    def __init__(self):
        super(BalooIndexExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []
        if not event.get_argument():
            return RenderResultListAction([ExtensionResultItem(icon='images/icon.png',
                                                               name='bs <query>',
                                                               on_enter=HideWindowAction())])
        # Get the results from baloo search
        result = subprocess.run(['baloosearch', '-l', '15', event.get_argument()], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        results = result.stdout.decode('utf-8').split('\n')
        for i, result in enumerate(results[:9] if len(results) > 10 else results[:10]):
            if not result:
                continue
            
            icon = get_icon_filename(result, 48)
            name = result.split('/')[-1]
            description = result
            if not os.path.exists(result):
                icon = folder_important_icon
                logger.error('File not found: %s' % result)
            items.append(ExtensionResultItem(icon=icon,
                                                name=name,
                                                description=description,
                                                on_enter=RenderResultListAction(FileActionResults(result))))

        # If no results found show a message
        if not items:
            items.append(ExtensionResultItem(icon=gnome_saved_search_icon,
                                             name='No results found',
                                             on_enter=HideWindowAction()))
        if len(results) > 10:
            items.append(ExtensionResultItem(icon=gnome_saved_search_icon,
                                             name='Please refine your search',
                                             description='Too many results'))

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        data = event.get_data()
        return RenderResultListAction([ExtensionResultItem(icon='images/icon.png',
                                                           name=data['new_name'],
                                                           on_enter=HideWindowAction())])


if __name__ == '__main__':
    BalooIndexExtension().run()
