"""Generate all figures for the Fourier Analysis paper.

Usage:
    uv run python -m fourier_analysis.figures.generate_all
"""

from __future__ import annotations

import sys
import traceback

from fourier_analysis.figures import (
    f02_partial_sums,
    f03_projection,
    f04_function_as_vector,
    f05_inner_product_1,
    f06_inner_product_2,
    f07_fourier_projection,
    f08_heat_plate,
    f09_gibbs,
    f10_fejer_vs_partial,
    f11_parseval,
    f12_laurent_annulus,
    f13_laurent_to_fourier,
    f14_dft_matrix,
    f15_butterfly,
    f16_bluestein,
    f17_convolution_theorem,
    f18_epicycle_annotated,
    f19_epicycle_convergence,
    f20_contour_pipeline,
)

GENERATORS = [
    ("F02", f02_partial_sums),
    ("F03", f03_projection),
    ("F04", f04_function_as_vector),
    ("F05", f05_inner_product_1),
    ("F06", f06_inner_product_2),
    ("F07", f07_fourier_projection),
    ("F08", f08_heat_plate),
    ("F09", f09_gibbs),
    ("F10", f10_fejer_vs_partial),
    ("F11", f11_parseval),
    ("F12", f12_laurent_annulus),
    ("F13", f13_laurent_to_fourier),
    ("F14", f14_dft_matrix),
    ("F15", f15_butterfly),
    ("F16", f16_bluestein),
    ("F17", f17_convolution_theorem),
    ("F18", f18_epicycle_annotated),
    ("F19", f19_epicycle_convergence),
    ("F20", f20_contour_pipeline),
]


def main() -> int:
    failed: list[str] = []

    for name, module in GENERATORS:
        print(f"Generating {name}...", end=" ", flush=True)
        try:
            module.generate()
            print("OK")
        except Exception:
            print("FAILED")
            traceback.print_exc()
            failed.append(name)

    if failed:
        print(f"\n{len(failed)} figure(s) failed: {', '.join(failed)}")
        return 1

    print(f"\nAll {len(GENERATORS)} figures generated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
