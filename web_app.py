from __future__ import annotations

import io
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import google.generativeai as genai

from analysis import (
    REQUIRED_COLUMNS,
    calculate_summary,
    export_outputs,
    load_temperature_files,
    plot_average_bar,
    plot_time_series,
    plot_urban_rural_diff,
    select_locations,
)


def ensure_temp_upload_dir(base_dir: Path) -> Path:
    temp_dir = base_dir / "temp_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def inject_styles(theme_mode: str) -> None:
    if theme_mode == "Dark":
        bg_gradient = "linear-gradient(180deg, #0b1220 0%, #0f172a 45%, #111827 100%)"
        card_bg = "rgba(15, 23, 42, 0.85)"
        border_color = "rgba(148, 163, 184, 0.28)"
        text_main = "#e5e7eb"
        text_soft = "#cbd5e1"
        pill_bg = "#1e293b"
        pill_text = "#bfdbfe"
        btn_bg = "#0ea5e9"
        btn_bg_hover = "#0284c7"
        btn_text = "#f8fafc"
        success_bg = "rgba(16, 185, 129, 0.14)"
        warn_bg = "rgba(245, 158, 11, 0.16)"
    else:
        bg_gradient = "linear-gradient(180deg, #f7fbff 0%, #ffffff 38%, #f4f6fb 100%)"
        card_bg = "rgba(255, 255, 255, 0.84)"
        border_color = "rgba(15, 23, 42, 0.08)"
        text_main = "#0f172a"
        text_soft = "#334155"
        pill_bg = "#eaf2ff"
        pill_text = "#173a73"
        btn_bg = "#0ea5e9"
        btn_bg_hover = "#0284c7"
        btn_text = "#f8fafc"
        success_bg = "rgba(16, 185, 129, 0.12)"
        warn_bg = "rgba(245, 158, 11, 0.12)"

    st.markdown(
        f"""
        <style>
            .block-container {{
                max-width: 1080px;
                padding-top: 1.4rem;
                padding-bottom: 2.6rem;
            }}
            .stApp {{
                background: {bg_gradient};
            }}
            .hero-card {{
                padding: 1.15rem 1.25rem;
                border-radius: 18px;
                border: 1px solid {border_color};
                background: {card_bg};
                box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
            }}
            .hero-card h1 {{
                color: {text_main};
                letter-spacing: -0.02em;
                font-size: 1.9rem;
            }}
            .feature-pill {{
                display: inline-block;
                padding: 0.36rem 0.74rem;
                margin: 0 0.4rem 0.4rem 0;
                border-radius: 999px;
                background: {pill_bg};
                color: {pill_text};
                font-size: 0.84rem;
                font-weight: 600;
            }}
            .section-title {{
                margin-top: 0.6rem;
                margin-bottom: 0.35rem;
                font-size: 1.05rem;
                font-weight: 700;
                color: {text_main};
            }}
            p, label, .stCaption, .stMarkdown, .stText {{
                color: {text_soft};
            }}
            div[data-testid="stMetric"] {{
                background: {card_bg};
                border: 1px solid {border_color};
                border-radius: 14px;
                padding: 0.6rem 0.75rem;
            }}
            .stButton > button, .stDownloadButton > button {{
                border-radius: 10px;
                border: none;
                background: {btn_bg};
                color: {btn_text};
                font-weight: 600;
                padding: 0.5rem 0.95rem;
            }}
            .stButton > button:hover, .stDownloadButton > button:hover {{
                background: {btn_bg_hover};
                color: {btn_text};
            }}
            div[data-baseweb="tab-list"] button {{
                font-weight: 600;
            }}
            div[data-baseweb="tab-list"] {{
                gap: 0.35rem;
            }}
            div[data-baseweb="tab-list"] button[aria-selected="true"] {{
                border-bottom: 2px solid {btn_bg};
            }}
            div[data-testid="stAlert"] {{
                border-radius: 12px;
                border: 1px solid {border_color};
            }}
            div[data-testid="stAlert"][kind="success"] {{
                background: {success_bg};
            }}
            div[data-testid="stAlert"][kind="warning"] {{
                background: {warn_bg};
            }}
            @media (max-width: 768px) {{
                .block-container {{
                    padding-top: 1rem;
                    padding-bottom: 1.3rem;
                }}
                .hero-card {{
                    padding: 0.95rem 1rem;
                    border-radius: 14px;
                }}
                .hero-card h1 {{
                    font-size: 1.45rem;
                }}
                .feature-pill {{
                    margin-bottom: 0.3rem;
                    font-size: 0.8rem;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def reset_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def save_uploaded_files(uploaded_files: list, target_dir: Path) -> None:
    reset_directory(target_dir)
    for uploaded_file in uploaded_files:
        (target_dir / uploaded_file.name).write_bytes(uploaded_file.getbuffer())


def validate_uploaded_files(uploaded_files: list) -> str | None:
    if not (2 <= len(uploaded_files) <= 3):
        return "Please upload 2 to 3 CSV files for comparison."

    for uploaded_file in uploaded_files:
        try:
            frame = pd.read_csv(io.BytesIO(uploaded_file.getvalue()))
        except Exception:
            return f"Could not read '{uploaded_file.name}'. Please upload a valid CSV file."

        missing = REQUIRED_COLUMNS - set(frame.columns)
        if missing:
            return (
                f"{uploaded_file.name} is missing required columns: "
                f"{', '.join(sorted(missing))}"
            )

    return None


def build_zip_bundle(output_dir: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in output_dir.glob("*"):
            if file_path.is_file():
                archive.write(file_path, arcname=file_path.name)
    buffer.seek(0)
    return buffer.read()


def build_template_csv() -> bytes:
    template = pd.DataFrame(
        {
            "datetime": ["2026-03-20 06:00", "2026-03-20 09:00", "2026-03-20 12:00"],
            "temperature_c": [25.4, 29.1, 33.8],
            "location_name": ["City Center", "City Center", "City Center"],
            "location_type": ["urban", "urban", "urban"],
        }
    )
    return template.to_csv(index=False).encode("utf-8")


def run_analysis(
    data_dir: Path,
    output_dir: Path,
    max_locations: int,
    chosen_locations: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    data = load_temperature_files(data_dir)

    if chosen_locations:
        if not (2 <= len(chosen_locations) <= 3):
            raise ValueError("Please choose between 2 and 3 locations.")
        available = set(data["location_name"].unique())
        missing_locations = [name for name in chosen_locations if name not in available]
        if missing_locations:
            raise ValueError(
                f"Selected locations not found in data: {', '.join(missing_locations)}"
            )
        selected = chosen_locations
    else:
        selected = select_locations(data, max_locations)

    filtered_data = data[data["location_name"].isin(selected)].copy()
    avg_by_location, urban_vs_rural = calculate_summary(filtered_data)

    export_outputs(filtered_data, avg_by_location, urban_vs_rural, output_dir)
    plot_time_series(filtered_data, output_dir)
    plot_average_bar(avg_by_location, output_dir)
    plot_urban_rural_diff(urban_vs_rural, output_dir)

    return filtered_data, avg_by_location, urban_vs_rural, selected


def get_preview_data(
    data_source: str,
    default_data_dir: Path,
    temp_upload_dir: Path,
    uploaded_files: list,
) -> tuple[pd.DataFrame | None, str | None]:
    try:
        if data_source == "Use CSV files from data folder":
            return load_temperature_files(default_data_dir), None

        if not uploaded_files:
            return None, None

        validation_error = validate_uploaded_files(uploaded_files)
        if validation_error:
            return None, validation_error

        save_uploaded_files(uploaded_files, temp_upload_dir)
        return load_temperature_files(temp_upload_dir), None
    except Exception as exc:
        return None, str(exc)

def generate_ai_plan(data_frame):
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Act as a city planner. Based on this temperature data, write a 3-paragraph Actionable Climate Resilience Plan to cool down the hardest-hit urban areas:\n\n{data_frame.to_string()}"
    response = model.generate_content(prompt)
    return response.text


def build_ui() -> None:
    st.set_page_config(page_title="Urban Heat Island Analysis Tool", layout="wide")

    with st.sidebar:
        st.header("Appearance")
        theme_mode = st.radio("Theme", options=["Light", "Dark"], index=1)

    inject_styles(theme_mode)

    st.markdown(
        """
        <div class="hero-card">
            <h1 style="margin:0 0 0.35rem 0;">Urban Heat Island Analysis Tool</h1>
            <p style="margin:0; font-size:1.02rem;">
                Compare urban and rural temperatures, generate charts, and export a polished report pack.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    feature_pills = "".join(
        f"<span class='feature-pill'>{label}</span>"
        for label in [
            "2-3 location comparison",
            "CSV upload or local data",
            "Excel + charts + ZIP download",
        ]
    )
    st.markdown(feature_pills, unsafe_allow_html=True)

    project_root = Path(__file__).resolve().parent
    default_data_dir = project_root / "data"
    outputs_dir = project_root / "outputs"
    temp_upload_dir = ensure_temp_upload_dir(project_root)

    with st.sidebar:
        st.header("Run Settings")
        data_source = st.radio(
            "Data source",
            options=["Use CSV files from data folder", "Upload CSV files"],
            index=0,
        )
        max_locations = st.slider("Max locations", min_value=2, max_value=3, value=3)
        st.download_button(
            label="Download CSV template",
            data=build_template_csv(),
            file_name="uhi_template.csv",
            mime="text/csv",
        )
        reset_requested = st.button("Reset app")

    if reset_requested:
        reset_directory(temp_upload_dir)
        st.rerun()

    uploaded_files = []
    if data_source == "Upload CSV files":
        st.markdown(
            "<div class='section-title'>Upload CSV Files</div>", unsafe_allow_html=True
        )
        st.caption(f"Required columns: {', '.join(sorted(REQUIRED_COLUMNS))}")
        uploaded_files = st.file_uploader(
            "Upload 2 to 3 CSV files",
            type=["csv"],
            accept_multiple_files=True,
        )

    preview_data, preview_error = get_preview_data(
        data_source=data_source,
        default_data_dir=default_data_dir,
        temp_upload_dir=temp_upload_dir,
        uploaded_files=uploaded_files,
    )

    chosen_locations: list[str] | None = None
    if preview_error:
        st.warning(preview_error)
    elif preview_data is not None:
        st.markdown(
            "<div class='section-title'>Data Preview</div>", unsafe_allow_html=True
        )
        location_options = sorted(
            preview_data["location_name"].drop_duplicates().tolist()
        )
        default_locations = location_options[:max_locations]
        chosen_locations = st.multiselect(
            "Choose 2 to 3 locations",
            options=location_options,
            default=default_locations,
            max_selections=3,
        )

        type_counts = preview_data["location_type"].value_counts().to_dict()
        st.caption(
            f"Rows loaded: {len(preview_data)} | "
            f"Urban rows: {type_counts.get('urban', 0)} | "
            f"Rural rows: {type_counts.get('rural', 0)}"
        )
        st.dataframe(preview_data.head(10), use_container_width=True)

    if st.button("Run Analysis", type="primary"):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = outputs_dir / f"web_run_{timestamp}"

            if data_source == "Use CSV files from data folder":
                data_dir = default_data_dir
            else:
                if not uploaded_files:
                    st.error("Please upload 2 to 3 CSV files first.")
                    return
                validation_error = validate_uploaded_files(uploaded_files)
                if validation_error:
                    st.error(validation_error)
                    return
                data_dir = temp_upload_dir
                save_uploaded_files(uploaded_files, data_dir)

            with st.spinner("Running analysis and generating charts..."):
                filtered_data, avg_by_location, urban_vs_rural, selected = run_analysis(
                    data_dir=data_dir,
                    output_dir=output_dir,
                    max_locations=max_locations,
                    chosen_locations=chosen_locations,
                )

            st.success("Analysis completed successfully.")
            st.write(f"Locations analyzed: {', '.join(selected)}")
            st.write(f"Output folder: {output_dir}")

            metric_values = urban_vs_rural.set_index("metric")["value"]
            urban_avg = float(metric_.get("urban_avg_temp_c", float("nan")))
            rural_avg = float(metric_values.get("rural_avg_temp_c", float("nan")))
            difference = float(
                metric_values.get("difference_urban_minus_rural_c", float("nan"))
            )

            col1, col2, col3 = st.columns(3)
            col1.metric("Urban Avg (C)", f"{urban_avg:.2f}")
            col2.metric("Rural Avg (C)", f"{rural_avg:.2f}")
            col3.metric("Urban - Rural (C)", f"{difference:.2f}")

            tab_tables, tab_charts, tab_downloads = st.tabs(
                ["Tables", "Charts", "Downloads"]
            )

            with tab_tables:
                st.subheader("Location Summary")
                st.dataframe(avg_by_location, use_container_width=True)
                st.subheader("Urban vs Rural Summary")
                st.dataframe(urban_vs_rural, use_container_width=True)
                
                st.subheader("AI Climate Resilience Plan")
                if st.button("Generate AI Plan"):
                    with st.spinner("Gemini is analyzing the temperature differentials..."):
                        ai_plan = generate_ai_plan(urban_vs_rural)
                        st.markdown(ai_plan)

                st.subheader("Cleaned Data")
                st.dataframe(filtered_data, use_container_width=True)

            with tab_charts:
                st.image(
                    str(output_dir / "temperature_trends.png"),
                    caption="Temperature Trends",
                )
                st.image(
                    str(output_dir / "average_temperature_by_location.png"),
                    caption="Average Temperature by Location",
                )
                st.image(
                    str(output_dir / "urban_rural_difference.png"),
                    caption="Urban vs Rural Difference",
                )

            with tab_downloads:
                for file_name in [
                    "combined_cleaned_data.csv",
                    "average_by_location.csv",
                    "urban_vs_rural_summary.csv",
                    "uhi_summary.xlsx",
                ]:
                    file_path = output_dir / file_name
                    mime = (
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        if file_name.endswith(".xlsx")
                        else "text/csv"
                    )
                    st.download_button(
                        label=f"Download {file_name}",
                        data=file_path.read_bytes(),
                        file_name=file_name,
                        mime=mime,
                    )

                st.download_button(
                    label="Download all outputs (ZIP)",
                    data=build_zip_bundle(output_dir),
                    file_name=f"uhi_outputs_{timestamp}.zip",
                    mime="application/zip",
                )

                st.caption("Tip: Open uhi_summary.xlsx in Excel for report submission.")

        except Exception as exc:
            st.error(f"Analysis failed: {exc}")


if __name__ == "__main__":
    build_ui()