def read_exactly(f, size):
    remaining = size
    chunks = []
    while remaining > 0:
        data = f.read(remaining)
        if not data:
            raise Exception("Unexpected EOF")
        chunks.append(data)
        remaining -= len(data)
    return b''.join(chunks)
