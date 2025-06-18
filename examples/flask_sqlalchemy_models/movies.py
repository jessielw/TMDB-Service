from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column, relationship

from your_app_service import db # UPDATE


class MovieCollections(db.Model, MappedAsDataclass):
    __bind_key__ = "tmdb"
    __tablename__ = "movie_collections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str | None] = mapped_column(default=None)
    poster_path: Mapped[str | None] = mapped_column(String(255), default=None)
    backdrop_path: Mapped[str | None] = mapped_column(String(255), default=None)

    # relationships
    movies: Mapped[list["Movie"]] = relationship(
        back_populates="belongs_to_collection",
        init=False,
        cascade="all, delete-orphan",
        single_parent=True,
        default_factory=list,
        repr=False,
    )


movie_genres_assoc = db.Table(
    "movie_genres_assoc",
    Column("movie_id", ForeignKey("movie.id"), primary_key=True),
    Column("genre_id", ForeignKey("movie_genres.id"), primary_key=True),
    bind_key="tmdb",
)


class MovieGenres(db.Model, MappedAsDataclass):
    __bind_key__ = "tmdb"
    __tablename__ = "movie_genres"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str | None] = mapped_column(String(255), default=None)

    # relationships
    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_genres_assoc, back_populates="genres", init=False, repr=False
    )


movie_companies_assoc = db.Table(
    "movie_companies_assoc",
    Column("movie_id", ForeignKey("movie.id"), primary_key=True),
    Column("company_id", ForeignKey("movie_production_companies.id"), primary_key=True),
    bind_key="tmdb",
)


class MovieProductionCompanies(db.Model, MappedAsDataclass):
    __bind_key__ = "tmdb"
    __tablename__ = "movie_production_companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str | None] = mapped_column(default=None)
    origin_country: Mapped[str | None] = mapped_column(String(255), default=None)
    logo_path: Mapped[str | None] = mapped_column(String(255), default=None)

    # relationships
    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_companies_assoc,
        back_populates="production_companies",
        init=False,
        repr=False,
    )


movie_countries_assoc = db.Table(
    "movie_countries_assoc",
    Column("movie_id", ForeignKey("movie.id"), primary_key=True),
    Column(
        "country_id",
        ForeignKey("movie_production_countries.iso_3166_1"),
        primary_key=True,
    ),
    bind_key="tmdb",
)


class MovieProductionCountries(db.Model, MappedAsDataclass):
    __bind_key__ = "tmdb"
    __tablename__ = "movie_production_countries"

    iso_3166_1: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(default=None)

    # relationships
    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_countries_assoc,
        back_populates="production_countries",
        init=False,
        repr=False,
    )


movie_languages_assoc = db.Table(
    "movie_languages_assoc",
    Column("movie_id", ForeignKey("movie.id"), primary_key=True),
    Column(
        "language_id", ForeignKey("movie_spoken_languages.iso_639_1"), primary_key=True
    ),
    bind_key="tmdb",
)


class MovieSpokenLanguages(db.Model, MappedAsDataclass):
    __bind_key__ = "tmdb"
    __tablename__ = "movie_spoken_languages"

    iso_639_1: Mapped[str] = mapped_column(primary_key=True)
    english_name: Mapped[str | None] = mapped_column(String(255), default=None)
    name: Mapped[str | None] = mapped_column(String(255), default=None)

    # relationships
    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_languages_assoc,
        back_populates="spoken_languages",
        init=False,
        repr=False,
    )


class MovieAlternativeTitles(db.Model, MappedAsDataclass):
    __bind_key__ = "tmdb"
    __tablename__ = "movie_alternative_titles"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, init=False
    )
    iso_3166_1: Mapped[str | None] = mapped_column(default=None)
    title: Mapped[str | None] = mapped_column(default=None)
    type: Mapped[str | None] = mapped_column(default=None)

    # relationships
    movie_id: Mapped[int | None] = mapped_column(ForeignKey("movie.id"), default=None)
    movie: Mapped["Movie | None"] = relationship(
        back_populates="alternative_titles", default=None, repr=False
    )


movie_cast_assoc = db.Table(
    "movie_cast_assoc",
    Column("movie_id", ForeignKey("movie.id"), primary_key=True),
    Column("cast_id", ForeignKey("movie_cast_members.id"), primary_key=True),
    bind_key="tmdb",
)


class MovieCastMembers(db.Model, MappedAsDataclass):
    __bind_key__ = "tmdb"
    __tablename__ = "movie_cast_members"

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
    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_cast_assoc,
        back_populates="cast_members",
        init=False,
        repr=False,
    )


class MovieExternalIDs(db.Model, MappedAsDataclass):
    __bind_key__ = "tmdb"
    __tablename__ = "movie_external_ids"

    movie_id: Mapped[int] = mapped_column(ForeignKey("movie.id"), primary_key=True)
    imdb_id: Mapped[str | None] = mapped_column(String(255), default=None)
    wikidata_id: Mapped[str | None] = mapped_column(String(255), default=None)
    facebook_id: Mapped[str | None] = mapped_column(String(255), default=None)
    instagram_id: Mapped[str | None] = mapped_column(String(255), default=None)
    twitter_id: Mapped[str | None] = mapped_column(String(255), default=None)

    # relationships
    movie: Mapped["Movie"] = relationship(
        back_populates="external_ids", uselist=False, init=False, repr=False
    )


movie_keywords_assoc = db.Table(
    "movie_keywords_assoc",
    Column("movie_id", ForeignKey("movie.id"), primary_key=True),
    Column("id", ForeignKey("movie_keywords.id"), primary_key=True),
    bind_key="tmdb",
)


class MovieKeywords(db.Model, MappedAsDataclass):
    __bind_key__ = "tmdb"
    __tablename__ = "movie_keywords"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), default=None)

    # relationships
    movie: Mapped[list["Movie"]] = relationship(
        secondary=movie_keywords_assoc,
        back_populates="keywords",
        init=False,
        default_factory=list,
        repr=False,
    )


class MovieReleaseDates(db.Model, MappedAsDataclass):
    __bind_key__ = "tmdb"
    __tablename__ = "movie_release_dates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, init=False)
    iso_3166_1: Mapped[str | None] = mapped_column(default=None)
    certification: Mapped[str | None] = mapped_column(default=None)
    release_date: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    type: Mapped[int | None] = mapped_column(default=None)
    note: Mapped[str | None] = mapped_column(default=None)
    movie_id: Mapped[int | None] = mapped_column(ForeignKey("movie.id"), default=None)

    movie: Mapped["Movie"] = relationship(
        back_populates="release_dates", default=None, repr=False
    )


class MovieVideos(db.Model, MappedAsDataclass):
    __bind_key__ = "tmdb"
    __tablename__ = "movie_videos"

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
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movie.id"), init=False, nullable=True
    )
    movie: Mapped["Movie"] = relationship(
        back_populates="videos", init=False, repr=False
    )


class Movie(db.Model, MappedAsDataclass):
    __bind_key__ = "tmdb"
    __tablename__ = "movie"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    backdrop_path: Mapped[str | None] = mapped_column(String(255), default=None)
    budget: Mapped[int | None] = mapped_column(BigInteger, default=None)
    homepage: Mapped[str | None] = mapped_column(default=None)
    imdb_id: Mapped[str | None] = mapped_column(String(12), default=None)
    origin_country: Mapped[str | None] = mapped_column(default=None)
    original_language: Mapped[str | None] = mapped_column(String(64), default=None)
    original_title: Mapped[str | None] = mapped_column(default=None)
    overview: Mapped[str | None] = mapped_column(default=None)
    popularity: Mapped[float | None] = mapped_column(default=None)
    poster_path: Mapped[str | None] = mapped_column(String(255), default=None)
    release_date: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    revenue: Mapped[int | None] = mapped_column(BigInteger, default=None)
    runtime: Mapped[int | None] = mapped_column(default=None)
    status: Mapped[str | None] = mapped_column(default=None)
    tagline: Mapped[str | None] = mapped_column(default=None)
    title: Mapped[str | None] = mapped_column(default=None)
    video: Mapped[bool | None] = mapped_column(default=None)
    vote_average: Mapped[float | None] = mapped_column(default=None)
    vote_count: Mapped[int | None] = mapped_column(BigInteger, default=None)

    belongs_to_collection_id: Mapped[int | None] = mapped_column(
        ForeignKey("movie_collections.id"), init=False, default=None
    )
    belongs_to_collection: Mapped[MovieCollections | None] = relationship(
        back_populates="movies", default=None
    )

    genres: Mapped[list[MovieGenres]] = relationship(
        secondary=movie_genres_assoc,
        back_populates="movies",
        default_factory=list,
    )
    production_companies: Mapped[list[MovieProductionCompanies]] = relationship(
        secondary=movie_companies_assoc, back_populates="movies", default_factory=list
    )
    production_countries: Mapped[list[MovieProductionCountries]] = relationship(
        secondary=movie_countries_assoc, back_populates="movies", default_factory=list
    )
    spoken_languages: Mapped[list[MovieSpokenLanguages]] = relationship(
        secondary=movie_languages_assoc, back_populates="movies", default_factory=list
    )
    alternative_titles: Mapped[list[MovieAlternativeTitles]] = relationship(
        back_populates="movie", cascade="all, delete-orphan", default_factory=list
    )
    cast_members: Mapped[list[MovieCastMembers]] = relationship(
        secondary=movie_cast_assoc,
        back_populates="movies",
        default_factory=list,
    )
    external_ids: Mapped[MovieExternalIDs | None] = relationship(
        back_populates="movie",
        uselist=False,
        default=None,
    )
    keywords: Mapped[list[MovieKeywords]] = relationship(
        secondary=movie_keywords_assoc, back_populates="movie", default_factory=list
    )
    release_dates: Mapped[list[MovieReleaseDates]] = relationship(
        back_populates="movie",
        default_factory=list,
        cascade="all, delete-orphan",
        repr=False,
    )
    videos: Mapped[list[MovieVideos]] = relationship(
        back_populates="movie", default_factory=list, cascade="all, delete-orphan"
    )
