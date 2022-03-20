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
from struct import pack, unpack
from . utils import CByteReader

class CLink():
    def __init__(self):
        self.root = ''
        self.links = dict()

    def read_lnk(self, raw_data : bytearray):
        parser = CByteReader(raw_data)
        link_number = parser.read('i')
        for _ in range(link_number):
            part_len = parser.read('i')
            part = parser.read(part_len*'s').decode().rstrip('\x00')
            part_len = parser.read('i')
            if part_len == 0:
                self.links[part] = None
                self.root = part
            else:
                parent = parser.read(part_len*'s').decode().rstrip('\x00')
                self.links[part] = parent
        if parser.is_EOF():
            #print('EOF reached')
            return 0
        return 1
        

    def write_lnk(self):
        raw_data = b''
        #root
        raw_data += pack('i', len(self.links.keys()))
        data = self.root.encode() + b'\x00'
        raw_data += pack('i', len(data))
        raw_data += pack(str(len(data))+'s', data)
        #add empty parent for root
        raw_data += pack('i', 0)
        for key, value in self.links.items():
            if value is None:
                continue #root
            data = key.encode() + b'\x00'
            raw_data += pack('i', len(data))
            raw_data += pack(str(len(data))+'s', data)
            data = value.encode() + b'\x00'
            raw_data += pack('i', len(data))
            raw_data += pack(str(len(data))+'s', data)

        return raw_data

    def import_lnk(self, lnkpath):
        '''
        Reads EI link file (links beetween model parts)
        '''
        file = open(lnkpath, 'rb')
        link_number = unpack('i', file.read(4))[0]
        for _ in range(link_number):
            tmp1 = unpack('i', file.read(4))[0]
            child = unpack(str(tmp1 - 1) + 's', file.read(tmp1 - 1))[0].decode()
            file.read(1)
            tmp1 = unpack('i', file.read(4))[0]
            if tmp1 == 0:
                self.links[child] = None
                self.root = child
            else:
                parent = unpack(str(tmp1 - 1) + 's', file.read(tmp1 - 1))[0].decode()
                file.read(1)
                self.links[child] = parent
        file.close()
        return

    def export_lnk(self, lnk_path):
        """
        Writes EI link file (links beetween model parts)
        """
        if not self.links:
            return 1

        with open(lnk_path, 'wb') as lnk_file:
            # write root mesh
            lnk_file.write(pack('i', len(self.links.keys())))
            str_format = str(len(self.root + 'a')) + 's'
            lnk_file.write(pack('i', len(self.root) + 1))
            lnk_file.write(pack(str_format, self.root.encode()))
            lnk_file.write(pack('i', 0))

            #write parts
            for key, value in self.links.items():
                if key == self.root:
                    continue

                lnk_file.write(pack('i', len(key) + 1))
                lnk_file.write(pack(str(len(key) + 1) + 's', key.encode()))
                lnk_file.write(pack('i', len(value) + 1))
                lnk_file.write(pack(str(len(value) + 1) + 's', value.encode()))

        return 0

    def add(self, child, parent):
        self.links[child] = parent
        if parent is None:
            self.root = child
