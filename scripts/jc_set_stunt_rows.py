"""Headless: change single cells of stunt DataTables without touching any other row.

JC_ROWS_JSON='{"/Game/Data/Scenes/DT_Stunts_S1": {"S1-6": {"TOff": "36.7", "C0": "0.7"}}}'
Reads every column of the live table (so rows edited after jc_make_data.py are kept), applies the overrides,
refills the table from that CSV, saves it, and re-reads it to prove the change. Lines go to JC_REPORT=/abs/file
(print() is swallowed under -nullrhi). Run via UnrealEditor-Cmd -ExecCmds="py <this>" (editor closed).
"""
import csv
import io
import json
import os

import unreal

DTL = unreal.DataTableFunctionLibrary


def say(line):
    print(line)
    if os.environ.get("JC_REPORT"):
        with open(os.environ["JC_REPORT"], "a") as fh:
            fh.write(line + "\n")


def table(dt):
    names = [str(n) for n in DTL.get_data_table_row_names(dt)]
    cols = [str(c) for c in DTL.get_data_table_column_export_names(dt)]
    data = {c: [str(v) for v in DTL.get_data_table_column_as_string(dt, c)] for c in cols}
    return names, cols, {n: {c: data[c][i] for c in cols} for i, n in enumerate(names)}


try:
    spec = json.loads(os.environ["JC_ROWS_JSON"])
    for path, rows in spec.items():
        dt = unreal.EditorAssetLibrary.load_asset(path)
        names, cols, cells = table(dt)
        for row, change in rows.items():
            if row not in cells:
                raise KeyError(f"{path}: no row {row}")
            for col, val in change.items():
                if col not in cols:
                    raise KeyError(f"{path}: no column {col}")
                say(f"JC_ROWS {path} {row}.{col}: {cells[row][col]} -> {val}")
                cells[row][col] = val
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(["Name"] + cols)
        for n in names:
            w.writerow([n] + [cells[n][c] for c in cols])
        ok = DTL.fill_data_table_from_csv_string(dt, buf.getvalue())
        saved = unreal.EditorAssetLibrary.save_loaded_asset(dt)
        names2, _, cells2 = table(dt)
        same_rows = names2 == names
        bad = [f"{r}.{c}" for r, ch in rows.items() for c, v in ch.items() if abs(float(cells2[r][c]) - float(v)) > 1e-4]
        untouched = all(cells2[n][c] == cells[n][c] for n in names if n not in rows for c in cols)
        say(f"JC_ROWS {'OK' if ok and saved and same_rows and not bad and untouched else 'FAIL'} {path} fill={ok} "
            f"saved={saved} rows={len(names2)} same_rows={same_rows} mismatched={bad} others_untouched={untouched}")
except Exception as exc:  # noqa: BLE001
    say(f"JC_ROWS FAIL {exc!r}")
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
