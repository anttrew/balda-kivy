[app]
title = Balda
package.name = balda
package.domain = org.familygames
source.dir = .
source.include_exts = py,txt,png,jpg,jpeg,kv,json
version = 0.1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0

# Debug APK для ручной установки. Для Google Play позже нужен release/AAB и подпись.
android.api = 35
android.minapi = 23
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
