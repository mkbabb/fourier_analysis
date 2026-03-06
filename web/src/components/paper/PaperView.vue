<script setup lang="ts">
import MathBlock from "./MathBlock.vue";
import MathInline from "./MathInline.vue";
import PaperSection from "./PaperSection.vue";
import Theorem from "./Theorem.vue";
import { ArrowRight, Sparkles } from "lucide-vue-next";
</script>

<template>
    <article class="paper-article mx-auto max-w-3xl px-6 py-14 leading-relaxed animate-fade-in">
        <!-- Title block — Fraunces display with boil effect -->
        <header class="mb-20 text-center">
            <h1
                class="fraunces text-4xl font-bold tracking-tight sm:text-5xl md:text-[3.25rem] depth-text leading-[1.15]"
                style="filter: url(#title-boil)"
            >
                An Introduction to<br />Fourier Analysis
            </h1>
            <p class="mt-5 text-lg tracking-wide text-muted-foreground" style="font-variant: small-caps;">
                From Heat Equations to Epicycles — An Interactive Companion
            </p>
            <div class="mt-8 flex items-center justify-center gap-3">
                <router-link
                    to="/visualize"
                    class="group inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground shadow-sm transition-all duration-200 hover:shadow-md hover:opacity-90 btn-press"
                >
                    <Sparkles class="h-4 w-4" />
                    Try the Demo
                    <ArrowRight class="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
                </router-link>
            </div>
        </header>

        <!-- ═══ Chapter 1: Introduction ═══ -->
        <PaperSection id="introduction" number="1" title="Introduction">
            <p>
                In 1807, Joseph Fourier presented a remarkable claim to the French
                Academy of Sciences: any periodic function can be decomposed into a sum of
                sines and cosines. This idea, initially met with skepticism from
                luminaries like Lagrange and Laplace, would go on to transform
                mathematics, physics, and engineering.
            </p>
            <p class="mt-4">
                The central object of study is the
                <em>Fourier series</em> of a periodic function
                <MathInline tex="f" />:
            </p>
            <MathBlock
                tex="f(x) = \frac{a_0}{2} + \sum_{n=1}^{\infty} \bigl( a_n \cos(nx) + b_n \sin(nx) \bigr)"
            />
            <p>
                Or equivalently, in complex exponential form:
            </p>
            <MathBlock tex="f(x) = \sum_{n=-\infty}^{\infty} c_n \, e^{inx}" />
            <p>
                where the Fourier coefficients are given by:
            </p>
            <MathBlock
                tex="c_n = \frac{1}{2\pi} \int_{-\pi}^{\pi} f(x) \, e^{-inx} \, dx"
            />
        </PaperSection>

        <!-- ═══ Chapter 2: Convergence ═══ -->
        <PaperSection id="convergence" number="2" title="Convergence of Fourier Series">
            <p>
                The partial sums
                <MathInline tex="S_N(x) = \sum_{n=-N}^{N} c_n e^{inx}" />
                approximate the original function with increasing accuracy as
                <MathInline tex="N \to \infty" />. But the nature of this convergence
                depends critically on the regularity of <MathInline tex="f" />.
            </p>

            <Theorem type="theorem" name="Dirichlet's Theorem">
                If <MathInline tex="f" /> is piecewise smooth and periodic, then the
                Fourier series converges to <MathInline tex="f(x)" /> at every point of
                continuity, and to
                <MathInline tex="\tfrac{1}{2}\bigl[f(x^+) + f(x^-)\bigr]" /> at points of
                discontinuity.
            </Theorem>

            <p class="mt-4">
                Near discontinuities, the partial sums exhibit the
                <em>Gibbs phenomenon</em>: an overshoot of approximately
                <MathInline tex="9\%" /> that does not diminish as
                <MathInline tex="N \to \infty" />, only narrows.
            </p>

            <div class="interactive-callout">
                <p class="font-medium text-foreground mb-2">Interactive: Partial sums with adjustable <MathInline tex="N" /></p>
                <router-link
                    to="/visualize"
                    class="inline-flex items-center gap-1.5 text-sm text-primary hover:underline transition-colors"
                >
                    Open in Visualize tab
                    <ArrowRight class="h-3.5 w-3.5" />
                </router-link>
            </div>
        </PaperSection>

        <!-- ═══ Chapter 3: DFT & FFT ═══ -->
        <PaperSection id="dft" number="3" title="The Discrete Fourier Transform">
            <p>
                For computational work, we discretize: given
                <MathInline tex="N" /> samples
                <MathInline tex="f_0, f_1, \ldots, f_{N-1}" />, the Discrete
                Fourier Transform (DFT) is:
            </p>
            <MathBlock
                tex="F_k = \sum_{n=0}^{N-1} f_n \, e^{-2\pi i \, kn / N}, \quad k = 0, 1, \ldots, N-1"
            />
            <p>
                The Fast Fourier Transform (FFT) computes this in
                <MathInline tex="O(N \log N)" /> operations via the Cooley–Tukey
                butterfly decomposition.
            </p>
        </PaperSection>

        <!-- ═══ Chapter 4: Eigenbasis ═══ -->
        <PaperSection id="bases" number="4" title="Beyond Fourier: Orthogonal Polynomial Bases">
            <p>
                The Fourier basis <MathInline tex="\{e^{inx}\}" /> is optimal for
                periodic signals, but for finite-interval approximation, polynomial
                bases can converge faster. We compare three orthogonal systems:
            </p>

            <Theorem type="definition" name="Chebyshev Polynomials">
                The Chebyshev polynomials of the first kind are defined by
                <MathInline tex="T_n(\cos\theta) = \cos(n\theta)" />, satisfying the
                orthogonality relation:
                <MathBlock
                    tex="\int_{-1}^{1} \frac{T_m(x)\, T_n(x)}{\sqrt{1-x^2}} \, dx = \begin{cases} 0 & m \neq n \\ \pi/2 & m = n \neq 0 \\ \pi & m = n = 0 \end{cases}"
                />
            </Theorem>

            <Theorem type="definition" name="Legendre Polynomials">
                The Legendre polynomials satisfy
                <MathInline
                    tex="\int_{-1}^{1} P_m(x)\, P_n(x) \, dx = \frac{2}{2n+1}\, \delta_{mn}"
                />, and arise as eigenfunctions of the Legendre differential equation.
            </Theorem>

            <p class="mt-4">
                Given a parametric curve
                <MathInline tex="z(t) = x(t) + iy(t)" />, we can decompose the real
                and imaginary parts independently in each basis. The truncated series
                at degree <MathInline tex="N" /> produces an approximation whose
                quality depends on the smoothness of the curve and the choice of basis.
            </p>
        </PaperSection>

        <!-- ═══ Chapter 5: Epicycles ═══ -->
        <PaperSection id="epicycles" number="5" title="Epicycles and Curve Tracing">
            <p>
                The complex Fourier series
                <MathInline tex="f(t) = \sum c_n\, e^{2\pi i n t}" /> has a beautiful
                geometric interpretation: each term
                <MathInline tex="c_n\, e^{2\pi i n t}" /> is a rotating vector
                (phasor) with angular velocity <MathInline tex="n" />, amplitude
                <MathInline tex="|c_n|" />, and initial phase
                <MathInline tex="\arg(c_n)" />.
            </p>
            <p class="mt-4">
                Chaining these vectors tip-to-tail produces an epicycle machine whose
                tip traces the original curve. Sorting by descending amplitude
                concentrates the large-scale shape in the first few circles; the
                remaining circles add progressively finer detail.
            </p>
            <div class="interactive-callout">
                <p class="font-medium text-foreground mb-2">Interactive: Upload an image and watch epicycles trace its contour</p>
                <router-link
                    to="/visualize"
                    class="inline-flex items-center gap-1.5 text-sm text-primary hover:underline transition-colors"
                >
                    Open in Visualize tab
                    <ArrowRight class="h-3.5 w-3.5" />
                </router-link>
            </div>
        </PaperSection>

        <!-- ═══ Chapter 6: Applications ═══ -->
        <PaperSection id="applications" number="6" title="Applications">
            <p>
                The contour extraction pipeline transforms a raster image into a
                Fourier-representable path: grayscale conversion, Gaussian blur,
                multi-Otsu thresholding, marching squares contour extraction, tour
                optimization via 2-opt, and arc-length resampling.
            </p>
            <p class="mt-4">
                With the resampled contour in hand, we compute the FFT to obtain
                Fourier coefficients, construct an epicycle chain, and animate the
                reconstruction. The same pipeline now supports Chebyshev and Legendre
                decompositions for comparison.
            </p>
        </PaperSection>
    </article>
</template>

<style scoped>
.paper-article {
    font-feature-settings: "liga", "kern";
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    hyphens: auto;
}

/* Interactive callout cards */
.interactive-callout {
    margin: 2rem 0;
    padding: 1.25rem 1.5rem;
    border-radius: 0.75rem;
    border: 1px solid hsl(var(--border));
    background: hsl(var(--card));
    text-align: center;
    font-size: 0.875rem;
    color: hsl(var(--muted-foreground));
    transition: transform 0.3s cubic-bezier(0.25, 0.1, 0.25, 1),
                box-shadow 0.3s cubic-bezier(0.25, 0.1, 0.25, 1),
                border-color 0.3s ease;
}

.interactive-callout:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.05);
    border-color: hsl(var(--primary) / 0.2);
}

:deep(.dark) .interactive-callout:hover {
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}
</style>
