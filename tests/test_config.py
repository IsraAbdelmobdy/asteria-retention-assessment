from pathlib import Path

import pytest

from asteria_retention.config import ConfigError, load_project_config


def test_checked_in_configuration_has_expected_contract():
    config = load_project_config(Path("."))

    indicators = config["indicators"]
    assert set(indicators["countries"]) == {"BG", "GR", "IE", "IT", "PL", "RO"}
    assert set(indicators["indicators"]) == {
        "unemployment_rate",
        "job_vacancy_rate",
        "consumer_price_inflation",
    }
    assert indicators["indicators"]["job_vacancy_rate"]["parameters"] == {
        "freq": "Q",
        "s_adj": "SA",
        "nace_r2": "B-S",
        "sizeclas": "TOTAL",
        "indic_em": "JVR",
    }
    assert indicators["indicators"]["unemployment_rate"]["ingestion_start"] == "2020-01"
    assert indicators["indicators"]["job_vacancy_rate"]["ingestion_start"] == "2020-Q1"


def test_missing_config_directory_has_clear_error(tmp_path):
    with pytest.raises(ConfigError, match="missing file"):
        load_project_config(tmp_path)
