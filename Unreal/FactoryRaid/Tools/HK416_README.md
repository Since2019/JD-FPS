# HK416 + EOTech XPS3

Restart either `启动工厂.cmd` or `启动破冰船.cmd` to load the new runtime.

- Primary 1: HK416, 30 starting rounds, mounted XPS3 holographic sight.
- Primary 2: existing MK18 with Specter optic.
- 1 / 2 select primary slots; X swaps; right mouse aims; left mouse fires.
- Inventory drag/drop moves the actual item; ammunition stays with that item.
- XPS3 uses a nonmagnifying window and a view-direction-based red ring/dot material on the window mesh. It is not a HUD crosshair. Mechanical sight material is hidden on the HK416 to keep the optical window clear.

The HK416 skeletal mesh and XPS3 static mesh include their imported material textures. Existing native weapon Blueprint and first-person hand rig still provide firing and hand poses; a new HK416 reload animation was not authored. The optic is mounted by weapon type, not a separately draggable attachment yet.

Validation: `test_hk416.py` runs PIE, captures hip/ADS views, fires five rounds, switches to MK18 and back, checks preserved ammunition and ADS alignment. This is automated engine validation, not a new physical-input test. Existing grid-inventory unit tests also pass.

Asset provenance: see `ImportedWeapons/SOURCES.md`.
