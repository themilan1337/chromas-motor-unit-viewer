"""Synthetic data only: three planted sources, ICs are noisy copies. Checks the math, says nothing about cuttlefish."""
import numpy as np

from mu_viewer.core import lab_ic_correlation, unit_stats


def make(noise=0.05, seed=0):
    rng = np.random.default_rng(seed)
    src = rng.standard_normal((3, 400))
    group = np.array([0, 0, 0, 1, 1, 2])
    ics = src[group] + noise * rng.standard_normal((6, 400))
    chrom = np.array([10, 11, 12, 10, 13, 14])
    return ics, group, chrom


def test_matches_lab_formula():
    ics, _, _ = make()
    c = lab_ic_correlation(ics)
    assert np.allclose(c, np.abs(np.corrcoef(ics)))
    assert np.allclose(np.diag(c), 1) and (c >= 0).all() and (c <= 1 + 1e-9).all()


def test_unit_stats_recovers_planted_units():
    ics, group, chrom = make()
    s = {u["unit"]: u for u in unit_stats(lab_ic_correlation(ics), group, chrom)}
    assert s[0]["n_ics"] == 3 and s[0]["chroms"] == [10, 11, 12] and s[0]["r_min"] > 0.95
    assert s[1]["n_ics"] == 2 and s[1]["n_chroms"] == 2
    assert s[2]["r_mean"] is None  # a single IC has no pair, no value is invented


def test_negative_label_skipped_and_anticorrelated_counts_as_high():
    ics, group, chrom = make()
    ics[1] *= -1  # lab takes abs(), so a sign flip must not lower the value
    labels = group.copy(); labels[5] = -1
    s = unit_stats(lab_ic_correlation(ics), labels, chrom)
    assert [u["unit"] for u in s] == [0, 1] and s[0]["r_min"] > 0.95


def test_assemble_and_render(tmp_path):
    from mu_viewer.build import assemble
    from mu_viewer.render import render

    ics, group, chrom = make()
    xy = np.array([[10, 10], [10, 30], [30, 10], [30, 30], [50, 50]], float)
    ids = np.array([10, 11, 12, 13, 14])
    sl = np.tile(np.array([0] * 18 + [1] * 18), (5, 1))
    p = assemble(ics, group, chrom, np.zeros(6, int), ids, xy, np.zeros(5), sl, np.zeros((64, 64, 3), np.uint8), 36, "SYNTHETIC")
    assert [u["unit"] for u in p["units"]] == [0, 1, 2] and p["units"][2]["r_mean"] is None
    out = render(p, tmp_path / "v.html")
    html = out.read_text()
    assert "SYNTHETIC" in html and "__DATA__" not in html and len(html) > 5000


def test_lab_csv_rows_columns_and_counts():
    from mu_viewer.build import lab_csv_rows

    rows = lab_csv_rows(np.array([10, 10, 11]), np.array([0, 1, 0]), np.array([0, 1, 0]), np.array([10, 11]), np.array([[5.0, 7.0], [20.0, 30.0]]))
    assert rows[0] == [10, 0, 0, 2, 7.0, 5.0] and rows[2] == [11, 0, 0, 1, 30.0, 20.0]  # x = column coordinate, y = row coordinate
