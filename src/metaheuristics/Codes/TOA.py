"""Teamwork Optimization Algorithm (TOA), Dehghani & Trojovsky (2021).

This is the continuous, minimization-oriented baseline. Each of the three
stages evaluates a candidate and accepts it only if it improves the current
individual. Objective evaluations are performed through ``fo`` so that the
domain manager can count function evaluations (NFE).

Reference: https://doi.org/10.3390/s21134567 (Equations 3-11).
"""

import numpy as np


def iterarTOA(population, fitness, fo):
    """Perform one TOA generation and return ``(population, fitness)``.

    ``fo(x)`` must return ``(repaired_x, objective_value)``. The function
    expects a continuous search domain and a *minimization* objective.

    When an individual has no strictly better teammates, stage 2 is skipped:
    its mean of better teammates is undefined in Equation (7).
    """
    population = np.asarray(population, dtype=float).copy()
    fitness = np.asarray(fitness, dtype=float).copy()

    if population.ndim != 2 or fitness.shape != (population.shape[0],):
        raise ValueError("TOA requires a (N, D) population and (N,) fitness.")
    if population.shape[0] == 0 or population.shape[1] == 0:
        raise ValueError("TOA requires a non-empty population and dimension.")
    if not np.all(np.isfinite(fitness)):
        raise ValueError("TOA requires finite initial fitness values.")

    supervisor = population[np.argmin(fitness)].copy()

    def accept_if_better(i, candidate):
        repaired, score = fo(np.asarray(candidate, dtype=float))
        score = float(score)
        if score < fitness[i]:
            population[i] = np.asarray(repaired, dtype=float)
            fitness[i] = score

    for i in range(len(population)):
        # Stage 1: supervisor guidance, Equations (4)-(6).
        r = np.random.random()
        update_index = int(np.floor(1 + r + 0.5))
        candidate = population[i] + r * (supervisor - update_index * population[i])
        accept_if_better(i, candidate)

        # Stage 2: learn from strictly better teammates, Equations (7)-(9).
        better = fitness < fitness[i]
        if np.any(better):
            mean_better = np.mean(population[better], axis=0)
            _, mean_score = fo(mean_better)
            direction = np.sign(fitness[i] - float(mean_score))
            r = np.random.random()
            update_index = int(np.floor(1 + r + 0.5))
            candidate = population[i] + (
                r * (mean_better - update_index * population[i]) * direction
            )
            accept_if_better(i, candidate)

        # Stage 3: small individual activity, Equations (10)-(11).
        r = np.random.random()
        candidate = population[i] + (-0.01 + 0.02 * r) * population[i]
        accept_if_better(i, candidate)

    return population, fitness
