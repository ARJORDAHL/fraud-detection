from risk_rules import label_risk, score_transaction


def _base_tx(**overrides):
    tx = {
        "device_risk_score": 10,
        "is_international": 0,
        "amount_usd": 100,
        "velocity_24h": 1,
        "failed_logins_24h": 0,
        "prior_chargebacks": 0,
    }
    tx.update(overrides)
    return tx


def test_label_risk_thresholds():
    assert label_risk(10) == "low"
    assert label_risk(35) == "medium"
    assert label_risk(75) == "high"


def test_large_amount_adds_risk():
    assert score_transaction(_base_tx(amount_usd=1200)) >= 25


def test_high_device_risk_adds_risk():
    low = score_transaction(_base_tx(device_risk_score=10))
    high = score_transaction(_base_tx(device_risk_score=75))
    assert high > low


def test_international_adds_risk():
    domestic = score_transaction(_base_tx(is_international=0))
    international = score_transaction(_base_tx(is_international=1))
    assert international > domestic


def test_high_velocity_adds_risk():
    low_v = score_transaction(_base_tx(velocity_24h=1))
    high_v = score_transaction(_base_tx(velocity_24h=8))
    assert high_v > low_v


def test_prior_chargebacks_add_risk():
    clean = score_transaction(_base_tx(prior_chargebacks=0))
    one = score_transaction(_base_tx(prior_chargebacks=1))
    two = score_transaction(_base_tx(prior_chargebacks=2))
    assert one > clean
    assert two > one


def test_medium_device_risk_adds_risk():
    none = score_transaction(_base_tx(device_risk_score=10))
    medium = score_transaction(_base_tx(device_risk_score=50))
    assert medium > none


def test_medium_amount_adds_risk():
    low = score_transaction(_base_tx(amount_usd=100))
    medium = score_transaction(_base_tx(amount_usd=750))
    large = score_transaction(_base_tx(amount_usd=1500))
    assert medium > low
    assert large > medium


def test_medium_velocity_adds_risk():
    low = score_transaction(_base_tx(velocity_24h=1))
    medium = score_transaction(_base_tx(velocity_24h=4))
    high = score_transaction(_base_tx(velocity_24h=8))
    assert medium > low
    assert high > medium


def test_failed_logins_high_adds_risk():
    none = score_transaction(_base_tx(failed_logins_24h=0))
    high = score_transaction(_base_tx(failed_logins_24h=5))
    assert high > none


def test_failed_logins_medium_adds_risk():
    none = score_transaction(_base_tx(failed_logins_24h=0))
    medium = score_transaction(_base_tx(failed_logins_24h=3))
    high = score_transaction(_base_tx(failed_logins_24h=6))
    assert medium > none
    assert high > medium


def test_score_floor_is_zero():
    tx = _base_tx(
        device_risk_score=0,
        is_international=0,
        amount_usd=1,
        velocity_24h=0,
        failed_logins_24h=0,
        prior_chargebacks=0,
    )
    assert score_transaction(tx) == 0


def test_score_ceiling_is_100():
    tx = _base_tx(
        device_risk_score=90,
        is_international=1,
        amount_usd=5000,
        velocity_24h=10,
        failed_logins_24h=8,
        prior_chargebacks=3,
    )
    assert score_transaction(tx) == 100
