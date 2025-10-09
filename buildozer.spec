[app]
title = Family Gathering App
package.name = familyapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

[android]
android.sdk = 33
android.ndk = 25b
android.api = 33
android.minapi = 21
