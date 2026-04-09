# OpenModelica Simulation Runner

A desktop GUI application built with **Python + PyQt6** to launch OpenModelica-compiled simulation executables with configurable start and stop times.

Built as part of the **FOSSEE Summer Fellowship 2026** screening task.

---

## Screenshot

> Run the app and you'll see a dark-themed terminal-style interface with:
> - Executable browser
> - Start/Stop time inputs with built-in validation
> - Live simulation output console

---

## Features

- Browse and select any OpenModelica-compiled `.exe`
- Set start and stop time with enforced constraint: `0 ≤ start < stop < 5`
- Runs simulation in a **background thread** — GUI stays responsive
- Live output streaming to the console
- Error dialogs for invalid inputs or missing files

---

## Project Structure

```
OpenModelicaApp/
│
├── gui/
│   └── app.py               # Main PyQt6 application
│
├── executable/
│   ├── TwoConnectedTanks.exe
│   ├── TwoConnectedTanks.bat
│   ├── TwoConnectedTanks_init.xml
│   ├── TwoConnectedTanks_info.json
│   ├── TwoConnectedTanks_JacA.bin
│   ├── TwoConnectedTanks_res.mat
│   └── TwoConnectedTanks.log
│
└── README.md
```

---

## Requirements

- Python 3.6+
- PyQt6
- OpenModelica 1.26.3 (for compiling the model)
- Windows 10/11

---

## Installation

```bash
pip install PyQt6
```

---

## Usage

```bash
cd gui
python app.py
```

1. Click **Browse** and navigate to `executable/TwoConnectedTanks.exe`
2. Set **Start Time** (0–3) and **Stop Time** (1–4), ensuring `start < stop < 5`
3. Click **▶ Run Simulation**
4. View live output in the console panel

---

## Model: TwoConnectedTanks

The `TwoConnectedTanks` model is part of the `NonInteractingTanks` package. It simulates fluid dynamics between two connected tanks. The model was compiled using **OMEdit** (OpenModelica Connection Editor) v1.26.3.

The executable accepts simulation flags via the `-override` argument:

```bash
TwoConnectedTanks.exe -override=startTime=0,stopTime=4
```

Reference: [OpenModelica Simulation Flags](https://openmodelica.org/doc/OpenModelicaUsersGuide/latest/simulationflags.html#simflag-override)

---

## Design Decisions

- **OOP structure**: Logic split into `SimulationRunner` (main window) and `SimulationWorker` (QThread) — keeps UI and simulation concerns separate
- **Background thread**: Simulation runs in `QThread` so the GUI never freezes
- **Input validation**: All edge cases caught before execution (missing file, bad time range)
- **PEP8 compliant**: Follows Python style guidelines throughout
