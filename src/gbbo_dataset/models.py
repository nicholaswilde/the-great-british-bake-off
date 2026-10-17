"""Pydantic data models for The Great British Bake Off (GBBO) dataset."""

import re
from enum import Enum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResultEnum(str, Enum):
    """Performance outcome for a baker in an episode."""

    SAFE = "SAFE"
    STAR_BAKER = "STAR_BAKER"
    ELIMINATED = "ELIMINATED"
    WINNER = "WINNER"
    RUNNER_UP = "RUNNER_UP"
    WITHDREW = "WITHDREW"


class Season(BaseModel):
    """Metadata for a Great British Bake Off series/season."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    series_number: int = Field(..., ge=1, description="Series / Season number")
    year: int | None = Field(default=None, description="Year broadcast")
    winner: str | None = Field(default=None, description="Series winner name")
    hosts: list[str] = Field(default_factory=list, description="Series host(s)")
    judges: list[str] = Field(default_factory=list, description="Series judge(s)")
    network: str | None = Field(default=None, description="Broadcaster / Network")
    pbs_season: int | None = Field(default=None, description="PBS Season number")
    netflix_collection: int | None = Field(
        default=None, description="Netflix Collection number"
    )
    roku_season: int | None = Field(default=None, description="The Roku Channel season")
    location: str | None = Field(default=None, description="Filming location")


class Baker(BaseModel):
    """A contestant in The Great British Bake Off."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    baker_id: str = Field(
        ...,
        description="Primary key: format s{series_number}_{first_name_lowercase} (e.g. s01_edward)",
    )
    series_number: int = Field(..., ge=1, description="Series / Season number")
    name: str = Field(..., description="Baker full name")
    age: int | None = Field(default=None, ge=0, description="Baker age during series")
    gender: str | None = Field(default=None, description="Baker gender (M, F, NB)")
    occupation: str | None = Field(default=None, description="Baker occupation")
    hometown: str | None = Field(default=None, description="Baker hometown")
    overall_placement: int | None = Field(
        default=None,
        ge=1,
        description="Final rank/placement in the series (1 = Winner)",
    )
    image_url: str | None = Field(
        default=None, description="URL link to official baker headshot photo"
    )
    latitude: float | None = Field(
        default=None, description="Hometown latitude coordinate (WGS84)"
    )
    longitude: float | None = Field(
        default=None, description="Hometown longitude coordinate (WGS84)"
    )
    country: str | None = Field(
        default=None,
        description="Hometown country (England, Scotland, Wales, Northern Ireland, Overseas)",
    )
    county_region: str | None = Field(
        default=None, description="Hometown county or administrative region"
    )

    @classmethod
    def generate_baker_id(cls, series_number: int, name: str) -> str:
        """Generate canonical baker_id: s{series_number:02d}_{first_name_lowercase}."""
        clean_name = re.sub(
            r"^(dr\.|dr|mr\.|mr|mrs\.|mrs|ms\.|ms|rev\.|rev)\s+",
            "",
            name.strip(),
            flags=re.IGNORECASE,
        )
        first_name = clean_name.split()[0].lower() if clean_name else "unknown"
        clean_first = re.sub(r"[^a-z0-9]", "", first_name)
        return f"s{series_number:02d}_{clean_first}"


class Episode(BaseModel):
    """An episode in a Great British Bake Off series."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    episode_id: str = Field(
        ...,
        description="Primary key: format s{series_number}e{episode_number} (e.g. s01e01)",
    )
    series_number: int = Field(..., ge=1, description="Series number")
    episode_number: int = Field(..., ge=1, description="Episode number within series")
    theme: str | None = Field(
        default=None, description="Episode theme (e.g. Cake Week)"
    )
    air_date: str | None = Field(
        default=None, description="Broadcast air date (YYYY-MM-DD)"
    )
    signature_time_min: int | None = Field(
        default=None, ge=0, description="Signature challenge time limit in minutes"
    )
    technical_time_min: int | None = Field(
        default=None, ge=0, description="Technical challenge time limit in minutes"
    )
    showstopper_time_min: int | None = Field(
        default=None, ge=0, description="Showstopper challenge time limit in minutes"
    )

    @classmethod
    def generate_episode_id(cls, series_number: int, episode_number: int) -> str:
        """Generate canonical episode_id: s{series_number:02d}e{episode_number:02d}."""
        return f"s{series_number:02d}e{episode_number:02d}"


class Performance(BaseModel):
    """Baker performance during an individual episode."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    performance_id: str = Field(
        ...,
        description="Primary key: format s{series}e{episode}_{baker_id}",
    )
    baker_id: str = Field(..., description="Foreign key reference to Baker")
    episode_id: str = Field(..., description="Foreign key reference to Episode")
    signature_dish: str | None = Field(
        default=None, description="Description or title of Signature challenge bake"
    )
    technical_rank: int | None = Field(
        default=None, ge=1, description="Rank in Technical challenge"
    )
    showstopper_dish: str | None = Field(
        default=None, description="Description or title of Showstopper challenge bake"
    )
    result: ResultEnum = Field(
        default=ResultEnum.SAFE, description="Outcome for episode"
    )
    hollywood_handshake: bool = Field(
        default=False,
        description="Whether baker received a Hollywood Handshake in this episode",
    )
    did_well: bool = Field(
        default=False,
        description="Whether baker was called out by judges as doing well",
    )
    at_risk: bool = Field(
        default=False,
        description="Whether baker was called out as in the bottom / at risk",
    )
    absent: bool = Field(
        default=False,
        description="Whether baker was absent from this episode due to illness",
    )

    @classmethod
    def generate_performance_id(cls, episode_id: str, baker_id: str) -> str:
        """Generate canonical performance_id: {episode_id}_{baker_id}."""
        return f"{episode_id}_{baker_id}"

    @model_validator(mode="after")
    def validate_ids(self) -> Self:
        """Ensure performance_id is populated if empty."""
        if not self.performance_id:
            self.performance_id = self.generate_performance_id(
                self.episode_id, self.baker_id
            )
        return self


class FandomRecipe(BaseModel):
    """Technical challenge recipe or signature bake metadata from Bake Off Fandom wiki."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    recipe_id: str = Field(
        ...,
        description="Unique recipe identifier (format: s{series}e{episode}_{slug})",
    )
    series_number: int = Field(..., ge=1, description="Series / Season number")
    episode_number: int = Field(..., ge=1, description="Episode number within series")
    challenge_type: str = Field(
        default="Technical",
        description="Challenge type (Technical, Signature, Showstopper)",
    )
    dish_name: str = Field(..., description="Name of the recipe or bake")
    baker_name: str | None = Field(
        default=None, description="Baker name if applicable (for signature/showstopper)"
    )
    recipe_url: str | None = Field(
        default=None, description="URL link to official recipe or Fandom page"
    )
    judging_notes: str | None = Field(
        default=None, description="Judge commentary or key technical criteria"
    )
    difficulty: str | None = Field(
        default=None, description="Relative difficulty or technical hurdle"
    )

    @classmethod
    def generate_recipe_id(
        cls, series_number: int, episode_number: int, dish_name: str
    ) -> str:
        """Generate canonical recipe_id: s{series:02d}e{episode:02d}_{slug}."""
        slug = re.sub(r"[^a-z0-9]+", "_", dish_name.lower()).strip("_")
        return f"s{series_number:02d}e{episode_number:02d}_{slug}"


class FandomLore(BaseModel):
    """Episode lore, judging quotes, and tent trivia from Bake Off Fandom wiki."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    lore_id: str = Field(
        ...,
        description="Unique lore identifier (format: s{series}e{episode}_lore)",
    )
    series_number: int = Field(..., ge=1, description="Series / Season number")
    episode_number: int = Field(..., ge=1, description="Episode number within series")
    theme: str | None = Field(
        default=None, description="Episode theme (e.g. Cake Week)"
    )
    famous_quotes: list[str] = Field(
        default_factory=list,
        description="Notable judging or tent quotes (e.g. 'soggy bottom')",
    )
    star_baker_runner_up: str | None = Field(
        default=None, description="Contestant highlighted as runner-up for Star Baker"
    )
    notable_moments: list[str] = Field(
        default_factory=list,
        description="Notable tent moments, accidents, or memorable interactions",
    )
    source_url: str | None = Field(default=None, description="Fandom wiki source URL")

    @classmethod
    def generate_lore_id(cls, series_number: int, episode_number: int) -> str:
        """Generate canonical lore_id: s{series:02d}e{episode:02d}_lore."""
        return f"s{series_number:02d}e{episode_number:02d}_lore"


class RedditComment(BaseModel):
    """Top community comment from episode discussion thread."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    comment_id: str = Field(..., description="Reddit comment ID")
    author: str = Field(default="[deleted]", description="Reddit username")
    score: int = Field(default=0, description="Comment upvote score")
    body: str = Field(..., description="Comment text body")


class RedditDiscussion(BaseModel):
    """Reddit episode discussion thread and sentiment metadata."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    thread_id: str = Field(
        ..., description="Reddit submission ID (e.g. t3_xyz123 or xyz123)"
    )
    subreddit: str = Field(default="GreatBritishBakeOff", description="Subreddit name")
    series_number: int = Field(..., ge=1, description="Series / Season number")
    episode_number: int = Field(..., ge=1, description="Episode number within series")
    title: str = Field(..., description="Discussion thread title")
    author: str = Field(default="[deleted]", description="Thread submitter")
    score: int = Field(default=0, description="Thread score / net upvotes")
    upvote_ratio: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Upvote ratio (0.0 to 1.0)"
    )
    num_comments: int = Field(
        default=0, ge=0, description="Total number of comments in thread"
    )
    permalink: str = Field(..., description="Permalink URL to thread")
    top_comments: list[RedditComment] = Field(
        default_factory=list,
        description="Top community reaction comments",
    )
    sentiment_label: str | None = Field(
        default=None,
        description="Aggregated reaction sentiment (Positive, Mixed, Critical)",
    )
