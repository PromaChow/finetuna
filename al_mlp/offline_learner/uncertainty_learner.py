import numpy as np
import torch
from al_mlp.utils import (
    compute_with_calc,
    write_to_db,
)

from al_mlp.calcs import DeltaCalc
import random
import ase


# from al_mlp.utils import write_to_db
from al_mlp.offline_learner.offline_learner import OfflineActiveLearner

# from torch.multiprocessing import Pool

torch.multiprocessing.set_sharing_strategy("file_system")


class UncertaintyLearner(OfflineActiveLearner):
    """Offline Active Learner using an uncertainty enabled ML potential to query
    data with the most uncertainty.
    Parameters
    ----------
    learner_settings: dict
        Dictionary of learner parameters and settings.

    trainer: object
        An isntance of a trainer that has a train and predict method.

    training_data: list
        A list of ase.Atoms objects that have attached calculators.
        Used as the first set of training data.

    parent_calc: ase Calculator object
        Calculator used for querying training data.

    base_calc: ase Calculator object
        Calculator used to calculate delta data for training.

    ensemble: int
        The number of models in ensemble
    """

    def __init__(
        self,
        learner_params,
        ml_potential,
        training_data,
        parent_calc,
        base_calc,
    ):
        super().__init__(
            learner_params, ml_potential, training_data, parent_calc, base_calc
        )

        self.ml_potential = ml_potential
        self.ensemble = learner_params.get("n_ensembles")
        self.parent_calls = 0

    def do_before_train(self):
        if self.iterations > 0:
            queried_images = self.query_func()
            self.new_dataset = compute_with_calc(queried_images, self.delta_sub_calc)
            queries_db = ase.db.connect("queried_images.db")
            for image in self.new_dataset:
                parent_E = image.info["parent energy"]
                base_E = image.info["base energy"]
                write_to_db(queries_db, [image], "queried", parent_E, base_E)
            self.training_data += self.new_dataset
            self.parent_calls += len(self.new_dataset)
        self.fn_label = f"{self.file_dir}{self.filename}_iter_{self.iterations}"

    def do_train(self):
        if self.iterations > 0:
            self.ml_potential.train(self.training_data, self.new_dataset)
        else:
            self.ml_potential.train(self.training_data)
        self.trained_calc = DeltaCalc(
            [self.ml_potential, self.base_calc], "add", self.refs
        )

    def do_after_train(self):
        self.atomistic_method.run(calc=self.trained_calc, filename=self.fn_label)
        self.sample_candidates = list(
            self.atomistic_method.get_trajectory(filename=self.fn_label)
        )
        self.terminate = self.check_terminate()
        self.iterations += 1

    def query_func(self):
        if self.iterations > 1:
            uncertainty = np.array(
                [atoms.info["max_force_stds"] for atoms in self.sample_candidates]
            )
            n_retrain = self.samples_to_retrain
            query_idx = np.argpartition(uncertainty, -1 * n_retrain)[-n_retrain:]
            queried_images = [self.sample_candidates[idx] for idx in query_idx]
        else:
            query_idx = random.sample(
                range(1, len(self.sample_candidates)),
                self.samples_to_retrain,
            )
            queried_images = [self.sample_candidates[idx] for idx in query_idx]

        return queried_images
