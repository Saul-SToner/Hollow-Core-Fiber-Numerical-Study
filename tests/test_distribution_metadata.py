"""The renamed wheel must run without the old distribution installed."""
import importlib.metadata as metadata
import pytest
import optics_portfolio

def test_distribution_identity_and_runtime_version():
    name='hollow-core-fiber-numerical-study'
    assert metadata.version(name)==optics_portfolio.__version__=='0.2.0'
    # Build backends may reorder equivalent comma-separated constraints.
    assert set(metadata.metadata(name)['Requires-Python'].split(','))=={'>=3.13','<3.14'}
    with pytest.raises(metadata.PackageNotFoundError):
        metadata.version('optics-portfolio-m2-private')
