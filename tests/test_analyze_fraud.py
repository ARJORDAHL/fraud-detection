import pandas as pd
import pytest
from analyze_fraud import load_inputs, score_transactions, summarize_results


# ---------------------------------------------------------------------------
# summarize_results unit tests
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_scored():
    return pd.DataFrame({
        "transaction_id": [1, 2, 3, 4],
        "risk_label": ["high", "high", "low", "low"],
        "amount_usd": [500.0, 300.0, 100.0, 200.0],
    })


@pytest.fixture
def minimal_chargebacks():
    return pd.DataFrame({"transaction_id": [1]})


def test_summarize_results_row_counts(minimal_scored, minimal_chargebacks):
    summary = summarize_results(minimal_scored, minimal_chargebacks)
    high = summary.loc[summary["risk_label"] == "high"].iloc[0]
    low = summary.loc[summary["risk_label"] == "low"].iloc[0]
    assert high["transactions"] == 2
    assert low["transactions"] == 2


def test_summarize_results_chargeback_rate(minimal_scored, minimal_chargebacks):
    summary = summarize_results(minimal_scored, minimal_chargebacks)
    high = summary.loc[summary["risk_label"] == "high"].iloc[0]
    low = summary.loc[summary["risk_label"] == "low"].iloc[0]
    assert high["chargeback_rate"] == pytest.approx(0.5)
    assert low["chargeback_rate"] == pytest.approx(0.0)


def test_summarize_results_amount_totals(minimal_scored, minimal_chargebacks):
    summary = summarize_results(minimal_scored, minimal_chargebacks)
    high = summary.loc[summary["risk_label"] == "high"].iloc[0]
    assert high["total_amount_usd"] == pytest.approx(800.0)
    assert high["avg_amount_usd"] == pytest.approx(400.0)


# ---------------------------------------------------------------------------
# Integration tests using the real data files
# ---------------------------------------------------------------------------

CONFIRMED_FRAUD_IDS = {50003, 50006, 50008, 50011, 50013, 50014, 50015, 50019}

# Transactions with no chargeback, domestic, low amount, clean device
CLEARLY_CLEAN_IDS = {50001, 50009, 50012, 50016, 50020}


@pytest.fixture(scope="module")
def scored_real():
    accounts, transactions, _ = load_inputs()
    return score_transactions(transactions, accounts)


def test_confirmed_fraud_not_labeled_low(scored_real):
    fraud_rows = scored_real[scored_real["transaction_id"].isin(CONFIRMED_FRAUD_IDS)]
    low_fraud = fraud_rows[fraud_rows["risk_label"] == "low"]
    assert len(low_fraud) == 0, (
        f"Fraud transactions labeled low: {low_fraud['transaction_id'].tolist()}"
    )


def test_confirmed_fraud_scores_above_threshold(scored_real):
    fraud_rows = scored_real[scored_real["transaction_id"].isin(CONFIRMED_FRAUD_IDS)]
    below_threshold = fraud_rows[fraud_rows["risk_score"] < 30]
    assert len(below_threshold) == 0, (
        f"Fraud transactions scored below 30: {below_threshold[['transaction_id', 'risk_score']].to_dict('records')}"
    )


def test_clean_low_risk_transactions_score_low(scored_real):
    clean_rows = scored_real[scored_real["transaction_id"].isin(CLEARLY_CLEAN_IDS)]
    not_low = clean_rows[clean_rows["risk_label"] != "low"]
    assert len(not_low) == 0, (
        f"Clean transactions not labeled low: {not_low[['transaction_id', 'risk_score', 'risk_label']].to_dict('records')}"
    )


def test_high_bucket_chargeback_rate(scored_real):
    accounts, transactions, chargebacks = load_inputs()
    summary = summarize_results(scored_real, chargebacks)
    high = summary.loc[summary["risk_label"] == "high"]
    assert len(high) == 1, "Expected a 'high' risk bucket in output"
    assert high.iloc[0]["chargeback_rate"] == pytest.approx(1.0), (
        "All high-risk transactions should be confirmed fraud"
    )
