"""Equation-level examples and BEN/solver regression checks for TOA."""

import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from metaheuristics.Codes.TOA import iterarTOA
from solver.domain_managers.ben_domain import BenDomainManager
from solver.termination_manager import TerminationCriteria
from solver.universal_solver import universal_solver


class TestTOAIntegration(unittest.TestCase):
    def test_hand_calculated_stages_and_fixed_supervisor(self):
        proposals = []

        def sphere(x):
            proposals.append(x.copy())
            return x.copy(), float(np.sum(x**2))

        # The first member improves before member 2 uses the original supervisor.
        with patch('numpy.random.random', side_effect=[.75, .25, .25, .75, .75]):
            population, fitness = iterarTOA(np.array([[1.], [4.]]), [1., 16.], sphere)

        expected = [.25, .24875, 3.25, .24875, -1.4384375, -1.4456296875]
        np.testing.assert_allclose(np.asarray(proposals).ravel(), expected)
        np.testing.assert_allclose(population.ravel(), [.24875, -1.4384375])
        np.testing.assert_allclose(fitness, population.ravel()**2)

    def test_mean_objective_controls_direction_on_nonconvex_function(self):
        proposals = []

        def double_well(x):
            proposals.append(float(x[0]))
            return x.copy(), float((x[0]**2 - 4)**2)

        # Two strictly better peers at -2 and 2 have mean 0, whose score 16
        # is worse than the current member's score 9. Equation 8 must repel.
        with patch('numpy.random.random', side_effect=[0., .5, 0., .5, 0., .25, .5]):
            population, fitness = iterarTOA(
                np.array([[-2.], [2.], [1.]]), [0., 0., 9.], double_well)
        self.assertEqual(proposals[5], 0.)
        self.assertEqual(proposals[6], 1.25)
        self.assertEqual(population[2, 0], 1.25)
        self.assertEqual(fitness[2], (1.25**2 - 4)**2)

    def test_universal_solver_counts_actual_calls_without_reevaluation(self):
        # No production DB is opened: only persistence and the optimum lookup
        # are mocked. The real adapter, BEN function, metrics and solver run.
        with patch('solver.domain_managers.ben_domain.BD') as lookup:
            lookup.return_value.obtenerOptimoInstancia.return_value = [(0.,)]
            domain = BenDomainManager('F1', dim=3, pop_size=4, lb=-10, ub=10)

        calls = []
        import solver.domain_managers.ben_domain as ben_module
        real_fitness = ben_module.benchmark_fitness

        def counted(name, x):
            calls.append(np.asarray(x).copy())
            return real_fitness(name, x)

        persistence = Mock()
        termination = TerminationCriteria(max_iter=4)
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmp)
                with patch('solver.universal_solver.BD', return_value=persistence), \
                     patch.object(ben_module, 'benchmark_fitness', side_effect=counted), \
                     contextlib.redirect_stdout(io.StringIO()):
                    universal_solver(17, 'TOA', domain, termination)
            finally:
                os.chdir(old_cwd)

        csv = persistence.insertarIteraciones.call_args.args[1]
        data = pd.read_csv(io.BytesIO(csv))
        self.assertEqual(len(data), 5)
        self.assertEqual(int(data.nfe.iloc[0]), 4)
        self.assertEqual(int(data.nfe.iloc[-1]), len(calls))
        self.assertEqual(termination.current_fe, len(calls))
        self.assertTrue((data.best_fitness.diff().dropna() <= 0).all())
        self.assertTrue(np.all(np.abs(calls) <= 10))
        score, _, best, _ = persistence.insertarResultados.call_args.args
        self.assertAlmostEqual(score, float(np.sum(best**2)))
        self.assertEqual(score, data.best_fitness.iloc[-1])

        # Processing an already evaluated TOA population must make zero calls.
        before = domain.nfe
        pop = np.array([[1., 2., 3.]])
        fit = np.array([14.])
        actual_pop, actual_fit = domain.process_new_population(pop, fit, 'TOA', {})
        self.assertIs(actual_pop, pop)
        self.assertIs(actual_fit, fit)
        self.assertEqual(domain.nfe, before)


if __name__ == '__main__':
    unittest.main()
