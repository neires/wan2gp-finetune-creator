English Version
# 🛠️ wan2gp-finetune-creator Plugin

What it is: A lightweight, highly optimized Gradio plugin for WanGP. It is designed to effortlessly generate, edit, and manage JSON configuration files for local model fine-tuning directly within the UI.

What it can do:

- Zero-Wait Local Browsing: Bypasses Gradio's notoriously slow browser upload mechanics. It uses native Windows file dialogs to instantly select massive .gguf or .safetensors checkpoints.
- Live Editable Preview: Generates a real-time JSON preview as you tweak parameters. The code box is fully editable for quick manual overrides before saving.
- Smart Architecture Support: Fully supports Wan 2.1 and Wan 2.2 models, automatically handling complex setups (like the High/Low-Noise dual-model requirement for Wan 2.2).
- Automated Path Formatting: Automatically cleans absolute Windows paths and converts them to the relative ckpts/ paths required by WanGP.
- Full File Management: Built-in tools to seamlessly load, edit, or delete existing finetune JSON files from your directory.
- No Restarts Required: Communicates directly with the WanGP backend to auto-refresh the main model dropdown whenever a finetune is saved or deleted.

<img width="1819" height="954" alt="finetune_creator" src="https://github.com/user-attachments/assets/540b2532-e820-442f-ada6-7423657a520e" />

---
Deutsche Version
# 🛠️ wan2gp-finetune-creator Plugin

Was es ist: Ein schlankes, hochoptimiertes Gradio-Plugin für WanGP. Es wurde entwickelt, um JSON-Konfigurationsdateien für das lokale Fine-Tuning von Modellen mühelos und direkt in der Benutzeroberfläche zu erstellen, zu bearbeiten und zu verwalten.

Was es kann:

- Lokale Dateiauswahl ohne Wartezeit: Umgeht den extrem langsamen Browser-Upload von Gradio komplett. Dank nativer Windows-Dateidialoge lassen sich riesige .gguf- oder .safetensors-Modelle in Sekundenschnelle auswählen.
- Editierbare Live-Vorschau: Generiert in Echtzeit eine JSON-Vorschau deiner Einstellungen. Die Code-Box ist vollständig editierbar, um vor dem Speichern noch schnelle manuelle Anpassungen vorzunehmen.
- Smarte Architektur-Erkennung: Bietet volle Unterstützung für Wan 2.1 und Wan 2.2 Modelle und richtet komplexe Konfigurationen (wie das Dual-Modell-Setup für Wan 2.2 High/Low-Noise) vollautomatisch ein.
- Automatische Pfad-Korrektur: Wandelt absolute Windows-Pfade automatisch in die von WanGP benötigten relativen ckpts/-Pfade um.
- Komplette Dateiverwaltung: Integrierte Funktionen zum nahtlosen Laden, Bearbeiten und Löschen bestehender Finetune-Dateien.
- Keine Neustarts nötig: Kommuniziert direkt mit dem WanGP-Backend und aktualisiert die Modell-Auswahlliste im Haupt-Tab vollautomatisch, sobald ein Finetune gespeichert oder gelöscht wird.

<img width="1819" height="954" alt="finetune_creator" src="https://github.com/user-attachments/assets/540b2532-e820-442f-ada6-7423657a520e" />

