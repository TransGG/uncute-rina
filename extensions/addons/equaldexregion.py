class EqualDexRegion:
    # noinspection LongLine
    """
    A class containing an EqualDex API response.

    :ivar id: A short `ISO Code`_ of a
     country. Some examples: America: US, Germany: DE,
     United Kingdom: GB.
    :ivar name: The English name of the country.
    :ivar continent: The English continent name of the country.
    :ivar url: A url to the equaldex.com page with more information
     about the laws.
    :ivar issues: A list or dictionary of issues related to the laws of
     the country.

    .. ISO Code: https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements # noqa
    """
    def __init__(self, data: dict):
        """
        Create a region shell to neatly encapsulate and separate api data.

        :param data: A dictionary with keys 'region_id', 'name',
         'continent', 'url', and 'issues'.
        """
        self.id: str = data['region_id']
        self.name: str = data['name']
        self.continent = data['continent']
        self.url: str = data['url']
        self.issues: dict[
            str,
            list[str] | dict[str, dict[str, str]]
        ] = data['issues']
