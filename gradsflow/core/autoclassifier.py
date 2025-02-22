#  Copyright (c) 2021 GradsFlow. All rights reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from abc import abstractmethod
from typing import Dict, List, Optional, Union

import torch
from flash.core.data.data_module import DataModule
from ray import tune

from gradsflow.core.automodel import AutoModel

# noinspection PyTypeChecker
from gradsflow.utility.common import listify


class AutoClassifier(AutoModel):
    """Implements `AutoModel` for classification tasks."""

    DEFAULT_BACKBONES = []

    def __init__(
        self,
        datamodule: DataModule,
        max_epochs: int = 10,
        max_steps: int = 10,
        n_trials: int = 100,
        optimization_metric: Optional[str] = None,
        suggested_backbones: Union[List, str, None] = None,
        suggested_conf: Optional[dict] = None,
        tune_confs: Optional[Dict] = None,
        timeout: int = 600,
        prune: bool = True,
    ):
        super().__init__(
            datamodule,
            max_epochs=max_epochs,
            max_steps=max_steps,
            optimization_metric=optimization_metric,
            n_trials=n_trials,
            suggested_conf=suggested_conf,
            timeout=timeout,
            prune=prune,
            tune_confs=tune_confs,
        )

        if isinstance(suggested_backbones, (str, list, tuple)):
            self.suggested_backbones = listify(suggested_backbones)
        elif suggested_backbones is None:
            self.suggested_backbones = self.DEFAULT_BACKBONES
        else:
            raise UserWarning("Invalid suggested_backbone type!")

        self.datamodule = datamodule
        self.num_classes = datamodule.num_classes

    def forward(self, x):
        if not self.model:
            raise UserWarning("model not initialized yet, run `hp_tune()` first.")
        return self.model(x)

    # noinspection PyTypeChecker
    def _create_search_space(self) -> Dict[str, str]:
        """Create hyperparameter config from `ray.tune`

        Returns:
             key-value pair of `ray.tune` hparams
        """
        trial_backbone = tune.choice(self.suggested_backbones)
        trial_lr = tune.loguniform(*self.suggested_lr)
        trial_optimizer = tune.choice(self.suggested_optimizers)
        hparams = {
            "backbone": trial_backbone,
            "lr": trial_lr,
            "optimizer": trial_optimizer,
        }
        return hparams

    @abstractmethod
    def build_model(self, config: dict) -> torch.nn.Module:
        """Every Task implementing AutoClassifier has to implement a
        build model method that can build `torch.nn.Module` from dictionary config
        and return the model.
        """
        raise NotImplementedError
