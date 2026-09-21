# Verification — 2026-09-08

Engine: Godot 4.7.2, Windows, Compatibility renderer, AMD Radeon RX 7900 XTX.

Command:
`Godot --headless --fixed-fps 60 --path . --script res://tests/factory_smoke.gd -- --test`

Final result: 40 checks PASS, exit code 0, no script errors or navigation warnings.

Coverage: physical/logical Tab, Alt+R and Alt+T, navigation around obstacles, ascending both office stair flights from ground, office/catwalk entry, basement descent/cross passage, acceleration, crouch/stand collision, magazine and chamber round conservation, dropped magazines, individual cartridge loading, limb injury and timed treatment, held search, wall occlusion, muzzle obstruction, ballistic head hit, corpse loot, grenade cover, closed/open doors, keyed/free extraction and interruption, loot persistence, backpack occupancy and fatal injury.

Native UI checks via computer-use: deployment button starts the raid, Tab opens/closes inventory after logical-key compatibility fix, C changes stance and camera height. A normal AI-enabled test run also reached the death summary. Other combat/traversal checks above were deterministic engine tests, not claims of human full-raid playthrough or EFT feel equivalence.

Rendered and inspected actual engine captures: classic-factory.png, classic-office.png, classic-pack.png, classic-tunnel.png. Preview captures pause AI and use fixed cameras. These are development screenshots, not evidence of visual parity with Escape from Tarkov.
