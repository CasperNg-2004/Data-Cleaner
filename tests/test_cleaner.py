import pandas as pd
import pytest

from cleaner.duplicates import remove_duplicates
from cleaner.missing_values import fill_missing, missing_summary
from cleaner.outliers import detect_iqr_outliers
from cleaner.text_cleaning import clean_column_names, clean_text_columns, normalize_text
from cleaner.type_converter import convert_column
from cleaner.validator import detect_invalid_values
from utils.report_generator import cleaning_suggestions, dataset_metrics, generate_report


def test_column_names_are_clean_and_unique():
    frame = pd.DataFrame(columns=[" Customer Name ", "Customer-Name", "!!!"])
    cleaned, _ = clean_column_names(frame)
    assert list(cleaned.columns) == ["customer_name", "customer_name_2", "column"]


def test_text_cleaning_preserves_missing_values():
    frame = pd.DataFrame({"name": ["  Ada   Lovelace ", None], "age": [36, 20]})
    cleaned, changed = clean_text_columns(frame)
    assert cleaned.loc[0, "name"] == "Ada Lovelace"
    assert pd.isna(cleaned.loc[1, "name"])
    assert changed == 1


def test_normalize_text():
    cleaned, changed = normalize_text(pd.DataFrame({"country": ["MALAYSIA", None]}), ["country"], "title")
    assert cleaned.loc[0, "country"] == "Malaysia"
    assert changed == 1


def test_remove_duplicates_by_subset():
    frame = pd.DataFrame({"email": ["a@x.com", "a@x.com"], "value": [1, 2]})
    cleaned, removed = remove_duplicates(frame, ["email"])
    assert len(cleaned) == 1
    assert removed == 1


def test_missing_summary_and_median_fill():
    frame = pd.DataFrame({"age": [10.0, None, 30.0]})
    assert missing_summary(frame).loc[0, "missing_percent"] == pytest.approx(33.33)
    cleaned, count = fill_missing(frame, "age", "median")
    assert cleaned.loc[1, "age"] == 20
    assert count == 1


def test_mean_rejected_for_text():
    with pytest.raises(TypeError):
        fill_missing(pd.DataFrame({"city": ["KL", None]}), "city", "mean")


def test_custom_numeric_fill_is_coerced_and_validated():
    cleaned, _ = fill_missing(pd.DataFrame({"age": [1.0, None]}), "age", "custom", "42")
    assert cleaned.loc[1, "age"] == 42
    with pytest.raises(ValueError):
        fill_missing(pd.DataFrame({"age": [1.0, None]}), "age", "custom", "not a number")


def test_conversion_counts_new_missing_values():
    cleaned, introduced = convert_column(pd.DataFrame({"salary": ["10", "bad", None]}), "salary", "numeric")
    assert cleaned.loc[0, "salary"] == 10
    assert introduced == 1


def test_outliers_are_detected_without_mutation():
    frame = pd.DataFrame({"value": [10, 10, 11, 9, 100]})
    outliers, _ = detect_iqr_outliers(frame, "value")
    assert outliers["value"].tolist() == [100]
    assert len(frame) == 5


def test_inferred_validation_rules():
    frame = pd.DataFrame(
        {"age": [20, 150], "email": ["a@example.com", "bad"], "salary": [1, -2]}
    )
    result = detect_invalid_values(frame)
    assert result["age"]["count"] == 1
    assert result["email"]["count"] == 1
    assert result["salary"]["count"] == 1


def test_metrics_suggestions_and_report():
    before = pd.DataFrame({" Age ": [1, None, 1]})
    after = pd.DataFrame({"age": [1, 1]})
    assert dataset_metrics(before)["missing"] == 1
    assert any("column name" in suggestion for suggestion in cleaning_suggestions(before))
    report = generate_report("test.csv", before, after, ["Cleaned data"])
    assert "test.csv" in report
    assert "Cleaned data" in report
