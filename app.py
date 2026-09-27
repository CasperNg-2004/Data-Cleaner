"""Interactive CSV Data Cleaner Streamlit application."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from cleaner import (
    clean_column_names,
    clean_text_columns,
    convert_column,
    detect_invalid_values,
    detect_iqr_outliers,
    fill_missing,
    missing_summary,
    normalize_text,
    remove_duplicates,
)
from cleaner.text_cleaning import text_columns
from utils.file_handler import read_csv_safely
from utils.report_generator import cleaning_suggestions, dataset_metrics, generate_report

st.set_page_config(page_title="CSV Data Cleaner", page_icon="🧹", layout="wide")


def show_metrics(df: pd.DataFrame) -> None:
    metrics = dataset_metrics(df)
    columns = st.columns(4)
    columns[0].metric("Rows", f"{metrics['rows']:,}")
    columns[1].metric("Columns", f"{metrics['columns']:,}")
    columns[2].metric("Missing values", f"{metrics['missing']:,}")
    columns[3].metric("Duplicate rows", f"{metrics['duplicates']:,}")


def reset_for_file(name: str, data: bytes) -> None:
    signature = (name, len(data), hash(data))
    if st.session_state.get("file_signature") != signature:
        frame, encoding = read_csv_safely(data)
        st.session_state.update(
            file_signature=signature,
            filename=name,
            encoding=encoding,
            original_df=frame,
            cleaned_df=frame.copy(),
            history=[],
        )


def apply_cleaning() -> None:
    df = st.session_state.original_df.copy()
    history: list[str] = []
    name_mapping = {str(column): str(column) for column in df.columns}

    if st.session_state.standardize_names:
        old_names = list(map(str, df.columns))
        df, name_mapping = clean_column_names(df)
        changed = sum(old != new for old, new in zip(old_names, df.columns))
        if changed:
            history.append(f"Standardized {changed} column name(s): {name_mapping}")

    if st.session_state.remove_whitespace:
        df, changed = clean_text_columns(df)
        if changed:
            history.append(f"Cleaned whitespace in {changed} text cell(s)")

    normalization = st.session_state.text_normalization
    selected_text = [column for column in st.session_state.normalize_columns if column in df.columns]
    if normalization != "None" and selected_text:
        df, changed = normalize_text(df, selected_text, normalization.lower())
        history.append(
            f"Normalized {changed} value(s) to {normalization.lower()} case in {', '.join(selected_text)}"
        )

    if st.session_state.remove_dupes:
        subset = [column for column in st.session_state.duplicate_subset if column in df.columns]
        df, removed = remove_duplicates(df, subset=subset or None)
        history.append(f"Removed {removed} duplicate row(s)")

    for original_column, config in st.session_state.missing_configs.items():
        column = name_mapping[str(original_column)]
        if column not in df.columns or config["method"] == "leave unchanged":
            continue
        method = config["method"]
        df, changed = fill_missing(df, column, method, config.get("custom"))
        history.append(f"Handled {changed} missing value(s) in '{column}' using {method}")

    for original_column, target in st.session_state.type_configs.items():
        if target == "keep current":
            continue
        column = name_mapping[str(original_column)]
        if column in df.columns:
            df, introduced = convert_column(df, column, target)
            history.append(
                f"Converted '{column}' to {target}; {introduced} invalid value(s) became missing"
            )

    st.session_state.cleaned_df = df
    st.session_state.history = history


st.title("🧹 CSV Data Cleaner")
st.caption("Inspect, clean, compare, and export CSV data without changing the uploaded file.")
uploaded = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded is None:
    st.info("Upload a CSV file to begin. A sample dataset is included in `sample_data/`.")
    st.stop()

try:
    reset_for_file(uploaded.name, uploaded.getvalue())
except (ValueError, pd.errors.EmptyDataError) as exc:
    st.error(f"The CSV could not be read: {exc}")
    st.stop()

original = st.session_state.original_df
st.success(f"Loaded {uploaded.name} using {st.session_state.encoding} encoding.")

st.header("Dataset overview")
show_metrics(original)

overview_tab, missing_tab, quality_tab, stats_tab = st.tabs(
    ["Preview", "Missing values", "Quality checks", "Statistics"]
)
with overview_tab:
    st.dataframe(original.head(500), use_container_width=True)
    st.caption("Showing up to 500 rows.")
    st.dataframe(
        pd.DataFrame({"column": original.columns, "data_type": original.dtypes.astype(str)}),
        hide_index=True,
        use_container_width=True,
    )
with missing_tab:
    summary = missing_summary(original)
    st.dataframe(summary, hide_index=True, use_container_width=True)
    chart_data = summary[summary["missing_count"] > 0]
    if not chart_data.empty:
        st.plotly_chart(
            px.bar(chart_data, x="column", y="missing_count", title="Missing values by column"),
            use_container_width=True,
        )
with quality_tab:
    validations = detect_invalid_values(original)
    validation_rows = [
        {"column": column, "rule": result["rule"], "invalid_count": result["count"]}
        for column, result in validations.items()
    ]
    if validation_rows:
        st.dataframe(validation_rows, hide_index=True, use_container_width=True)
    else:
        st.info("No email, age, phone, or non-negative business rules could be inferred.")
    st.subheader("Automatic suggestions")
    for suggestion in cleaning_suggestions(original):
        st.write(f"• {suggestion}")
with stats_tab:
    numeric = original.select_dtypes(include="number")
    if numeric.empty:
        st.info("No numerical columns were detected.")
    else:
        st.dataframe(numeric.describe().T, use_container_width=True)

st.header("Configure cleaning")
basic_tab, missing_config_tab, types_tab, outliers_tab = st.tabs(
    ["Basic cleaning", "Missing values", "Type conversion", "Outliers"]
)
with basic_tab:
    st.checkbox("Standardize column names", value=True, key="standardize_names")
    st.checkbox("Remove extra whitespace", value=True, key="remove_whitespace")
    st.checkbox("Remove duplicate rows", value=True, key="remove_dupes")
    st.multiselect(
        "Duplicate matching columns (empty means entire row)",
        options=list(original.columns),
        key="duplicate_subset",
    )
    st.selectbox("Text capitalization", ["None", "Title", "Lower", "Upper"], key="text_normalization")
    st.multiselect(
        "Text columns to normalize",
        options=text_columns(original),
        key="normalize_columns",
    )

missing_configs: dict[str, dict[str, object]] = {}
with missing_config_tab:
    columns_with_missing = [column for column in original.columns if original[column].isna().any()]
    if not columns_with_missing:
        st.info("No missing values detected.")
    for column in columns_with_missing:
        numeric_column = pd.api.types.is_numeric_dtype(original[column])
        options = ["leave unchanged", "drop rows", "mode", "custom"]
        if numeric_column:
            options[2:2] = ["mean", "median"]
        else:
            options.insert(3, "unknown")
        left, right = st.columns([2, 1])
        method = left.selectbox(
            f"{column} ({int(original[column].isna().sum())} missing)",
            options,
            key=f"missing_{column}",
        )
        custom = right.text_input("Custom value", key=f"custom_{column}", disabled=method != "custom")
        missing_configs[column] = {"method": method, "custom": custom}
st.session_state.missing_configs = missing_configs

type_configs: dict[str, str] = {}
with types_tab:
    st.caption("Invalid numeric, date, or boolean values are converted to missing values.")
    for column in original.columns:
        type_configs[column] = st.selectbox(
            f"{column} · current: {original[column].dtype}",
            ["keep current", "numeric", "date", "text", "boolean"],
            key=f"type_{column}",
        )
st.session_state.type_configs = type_configs

with outliers_tab:
    numeric_columns = list(original.select_dtypes(include="number").columns)
    if not numeric_columns:
        st.info("Convert a column to numeric and clean the data to enable numeric outlier review.")
    else:
        outlier_column = st.selectbox("Numeric column", numeric_columns)
        multiplier = st.slider("IQR multiplier", 0.5, 3.0, 1.5, 0.1)
        outliers, bounds = detect_iqr_outliers(original, outlier_column, multiplier)
        st.write(f"Detected **{len(outliers)}** outlier(s); expected range: {bounds[0]:,.3g} to {bounds[1]:,.3g}.")
        st.dataframe(outliers, use_container_width=True)
        st.caption("Outliers are shown for review and are never removed automatically.")

if st.button("Clean dataset", type="primary", use_container_width=True):
    try:
        apply_cleaning()
    except (ValueError, TypeError, KeyError) as exc:
        st.error(f"Cleaning stopped: {exc}")
    else:
        st.success("Cleaning completed. Review the results below.")

if "cleaned_df" in st.session_state:
    cleaned = st.session_state.cleaned_df
    st.header("Before and after")
    before_col, after_col = st.columns(2)
    with before_col:
        st.subheader("Before")
        show_metrics(original)
        st.dataframe(original.head(200), use_container_width=True)
    with after_col:
        st.subheader("After")
        show_metrics(cleaned)
        st.dataframe(cleaned.head(200), use_container_width=True)

    st.subheader("Cleaning history")
    if st.session_state.history:
        for index, action in enumerate(st.session_state.history, 1):
            st.write(f"{index}. {action}")
    else:
        st.info("No cleaning changes have been applied yet.")

    safe_stem = uploaded.name.rsplit(".", 1)[0]
    report = generate_report(uploaded.name, original, cleaned, st.session_state.history)
    download_csv, download_report = st.columns(2)
    download_csv.download_button(
        "Download cleaned CSV",
        cleaned.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{safe_stem}_cleaned.csv",
        mime="text/csv",
        use_container_width=True,
    )
    download_report.download_button(
        "Download cleaning report",
        report,
        file_name=f"{safe_stem}_cleaning_report.txt",
        mime="text/plain",
        use_container_width=True,
    )
