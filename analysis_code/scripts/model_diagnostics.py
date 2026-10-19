"""Rank and estimability diagnostics without changing WLS specifications."""
import hashlib
import numpy as np


def diagnose_fit(fit, frame, weight):
    x = np.asarray(fit.model.wexog, dtype=float)
    _, singular, vt = np.linalg.svd(x, full_matrices=False)
    tolerance = singular[0] * max(x.shape) * np.finfo(float).eps
    rank = int((singular > tolerance).sum())
    names = fit.model.exog_names
    projection = vt[:rank].T @ vt[:rank]
    errors = np.linalg.norm(np.eye(x.shape[1]) - projection, axis=0)
    nonestimable = [name for name, error in zip(names, errors) if error > 1e-8]
    fit.nonestimable_terms = set(nonestimable)
    identifier = next(c for c in ['mergeid', 'ID', 'pid'] if c in frame)
    used = frame.loc[fit.model.data.row_labels]
    sample_hash = hashlib.sha256('\n'.join(sorted(used[identifier].astype(str))).encode()).hexdigest()
    weights_hash = hashlib.sha256(np.asarray(used[weight], dtype='<f8').tobytes()).hexdigest()
    order = np.argsort(names)
    design_hash = hashlib.sha256(np.asarray(fit.model.exog[:, order], dtype='<f8').tobytes()).hexdigest()
    outcome_hash = hashlib.sha256(np.asarray(fit.model.endog, dtype='<f8').tobytes()).hexdigest()
    return dict(design_columns=x.shape[1], design_rank=rank, full_rank=rank == x.shape[1],
                singular_value_min=float(singular[-1]), singular_value_max=float(singular[0]),
                rank_tolerance=float(tolerance), nonestimable_terms=nonestimable,
                zero_columns=[names[j] for j in range(x.shape[1]) if not np.any(x[:, j])],
                sample_sha256=sample_hash, weights_sha256=weights_hash,
                design_sha256=design_hash, outcome_sha256=outcome_hash,
                design_column_names=names, n=int(fit.nobs))
