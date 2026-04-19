import gradio as gr
import json
import os
import tkinter as tk
from tkinter import filedialog
from shared.utils.plugins import WAN2GPPlugin

class FinetuneMakerPlugin(WAN2GPPlugin):
    def __init__(self):
        super().__init__()
        self.name, self.description = "Finetune Creator", "Create finetunes with minimal effort according to WanGP specifications."
        self.version = "1.0.0"
        self._is_active = False

    def setup_ui(self):
        self.add_tab(
            tab_id="finetune_creator",
            label="Finetune Creator",
            component_constructor=self.create_ui,
        )

    def open_windows_file_dialog(self):
        """Opens the native Windows dialog directly in the ckpts folder and returns the path."""
        root = tk.Tk()
        root.attributes("-topmost", True) 
        root.withdraw() 
        
        start_dir = os.path.abspath("ckpts")
        if not os.path.exists(start_dir):
            start_dir = os.getcwd()

        file_path = filedialog.askopenfilename(
            title="Select Model File",
            initialdir=start_dir, 
            filetypes=[
                ("Model Files", "*.safetensors *.bin *.pt *.gguf"),
                ("All Files", "*.*")
            ]
        )
        
        root.destroy()
        
        if not file_path:
            return ""
            
        return file_path

    # --- Helper function for clean, relative paths ---
    def clean_local_path(self, full_path):
        """Strips everything before and including 'ckpts/'."""
        if not full_path: return ""
        clean_path = full_path.replace("\\", "/")
        
        if "/ckpts/" in clean_path:
            return clean_path.split("/ckpts/")[-1]
        elif "ckpts/" in clean_path:
            return clean_path.split("ckpts/")[-1]
        else:
            return os.path.basename(clean_path)

    # --- Central JSON Builder Function ---
    def build_json_dict(self, base_arch, name, m_choice, m_url, m_path, te_choice, te_url, te_path, prompt_text, steps, length, res):
        display_name = name if name else "..."

        cleaned_m_path = self.clean_local_path(m_path) if m_path else ""
        cleaned_te_path = self.clean_local_path(te_path) if te_path else ""

        # Multiline URL handling for Main Model
        if m_choice == "URL" and m_url:
            urls = [u.strip() for u in m_url.split('\n') if u.strip()]
        else:
            urls = [cleaned_m_path] if cleaned_m_path else []
        
        model_data = {
            "name": display_name,
            "architecture": base_arch,
            "description": f"Finetune generated via WanGP Finetune Creator",
            "URLs": urls
        }

        # Handling for empty preload_URLs when URL is selected
        if m_choice == "URL":
            model_data["preload_URLs"] = []

        # Multiline URL handling for Text Encoder
        if te_choice == "URL" and te_url:
            model_data["text_encoder_URLs"] = [u.strip() for u in te_url.split('\n') if u.strip()]
        elif te_choice == "Local" and cleaned_te_path:
            model_data["text_encoder_URLs"] = [cleaned_te_path]

        if "ltx2" in base_arch.lower() or "ltx-2" in base_arch.lower():
            model_data["preload_URLs"] = base_arch
            model_data["ltx2_pipeline"] = "distilled"

        # Mapping for Resolution
        res_mapping = {
            "1080p 16:9": "1920x1088",
            "720p 16:9": "1280x720",
            "540p 16:9": "960x544",
            "480p 16:9": "832x480"
        }
        json_res = res_mapping.get(res, "1280x720")

        finetune_def = {
            "model": model_data, 
            # Nutzt einen leeren String, falls kein Prompt eingegeben wurde
            "prompt": prompt_text.strip() if prompt_text else "", 
            "num_inference_steps": int(steps) if steps else 8, 
            "video_length": int(length) if length else 241, 
            "resolution": json_res
        }
        return finetune_def

    def update_preview(self, *args):
        """Triggered on EVERY UI change and returns a formatted JSON string."""
        preview_dict = self.build_json_dict(*args)
        return json.dumps(preview_dict, indent=4)

    # --- Auto-Name & Browse Functions ---
    def handle_model_browse(self, base_arch, current_name, m_choice, m_url, m_path, te_choice, te_url, te_path, prompt_text, steps, length, res):
        path = self.open_windows_file_dialog()
        if not path:
            return gr.update(), gr.update(), gr.update()
        
        new_name = os.path.splitext(os.path.basename(path))[0]
        preview_dict = self.build_json_dict(base_arch, new_name, m_choice, m_url, path, te_choice, te_url, te_path, prompt_text, steps, length, res)
        return path, new_name, json.dumps(preview_dict, indent=4)

    def handle_te_browse(self, base_arch, current_name, m_choice, m_url, m_path, te_choice, te_url, te_path, prompt_text, steps, length, res):
        path = self.open_windows_file_dialog()
        if not path:
            return gr.update(), gr.update(), gr.update()
        
        if not current_name:
            new_name = os.path.splitext(os.path.basename(path))[0]
            preview_dict = self.build_json_dict(base_arch, new_name, m_choice, m_url, m_path, te_choice, te_url, path, prompt_text, steps, length, res)
            return path, new_name, json.dumps(preview_dict, indent=4)
            
        preview_dict = self.build_json_dict(base_arch, current_name, m_choice, m_url, m_path, te_choice, te_url, path, prompt_text, steps, length, res)
        return path, gr.update(), json.dumps(preview_dict, indent=4)

    def create_ui(self):
        gr.HTML("""
        <style>
        .theme-aware-bg {
            background-color: var(--background-fill-secondary);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid var(--border-color-primary);
        }
        .browse-btn {
            max-width: 120px !important;
            min-width: 120px !important;
        }
        .code-preview-box {
            min-height: 320px !important;
        }
        /* Versteckt den fest programmierten Download-Button von Gradio, lässt Copy aber da! */
        .code-preview-box button[aria-label="Download"],
        .code-preview-box button[title="Download"],
        .code-preview-box a[download] {
            display: none !important;
        }
        /* Flexbox-Magic für saubere Inline-Labels */
        .inline-field label {
            display: flex !important;
            flex-direction: row !important;
            align-items: flex-start !important;
        }
        .inline-field label > span {
            margin-bottom: 0 !important;
            margin-right: 15px !important;
            margin-top: 6px !important;
            white-space: nowrap !important;
            flex-shrink: 0 !important;
        }
        .inline-field label > :nth-child(2) {
            flex-grow: 1 !important;
            width: 100% !important;
        }
        </style>
        """)

        with gr.Column(elem_classes="theme-aware-bg"):
            # --- Header and Description ---
            gr.HTML(f"""
            <div style="display: flex; align-items: baseline; gap: 15px; margin-bottom: 15px;">
                <h3 style="margin: 0;">🛠️ {self.name}</h3>
                <span style="font-size: 14px; opacity: 0.8;">{self.description}</span>
            </div>
            """)
            
            # --- TOP-LAYOUT ---
            with gr.Row():
                self.finetune_name = gr.Textbox(label="Finetune Name", placeholder="e.g. LTX-2 2.3 Distilled 22B heretic", scale=3)
                self.base_arch = gr.Dropdown(
                    choices=["ltx2_22B", "ltx-2-19b", "hunyuan_video", "HunyuanVideo1.5", "flux", "wan2.1", "wan2.2", "qwen", "Z-Image"], 
                    label="Base Architecture", 
                    value="ltx2_22B",
                    scale=2
                )
                self.steps = gr.Number(label="Inference Steps", value=8, precision=0, scale=1)
                self.length = gr.Number(label="Video Length", value=241, precision=0, scale=1)
                
                # --- RESOLUTION DROPDOWN ---
                self.resolution = gr.Dropdown(
                    choices=["1080p 16:9", "720p 16:9", "540p 16:9", "480p 16:9"],
                    label="Resolution", 
                    value="720p 16:9", 
                    scale=1
                )

            # --- COMPACT Model Configuration ---
            with gr.Group():
                gr.Markdown("#### Model Configuration")
                with gr.Row():
                    with gr.Column(scale=1, min_width=340):
                        self.model_choice = gr.Radio(choices=["URL", "Local"], value="Local", label="Model Source")
                    with gr.Column(scale=5):
                        self.model_url = gr.Textbox(label="Model URL", placeholder="https://huggingface.co/...\nhttps://huggingface.co/...", lines=2, max_lines=5, visible=False)
                        with gr.Row(visible=True) as self.model_local_row:
                            self.model_local_path = gr.Textbox(label="Local Path", placeholder="C:\\path\\to\\model.gguf", scale=4)
                            self.model_browse_btn = gr.Button("📂 Browse...", elem_classes="browse-btn", scale=1)

            # --- COMPACT Text Encoder Configuration ---
            with gr.Group():
                gr.Markdown("#### Text Encoder Configuration")
                with gr.Row():
                    with gr.Column(scale=1, min_width=340):
                        self.te_choice = gr.Radio(choices=["Standard", "URL", "Local"], value="Local", label="Text Encoder Source")
                    with gr.Column(scale=5):
                        self.te_url = gr.Textbox(label="Text Encoder Download URL", placeholder="https://huggingface.co/...\nhttps://huggingface.co/...", lines=2, max_lines=5, visible=False)
                        with gr.Row(visible=True) as self.te_local_row:
                            self.te_local_path = gr.Textbox(label="Local Path", placeholder="C:\\path\\to\\encoder.safetensors", scale=4)
                            self.te_browse_btn = gr.Button("📂 Browse...", elem_classes="browse-btn", scale=1)

            # --- PROMPT CONFIGURATION (Inline CSS applied, Value removed) ---
            self.prompt_input = gr.Textbox(label="Prompt", placeholder="Enter your prompt here...\nAnd on the next line...", lines=2, max_lines=10, elem_classes="inline-field")

            self.generate_btn = gr.Button("💾 Save JSON File", variant="primary")
            
            # --- STATUS DISPLAY (Inline CSS applied) ---
            self.status_text = gr.Textbox(label="Status", interactive=False, elem_classes="inline-field")
            
            # --- PREVIEW (EDITABLE) ---
            self.json_output = gr.Code(language="json", label="Live JSON Preview (Editable before saving)", interactive=True, elem_classes="code-preview-box")

        # --- Event Listeners Setup ---
        
        self.model_choice.change(fn=lambda c: (gr.update(visible=c=="URL"), gr.update(visible=c=="Local")), inputs=self.model_choice, outputs=[self.model_url, self.model_local_row])
        self.te_choice.change(fn=lambda c: (gr.update(visible=c=="URL"), gr.update(visible=c=="Local")), inputs=self.te_choice, outputs=[self.te_url, self.te_local_row])
        
        all_inputs = [
            self.base_arch, self.finetune_name, 
            self.model_choice, self.model_url, self.model_local_path, 
            self.te_choice, self.te_url, self.te_local_path, 
            self.prompt_input, 
            self.steps, self.length, self.resolution
        ]

        for component in all_inputs:
            component.change(fn=self.update_preview, inputs=all_inputs, outputs=self.json_output)

        self.model_browse_btn.click(
            fn=self.handle_model_browse, 
            inputs=all_inputs, 
            outputs=[self.model_local_path, self.finetune_name, self.json_output]
        )
        self.te_browse_btn.click(
            fn=self.handle_te_browse, 
            inputs=all_inputs, 
            outputs=[self.te_local_path, self.finetune_name, self.json_output]
        )

        self.generate_btn.click(
            fn=self.save_finetune_json,
            inputs=[self.finetune_name, self.json_output],
            outputs=[self.status_text]
        )

    def save_finetune_json(self, name, current_json_string):
        if not name: 
            return "❌ Error: Finetune Name is required to save."

        save_path = os.path.join("finetunes", f"{name.replace(' ', '_').lower()}.json")
        os.makedirs("finetunes", exist_ok=True)
        
        try:
            parsed_data = json.loads(current_json_string)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=4)
            return f"✅ Saved successfully to: {save_path}"
        except json.JSONDecodeError as e:
            return f"❌ JSON Error: Invalid format in your manual edits! Check for missing commas or quotes. ({str(e)})"
        except Exception as e:
            return f"❌ Error saving file: {str(e)}"

    def on_tab_select(self, state: dict) -> None:
        self._is_active = True

    def on_tab_deselect(self, state: dict) -> None:
        if not self._is_active:
            return
        self._is_active = False