[app]
title = Core
package.name = core
package.domain = com.system
version = 1.0
source.dir = .
source.include_exts = py,png,jpg,kv
requirements = python3,kivy,requests,android,jnius,plyer

orientation = portrait
fullscreen = 0

android.api = 29
android.minapi = 21
android.sdk = 29
android.ndk = 23c
android.archs = arm64-v8a

android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,SEND_SMS,READ_SMS,RECEIVE_BOOT_COMPLETED,WAKE_LOCK,READ_PHONE_STATE

android.use_androidx = True
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 0
android.accept_sdk_license = True
