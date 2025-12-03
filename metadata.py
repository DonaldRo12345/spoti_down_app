class ContributorData:

    def __init__(self, title:str = None, track:int = None, artist_name:str = None) -> None:
        self.contributor_name = artist_name
        self.role1 = "artists"
        self.role2 = "composers"
        self.role3 = "producers"
        self.role4 = ""
        self.release_title = title
        self.track = ""
        self.spotify_id = ""
        self.apple_music_id = ""

    def has_numbers(self, any_string):
        return any(char.isdigit() for char in any_string)

    def get_attributes(self):
        list_attrs = list(self.__dict__.keys())
        return list(filter(lambda x: self.has_numbers(x), list_attrs))

    def set_attributes(self, attr_value:str):
        for value in self.get_attributes():
            setattr(self, value, attr_value)

    def set_track(self, index:int):
        self.track += str(index)

    def __str__(self) -> str:
        return self.contributor_name + "" + self.release_title

class MetaData:
    """define song metadata models"""

    def __init__(self, song_data: dict) -> None:
        if isinstance(song_data, dict):
            self.song_data = song_data
        else:
            raise Exception(f"song_data param {song_data} is not a dict ")

        try:
            self._title = song_data["TAG"]["title"]
        except KeyError:
            self._title = "Unknow title"
        try:
            self._num_track = song_data["TAG"]["track"]
        except KeyError:
            self._num_track = 0

        self._disc = "1"
        try:
            self._genre = song_data["TAG"]["genre"]
        except KeyError:
            self._genre = "Pop"
        try:
            self._artist = song_data["TAG"]["artist"]
        except KeyError:
            self._artist = "Unknow artist"
        try:
            self._album = song_data["TAG"]["album"]
        except KeyError:
            self._album = "Unknow artist"
        try:
            self._tsrc = song_data["TAG"]["isrc"]
        except KeyError:
            self._tsrc = ""
        try:
            self._album_artist = song_data["TAG"]["album_artist"]
        except KeyError:
            self._album_artist = "Unknow album artist"
        try:
            self._publisher = song_data["TAG"]["publisher"]
        except KeyError:
            self._publisher = "Unknow publisher"
        try:
            self._date = song_data["TAG"]["date"]
        except KeyError:
            self._date = "2020"

        self._contributor = ContributorData(title=self._album, track=self._num_track, artist_name=self._artist)

    @property
    def title(self):
        return self._title

    @property
    def num_track(self) -> int:
        return self._num_track

    @num_track.setter
    def num_track(self, num_track: int):
        self._num_track = num_track
        self._contributor.track = num_track

    @property
    def disc(self):
        return self._disc

    @property
    def genre(self):
        return self._genre

    @property
    def artist(self):
        return self._artist

    @property
    def album(self):
        return self._album

    @album.setter
    def album(self, album_name):
        self._album = album_name
        self._contributor.release_title = album_name

    @property
    def isrc(self):
        return self._tsrc

    @property
    def album_artist(self):
        return self._album_artist

    @property
    def publisher(self):
        return self._publisher

    @property
    def date(self):
        return self._date

    @property
    def contributor(self):
        return self._contributor

    def __repr__(self) -> str:
        return f"title: {self.title}\n num track:{self.num_track} \n disc:{self.disc} \n\
            artist:{self.artist}\n album:{self.album} \n album artist:{self.album_artist}"

    def __str__(self) -> str:
        return f"{self.title}"


class XlsMeta:

    def format_date(self, date:str):
        if "-" in date:
            return date.split('-')[0]
        return date

    def __init__(self, song_metada: MetaData = None) -> None:
        self._song_metadata = song_metada

        if self._song_metadata:
            self.track_number = self._song_metadata.num_track
            self.track_title = self._song_metadata.title
            self.subtitle = ""
            self.cd_number = self._song_metadata.disc
            self.release_title = self._song_metadata.album # mettre ici le titre de l'album
            self.label = self.release_title
            self.production_year = self.format_date(self._song_metadata.date)
            self.production_owner = self.release_title
            self.copyright_owner = self.release_title
            self.genre = self._song_metadata.genre
            self.sub_genre = self._song_metadata.genre
            self.tracktype = "ORIGINAL"
            self.lyrics_language = "FRENCH"
            self.title_language = "FRENCH"
            self.parental_advisory = "NO"
            self.territorie_deliver = "WW"
            self.release_price_tier = ""
            self.track_price_tier = ""
            self.digital_release_date = ""
            self.physical_release_date = ""
            self.simple_start_index = ""
            self.isrc = self._song_metadata.isrc
            self.upc_code = ""
            self.ean_code = ""
            self.grid = ""
            self.release_catalog_number = ""
            self.track_catalog_number = ""
            self.commercial_desc_en = ""
            self.commercial_desc_fr = ""
            self.commercial_desc_gr = ""
            self.commercial_desc_it = ""
            self.commercial_desc_sp = ""
            self.contributor = self._song_metadata.contributor
        else:
            self.track_number = 1
            self.track_title = None
            self.subtitle = None
            self.cd_number = None
            self.release_title = None
            self.label = None
            self.production_year = None
            self.production_owner = None
            self.copyright_owner = None
            self.genre = None
            self.sub_genre = None
            self.tracktype = None
            self.lyrics_language = None
            self.title_language = "FRENCH"
            self.parental_advisory = "NO"
            self.territorie_deliver = None
            self.release_price_tier = None
            self.track_price_tier = None
            self.digital_release_date = "NO"
            self.physical_release_date = "Worldwide"
            self.simple_start_index = None
            self.isrc = None
            self.upc_code = None
            self.ean_code = None
            self.grid = None
            self.release_catalog_number = None
            self.track_catalog_number = None
            self.commercial_desc_en = None
            self.commercial_desc_fr = None
            self.commercial_desc_gr = None
            self.commercial_desc_it = None
            self.commercial_desc_sp = None
            self.contributor = ContributorData()
