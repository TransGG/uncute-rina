class EqualDexRegion:
    def __init__(self, data):
        self.id = data['region_id']
        self.name = data['name']
        self.continent = data['continent']
        self.url = data['url']
        self.issues = data['issues']