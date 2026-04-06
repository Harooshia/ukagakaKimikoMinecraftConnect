"""Standalone classified courtroom UI for Kimiko judgement mode."""

from __future__ import annotations

import tkinter as tk

THEME = {
    "bg": "#0a0f14",
    "panel": "#111821",
    "accent": "#00ff9c",
    "danger": "#ff3b3b",
    "warning": "#ffaa00",
    "text": "#d3e6ff",
}


class JudgementWindow:
    def __init__(self, parent: tk.Tk, on_process, on_close) -> None:
        self.parent = parent
        self.on_process = on_process
        self.on_close = on_close
        self.always_on_top = tk.BooleanVar(value=True)
        self.last_case_input = ""

        self.window = tk.Toplevel(parent)
        self.window.title("JUDGEMENT SYSTEM")
        self.window.geometry("900x660")
        self.window.minsize(760, 560)
        self.window.configure(bg=THEME["bg"])
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self._build_layout()

    def _build_layout(self) -> None:
        root = self.window
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(2, weight=1)

        top = tk.Frame(root, bg=THEME["panel"], bd=1, relief="solid")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        top.grid_columnconfigure(1, weight=1)

        self.title_label = tk.Label(
            top,
            text="JUDGEMENT SYSTEM //--// CASE 001",
            bg=THEME["panel"],
            fg=THEME["accent"],
            font=("Consolas", 14, "bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))

        tk.Label(
            top,
            text="CLASSIFIED // COURTROOM INTERFACE",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Consolas", 10),
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))

        self.status_label = tk.Label(
            top,
            text="STATUS: ACTIVE // CLEARANCE: LEVEL 3 // VERDICT: PENDING",
            bg=THEME["panel"],
            fg=THEME["warning"],
            font=("Consolas", 10, "bold"),
        )
        self.status_label.grid(row=0, column=1, rowspan=2, sticky="e", padx=10)

        mid = tk.Frame(root, bg=THEME["bg"])
        mid.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        mid.grid_columnconfigure(0, weight=1)

        tk.Label(mid, text="CASE FILE INPUT", bg=THEME["bg"], fg=THEME["accent"], font=("Consolas", 11, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )

        self.input_box = tk.Text(
            mid,
            height=5,
            bg=THEME["panel"],
            fg=THEME["text"],
            insertbackground=THEME["accent"],
            font=("Consolas", 11),
            wrap="word",
            bd=1,
            relief="solid",
        )
        self.input_box.grid(row=1, column=0, sticky="ew")
        self.input_box.insert("1.0", "STATE YOUR CASE...")

        tk.Button(
            mid,
            text="PROCESS CASE",
            command=self._submit_case,
            bg=THEME["accent"],
            fg="#00190f",
            font=("Consolas", 10, "bold"),
            relief="flat",
            padx=10,
            pady=6,
        ).grid(row=2, column=0, sticky="e", pady=(6, 0))

        body = tk.Frame(root, bg=THEME["bg"])
        body.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 6))
        body.grid_rowconfigure(1, weight=1)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=1)

        tk.Label(body, text="VERDICT OUTPUT //--// CLASSIFIED", bg=THEME["bg"], fg=THEME["accent"], font=("Consolas", 11, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        tk.Label(body, text="CASE ARCHIVE", bg=THEME["bg"], fg=THEME["accent"], font=("Consolas", 11, "bold")).grid(
            row=0, column=1, sticky="w", pady=(0, 4), padx=(8, 0)
        )

        self.output_box = tk.Text(
            body,
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Consolas", 10),
            wrap="word",
            bd=1,
            relief="solid",
            state="disabled",
        )
        self.output_box.grid(row=1, column=0, sticky="nsew")

        self.case_list = tk.Listbox(
            body,
            bg=THEME["panel"],
            fg=THEME["text"],
            highlightthickness=1,
            highlightbackground=THEME["accent"],
            font=("Consolas", 9),
        )
        self.case_list.grid(row=1, column=1, sticky="nsew", padx=(8, 0))

        controls = tk.Frame(root, bg=THEME["panel"], bd=1, relief="solid")
        controls.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

        tk.Button(controls, text="CLEAR", command=self.clear, bg=THEME["warning"], fg="#251300", font=("Consolas", 10, "bold"), relief="flat").pack(
            side="left", padx=8, pady=8
        )
        tk.Button(controls, text="REPROCESS", command=self.reprocess, bg=THEME["accent"], fg="#00190f", font=("Consolas", 10, "bold"), relief="flat").pack(
            side="left", padx=8, pady=8
        )
        tk.Button(controls, text="COPY RESULT", command=self.copy_result, bg=THEME["panel"], fg=THEME["text"], font=("Consolas", 10, "bold"), relief="solid").pack(
            side="left", padx=8, pady=8
        )
        tk.Checkbutton(
            controls,
            text="ALWAYS ON TOP",
            variable=self.always_on_top,
            command=self._toggle_topmost,
            bg=THEME["panel"],
            fg=THEME["text"],
            selectcolor=THEME["bg"],
            activebackground=THEME["panel"],
            activeforeground=THEME["text"],
            font=("Consolas", 10),
        ).pack(side="right", padx=8)
        tk.Button(controls, text="CLOSE", command=self.close, bg=THEME["danger"], fg="white", font=("Consolas", 10, "bold"), relief="flat").pack(
            side="right", padx=8, pady=8
        )

    def _toggle_topmost(self) -> None:
        self.window.attributes("-topmost", bool(self.always_on_top.get()))

    def _submit_case(self) -> None:
        content = self.get_case_input()
        if not content:
            self.set_status("STATUS: ACTIVE // INPUT REQUIRED", color=THEME["warning"])
            return
        self.last_case_input = content
        self.on_process(content)

    def reprocess(self) -> None:
        if self.last_case_input:
            self.on_process(self.last_case_input)

    def copy_result(self) -> None:
        result = self.get_output_text()
        if not result:
            return
        self.window.clipboard_clear()
        self.window.clipboard_append(result)
        self.set_status("STATUS: ACTIVE // RESULT COPIED", color=THEME["accent"])

    def get_case_input(self) -> str:
        text = self.input_box.get("1.0", "end").strip()
        if text == "STATE YOUR CASE...":
            return ""
        return text

    def set_case_id(self, case_id: int) -> None:
        self.title_label.configure(text=f"JUDGEMENT SYSTEM //--// CASE {case_id:03d}")

    def set_status(self, text: str, color: str | None = None) -> None:
        self.status_label.configure(text=text, fg=color or THEME["warning"])

    def append_case_summary(self, summary: str) -> None:
        self.case_list.insert("end", summary)

    def set_output(self, message: str, animate: bool = True) -> None:
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")

        if not animate:
            self.output_box.insert("1.0", message)
            self.output_box.configure(state="disabled")
            return

        def write_chunk(index: int = 0) -> None:
            if index >= len(message):
                self.output_box.configure(state="disabled")
                return
            self.output_box.insert("end", message[index])
            self.output_box.see("end")
            self.window.after(4, write_chunk, index + 1)

        write_chunk()

    def get_output_text(self) -> str:
        return self.output_box.get("1.0", "end").strip()

    def clear(self) -> None:
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", "STATE YOUR CASE...")
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.configure(state="disabled")
        self.set_status("STATUS: ACTIVE // VERDICT: PENDING", color=THEME["warning"])

    def close(self) -> None:
        self.window.withdraw()
        self.on_close()

    def show(self) -> None:
        self.window.deiconify()
        self.window.lift()

    def hide(self) -> None:
        self.window.withdraw()


def create_judgement_window(parent: tk.Tk, on_process, on_close) -> JudgementWindow:
    """Factory for the judgement system floating window."""

    return JudgementWindow(parent=parent, on_process=on_process, on_close=on_close)
