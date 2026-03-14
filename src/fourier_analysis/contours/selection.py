from __future__ import annotations

import numpy as np

from fourier_analysis.contours.candidates import (
    _ContourCandidate,
    _build_candidate,
    _build_candidate_from_masks,
    _build_candidate_from_processed,
    _hybridize_envelope_candidate,
)
from fourier_analysis.contours.image import LoadedImage
from fourier_analysis.contours.masks import (
    adaptive_threshold_masks,
    alpha_masks,
    canny_masks,
    detail_canny_masks,
    direct_iso_contours,
    edge_density_contours,
    edge_aware_masks,
    multi_threshold_masks,
    quantile_threshold_masks,
    threshold_masks,
)
from fourier_analysis.contours.ml import ml_masks
from fourier_analysis.contours.models import (
    AlphaMode,
    ContourCandidateDiagnostics,
    ContourConfig,
    ContourStrategy,
)


def _select_auto_candidate(
    image: LoadedImage,
    config: ContourConfig,
) -> tuple[_ContourCandidate | None, tuple[ContourCandidateDiagnostics, ...], tuple[str, ...]]:
    """ML-first AUTO selection.

    Always uses U²-Net saliency for subject isolation, then enriches
    with multi-threshold interior detail.  The best ML-based candidate wins.
    """
    notes: list[str] = []
    candidates: list[_ContourCandidate] = []

    if config.alpha_mode == AlphaMode.ONLY:
        if image.alpha is None:
            notes.append("alpha_mode=only requested, but the image has no usable alpha mask")
        else:
            candidates.append(
                _build_candidate_from_masks(
                    label="alpha",
                    strategy="alpha",
                    masks=alpha_masks(image),
                    used_alpha=True,
                    image=image,
                    config=config,
                    allow_jump_pruning=False,
                )
            )
        diagnostics = tuple(c.diagnostics for c in candidates)
        viable = [c for c in candidates if c.contours]
        if not viable:
            return None, diagnostics, tuple(notes)
        return max(viable, key=lambda c: c.diagnostics.score), diagnostics, tuple(notes)

    # ---- ML foundation ----
    ml_mask_set = ml_masks(image, config)

    # ML standalone: iso-probability contours from the saliency map
    ml_cand = _build_candidate_from_masks(
        label="ml",
        strategy=ContourStrategy.ML.value,
        masks=ml_mask_set,
        used_alpha=False,
        image=image,
        config=config,
        allow_jump_pruning=True,
    )
    candidates.append(ml_cand)

    # ---- Interior detail sources (multi-threshold within ML region) ----
    # Mask the grayscale to the ML subject region before thresholding,
    # so threshold levels align with subject intensity, not background.
    primary_ml_mask = ml_mask_set[0] if ml_mask_set else None

    # When alpha is available, intersect with ML for tighter subject
    # isolation — both masks must agree a pixel is subject.
    if image.alpha is not None and primary_ml_mask is not None:
        alpha_mask = image.alpha > 0.5
        alpha_coverage = float(np.mean(alpha_mask))
        if 0.05 < alpha_coverage < 0.98:
            combined = alpha_mask & primary_ml_mask
            # Only use intersection if it retains enough of the subject.
            if float(np.mean(combined)) > 0.05:
                primary_ml_mask = combined

    # Use subject mask for quantile level computation (focus thresholds
    # on the subject).  Skip contour filtering when coverage is tiny.
    ml_quantile_mask = primary_ml_mask  # always used for level computation
    if primary_ml_mask is not None:
        ml_coverage = float(np.mean(primary_ml_mask))
        if ml_coverage < 0.12:
            primary_ml_mask = None

    _DETAIL_STRATEGY_MAP = {
        "multi_threshold": ContourStrategy.MULTI_THRESHOLD.value,
        "multi_threshold_4c": ContourStrategy.MULTI_THRESHOLD.value,
        "enhanced_multi_threshold": ContourStrategy.MULTI_THRESHOLD.value,
        "enhanced_multi_threshold_4c": ContourStrategy.MULTI_THRESHOLD.value,
        "quantile": ContourStrategy.MULTI_THRESHOLD.value,
        "quantile_detail": ContourStrategy.MULTI_THRESHOLD.value,
        "threshold_dark": ContourStrategy.THRESHOLD.value,
        "adaptive_dark": ContourStrategy.ADAPTIVE_THRESHOLD.value,
        "edge_aware": ContourStrategy.EDGE_AWARE.value,
        "canny": ContourStrategy.CANNY.value,
        "detail_canny": ContourStrategy.CANNY.value,
    }

    detail_candidates: list[_ContourCandidate] = []
    for label, masks in [
        ("multi_threshold", multi_threshold_masks(image, config)),
        ("multi_threshold_4c", multi_threshold_masks(image, config, n_classes=4)),
        ("enhanced_multi_threshold", multi_threshold_masks(image, config, use_detail=True)),
        ("enhanced_multi_threshold_4c", multi_threshold_masks(image, config, use_detail=True, n_classes=4)),
        ("quantile", quantile_threshold_masks(image, config, subject_mask=ml_quantile_mask)),
        ("quantile_detail", quantile_threshold_masks(image, config, use_detail=True, subject_mask=ml_quantile_mask)),
        ("threshold_dark", threshold_masks(image, config, light_foreground=False)),
        ("adaptive_dark", adaptive_threshold_masks(image, config, light_foreground=False)),
        ("edge_aware", edge_aware_masks(image, config)),
        ("canny", canny_masks(image, config)),
        ("detail_canny", detail_canny_masks(image, config)),
    ]:
        # Restrict detail masks to the ML subject region so background
        # intensity levels don't produce spurious contours.
        if primary_ml_mask is not None:
            masks = tuple(m & primary_ml_mask for m in masks)

        cand = _build_candidate_from_masks(
            label=label,
            strategy=_DETAIL_STRATEGY_MAP[label],
            masks=masks,
            used_alpha=False,
            image=image,
            config=config,
            allow_jump_pruning=True,
        )
        detail_candidates.append(cand)
        candidates.append(cand)

    # ---- Direct contours (no mask cleanup) ----
    def _filter_to_subject(raw_contours: list) -> list:
        if primary_ml_mask is None:
            return raw_contours
        filtered: list = []
        for rc in raw_contours:
            rows = np.clip(rc[:, 0].astype(int), 0, primary_ml_mask.shape[0] - 1)
            cols = np.clip(rc[:, 1].astype(int), 0, primary_ml_mask.shape[1] - 1)
            if np.mean(primary_ml_mask[rows, cols]) > 0.5:
                filtered.append(rc)
        return filtered

    for label, use_detail in [("iso", False), ("iso_detail", True)]:
        raw_contours = _filter_to_subject(direct_iso_contours(
            image, config, use_detail=use_detail, subject_mask=ml_quantile_mask,
        ))
        cand = _build_candidate(
            label=label,
            strategy=ContourStrategy.MULTI_THRESHOLD.value,
            raw_contours=raw_contours,
            used_alpha=False,
            image=image,
            config=config,
            allow_jump_pruning=True,
        )
        detail_candidates.append(cand)
        candidates.append(cand)

    # Edge-density contours: trace actual edge features (eyes, nose, mouth).
    edge_raw = _filter_to_subject(edge_density_contours(
        image, config, subject_mask=ml_quantile_mask,
    ))
    # Build edge candidate without max_contours cap so small features
    # (eyes, nose) survive for grafting instead of being cut by the
    # largest-first sort in _postprocess_raw_contours.
    from dataclasses import replace as _replace
    edge_config = _replace(config, max_contours=None)
    edge_cand = _build_candidate(
        label="edge_density",
        strategy=ContourStrategy.EDGE_AWARE.value,
        raw_contours=edge_raw,
        used_alpha=False,
        image=image,
        config=edge_config,
        allow_jump_pruning=True,
    )
    # Uncapped version for grafting only.
    detail_candidates.append(edge_cand)
    # Capped version competes in scoring so edge-rich images
    # (sponge-scared, etc.) can select it as the winner.
    edge_cand_scored = _build_candidate(
        label="edge_density_scored",
        strategy=ContourStrategy.EDGE_AWARE.value,
        raw_contours=edge_raw,
        used_alpha=False,
        image=image,
        config=config,
        allow_jump_pruning=True,
    )
    detail_candidates.append(edge_cand_scored)
    candidates.append(edge_cand_scored)

    # Combined: quantile structure + edge features in one candidate.
    for q_label in ("quantile", "quantile_detail"):
        q_cand = next((c for c in detail_candidates if c.label == q_label), None)
        if q_cand is None or not q_cand.contours or not edge_cand.contours:
            continue
        # Merge: take quantile contours (overall shape) + edge contours (features).
        combined_raw = list(q_cand.contours) + list(edge_cand.contours)
        combined_areas = list(q_cand.areas) + list(edge_cand.areas)
        combo = _build_candidate_from_processed(
            label=f"{q_label}_edges",
            strategy=ContourStrategy.MULTI_THRESHOLD.value,
            contours=combined_raw,
            areas=combined_areas,
            used_alpha=False,
            image=image,
            config=config,
            nested_hybrid=True,
        )
        candidates.append(combo)

    # ---- ML envelope hybrids ----
    # Use the ML silhouette as the outer contour, stuff interior detail inside.
    if ml_cand.contours:
        ml_envelope = ml_cand.contours[0]
        ml_area = float(ml_cand.areas[0])

        for detail_cand in sorted(detail_candidates, key=lambda c: c.diagnostics.score, reverse=True):
            if not detail_cand.contours:
                continue
            hybrid = _hybridize_envelope_candidate(
                label=f"ml_{detail_cand.label}",
                strategy=ContourStrategy.ML.value,
                envelope_contour=ml_envelope,
                envelope_area=ml_area,
                detail_candidate=detail_cand,
                image=image,
                config=config,
                nested_hybrid=True,
            )
            if hybrid is not None:
                candidates.append(hybrid)

    # ---- Build primary candidate: ML silhouette + edge features ----
    # Edge density contours trace actual features (eyes, nose, mouth).
    # Use ML silhouette as the outer boundary, edge contours as interior.
    if ml_cand.contours and edge_cand.contours:
        from fourier_analysis.contours.geometry import _contours_are_near_duplicates

        ml_envelope = ml_cand.contours[0]
        ml_area_val = float(ml_cand.areas[0])
        edge_interior: list[np.ndarray] = []
        edge_interior_areas: list[float] = []
        max_interior = (config.max_contours or 8) - 1

        for ec, ea in zip(edge_cand.contours, edge_cand.areas):
            if len(edge_interior) >= max_interior:
                break
            if _contours_are_near_duplicates(ec, float(ea), ml_envelope, ml_area_val, image):
                continue
            edge_interior.append(ec)
            edge_interior_areas.append(float(ea))

        if edge_interior:
            primary = _build_candidate_from_processed(
                label="ml_edges",
                strategy=ContourStrategy.ML.value,
                contours=[ml_envelope] + edge_interior,
                areas=[ml_area_val] + edge_interior_areas,
                used_alpha=False,
                image=image,
                config=config,
                nested_hybrid=True,
            )
            candidates.append(primary)

    diagnostics = tuple(c.diagnostics for c in candidates)

    # All viable candidates compete.
    viable = [c for c in candidates if c.contours]
    if not viable:
        return None, diagnostics, tuple(notes)

    selected = max(viable, key=lambda c: c.diagnostics.score)

    # ---- Graft edge features onto the winner ----
    # The scored winner provides overall structure (silhouette, intensity
    # regions).  Edge density contours trace actual features (eyes, nose,
    # mouth) that threshold-based contours miss.  Replace some of the
    # winner's smaller contours with edge features.
    if edge_cand.contours and len(edge_cand.contours) >= 3 and "edge_density" not in selected.label:
        from fourier_analysis.contours.geometry import _contours_are_near_duplicates

        # Keep ALL winner contours for structure, add edge features
        # into remaining slots.
        max_total = (config.max_contours or 16) + 16  # budget for edge features
        grafted_contours = list(selected.contours)
        grafted_areas = list(selected.areas)

        # Filter edge contours to "feature scale": too small is noise,
        # too large repeats the silhouette already in the structure contours.
        min_feature_area = image.image_area * 0.0003
        max_feature_area = image.image_area * 0.06
        feature_edges = [
            (ec, ea) for ec, ea in zip(edge_cand.contours, edge_cand.areas)
            if min_feature_area <= ea <= max_feature_area
        ]
        # Sort by compactness (circularity = 4πA/P²) descending.
        # Circular features (eyes, nostrils) score high; elongated noise
        # fragments score low.  This prioritizes real features over noise.
        def _compactness_key(pair):
            contour, area = pair
            perimeter = float(np.sum(np.abs(np.diff(contour))))
            if perimeter < 1e-6:
                return 0.0
            return 4.0 * np.pi * area / (perimeter ** 2)

        feature_edges.sort(key=_compactness_key, reverse=True)

        # Track centroids of picked edge features for spatial diversity.
        picked_centers: list[complex] = []
        min_spacing = image.diagonal * 0.06  # ~45px at 768

        for ec, ea in feature_edges:
            if len(grafted_contours) >= max_total:
                break
            is_dup = any(
                _contours_are_near_duplicates(ec, float(ea), sc, float(sa), image)
                for sc, sa in zip(grafted_contours, grafted_areas)
            )
            if is_dup:
                continue
            # Spatial diversity: skip if too close to an already-picked edge.
            center = complex(float(ec.real.mean()), float(ec.imag.mean()))
            if any(abs(center - pc) < min_spacing for pc in picked_centers):
                continue
            grafted_contours.append(ec)
            grafted_areas.append(float(ea))
            picked_centers.append(center)

        if len(grafted_contours) != len(selected.contours):
            selected = _build_candidate_from_processed(
                label=selected.label,
                strategy=selected.strategy,
                contours=grafted_contours,
                areas=grafted_areas,
                used_alpha=selected.used_alpha,
                image=image,
                config=config,
                nested_hybrid=True,
            )

    # ---- Prune spatial outliers ----
    # Remove contours whose centroid is far outside the main body
    # of contours.  Uses the union bbox of the top-3 largest contours
    # expanded by 25%.
    if len(selected.contours) > 3:
        # Compute union bbox of the 3 largest contours (the structure).
        n_ref = min(3, len(selected.contours))
        re_min = min(float(c.real.min()) for c in selected.contours[:n_ref])
        re_max = max(float(c.real.max()) for c in selected.contours[:n_ref])
        im_min = min(float(c.imag.min()) for c in selected.contours[:n_ref])
        im_max = max(float(c.imag.max()) for c in selected.contours[:n_ref])
        margin_re = (re_max - re_min) * 0.25
        margin_im = (im_max - im_min) * 0.25
        bbox = (re_min - margin_re, im_min - margin_im,
                re_max + margin_re, im_max + margin_im)

        pruned_contours = list(selected.contours[:n_ref])
        pruned_areas = list(selected.areas[:n_ref])
        for c, a in zip(selected.contours[n_ref:], selected.areas[n_ref:]):
            cx, cy = float(c.real.mean()), float(c.imag.mean())
            if bbox[0] <= cx <= bbox[2] and bbox[1] <= cy <= bbox[3]:
                pruned_contours.append(c)
                pruned_areas.append(a)

        if len(pruned_contours) < len(selected.contours):
            selected = _build_candidate_from_processed(
                label=selected.label,
                strategy=selected.strategy,
                contours=pruned_contours,
                areas=pruned_areas,
                used_alpha=selected.used_alpha,
                image=image,
                config=config,
                nested_hybrid=True,
            )

    if selected.diagnostics.pruned_large_jump:
        notes.append("large inter-contour jumps were pruned")
    return selected, diagnostics, tuple(notes)


def _select_explicit_candidate(
    image: LoadedImage,
    config: ContourConfig,
) -> tuple[_ContourCandidate | None, tuple[ContourCandidateDiagnostics, ...], tuple[str, ...]]:
    if config.alpha_mode == AlphaMode.ONLY:
        if image.alpha is None:
            return None, (), ("alpha_mode=only requested, but the image has no usable alpha mask",)
        candidate = _build_candidate_from_masks(
            label="alpha",
            strategy="alpha",
            masks=alpha_masks(image),
            used_alpha=True,
            image=image,
            config=config,
            allow_jump_pruning=False,
        )
        return candidate if candidate.contours else None, (candidate.diagnostics,), ()

    if config.strategy == ContourStrategy.THRESHOLD:
        candidate = _build_candidate_from_masks(
            label="threshold",
            strategy=ContourStrategy.THRESHOLD.value,
            masks=threshold_masks(image, config, light_foreground=False),
            used_alpha=False,
            image=image,
            config=config,
            allow_jump_pruning=False,
        )
    elif config.strategy == ContourStrategy.ADAPTIVE_THRESHOLD:
        dark_candidate = _build_candidate_from_masks(
            label="adaptive_dark",
            strategy=ContourStrategy.ADAPTIVE_THRESHOLD.value,
            masks=adaptive_threshold_masks(image, config, light_foreground=False),
            used_alpha=False,
            image=image,
            config=config,
            allow_jump_pruning=False,
        )
        light_candidate = _build_candidate_from_masks(
            label="adaptive_light",
            strategy=ContourStrategy.ADAPTIVE_THRESHOLD.value,
            masks=adaptive_threshold_masks(image, config, light_foreground=True),
            used_alpha=False,
            image=image,
            config=config,
            allow_jump_pruning=False,
        )
        candidate = max(
            [dark_candidate, light_candidate],
            key=lambda item: item.diagnostics.score,
        )
    elif config.strategy == ContourStrategy.MULTI_THRESHOLD:
        candidate = _build_candidate_from_masks(
            label="multi_threshold",
            strategy=ContourStrategy.MULTI_THRESHOLD.value,
            masks=multi_threshold_masks(image, config),
            used_alpha=False,
            image=image,
            config=config,
            allow_jump_pruning=False,
        )
    elif config.strategy == ContourStrategy.EDGE_AWARE:
        candidate = _build_candidate_from_masks(
            label="edge_aware",
            strategy=ContourStrategy.EDGE_AWARE.value,
            masks=edge_aware_masks(image, config),
            used_alpha=False,
            image=image,
            config=config,
            allow_jump_pruning=False,
        )
    elif config.strategy == ContourStrategy.ML:
        candidate = _build_candidate_from_masks(
            label="ml",
            strategy=ContourStrategy.ML.value,
            masks=ml_masks(image, config),
            used_alpha=False,
            image=image,
            config=config,
            allow_jump_pruning=False,
        )
    else:
        candidate = _build_candidate_from_masks(
            label="canny",
            strategy=ContourStrategy.CANNY.value,
            masks=canny_masks(image, config),
            used_alpha=False,
            image=image,
            config=config,
            allow_jump_pruning=False,
        )

    return candidate if candidate.contours else None, (candidate.diagnostics,), ()
