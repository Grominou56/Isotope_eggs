import os
import pandas as pd
from tkinter import Tk, filedialog
from pandas.errors import EmptyDataError

def load_spreadsheets_from_folder():
    root = Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Select folder with Excel and ODS files")
    if not folder:
        return pd.DataFrame()

    dfs = []
    for file in os.listdir(folder):
        ext = os.path.splitext(file)[1].lower()
        if ext in ['.xlsx', '.xls', '.ods']:
            path = os.path.join(folder, file)
            try:
                engine = 'odf' if ext == '.ods' else None
                df = pd.read_excel(path, engine=engine)
                if df.empty:
                    raise EmptyDataError("Empty file.")
                df['source_file'] = file
                dfs.append(df)
            except EmptyDataError:
                print(f"Skipped empty file: {file}")
            except Exception as e:
                print(f"Error reading {file}: {e}")

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
