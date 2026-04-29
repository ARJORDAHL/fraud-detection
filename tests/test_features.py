import pandas as pd
import pytest
from features import build_model_frame


@pytest.fixture
def sample_transactions():
    return pd.DataFrame({
        "transaction_id": [1, 2, 3, 4],
        "account_id": [10, 20, 10, 20],
        "amount_usd": [500.0, 1200.0, 80.0, 750.0],
        "failed_logins_24h": [0, 2, 3, 6],
    })


@pytest.fixture
def sample_accounts():
    return pd.DataFrame({
        "account_id": [10, 20],
        "prior_chargebacks": [0, 2],
        "country": ["US", "NG"],
    })


def test_build_model_frame_merges_account_fields(sample_transactions, sample_accounts):
    df = build_model_frame(sample_transactions, sample_accounts)
    assert "prior_chargebacks" in df.columns
    assert "country" in df.columns
    assert len(df) == len(sample_transactions)
    assert df.loc[df["account_id"] == 20, "prior_chargebacks"].iloc[0] == 2


def test_is_large_amount_flag(sample_transactions, sample_accounts):
    df = build_model_frame(sample_transactions, sample_accounts)
    assert df.loc[df["amount_usd"] == 1200.0, "is_large_amount"].iloc[0] == 1
    assert df.loc[df["amount_usd"] == 500.0, "is_large_amount"].iloc[0] == 0
    assert df.loc[df["amount_usd"] == 80.0, "is_large_amount"].iloc[0] == 0


def test_login_pressure_categories(sample_transactions, sample_accounts):
    df = build_model_frame(sample_transactions, sample_accounts)
    pressure = df.set_index("failed_logins_24h")["login_pressure"]
    assert str(pressure[0]) == "none"
    assert str(pressure[2]) == "low"
    assert str(pressure[3]) == "high"
    assert str(pressure[6]) == "high"
