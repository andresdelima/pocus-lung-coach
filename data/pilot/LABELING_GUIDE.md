# Pilot labeling guide

One row per file in `labels.csv`. Your labels are the ground truth the coach is compared against.

| Column | What to write |
|---|---|
| `file` | Filled in for you (path inside `images/`). |
| `target_view` | The card id the learner was aiming for (list below). The coach checks the image against it. |
| `true_view` | What the image really shows: usually the same id; another card id if it is a different view; `other` if it matches no card. Leave blank to copy `target_view`. |
| `region` | Optional: `anterior` or `lateral` chest, the region the learner tapped. Default: the card's first region (card 02 belongs to both). |
| `probe` | Optional: `linear`, `curvilinear` or `phased_array`. |
| `head_side` | Optional: `right` if the patient's head is on the right of the screen (default `left`). |
| `structures_missing` | Numbers of the target card's required structures that are **not** visible, separated by `;` (e.g. `2;4`). Leave blank if all are visible. |
| `author_subscores` | Optional: your five 0–2 scores as `L/O/D/G/I` (landmarks, orientation, depth, gain/focus, interpretability), e.g. `2/2/1/2/2`. |
| `author_grade` | Your 1–10 acquisition-quality grade, using the rubric: the plain sum of five 0–2 scores; landmarks 0 means uninterpretable, grade 1. |
| `notes` | Optional. |

Rows with an empty `author_grade` are skipped, so you can label a few at a time.

## Card ids and their required structures

**01 `anterior_pleura_longitudinal`**: Anterior chest, longitudinal intercostal view (bat sign)
  1. Two rib shadows
  2. Pleural line

**02 `intercostal_aeration`**: Intercostal (transverse) view: A-/B-lines and aeration score
  1. Continuous pleural line
  2. Enough depth

**03 `mmode_pleura`**: M-mode through the pleural line: sliding, lung point, lung pulse
  1. B-mode reference with cursor
  2. M-mode trace

**04 `posterolateral_plaps`**: Posterolateral / costophrenic view: effusion and consolidation (PLAPS)
  1. Liver or spleen
  2. Diaphragm
  3. Space above the diaphragm
  4. Lung tissue
  5. Chest wall
