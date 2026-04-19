# 🛠️ Wan2GP Finetune Creator Plugin

Create finetunes with minimal effort according to WanGP specifications.

A powerful, lightweight Gradio plugin for Wan2GP that streamlines the creation of finetuning JSON definitions. 
Designed specifically for local offline workflows, it completely bypasses Gradio's slow browser upload mechanics and provides a real-time, editable preview of your configuration.

**Key Features:**
* **Native Windows File Explorer:** Say goodbye to the dreaded "Uploading 1 file..." freeze. Select massive `.gguf` or `.safetensors` checkpoints instantly using Python's native `tkinter` dialog. Zero upload time, zero browser crashes.
* **Smart Relative Paths:** Automatically cleans absolute Windows paths and outputs the correct relative paths for the `ckpts/` directory required by Wan2GP.
* **Auto-Naming:** Automatically extracts and applies the finetune name based on your selected base model.
* **Live & Editable JSON Preview:** Watch your JSON build in real-time as you adjust parameters. The preview box is fully editable, allowing you to manually tweak keys and values before hitting save.
* **Compact Single-Row UI:** Highly optimized, space-saving layout without unnecessary scrollbars or stretched input fields.
* 

<img width="1833" height="922" alt="finetune_creator" src="https://github.com/user-attachments/assets/4f3be54f-43f1-4744-9ac7-ad19208a418f" />
