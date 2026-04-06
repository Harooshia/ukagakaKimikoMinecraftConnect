# ukagakaKimikoMinecraftConnect

Kimiko is a Python desktop AI assistant with a floating ghost interface, mode-aware prompts, memory, and local web settings.

## Local Settings Dashboard

Run the local Flask dashboard:

```bash
pip install -r requirements.txt
python -m webui.app
```

Open `http://localhost:5000/settings`.

Pages included:
- Modules
- Model
- Memory
- Data

The dashboard persists to `settings.json` and is read dynamically by `KimikoCore`.

## Judgement Mode

`judgement` is a dedicated AI courtroom context called:

**JUDGEMENT SYSTEM // CLASSIFIED INTERFACE**

When switched to this context, Kimiko opens a separate floating window with a classified terminal aesthetic where users can submit case-style scenarios for evaluation.

### How it works

1. User submits a case via **CASE FILE INPUT**.
2. System generates an auto-incrementing **Case ID**.
3. A mandatory hybrid score is computed before any AI reasoning:
   - Harm keywords: `-30`
   - Severe harm keywords: `-50`
   - Positive keywords: `+20`
   - Justification keywords: `+10`
   - Sentiment polarity (lexicon-based): `polarity * 6`
4. Verdict mapping:
   - `> 20` → **NOT GUILTY**
   - `-20 to 20` → **UNCLEAR**
   - `< -20` → **GUILTY**
5. Structured AI analysis is then produced and rendered in a courtroom report panel.
6. For very short but unethical prompts, an ethics override can apply an additional negative boost so harmful intent is still surfaced clearly.

### Structured verdict output

The judgement panel renders:

- `VERDICT`
- `SEVERITY`
- `SCORE`
- `INTENT ANALYSIS`
- `CONSEQUENCE ANALYSIS`
- `FINAL REASONING`

### Features

- Context switching with mode menu integration.
- Independent desktop floating judgement window.
- Case archive list for previous verdicts.
- Clicking archive entries reloads that full case report from memory (including score) into the main verdict panel.
- Processing-state feedback:
  - `PROCESSING CASE...`
  - `ANALYSING INTENT...`
  - `FINALISING VERDICT...`
- Optional always-on-top toggle.
- Reprocess / clear / copy result controls.
- Existing Kimiko features remain intact (memory, TTS if enabled, Minecraft mode, and web settings dashboard).

### Technical highlights

- Hybrid reasoning architecture: keyword rules + sentiment signal + AI narrative analysis.
- Modular judgement implementation:
  - `Kimiko/judgement_ui.py`
  - `Kimiko/judgement_logic.py`
  - `Kimiko/judgement_memory.py`
- New mode context added to `KimikoCore` for clean prompt routing.
