from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAP_DIR = ROOT / "pk3_build" / "maps"
NAME = "rustchain_antiquity_vault"


def test_antiquity_vault_delivery_files_exist():
    expected = [
        f"{NAME}.map",
        f"{NAME}.bsp",
        f"{NAME}.mapinfo",
        f"{NAME}.tga",
        f"{NAME}.README.md",
        f"{NAME}.LICENSE",
    ]

    missing = [filename for filename in expected if not (MAP_DIR / filename).exists()]
    assert missing == []


def test_antiquity_vault_mapinfo_and_entities_are_playable():
    mapinfo = (MAP_DIR / f"{NAME}.mapinfo").read_text(encoding="utf-8")
    map_text = (MAP_DIR / f"{NAME}.map").read_text(encoding="utf-8")

    assert "has weapons" in mapinfo
    assert "gametype dm" in mapinfo
    assert "gametype ca" in mapinfo
    assert "RustChain Antiquity Vault" in map_text
    assert map_text.count('"classname" "info_player_deathmatch"') >= 10
    assert map_text.count('"classname" "weapon_') >= 7
    assert map_text.count('"classname" "light"') >= 6


def test_antiquity_vault_bsp_and_levelshot_have_expected_headers():
    bsp = (MAP_DIR / f"{NAME}.bsp").read_bytes()
    tga = (MAP_DIR / f"{NAME}.tga").read_bytes()

    assert bsp[:4] == b"IBSP"
    assert len(bsp) > 100_000
    assert tga[2] == 2  # uncompressed true-color TGA
    assert int.from_bytes(tga[12:14], "little") >= 512
    assert int.from_bytes(tga[14:16], "little") >= 384
