import pytest
import torch

from nlp.device import get_device


@pytest.mark.parametrize(
    ("cuda", "mps", "expected"),
    [
        (True, True, "cuda"),
        (True, False, "cuda"),
        (False, True, "mps"),
        (False, False, "cpu"),
    ],
)
def test_get_device_preference(monkeypatch, cuda, mps, expected):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: cuda)
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: mps)
    assert get_device() == expected


def test_get_device_runs_on_this_machine():
    device = get_device()
    assert device in {"cuda", "mps", "cpu"}
    assert torch.ones(2, device=device).sum().item() == 2
