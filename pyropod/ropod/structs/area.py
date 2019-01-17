class SubArea(object):
    def __init__(self):
        self.id = ''
        self.name = ''
        self.x = -1.
        self.y = -1.

    def to_dict(self):
        sub_area_dict = dict()
        sub_area_dict['name'] = self.name
        sub_area_dict['id'] = self.id
        sub_area_dict['x'] = self.x
        sub_area_dict['y'] = self.y
        return sub_area_dict

    @staticmethod
    def from_dict(sub_area_dict):
        sub_area = SubArea()
        sub_area.name = sub_area_dict['name']
        sub_area.id = sub_area_dict['id']
        sub_area.x = sub_area_dict['x']
        sub_area.y = sub_area_dict['y']
        return sub_area

class Area(object):
    def __init__(self):
        self.id = ''
        self.name = ''
        self.sub_areas = list()
        self.floor_number = 0
        self.type = ''

    def to_dict(self):
        area_dict = dict()
        area_dict['id'] = self.id
        area_dict['name'] = self.name
        area_dict['subAreas'] = list()
        area_dict['floorNumber'] = self.floor_number
        area_dict['type'] = self.type
        for sub_area in self.sub_areas:
            area_dict['subAreas'].append(sub_area.to_dict())
        return area_dict

    @staticmethod
    def from_dict(area_dict):
        area = Area()
        area.id = area_dict['id']
        area.name = area_dict['name']
        area.floor_number = area_dict['floorNumber']
        area.type = area_dict['type']
        for sub_areas_dict in area_dict['subAreas']:
            sub_area = SubArea.from_dict(sub_areas_dict)
            area.sub_areas.append(sub_area)
        return area
