import base64

def encode_hash_to_b64(hash_bytes: bytes) -> str:
    return base64.b64encode(hash_bytes).decode("utf-8")

def decode_hash_from_b64(b64_string: str) -> bytes:
    return base64.b64decode(b64_string.encode("utf-8"))