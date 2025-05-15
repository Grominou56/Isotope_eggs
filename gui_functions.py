import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk
from pandas.errors import EmptyDataError


""" Load all spreadsheets from a folder and create a unique Pandas dataframe """

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

""" Clean datasets by various selections """

def filter_dataframe_by_checkboxes(df, max_unique_values=10):
    selected_values = {}
    float_columns = [col for col in df.columns if df[col].dtype == 'float64']

    # Step 1: Get eligible object columns
    eligible_columns = [
        col for col in df.columns
        if df[col].dtype == 'object' and df[col].nunique(dropna=False) <= max_unique_values
    ]

    if not eligible_columns and not float_columns:
        print("No eligible object or float columns.")
        return df

    # Step 2: Tkinter window
    root = tk.Tk()
    root.title("Filter DataFrame by Values")
    root.geometry("600x700")

    # Frame for float column NaN removal options
    float_frame = tk.LabelFrame(root, text="Remove rows with NaN in selected float columns")
    float_frame.pack(fill="x", padx=10, pady=5)

    float_vars = {}
    for col in float_columns:
        var = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(float_frame, text=col, variable=var)
        cb.pack(anchor="w", padx=10)
        float_vars[col] = var

    # Outer layout: scrollable top + fixed bottom
    outer_frame = tk.Frame(root)
    outer_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(outer_frame)
    scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Store checkbox variables per object column
    checkbox_vars = {}

    for col in eligible_columns:
        tk.Label(scrollable_frame, text=f"{col}:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        frame = tk.Frame(scrollable_frame)
        frame.pack(anchor="w", padx=20, pady=2)

        values = df[col].dropna().unique().tolist()
        if df[col].isnull().any():
            values.append(None)

        checkbox_vars[col] = {}
        for val in values:
            label = str(val) if val is not None else "<NaN>"
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(frame, text=label, variable=var, anchor="w")
            cb.pack(anchor="w")
            checkbox_vars[col][val] = var

    # Submit logic
    def submit():
        for col, value_vars in checkbox_vars.items():
            selected = [
                val for val, var in value_vars.items()
                if var.get()
            ]
            if selected:
                selected_values[col] = selected
        root.quit()

    # Fixed submit button
    bottom_frame = tk.Frame(root)
    bottom_frame.pack(fill="x")
    submit_btn = tk.Button(bottom_frame, text="Apply Filter", command=submit)
    submit_btn.pack(pady=10)

    root.mainloop()
    root.destroy()

    # Step 3: Apply filters
    filtered_df = df.copy()
    columns_used = []

    for col, selected in selected_values.items():
        columns_used.append(col)
        if any(v is None for v in selected):
            filtered_df = filtered_df[
                filtered_df[col].isin([v for v in selected if v is not None]) | filtered_df[col].isna()
            ]
        else:
            filtered_df = filtered_df[filtered_df[col].isin(selected)]

    # Step 4: Drop rows with NaN in selected float columns
    float_cols_to_dropna = [col for col, var in float_vars.items() if var.get()]
    if float_cols_to_dropna:
        filtered_df = filtered_df.dropna(subset=float_cols_to_dropna)

    return filtered_df


""" Load a geotiff file """

def load_file():
    # Create a Tkinter root window (it won't be shown)
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    root.call('wm', 'attributes', '.', '-topmost', True)  # Bring the file dialog to the front
    
    # Open the file dialog to select geotiff file
    file_path = filedialog.askopenfilename(
        title="Select a geotiff or netCDF file",
        filetypes=[
            ("All files", "*.*"), ("geotiff", "*.tif"), ("NetCDF", "*.nc")
        ]
    )
    if file_path:        
        print(f"Selected file: {file_path}")
        return file_path


""" Load a folder """

def load_folder():
    # Create a Tkinter root window (it won't be shown)
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    root.call('wm', 'attributes', '.', '-topmost', True)  # Bring the file dialog to the front
    
    # Open the file dialog to select geotiff folder
    folder_path = filedialog.askdirectory()

    print(f"Selected folder: {folder_path}")
    return folder_path