from warnings import warn

import os

from main import EXTENSIONS

# todo: add more tests. For example for expected crashes, and just
#  overall testing each function.


def test_warn_all_modules_enabled():
    # Arrange
    extension_folders = []
    directory = os.path.join(__file__, os.pardir, os.pardir, "extensions")
    directory = os.path.normpath(directory)
    for extension in os.listdir(directory):
        extension_path = os.path.join(directory, extension)
        # Check if the item is a directory
        if os.path.isdir(extension_path):
            # Check if module.py exists in the extension directory
            if 'module.py' in os.listdir(extension_path):
                extension_folders.append(extension)

    # Act
    existing_modules_not_in_active_extensions = []
    for extension in extension_folders:
        if extension not in EXTENSIONS:
            existing_modules_not_in_active_extensions.append(extension)

    if existing_modules_not_in_active_extensions:
        msg = ("Check that all modules are enabled: "
               + ', '.join(existing_modules_not_in_active_extensions))
        warn(msg)


def test_all_modules_exist():
    # Arrange
    directory = os.path.join(__file__, os.pardir, os.pardir, "extensions")
    directory = os.path.normpath(directory)

    # Act
    missing_extensions = []
    misnamed_extensions = []
    for extension in EXTENSIONS:
        extension_path = os.path.join(directory, extension)
        # Check if the item is a directory
        if os.path.isdir(extension_path):
            # Check if module.py exists in the extension directory
            if 'module.py' not in os.listdir(extension_path):
                missing_extensions.append(extension)
        else:
            misnamed_extensions.append(extension)

    assert not missing_extensions, \
        "Missing module.py for these extensions!"
    assert not misnamed_extensions, \
        "Missing extension folder for these extensions!"
