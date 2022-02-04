# Terradata GNSS Converter #

## Einführung ##
Diese App bietet die Funktionalität, EMLID GNSS Daten für die Verwendung im Bernese Server zu parsen und wichtige Metadaten in einer JSON Datei abzuspeichern.
Bei erstmaligem Speichern einer konvertierten Datei wird auf dem Mobilgerät ein Ordner für die Speicherung sämtlicher konvertierter Daten abgelegt. Dieser wird wie folgt gespeichert.
```
{$primary_internal_storage}/Documents/Terradata_GNSS_Parser_Exports
```

## Code Dokumentation ##
Die vorliegende Applikation wurde auf Basis des Kivy packages für Python entwickelt. Sämtliche benötigten packages sind in ``requirements.txt`` festgehalten.
Die packages werden wie folgt verwendet. <br>
* `kivy`: Kivy stellt die nötigen Funktionalitäten für eine Android App zur Verfügung
* `kivymd` Stellt Material Design templates für die Gestaltung einer App zur Verfügung. Erleichter die Gestaltung verglichen zu klassischem kivy

### Code Files ###
* `main.py` Hauptapplikation
* `gnss_device.py` Klasse für die Verarbeitung eines EMLID GNSS Gerätes. Übernommen von Philippe Limpach.
* `forge.py` Erstellt die nötigen Exporter. Übernommen von Philippe Limpach.
* `export_handler.py` Stellt die nötigen Exporter zur Verfügung. Übernommen von Philippe Limpach.
* `file_handler.py` Erweitert GNSS Device für das Handling der Messfiles. Adaptiert von Philippe Limpach.

`teda_gnss.kv` Beinhaltet die Darstellungsangaben der Applikation. Diese ist in `kivy`s eigener Sprache geschrieben. Sämtliche Interaktiven Features (Pop Ups, etc) werden in m`main.py` definiert.

## APK erstellen ##
Für die Erstellung der APK wird `buildozer` benötigt. Dieser erlaubt es automatisiert eine Python Applikation in eine APK zu verpacken. `buildozer` funktioniert ausschliesslich auf Linux. Für das packaging ist unter `./virtual_machine/` eine virtuelle Maschine mit Ubuntu 20.04.3 zu finden, welche `buildozer`vorinstalliert hat. Folgende Schritte sind beim packaging zu beachten.
* Script welches die App beinhaltet muss zwingend `main.py` benannt sein.
* Im selben Ordner wie `main.py` muss ein File `buildozer.spec` abgelegt sein. Dieses spezifiziert die Informationen zur Erstellung der APK.

### buildozer.spec ###
`buildozer.spec` definiert die Spezifikationen für das packaging der Applikation. Wichtig sind insbesondere folgende Einstellungen:
* `source_dir`: Der Pfad in dem der Python Quellcode abgelegt ist.
* `source.include_exts`: Definiert welche Dateitypen im packaging berücksichtigt werden. Die Applikation setzt py und kv voraus. Für das Branding sind png und jpg nötig.
* `requirements`: Definiert welche packages für die Ausführung der Applikation nötig sind. Python native packages müssen nicht aufgeführt werden.
</br></br>
* `title`: Der Name der Applikation auf Android
* `presplash.filename`: Der Dateipfad für das anzeigte Bild beim Aufstarten der Applikation.
* `icon.filename`: Der Dateipfad zum Icon der Applikation auf Android

### buildozer ausführen ###
Buildozer ist ein Python package, für das Packaging von Python Applikationen als APK. Im Ordner `~/gnss_parser` ist ein virtualenv vorhanden, welches alle nötigen Packete und `buildozer` installiert hat.
Für das Ausführen des Packagings wird zunächst das virtualenv aktiviert. Anschliessend kann buildozer im Code Ordner (Ordner in dem `main.py` und `buildozer.spec` abgelegt sind) ausgeführt werden. Buildozer hat die Folgende Command-Struktur.
```
buildozer -v android _commands_ logcat
```
Das `logcat` Argument führt dazu, dass die Ausgabe der Applikation in der ausführenden Command Prompt angezeigt wird.
Folgende Kommandos werden bentötigt (anstelle von `_command_` einsetzen):
* `debug`: Kompiliert den Code aus und verpackt ihn in eine debug APK. Diese ist bereit um auf Android ausgeführt zu werden.
* `deploy`: APK wird auf das verbundene Mobilgerät übertragen. Das Gerät muss USB Debugging erlauben und für File Transfer geöffnet sein.
* `run`: Die übertragene APK wird auf dem verbundenen Mobilgerät ausgeführt.
* `release`: Die Applikation wird in eine unsignierte APK für den Release verpackt und im `./bin` Ordner abgelegt.

Die Kommandos `debug`, `deploy` und `run` können in dieser Reihenfolge kombiniert werden. Diese Eingabe wird für das Debugging normalerweise verwendet.
```
buildozer -v android debug deploy run logcat
```

Für das finale Packaging wird der folgende Command benötigt.
```
buildozer -v android release
```