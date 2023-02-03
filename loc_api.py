import os
import yaml
from PyQt5 import QtCore

import config_api

LANG = {
}


def load_lang() -> None:
    """Loads localization keys from res/lang to LANG dict"""

    global LANG
    for file in os.listdir('res/lang'):
        with open(f'res/lang/{file}', 'r', encoding='utf8') as yml:
            LANG[file[:-4]] = yaml.load(yml, Loader=yaml.CLoader)


def get_lang(scope) -> str:
    """get_lang(scope) -> str, where scope is QObject or str

    Returns text by the localization key from res/lang/__language__.yml, where __language__ is the selected language
    corresponding to the lang parameter from the config.ini file. If there is no such value, then __language__
    equates to the language corresponding to the default_lang parameter from the config.ini configuration file. If
    there is no such value either, it returns the localization key"""

    if isinstance(scope, QtCore.QObject):
        key = get_loc_key(scope)
    else:
        key = scope

    if key in LANG[config_api.CONFIG['LANGUAGE']['selectedLang']]:
        return LANG[config_api.CONFIG['LANGUAGE']['selectedLang']][key]
    elif key in LANG[config_api.CONFIG['LANGUAGE']['defaultLang']]:
        return LANG[config_api.CONFIG['LANGUAGE']['defaultLang']][key]
    return key


def get_loc_key(scope: QtCore.QObject) -> str:
    """Returns dot-separated path from first parent QObject to scope"""

    if scope.parent():
        return get_loc_key(scope.parent()) + '.' + scope.objectName()
    else:
        return scope.objectName()


def is_valid_key(key: str) -> bool:
    if any(key in lang for lang in LANG):
        return True
    return False
