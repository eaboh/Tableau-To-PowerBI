"""Lightweight end-user GUI for Tableau to Power BI migration.

Zero external dependencies: built with Tkinter + subprocess.

Usage:
    python web/light_ui.py
"""

from __future__ import annotations

import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import csv
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

try:
    import winsound
except ImportError:
    winsound = None


class LightMigrationUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Tableau to Power BI - Light UI")
        self.root.geometry("980x680")
        self.root.minsize(900, 620)

        self.repo_root = Path(__file__).resolve().parents[1]
        self.migrate_script = self.repo_root / "migrate.py"

        self.mode_var = tk.StringVar(value="batch")
        self.preset_var = tk.StringVar(value="Migrate")
        self.source_var = tk.StringVar(value="")
        self.output_var = tk.StringVar(value=str(self.repo_root / "artifacts" / "light_ui_output"))
        self.verbose_var = tk.BooleanVar(value=True)
        self.assess_only_var = tk.BooleanVar(value=False)
        self.global_assess_var = tk.BooleanVar(value=False)
        self.prep_lineage_only_var = tk.BooleanVar(value=False)
        self.notify_var = tk.BooleanVar(value=True)
        self.auto_open_report_var = tk.BooleanVar(value=True)
        self.progress_var = tk.DoubleVar(value=0.0)
        self._progress_total = 0
        self._applying_preset = False
        self._run_started_at: float | None = None
        self._all_logs: list[str] = []
        self._last_output_dir = ""
        self._last_dashboard = ""
        self._last_comparison = ""
        self._last_summary_csv = ""
        self._kpi_only = False

        self._process: subprocess.Popen[str] | None = None
        self._log_queue: queue.Queue[str] = queue.Queue()
        self._running = False
        self._stop_requested = False
        self._active_context: dict[str, object] = {}
        self._session_records: list[dict[str, object]] = []

        self._set_app_icon()
        self._build_ui()
        self._poll_log_queue()

    def _set_app_icon(self) -> None:
        # Build a small in-memory icon so no external asset is required.
        icon = tk.PhotoImage(width=16, height=16)
        for y in range(16):
            for x in range(16):
                color = "#0f4c81" if x < 8 else "#1d9bf0"
                if (x + y) % 5 == 0:
                    color = "#f5b700"
                icon.put(color, (x, y))
        self._app_icon = icon
        self.root.iconphoto(True, self._app_icon)

    def _build_ui(self) -> None:
        self.root.configure(bg="#f3f6fb")

        top = tk.Frame(self.root, padx=12, pady=12, bg="#f3f6fb")
        top.pack(fill=tk.X)

        hero = tk.Frame(top, bg="#0f4c81", padx=18, pady=16, bd=0, highlightthickness=0)
        hero.pack(fill=tk.X)
        tk.Label(
            hero,
            text="Tableau to Power BI Migration",
            font=("Segoe UI", 18, "bold"),
            anchor="w",
            bg="#0f4c81",
            fg="white",
        ).pack(fill=tk.X)
        tk.Label(
            hero,
            text="Pick a batch folder, choose where the result should go, then run the migration.",
            font=("Segoe UI", 10),
            fg="#dcecff",
            anchor="w",
            bg="#0f4c81",
        ).pack(fill=tk.X, pady=(4, 8))

        quick_row = tk.Frame(hero, bg="#0f4c81")
        quick_row.pack(fill=tk.X)
        tk.Label(
            quick_row,
            text="1) Select batch folder   2) Select output   3) Click Run migration",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            bg="#0f4c81",
        ).pack(side=tk.LEFT)
        tk.Checkbutton(
            quick_row,
            text="Auto-open HTML report",
            variable=self.auto_open_report_var,
            bg="#0f4c81",
            fg="white",
            activebackground="#0f4c81",
            activeforeground="white",
            selectcolor="#0f4c81",
        ).pack(side=tk.RIGHT)

        content = tk.Frame(self.root, padx=12, pady=10, bg="#f3f6fb")
        content.pack(fill=tk.BOTH, expand=True)

        setup_card = tk.LabelFrame(content, text="Migration Setup", padx=12, pady=10)
        setup_card.pack(fill=tk.X)

        mode_row = tk.Frame(setup_card)
        mode_row.pack(fill=tk.X, pady=4)
        tk.Label(mode_row, text="Mode", width=14, anchor="w").pack(side=tk.LEFT)
        tk.Label(mode_row, text="Batch folder only", fg="#0f4c81", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

        preset_row = tk.Frame(setup_card)
        preset_row.pack(fill=tk.X, pady=4)
        tk.Label(preset_row, text="Task", width=14, anchor="w").pack(side=tk.LEFT)
        self.preset_box = ttk.Combobox(
            preset_row,
            textvariable=self.preset_var,
            state="readonly",
            values=(
                "Assess",
                "Migrate",
                "Lineage",
            ),
            width=28,
        )
        self.preset_box.pack(side=tk.LEFT)
        self.preset_box.bind("<<ComboboxSelected>>", lambda _e: self._apply_preset())
        self.workflow_hint = tk.Label(
            setup_card,
            text="Batch workflow only. Pick one task: Assess, Migrate, or Lineage.",
            fg="#4b5563",
            anchor="w",
            justify="left",
        )
        self.workflow_hint.pack(fill=tk.X, pady=(0, 6))

        src_row = tk.Frame(setup_card)
        src_row.pack(fill=tk.X, pady=4)
        tk.Label(src_row, text="Source", width=14, anchor="w").pack(side=tk.LEFT)
        tk.Entry(src_row, textvariable=self.source_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        tk.Button(src_row, text="Browse", command=self._browse_source, width=10).pack(side=tk.LEFT)

        out_row = tk.Frame(setup_card)
        out_row.pack(fill=tk.X, pady=4)
        tk.Label(out_row, text="Output folder", width=14, anchor="w").pack(side=tk.LEFT)
        tk.Entry(out_row, textvariable=self.output_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        tk.Button(out_row, text="Browse", command=self._browse_output, width=10).pack(side=tk.LEFT)

        opts_row = tk.Frame(setup_card)
        opts_row.pack(fill=tk.X, pady=4)
        tk.Label(opts_row, text="Options", width=14, anchor="w").pack(side=tk.LEFT)
        tk.Checkbutton(opts_row, text="Verbose output", variable=self.verbose_var).pack(side=tk.LEFT)
        tk.Checkbutton(opts_row, text="Notify when done", variable=self.notify_var).pack(side=tk.LEFT, padx=(10, 0))
        tk.Button(opts_row, text="KPI Only View", width=14, command=self._toggle_kpi_only).pack(side=tk.RIGHT)

        mode_opts_row = tk.Frame(setup_card)
        self.assess_cb = tk.Checkbutton(
            mode_opts_row,
            text="Assessment only (--assess)",
            variable=self.assess_only_var,
            command=self._on_assess_toggle,
        )
        self.assess_cb.pack(side=tk.LEFT)
        self.global_assess_cb = tk.Checkbutton(
            mode_opts_row,
            text="Global assess (--global-assess)",
            variable=self.global_assess_var,
            command=self._on_global_assess_toggle,
        )
        self.global_assess_cb.pack(side=tk.LEFT, padx=(10, 0))
        self.prep_lineage_cb = tk.Checkbutton(
            mode_opts_row,
            text="Prep lineage only (--prep-lineage)",
            variable=self.prep_lineage_only_var,
            command=self._on_prep_lineage_toggle,
        )
        self.prep_lineage_cb.pack(side=tk.LEFT, padx=(10, 0))
        self.mode_opts_row = mode_opts_row

        actions_card = tk.LabelFrame(content, text="Run", padx=12, pady=10)
        actions_card.pack(fill=tk.X, pady=(10, 0))
        actions = tk.Frame(actions_card)
        actions.pack(fill=tk.X)
        self.run_btn = tk.Button(actions, text="Run migration", width=16, command=self._start_run)
        self.run_btn.pack(side=tk.LEFT)
        self.stop_btn = tk.Button(actions, text="Stop", width=10, command=self._stop_run, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.status_label = tk.Label(actions, text="Ready", fg="#145a32", anchor="w")
        self.status_label.pack(side=tk.LEFT, padx=(12, 0))
        results_actions = tk.Frame(actions_card)
        results_actions.pack(fill=tk.X, pady=(10, 0))
        tk.Label(results_actions, text="Results", fg="#0f4c81", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.open_summary_btn = tk.Button(results_actions, text="Summary CSV", width=13,
                          command=self._open_summary_csv, state=tk.DISABLED)
        self.open_summary_btn.pack(side=tk.RIGHT, padx=(0, 8))
        self.open_comparison_btn = tk.Button(results_actions, text="Comparison", width=13,
                             command=self._open_comparison, state=tk.DISABLED)
        self.open_comparison_btn.pack(side=tk.RIGHT, padx=(0, 8))
        self.open_dashboard_btn = tk.Button(results_actions, text="HTML Report", width=13,
                            command=self._open_dashboard, state=tk.DISABLED)
        self.open_dashboard_btn.pack(side=tk.RIGHT, padx=(0, 8))
        self.open_output_btn = tk.Button(results_actions, text="Output Folder", width=13,
                         command=self._open_output_folder, state=tk.DISABLED)
        self.open_output_btn.pack(side=tk.RIGHT, padx=(0, 8))

        kpi_panel = tk.Frame(self.root, padx=12, pady=6, bg="#eef6ff")
        kpi_panel.pack(fill=tk.X)
        self.kpi_measures = tk.Label(kpi_panel, text="Measures: -", bg="#eef6ff", fg="#0f4c81", font=("Segoe UI", 10, "bold"))
        self.kpi_measures.pack(side=tk.LEFT, padx=(0, 12))
        self.kpi_visuals = tk.Label(kpi_panel, text="Visuals: -", bg="#eef6ff", fg="#0f4c81", font=("Segoe UI", 10, "bold"))
        self.kpi_visuals.pack(side=tk.LEFT, padx=(0, 12))
        self.kpi_dax = tk.Label(kpi_panel, text="Visuals with values: -", bg="#eef6ff", fg="#0f4c81", font=("Segoe UI", 10, "bold"))
        self.kpi_dax.pack(side=tk.LEFT, padx=(0, 12))
        self.kpi_fidelity = tk.Label(kpi_panel, text="Fidelity: -", bg="#eef6ff", fg="#0f4c81", font=("Segoe UI", 10, "bold"))
        self.kpi_fidelity.pack(side=tk.LEFT)

        progress_row = tk.Frame(self.root, padx=12, pady=4)
        progress_row.pack(fill=tk.X)
        self.progress = ttk.Progressbar(
            progress_row,
            orient="horizontal",
            mode="determinate",
            variable=self.progress_var,
            maximum=100,
        )
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress_text = tk.Label(progress_row, text="0%", width=8, anchor="e")
        self.progress_text.pack(side=tk.LEFT, padx=(10, 0))

        status_row = tk.Frame(self.root, padx=12, pady=6)
        status_row.pack(fill=tk.X)
        self.stage_label = tk.Label(status_row, text="Stage: idle", anchor="w", fg="#334")
        self.stage_label.pack(side=tk.LEFT)
        self.elapsed_label = tk.Label(status_row, text="Elapsed: 00:00", anchor="w", fg="#334")
        self.elapsed_label.pack(side=tk.LEFT, padx=(20, 0))
        self.summary_label = tk.Label(status_row, text="", anchor="w", fg="#225")
        self.summary_label.pack(side=tk.LEFT, padx=(20, 0))

        info_row = tk.Frame(self.root, padx=12, pady=2)
        info_row.pack(fill=tk.X)
        self.dax_hint_label = tk.Label(
            info_row,
            text="Main KPI shows visuals with values. Explicit DAX visuals are tracked separately in the summary details.",
            anchor="w",
            fg="#4b5563",
        )
        self.dax_hint_label.pack(side=tk.LEFT)
        self.health_label = tk.Label(info_row, text="", anchor="e", fg="#1d4ed8")
        self.health_label.pack(side=tk.RIGHT)

        logs_frame = tk.Frame(self.root, padx=12, pady=12)
        logs_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(logs_frame, text="Logs", anchor="w").pack(fill=tk.X)
        self.log_box = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD, height=24)
        self.log_box.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self.log_box.configure(state=tk.DISABLED)
        self.logs_frame = logs_frame

        self._update_command_preview()
        self.source_var.trace_add("write", lambda *_: self._update_command_preview())
        self.output_var.trace_add("write", lambda *_: self._update_command_preview())
        self.mode_var.trace_add("write", lambda *_: self._update_command_preview())
        self.verbose_var.trace_add("write", lambda *_: self._update_command_preview())
        self.assess_only_var.trace_add("write", lambda *_: self._update_command_preview())
        self.global_assess_var.trace_add("write", lambda *_: self._update_command_preview())
        self.prep_lineage_only_var.trace_add("write", lambda *_: self._update_command_preview())
        self.mode_var.trace_add("write", lambda *_: self._update_option_states())
        self._update_option_states()
        self._apply_preset()

    def _apply_preset(self) -> None:
        preset = self.preset_var.get()
        self._applying_preset = True
        try:
            if preset == "Migrate":
                self.mode_var.set("batch")
                self.assess_only_var.set(False)
                self.global_assess_var.set(False)
                self.prep_lineage_only_var.set(False)
                self.verbose_var.set(True)
                self.workflow_hint.configure(text="Run a full migration batch and generate Power BI outputs.")
            elif preset == "Lineage":
                self.mode_var.set("batch")
                self.assess_only_var.set(False)
                self.global_assess_var.set(False)
                self.prep_lineage_only_var.set(True)
                self.verbose_var.set(True)
                self.workflow_hint.configure(text="Analyze Tableau Prep flow links across a folder of prep files.")
            elif preset == "Assess":
                self.mode_var.set("batch")
                self.assess_only_var.set(False)
                self.global_assess_var.set(True)
                self.prep_lineage_only_var.set(False)
                self.verbose_var.set(True)
                self.workflow_hint.configure(text="Review a whole folder and generate an overall assessment summary.")
        finally:
            self._applying_preset = False

    def _update_option_states(self) -> None:
        self.assess_cb.configure(state=tk.DISABLED)
        self.global_assess_cb.configure(state=tk.NORMAL)
        self.prep_lineage_cb.configure(state=tk.NORMAL)
        self.assess_only_var.set(False)

    def _on_assess_toggle(self) -> None:
        if self.assess_only_var.get():
            self.global_assess_var.set(False)
            self.prep_lineage_only_var.set(False)

    def _on_global_assess_toggle(self) -> None:
        if self.global_assess_var.get():
            self.prep_lineage_only_var.set(False)

    def _on_prep_lineage_toggle(self) -> None:
        if self.prep_lineage_only_var.get():
            self.global_assess_var.set(False)

    def _browse_source(self) -> None:
        path = filedialog.askdirectory(title="Select folder for batch migration")
        if path:
            self.source_var.set(path)

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.output_var.set(path)

    def _toggle_kpi_only(self) -> None:
        self._kpi_only = not self._kpi_only
        if self._kpi_only:
            self.logs_frame.pack_forget()
            self.status_label.configure(text="KPI-only view enabled", fg="#145a32")
        else:
            self.logs_frame.pack(fill=tk.BOTH, expand=True)
            self.status_label.configure(text="Ready", fg="#145a32")

    def _build_command(self) -> list[str]:
        source = self.source_var.get().strip()
        output = self.output_var.get().strip()

        cmd = [sys.executable, str(self.migrate_script)]
        if self.prep_lineage_only_var.get():
            cmd += ["--prep-lineage", source]
        else:
            if self.global_assess_var.get():
                cmd.append("--global-assess")
            cmd += ["--batch", source]

        cmd += ["--output-dir", output]
        if self.verbose_var.get():
            cmd.append("--verbose")
        return cmd

    def _update_command_preview(self) -> None:
        return

    def _validate_inputs(self) -> bool:
        source = self.source_var.get().strip()
        output = self.output_var.get().strip()

        if not self.migrate_script.exists():
            messagebox.showerror("Missing script", f"Could not find migrate.py at:\n{self.migrate_script}")
            return False
        if not source:
            messagebox.showwarning("Missing source", "Please choose a source folder.")
            return False

        source_path = Path(source)
        if not source_path.is_dir():
            messagebox.showwarning("Invalid source", "Batch mode requires a folder.")
            return False

        if not output:
            messagebox.showwarning("Missing output", "Please choose an output folder.")
            return False

        Path(output).mkdir(parents=True, exist_ok=True)

        # Preflight: verify output directory is writable.
        try:
            with tempfile.NamedTemporaryFile(prefix="ttpbi_", suffix=".tmp", dir=output, delete=True):
                pass
        except OSError as exc:
            messagebox.showwarning(
                "Output not writable",
                f"Cannot write to output folder:\n{output}\n\nDetails: {exc}",
            )
            return False

        return True

    def _append_log(self, text: str) -> None:
        self._all_logs.append(text)
        self._capture_artifact_paths(text)
        self._update_progress_from_log(text)
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.insert(tk.END, text)
        self.log_box.see(tk.END)
        self.log_box.configure(state=tk.DISABLED)

    def _capture_artifact_paths(self, text: str) -> None:
        out_match = re.search(r"Output:\s*(.+)", text)
        if out_match:
            self._last_output_dir = out_match.group(1).strip()

        dash_match = re.search(r"HTML dashboard:\s*(.+\.html)", text)
        if dash_match:
            self._last_dashboard = dash_match.group(1).strip()
            self._last_summary_csv = os.path.splitext(self._last_dashboard)[0] + "_summary.csv"

        comp_match = re.search(r"Comparison report:\s*(.+\.html)", text)
        if comp_match:
            self._last_comparison = comp_match.group(1).strip()

        pbip_match = re.search(r"\[OK\]\s+Power BI Project created:\s*(.+)", text)
        if pbip_match and not self._last_output_dir:
            self._last_output_dir = pbip_match.group(1).strip()

    def _set_progress(self, value: float, label: str | None = None) -> None:
        clamped = max(0.0, min(100.0, value))
        self.progress_var.set(clamped)
        self.progress_text.configure(text=f"{clamped:.0f}%")
        if label:
            self.status_label.configure(text=label)

    def _update_progress_from_log(self, text: str) -> None:
        batch_match = re.search(r"\[(\d+)/(\d+)\]\s+Migrating", text)
        if batch_match:
            done = int(batch_match.group(1))
            total = int(batch_match.group(2))
            self._progress_total = max(self._progress_total, total)
            self._set_progress((done / total) * 100.0, label=f"Running... ({done}/{total})")
            self.stage_label.configure(text="Stage: batch migration")
            return

        step_match = re.search(r"\[Step\s+(\d+)/(\d+)\]", text)
        if step_match and self.mode_var.get() == "single":
            step = int(step_match.group(1))
            total = int(step_match.group(2))
            self._set_progress((step / total) * 100.0, label=f"Running... (step {step}/{total})")
            if "TABLEAU OBJECTS EXTRACTION" in text:
                self.stage_label.configure(text="Stage: extract")
            elif "POWER BI PROJECT GENERATION" in text:
                self.stage_label.configure(text="Stage: generate")
            return

        if "MIGRATION REPORT:" in text:
            self.stage_label.configure(text="Stage: report")

        if "PBI Desktop Validation:" in text:
            self.stage_label.configure(text="Stage: validate")

        if "BATCH MIGRATION SUMMARY" in text or "IMPORT COMPLETE" in text:
            self._set_progress(100.0)

    def _update_elapsed_label(self) -> None:
        if not self._running or self._run_started_at is None:
            return
        elapsed = int(time.monotonic() - self._run_started_at)
        mins, secs = divmod(elapsed, 60)
        self.elapsed_label.configure(text=f"Elapsed: {mins:02d}:{secs:02d}")
        self.root.after(500, self._update_elapsed_label)

    def _start_run(self) -> None:
        if self._running:
            return
        if not self._validate_inputs():
            return

        context = {
            "source": self.source_var.get().strip(),
            "output": self.output_var.get().strip(),
            "mode": self.mode_var.get(),
            "command": self._build_command(),
            "options": self._collect_current_options(),
            "queue_index": None,
        }
        self._start_execution(context)

    def _start_execution(self, context: dict[str, object]) -> None:
        self._running = True
        self._stop_requested = False
        self._active_context = context
        self._progress_total = 0
        self._run_started_at = time.monotonic()
        self._all_logs = []
        self._last_output_dir = ""
        self._last_dashboard = ""
        self._last_comparison = ""
        self._last_summary_csv = ""
        self.summary_label.configure(text="")
        self.health_label.configure(text="")
        self.stage_label.configure(text="Stage: starting")
        self.elapsed_label.configure(text="Elapsed: 00:00")
        self._set_progress(0.0, label="Running...")
        self.run_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.open_output_btn.configure(state=tk.DISABLED)
        self.open_dashboard_btn.configure(state=tk.DISABLED)
        self.open_comparison_btn.configure(state=tk.DISABLED)
        self.open_summary_btn.configure(state=tk.DISABLED)
        self.status_label.configure(text="Running...", fg="#8a6d1f")

        self._append_log("\n" + "=" * 80 + "\n")
        self._append_log(f"Starting migration: {context.get('source', '')}\n")

        cmd = context["command"]
        thread = threading.Thread(target=self._run_process, args=(cmd,), daemon=True)
        thread.start()
        self.root.after(500, self._update_elapsed_label)

    def _run_process(self, cmd: object) -> None:
        try:
            assert isinstance(cmd, list)
            self._process = subprocess.Popen(
                cmd,
                cwd=str(self.repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )

            assert self._process.stdout is not None
            for line in self._process.stdout:
                self._log_queue.put(line)

            exit_code = self._process.wait()
            self._log_queue.put(f"\nProcess finished with exit code: {exit_code}\n")
            self._log_queue.put("__RUN_SUCCESS__" if exit_code == 0 else "__RUN_FAILED__")
        except Exception as exc:
            self._log_queue.put(f"\nError launching migration: {exc}\n")
            self._log_queue.put("__RUN_FAILED__")
        finally:
            self._process = None

    def _stop_run(self) -> None:
        self._stop_requested = True
        if self._process and self._process.poll() is None:
            self._process.terminate()
            self._append_log("\nStop requested by user.\n")

    def _finish_run(self, ok: bool) -> None:
        elapsed = 0.0
        if self._run_started_at is not None:
            elapsed = max(0.0, time.monotonic() - self._run_started_at)
        item_status = "success" if ok else ("stopped" if self._stop_requested else "failed")
        self._record_session_row(item_status, elapsed)

        self._running = False
        self._run_started_at = None
        self.run_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)

        if ok:
            self._set_progress(100.0)
            self.status_label.configure(text="Completed", fg="#145a32")
            self.stage_label.configure(text="Stage: completed")
            if self._last_output_dir:
                self.open_output_btn.configure(state=tk.NORMAL)
            if self._last_dashboard and os.path.exists(self._last_dashboard):
                self.open_dashboard_btn.configure(state=tk.NORMAL)
            if self._last_comparison and os.path.exists(self._last_comparison):
                self.open_comparison_btn.configure(state=tk.NORMAL)
            if self._last_summary_csv and os.path.exists(self._last_summary_csv):
                self.open_summary_btn.configure(state=tk.NORMAL)
            summary_text = ""
            if self._last_output_dir:
                summary_text = f"Output ready: {self._last_output_dir}"
            self.summary_label.configure(text=summary_text)
            self.health_label.configure(text=self._build_health_summary())
            self._update_kpi_panel(self._read_summary_metrics())
            if self.auto_open_report_var.get() and self._last_dashboard and os.path.exists(self._last_dashboard):
                os.startfile(self._last_dashboard)
            self._notify("Migration completed successfully")
            messagebox.showinfo("Migration complete", "Migration finished successfully.")
        else:
            if self.progress_var.get() < 1:
                self._set_progress(0.0)
            self.status_label.configure(text="Failed", fg="#8a1f1f")
            self.stage_label.configure(text="Stage: failed")
            hint = self._build_error_hint()
            self.health_label.configure(text="")
            msg = "Migration ended with errors. Check logs."
            if hint:
                msg += f"\n\nSuggested action:\n- {hint}"
            self._notify("Migration failed")
            messagebox.showwarning("Migration failed", msg)

    def _collect_current_options(self) -> dict[str, object]:
        return {
            "verbose": self.verbose_var.get(),
            "assess_only": self.assess_only_var.get(),
            "global_assess": self.global_assess_var.get(),
            "prep_lineage_only": self.prep_lineage_only_var.get(),
            "preset": self.preset_var.get(),
        }

    def _record_session_row(self, status: str, elapsed_seconds: float) -> None:
        source = str(self._active_context.get("source", ""))
        output = str(self._active_context.get("output", ""))
        mode = str(self._active_context.get("mode", ""))
        options = self._active_context.get("options", {})
        if not isinstance(options, dict):
            options = {}
        metrics = self._read_summary_metrics()
        row = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": source,
            "output": output,
            "mode": mode,
            "status": status,
            "duration_seconds": round(elapsed_seconds, 2),
            "options": options,
            "metrics": metrics,
        }
        self._session_records.append(row)


    def _read_summary_metrics(self) -> dict[str, object]:
        if not self._last_summary_csv or not os.path.exists(self._last_summary_csv):
            return {}
        try:
            with open(self._last_summary_csv, "r", encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            return rows[0] if rows else {}
        except OSError:
            return {}

    def _update_kpi_panel(self, metrics: dict[str, object]) -> None:
        self.kpi_measures.configure(text=f"Measures: {metrics.get('measures_count', '-')}")
        self.kpi_visuals.configure(text=f"Visuals: {metrics.get('visuals_count', '-')}")
        self.kpi_dax.configure(text=f"Visuals with values: {metrics.get('visuals_with_values_count', '-')}")
        self.kpi_fidelity.configure(text=f"Fidelity: {metrics.get('fidelity_score', '-')}")


    def _notify(self, text: str) -> None:
        if not self.notify_var.get():
            return
        self.root.title(f"Tableau to Power BI - {text}")
        if winsound is not None:
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except RuntimeError:
                pass

    def _build_error_hint(self) -> str:
        log_text = "\n".join(self._all_logs)
        checks = [
            ("handleClearSelection", "Regenerate with latest slicer hotfix and reopen the new .pbip output."),
            ("same name already exists", "Name collision detected; ensure latest generator is used and regenerate output from scratch."),
            ("Number of Records", "Use the patched build that removes Number of Records measure/column collisions and regenerate."),
            ("Access is denied", "Choose a different output folder or close apps locking files (OneDrive sync can lock files)."),
            ("No datasources found", "Source workbook has no extractable datasources; verify the Tableau file and rerun."),
        ]
        for token, hint in checks:
            if token in log_text:
                return hint
        return "Review the first ERROR/Traceback section in logs and rerun after applying that fix."

    def _open_output_folder(self) -> None:
        if self._last_output_dir and os.path.exists(self._last_output_dir):
            os.startfile(self._last_output_dir)
        else:
            messagebox.showwarning("Output not found", "No output folder is available yet.")

    def _open_dashboard(self) -> None:
        if self._last_dashboard and os.path.exists(self._last_dashboard):
            os.startfile(self._last_dashboard)
        else:
            messagebox.showwarning("Dashboard not found", "No HTML dashboard is available yet.")

    def _open_comparison(self) -> None:
        if self._last_comparison and os.path.exists(self._last_comparison):
            os.startfile(self._last_comparison)
        else:
            messagebox.showwarning("Comparison report not found", "No comparison report is available yet.")

    def _open_summary_csv(self) -> None:
        if self._last_summary_csv and os.path.exists(self._last_summary_csv):
            os.startfile(self._last_summary_csv)
        else:
            messagebox.showwarning("Summary CSV not found", "No summary CSV is available yet.")

    def _build_health_summary(self) -> str:
        if self._last_summary_csv and os.path.exists(self._last_summary_csv):
            try:
                with open(self._last_summary_csv, "r", encoding="utf-8", newline="") as fh:
                    rows = list(csv.DictReader(fh))
                if rows:
                    row = rows[0]
                    visuals = row.get("visuals_count", "-")
                    visuals_with_values = row.get("visuals_with_values_count", "-")
                    dax_visuals = row.get("visuals_with_dax_measures_count", "-")
                    measures = row.get("measures_count", "-")
                    return (
                        f"Health: measures={measures}, visuals={visuals}, "
                        f"visuals with values={visuals_with_values}, explicit DAX visuals={dax_visuals}"
                    )
            except OSError:
                pass
        return ""

    def _poll_log_queue(self) -> None:
        try:
            while True:
                msg = self._log_queue.get_nowait()
                if msg == "__RUN_SUCCESS__":
                    self._finish_run(ok=True)
                elif msg == "__RUN_FAILED__":
                    self._finish_run(ok=False)
                else:
                    self._append_log(msg)
        except queue.Empty:
            pass
        self.root.after(120, self._poll_log_queue)


def main() -> int:
    if os.environ.get("DISPLAY", "") == "" and os.name != "nt":
        print("No GUI display found. Run on a desktop environment.")
        return 1

    root = tk.Tk()
    app = LightMigrationUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
