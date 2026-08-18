[app]
title = Core
package.name = core
package.domain = com.system
version = 1.0
source.dir = .
source.include_exts = py,png,jpg
requirements = python3,kivy,requests
android.api = 30
android.minapi = 21
android.sdk = 30
android.ndk = 28c
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,SEND_SMS,READ_SMS,RECEIVE_BOOT_COMPLETED,WAKE_LOCK,READ_PHONE_STATE
fullscreen = 0
orientation = portrait
android.orientation = portrait
android.debug = True
android.use_androidx = True
android.add_src = 
    <receiver android:name=".BootReceiver" android:enabled="true" android:exported="true">
        <intent-filter>
            <action android:name="android.intent.action.BOOT_COMPLETED" />
            <action android:name="android.intent.action.QUICKBOOT_POWERON" />
        </intent-filter>
    </receiver>
