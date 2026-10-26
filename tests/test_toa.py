"""Focused, dependency-light regression tests for the continuous TOA baseline."""

import os
import sys
import unittest

import numpy as np


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from metaheuristics.Codes.TOA import iterarTOA
from solver.metaheuristic_adapter import MetaheuristicAdapter


class TestTOA(unittest.TestCase):
    @staticmethod
    def sphere(x):
        x = np.clip(x, -10.0, 10.0)
        return x, float(np.dot(x, x))

    def test_greedy_steps_and_fitness_consistency(self):
        rng = np.random.default_rng(42)
        population = rng.uniform(-10, 10, size=(12, 5))
        fitness = np.sum(population**2, axis=1)
        original_population = population.copy()
        original_fitness = fitness.copy()
        evaluations = 0

        def objective(x):
            nonlocal evaluations
            evaluations += 1
            return self.sphere(x)

        np.random.seed(123)
        updated, scores = iterarTOA(population, fitness, objective)

        self.assertEqual(updated.shape, population.shape)
        self.assertTrue(np.all(scores <= original_fitness))
        self.assertTrue(np.all(updated >= -10.0))
        self.assertTrue(np.all(updated <= 10.0))
        np.testing.assert_allclose(scores, np.sum(updated**2, axis=1))
        np.testing.assert_array_equal(population, original_population)
        np.testing.assert_array_equal(fitness, original_fitness)
        self.assertGreaterEqual(evaluations, 2 * len(population))
        self.assertLessEqual(evaluations, 4 * len(population))

    def test_constant_fitness_never_replaces_an_individual(self):
        population = np.array([[1.0, 2.0], [3.0, -1.0], [-2.0, 4.0]])
        fitness = np.ones(3)
        evaluations = 0

        def constant(x):
            nonlocal evaluations
            evaluations += 1
            return x.copy(), 1.0

        updated, scores = iterarTOA(population, fitness, constant)
        np.testing.assert_array_equal(updated, population)
        np.testing.assert_array_equal(scores, fitness)
        # No strictly better colleagues: only stages 1 and 3 evaluate.
        self.assertEqual(evaluations, 2 * len(population))

    def test_reproducible_with_fixed_numpy_seed(self):
        population = np.array([[5., 3.], [-4., 3.], [1., 2.], [-2., -5.]])
        fitness = np.sum(population**2, axis=1)
        np.random.seed(77)
        first = iterarTOA(population, fitness, self.sphere)
        np.random.seed(77)
        second = iterarTOA(population, fitness, self.sphere)
        for left, right in zip(first, second):
            np.testing.assert_array_equal(left, right)

    def test_sphere_improves_over_multiple_generations(self):
        np.random.seed(2026)
        population = np.random.uniform(-10, 10, size=(12, 2))
        fitness = np.sum(population**2, axis=1)
        initial_best = float(np.min(fitness))
        best_history = [initial_best]

        for _ in range(50):
            population, fitness = iterarTOA(population, fitness, self.sphere)
            best_history.append(float(np.min(fitness)))

        self.assertTrue(np.all(np.diff(best_history) <= 0.0))
        self.assertLess(best_history[-1], initial_best)
        np.testing.assert_allclose(fitness, np.sum(population**2, axis=1))

    def test_adapter_preserves_internally_evaluated_fitness(self):
        population = np.array([[5., 3.], [-4., 3.], [1., 2.], [-2., -5.]])
        fitness = np.sum(population**2, axis=1)
        adapter = MetaheuristicAdapter('TOA', 4, 2, [-10, -10], [10, 10])
        np.random.seed(55)
        updated, scores, state = adapter.run_iteration(
            population, fitness, adapter.initialize_state(population),
            iter_num=1, max_iter=10, best=population[2], fo=self.sphere,
        )
        self.assertEqual(updated.shape, population.shape)
        np.testing.assert_allclose(scores, np.sum(updated**2, axis=1))
        self.assertIsNone(state['vel'])

    def test_rejects_inconsistent_shapes(self):
        with self.assertRaises(ValueError):
            iterarTOA(np.ones((3, 2)), np.ones(2), self.sphere)


if __name__ == '__main__':
    unittest.main()
