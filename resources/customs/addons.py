class EqualDexRegion:
    def __init__(self, data: dict):
        """
        Create a region shell to neatly encapsulate and separate api data.

        ### Parameters
        data: :class:`dict`
            A dictionary with keys 'region_id', 'name', 'continent', 'url', and 'issues'.
        """
        self.id = data['region_id']
        self.name: str = data['name']
        self.continent = data['continent']
        self.url: str = data['url']
        self.issues: dict[str, list | dict[str, str]] = data['issues']
