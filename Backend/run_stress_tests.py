"""
Test runner for stress test suite.
Executes all phases and generates a comprehensive report.
"""

import sys
import asyncio
import time
import pytest
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Test phases to run
PHASES = {
    "Infrastructure": ["tests/test_infra_setup.py"],
    "Concurrency": ["tests/test_concurrency_race_conditions.py"],
    "Scale": ["tests/test_scale_and_performance.py"],
    "Boundaries": ["tests/test_boundary_conditions.py"],
    "Error Recovery": ["tests/test_error_recovery_and_rollback.py"],
    "Data Integrity": ["tests/test_data_integrity_and_consistency.py"],
}


def run_phase(phase_name: str, test_files: List[str]) -> Tuple[int, float]:
    """Run a single test phase and return (exit_code, duration_seconds)."""
    print(f"\n{'='*70}")
    print(f"Running Phase: {phase_name}")
    print(f"{'='*70}")
    
    start = time.time()
    
    # Run pytest with verbose output and colored markers
    args = [
        *test_files,
        "-v",
        "--tb=short",
        "-s",  # No capture, show print statements
        "--asyncio-mode=auto",  # Auto mode for pytest-asyncio
    ]
    
    exit_code = pytest.main(args)
    duration = time.time() - start
    
    return exit_code, duration


def run_all_phases() -> Dict[str, Tuple[int, float]]:
    """Run all test phases and return results."""
    results = {}
    
    for phase_name, test_files in PHASES.items():
        try:
            exit_code, duration = run_phase(phase_name, test_files)
            results[phase_name] = (exit_code, duration)
            
            status = "✓ PASS" if exit_code == 0 else "✗ FAIL"
            print(f"\n{status} Phase '{phase_name}' completed in {duration:.2f}s")
        
        except Exception as e:
            print(f"\n✗ FAIL Phase '{phase_name}': {e}")
            results[phase_name] = (1, 0)
    
    return results


def generate_report(results: Dict[str, Tuple[int, float]]) -> str:
    """Generate a markdown report of test results."""
    report = []
    report.append("# Stress Test Report\n")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    report.append("## Summary\n")
    
    total_phases = len(results)
    passed_phases = sum(1 for exit_code, _ in results.values() if exit_code == 0)
    failed_phases = total_phases - passed_phases
    total_duration = sum(duration for _, duration in results.values())
    
    report.append(f"- Total Phases: {total_phases}")
    report.append(f"- Passed: {passed_phases}")
    report.append(f"- Failed: {failed_phases}")
    report.append(f"- Total Duration: {total_duration:.2f}s\n")
    
    report.append("## Phase Results\n")
    
    for phase_name, (exit_code, duration) in results.items():
        status = "✓ PASS" if exit_code == 0 else "✗ FAIL"
        report.append(f"- {status} {phase_name}: {duration:.2f}s")
    
    report.append("\n## Notes\n")
    report.append("- Run individual phases with: `pytest tests/test_<phase>.py -v`")
    report.append("- Run all phases with: `python run_stress_tests.py`")
    report.append("- See detailed test code in `Backend/tests/` directory\n")
    
    return "\n".join(report)


def main():
    """Main entry point."""
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  PLACEMENT SYSTEM STRESS TEST SUITE".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝\n")
    
    # Run all phases
    results = run_all_phases()
    
    # Generate report
    report = generate_report(results)
    
    print("\n" + report)
    
    # Save report
    report_path = Path("STRESS_TEST_RESULTS.md")
    report_path.write_text(report)
    print(f"\nReport saved to: {report_path}")
    
    # Exit with appropriate code
    failed_phases = sum(1 for exit_code, _ in results.values() if exit_code != 0)
    sys.exit(1 if failed_phases > 0 else 0)


if __name__ == "__main__":
    main()
