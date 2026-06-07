"""
Evolution Engine - genetic algorithm to find the best trading formulas.
Population-based search using selection, crossover, and mutation.
"""
import random
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Callable, Optional
from joblib import Parallel, delayed
from loguru import logger

from core.formula_engine import FormulaEngine, CONDITION_TYPES, PARAM_RANGES
from core.backtest_engine import BacktestEngine, BacktestResult


def _evaluate_one(formula: Dict, df_entry: pd.DataFrame,
                   df_htf: pd.DataFrame, fe: FormulaEngine,
                   be: BacktestEngine) -> float:
    """Evaluate fitness of a single formula - must be top-level for joblib."""
    try:
        result = be.run(df_entry, df_htf, formula, fe)
        return result.fitness_score()
    except Exception:
        return 0.0


class EvolutionEngine:
    def __init__(self, config: dict = None):
        cfg = config or {}
        self.population_size = cfg.get("population_size", 1000)
        self.max_generations  = cfg.get("max_generations", 200)
        self.target_winrate   = cfg.get("target_winrate", 0.75)
        self.elite_ratio      = cfg.get("elite_ratio", 0.05)
        self.crossover_ratio  = cfg.get("crossover_ratio", 0.60)
        self.mutation_rate    = cfg.get("mutation_rate", 0.15)
        self.n_jobs           = cfg.get("n_cpu_cores", -1)
        self.checkpoint_interval = cfg.get("checkpoint_interval", 10)
        self.min_trades       = cfg.get("min_trades", 100)

    def evolve(self, df_entry: pd.DataFrame, df_htf: pd.DataFrame,
               formula_engine: FormulaEngine, backtest_engine: BacktestEngine,
               callback: Callable = None,
               checkpoint_callback: Callable = None) -> Dict:
        """
        Main evolution loop.

        callback(gen, best_winrate, best_formula, pop_size) - called each generation for GUI updates
        checkpoint_callback(gen, best_formula, metrics) - called every checkpoint_interval generations

        Returns: {best_formula, best_fitness, best_metrics, history}
        """
        logger.info(f"Starting evolution: pop={self.population_size}, "
                    f"max_gen={self.max_generations}, target_wr={self.target_winrate}")

        population = formula_engine.generate_population(self.population_size)
        history = []
        best_formula = None
        best_fitness = 0.0
        best_metrics = None

        for gen in range(self.max_generations):
            # Evaluate all formulas in parallel
            fitness_scores = self._evaluate_population(
                population, df_entry, df_htf, formula_engine, backtest_engine
            )

            # Find best in this generation
            best_idx = int(np.argmax(fitness_scores))
            gen_best_fitness = fitness_scores[best_idx]
            gen_best_formula = population[best_idx]

            if gen_best_fitness > best_fitness:
                best_fitness = gen_best_fitness
                best_formula = gen_best_formula.copy()
                best_result = backtest_engine.run(df_entry, df_htf, best_formula, formula_engine)
                best_metrics = {
                    "winrate": best_result.winrate,
                    "profit_factor": best_result.profit_factor,
                    "total_trades": best_result.total_trades,
                    "max_drawdown": best_result.max_drawdown,
                    "fitness": best_fitness,
                }

            avg_fitness = float(np.mean(fitness_scores))
            gen_winrates = self._batch_winrates(
                population, fitness_scores, df_entry, df_htf, formula_engine, backtest_engine
            )
            best_wr = float(np.max(gen_winrates)) if len(gen_winrates) > 0 else 0.0

            history.append({
                "generation": gen,
                "best_fitness": gen_best_fitness,
                "avg_fitness": avg_fitness,
                "best_winrate": best_wr,
            })

            logger.info(f"Gen {gen+1:>4}/{self.max_generations} | "
                        f"best_fit={gen_best_fitness:.4f} | avg_fit={avg_fitness:.4f} | "
                        f"best_wr={best_wr:.1%}")

            if callback:
                try:
                    callback(gen + 1, best_wr, gen_best_formula, self.max_generations)
                except Exception:
                    pass

            if gen % self.checkpoint_interval == 0 and checkpoint_callback and best_formula:
                try:
                    checkpoint_callback(gen, best_formula, best_metrics)
                except Exception:
                    pass

            # Early stop if target achieved
            if best_metrics and best_metrics["winrate"] >= self.target_winrate and best_metrics["total_trades"] >= self.min_trades:
                logger.info(f"Target winrate {self.target_winrate:.1%} achieved at generation {gen+1}!")
                break

            # Generate next generation
            population = self._next_generation(population, fitness_scores, formula_engine)

        logger.info(f"Evolution complete. Best winrate: {best_metrics['winrate']:.1%} "
                    f"({best_metrics['total_trades']} trades)" if best_metrics else "No valid formula found")

        return {
            "best_formula": best_formula,
            "best_fitness": best_fitness,
            "best_metrics": best_metrics,
            "history": history,
        }

    def _evaluate_population(self, population: List[Dict], df_entry: pd.DataFrame,
                              df_htf: pd.DataFrame, fe: FormulaEngine,
                              be: BacktestEngine) -> np.ndarray:
        """Evaluate all formulas in parallel using joblib."""
        if self.n_jobs == 1:
            scores = [_evaluate_one(f, df_entry, df_htf, fe, be) for f in population]
        else:
            scores = Parallel(n_jobs=self.n_jobs, prefer="threads")(
                delayed(_evaluate_one)(f, df_entry, df_htf, fe, be)
                for f in population
            )
        return np.array(scores, dtype=float)

    def _batch_winrates(self, population: List[Dict], fitness_scores: np.ndarray,
                         df_entry: pd.DataFrame, df_htf: pd.DataFrame,
                         fe: FormulaEngine, be: BacktestEngine) -> np.ndarray:
        """Get winrates for top-10 formulas to track best_winrate."""
        top_indices = np.argsort(fitness_scores)[-10:]
        winrates = []
        for idx in top_indices:
            try:
                r = be.run(df_entry, df_htf, population[idx], fe)
                winrates.append(r.winrate)
            except Exception:
                winrates.append(0.0)
        return np.array(winrates)

    def _next_generation(self, population: List[Dict], fitness_scores: np.ndarray,
                          formula_engine: FormulaEngine) -> List[Dict]:
        """Create next generation via elitism + crossover + mutation."""
        n = len(population)
        n_elite = max(1, int(n * self.elite_ratio))
        n_crossover = int(n * self.crossover_ratio)
        n_random = n - n_elite - n_crossover

        # Sort by fitness
        sorted_indices = np.argsort(fitness_scores)[::-1]

        # Elitism: keep top n_elite
        elite = [population[i].copy() for i in sorted_indices[:n_elite]]

        # Crossover offspring
        crossover_pool = [population[i] for i in sorted_indices[:max(20, n_elite * 4)]]
        offspring = []
        while len(offspring) < n_crossover:
            p1 = random.choice(crossover_pool)
            p2 = random.choice(crossover_pool)
            child1, child2 = self._crossover(p1, p2)
            offspring.append(self._mutate(child1))
            if len(offspring) < n_crossover:
                offspring.append(self._mutate(child2))

        # Random immigrants for diversity
        immigrants = formula_engine.generate_population(n_random)

        return elite + offspring[:n_crossover] + immigrants

    def _crossover(self, parent1: Dict, parent2: Dict) -> Tuple[Dict, Dict]:
        """Uniform crossover: each gene randomly taken from either parent."""
        import uuid

        def blend_params(p1: dict, p2: dict) -> dict:
            result = {}
            for key in p1:
                result[key] = random.choice([p1[key], p2[key]])
            return result

        # Blend conditions: union with random sampling
        all_conds = list(set(parent1["conditions"] + parent2["conditions"]))
        n_conds = random.randint(1, min(4, len(all_conds)))
        child1_conds = random.sample(all_conds, min(n_conds, len(all_conds)))
        child2_conds = random.sample(all_conds, min(n_conds, len(all_conds)))

        child1 = {
            "id": str(uuid.uuid4())[:8],
            "direction": random.choice([parent1["direction"], parent2["direction"]]),
            "conditions": child1_conds,
            "params": blend_params(parent1["params"], parent2["params"]),
        }
        child2 = {
            "id": str(uuid.uuid4())[:8],
            "direction": random.choice([parent1["direction"], parent2["direction"]]),
            "conditions": child2_conds,
            "params": blend_params(parent1["params"], parent2["params"]),
        }

        self._fix_params(child1["params"])
        self._fix_params(child2["params"])
        return child1, child2

    def _mutate(self, formula: Dict) -> Dict:
        """Apply random mutations to formula parameters."""
        import uuid
        import copy
        f = copy.deepcopy(formula)
        f["id"] = str(uuid.uuid4())[:8]
        p = f["params"]

        for key, val in p.items():
            if random.random() < self.mutation_rate:
                lo, hi = PARAM_RANGES.get(key, (val * 0.5, val * 1.5))
                if isinstance(val, int):
                    delta = random.randint(-max(1, int((hi - lo) * 0.1)),
                                           max(1, int((hi - lo) * 0.1)))
                    p[key] = int(np.clip(val + delta, lo, hi))
                else:
                    delta = random.gauss(0, (hi - lo) * 0.05)
                    p[key] = float(np.clip(val + delta, lo, hi))

        # Randomly add or remove a condition
        if random.random() < self.mutation_rate:
            if len(f["conditions"]) > 1 and random.random() < 0.3:
                f["conditions"].pop(random.randrange(len(f["conditions"])))
            else:
                new_cond = random.choice(CONDITION_TYPES)
                if new_cond not in f["conditions"]:
                    f["conditions"].append(new_cond)

        # Randomly flip direction
        if random.random() < self.mutation_rate * 0.3:
            f["direction"] = "sell" if f["direction"] == "buy" else "buy"

        self._fix_params(f["params"])
        return f

    @staticmethod
    def _fix_params(p: dict):
        """Ensure parameter constraints are satisfied."""
        p["ema_fast"] = int(np.clip(p["ema_fast"], 5, 30))
        p["ema_slow"] = int(np.clip(p["ema_slow"], p["ema_fast"] + 5, 200))
        p["macd_fast"] = int(np.clip(p["macd_fast"], 8, 20))
        p["macd_slow"] = int(np.clip(p["macd_slow"], p["macd_fast"] + 4, 40))
        p["stoch_d"] = int(np.clip(p["stoch_d"], 2, p["stoch_k"]))
