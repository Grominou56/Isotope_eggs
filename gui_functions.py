import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk
from pandas.errors import EmptyDataError
import ezodf


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
    float_columns = [col for col in df.columns if pd.api.types.is_float_dtype(df[col])]

    # 1. Colonnes object éligibles
    eligible_columns = [
        col for col in df.columns
        if pd.api.types.is_object_dtype(df[col]) and df[col].nunique(dropna=False) <= max_unique_values
    ]

    if not eligible_columns and not float_columns:
        print("No eligible columns.")
        return df

    root = tk.Tk()
    root.title("Filter DataFrame by Values")
    root.geometry("600x700")

    # 2. Frame pour NaN dans colonnes float
    float_frame = tk.LabelFrame(root, text="Remove rows with NaN in selected float columns")
    float_frame.pack(fill="x", padx=10, pady=5)

    float_vars = {}
    for col in float_columns:
        var = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(float_frame, text=col, variable=var)
        cb.pack(anchor="w", padx=10)
        float_vars[col] = var

    # 3. Scrollable frame pour les colonnes object
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
            cb = tk.Checkbutton(frame, text=label, variable=var)
            cb.pack(anchor="w")
            checkbox_vars[col][val] = var

    def submit():
        for col, value_vars in checkbox_vars.items():
            selected = [val for val, var in value_vars.items() if var.get()]
            if selected:
                selected_values[col] = selected
        root.quit()

    # Bouton appliquer (fixe en bas)
    bottom_frame = tk.Frame(root)
    bottom_frame.pack(fill="x")
    submit_btn = tk.Button(bottom_frame, text="Apply Filter", command=submit)
    submit_btn.pack(pady=10)

    root.mainloop()
    root.destroy()

    # 4. Application des filtres object
    filtered_df = df.copy()

    for col, selected in selected_values.items():
        selected_nonan = [v for v in selected if v is not None]
        mask = filtered_df[col].isin(selected_nonan)

        if None in selected:
            mask |= filtered_df[col].isna()

        filtered_df = filtered_df[mask]

    # 5. Suppression des NaN dans colonnes float sélectionnées
    float_cols_to_drop = [col for col, var in float_vars.items() if var.get()]
    if float_cols_to_drop:
        filtered_df = filtered_df.dropna(subset=float_cols_to_drop)

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

""" Load an excel or libreoffice calc or csv file """

def load_table_file():
    # Initialize Tkinter window (hidden)
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Prompt the user to select a file
    file_path = filedialog.askopenfilename(
        title="Select a file", 
        filetypes=[("Excel files", "*.xlsx *.xls"), ("OSD files", "*.ods"), ("CSV files", "*.csv"), ("All files", "*.*")]
    )

    # Check if a file was selected
    if file_path:
        try:
            if file_path.endswith('.csv'):
                # Load CSV file
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                # Load Excel file
                df = pd.read_excel(file_path)
            elif file_path.endswith('.ods'):
                spreadsheet = ezodf.opendoc(file_path)
                sheet = spreadsheet.sheets[0]
                data = []
                for row in sheet.rows():
                    row_data = [cell.value for cell in row]
                    data.append(row_data)
                header = data[0]
                data = data[1:]
                df = pd.DataFrame(data, columns=header)
            else:
                print("Unsupported file type")
                return None
            
            print(f"File loaded successfully: {file_path}")
            return df
        except Exception as e:
            print(f"Error loading file: {e}")
            return None
    else:
        print("No file selected")
        return None
    

""" Open a windows that create a grid to entry fields and convert it to a pandas dataframe """

import tkinter as tk
from tkinter import messagebox
import pandas as pd

class ExcelLikeGridApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Excel-Like Table")
        self.entries = []

        # Frame for input and buttons
        input_frame = tk.Frame(master)
        input_frame.pack(pady=10, anchor="w")

        tk.Label(input_frame, text="Rows:").grid(row=0, column=0)
        self.row_entry = tk.Entry(input_frame, width=5)
        self.row_entry.grid(row=0, column=1)

        tk.Label(input_frame, text="Columns:").grid(row=0, column=2)
        self.col_entry = tk.Entry(input_frame, width=5)
        self.col_entry.grid(row=0, column=3)

        create_btn = tk.Button(input_frame, text="Create Table", command=self.create_table)
        create_btn.grid(row=0, column=4, padx=10)

        self.canvas_frame = tk.Frame(master)
        self.canvas_frame.pack(fill="both", expand=True)

        # Canvas + scrollbar
        self.canvas = tk.Canvas(self.canvas_frame)
        self.scrollbar = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Frame inside the canvas for table
        self.table_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.table_frame, anchor="nw")

        self.table_frame.bind("<Configure>", self.update_scroll_region)

        self.df_button = tk.Button(master, text="Convert to DataFrame", command=self.convert_to_dataframe)
        self.df_button.pack(pady=10)

    def update_scroll_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def create_table(self):
        # Clear previous table
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        self.entries = []

        try:
            rows = int(self.row_entry.get())
            cols = int(self.col_entry.get())
            if rows <= 0 or cols <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter positive integers for rows and columns.")
            return

        # Create the table grid
        for r in range(rows):
            row_entries = []
            for c in range(cols):
                entry = tk.Entry(self.table_frame, width=15)
                entry.grid(row=r, column=c, padx=1, pady=1)
                entry.bind("<Control-v>", self.paste_from_clipboard)
                entry.bind("<Command-v>", self.paste_from_clipboard)
                row_entries.append(entry)
            self.entries.append(row_entries)

        self.update_scroll_region()

    def paste_from_clipboard(self, event):
        try:
            clipboard = self.master.clipboard_get()
        except tk.TclError:
            return "break"

        start_widget = event.widget

        for r, row in enumerate(self.entries):
            if start_widget in row:
                start_row = r
                start_col = row.index(start_widget)
                break
        else:
            return "break"

        lines = clipboard.strip().split('\n')
        for i, line in enumerate(lines):
            cells = line.split('\t')
            for j, cell in enumerate(cells):
                r = start_row + i
                c = start_col + j
                if r < len(self.entries) and c < len(self.entries[0]):
                    entry = self.entries[r][c]
                    entry.delete(0, tk.END)
                    entry.insert(0, cell)

        return "break"

    def convert_to_dataframe(self):
        data = []
        for row_entries in self.entries:
            row_data = [entry.get() for entry in row_entries]
            data.append(row_data)

        df = pd.DataFrame(data)
        print("\nGenerated DataFrame:\n", df)

        # Show preview in a new Text widget
        top = tk.Toplevel(self.master)
        top.title("DataFrame Preview")
        text = tk.Text(top, wrap="none", width=100, height=20)
        text.insert("1.0", df.to_string(index=False))
        text.pack(padx=10, pady=10)

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x600")  # Optional: force initial window size
    app = ExcelLikeGridApp(root)
    root.mainloop()