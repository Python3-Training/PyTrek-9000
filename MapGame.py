import random
import TrekStrings

import Glyphs
from AbsShip import KlingonShip
from Points import Destination
from Quadrant import Quadrant
from Sectors import Sectors

import MapSparse

class GameMap(MapSparse.SparseMap):

    def __init__(self):
        super().__init__()
        self.sector = -1
        self.major_x = self.major_y = -1
        self.xpos    = self.ypos    = -1
        self.stars      = -1
        self.klingons   = -1
        self.starbases  = -1
        self.last_nav = None
        
    def place(self, takers):
        ''' 
        Randomly place game-objects, into the map.
        '''
        if not sum(takers):
            return None
        takers =list(takers)
        for which, nelem in enumerate(takers):
            if not nelem:
                continue
            to_take = random.randrange(0, nelem)
            if nelem is 1:
                to_take = 1
            if not to_take:
                continue
            taken = 0
            while taken != to_take:
                for ss, area in enumerate(self.areas()):
                    should_take = random.randrange(1, 8)
                    if should_take % (ss + 2) == 0:
                        if which is 0:
                            area.place_glyph(Glyphs.STARBASE)
                        elif which is 1:
                            area.place_glyph(Glyphs.STAR)
                        elif which is 2:
                            area.place_glyph(Glyphs.KLINGON)
                        taken += 1
                        if taken == to_take:
                            break;
            takers[which] -= taken
        return tuple(takers)

    def enterprise_in(self, glyph, dest=None):
        ''' Place the ENTERPRISE at the destination, else a 
        random one. Return the x, y location - else False '''
        area = self.area()
        if area:
            pos = area.place_glyph(Glyphs.ENTERPRISE, dest)
            if pos:
                return pos
        return False

    def enterprise_location(self):
        ''' Get Enterprise location. False if not found. '''
        area = self.area()
        if area:
            for obj in area.objs:
                if obj.glyph == Glyphs.ENTERPRISE:
                    return obj.xpos, obj.ypos
        return False

    def enterprise_out(self):
        ''' Remove the ENTERPRISE from the present AREA '''
        pos = self.enterprise_location()
        if pos:
            self.remove(*pos)

    def place_glyph(self, glyph, dest=None):
        ''' Place the glyph as the destination, else a random one '''
        area = self.area()
        if area:
            pos = area.place_glyph(self, glyph, dest)
            if pos:
                return True
        return False

    def remove(self, xpos, ypos):
        ''' Remove ANYTHING from the present AREA '''
        area = self.area()
        if area:
            area.remove(xpos, ypos)

    def area(self):
        ''' 
        Return the internal / sparsely populated AREA object.
        Return an empty / default AREA upon coordinate error.
        '''
        if self.sector > 0:
            for area in self.areas():
                if area.number == self.sector:
                    return area
        return MapSparse.SparseMap.Area()

    def scan_quad(self, sector):
        '''
        Return a scan (LRS?) for a specific quadrant.
        Return empty quadrant, on error.
        '''
        if sector > 0 and sector < 65:
            for area in self.areas():
                if area.number == self.sector:
                    return Quadrant.from_area(area)
        return Quadrant()

    def _count(self, glyph):
        ''' Tally the number of glyphs in the AREA '''
        count = 0
        area = self.area()
        if area:
            for obj in area.objs:
                if obj.glyph == glyph:
                    count += 1
        return count

    def remove_items(self, destroyed_ships):
        area = self.area()
        for obj in destroyed_ships:
            area.remove(obj.xpos, obj.ypos)

    def get_area_klingons(self):
        '''
        Return this Area's data for Kingons, in an array.
        '''
        results = []
        area = self.area()
        for data in area.get_data(Glyphs.KLINGON):
            ship = KlingonShip()
            ship.from_map(data.xpos, data.ypos)
            results.append(ship)
        return results

    def num_area_klingons(self):
        return self._count(Glyphs.KLINGON)

    def num_area_starbases(self):
        return self._count(Glyphs.STARBASE)

    def num_area_stars(self):
        return self._count(Glyphs.STAR)

    def get_area_objects(self):
        '''
        Return the actual objects, as located in the Area. 
        NOTE: Changes to this collection will update Area
        content.
        '''
        area = self.area()
        return area.objs

    def game_id(self, piece):
        '''
        Uniquely identify a game piece / object.
        '''
        area = self.area()
        num = (area.number * 100) + (piece.ypos * 8) + piece.xpos
        return f"{piece.glyph[0]}x{num}"

    def get_all(self, glyph):
        '''
        Return [ [AREA, PIECE], ... ] for every glyph found.
        '''
        results = []
        for area in self.areas():
            for piece in area.get_data(glyph):
                results.append([area, piece])
        return results

    def quad(self):
        area = self.area()
        return Quadrant.from_area(area)

    def get_map(self):
        ''' 
        Generate AREA map of the present sector.
        '''
        area = self.area()
        return area.get_map()

    def random_jump(self):
        dest = Destination(
            random.randint(1, 65),
            random.randint(0, 7),
            random.randint(0, 7)
            )
        self.go_to(dest)

    def go_to(self, dest):
        if self.last_nav:
            self.enterprise_out()
        assert(isinstance(self.sector, int))
        self.sector = dest.sector
        if self.sector > 0:
            fop = (self.sector + 8) / 8
            self.major_x = int(fop) - 1 # ZERO BASED REGIONS
            if not fop.is_integer():
                self.major_y = \
                ((fop - float(self.major_x)) * 10) - 1 # ZBR
        else:
            self.major_x = -1
            self.major_y = -1

        self.xpos = dest.xpos
        self.ypos = dest.ypos
        self.enterprise_in(dest)
        self.last_nav = dest

    def randomize(self, bases=None, stars=None, aliens=None):
        if not aliens:
            aliens = 15 + random.randint(0, 5)
        if not bases:
            bases = 2 + random.randint(0, 2)
        self.starbases = bases
        self.klingons = aliens
        self.stars = stars
        self.init()
        takers = bases, stars, aliens
        while takers:
            for lrs in self.map:
                takers = self.place(takers)
                if not takers:
                    break


