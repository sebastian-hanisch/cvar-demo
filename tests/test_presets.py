"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Permalink begrenzt und rastet ein."""

import pytest

import cvr_constants as C
import cvr_evaluation as ev
import cvr_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds_and_on_the_step_grid():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            value = preset[key]
            if spec.choices is not None:
                assert value in spec.choices, (name, key)
            else:
                assert spec.lo <= value <= spec.hi, (name, key)
                assert P.snap(spec, value) == pytest.approx(value), (name, key)


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_snap_clamps_and_rounds_to_the_step():
    assert P.snap(P.SETTING_SPECS["s_slider"], 999) == C.S_MAX
    assert P.snap(P.SETTING_SPECS["s_slider"], 130) == 140
    assert P.snap(P.SETTING_SPECS["lam_slider"], 0.6) == pytest.approx(0.5)
    assert P.snap(P.SETTING_SPECS["alpha_radio"], 0.7) == C.DEFAULT_ALPHA
    assert P.snap(P.SETTING_SPECS["budget_radio"], "viel") == C.DEFAULT_BUDGET


def test_sweep_and_lambda_grid_are_consistent_with_the_slider():
    assert set(C.LAMBDA_GRID) >= {C.DEFAULT_LAMBDA, 0.0, 1.0}
    assert max(C.SWEEP_S) <= C.S_MAX and min(C.SWEEP_S) >= C.S_MIN
