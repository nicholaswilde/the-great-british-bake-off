"""Unit tests for GBBO Pydantic models."""

import pytest
from pydantic import ValidationError

from gbbo_dataset.models import (
    Baker,
    Episode,
    FandomLore,
    FandomRecipe,
    Performance,
    RedditComment,
    RedditDiscussion,
    ResultEnum,
)


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
        latitude=53.7960,
        longitude=-1.7594,
        country="England",
        county_region="West Yorkshire",
    )
    assert baker.baker_id == "s01_edward"
    assert baker.series_number == 1
    assert baker.overall_placement == 1
    assert baker.latitude == 53.7960
    assert baker.longitude == -1.7594
    assert baker.country == "England"
    assert baker.county_region == "West Yorkshire"


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


def test_fandom_and_reddit_models():
    """Test Fandom and Reddit model instantiation and canonical ID generation."""
    r_id = FandomRecipe.generate_recipe_id(15, 1, "Battenberg Cake")
    assert r_id == "s15e01_battenberg_cake"
    recipe = FandomRecipe(
        recipe_id=r_id,
        series_number=15,
        episode_number=1,
        dish_name="Battenberg Cake",
    )
    assert recipe.challenge_type == "Technical"

    l_id = FandomLore.generate_lore_id(5, 4)
    assert l_id == "s05e04_lore"
    lore = FandomLore(
        lore_id=l_id,
        series_number=5,
        episode_number=4,
        famous_quotes=["No one likes a soggy bottom."],
    )
    assert len(lore.famous_quotes) == 1

    comment = RedditComment(comment_id="c1", author="fan", score=10, body="Great bake!")
    disc = RedditDiscussion(
        thread_id="t1",
        series_number=1,
        episode_number=1,
        title="Discussion",
        permalink="/r/test",
        top_comments=[comment],
    )
    assert disc.top_comments[0].body == "Great bake!"
