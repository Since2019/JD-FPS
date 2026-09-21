# Surface assets

Downloaded 2026-09-09 from Poly Haven's asset download service; 1K diffuse, DirectX normal and roughness maps.

- [Concrete Wall 006](https://polyhaven.com/a/concrete_wall_006)
- [Concrete Floor 02](https://polyhaven.com/a/concrete_floor_02), Rob Tuytel
- [Poly Haven asset license: CC0](https://polyhaven.com/license)

The materials use world-space triplanar projection, independent roughness and decoded world-space normals. Metal and cloth shaders are authored in `prepare_look.py`; they do not reuse the concrete texture.

Optic geometry and shader lines are authored for this prototype. The visual reference is [ELCAN SpecterDR 1x/4x and CX5395](https://armament.com/products/elcan-specterdr-1x4x). No manufacturer image is embedded in the game. A weapon-mounted lens renders a live 1x view with the reticle etched into the same surface; 4x switching and calibrated long-distance ballistic marks are not implemented.
