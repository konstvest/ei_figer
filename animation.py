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
from mathutils import Quaternion
from . utils import read_xyzw, write_xyzw, read_xyz, write_xyz, CByteReader

class CAnimation(object):
    '''
    container of EI figure animation frames
    '''
    def __init__(self):
        self.name = ''
        self.rotations = [] # rotation in w,x,y,z for each frame
        self.abs_rotation : list[Quaternion] = []
        self.translations = []
        self.morphations = []

    def read_anm(self, name, raw_data : bytearray):
        """
        Reads animation data from byte array (from .res file)
        """
        self.name = name
        parser = CByteReader(raw_data)
        rot_count = parser.read('i')

        #rotations
        for _ in range(rot_count):
            self.rotations.append(Quaternion(parser.read('ffff')))
        
        #translations
        trans_count = parser.read('i')
        for _ in range(trans_count):
            self.translations.append(parser.read('fff'))
        
        #morphations
        morhp_frame_count = parser.read('i')
        if morhp_frame_count == 0 and parser.is_EOF():
            #print('EOF reached')
            return 0
        morph_vert_count = parser.read('i')
        for _ in range(morhp_frame_count):
            morph = list()
            for _ in range(morph_vert_count):
                morph.append(parser.read('fff'))
            self.morphations.append(morph)
        if parser.is_EOF():
            #print('EOF reached')
            return 0
        return 1

    def write_anm(self):
        raw_data = b''
        raw_data += pack('i', len(self.rotations))
        for rot in self.rotations:
            raw_data += pack('%sf' % len(rot), *rot)
        #translations
        raw_data += pack('i', len(self.translations))
        for trans in self.translations:
            raw_data += pack('%sf' % len(trans), *trans)
        #morphations
        raw_data += (pack('i', len(self.morphations)))
        if len(self.morphations) > 0:
            raw_data += pack('i', len(self.morphations[0]))
        for frame in self.morphations:
            for vec in frame:
                raw_data += pack('%sf' % len(vec), *vec)
        return raw_data

    def import_anm(self, path):
        """
        Reads animations file
        """
        self.name = os.path.basename(path)
        with open(path, 'rb') as anm_file:
            #rotations
            rot_count = unpack('i', anm_file.read(4))[0]
            for _ in range(rot_count):
                self.rotations.append(read_xyzw(anm_file))
            #translations
            trans_count = unpack('i', anm_file.read(4))[0]
            for _ in range(trans_count):
                self.translations.append(read_xyz(anm_file))
            #morphations
            morhp_frame_count = unpack('i', anm_file.read(4))[0]
            if morhp_frame_count == 0 and anm_file.read(1) == b'':
                #print('EOF reached')
                return 0
            morph_vert_count = unpack('i', anm_file.read(4))[0]
            for _ in range(morhp_frame_count):
                morph = list()
                for _ in range(morph_vert_count):
                    morph.append(read_xyz(anm_file))
                self.morphations.append(morph)
        return 0

    def export_anm(self, path):
        """
        Writes animation data to file
        """
        with open(path, 'wb') as anm_file:
            #rotations
            anm_file.write(pack('i', len(self.rotations)))
            for rot in self.rotations:
                write_xyzw(anm_file, rot)
            #translations
            anm_file.write(pack('i', len(self.translations)))
            for trans in self.translations:
                write_xyz(anm_file, trans)
            #morphations
            anm_file.write(pack('i', len(self.morphations)))
            if len(self.morphations) > 0:
                anm_file.write(pack('i', len(self.morphations[0])))
            for frame in self.morphations:
                for vec in frame:
                    write_xyz(anm_file, vec)

        return 0