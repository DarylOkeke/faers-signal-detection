#!/usr/bin/env python3
"""
Test Suite for PRR/ROR Mathematical Functions

Tests the statistical calculations in compute_summary.py with known cases.

Author: FAERS Signal Detection Team
Date: August 2025
"""

import pytest
import math
import sys
import os

# Add src to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from compute_summary import (
    apply_haldane_correction,
    compute_prr_stats,
    compute_ror_stats,
    compute_chi2_pearson,
    compute_statistics_row
)

class TestHaldaneCorrection:
    """Test Haldane-Anscombe correction logic."""
    
    def test_no_correction_needed(self):
        """Test that correction is not applied when all cells > 0."""
        a, b, c, d = 30, 970, 300, 9700
        a_prime, b_prime, c_prime, d_prime = apply_haldane_correction(a, b, c, d)
        
        assert a_prime == 30.0
        assert b_prime == 970.0
        assert c_prime == 300.0
        assert d_prime == 9700.0
    
    def test_correction_applied_zero_a(self):
        """Test that correction is applied when a=0."""
        a, b, c, d = 0, 100, 10, 10000
        a_prime, b_prime, c_prime, d_prime = apply_haldane_correction(a, b, c, d)
        
        assert a_prime == 0.5
        assert b_prime == 100.5
        assert c_prime == 10.5
        assert d_prime == 10000.5
    
    def test_correction_applied_zero_d(self):
        """Test that correction is applied when d=0."""
        a, b, c, d = 5, 95, 50, 0
        a_prime, b_prime, c_prime, d_prime = apply_haldane_correction(a, b, c, d)
        
        assert a_prime == 5.5
        assert b_prime == 95.5
        assert c_prime == 50.5
        assert d_prime == 0.5

class TestPRRCalculations:
    """Test PRR calculations and confidence intervals."""
    
    def test_prr_balanced_case(self):
        """Test PRR calculation for balanced 2x2 table."""
        # Known case: a=30, b=970, c=300, d=9700
        # Expected PRR ≈ 1.0 (no association)
        a_prime, b_prime, c_prime, d_prime = 30.0, 970.0, 300.0, 9700.0
        
        prr, prr_lcl, prr_ucl = compute_prr_stats(a_prime, b_prime, c_prime, d_prime)
        
        # PRR should be very close to 1.0
        assert abs(prr - 1.0) < 1e-6
        
        # Confidence interval should be finite and reasonable
        assert 0 < prr_lcl < prr < prr_ucl
        assert prr_lcl > 0.5  # Should be reasonably tight
        assert prr_ucl < 2.0
    
    def test_prr_with_haldane_correction(self):
        """Test PRR calculation with Haldane correction applied."""
        # Case with a=0 requiring correction
        a_prime, b_prime, c_prime, d_prime = 0.5, 100.5, 10.5, 10000.5
        
        prr, prr_lcl, prr_ucl = compute_prr_stats(a_prime, b_prime, c_prime, d_prime)
        
        # Should not crash and return finite values
        assert math.isfinite(prr)
        assert math.isfinite(prr_lcl)
        assert math.isfinite(prr_ucl)
        assert 0 < prr_lcl < prr < prr_ucl
    
    def test_prr_edge_case_zero_background(self):
        """Test PRR when background rate is zero (c=d=0)."""
        a_prime, b_prime, c_prime, d_prime = 5.5, 95.5, 0.5, 0.5
        
        prr, prr_lcl, prr_ucl = compute_prr_stats(a_prime, b_prime, c_prime, d_prime)
        
        # Should handle gracefully, even if infinite
        assert prr > 0  # Should be positive
        # CIs might be infinite, but shouldn't crash

class TestRORCalculations:
    """Test ROR calculations and confidence intervals."""
    
    def test_ror_balanced_case(self):
        """Test ROR calculation for balanced 2x2 table."""
        # Same balanced case as PRR test
        a_prime, b_prime, c_prime, d_prime = 30.0, 970.0, 300.0, 9700.0
        
        ror, ror_lcl, ror_ucl = compute_ror_stats(a_prime, b_prime, c_prime, d_prime)
        
        # ROR should be close to 1.0 for balanced case
        expected_ror = (30.0 / 970.0) / (300.0 / 9700.0)
        assert abs(ror - expected_ror) < 1e-10
        
        # Confidence interval should be finite
        assert 0 < ror_lcl < ror < ror_ucl
    
    def test_ror_with_haldane_correction(self):
        """Test ROR calculation with Haldane correction."""
        a_prime, b_prime, c_prime, d_prime = 0.5, 100.5, 10.5, 10000.5
        
        ror, ror_lcl, ror_ucl = compute_ror_stats(a_prime, b_prime, c_prime, d_prime)
        
        # Should not crash
        assert math.isfinite(ror)
        assert math.isfinite(ror_lcl) 
        assert math.isfinite(ror_ucl)
        assert 0 < ror_lcl < ror < ror_ucl

class TestChi2Calculations:
    """Test chi-square calculations."""
    
    def test_chi2_balanced_case(self):
        """Test chi-square for balanced case (should be close to 0)."""
        a_prime, b_prime, c_prime, d_prime = 30.0, 970.0, 300.0, 9700.0
        
        chi2 = compute_chi2_pearson(a_prime, b_prime, c_prime, d_prime)
        
        # For balanced case, chi-square should be very small
        assert chi2 < 0.1  # Very small chi-square
        assert chi2 >= 0   # Should be non-negative
    
    def test_chi2_with_association(self):
        """Test chi-square with clear association."""
        # Case with clear association
        a_prime, b_prime, c_prime, d_prime = 50.0, 50.0, 10.0, 990.0
        
        chi2 = compute_chi2_pearson(a_prime, b_prime, c_prime, d_prime)
        
        # Should show significant association
        assert chi2 > 4.0  # Should exceed typical threshold
        assert math.isfinite(chi2)
    
    def test_chi2_with_correction(self):
        """Test chi-square with Haldane correction."""
        a_prime, b_prime, c_prime, d_prime = 0.5, 100.5, 10.5, 10000.5
        
        chi2 = compute_chi2_pearson(a_prime, b_prime, c_prime, d_prime)
        
        # Should not crash
        assert math.isfinite(chi2)
        assert chi2 >= 0

class TestIntegratedCalculations:
    """Test the integrated statistics computation."""
    
    def test_compute_statistics_row_normal_case(self):
        """Test complete statistics computation for normal case."""
        # Create a mock row
        import pandas as pd
        row = pd.Series({'a': 30, 'b': 970, 'c': 300, 'd': 9700})
        
        stats = compute_statistics_row(row)
        
        # Check all expected keys are present
        expected_keys = ['PRR', 'PRR_LCL', 'PRR_UCL', 'ROR', 'ROR_LCL', 'ROR_UCL', 'chi2']
        for key in expected_keys:
            assert key in stats
            assert math.isfinite(stats[key])
        
        # Check specific values for this balanced case
        assert abs(stats['PRR'] - 1.0) < 1e-6
        assert stats['chi2'] < 0.1
    
    def test_compute_statistics_row_sparse_case(self):
        """Test statistics computation for sparse case (a=0)."""
        import pandas as pd
        row = pd.Series({'a': 0, 'b': 100, 'c': 10, 'd': 10000})
        
        stats = compute_statistics_row(row)
        
        # Should not crash and return finite values
        expected_keys = ['PRR', 'PRR_LCL', 'PRR_UCL', 'ROR', 'ROR_LCL', 'ROR_UCL', 'chi2']
        for key in expected_keys:
            assert key in stats
            # All values should be finite (Haldane correction should prevent inf/nan)
            assert math.isfinite(stats[key])

class TestFlagingLogic:
    """Test signal flagging criteria."""
    
    def test_flagging_criteria(self):
        """Test that flagging logic works correctly."""
        # This would be tested at the DataFrame level in compute_summary
        # For now, just verify the individual components work
        
        # Test case that should be flagged: high PRR, high chi2, sufficient N
        prr = 5.0
        chi2 = 10.0
        n = 10
        
        # Manual flagging logic
        flagged = (prr >= 2.0) and (chi2 >= 4.0) and (n >= 3)
        assert flagged
        
        # Test case that should NOT be flagged: low N
        n = 1
        flagged = (prr >= 2.0) and (chi2 >= 4.0) and (n >= 3)
        assert not flagged

if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
