import json
import os
import math
import tkinter as tk
from tkinter import ttk, messagebox
from itertools import combinations

STAT_OPTIONS = ["None", "Luck", "Mining Power", "Swift Mining", "Yield"]
STAT_CODES = {
    "None": "",
    "Luck": "L",
    "Mining Power": "MP",
    "Swift Mining": "S",
    "Yield": "Y"
}

class RuneOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rune Optimizer")
        self.root.geometry("550x420")
        self.root.resizable(False, False)

        self.runes = []
        # Auto-load backup if exists
        if os.path.exists("runas_backup.json"):
            try:
                with open("runas_backup.json", 'r', encoding='utf-8') as f:
                    runes_data = json.load(f)
                    for rune_data in runes_data:
                        self.runes.append({
                            'name': rune_data['name'],
                            'code': rune_data['code'],
                            'stats': rune_data['stats']
                        })
                    if self.runes:
                        self.next_rune_number = max(
                            [int(r['name'].split()[1]) for r in self.runes if r['name'].startswith('Rune ')],
                            default=0
                        ) + 1
                        self.update_rune_list()
            except:
                pass
        self.next_rune_number = 1

        self.pickaxes = {}
        self.rocks = {}
        self.ores = {}
        self.selected_pickaxe_id = None
        self.selected_rock_id = None
        self.selected_ore_id = None
        self.selected_world_num = 3

        self.pickaxe_damage = 100
        self.pickaxe_speed_bonus = 0
        self.pickaxe_luck = 0
        self.rune_slots = 0

        self.hp_rock = 1000
        self.rock_luck = 0
        self.ore_count = 0

        self.chance_numerator = 0
        self.chance_denominator = 1

        self.master_miner_level = 5
        self.dedicated_player_level = 5

        self.load_json_data()
        self.set_default_parameters()  # Load default parameters on startup

        # Frame superior con título y botones
        top_frame = ttk.Frame(root)
        top_frame.pack(fill="x", padx=10, pady=(10, 0))

        ttk.Label(top_frame, text="Rune List", font=("Segoe UI", 10, "bold")).pack(side="left")

        # Botones SOLO arriba a la derecha
        btn_save = ttk.Button(top_frame, text="Save Runas", command=self.save_runes_to_file)
        btn_save.pack(side="right", padx=2)

        btn_load = ttk.Button(top_frame, text="Load Runas", command=self.load_runes_from_file)
        btn_load.pack(side="right", padx=2)

        # Frame para la lista
        frame_list = ttk.Frame(root, padding=10)
        frame_list.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.listbox = tk.Listbox(frame_list, height=12, font=("Segoe UI", 10))
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        frame_buttons = ttk.Frame(root)
        frame_buttons.pack(fill="x", padx=10, pady=5)

        btn_add = ttk.Button(frame_buttons, text="Add Rune", command=self.open_add_rune_window)
        btn_add.pack(side="left", padx=5)

        btn_delete = ttk.Button(frame_buttons, text="Delete Rune", command=self.delete_selected_rune)
        btn_delete.pack(side="left", padx=5)

        btn_optimize = ttk.Button(frame_buttons, text="Optimize", command=self.optimize_runes)
        btn_optimize.pack(side="left", padx=5)

        btn_modify_params = ttk.Button(frame_buttons, text="Modify parameters", command=self.open_modify_parameters_window)
        btn_modify_params.pack(side="right", padx=5)

        # Status label and result text removed per user request
        # At the end of __init__, after creating all widgets
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_json_data(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            with open(os.path.join(base_dir, "pickaxes.json"), encoding="utf-8") as f:
                self.pickaxes = json.load(f)
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load pickaxes.json: {e}")
            self.pickaxes = {}

        try:
            with open(os.path.join(base_dir, "rocks.json"), encoding="utf-8") as f:
                self.rocks = json.load(f)
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load rocks.json: {e}")
            self.rocks = {}

        try:
            with open(os.path.join(base_dir, "ores.json"), encoding="utf-8") as f:
                self.ores = json.load(f)
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load ores.json: {e}")
            self.ores = {}

    def set_default_parameters(self):
        """Set default parameters from JSON data on startup."""
        # Find and set Kitsune Pickaxe
        if "Kitsune Pickaxe" in self.pickaxes:
            self.selected_pickaxe_id = "Kitsune Pickaxe"
            data = self.pickaxes["Kitsune Pickaxe"]
            self.pickaxe_damage = data.get("pickaxe_damage", 0)
            self.pickaxe_speed_bonus = data.get("pickaxe_speed_bonus", 0)
            self.pickaxe_luck = data.get("pickaxe_luck", 0)
            self.rune_slots = data.get("rune_slots", 0)
            print(f"[DEFAULT] Kitsune Pickaxe loaded: damage={self.pickaxe_damage}, speed={self.pickaxe_speed_bonus}, luck={self.pickaxe_luck}, slots={self.rune_slots}")
        
        # Find and set Floating Crystal
        for rock_id, rock_data in self.rocks.items():
            if rock_data.get("display_name") == "Floating Crystal":
                self.selected_rock_id = rock_id
                self.selected_world_num = rock_data.get("world", self.selected_world_num)
                self.hp_rock = rock_data.get("hp_rock", 0)
                self.rock_luck = rock_data.get("rock_luck", 0)
                ore_count_raw = rock_data.get("ore_count", 1)
                if isinstance(ore_count_raw, list):
                    self.ore_count = ore_count_raw
                else:
                    self.ore_count = [ore_count_raw]
                print(f"[DEFAULT] Floating Crystal loaded: hp={self.hp_rock}, luck={self.rock_luck}, ore_count={self.ore_count}")
                break
        
        # Find and set Gargantuan ore
        for ore_id, ore_data in self.ores.items():
            if ore_data.get("display_name") == "Gargantuan":
                self.selected_ore_id = ore_id
                self.chance_numerator = ore_data.get("chance_numerator", 0)
                self.chance_denominator = ore_data.get("chance_denominator", 1)
                print(f"[DEFAULT] Gargantuan ore loaded: numerator={self.chance_numerator}, denominator={self.chance_denominator}")
                break

    def open_add_rune_window(self):
        self.add_window = tk.Toplevel(self.root)
        self.add_window.title("Add Rune")
        self.add_window.geometry("420x260")
        self.add_window.resizable(False, False)
        self.add_window.transient(self.root)
        self.add_window.grab_set()

        ttk.Label(self.add_window, text="Select up to two attributes:", font=("Segoe UI", 10, "bold")).pack(pady=(10, 5))

        frame_attr1 = ttk.Frame(self.add_window)
        frame_attr1.pack(fill="x", padx=15, pady=5)
        ttk.Label(frame_attr1, text="Attribute 1:", width=12).pack(side="left")
        self.attr1_var = tk.StringVar(value="None")
        self.attr1_combo = ttk.Combobox(frame_attr1, textvariable=self.attr1_var, values=STAT_OPTIONS, state="readonly", width=16)
        self.attr1_combo.pack(side="left", padx=(0, 10))
        self.attr1_combo.bind("<<ComboboxSelected>>", lambda event: self.update_value_states())
        self.value1_var = tk.StringVar()
        self.value1_entry = ttk.Entry(frame_attr1, textvariable=self.value1_var, width=6, state="disabled", validate="key")
        self.value1_entry.pack(side="left")
        ttk.Label(frame_attr1, text="%", width=2).pack(side="left")

        frame_attr2 = ttk.Frame(self.add_window)
        frame_attr2.pack(fill="x", padx=15, pady=5)
        ttk.Label(frame_attr2, text="Attribute 2:", width=12).pack(side="left")
        self.attr2_var = tk.StringVar(value="None")
        self.attr2_combo = ttk.Combobox(frame_attr2, textvariable=self.attr2_var, values=STAT_OPTIONS, state="readonly", width=16)
        self.attr2_combo.pack(side="left", padx=(0, 10))
        self.attr2_combo.bind("<<ComboboxSelected>>", lambda event: self.update_value_states())
        self.value2_var = tk.StringVar()
        self.value2_entry = ttk.Entry(frame_attr2, textvariable=self.value2_var, width=6, state="disabled", validate="key")
        self.value2_entry.pack(side="left")
        ttk.Label(frame_attr2, text="%", width=2).pack(side="left")

        vcmd = (self.add_window.register(self.validate_numeric), "%P")
        self.value1_entry.config(validatecommand=vcmd)
        self.value2_entry.config(validatecommand=vcmd)

        frame_actions = ttk.Frame(self.add_window)
        frame_actions.pack(fill="x", padx=15, pady=15)

        self.btn_accept = ttk.Button(frame_actions, text="Accept", command=self.accept_new_rune, state="disabled")
        self.btn_accept.pack(side="left", padx=5)

        btn_cancel = ttk.Button(frame_actions, text="Cancel", command=self.add_window.destroy)
        btn_cancel.pack(side="left", padx=5)

        self.update_value_states()

    def validate_numeric(self, text):
        return text.isdigit() or text == ""

    def update_value_states(self):
        self._set_entry_state(self.attr1_var.get(), self.value1_entry, self.value1_var)
        self._set_entry_state(self.attr2_var.get(), self.value2_entry, self.value2_var)
        self.btn_accept.config(state="normal" if self.can_accept_rune() else "disabled")

    def _set_entry_state(self, attr, entry_widget, value_var):
        if attr == "None":
            entry_widget.config(state="disabled")
            value_var.set("")
        else:
            entry_widget.config(state="normal")

    def can_accept_rune(self):
        attr1 = self.attr1_var.get()
        attr2 = self.attr2_var.get()
        # At least one attribute must be different from 'None'
        return attr1 != "None" or attr2 != "None"

    def build_rune_code(self, stats):
        code_parts = []
        for attr, value in stats:
            prefix = STAT_CODES.get(attr, "")
            code_parts.append(f"{prefix}{value}")
        return "".join(code_parts)

    def accept_new_rune(self):
        stats = []
        if self.attr1_var.get() != "None":
            val1 = self.value1_var.get() if self.value1_var.get() else "0"
            stats.append((self.attr1_var.get(), int(val1)))
        if self.attr2_var.get() != "None":
            val2 = self.value2_var.get() if self.value2_var.get() else "0"
            stats.append((self.attr2_var.get(), int(val2)))

        rune_name = f"Rune {self.next_rune_number}"
        rune_code = self.build_rune_code(stats)
        self.runes.append({"name": rune_name, "code": rune_code, "stats": stats})
        self.next_rune_number += 1
        self.update_rune_list()
        self.add_window.destroy()

    def update_rune_list(self):
        self.listbox.delete(0, tk.END)
        for rune in self.runes:
            self.listbox.insert(tk.END, f"{rune['name']} - {rune['code']}")

    def delete_selected_rune(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("Delete Rune", "Select a rune to delete.")
            return
        index = selected[0]
        removed = self.runes.pop(index)
        self.update_rune_list()
        # status label removed

    def optimize_runes(self):
        print("\n" + "="*60)
        print("=== DEBUG: Optimize Start ===")
        print(f"selected_pickaxe_id: {self.selected_pickaxe_id}")
        print(f"selected_rock_id: {self.selected_rock_id}")
        print(f"selected_ore_id: {self.selected_ore_id}")
        print(f"rune_slots: {self.rune_slots}")
        print(f"available runes: {len(self.runes)}")
        for idx, rune in enumerate(self.runes):
            print(f"  Rune {idx}: {rune['name']} - {rune['code']}, stats: {rune['stats']}")
        print("="*60 + "\n")
        
        if not self.selected_pickaxe_id or self.rune_slots <= 0:
            messagebox.showinfo("Optimize", "Select a pickaxe in Modify Parameters before optimizing.")
            return
        if len(self.runes) < self.rune_slots:
            messagebox.showinfo("Optimize", f"Add at least {self.rune_slots} runes before optimizing.")
            return

        # Calculate boost values based on checkboxes
        # Angel Race: +30% luck
        angel_race_bonus = 0.30 if getattr(self, 'angel_race', False) else 0.0
        # Supporter GP: +10% luck
        supporter_gp_bonus = 0.10 if getattr(self, 'supporter_gp', False) else 0.0
        # Luck Potion: +20% luck
        luck_potion_bonus = 0.20 if getattr(self, 'luck_potion', False) else 0.0
        # Luck Totem: +25% luck
        luck_totem_bonus = 0.25 if getattr(self, 'luck_totem', False) else 0.0
        
        # Mining Potion: +10% mining power, +15% swing speed
        mining_potion_power = 0.10 if getattr(self, 'mining_potion', False) else 0.0
        mining_potion_speed = 0.15 if getattr(self, 'mining_potion', False) else 0.0
        
        # Mining Totem: +15% mining power, +20% swing speed
        mining_totem_power = 0.15 if getattr(self, 'mining_totem', False) else 0.0
        mining_totem_speed = 0.20 if getattr(self, 'mining_totem', False) else 0.0
        
        # Fungi Potion: +15% mining power, +20% swing speed, +15% luck
        fungi_potion_power = 0.15 if getattr(self, 'fungi_potion', False) else 0.0
        fungi_potion_speed = 0.20 if getattr(self, 'fungi_potion', False) else 0.0
        fungi_potion_luck = 0.15 if getattr(self, 'fungi_potion', False) else 0.0

        # Lucky Cat Buff: +5% luck, +5% yield
        lucky_cat_luck = 0.05 if getattr(self, 'lucky_cat_buff', False) else 0.0
        lucky_cat_yield = 0.05 if getattr(self, 'lucky_cat_buff', False) else 0.0

        # Starite Buff: +4% luck, +6% yield
        starite_luck = 0.04 if getattr(self, 'starite_buff', False) else 0.0
        starite_yield = 0.06 if getattr(self, 'starite_buff', False) else 0.0
        
        # Total boost sums
        total_luck_boost = angel_race_bonus + supporter_gp_bonus + luck_potion_bonus + luck_totem_bonus + fungi_potion_luck + lucky_cat_luck + starite_luck
        total_mining_power_boost = mining_potion_power + mining_totem_power + fungi_potion_power
        total_swift_mining_boost = mining_potion_speed + mining_totem_speed + fungi_potion_speed
        total_yield_boost = lucky_cat_yield + starite_yield

        print(f"Boost Summary:")
        print(f"  Total Luck Boost: {total_luck_boost * 100:.0f}%")
        print(f"  Total Mining Power Boost: {total_mining_power_boost * 100:.0f}%")
        print(f"  Total Swift Mining Boost: {total_swift_mining_boost * 100:.0f}%")
        print("="*60 + "\n")

        best_combo = None
        best_score = float('inf')
        best_metrics = None
        best_title = None

        # Generate all combinations
        all_combos = list(combinations(self.runes, self.rune_slots))
        print(f"Total combinations found: {len(all_combos)}\n")
        
        combo_idx = 0
        for combo in all_combos:
            for title in ["Master Miner", "Dedicated Player"]:
                combo_idx += 1
                try:
                    print(f"--- Combination {combo_idx} ---")
                    combo_names = [rune['name'] for rune in combo]
                    print(f"Runes: {combo_names}")
                    
                    # Sums of attributes from runes
                    sum_luck = 0.0
                    sum_mining_power = 0.0
                    sum_swift_mining = 0.0
                    sum_yield = 0.0
                    for rune in combo:
                        for attr, val in rune.get("stats", []):
                            dec = float(val) / 100.0
                            if attr == "Luck":
                                sum_luck += dec
                            elif attr == "Mining Power":
                                sum_mining_power += dec
                            elif attr == "Swift Mining":
                                sum_swift_mining += dec
                            elif attr == "Yield":
                                sum_yield += dec
                    
                    # Add boost bonuses
                    sum_luck += total_luck_boost
                    sum_mining_power += total_mining_power_boost
                    sum_swift_mining += total_swift_mining_boost
                    # Add yield boost from buffs
                    sum_yield += total_yield_boost
                    
                    # Title bonuses
                    if title == "Master Miner":
                        sum_mining_power += self.master_miner_level * 0.05
                    elif title == "Dedicated Player":
                        sum_luck += self.dedicated_player_level * 0.08

                    # Effective variables
                    mining_power_eff = self.pickaxe_damage * (1 + sum_mining_power)
                    swing_time = 1.18 / (1 + self.pickaxe_speed_bonus + sum_swift_mining)
                    times_to_break_raw = self.hp_rock / mining_power_eff if mining_power_eff > 0 else float('inf')
                    times_to_break = math.ceil(times_to_break_raw)
                    t_per_rock = times_to_break * swing_time

                    # Effective luck
                    pickaxe_luck_decimal = self.pickaxe_luck / 100.0
                    luck_eff = 1 + pickaxe_luck_decimal + sum_luck
                    true_luck = self.rock_luck * luck_eff
                    
                    print(f"  sum_luck (with boosts): {sum_luck}")
                    print(f"  sum_mining_power (with boosts): {sum_mining_power}")
                    print(f"  sum_swift_mining (with boosts): {sum_swift_mining}")
                    print(f"  mining_power_eff: {mining_power_eff}")
                    print(f"  swing_time: {swing_time}")
                    print(f"  times_to_break: {times_to_break}")
                    print(f"  t_per_rock: {t_per_rock}")
                    print(f"  luck_eff: {luck_eff}")
                    print(f"  true_luck: {true_luck}")

                    # Base ore probability
                    prob_ore = min((self.chance_numerator * true_luck) / self.chance_denominator if self.chance_denominator > 0 else 0, 1)

                    # Yield effective
                    yield_eff = sum_yield

                    # ore_count scenarios
                    ore_counts = self.ore_count if isinstance(self.ore_count, list) and self.ore_count else [1]
                    k = len(ore_counts)
                    scenario_probability = 1.0 / k
                    prob_ore_per_rock = 0.0
                    for N in ore_counts:
                        p = prob_ore
                        succ = yield_eff * (1 - pow((1 - p), (N + 1))) + (1 - yield_eff) * (1 - pow((1 - p), N))
                        prob_ore_per_rock += scenario_probability * succ

                    # Average time per ore
                    if prob_ore_per_rock <= 1e-10:
                        average_t_per_ore = float('inf')
                    else:
                        average_t_per_ore = t_per_rock / prob_ore_per_rock
                    
                    print(f"  prob_ore: {prob_ore}")
                    print(f"  prob_ore_per_rock: {prob_ore_per_rock}")
                    print(f"  average_t_per_ore: {average_t_per_ore}")

                    # Select best (minimum average_t_per_ore)
                    if average_t_per_ore < best_score:
                        best_score = average_t_per_ore
                        best_combo = combo
                        best_title = title
                        best_metrics = {
                            'average_t_per_ore': average_t_per_ore,
                            'mining_power_eff': mining_power_eff,
                            'swing_time': swing_time,
                            'times_to_break': times_to_break,
                            't_per_rock': t_per_rock,
                            'luck_eff': luck_eff,
                            'true_luck': true_luck,
                            'prob_ore': prob_ore,
                            'prob_ore_per_rock': prob_ore_per_rock,
                            'sum_luck': sum_luck,
                            'sum_mining_power': sum_mining_power,
                            'sum_swift_mining': sum_swift_mining,
                            'sum_yield': sum_yield,
                            'total_luck_boost': total_luck_boost,
                            'total_mining_power_boost': total_mining_power_boost,
                            'total_swift_mining_boost': total_swift_mining_boost,
                            'total_yield_boost': total_yield_boost,
                        }
                except Exception as e:
                    print(f"ERROR in combination {combo_idx}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

        print(f"\nBest combination score: {best_score}")
        print("="*60 + "\n")
        
        if best_combo is None:
            messagebox.showinfo("Optimize", "No valid rune combination found.")
            return

        # Display results for best combo
        m = best_metrics
        
        # Build boost summary string
        boost_lines = []
        if m['total_luck_boost'] > 0:
            boost_lines.append(f"  Luck Boost: {m['total_luck_boost']*100:.0f}%")
        if m['total_mining_power_boost'] > 0:
            boost_lines.append(f"  Mining Power Boost: {m['total_mining_power_boost']*100:.0f}%")
        if m['total_swift_mining_boost'] > 0:
            boost_lines.append(f"  Swift Mining Boost: {m['total_swift_mining_boost']*100:.0f}%")
        if m.get('total_yield_boost', 0) > 0:
            boost_lines.append(f"  Yield Boost: {m['total_yield_boost']*100:.0f}%")
        
        boosts_msg = "\n".join(boost_lines) if boost_lines else "  None"
        
        msg = f"Average Time Per Ore: {m['average_t_per_ore']:.2f} s\n\n"
        msg += f"Title: {best_title}\n\n"
        msg += f"Active Boosts:\n{boosts_msg}\n\n"
        msg += "Runes:\n"
        for rune in best_combo:
            msg += f"  {rune['name']} - {rune['code']}\n"

        messagebox.showinfo("Optimization Result", msg)

    def open_modify_parameters_window(self):
        param_window = tk.Toplevel(self.root)
        param_window.title("Modify Parameters")
        param_window.geometry("500x500")
        param_window.resizable(False, False)
        param_window.transient(self.root)
        param_window.grab_set()

        pickaxe_display_names = list(self.pickaxes.keys())
        rock_display_names = [rock_data.get("display_name", rock_id) for rock_id, rock_data in self.rocks.items()]

        # Frame Pickaxe
        frame_pickaxe = ttk.Frame(param_window)
        frame_pickaxe.pack(fill="x", padx=15, pady=6)
        ttk.Label(frame_pickaxe, text="Pickaxe:", width=12).pack(side="left")
        pickaxe_var = tk.StringVar()
        pickaxe_combo = ttk.Combobox(frame_pickaxe, textvariable=pickaxe_var, values=pickaxe_display_names, state="readonly", width=25)
        pickaxe_combo.pack(side="left", padx=5)
        if self.selected_pickaxe_id and self.selected_pickaxe_id in pickaxe_display_names:
            pickaxe_combo.set(self.selected_pickaxe_id)

        # Frame Filter by World
        frame_world = ttk.Frame(param_window)
        frame_world.pack(fill="x", padx=15, pady=6)
        ttk.Label(frame_world, text="Filter:", width=12).pack(side="left")
        world_var = tk.StringVar(value=f"World {self.selected_world_num}")
        world_combo = ttk.Combobox(
            frame_world,
            textvariable=world_var,
            values=["World 1", "World 2", "World 3", "World 4"],
            state="readonly",
            width=25
        )
        world_combo.pack(side="left", padx=5)

        # Frame Rock
        frame_rock = ttk.Frame(param_window)
        frame_rock.pack(fill="x", padx=15, pady=6)
        ttk.Label(frame_rock, text="Rock:", width=12).pack(side="left")
        rock_var = tk.StringVar()
        rock_combo = ttk.Combobox(frame_rock, textvariable=rock_var, values=rock_display_names, state="readonly", width=25, height=12)
        rock_combo.pack(side="left", padx=5)

        # Frame Ore
        frame_ore = ttk.Frame(param_window)
        frame_ore.pack(fill="x", padx=15, pady=6)
        ttk.Label(frame_ore, text="Ore:", width=12).pack(side="left")
        ore_var = tk.StringVar()
        ore_combo = ttk.Combobox(frame_ore, textvariable=ore_var, values=[], state="readonly", width=25, height=10)
        ore_combo.pack(side="left", padx=5)

        # Frame for Checkboxes (Angel Race + Boosts) - Two columns
        frame_boosts = ttk.LabelFrame(param_window, text="Active Boosts", padding=5)
        frame_boosts.pack(fill="x", padx=15, pady=6)

        # Variables for checkboxes (False by default)
        self.angel_race_var = tk.BooleanVar(value=False)
        self.luck_potion_var = tk.BooleanVar(value=False)
        self.mining_potion_var = tk.BooleanVar(value=False)
        self.fungi_potion_var = tk.BooleanVar(value=False)
        self.luck_totem_var = tk.BooleanVar(value=False)
        self.mining_totem_var = tk.BooleanVar(value=False)
        self.supporter_gp_var = tk.BooleanVar(value=False)
        self.lucky_cat_buff_var = tk.BooleanVar(value=False)
        self.starite_buff_var = tk.BooleanVar(value=False)

        # Column 1
        col1 = ttk.Frame(frame_boosts)
        col1.pack(side="left", fill="x", expand=True, padx=5)
        
        ttk.Checkbutton(col1, text="Angel Race", variable=self.angel_race_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(col1, text="Luck Potion", variable=self.luck_potion_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(col1, text="Mining Potion", variable=self.mining_potion_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(col1, text="Fungi Potion", variable=self.fungi_potion_var).pack(anchor="w", pady=2)

        # Column 2
        col2 = ttk.Frame(frame_boosts)
        col2.pack(side="left", fill="x", expand=True, padx=5)

        ttk.Checkbutton(col2, text="Luck Totem", variable=self.luck_totem_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(col2, text="Mining Totem", variable=self.mining_totem_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(col2, text="Supporter GP", variable=self.supporter_gp_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(col2, text="Lucky Cat Buff", variable=self.lucky_cat_buff_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(col2, text="Starite Buff", variable=self.starite_buff_var).pack(anchor="w", pady=2)

        rock_display_to_id = {rock_data.get("display_name", rock_id): rock_id for rock_id, rock_data in self.rocks.items()}
        ore_display_to_id = {}

        def on_pickaxe_selected(event=None):
            pickaxe_id = pickaxe_var.get()
            if pickaxe_id not in self.pickaxes:
                self.selected_pickaxe_id = None
                self.rune_slots = 0
                return
            self.selected_pickaxe_id = pickaxe_id
            data = self.pickaxes[pickaxe_id]
            self.pickaxe_damage = data.get("pickaxe_damage", 0)
            self.pickaxe_speed_bonus = data.get("pickaxe_speed_bonus", 0)
            self.pickaxe_luck = data.get("pickaxe_luck", 0)
            self.rune_slots = data.get("rune_slots", 0)

        def select_current_rock_or_first(filtered_rocks):
            current_rock_display = rock_var.get()
            if current_rock_display in filtered_rocks:
                rock_combo.set(current_rock_display)
            elif filtered_rocks:
                rock_combo.set(filtered_rocks[0])
            else:
                rock_var.set("")
                self.selected_rock_id = None
                ore_combo.config(values=[])
                ore_var.set("")
                self.selected_ore_id = None
                self.chance_numerator = 0
                self.chance_denominator = 1
                return
            on_rock_selected()

        def filter_rocks_by_world(*args):
            selected_world = world_var.get()
            world_num = int(selected_world.split()[-1])
            self.selected_world_num = world_num
            filtered_rocks = [
                rock_data.get("display_name", rock_id) 
                for rock_id, rock_data in self.rocks.items()
                if rock_data.get("world") == world_num
            ]
            rock_combo.config(values=filtered_rocks)
            select_current_rock_or_first(filtered_rocks)

        def on_rock_selected(event=None):
            rock_display = rock_var.get()
            rock_id = rock_display_to_id.get(rock_display)
            if not rock_id:
                self.selected_rock_id = None
                ore_combo.config(values=[])
                ore_var.set("")
                self.selected_ore_id = None
                self.chance_numerator = 0
                self.chance_denominator = 1
                return
            self.selected_rock_id = rock_id
            rock_data = self.rocks.get(rock_id, {})
            self.hp_rock = rock_data.get("hp_rock", 0)
            self.rock_luck = rock_data.get("rock_luck", 0)
            ore_count_raw = rock_data.get("ore_count", 1)
            if isinstance(ore_count_raw, list):
                self.ore_count = ore_count_raw
            else:
                self.ore_count = [ore_count_raw]
            ore_ids = rock_data.get("ores", [])
            ore_display_names = [self.ores[ore_id]["display_name"] for ore_id in ore_ids if ore_id in self.ores]
            nonlocal ore_display_to_id
            ore_display_to_id = {self.ores[ore_id]["display_name"]: ore_id for ore_id in ore_ids if ore_id in self.ores}
            ore_combo.config(values=ore_display_names)

            current_ore_display = None
            if self.selected_ore_id in ore_display_to_id.values():
                for ore_display_name, ore_id in ore_display_to_id.items():
                    if ore_id == self.selected_ore_id:
                        current_ore_display = ore_display_name
                        break
            elif ore_display_names:
                current_ore_display = ore_display_names[0]

            if current_ore_display:
                ore_combo.set(current_ore_display)
                on_ore_selected()
            else:
                ore_var.set("")
                self.selected_ore_id = None
                self.chance_numerator = 0
                self.chance_denominator = 1

        def on_ore_selected(event=None):
            ore_display = ore_var.get()
            ore_id = ore_display_to_id.get(ore_display)
            if not ore_id:
                self.selected_ore_id = None
                self.chance_numerator = 0
                self.chance_denominator = 1
                return
            self.selected_ore_id = ore_id
            ore_data = self.ores.get(ore_id, {})
            self.chance_numerator = ore_data.get("chance_numerator", 0)
            self.chance_denominator = ore_data.get("chance_denominator", 1)

        pickaxe_combo.bind("<<ComboboxSelected>>", on_pickaxe_selected)
        rock_combo.bind("<<ComboboxSelected>>", on_rock_selected)
        ore_combo.bind("<<ComboboxSelected>>", on_ore_selected)
        world_combo.bind("<<ComboboxSelected>>", filter_rocks_by_world)

        if self.selected_rock_id and self.selected_rock_id in self.rocks:
            selected_rock_display = self.rocks[self.selected_rock_id].get("display_name", self.selected_rock_id)
            rock_var.set(selected_rock_display)
        if self.selected_ore_id and self.selected_ore_id in self.ores:
            selected_ore_display = self.ores[self.selected_ore_id].get("display_name", self.selected_ore_id)
            ore_var.set(selected_ore_display)

        if self.selected_rock_id and self.selected_rock_id in self.rocks:
            on_rock_selected()

        filter_rocks_by_world()

        # Separator
        ttk.Frame(param_window).pack(pady=5)
        ttk.Separator(param_window, orient="horizontal").pack(fill="x", padx=15, pady=5)

        # Achievement Skills
        ttk.Label(param_window, text="Achievement Skills:", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=15)

        achievement_frame = ttk.Frame(param_window)
        achievement_frame.pack(fill="x", padx=15, pady=8)

        # Master Miner row
        master_frame = ttk.Frame(achievement_frame)
        master_frame.pack(fill="x", pady=2)
        
        master_var = tk.StringVar(value=str(self.master_miner_level))
        
        ttk.Label(master_frame, text="Master Miner (Mining Power Boost)", width=28, anchor="w").pack(side="left")
        master_combo = ttk.Combobox(
            master_frame,
            textvariable=master_var,
            values=["1","2","3","4","5"],
            width=3,
            state="readonly"
        )
        master_combo.pack(side="left", padx=(5,2))
        ttk.Label(master_frame, text="/5").pack(side="left")

        # Dedicated Player row
        dedicated_frame = ttk.Frame(achievement_frame)
        dedicated_frame.pack(fill="x", pady=2)
        
        dedicated_var = tk.StringVar(value=str(self.dedicated_player_level))
        
        ttk.Label(dedicated_frame, text="Dedicated Player (Luck Boost)", width=28, anchor="w").pack(side="left")
        dedicated_combo = ttk.Combobox(
            dedicated_frame,
            textvariable=dedicated_var,
            values=["1","2","3","4","5"],
            width=3,
            state="readonly"
        )
        dedicated_combo.pack(side="left", padx=(5,2))
        ttk.Label(dedicated_frame, text="/5").pack(side="left")

        frame_actions = ttk.Frame(param_window)
        frame_actions.pack(side="bottom", anchor="e", fill="x", padx=15, pady=10)

        def save_parameters():
            if pickaxe_var.get() and pickaxe_var.get() in self.pickaxes:
                on_pickaxe_selected()
            if world_var.get():
                self.selected_world_num = int(world_var.get().split()[-1])
            if rock_var.get() and rock_var.get() in rock_display_to_id:
                on_rock_selected()
            if ore_var.get() and ore_var.get() in ore_display_to_id:
                on_ore_selected()
            self.master_miner_level = int(master_var.get())
            self.dedicated_player_level = int(dedicated_var.get())
            
            # Save boost variables to self so they can be used in optimize_runes
            self.angel_race = self.angel_race_var.get()
            self.luck_potion = self.luck_potion_var.get()
            self.mining_potion = self.mining_potion_var.get()
            self.fungi_potion = self.fungi_potion_var.get()
            self.luck_totem = self.luck_totem_var.get()
            self.mining_totem = self.mining_totem_var.get()
            self.supporter_gp = self.supporter_gp_var.get()
            self.lucky_cat_buff = self.lucky_cat_buff_var.get()
            self.starite_buff = self.starite_buff_var.get()
            
            param_window.destroy()

        btn_save = ttk.Button(frame_actions, text="Save Parameters", command=save_parameters)
        btn_save.pack(side="left", padx=5)

        btn_cancel = ttk.Button(frame_actions, text="Cancel", command=param_window.destroy)
        btn_cancel.pack(side="right", padx=5)

    def save_runes_to_file(self):
        """Save all runes to a JSON file"""
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Runas"
        )
        
        if file_path:
            try:
                # Prepare data to save
                runes_data = []
                for rune in self.runes:
                    runes_data.append({
                        'name': rune['name'],
                        'code': rune['code'],
                        'stats': rune['stats']
                    })
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(runes_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Save Runas", f"Runas saved successfully!\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save runas: {e}")

    def load_runes_from_file(self):
        """Load runes from a JSON file"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Runas"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    runes_data = json.load(f)
                
                # Clear current runes
                self.runes = []
                self.next_rune_number = 1
                
                # Load runes
                for rune_data in runes_data:
                    self.runes.append({
                        'name': rune_data['name'],
                        'code': rune_data['code'],
                        'stats': rune_data['stats']
                    })
                    # Update next_rune_number to avoid duplicate names
                    if rune_data['name'].startswith('Rune '):
                        try:
                            num = int(rune_data['name'].split()[1])
                            if num >= self.next_rune_number:
                                self.next_rune_number = num + 1
                        except:
                            pass
                
                self.update_rune_list()
                messagebox.showinfo("Load Runas", f"Loaded {len(self.runes)} runas successfully!\n{file_path}")
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load runas: {e}")
    def on_closing(self):
        """Auto-save runes when closing the program"""
        try:
            with open("runas_backup.json", 'w', encoding='utf-8') as f:
                runes_data = []
                for rune in self.runes:
                    runes_data.append({
                        'name': rune['name'],
                        'code': rune['code'],
                        'stats': rune['stats']
                    })
                json.dump(runes_data, f, indent=2, ensure_ascii=False)
        except:
            pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RuneOptimizerApp(root)
    root.mainloop()
