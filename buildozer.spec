[app]
title = GhostApp
package.name = ghostapp
package.domain = org.ghost
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy==2.3.0,requests
orientation = portrait
fullscreen = 0
android.archs = armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
