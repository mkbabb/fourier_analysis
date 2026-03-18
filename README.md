# `fourier-analysis`

Companion code for [_An Introduction to Fourier Analysis_](paper/fourier_paper.pdf). Fourier series computation, basis decomposition (Chebyshev, Legendre), epicycle reconstruction, contour tracing, and an interactive web demo.

## About

This package implements the computational backbone for the paper _An Introduction to Fourier Analysis_ by me, Michael Babb, a mathematical exposition that develops Fourier series from the dual vantage of linear algebra and complex analysis, proceeding through the DFT and its applications. The code here generates every figure in the paper and exposes the core operations (coefficient extraction, reconstruction, partial sums, epicycle chains, multi-basis decomposition) as a usable library.

The project progenates from `fourier-animate` (February 2019), an earlier Fourier series epicycle visualization tool built concurrently with [`mdarray`](https://github.com/mkbabb/mdarray). Where that project was narrowly scoped to epicycles tracing closed curves in the complex plane, this one covers the full pipeline from contour extraction through tour ordering, Fourier decomposition, and animation rendering, plus the figure generation apparatus for the paper itself.

Fourier coefficients are extracted via FFT, reconstruction inverts them, and partial sums truncate the spectrum to _N_ harmonics. Epicycle chains reify those coefficients as rotating phasors sorted by amplitude. The `bases` module extends this to Chebyshev and Legendre polynomial decompositions (Legendre coefficients are derived from Chebyshev via coefficient conversion rather than fitted independently), enabling side-by-side comparison of how different orthogonal systems approximate the same contour. The contour module handles extracting and ordering edge paths from raster images so they can be fed to the Fourier machinery.

## Installation

```bash
uv sync
```

With development dependencies ([pytest](https://docs.pytest.org/), [ruff](https://docs.astral.sh/ruff/), mypy, pre-commit):

```bash
uv sync --extra dev
```

With web demo dependencies (FastAPI, Motor, etc.):

```bash
uv sync --extra web
```

Requires Python 3.12+.

## CLI

The package installs a `fourier` command with five subcommands:

```bash
# Generate all 25 paper figures
fourier figures

# Generate specific figures
fourier figures --only F19 F20 F21

# Epicycle reconstruction from an image
fourier epicycles photo.jpg -n 200 -o reconstruction.png

# Fourier coefficients from a signal file
fourier series signal.txt -n 50 -o spectrum.png

# Render an epicycle animation
fourier animate photo.jpg -n 200 --duration 30 -o output.mp4

# Compare basis approximations (Fourier, Chebyshev, Legendre)
fourier bases photo.jpg -n 200 --degrees 3,10,50,200 -o comparison.png
```

Run `fourier --help` or `fourier <subcommand> --help` for full option listings.

## Usage (Library)

### Fourier coefficients and reconstruction

```python
import numpy as np
from fourier_analysis import fourier_coefficients, fourier_reconstruct, partial_sum

# Compute coefficients of a signal
signal = np.sin(2 * np.pi * 3 * np.arange(128) / 128)
coeffs = fourier_coefficients(signal)

# Reconstruct at higher resolution
recon = fourier_reconstruct(coeffs, n_points=512)

# Partial sum with N harmonics
S_10 = partial_sum(signal, n_harmonics=10)
```

### Epicycle decomposition

```python
from fourier_analysis import EpicycleChain

chain = EpicycleChain.from_signal(signal, n_harmonics=50)

# Evaluate the chain at time t in [0, 1)
point = chain.evaluate(0.25)

# Get cumulative arm positions for drawing
positions = chain.positions_at(0.25)
```

### Multi-basis decomposition

```python
from fourier_analysis import approximate_curve, BasisDecomposition
from fourier_analysis.bases import evaluate_partial_sum

# Decompose a complex contour into Fourier, Chebyshev, and Legendre bases
approx = approximate_curve(contour_points, max_degree=200)

# Each basis's decomposition is accessible
fourier_decomp = approx.fourier
cheb_x = approx.x["chebyshev"]
leg_y = approx.y["legendre"]

# Evaluate a partial sum at a given truncation degree
curve = evaluate_partial_sum(fourier_decomp, degree=50, n_eval=1000)
```

### Contour extraction and ordering

Seven [strategies](src/fourier_analysis/contours/) are available:

| Strategy             | Best for                 | Method                                                                                                                                            |
| -------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `auto` (default)     | General use              | 5-stage pipeline: subject isolation, structure extraction, feature extraction, assembly, and tour ordering                                        |
| `threshold`          | Portraits, silhouettes   | [Otsu binarization](https://en.wikipedia.org/wiki/Otsu%27s_method) → marching squares                                                             |
| `adaptive_threshold` | Uneven lighting          | Local adaptive thresholding → marching squares                                                                                                    |
| `multi_threshold`    | Interior detail          | [Multi-Otsu](https://scikit-image.org/docs/stable/api/skimage.filters.html#skimage.filters.threshold_multiotsu) → contours at each level boundary |
| `canny`              | Line drawings, gradients | Canny edges → morphological closing → marching squares                                                                                            |
| `edge_aware`         | Photos with soft edges   | Edge-density-guided region extraction                                                                                                             |
| `ml`                 | Complex scenes           | ML-based subject isolation with configurable thresholds                                                                                           |

```python
from fourier_analysis.contours import extract_contours, resample_arc_length
from fourier_analysis.shortest_tour import order_contours

# Extract edge contours from an image as complex paths
contours = extract_contours(
    "image.png", strategy="auto", resize=768, blur_sigma=0.5,
    min_contour_area=0.001, max_contours=16, smooth_contours=0.03,
)

# Order via KDTree nearest-neighbor + 2-opt refinement, concatenate into a single path
path = order_contours(contours, method="nearest_2opt")

# Uniform arc-length resampling for accurate FFT
path = resample_arc_length(path, n_points=1024)

# Then feed to EpicycleChain
chain = EpicycleChain.from_signal(path, n_harmonics=200)
```

### Animation

```python
from fourier_analysis.animation import FourierAnimation

anim = FourierAnimation(chain, duration=30.0, fps=30, max_circles=80)
anim.render("output.mp4")       # save to file
anim.render()                    # or display interactively
```

### Figures

Regenerate all paper figures:

```bash
fourier figures
```

The figures span the paper's arc: partial sums, orthogonal projection, inner products, Fourier projection, the heat equation, Gibbs phenomenon, Fejér summation, Parseval's identity, Laurent series, DFT matrices, butterfly diagrams, Bluestein's algorithm, the convolution theorem, epicycle annotation and convergence, the contour-tracing pipeline, epicycle portrait reconstructions, SVD ellipsoids, PCA ellipses, the Runge phenomenon, and Hermite eigenfunctions.

## Web Demo

An interactive web application for exploring Fourier and polynomial basis decompositions. Upload an image, extract contours, and view thereupon the animated epicycle reconstructions.

## The mdarray connection

Both this project and [`mdarray`](https://github.com/mkbabb/mdarray) descend from `fftplusplus` (May 2018), a C++ FFTPACK port with CPython bindings and several pure-Python FFT iterations. `mdarray` carried that lineage into a full N-dimensional array library with a [Temperton](<https://doi.org/10.1016/0021-9991(83)90013-X>) staged mixed-radix FFT engine; this project applies the Fourier analysis to series, epicycles, and visualization.

The FFT backend is abstracted behind a [protocol](src/fourier_analysis/fft_backend.py) in `fft_backend.py`. By default, NumPy's FFT is used. If you have `mdarray` installed locally, you can switch:

```python
from fourier_analysis.fft_backend import set_backend

set_backend("mdarray")
```

Since `mdarray` isn't on PyPI, it's not listed as a dependency. To use it, install from a local checkout:

```bash
uv pip install -e /path/to/mdarray
```

Then `set_backend("mdarray")` will route all FFT calls through mdarray's pure-Python mixed-radix engine—useful for testing, pedagogical comparison, or environments where NumPy isn't available.


## Paper

The paper source lives in `paper/` and can be compiled with:

```bash
latexmk -pdf paper/fourier_paper.tex
```

A pre-compiled PDF is included at [`paper/fourier_paper.pdf`](paper/fourier_paper.pdf).