import pytest
from data_pipeline import load_and_preprocess_data, run_experiment
from model import parse_hyperparams, train_custom_model


def test_preprocess_shapes():
    X_train, X_test, y_train, y_test = load_and_preprocess_data()
    assert len(X_train) > 0
    assert len(X_test) > 0
    assert len(X_train) + len(X_test) == 200


def test_experiment_accuracy():
    acc = run_experiment()
    assert acc > 0.0


def test_model_training():
    res = train_custom_model([1, 2], [0, 1])
    assert res["status"] == "trained"
