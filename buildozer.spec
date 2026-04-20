[app]
title = Ghost C2
package.name = ghostc2
package.domain = org.zain
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0
requirements = python3, kivy==2.3.0, requests
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, CAMERA, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, ACCESS_FINE_LOCATION, RECORD_AUDIO
android.api = 33
android.minapi = 21
android.ndk = 25b
android.skip_update = False
android.accept_sdk_license = True
android.archs = arm64-v8a
[buildozer]
log_level = 2
warn_on_root = 1 
