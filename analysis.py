from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import pandas as pd


matplotlib.use("Agg")
import matplotlib.pyplot as plt


REQUIRED_COLUMNS = {"datetime", "temperature_c", "location_name", "location_type"}


def load_temperature_files(data_dir: Path) -> pd.DataFrame:
    files = sorted(data_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No CSV files found in '{data_dir}'. Add pre-downloaded temperature CSV files first."
        )

    frames: list[pd.DataFrame] = []
    for csv_file in files:
        frame = pd.read_csv(csv_file)
        missing = REQUIRED_COLUMNS - set(frame.columns)
        if missing:
            raise ValueError(
                f"{csv_file.name} is missing required columns: {', '.join(sorted(missing))}"
            )
        frame["source_file"] = csv_file.name
        frames.append(frame)

    data = pd.concat(frames, ignore_index=True)
    data["datetime"] = pd.to_datetime(data["datetime"], errors="coerce")
    data["temperature_c"] = pd.to_numeric(data["temperature_c"], errors="coerce")
    data["location_type"] = data["location_type"].astype(str).str.strip().str.lower()

    data = data.dropna(
        subset=["datetime", "temperature_c", "location_name", "location_type"]
    )
    data = data[data["location_type"].isin(["urban", "rural"])]

    if data.empty:
        raise ValueError("No valid rows found after cleaning. Check your CSV content.")

    return data


def select_locations(data: pd.DataFrame, max_locations: int) -> list[str]:
    unique_locations = data["location_name"].drop_duplicates().tolist()
    if len(unique_locations) < 2:
        raise ValueError("At least 2 distinct locations are required for comparison.")
    return unique_locations[:max_locations]


def calculate_summary(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    location_types = set(data["location_type"].dropna().str.lower())
    if "urban" not in location_types or "rural" not in location_types:
        raise ValueError(
            "Data must include both urban and rural rows to compute UHI difference."
        )

    avg_by_location = (
        data.groupby(["location_name", "location_type"], as_index=False)[
            "temperature_c"
        ]
        .mean()
        .rename(columns={"temperature_c": "avg_temperature_c"})
        .sort_values("avg_temperature_c", ascending=False)
    )

    urban_mean = data.loc[data["location_type"] == "urban", "temperature_c"].mean()
    rural_mean = data.loc[data["location_type"] == "rural", "temperature_c"].mean()

    urban_vs_rural = pd.DataFrame(
        {
            "metric": [
                "urban_avg_temp_c",
                "rural_avg_temp_c",
                "difference_urban_minus_rural_c",
            ],
            "value": [urban_mean, rural_mean, urban_mean - rural_mean],
        }
    )

    return avg_by_location, urban_vs_rural


def plot_time_series(data: pd.DataFrame, output_dir: Path) -> None:
    plt.figure(figsize=(10, 5))
    for location_name, subset in data.groupby("location_name"):
        series = (
            subset.sort_values("datetime")
            .groupby("datetime", as_index=False)["temperature_c"]
            .mean()
        )
        plt.plot(
            series["datetime"], series["temperature_c"], marker="o", label=location_name
        )

    plt.title("Temperature Trend by Location")
    plt.xlabel("Date-Time")
    plt.ylabel("Temperature (C)")
    plt.xticks(rotation=30)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "temperature_trends.png", dpi=150)
    plt.close()


def plot_average_bar(avg_by_location: pd.DataFrame, output_dir: Path) -> None:
    chart_data = avg_by_location.copy()
    chart_data["label"] = (
        chart_data["location_name"] + " (" + chart_data["location_type"] + ")"
    )

    plt.figure(figsize=(8, 5))
    plt.bar(chart_data["label"], chart_data["avg_temperature_c"])
    plt.title("Average Temperature by Location")
    plt.xlabel("Location")
    plt.ylabel("Average Temperature (C)")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(output_dir / "average_temperature_by_location.png", dpi=150)
    plt.close()


def plot_urban_rural_diff(urban_vs_rural: pd.DataFrame, output_dir: Path) -> None:
    rows = urban_vs_rural.set_index("metric")
    if {
        "urban_avg_temp_c",
        "rural_avg_temp_c",
        "difference_urban_minus_rural_c",
    }.issubset(rows.index):
        values = [
            float(rows.loc["urban_avg_temp_c", "value"]),
            float(rows.loc["rural_avg_temp_c", "value"]),
            float(rows.loc["difference_urban_minus_rural_c", "value"]),
        ]

        plt.figure(figsize=(7, 5))
        plt.bar(["Urban Avg", "Rural Avg", "Urban - Rural"], values)
        plt.title("Urban vs Rural Temperature Difference")
        plt.ylabel("Temperature (C)")
        plt.tight_layout()
        plt.savefig(output_dir / "urban_rural_difference.png", dpi=150)
        plt.close()


def export_outputs(
    data: pd.DataFrame,
    avg_by_location: pd.DataFrame,
    urban_vs_rural: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    data.to_csv(output_dir / "combined_cleaned_data.csv", index=False)
    avg_by_location.to_csv(output_dir / "average_by_location.csv", index=False)
    urban_vs_rural.to_csv(output_dir / "urban_vs_rural_summary.csv", index=False)

    excel_path = output_dir / "uhi_summary.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        data.to_excel(writer, sheet_name="raw_data", index=False)
        avg_by_location.to_excel(writer, sheet_name="avg_by_location", index=False)
        urban_vs_rural.to_excel(writer, sheet_name="urban_vs_rural", index=False)


def run(data_dir: Path, output_dir: Path, max_locations: int) -> None:
    data = load_temperature_files(data_dir)
    chosen_locations = select_locations(data, max_locations)
    data = data[data["location_name"].isin(chosen_locations)]

    avg_by_location, urban_vs_rural = calculate_summary(data)

    export_outputs(data, avg_by_location, urban_vs_rural, output_dir)
    plot_time_series(data, output_dir)
    plot_average_bar(avg_by_location, output_dir)
    plot_urban_rural_diff(urban_vs_rural, output_dir)

    print("Urban Heat Island analysis complete.")
    print(f"Locations analyzed: {', '.join(chosen_locations)}")
    print(f"Output folder: {output_dir.resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simplified Urban Heat Island Analysis Tool"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Folder containing pre-downloaded CSV files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Folder where charts and summary files are saved",
    )
    parser.add_argument(
        "--max-locations",
        type=int,
        default=3,
        help="Maximum number of locations to compare (recommended: 2-3)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.data_dir, args.output_dir, args.max_locations)
