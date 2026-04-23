# Urban Heat Island Analysis Tool

A small Python project by Viraj that compares temperatures in urban and rural locations and shows the Urban Heat Island effect.

The project has two ways to run it:
* A command-line script for analysis
* A Streamlit web app for a simple browser demo

The web app includes:
* Light and dark theme toggle
* CSV upload validation (2 to 3 files)
* Data preview before running analysis
* Manual location selection (2 to 3 locations)
* Tabbed results view for tables, charts, and downloads
* Single-click ZIP download of all output files
* CSV template download for quick testing
* Reset button to clear temporary upload data

## What It Does

* Reads pre-downloaded CSV files for 2 to 3 locations
* Cleans the data and checks required columns
* Calculates average temperature by location
* Calculates the urban minus rural temperature difference
* Creates line and bar charts
* Exports CSV and Excel output files

## Tech Stack

* Python
* Pandas
* Matplotlib
* Streamlit
* Excel-compatible `.xlsx` output

## Input Format

Each CSV file in `data/` should include these columns:
* datetime
* temperature_c
* location_name
* location_type with values `urban` or `rural`

Example:
`2026-03-20 06:00,25.4,City Center,urban`

## Sample Data Included

The repository includes six ready-to-use sample CSV files in `data/`:
* city_center_urban.csv
* industrial_zone_urban.csv
* metro_core_urban.csv
* green_village_rural.csv
* lakeside_rural.csv
* highland_rural.csv

You can use these directly in the web app, or upload your own files in the same format.

## Download and Run

### Option 1: Clone from GitHub
1. Clone the repository.
2. Open the project folder.
3. Double-click `launch_web.bat`.
4. Open `http://localhost:8501` in your browser.

### Option 2: Download ZIP from GitHub
1. Download the repository as ZIP.
2. Extract it.
3. Double-click `launch_web.bat`.
4. Open `http://localhost:8501`.

## Live App (Cloud)

Once deployed, the app can be used directly on phone and desktop without installation.
Live URL: [Add your Streamlit link here]

### Deploy to Streamlit Community Cloud
1. Open Streamlit Community Cloud and sign in with GitHub.
2. Click New app.
3. Select repository: `Vivichanispoopyhead/Urban-Heat-Island-Analysis`.
4. Select branch: `main`.
5. Set main file path: `web_app.py`.
6. Click Deploy.
7. Copy the generated URL and paste it under Live URL above.

*Notes: Free-tier apps may sleep when inactive. First load after sleep can take a short while.*

## Command-Line Mode

If you want the terminal version, double-click `run_analysis.bat`.
You can also run it directly:
`python analysis.py --data-dir data --output-dir outputs --max-locations 3`

## Output Files

After a run, the project creates these files:
* combined_cleaned_data.csv
* average_by_location.csv
* urban_vs_rural_summary.csv
* uhi_summary.xlsx
* temperature_trends.png
* average_temperature_by_location.png
* urban_rural_difference.png

Web runs are saved in timestamped folders inside `outputs/`.

## Excel Use

Open `uhi_summary.xlsx` in Excel.
It contains these sheets:
* raw_data
* avg_by_location
* urban_vs_rural
