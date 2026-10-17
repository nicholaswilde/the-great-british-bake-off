"""Unit tests for GBBO Pydantic models."""

import pytest
from pydantic import ValidationError

from gbbo_dataset.models import Baker, Episode, Performance, ResultEnum


def test_baker_model_valid():
    """Test valid Baker creation and ID generation."""
    baker_id = Baker.generate_baker_id(series_number=1, name="Edward Kimber")
    assert baker_id == "s01_edward"

    baker = Baker(
        baker_id=baker_id,
        series_number=1,
        name="Edward Kimber",
        age=24,
        occupation="Debt collector",
        hometown="Bradford",
        overall_placement=1,
    )
    assert baker.baker_id == "s01_edward"
    assert baker.series_number == 1
    assert baker.overall_placement == 1


def test_baker_model_invalid_series():
    """Test Baker validation fails for invalid series number."""
    with pytest.raises(ValidationError):
        Baker(
            baker_id="s00_test",
            series_number=0,
            name="Invalid Baker",
        )


def test_episode_model_valid():
    """Test valid Episode creation."""
    episode_id = Episode.generate_episode_id(series_number=1, episode_number=1)
    assert episode_id == "s01e01"

    episode = Episode(
        episode_id=episode_id,
        series_number=1,
        episode_number=1,
        theme="Cakes",
        air_date="2010-08-17",
    )
    assert episode.episode_id == "s01e01"
    assert episode.theme == "Cakes"


def test_performance_model_valid():
    """Test valid Performance creation and handshake flag."""
    perf_id = Performance.generate_performance_id("s01e01", "s01_edward")
    assert perf_id == "s01e01_s01_edward"

    perf = Performance(
        performance_id=perf_id,
        baker_id="s01_edward",
        episode_id="s01e01",
        signature_dish="Caramel Cake",
        technical_rank=1,
        showstopper_dish="Chocolate Box",
        result=ResultEnum.STAR_BAKER,
        hollywood_handshake=True,
    )
    assert perf.result == ResultEnum.STAR_BAKER
    assert perf.hollywood_handshake is True
