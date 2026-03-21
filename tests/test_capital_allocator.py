"""
test_capital_allocator.py — Position Sizing & Capital Allocation Tests
=======================================================================
"""
import pytest
from scripts.capital_allocator import (
    get_risk_per_trade,
    get_deployment_model,
    calculate_position_size,
)
from scripts.config import CFG


class TestRiskPerTrade:
    def test_full_offense(self):
        risk = get_risk_per_trade(85)
        assert risk == CFG.RISK_PER_TRADE_FULL  # 1%

    def test_selective(self):
        risk = get_risk_per_trade(65)
        assert risk == CFG.RISK_PER_TRADE_SELECTIVE  # 0.75%

    def test_defensive(self):
        risk = get_risk_per_trade(40)
        assert risk == CFG.RISK_PER_TRADE_DEFENSIVE  # 0.5%

    def test_capital_preservation(self):
        risk = get_risk_per_trade(20)
        assert risk == CFG.RISK_PER_TRADE_DEFENSIVE * 0.5  # 0.25%

    def test_boundary_80(self):
        risk = get_risk_per_trade(80)
        assert risk == CFG.RISK_PER_TRADE_FULL

    def test_boundary_50(self):
        risk = get_risk_per_trade(50)
        assert risk == CFG.RISK_PER_TRADE_SELECTIVE

    def test_boundary_30(self):
        risk = get_risk_per_trade(30)
        assert risk == CFG.RISK_PER_TRADE_DEFENSIVE


class TestDeploymentModel:
    def test_full_offense_model(self):
        model = get_deployment_model(90)
        assert model["label"] == "FULL OFFENSE"
        assert model["max_positions"] == 8
        assert model["equity_deployed_pct"] == 80.0

    def test_selective_model(self):
        model = get_deployment_model(65)
        assert model["label"] == "SELECTIVE"
        assert model["max_positions"] == 5

    def test_defensive_model(self):
        model = get_deployment_model(40)
        assert model["label"] == "DEFENSIVE"
        assert model["max_positions"] == 3

    def test_preservation_model(self):
        model = get_deployment_model(10)
        assert model["label"] == "CAPITAL PRESERVATION"
        assert model["max_positions"] == 1
        assert model["equity_deployed_pct"] == 10.0

    def test_model_has_all_keys(self):
        model = get_deployment_model(70)
        required_keys = [
            "label", "equity", "risk_per_trade_pct", "risk_per_trade_dollar",
            "max_position_size", "max_positions", "equity_deployed_pct",
            "max_capital_deployed", "max_sector_pct", "time_stop_days", "advice"
        ]
        for key in required_keys:
            assert key in model, f"Missing key: {key}"

    def test_equity_correct(self):
        model = get_deployment_model(70)
        assert model["equity"] == CFG.ACCOUNT_EQUITY


class TestPositionSize:
    def test_basic_calculation(self):
        result = calculate_position_size(100.0, 95.0, 85)
        assert result["shares"] > 0
        assert result["risk_dollar"] > 0
        assert result["position_value"] > 0

    def test_zero_risk(self):
        """Entry == stop loss → no shares."""
        result = calculate_position_size(100.0, 100.0, 85)
        assert result["shares"] == 0

    def test_position_capped_by_max_pct(self):
        """Position value should not exceed MAX_POSITION_PCT * equity."""
        max_pos = CFG.ACCOUNT_EQUITY * CFG.MAX_POSITION_PCT
        result = calculate_position_size(10.0, 9.90, 85)  # Tiny risk → many shares
        assert result["position_value"] <= max_pos + 10  # Allow tiny float rounding

    def test_risk_dollar_within_budget(self):
        """Actual risk should not exceed allocated risk per trade."""
        result = calculate_position_size(50.0, 45.0, 85)
        risk_budget = CFG.ACCOUNT_EQUITY * CFG.RISK_PER_TRADE_FULL
        assert result["risk_dollar"] <= risk_budget + 5  # Small float rounding

    def test_shares_are_whole_numbers(self):
        result = calculate_position_size(150.0, 140.0, 65)
        assert isinstance(result["shares"], int)

    def test_regime_affects_size(self):
        """Higher regime → more shares (more risk budget)."""
        full_offense = calculate_position_size(100.0, 95.0, 85)
        preservation = calculate_position_size(100.0, 95.0, 10)
        assert full_offense["shares"] >= preservation["shares"]
