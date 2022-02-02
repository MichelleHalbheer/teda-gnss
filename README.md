# Terradata GNSS Converter #

## Einführung ##
Diese App bietet die Funktionalität, EMLID GNSS Daten für die Verwendung im Bernese Server zu parsen wichtige Metadaten in einer JSON Datei abzuspeichern.
Bei erstmaligem Speichern einer konvertierten Datei wird auf dem Gerät ein Ordner für die Speicherung sämtlicher konvertierter Daten abgelegt. Dieser wird wie folgt gespeichert.
`{$primary_internal_storage}/Documents/Terradata_GNSS_Parser_Exports`

## Code Dokumentation ##
Die vorliegende Applikation wurde auf Basis des Kivy packages für Python entwickelt. Sämtliche benötigten packages sind in ``requirements.txt`` festgehalten.
Die packages werden wie folgt verwendet. <br>
* `kivy`: Kivy stellt die nötigen Funktionalitäten für eine Android App zur Verfügung
* `kivymd` stellt Material Design templates für die Gestaltung einer App zur Verfügung. Erleichter die Gestaltung verglichen zu klassischem kivy

### Code Dokumente ###
* `main.py` Hauptapplikation
* `gnss_device.py` Klasse für die Verarbeitung eines EMLID GNSS Gerätes. Übernommen von Philippe Limpach.
* `forge.py` Erstellt die nötigen Exporter. Übernommen von Philippe Limpach.
* `export_handler.py` Stellt die nötigen Exporter zur Verfügung. Übernommen von Philippe Limpach.
* `file_handler.py` Erweitert GNSS Device für das Handling der Messfiles. Adaptiert von Philippe Limpach.

## APK erstellen ##
Für die Erstellung der APK wird `buildozer` benötigt. Dieser erlaubt es automatisiert eine Python Applikation in eine APK zu verpacken. `buildozer` funktioniert ausschliesslich auf Linux. Für das packaging ist unter `./virtual_machine/` eine virtuelle Maschine mit Ubuntu 20.04.3 zu finden, welche `buildozer`vorinstalliert hat. Folgende Schritte sind beim packaging zu beachten.
* Script welches die App beinhaltet muss zwingend `main.py` benannt sein.
* Im selben Ordner wie `main.py` muss ein File `buildozer.spec` abgelegts sein. Dieses spezifiziert die Informationen zur Erstellung der APK.

### buildozer.spec ###
`buildozer.spec` definiert die Spezifikationen für das packaging der Applikation. Wichtig sind insbesondere folgende Einstellungen:
__TODO__
