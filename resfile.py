import copy
import io
import struct
from dataclasses import dataclass
from datetime import datetime

from . helpers import read_exactly

_SIGNATURE = 0x019CE23C
_HEADER_FORMAT = '<LLLL'
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)
_TABLE_ENTRY_FORMAT = '<lLLLHL'
_TABLE_ENTRY_SiZE = struct.calcsize(_TABLE_ENTRY_FORMAT)


class InvalidResFile(Exception):
    pass


@dataclass
class ResFileItemInfo:

    name: str
    file_size: int
    file_offset: int
    modify_time: datetime


class _ResSubFile(io.BufferedIOBase):

    def __init__(self, file: io.BufferedIOBase, mode, entry: ResFileItemInfo, close_cb):
        super().__init__()
        self._file = file
        self._mode = mode
        self._entry = entry
        self._close_cb = close_cb

        assert mode in ('r', 'w')
        self._file.seek(self._entry.file_offset)

    @property
    def mode(self):
        return self._mode

    def readable(self):
        return self._mode == 'r'

    def writable(self):
        return self._mode == 'w'

    def read(self, size=-1):
        self._check_closed('read')
        if not self.readable():
            raise io.UnsupportedOperation('file not open for reading')
        if size < 0:
            size = self._entry.file_size

        return self._file.read(min(size, self._entry.file_size - self.tell()))

    def write(self, data):
        self._check_closed('write')
        if not self.writable():
            raise io.UnsupportedOperation('file not open for writing')

        self._file.write(data)
        self._entry.file_size = max(self._entry.file_size, self.tell())

    def tell(self):
        self._check_closed('tell')
        return self._file.tell() - self._entry.file_offset

    def seek(self, pos, whence=0):
        self._check_closed('seek')

        cur_pos = self.tell()
        if whence == 0:
            new_pos = pos
        elif whence == 1:
            new_pos = cur_pos + pos
        elif whence == 2:
            new_pos = self._entry.file_size + pos
        else:
            raise ValueError('invalid whence value')

        if new_pos < 0:
            new_pos = 0
        elif self._mode == 'r':
            new_pos = min(new_pos, self._entry.file_size)
        else:
            self._entry.file_size = max(self._entry.file_size, new_pos)

        self._file.seek(new_pos + self._entry.file_offset, 0)
        return new_pos

    def close(self):
        if self.closed:  # pylint: disable=using-constant-test
            return
        try:
            super().close()
        finally:
            self._close_cb()

    def _check_closed(self, operation):
        if self.closed:  # pylint: disable=using-constant-test
            raise ValueError(f'{operation} on closed file')

    def truncate(self):
        pass


class ResFile:

    def __init__(self, file, mode='r'):
        if mode not in ('r', 'w', 'a'):
            raise ValueError('ResFile requires mode "r", "w", "a"')

        self._opened = isinstance(file, str)
        self._file = file if not self._opened else None
        self._mode = mode
        self._table = {}
        self._subfile = None

        if not self._file and self._mode == 'a':
            try:
                self._file = open(file, 'rb+')
            except FileNotFoundError:
                self._mode = 'w'

        if not self._file:
            self._file = open(file, self._mode + 'b')

        if self._mode in ('r', 'a'):
            self._read_headers()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def open(self, name, mode='r'):
        if not self._file:
            raise ValueError('ResFile is closed')
        if self._subfile:
            raise ValueError('only one opened file is allowed')

        if mode == 'r':
            entry = self._table[name]
        elif mode == 'w':
            if self._mode == 'r':
                raise ValueError('ResFile was opened in read mode, so open() requires mode "r"')
            self._write_alignment()
            entry = ResFileItemInfo(name, 0, max(_HEADER_SIZE, self._file.tell()), datetime.now())
            self._table[name] = entry
        else:
            raise ValueError('open() requires mode "r" or "w"')

        self._subfile = _ResSubFile(self._file, mode, entry, self._close_subfile)
        return self._subfile

    def get_info(self, name):
        return copy.deepcopy(self._table[name])

    def iter_files(self):
        for entry in self._table.values():
            yield copy.deepcopy(entry)

    def close(self):
        if not self._file:
            return

        try:
            if self._subfile:
                if self._subfile.mode != 'r':
                    raise ValueError("can't close the ResFile while there is an opened subfile")
                self._close_subfile()

            if self._mode != 'r':
                self._write_headers()
        finally:
            if self._opened:
                self._file.close()
            self._file = None

    def _write_alignment(self):
        end_of_files_data = (
            max(e.file_offset + e.file_size for e in self._table.values())
            if self._table else 0
        )
        self._file.seek(end_of_files_data)
        self._file.write(b'\0' * ((16 - self._file.tell() % 16) % 16))

    def _close_subfile(self):
        if self._subfile.mode != 'r':
            self._write_alignment()
        self._subfile = None

    def _read(self, size, message='Unexpected EOF'):
        try:
            return read_exactly(self._file, size)
        except Exception as ex:
            raise InvalidResFile(message) from ex

    def _lower_ascii(self, value):
        return ''.join((c.lower() if ord(c) >= 128 else c) for c in value)

    def _read_headers(self):
        self._file.seek(0, 2)
        res_file_size = self._file.tell()
        self._file.seek(0)
        header_data = self._read(_HEADER_SIZE, 'File header is truncated')
        magic, table_size, table_offset, names_size = struct.unpack(_HEADER_FORMAT, header_data)
        if magic != _SIGNATURE:
            raise InvalidResFile('Invalid signature')
        table_data_size = table_size * _TABLE_ENTRY_SiZE
        if table_offset + table_data_size + names_size > res_file_size:
            raise InvalidResFile('Files table is truncated')

        self._file.seek(table_offset)
        tables_data = self._read(table_data_size)
        names_data = self._read(names_size)
        for table_entry in struct.iter_unpack(_TABLE_ENTRY_FORMAT, tables_data):
            _, file_size, file_offset, modify_timestamp, name_length, name_offset = table_entry
            name = names_data[name_offset:name_offset+name_length].decode('cp1251')
            self._table[self._lower_ascii(name)] = ResFileItemInfo(
                name=name, file_size=file_size, file_offset=file_offset,
                modify_time=datetime.fromtimestamp(modify_timestamp)
            )

    def _write_headers(self):
        self._write_alignment()
        table_offset = self._file.tell()

        # Build hash table
        hash_table = [[None, -1] for _ in self._table]  # entry, next_index
        last_free_index = len(hash_table) - 1
        for entry in self._table.values():
            # Calculate entry's hash
            entry_hash = sum(b for b in self._lower_ascii(entry.name).encode('cp1251')) % (1 << 32)
            index = entry_hash % len(hash_table)

            # If index is busy, find another one
            if hash_table[index][0] is not None:
                while hash_table[index][1] >= 0:
                    index = hash_table[index][1]

                while hash_table[last_free_index][0] is not None:
                    last_free_index -= 1

                hash_table[index][1] = last_free_index
                index = last_free_index
                last_free_index -= 1

            # Put entry in the hash table
            hash_table[index][0] = entry

        # Write hash table
        encoded_names = []
        name_offset = 0
        for entry, next_index in hash_table:
            encoded_names.append(entry.name.encode('cp1251'))
            name_length = len(encoded_names[-1])
            data = struct.pack(
                _TABLE_ENTRY_FORMAT,
                next_index,
                entry.file_size,
                entry.file_offset,
                int(entry.modify_time.timestamp()),
                name_length,
                name_offset,
            )
            name_offset += name_length
            self._file.write(data)

        # Write file names
        self._file.write(b''.join(encoded_names))
        self._file.truncate()

        # Update file header
        self._file.seek(0)
        data = struct.pack(_HEADER_FORMAT, _SIGNATURE, len(hash_table), table_offset, name_offset)
        self._file.write(data)

    def get_filename_list(self):
        return tuple(self._table.keys())