import customtkinter as ctk
import subprocess
import signal
import os
from tkinter import messagebox
import keyboard
import json
import time
import threading

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.geometry("1000x880")
root.title("Mirror Dungeon Runner")

status_columns = [
    ["sinking", "burn", "poise"],
    ["charge", "rupture", "slash", "blunt"],
    ["bleed", "tremor", "pierce"]
]

sinner_list = [
    "Yi Sang", "Faust", "Don Quixote", "Ryōshū", "Meursault",
    "Hong Lu", "Heathcliff", "Ishmael", "Rodion", "Sinclair", "Gregor", "Outis"
]

json_path = os.path.join("config", "squad_order.json")
slow_json_path = os.path.join("config", "slow_squad_order.json")

squad_data = {}
slow_squad_data = {}

def sinner_key(name):
    return name.lower().replace(" ", "").replace("ō", "o").replace("ū", "u")

def load_json():
    global squad_data, slow_squad_data
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            squad_data = json.load(f)
    else:
        squad_data = {}
    # Copy squad to slow
    slow_squad_data = json.loads(json.dumps(squad_data))
    save_slow_json()

def save_json():
    with open(json_path, "w") as f:
        json.dump(squad_data, f, indent=4)

def save_slow_json():
    with open(slow_json_path, "w") as f:
        json.dump(slow_squad_data, f, indent=4)

def delayed_slow_sync():
    time.sleep(3)
    slow_squad_data.update(json.loads(json.dumps(squad_data)))
    save_slow_json()

checkbox_vars = {}
dropdown_vars = {}
expand_frames = {}

tabs = ctk.CTkTabview(master=root, width=960, height=820)
tabs.pack(padx=20, pady=20, fill="both", expand=True)

tab_md = tabs.add("Mirror Dungeon")
tab_exp = tabs.add("Exp")
tab_threads = tabs.add("Threads")

process = None

def kill_bot():
    global process
    if process:
        try:
            os.kill(process.pid, signal.SIGTERM)
        except Exception as e:
            print(f"[ERROR] Failed to kill process: {e}")
        process = None
    start_button.configure(text="Start")

def save_selected_statuses():
    selected = [name for name, var in checkbox_vars.items() if var.get()]
    os.makedirs("config", exist_ok=True)
    with open("config/status_selection.txt", "w") as f:
        f.write("\n".join(selected))

def load_initial_selections():
    try:
        with open("config/status_selection.txt", "r") as f:
            return {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        return set()

def on_checkbox_toggle(changed_option):
    for name, var in checkbox_vars.items():
        if name != changed_option:
            var.set(False)
    save_selected_statuses()

def toggle_expand(frame, arrow_var):
    if frame.winfo_ismapped():
        frame.pack_forget()
        arrow_var.set("▶")
    else:
        frame.pack(pady=(2, 8), fill="x")
        arrow_var.set("▼")

def update_json_from_dropdown(status):
    entries = dropdown_vars[status]
    updated = {}
    for i, var in enumerate(entries):
        val = var.get()
        if val != "None":
            updated[sinner_key(val)] = i + 1
    squad_data[status] = updated
    save_json()
    threading.Thread(target=delayed_slow_sync, daemon=True).start()

def dropdown_callback(status, index, *_):
    new_val = dropdown_vars[status][index].get()
    if new_val == "None":
        update_json_from_dropdown(status)
        return

    # Check if duplicate exists
    for i, var in enumerate(dropdown_vars[status]):
        if i != index and var.get() == new_val:
            # Swap with old value from slow_squad
            slot_num = i + 1
            old_key = next((k for k, v in slow_squad_data.get(status, {}).items() if v == index + 1), None)
            if old_key:
                old_pretty = next((x for x in sinner_list if sinner_key(x) == old_key), "None")
                var.set(old_pretty)
            break

    update_json_from_dropdown(status)

def start_run():
    global process
    if start_button.cget("text") == "Stop":
        kill_bot()
        return
    try:
        count = int(entry.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Enter a valid number of runs.")
        return
    save_selected_statuses()
    script_path = os.path.join(os.getcwd(), "compiled_runner.py")
    process = subprocess.Popen(["python", script_path, str(count)])
    start_button.configure(text="Stop")

scroll = ctk.CTkScrollableFrame(master=tab_md)
scroll.pack(fill="both", expand=True)

ctk.CTkLabel(scroll, text="Number of Runs:").pack(pady=(10, 0))
entry = ctk.CTkEntry(scroll)
entry.pack(pady=(0, 5))

start_button = ctk.CTkButton(scroll, text="Start", command=start_run)
start_button.pack(pady=(0, 15))

ctk.CTkLabel(scroll, text="Your Team", font=ctk.CTkFont(size=16, weight="bold")).pack()
team_frame = ctk.CTkFrame(scroll)
team_frame.pack(pady=(0, 15))

team_order = [
    ("sinking", 0, 0), ("charge", 0, 1), ("slash", 0, 2),
    ("blunt", 1, 0), ("burn", 1, 1), ("rupture", 1, 2),
    ("poise", 2, 0), ("bleed", 2, 1), ("tremor", 2, 2),
    ("pierce", 3, 1)
]

prechecked = load_initial_selections()
for name, row, col in team_order:
    var = ctk.BooleanVar(value=name in prechecked)
    chk = ctk.CTkCheckBox(
        master=team_frame,
        text=name.capitalize(),
        variable=var,
        command=lambda opt=name: on_checkbox_toggle(opt)
    )
    chk.grid(row=row, column=col, padx=5, pady=2, sticky="w")
    checkbox_vars[name] = var

ctk.CTkLabel(scroll, text="Assign Sinners to Name", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="center", pady=(0, 10))

container = ctk.CTkFrame(scroll)
container.pack()

load_json()

for col_idx, group in enumerate(status_columns):
    col = ctk.CTkFrame(container, fg_color="transparent")
    col.grid(row=0, column=col_idx, padx=15, sticky="n")

    for row_idx, status in enumerate(group):
        wrapper = ctk.CTkFrame(master=col, fg_color="transparent")
        wrapper.grid(row=row_idx, column=0, sticky="nw")

        arrow_var = ctk.StringVar(value="▶")
        full_text = ctk.StringVar(value=f"{arrow_var.get()} {status.capitalize()}")

        def make_toggle(stat=status, arrow=arrow_var):
            return lambda: toggle_expand(expand_frames[stat], arrow)

        btn = ctk.CTkButton(
            master=wrapper,
            textvariable=full_text,
            command=make_toggle(),
            width=200,
            height=38,
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w"
        )
        btn.pack(anchor="w", pady=(0, 6))

        arrow_var.trace_add("write", lambda *a, var=arrow_var, textvar=full_text, name=status: textvar.set(f"{var.get()} {name.capitalize()}"))

        frame = ctk.CTkFrame(master=wrapper, fg_color="transparent", corner_radius=0)
        expand_frames[status] = frame
        frame.pack_forget()

        dropdown_vars[status] = []
        default_order = squad_data.get(status, {})
        reverse_map = {v: k for k, v in default_order.items()}

        for i in range(12):
            row = ctk.CTkFrame(master=frame, fg_color="transparent")
            row.pack(pady=1, anchor="w")

            label = ctk.CTkLabel(
                master=row,
                text=f"{i+1}.",
                anchor="e",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#b0b0b0",
                width=30
            )
            label.pack(side="left", padx=(0, 10))

            var = ctk.StringVar()
            raw_name = reverse_map.get(i + 1)
            pretty = next((x for x in sinner_list if sinner_key(x) == raw_name), "None") if raw_name else "None"
            var.set(pretty)

            def bind_callback(status=status, idx=i, v=var):
                v.trace_add("write", lambda *a: dropdown_callback(status, idx))

            dropdown = ctk.CTkOptionMenu(
                master=row,
                variable=var,
                values=sinner_list,
                width=160,
                font=ctk.CTkFont(size=15, weight="bold")
            )
            dropdown.pack(side="left")
            bind_callback()
            dropdown_vars[status].append(var)

keyboard.add_hotkey("ctrl+q", start_run)
root.mainloop()
