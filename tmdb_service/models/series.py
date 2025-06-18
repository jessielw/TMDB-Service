from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tmdb_service.globals import Base


series_created_by_assoc = Table(
    "series_created_by_assoc",
    Base.metadata,
    Column("series_id", ForeignKey("series.id"), primary_key=True),
    Column("created_by_id", ForeignKey("series_created_by.id"), primary_key=True),
)


class SeriesCreatedBy(Base):
    __tablename__ = "series_created_by"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    credit_id: Mapped[str | None] = mapped_column(String(255), default=None)
    name: Mapped[str | None] = mapped_column(default=None)
    original_name: Mapped[str | None] = mapped_column(default=None)
    gender: Mapped[int | None] = mapped_column(SmallInteger, default=None)
    profile_path: Mapped[str | None] = mapped_column(String(255), default=None)

    # relationships
    series: Mapped[list["Series"]] = relationship(
        secondary=series_created_by_assoc,
        back_populates="created_by",
        init=False,
        repr=False,
    )


series_genres_assoc = Table(
    "series_genres_assoc",
    Base.metadata,
    Column("series_id", ForeignKey("series.id"), primary_key=True),
    Column("genre_id", ForeignKey("series_genres.id"), primary_key=True),
)


class SeriesGenres(Base):
    __tablename__ = "series_genres"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str | None] = mapped_column(String(255), default=None)

    # relationships
    series: Mapped[list["Series"]] = relationship(
        secondary=series_genres_assoc,
        back_populates="genres",
        init=False,
        repr=False,
    )


class SeriesLastEpisodeToAir(Base):
    __tablename__ = "series_last_episode_to_air"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str | None] = mapped_column(default=None)
    overview: Mapped[str | None] = mapped_column(default=None)
    vote_average: Mapped[float | None] = mapped_column(default=None)
    vote_count: Mapped[int | None] = mapped_column(BigInteger, default=None)
    air_date: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    episode_number: Mapped[int | None] = mapped_column(default=None)
    episode_type: Mapped[str | None] = mapped_column(default=None)
    production_code: Mapped[str | None] = mapped_column(default=None)
    runtime: Mapped[int | None] = mapped_column(default=None)
    season_number: Mapped[int | None] = mapped_column(default=None)
    show_id: Mapped[int | None] = mapped_column(default=None)
    still_path: Mapped[str | None] = mapped_column(String(255), default=None)

    # relationships
    series: Mapped["Series"] = relationship(
        back_populates="last_episode_to_air",
        init=False,
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
        repr=False,
    )


class SeriesNextEpisodeToAir(Base):
    __tablename__ = "series_next_episode_to_air"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str | None] = mapped_column(default=None)
    overview: Mapped[str | None] = mapped_column(default=None)
    vote_average: Mapped[float | None] = mapped_column(default=None)
    vote_count: Mapped[int | None] = mapped_column(BigInteger, default=None)
    air_date: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    episode_number: Mapped[int | None] = mapped_column(default=None)
    episode_type: Mapped[str | None] = mapped_column(default=None)
    production_code: Mapped[str | None] = mapped_column(default=None)
    runtime: Mapped[int | None] = mapped_column(default=None)
    season_number: Mapped[int | None] = mapped_column(default=None)
    show_id: Mapped[int | None] = mapped_column(default=None)
    still_path: Mapped[str | None] = mapped_column(String(255), default=None)

    # relationships
    series: Mapped["Series"] = relationship(
        back_populates="next_episode_to_air",
        init=False,
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
        repr=False,
    )


series_networks_assoc = Table(
    "series_networks_assoc",
    Base.metadata,
    Column("series_id", ForeignKey("series.id"), primary_key=True),
    Column("network_id", ForeignKey("series_networks.id"), primary_key=True),
)


class SeriesNetworks(Base):
    __tablename__ = "series_networks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    logo_path: Mapped[str | None] = mapped_column(String(255), default=None)
    name: Mapped[str | None] = mapped_column(default=None)
    origin_country: Mapped[str | None] = mapped_column(String(64), default=None)

    # relationships
    series: Mapped[list["Series"]] = relationship(
        secondary=series_networks_assoc,
        back_populates="networks",
        init=False,
        repr=False,
    )


series_companies_assoc = Table(
    "series_companies_assoc",
    Base.metadata,
    Column("series_id", ForeignKey("series.id"), primary_key=True),
    Column(
        "company_id", ForeignKey("series_production_companies.id"), primary_key=True
    ),
)


class SeriesProductionCompanies(Base):
    __tablename__ = "series_production_companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str | None] = mapped_column(default=None)
    origin_country: Mapped[str | None] = mapped_column(String(255), default=None)
    logo_path: Mapped[str | None] = mapped_column(String(255), default=None)

    # relationships
    series: Mapped[list["Series"]] = relationship(
        secondary=series_companies_assoc,
        back_populates="production_companies",
        init=False,
        repr=False,
    )


series_countries_assoc = Table(
    "series_countries_assoc",
    Base.metadata,
    Column("series_id", ForeignKey("series.id"), primary_key=True),
    Column(
        "country_id",
        ForeignKey("series_production_countries.iso_3166_1"),
        primary_key=True,
    ),
)


class SeriesProductionCountries(Base):
    __tablename__ = "series_production_countries"

    iso_3166_1: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(default=None)

    # relationships
    series: Mapped[list["Series"]] = relationship(
        secondary=series_countries_assoc,
        back_populates="production_countries",
        init=False,
        repr=False,
    )


class SeriesSeasons(Base):
    __tablename__ = "series_seasons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    air_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    episode_count: Mapped[int | None] = mapped_column(default=None)
    name: Mapped[str | None] = mapped_column(default=None)
    overview: Mapped[str | None] = mapped_column(default=None)
    poster_path: Mapped[str | None] = mapped_column(String(255), default=None)
    season_number: Mapped[int | None] = mapped_column(default=None)
    vote_average: Mapped[float | None] = mapped_column(default=None)

    # many-to-one relationship
    series_id: Mapped[int | None] = mapped_column(ForeignKey("series.id"), init=False)
    series: Mapped["Series"] = relationship(
        back_populates="seasons", init=False, repr=False
    )


series_languages_assoc = Table(
    "series_languages_assoc",
    Base.metadata,
    Column("series_id", ForeignKey("series.id"), primary_key=True),
    Column(
        "language_id", ForeignKey("series_spoken_languages.iso_639_1"), primary_key=True
    ),
)


class SeriesSpokenLanguages(Base):
    __tablename__ = "series_spoken_languages"

    iso_639_1: Mapped[str] = mapped_column(primary_key=True)
    english_name: Mapped[str | None] = mapped_column(String(255), default=None)
    name: Mapped[str | None] = mapped_column(String(255), default=None)

    # relationships
    series: Mapped[list["Series"]] = relationship(
        secondary=series_languages_assoc,
        back_populates="spoken_languages",
        init=False,
        repr=False,
    )


class SeriesAlternativeTitles(Base):
    __tablename__ = "series_alternative_titles"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, init=False
    )
    iso_3166_1: Mapped[str | None] = mapped_column(default=None)
    title: Mapped[str | None] = mapped_column(default=None)
    type: Mapped[str | None] = mapped_column(default=None)

    # relationships
    series_id: Mapped[int | None] = mapped_column(
        ForeignKey("series.id"),
        default=None,
    )
    series: Mapped["Series | None"] = relationship(
        back_populates="alternative_titles", default=None, repr=False
    )


series_cast_assoc = Table(
    "series_cast_assoc",
    Base.metadata,
    Column("series_id", ForeignKey("series.id"), primary_key=True),
    Column("cast_id", ForeignKey("series_cast_members.id"), primary_key=True),
)


class SeriesCastMembers(Base):
    __tablename__ = "series_cast_members"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    adult: Mapped[bool | None] = mapped_column(default=None)
    gender: Mapped[int | None] = mapped_column(SmallInteger, default=None)
    cast_id: Mapped[int | None] = mapped_column(default=None)
    name: Mapped[str | None] = mapped_column(String(255), default=None)
    original_name: Mapped[str | None] = mapped_column(String(255), default=None)
    known_for_department: Mapped[str | None] = mapped_column(String(255), default=None)
    popularity: Mapped[float | None] = mapped_column(default=None)
    profile_path: Mapped[str | None] = mapped_column(String(255), default=None)
    character: Mapped[str | None] = mapped_column(default=None)
    cast_order: Mapped[int | None] = mapped_column(SmallInteger, default=None)

    # relationships
    series: Mapped[list["Series"]] = relationship(
        secondary=series_cast_assoc,
        back_populates="cast_members",
        init=False,
        repr=False,
    )


class SeriesExternalIDs(Base):
    __tablename__ = "series_external_ids"

    series_id: Mapped[int] = mapped_column(ForeignKey("series.id"), primary_key=True)
    imdb_id: Mapped[str | None] = mapped_column(String(255), default=None)
    wikidata_id: Mapped[str | None] = mapped_column(String(255), default=None)
    facebook_id: Mapped[str | None] = mapped_column(String(255), default=None)
    instagram_id: Mapped[str | None] = mapped_column(String(255), default=None)
    twitter_id: Mapped[str | None] = mapped_column(String(255), default=None)

    # relationships
    series: Mapped["Series"] = relationship(
        back_populates="external_ids", uselist=False, init=False, repr=False
    )


series_keywords_assoc = Table(
    "series_keywords_assoc",
    Base.metadata,
    Column("series_id", ForeignKey("series.id"), primary_key=True),
    Column("id", ForeignKey("series_keywords.id"), primary_key=True),
)


class SeriesKeywords(Base):
    __tablename__ = "series_keywords"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), default=None)

    # relationships
    series: Mapped[list["Series"]] = relationship(
        secondary=series_keywords_assoc,
        back_populates="keywords",
        init=False,
        default_factory=list,
        repr=False,
    )


class SeriesVideos(Base):
    __tablename__ = "series_videos"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    iso_639_1: Mapped[str | None] = mapped_column(default=None)
    iso_3166_1: Mapped[str | None] = mapped_column(default=None)
    name: Mapped[str | None] = mapped_column(default=None)
    key: Mapped[str | None] = mapped_column(String(255), default=None)
    site: Mapped[str | None] = mapped_column(String(255), default=None)
    size: Mapped[int | None] = mapped_column(default=None)
    type: Mapped[str | None] = mapped_column(String(255), default=None)
    official: Mapped[bool | None] = mapped_column(default=None)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    # relationships
    series_id: Mapped[int] = mapped_column(
        ForeignKey("series.id"), init=False, nullable=True
    )
    series: Mapped["Series"] = relationship(
        back_populates="videos", init=False, repr=False
    )


class Series(Base):
    __tablename__ = "series"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    backdrop_path: Mapped[str | None] = mapped_column(String(255), default=None)
    first_air_date: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    homepage: Mapped[str | None] = mapped_column(default=None)
    imdb_id: Mapped[str | None] = mapped_column(String(12), default=None)
    in_production: Mapped[bool | None] = mapped_column(default=None)
    last_air_date: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    name: Mapped[str | None] = mapped_column(default=None)
    number_of_episodes: Mapped[int | None] = mapped_column(default=None)
    number_of_seasons: Mapped[int | None] = mapped_column(default=None)
    origin_country: Mapped[str | None] = mapped_column(String(64), default=None)
    original_language: Mapped[str | None] = mapped_column(String(64), default=None)
    original_name: Mapped[str | None] = mapped_column(default=None)
    overview: Mapped[str | None] = mapped_column(default=None)
    popularity: Mapped[float | None] = mapped_column(default=None)
    poster_path: Mapped[str | None] = mapped_column(String(255), default=None)
    status: Mapped[str | None] = mapped_column(default=None)
    tagline: Mapped[str | None] = mapped_column(default=None)
    type: Mapped[str | None] = mapped_column(default=None)
    vote_average: Mapped[float | None] = mapped_column(default=None)
    vote_count: Mapped[int | None] = mapped_column(BigInteger, default=None)

    created_by: Mapped[list[SeriesCreatedBy]] = relationship(
        secondary=series_created_by_assoc,
        back_populates="series",
        default_factory=list,
    )
    genres: Mapped[list[SeriesGenres]] = relationship(
        secondary=series_genres_assoc,
        back_populates="series",
        default_factory=list,
    )
    last_episode_to_air_id: Mapped[int | None] = mapped_column(
        ForeignKey("series_last_episode_to_air.id"), init=False, default=None
    )
    last_episode_to_air: Mapped[SeriesLastEpisodeToAir | None] = relationship(
        back_populates="series",
        default=None,
        uselist=False,
    )
    next_episode_to_air_id: Mapped[int | None] = mapped_column(
        ForeignKey("series_next_episode_to_air.id"), init=False
    )
    next_episode_to_air: Mapped[SeriesNextEpisodeToAir | None] = relationship(
        back_populates="series",
        default=None,
        uselist=False,
    )
    networks: Mapped[list[SeriesNetworks]] = relationship(
        secondary=series_networks_assoc, back_populates="series", default_factory=list
    )
    production_companies: Mapped[list[SeriesProductionCompanies]] = relationship(
        secondary=series_companies_assoc, back_populates="series", default_factory=list
    )
    production_countries: Mapped[list[SeriesProductionCountries]] = relationship(
        secondary=series_countries_assoc, back_populates="series", default_factory=list
    )
    seasons: Mapped[list["SeriesSeasons"]] = relationship(
        back_populates="series", default_factory=list, cascade="all, delete-orphan"
    )
    spoken_languages: Mapped[list[SeriesSpokenLanguages]] = relationship(
        secondary=series_languages_assoc, back_populates="series", default_factory=list
    )
    alternative_titles: Mapped[list[SeriesAlternativeTitles]] = relationship(
        back_populates="series", cascade="all, delete-orphan", default_factory=list
    )
    cast_members: Mapped[list[SeriesCastMembers]] = relationship(
        secondary=series_cast_assoc,
        back_populates="series",
        default_factory=list,
    )
    external_ids: Mapped[SeriesExternalIDs | None] = relationship(
        back_populates="series", uselist=False, default=None
    )
    keywords: Mapped[list[SeriesKeywords]] = relationship(
        secondary=series_keywords_assoc, back_populates="series", default_factory=list
    )
    videos: Mapped[list[SeriesVideos]] = relationship(
        back_populates="series", default_factory=list, cascade="all, delete-orphan"
    )
