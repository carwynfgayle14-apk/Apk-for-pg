[app]

# (str) Title of your application
title = Password Generator

# (str) Package name (no spaces, used internally)
package.name = pwgenerator

# (str) Package domain (reverse-DNS style, must be unique-ish)
package.domain = org.zeplerish

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning
version = 1.0

# (list) Application requirements
requirements = python3,kivy

# (str) Presplash / icon - optional, add files and uncomment if you have them
# presplash.filename = %(source.dir)s/data/presplash.png
# icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
# Kivy's Clipboard and local file storage don't need special Android
# permissions on modern Android versions, so this can stay empty.
android.permissions =

# (int) Target Android API, minimum API, NDK API
android.api = 34
android.minapi = 21
android.ndk_api = 21

# (str) Android archive format built by buildozer android debug
# apk (default) is fine for testing/sideloading.

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
