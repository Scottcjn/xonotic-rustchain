from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAP_DIR = ROOT / "pk3_build" / "maps"
NAME = "rustchain_ledger_exchange"


def test_ledger_exchange_delivery_files_exist():
    expected = [f"{NAME}.map", f"{NAME}.bsp", f"{NAME}.mapinfo", f"{NAME}.tga",
                f"{NAME}.README.md", f"{NAME}.LICENSE"]
    missing = [f for f in expected if not (MAP_DIR / f).exists()]
    assert missing == []


def test_ledger_exchange_mapinfo_and_entities_are_playable():
    mapinfo = (MAP_DIR / f"{NAME}.mapinfo").read_text(encoding="utf-8")
    map_text = (MAP_DIR / f"{NAME}.map").read_text(encoding="utf-8")
    assert "has weapons" in mapinfo
    assert "gametype dm" in mapinfo
    assert "gametype ca" in mapinfo
    assert map_text.count('"classname" "info_player_deathmatch"') >= 8
    assert map_text.count('"classname" "weapon_') >= 2
    assert map_text.count('"classname" "item_') >= 1
    assert "prins1bap-ui" in map_text or "prins1bap-ui" in mapinfo


def test_ledger_exchange_bsp_and_levelshot_have_expected_headers():
    bsp = (MAP_DIR / f"{NAME}.bsp").read_bytes()
    tga = (MAP_DIR / f"{NAME}.tga").read_bytes()
    assert bsp[:4] == b"IBSP"
    assert len(bsp) > 100_000
    assert len(tga) > 100_000
