import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk
from pandas.errors import EmptyDataError


""" Load spreadsheets and create Pandas dataframe """

def load_spreadsheets_from_folder():
    root = tk.Tk()
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


""" Select only relevant columns """

def select_columns_gui(df, max_button_width=15, max_window_height=500, min_button_padding=20):
    selected_cols = []

    def toggle_column(col_name):
        if col_name in selected_cols:
            selected_cols.remove(col_name)
            buttons[col_name].config(relief="raised", bg="SystemButtonFace")
        else:
            selected_cols.append(col_name)
            buttons[col_name].config(relief="sunken", bg="lightblue")

    def submit():
        root.quit()

    # --- Layout sizing logic ---
    column_names = list(df.columns)
    max_col_len = max(len(str(col)) for col in column_names)
    button_pixel_width = max_col_len * 7 + min_button_padding
    buttons_per_row = max(1, min(6, 1000 // button_pixel_width))  # max ~6 per row
    total_width = min(1000, buttons_per_row * button_pixel_width + 50)

    # --- Main window ---
    root = tk.Tk()
    root.title("Select Columns")
    root.geometry(f"{total_width}x{max_window_height}")

    # --- Outer layout: top (scrollable) + bottom (submit) ---
    outer_frame = tk.Frame(root)
    outer_frame.pack(fill="both", expand=True)

    # --- Canvas + Scrollbar setup ---
    canvas = tk.Canvas(outer_frame, width=total_width)
    scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # --- Create scrollable frame ---
    scrollable_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # --- Ensure canvas resizes properly ---
    def update_scrollregion(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    scrollable_frame.bind("<Configure>", update_scrollregion)

    # --- Fill with buttons ---
    buttons = {}
    for i, col in enumerate(column_names):
        row = i // buttons_per_row
        col_pos = i % buttons_per_row
        btn = tk.Button(scrollable_frame, text=col, width=max_button_width, command=lambda c=col: toggle_column(c))
        btn.grid(row=row, column=col_pos, padx=5, pady=5)
        buttons[col] = btn

    # --- Submit button, fixed at bottom ---
    submit_frame = tk.Frame(root)
    submit_frame.pack(fill="x")
    submit_btn = tk.Button(submit_frame, text="Submit", command=submit)
    submit_btn.pack(pady=10)

    # --- Final setup ---
    root.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

    root.mainloop()
    root.destroy()

    return df[selected_cols]

