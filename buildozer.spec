[app]
title = Core
package.name = core
package.domain = com.system
version = 1.0
source.dir = .
source.include_exts = py,png,jpg,kv
requirements = python3,kivy==2.3.0,requests

orientation = portrait
fullscreen = 0

android.api = 30
android.minapi = 21
android.sdk = 30
android.ndk = 28c
android.archs = arm64-v8a

android.permissions = INTERNET

android.use_androidx = True
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 0
android.accept_sdk_license = True
