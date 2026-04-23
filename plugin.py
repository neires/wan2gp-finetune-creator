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
        self.version = "1.0.4"
        self._is_active = False

        # --- ARCHITECTURE MAPPING ---
        # Display Name (UI) -> Actual JSON Name (Backend)
        self.arch_mapping = {
            "ltx2_22B": "ltx2_22B",
            "ltx-2-19b": "ltx-2-19b",
            "hunyuan_video": "hunyuan_video",
            "HunyuanVideo1.5": "HunyuanVideo1.5",
            "flux": "flux",
            "qwen": "qwen",
            "Z-Image": "Z-Image",
            "Wan 2.1 - t2v-1-3B": "t2v-1-3B",
            "Wan 2.1 - t2v-14B": "t2v-14B",
            "Wan 2.1 - i2v-14B": "i2v-14B",
            "Wan 2.2 - t2v_2_2": "t2v_2_2",
            "Wan 2.2 - i2v_2_2": "i2v_2_2",
            "Wan 2.2 - ti2v_2_2": "ti2v_2_2",
            "Wan 2.2 - vace_14B_2_2": "vace_14B_2_2"
        }

    def setup_ui(self):
        self.request_global("refresh_model_defs")
        
        self.add_tab(
            tab_id="finetune_creator",
            label="Finetune Creator",
            component_constructor=self.create_ui,
        )

    def get_finetune_list(self):
        """Liest alle JSON Dateien aus dem finetunes Ordner."""
        os.makedirs("finetunes", exist_ok=True)
        return [f for f in os.listdir("finetunes") if f.endswith(".json")]

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
        if not file_path: return ""
        return file_path

    # --- Helper function for clean, relative paths ---
    def clean_local_path(self, full_path):
        if not full_path: return ""
        clean_path = full_path.replace("\\", "/")
        if "/ckpts/" in clean_path:
            return clean_path.split("/ckpts/")[-1]
        elif "ckpts/" in clean_path:
            return clean_path.split("ckpts/")[-1]
        else:
            return os.path.basename(clean_path)

    # --- Central JSON Builder Function ---
    def build_json_dict(self, ui_base_arch, name, m_choice, m_url, m_path, m_url_2, m_path_2, te_choice, te_url, te_path, prompt_text, steps, length, res):
        display_name = name if name else "..."
        real_base_arch = self.arch_mapping.get(ui_base_arch, ui_base_arch)

        cleaned_m_path = self.clean_local_path(m_path) if m_path else ""
        cleaned_m_path_2 = self.clean_local_path(m_path_2) if m_path_2 else ""
        cleaned_te_path = self.clean_local_path(te_path) if te_path else ""

        if m_choice == "URL" and m_url:
            urls = [u.strip() for u in m_url.split('\n') if u.strip()]
        else:
            urls = [cleaned_m_path] if cleaned_m_path else []
        
        model_data = {
            "name": display_name,
            "architecture": real_base_arch,
            "description": f"Finetune generated via WanGP Finetune Creator",
            "URLs": urls
        }

        if "_2_2" in real_base_arch.lower():
            if m_choice == "URL" and m_url_2:
                urls2 = [u.strip() for u in m_url_2.split('\n') if u.strip()]
            else:
                urls2 = [cleaned_m_path_2] if cleaned_m_path_2 else []
            if urls2:
                model_data["URLs2"] = urls2

        if m_choice == "URL":
            model_data["preload_URLs"] = []

        if te_choice == "URL" and te_url:
            model_data["text_encoder_URLs"] = [u.strip() for u in te_url.split('\n') if u.strip()]
        elif te_choice == "Local" and cleaned_te_path:
            model_data["text_encoder_URLs"] = [cleaned_te_path]

        if "ltx2" in real_base_arch.lower() or "ltx-2" in real_base_arch.lower():
            model_data["preload_URLs"] = real_base_arch
            model_data["ltx2_pipeline"] = "distilled"

        res_mapping = {
            "1080p 16:9": "1920x1088",
            "720p 16:9": "1280x720",
            "540p 16:9": "960x544",
            "480p 16:9": "832x480"
        }
        json_res = res_mapping.get(res, res) # Fallback to the raw res if it's a custom one

        finetune_def = {
            "model": model_data, 
            "prompt": prompt_text.strip() if prompt_text else "", 
            "num_inference_steps": int(steps) if steps else 8, 
            "resolution": json_res
        }

        image_models = ["flux", "qwen", "z-image"]
        if real_base_arch.lower() not in image_models:
            finetune_def["video_length"] = int(length) if length else 241

        if "_2_2" in real_base_arch.lower():
            finetune_def["guidance_phases"] = 2
            finetune_def["switch_threshold"] = 900
            finetune_def["flow_shift"] = 5
            finetune_def["multi_prompts_gen_type"] = 2

        return finetune_def

    def update_preview(self, *args):
        preview_dict = self.build_json_dict(*args)
        return json.dumps(preview_dict, indent=4)

    # --- Button Handlers ---
    def handle_model_browse(self, base_arch, current_name, m_choice, m_url, m_path, m_url_2, m_path_2, te_choice, te_url, te_path, prompt_text, steps, length, res):
        path = self.open_windows_file_dialog()
        if not path: return gr.update(), gr.update(), gr.update()
        new_name = os.path.splitext(os.path.basename(path))[0]
        preview_dict = self.build_json_dict(base_arch, new_name, m_choice, m_url, path, m_url_2, m_path_2, te_choice, te_url, te_path, prompt_text, steps, length, res)
        return path, new_name, json.dumps(preview_dict, indent=4)

    def handle_model_2_browse(self, base_arch, current_name, m_choice, m_url, m_path, m_url_2, m_path_2, te_choice, te_url, te_path, prompt_text, steps, length, res):
        path = self.open_windows_file_dialog()
        if not path: return gr.update(), gr.update()
        preview_dict = self.build_json_dict(base_arch, current_name, m_choice, m_url, m_path, m_url_2, path, te_choice, te_url, te_path, prompt_text, steps, length, res)
        return path, json.dumps(preview_dict, indent=4)

    def handle_te_browse(self, base_arch, current_name, m_choice, m_url, m_path, m_url_2, m_path_2, te_choice, te_url, te_path, prompt_text, steps, length, res):
        path = self.open_windows_file_dialog()
        if not path: return gr.update(), gr.update(), gr.update()
        if not current_name:
            new_name = os.path.splitext(os.path.basename(path))[0]
            preview_dict = self.build_json_dict(base_arch, new_name, m_choice, m_url, m_path, m_url_2, m_path_2, te_choice, te_url, path, prompt_text, steps, length, res)
            return path, new_name, json.dumps(preview_dict, indent=4)
        preview_dict = self.build_json_dict(base_arch, current_name, m_choice, m_url, m_path, m_url_2, m_path_2, te_choice, te_url, path, prompt_text, steps, length, res)
        return path, gr.update(), json.dumps(preview_dict, indent=4)

    def save_finetune_json(self, name, current_json_string):
        if not name: return "❌ Error: Finetune Name is required to save.", gr.update()
        save_path = os.path.join("finetunes", f"{name.replace(' ', '_').lower()}.json")
        os.makedirs("finetunes", exist_ok=True)
        try:
            parsed_data = json.loads(current_json_string)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=4)
            if hasattr(self, "refresh_model_defs"):
                self.refresh_model_defs()
            new_list = self.get_finetune_list()
            return f"✅ Saved successfully to: {save_path}", gr.update(choices=new_list, value=f"{name.replace(' ', '_').lower()}.json")
        except Exception as e:
            return f"❌ Error saving file: {str(e)}", gr.update()

    def delete_finetune(self, filename):
        if not filename: return "❌ Select a finetune to delete.", gr.update()
        filepath = os.path.join("finetunes", filename)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            if hasattr(self, "refresh_model_defs"):
                self.refresh_model_defs()
            new_list = self.get_finetune_list()
            return f"✅ Deleted successfully: {filename}", gr.update(choices=new_list, value=None)
        except Exception as e:
            return f"❌ Error deleting file: {str(e)}", gr.update()

    def edit_finetune(self, filename):
        if not filename:
            return [gr.update()] * 15 + ["❌ Please select a finetune to edit."]
        
        filepath = os.path.join("finetunes", filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            ft_name = data.get("model", {}).get("name", filename.replace(".json", ""))
            raw_arch = data.get("model", {}).get("architecture", "ltx2_22B")
            
            # Reverse Lookup for UI Architecture Name (Fallback to raw_arch if custom)
            ui_arch = raw_arch
            for k, v in self.arch_mapping.items():
                if v == raw_arch:
                    ui_arch = k
                    break
                    
            urls = data.get("model", {}).get("URLs", [])
            m_choice = "URL" if (urls and urls[0].startswith("http")) else "Local"
            m_url = "\n".join(urls) if m_choice == "URL" else ""
            m_path = urls[0] if (m_choice == "Local" and urls) else ""
            
            urls2 = data.get("model", {}).get("URLs2", [])
            m_url_2 = "\n".join(urls2) if m_choice == "URL" else "" 
            m_path_2 = urls2[0] if (m_choice == "Local" and urls2) else ""
            
            te_urls = data.get("model", {}).get("text_encoder_URLs", [])
            te_choice = "URL" if (te_urls and te_urls[0].startswith("http")) else "Local"
            te_url = "\n".join(te_urls) if te_choice == "URL" else ""
            te_path = te_urls[0] if (te_choice == "Local" and te_urls) else ""
            
            prompt = data.get("prompt", "")
            steps = data.get("num_inference_steps", 8)
            length = data.get("video_length", 241)
            
            # Reverse Lookup for UI Resolution (Fallback to raw resolution if custom)
            res_val = data.get("resolution", "1280x720")
            ui_res = res_val 
            res_mapping = {"1080p 16:9": "1920x1088", "720p 16:9": "1280x720", "540p 16:9": "960x544", "480p 16:9": "832x480"}
            for k, v in res_mapping.items():
                if v == res_val:
                    ui_res = k
                    break
                    
            json_str = json.dumps(data, indent=4)
            
            return (
                ft_name, ui_arch, 
                m_choice, m_url, m_path, 
                m_url_2, m_path_2, 
                te_choice, te_url, te_path, 
                prompt, steps, length, ui_res, 
                json_str, f"✅ Loaded {filename} for editing."
            )
        except Exception as e:
            return [gr.update()] * 15 + [f"❌ Error loading: {str(e)}"]

    def create_ui(self):
        gr.HTML("""
        <style>
        .theme-aware-bg { background-color: var(--background-fill-secondary); padding: 20px; border-radius: 10px; border: 1px solid var(--border-color-primary); }
        .browse-btn { max-width: 120px !important; min-width: 120px !important; }
        .code-preview-box { min-height: 320px !important; }
        .code-preview-box button[aria-label="Download"], .code-preview-box button[title="Download"], .code-preview-box a[download] { display: none !important; }
        .inline-field label { display: flex !important; flex-direction: row !important; align-items: center !important; }
        .inline-field label > span { margin-bottom: 0 !important; margin-right: 15px !important; white-space: nowrap !important; flex-shrink: 0 !important; }
        .inline-field label > :nth-child(2) { flex-grow: 1 !important; width: 100% !important; }
        </style>
        """)

        with gr.Column(elem_classes="theme-aware-bg"):
            gr.HTML(f"""
            <div style="display: flex; align-items: baseline; gap: 15px; margin-bottom: 15px;">
                <h3 style="margin: 0;">🛠️ {self.name}</h3>
                <span style="font-size: 14px; opacity: 0.8;">{self.description}</span>
            </div>
            """)
            
            with gr.Row():
                self.finetune_name = gr.Textbox(label="Finetune Name", placeholder="e.g. LTX-2 2.3 Distilled 22B heretic", scale=3)
                
                # FIX: allow_custom_value=True verhindert Abstürze bei unbekannten alten Architekturen!
                self.base_arch = gr.Dropdown(
                    choices=list(self.arch_mapping.keys()), 
                    label="Base Architecture", 
                    value="ltx2_22B", 
                    scale=2,
                    allow_custom_value=True
                )
                
                self.steps = gr.Number(label="Inference Steps", value=8, precision=0, scale=1)
                self.length = gr.Number(label="Video Length", value=241, precision=0, scale=1)
                
                # FIX: allow_custom_value=True für den Fall, dass alte JSONs komische Auflösungen haben!
                self.resolution = gr.Dropdown(
                    choices=["1080p 16:9", "720p 16:9", "540p 16:9", "480p 16:9"], 
                    label="Resolution", 
                    value="720p 16:9", 
                    scale=1,
                    allow_custom_value=True
                )

            with gr.Group():
                gr.Markdown("#### Model Configuration")
                with gr.Row():
                    with gr.Column(scale=1, min_width=340):
                        self.model_choice = gr.Radio(choices=["URL", "Local"], value="Local", label="Model Source")
                    with gr.Column(scale=5):
                        self.model_url = gr.Textbox(label="Model URL (High Noise)", placeholder="https://huggingface.co/...\nhttps://huggingface.co/...", lines=2, max_lines=5, visible=False)
                        with gr.Row(visible=True) as self.model_local_row:
                            self.model_local_path = gr.Textbox(label="Local Path (High Noise)", placeholder="C:\\path\\to\\model_high.gguf", scale=4)
                            self.model_browse_btn = gr.Button("📂 Browse...", elem_classes="browse-btn", scale=1)
                        
                        with gr.Group(visible=False) as self.wan22_extra_group:
                            self.model_url_2 = gr.Textbox(label="Model URL 2 (Low Noise)", placeholder="https://huggingface.co/...\nhttps://huggingface.co/...", lines=2, max_lines=5, visible=False)
                            with gr.Row(visible=True) as self.model_local_row_2:
                                self.model_local_path_2 = gr.Textbox(label="Local Path 2 (Low Noise)", placeholder="C:\\path\\to\\model_low.gguf", scale=4)
                                self.model_browse_btn_2 = gr.Button("📂 Browse...", elem_classes="browse-btn", scale=1)

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

            with gr.Row():
                self.prompt_input = gr.Textbox(label="Prompt", placeholder="Enter your prompt here...\nAnd on the next line...", lines=2, max_lines=10, scale=4)
                
                with gr.Column(scale=3):
                    with gr.Row():
                        self.finetune_list = gr.Dropdown(choices=self.get_finetune_list(), label="Saved Finetunes", scale=5)
                        self.refresh_ft_btn = gr.Button("🔄", scale=1, min_width=40)
                    with gr.Row():
                        self.edit_btn = gr.Button("✏️ Edit", scale=1)
                        self.delete_btn = gr.Button("🗑️ Delete", variant="stop", scale=1)

            with gr.Row():
                self.status_text = gr.Textbox(label="Status", interactive=False, elem_classes="inline-field", scale=4)
                self.generate_btn = gr.Button("💾 Save JSON File", variant="primary", scale=1)
            
            self.json_output = gr.Code(language="json", label="Live JSON Preview (Editable before saving)", interactive=True, elem_classes="code-preview-box")

        # --- Event Listeners ---
        self.base_arch.change(fn=lambda arch: gr.update(visible="Wan 2.2" in str(arch)), inputs=self.base_arch, outputs=self.wan22_extra_group)
        self.model_choice.change(fn=lambda c: (gr.update(visible=c=="URL"), gr.update(visible=c=="Local"), gr.update(visible=c=="URL"), gr.update(visible=c=="Local")), inputs=self.model_choice, outputs=[self.model_url, self.model_local_row, self.model_url_2, self.model_local_row_2])
        self.te_choice.change(fn=lambda c: (gr.update(visible=c=="URL"), gr.update(visible=c=="Local")), inputs=self.te_choice, outputs=[self.te_url, self.te_local_row])
        
        all_inputs = [
            self.base_arch, self.finetune_name, 
            self.model_choice, self.model_url, self.model_local_path, self.model_url_2, self.model_local_path_2,
            self.te_choice, self.te_url, self.te_local_path, 
            self.prompt_input, self.steps, self.length, self.resolution
        ]

        for component in all_inputs:
            component.change(fn=self.update_preview, inputs=all_inputs, outputs=self.json_output)

        self.model_browse_btn.click(fn=self.handle_model_browse, inputs=all_inputs, outputs=[self.model_local_path, self.finetune_name, self.json_output])
        self.model_browse_btn_2.click(fn=self.handle_model_2_browse, inputs=all_inputs, outputs=[self.model_local_path_2, self.json_output])
        self.te_browse_btn.click(fn=self.handle_te_browse, inputs=all_inputs, outputs=[self.te_local_path, self.finetune_name, self.json_output])

        self.generate_btn.click(fn=self.save_finetune_json, inputs=[self.finetune_name, self.json_output], outputs=[self.status_text, self.finetune_list])
        
        # --- Management Buttons ---
        self.refresh_ft_btn.click(fn=lambda: gr.update(choices=self.get_finetune_list()), outputs=self.finetune_list)
        self.delete_btn.click(fn=self.delete_finetune, inputs=self.finetune_list, outputs=[self.status_text, self.finetune_list])
        
        self.edit_btn.click(
            fn=self.edit_finetune,
            inputs=[self.finetune_list],
            outputs=[
                self.finetune_name, self.base_arch,
                self.model_choice, self.model_url, self.model_local_path, self.model_url_2, self.model_local_path_2,
                self.te_choice, self.te_url, self.te_local_path,
                self.prompt_input, self.steps, self.length, self.resolution,
                self.json_output, self.status_text
            ]
        )

    def on_tab_select(self, state: dict) -> None:
        self._is_active = True

    def on_tab_deselect(self, state: dict) -> None:
        if not self._is_active: return
        self._is_active = False
