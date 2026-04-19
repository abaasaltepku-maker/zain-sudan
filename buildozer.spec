[app]
# (str) Title of your application
title = GhostApp

# (str) Package name
package.name = ghostapp

# (str) Package domain (needed for android packaging)
package.domain = org.ghost

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# أضفنا توابع requests لضمان استقرار الاتصال بالشبكة
requirements = python3,kivy==2.3.0,requests,urllib3,charset-normalizer,idna,certifi

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, then skip trying to update the Android sdk
android.skip_update = False

# (bool) If True, then automatically accept SDK license
# هامة جداً لتجاوز خطأ gradlew failed
android.accept_sdk_license = True

# (str) Android architecture to build for
android.archs = armeabi-v7a

# (bool) enables Androidx support
android.enable_androidx = True

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = no, 1 = yes)
warn_on_root = 1
