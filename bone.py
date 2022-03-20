# Copyright (c) 2022 konstvest

# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
from struct import pack, unpack
from . utils import CByteReader

class CBone(object):
    '''
    Bone positions for morphing components
    '''
    def __init__(self):
        self.name = ''
        self.pos = [] #(0.0, 0.0, 0.0) for _ in range(8)

    def read_bon(self, name, raw_data : bytearray):
        self.name = name
        parser = CByteReader(raw_data)
        for _ in range(8):
            self.pos.append(parser.read('fff'))
        return 0
    
    def write_bon(self):
        raw_data = b''
        for pos in self.pos:
            raw_data += pack('%sf' % len(pos), *pos)
        return raw_data

    def import_bon(self, path):
        '''
        Reads bone positions from file
        '''
        self.name = os.path.basename(path)
        with open(path, 'rb') as bon_file:
            btmp = [0, 0, 0]
            for _ in range(8): #morphing components
                for orig in range(3):
                    btmp[orig] = unpack('f', bon_file.read(4))[0]
                self.pos.append(tuple(btmp))
        return 0

    def export_bon(self, path):
        '''
        Writes bone position in file
        '''
        with open(path, 'wb') as bon_file:
            for mrph_cmp in range(8):
                for xyz in range(3):
                    bon_file.write(pack('f', self.pos[mrph_cmp][xyz]))
    
    def fillPositions(self):
        for _ in range(1, 8):
            self.pos.append(self.pos[0])
