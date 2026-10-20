from shared.crypto import decrypt, encrypt, keyed_hash


def test_encrypt_round_trip():
    token = encrypt("52998224725")

    assert decrypt(token) == "52998224725"


def test_token_does_not_contain_plain_text():
    assert "52998224725" not in encrypt("52998224725")


def test_encrypt_is_not_deterministic():
    assert encrypt("52998224725") != encrypt("52998224725")


def test_keyed_hash_is_deterministic_and_distinct():
    first = keyed_hash("52998224725")

    assert first == keyed_hash("52998224725")
    assert first != keyed_hash("11144477735")
    assert len(first) == 64
    assert "52998224725" not in first
