# `fourier-analysis`

Companion code for [*An Introduction to Fourier Analysis*](paper/fourier_paper.pdf). Fourier series computation, basis decomposition (Chebyshev, Legendre), epicycle reconstruction, contour tracing, and an interactive web demo.

## About

This package implements the computational backbone for the paper *An Introduction to Fourier Analysis* by me, Michael Babb—a mathematical exposition that develops Fourier series from the dual vantage of linear algebra and complex analysis, proceeding through the DFT and its applications. The code here generates every figure in the paper and exposes the core operations (coefficient extraction, reconstruction, partial sums, epicycle chains, multi-basis decomposition) as a usable library.

The project descends from `fourier-animate` (February 2019), an earlier Fourier series epicycle visualization tool built concurrently with [`mdarray`](https://github.com/mkbabb/mdarray). Where that project was narrowly scoped—epicycles tracing closed curves in the complex plane—this one broadens the aperture: the full pipeline from contour extraction through tour ordering, Fourier decomposition, and animation rendering, plus the figure generation apparatus for the paper itself.

The core computational path is deliberately simple. Fourier coefficients are extracted via FFT, reconstruction inverts them, and partial sums truncate the spectrum to *N* harmonics. Epicycle chains reify those coefficients as rotating phasors sorted by amplitude. The `bases` module extends this to Chebyshev and Legendre polynomial decompositions, enabling side-by-side comparison of how different orthogonal systems approximate the same contour. The contour module handles the messier business of extracting and ordering edge paths from raster images so they can be fed to the Fourier machinery.

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
# Generate all 21 paper figures
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

Four [strategies](src/fourier_analysis/contours.py) are available:

| Strategy | Best for | Method |
|---|---|---|
| `auto` (default) | General use | Otsu threshold + morphological cleanup (both polarities), falls back to `multi_threshold` |
| `threshold` | Portraits, silhouettes | [Otsu binarization](https://en.wikipedia.org/wiki/Otsu%27s_method) → marching squares |
| `multi_threshold` | Interior detail | [Multi-Otsu](https://scikit-image.org/docs/stable/api/skimage.filters.html#skimage.filters.threshold_multiotsu) → contours at each level boundary |
| `canny` | Line drawings, gradients | Canny edges → morphological closing → marching squares |

```python
from fourier_analysis.contours import extract_contours, resample_arc_length
from fourier_analysis.shortest_tour import order_contours

# Extract edge contours from an image as complex paths
contours = extract_contours(
    "image.png", strategy="auto", resize=512, blur_sigma=1.0,
    min_contour_area=0.01, max_contours=10, smooth_contours=0.2,
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

## Web Demo

An interactive web application for exploring Fourier and polynomial basis decompositions. Upload an image, extract contours, and watch epicycles trace the result in real time.

### Architecture

- **Frontend**: Vue 3 + Vite 7 + Tailwind v4 SPA with Canvas 2D epicycle renderer, KaTeX math rendering, and a build-time LaTeX paper parser
- **Backend**: FastAPI with Motor (async MongoDB) for sessions and GridFS for image storage
- **Database**: MongoDB 7 with TTL-indexed sessions (auto-expire after 30 days)
- **Proxy**: nginx reverse proxy with rate limiting in production

### Running locally

The simplest path is the dev script, which starts both servers with hot-reload:

```bash
# Requires: Python 3.12+, Node 22+, MongoDB on localhost:27017
./scripts/dev.sh
```

This launches uvicorn on port 8000 and Vite on port 3000, with `/api` requests proxied to the backend.

Alternatively, with Docker:

```bash
docker compose up
```

### Deployment

Production uses a two-file compose overlay with an nginx entry point:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

The deploy script (`scripts/deploy.sh`) pushes to GitHub, SSHs to the production host, pulls, rebuilds, and runs health checks. Environment variables are documented in `.env.example`.

### Frontend features

- **Paper view**: the LaTeX paper parsed at build time into navigable, collapsible sections with KaTeX-rendered math and theorem blocks
- **Visualization view**: image upload (drag-and-drop), contour parameter tuning (strategy, blur, area filtering, max contours, contour smoothing), basis selection (Fourier/Chebyshev/Legendre), animated epicycle canvas, coefficient panel, frame export
- **Session persistence**: slug-based URLs (`/s/big-red-angry-python`), stored in MongoDB with GridFS-backed images

### API endpoints

All routes are prefixed with `/api`:

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/sessions` | Create session (generates a 4-word slug) |
| `GET` | `/sessions/{slug}` | Get session |
| `PUT` | `/sessions/{slug}` | Update contour/animation settings |
| `DELETE` | `/sessions/{slug}` | Delete session and its image |
| `POST` | `/sessions/{slug}/upload` | Upload image (SHA-256 dedup) |
| `GET` | `/sessions/{slug}/image` | Retrieve image from GridFS |
| `POST` | `/sessions/{slug}/compute/contours` | Extract contours |
| `POST` | `/sessions/{slug}/compute/epicycles` | Compute Fourier epicycle decomposition |
| `POST` | `/sessions/{slug}/compute/bases` | Compute multi-basis decomposition |

## Structure

```
fourier_analysis/
    assets/                      # Generated figures (PDF + PNG)
        portraits/               # Input images for epicycle reconstruction
    paper/
        fourier_paper.tex        # Paper source
        fourier_paper.bib        # Bibliography
        fourier_paper.pdf        # Compiled paper
    src/fourier_analysis/
        __init__.py              # Public API exports
        cli.py                   # CLI entry point (fourier command)
        series.py                # Fourier coefficients, reconstruction, partial sums
        epicycles.py             # EpicycleComponent, EpicycleChain
        bases.py                 # Multi-basis decomposition (Fourier, Chebyshev, Legendre)
        fft_backend.py           # FFT backend abstraction (NumPy / mdarray)
        contours.py              # Contour extraction (Otsu, multi-Otsu, Canny), area filtering, contour ranking, smoothing
        shortest_tour.py         # KDTree nearest-neighbor + 2-opt tour ordering
        animation.py             # Matplotlib epicycle animation renderer
        figures/
            generate_all.py      # Driver for all 21 paper figures
            f01_title_epicycle.py  # ...through f21_epicycle_portraits.py
            style.py             # Shared matplotlib styling
    api/
        main.py                  # FastAPI app with lifespan, CORS, router mounting
        config.py                # pydantic-settings configuration
        dependencies.py          # Slug validation, session lookup, GridFS access
        slugs.py                 # Human-readable slug generation (coolname)
        Dockerfile               # Multi-stage (dev + prod targets)
        models/
            session.py           # Session document models
            computation.py       # Compute request/response models
        routers/
            sessions.py          # Session CRUD
            images.py            # Image upload/retrieval (GridFS)
            compute.py           # Contour, epicycle, and basis compute endpoints
        services/
            database.py          # Motor client lifecycle, TTL index
            computation.py       # Wraps fourier_analysis library for async compute
    web/
        package.json             # Vue 3, Pinia, KaTeX, Tailwind v4, Vite 7
        vite.config.ts           # Dev proxy, LaTeX paper plugin, path aliases
        Dockerfile               # Multi-stage (dev Vite / prod nginx)
        src/
            App.vue              # Shell: header, router view, SVG filters
            router/index.ts      # /paper, /visualize, /s/:slug routes
            stores/
                session.ts       # Session CRUD, image upload, compute dispatch
                animation.ts     # rAF-driven animation loop, scrubbing, speed
            components/
                paper/           # PaperView, PaperSection, theorem/math blocks
                visualization/   # VisualizationView, BasisCanvas, AnimationControls,
                                 #   ImageUpload, ContourSettings, BasisSelector,
                                 #   CoefficientsPanel, ExportModal
                ui/              # Reusable primitives (toggle, slider, select, tooltip)
            lib/
                api.ts           # Backend API client
                bases.ts         # Client-side Fourier/Chebyshev/Legendre evaluation
                math-worker.ts   # Web Worker for off-thread trace precomputation
        plugins/
            vite-plugin-latex-paper.ts  # Parses fourier_paper.tex into structured JSON at build time
    nginx/
        fourier.conf             # Reverse proxy config (rate limiting, sub-path rewriting)
    scripts/
        dev.sh                   # Local dev launcher (uvicorn + Vite, port discovery)
        deploy.sh                # Production deploy (SSH, build, health check)
    tests/
        test_series.py           # Coefficient, reconstruction, Parseval, shift theorem tests
        test_epicycles.py        # Epicycle chain tests
        test_contours.py         # Contour extraction and resampling tests
        test_shortest_tour.py    # Tour ordering tests
        test_fft_backend.py      # Backend switching tests
        test_bases.py            # Multi-basis decomposition and animation data tests
```

## Figures

Regenerate all 21 paper figures:

```bash
fourier figures
```

The figures span the paper's arc—partial sums, orthogonal projection, inner products, Fourier projection, the heat equation, Gibbs phenomenon, Fejér summation, Parseval's identity, Laurent series, DFT matrices, butterfly diagrams, Bluestein's algorithm, the convolution theorem, epicycle annotation and convergence, the contour-tracing pipeline, and epicycle portrait reconstructions.

## The mdarray connection

Both this project and [`mdarray`](https://github.com/mkbabb/mdarray) descend from `fftplusplus` (May 2018), a C++ FFTPACK port with CPython bindings and several pure-Python FFT iterations. `mdarray` carried that lineage into a full N-dimensional array library with a [Temperton](https://doi.org/10.1016/0021-9991(83)90013-X) staged mixed-radix FFT engine; this project applies the Fourier analysis to series, epicycles, and visualization.

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

## Testing

```bash
uv run pytest
```

59 tests covering coefficient extraction, FFT roundtrip reconstruction, upsampling, partial sum convergence, Parseval's identity, shift theorem, linearity, conjugate symmetry, epicycle chain evaluation, contour extraction strategies, arc-length resampling, tour ordering, backend switching, and multi-basis decomposition (Chebyshev fitting, Legendre conversion, partial sum convergence across all three bases, animation data structure).

## Paper

The paper source lives in `paper/` and can be compiled with:

```bash
latexmk -pdf paper/fourier_paper.tex
```

A pre-compiled PDF is included at [`paper/fourier_paper.pdf`](paper/fourier_paper.pdf).

## References

- Fourier, J.B.J. *Théorie analytique de la chaleur.* Cambridge University Press, 1878.
- Stein, E.M. and Shakarchi, R. [*Fourier Analysis: An Introduction.*](https://press.princeton.edu/books/hardcover/9780691113845/fourier-analysis) Princeton Lectures in Analysis, Princeton University Press, 2003.
- Axler, S. [*Linear Algebra Done Right.*](https://linear.axler.net/) 3rd ed., Springer, 2015.
- Ahlfors, L.V. *Complex Analysis.* 3rd ed., McGraw-Hill, 1979.
- Kreyszig, E. *Introductory Functional Analysis with Applications.* Wiley, 1978.
- Cooley, J.W. and Tukey, J.W. ["An Algorithm for the Machine Calculation of Complex Fourier Series."](https://doi.org/10.1090/S0025-5718-1965-0178586-1) *Math. Comp.* **19**(90), 297–301 (1965).
- Bluestein, L.I. ["A Linear Filtering Approach to the Computation of the Discrete Fourier Transform."](https://doi.org/10.1109/TAU.1970.1162132) *IEEE Trans. Audio Electroacoust.* **18**(4), 451–455 (1970).
- Temperton, C. ["Self-Sorting Mixed-Radix Fast Fourier Transforms."](https://doi.org/10.1016/0021-9991(83)90013-X) *J. Comput. Phys.* **52**, 1–23 (1983).
- Van Loan, C.F. *Computational Frameworks for the Fast Fourier Transform.* SIAM, 1992.

## License

MIT
