from chunk_service import extract_chunks_from_file

chunks = extract_chunks_from_file("./pyproject.toml",".toml")
for c in chunks:
    print(c)