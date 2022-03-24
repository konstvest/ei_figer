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
from . utils import CByteReader, unpack_uv, pack_uv, pack, unpack, \
    read_x, read_xy, read_xyz, read_xyzw, write_xy, write_xyz, write_xyzw, \
    get_uv_convert_count

class CFigure(object):
    '''
    3D model with morphing components
    '''
    def __init__(self):
        self.name = ''
# header:
# vertex_count
# normal_count
# texcoord_count
# index_count
# vertex_component_count
# morph_component_count
# unknown
# group
# texture_number
        self.header = [0 for _ in range(9)]
        self.center = [] #(0.0, 0.0, 0.0) for _ in range(8)
        self.fmin = [] #(0.0, 0.0, 0.0) for _ in range(8)
        self.fmax = [] #(0.0, 0.0, 0.0) for _ in range(8)
        self.radius = [] #0.0 for _ in range(8)
        # [main], [strength], [dexterity], [unique] and scaled once
        self.verts = [[], [], [], [], [], [], [], []]
        self.normals = []
        #texture coordinates
        self.t_coords = []
        #indicies
        self.indicies = []
        #vertex components
        self.v_c = []
        self.m_c = []
        self.morph_count = 8

    def __eq__(self, other):
        if not isinstance(other, CFigure):
            # don't attempt to compare against unrelated types
            return NotImplemented

        is_equal = self.header == other.header and self.center == other.center and self.fmin == other.fmin
        is_equal = is_equal and self.fmax == other.fmax and self.radius == other.radius
        is_equal = is_equal and self.indicies == other.indicies and self.v_c == other.v_c
        #TODO: set precision for compare points
        is_equal = is_equal and self.verts == other.verts and self.normals == other.normals
        is_equal = is_equal and self.t_coords == other.t_coords

        return is_equal

    def read_fig(self, name, raw_data : bytearray):
        self.name = name
        parser = CByteReader(raw_data)
        signature = parser.read('ssss').decode()
        if signature != 'FIG8':
            print(self.name + ' has unknown figure signature: ' + signature)
            return 2

        # header
        for i in range(9):
            self.header[i] = parser.read('i')
        # Center
        for _ in range(self.morph_count):
            self.center.append(parser.read('fff'))
        # MIN
        for _ in range(self.morph_count):
            self.fmin.append(parser.read('fff'))
        # MAX
        for _ in range(self.morph_count):
            self.fmax.append(parser.read('fff'))
        # Radius
        for _ in range(self.morph_count):
            self.radius.append(parser.read('f'))
        # VERTICES
        block = [[[0 for _ in range(3)] for _ in range(8)] for _ in range(4)]
        for _ in range(self.header[0]):
            for xyz in range(3):
                for i in range(self.morph_count):  #morphing component
                    for cur_block in range(4):  #block with 4 verts
                        block[cur_block][i][xyz] = parser.read('f')
            #convert verts from block 4*n to 1-row data
            for cur_block in range(4):
                for i in range(self.morph_count):
                    self.verts[i].append(tuple(block[cur_block][i][0:3]))
        del block
        # NORMALS
        for i in range(self.header[1]*4): #normal count * block_size(4)
            self.normals.append(parser.read('ffff'))
        # TEXTURE COORDS
        for _ in range(self.header[2]):
            t_coord = parser.read('ff')
            self.t_coords.append(list(t_coord))
        unpack_uv(self.t_coords, get_uv_convert_count(self.name))
        # INDICES
        for _ in range(self.header[3]):
            self.indicies.append(parser.read('h'))
        # VERTICES COMPONENTS
        for _ in range(self.header[4]):
            parser.read('h') #TODO: fix missing data here (vert index)
            self.v_c.append(parser.read('hh'))
        # MORHING COMPONENTS
        for _ in range(self.header[5]):
            self.m_c.append(parser.read('hh'))
        
        if parser.is_EOF():
            #print('EOF reached')
            return 0
        return 1

    def write_fig(self):
        raw_data = b''
        
        if len(self.normals) != self.header[1]*4: #normal count * block_size(4)
            print('normals count corrupted')
        if len(self.t_coords) != self.header[2]:
            print('texture coordinates count corrupted')
        if len(self.indicies) != self.header[3]:
            print('indices count corrupted')
        if len(self.m_c) != self.header[5]:
            print('morph components count corrupted')
        if len(self.center) != 8 or len(self.fmin) != 8 or len(self.fmax) != 8 or len(self.center) != 8:
            print('aux data components count corrupted')
        raw_data += pack('4s', b'FIG8')
        # header
        for header_ind in range(9):
            raw_data += pack('i', self.header[header_ind])
        # center
        for vec in self.center:
            raw_data += pack('%sf' % len(vec), *vec)
        # min
        for vec in self.fmin:
            raw_data += pack('%sf' % len(vec), *vec)
        # max
        for vec in self.fmax:
            raw_data += pack('%sf' % len(vec), *vec)
        # radius
        for rad in self.radius:
            raw_data += pack('f', rad)
        # verts
        block_index = 0
        for _ in range(self.header[0]):
            for xyz in range(3):
                for i in range(self.morph_count):
                    for cur_block_ind in range(4):
                        raw_data += pack('f', self.verts[i][block_index + cur_block_ind][xyz])
            block_index += 4
        # normals
        block_index = 0
        
        for vec in self.normals: 
            raw_data += pack('%sf' % len(vec), *vec)
        # texture coordinates
        pack_uv(self.t_coords, get_uv_convert_count(self.name))
        
        for vec in self.t_coords:
            raw_data += pack('%sf' % len(vec), *vec)
        # indicies
        for ind in self.indicies:
            raw_data += pack('h', ind)
        # vertex components
        for vec in self.v_c:
            raw_data += pack('h', vec[0]) #TODO: save real data instead copy of 0 element
            raw_data += pack('hh', vec[0], vec[1])
        # morphing components
        for vec in self.m_c:
            raw_data += pack('%sh' % len(vec), *vec)
        return raw_data

    def import_fig(self, fig_path):
        '''
        Reads data from figure file
        '''
        with open(fig_path, 'rb') as fig_file:
            # SIGNATURE
            if fig_file.read(4) != b'FIG8':
                print('figure header is not correct')
                return 2

            # HEADER
            for ind in range(9):
                self.header[ind] = unpack('i', fig_file.read(4))[0]
            # Center
            for _ in range(self.morph_count):
                self.center.append(read_xyz(fig_file))
            # MIN
            for _ in range(self.morph_count):
                self.fmin.append(read_xyz(fig_file))
            # MAX
            for _ in range(self.morph_count):
                self.fmax.append(read_xyz(fig_file))
            # Radius
            for _ in range(self.morph_count):
                self.radius.append(unpack('f', fig_file.read(4))[0])
            # VERTICES
            block = [[[0 for _ in range(3)] for _ in range(8)] for _ in range(4)]
            for _ in range(self.header[0]):
                for xyz in range(3):
                    for i in range(self.morph_count):  #morphing component
                        for cur_block in range(4):  #block with 4 verts
                            block[cur_block][i][xyz] = unpack('f', fig_file.read(4))[0]
                #convert verts from block 4*n to 1-row data
                for cur_block in range(4):
                    for i in range(self.morph_count):
                        self.verts[i].append(tuple(block[cur_block][i][0:3]))
            del block
            # NORMALS
            for i in range(self.header[1]*4): #normal count * block_size(4)
                self.normals.append(read_xyzw(fig_file))
            # TEXTURE COORDS
            for _ in range(self.header[2]):
                t_coord = read_xy(fig_file)
                self.t_coords.append(list(t_coord))
            unpack_uv(self.t_coords, get_uv_convert_count(self.name))
            # INDICES
            for _ in range(self.header[3]):
                self.indicies.append(read_x(fig_file))
            # VERTICES COMPONENTS
            for _ in range(self.header[4]):
                fig_file.read(2) #TODO: fix missing data here (vert index)
                self.v_c.append(read_xy(fig_file, 'short'))
            # MORHING COMPONENTS
            for _ in range(self.header[5]):
                self.m_c.append(read_xy(fig_file, 'short'))
            
            if fig_file.read(1) == b'':
                # print('EOF reached')
                return 0
        return 1

    def export_fig(self, fig_path):
        '''
        Writes figure file
        '''
        with open(fig_path, 'wb') as fig_file:
            # signature
            fig_file.write(b'FIG8')
            # header
            for header_ind in range(9):
                fig_file.write(pack('i', self.header[header_ind]))
            # center
            for i in range(self.morph_count):
                write_xyz(fig_file, self.center[i])
            # min
            for i in range(self.morph_count):
                write_xyz(fig_file, self.fmin[i])
            # max
            for i in range(self.morph_count):
                write_xyz(fig_file, self.fmax[i])
            # radius
            for i in range(self.morph_count):
                fig_file.write(pack('f', self.radius[i]))
            # verts
            block_index = 0
            for _ in range(self.header[0]):
                for xyz in range(3):
                    for i in range(self.morph_count):
                        for cur_block_ind in range(4):
                            fig_file.write(pack('f', self.verts[i][block_index + cur_block_ind][xyz]))
                block_index += 4
            # normals
            block_index = 0
            for i in range(self.header[1]*4): #normal count * block_size(4)
                write_xyzw(fig_file, self.normals[i])
            # texture coordinates
            pack_uv(self.t_coords, get_uv_convert_count(self.name))
            for tex_ind in range(self.header[2]):
                write_xy(fig_file, self.t_coords[tex_ind])
            # indicies
            for i in range(self.header[3]):
                fig_file.write(pack('h', self.indicies[i]))
            # vertex components
            for i in range(self.header[4]):
                fig_file.write(pack('h', self.v_c[i][0])) #TODO: save real data instead copy of 0 element
                write_xy(fig_file, self.v_c[i], 'h')
            # morphing components
            for i in range(self.header[5]):
                write_xy(fig_file, self.m_c[i], 'h')
    
    def fillVertices(self):
        for i in range(1, 8):
            self.verts[i] = self.verts[0]

    def fillAux(self):
        for i in range(1, 8):
            self.fmin.append(self.fmin[0])
            self.fmax.append(self.fmax[0])
            self.center.append(self.center[0])
            self.radius.append(self.radius[0])


    def generate_m_c(self):
        self.m_c = []
        for i in range(self.header[5]):
            self.m_c.append(tuple([i, i]))