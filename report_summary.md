# Urban Heat Island Analysis Project Report

## Project Title

Urban Heat Island Analysis Tool

## Objective

To compare temperature differences between urban and rural areas using pre-downloaded temperature CSV files.

## Tools Used

- Python
- Pandas
- Matplotlib
- Streamlit
- Excel

## Dataset Description

Six sample locations are included:

- City Center, urban
- Industrial Zone, urban
- Metro Core, urban
- Green Village, rural
- Lakeside, rural
- Highland Fields, rural

Each CSV uses these columns:

- `datetime`
- `temperature_c`
- `location_name`
- `location_type`

## Workflow

1. Load the CSV files from `data/`.
2. Validate and clean the data.
3. Compare 2 to 3 locations.
4. Calculate average temperatures by location.
5. Calculate the urban minus rural temperature difference.
6. Generate line and bar charts.
7. Export CSV and Excel output files.
8. Show the results in a web app.

## Sample Result

- Urban average temperature: 31.15 C
- Rural average temperature: 27.19 C
- Urban minus rural difference: 3.96 C

This shows the expected Urban Heat Island pattern in the sample data.

## Output Files

- `outputs/combined_cleaned_data.csv`
- `outputs/average_by_location.csv`
- `outputs/urban_vs_rural_summary.csv`
- `outputs/uhi_summary.xlsx`
- `outputs/temperature_trends.png`
- `outputs/average_temperature_by_location.png`
- `outputs/urban_rural_difference.png`

## How to Run

### Web App

```bash
.venv\Scripts\python.exe -m streamlit run web_app.py --server.port 8501
```

Open `http://localhost:8501` in your browser.

### Command Line

```bash
.venv\Scripts\python.exe analysis.py
```

## Conclusion

The project is a simple but complete Urban Heat Island analysis tool that works both as a script and as a web app.
