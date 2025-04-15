import time
import logging
logger = logging.getLogger(__name__)

import numpy as np
import torch
from qtpy import QtCore

import kilosort
from kilosort.run_kilosort import (
    # setup_logger, initialize_ops, compute_preprocessing, compute_drift_correction,
    # detect_spikes, cluster_spikes, save_sorting, close_logger
    setup_logger, _sort
    )
from kilosort.io import save_preprocessing
from kilosort.utils import (
    log_performance, log_cuda_details, ops_as_string, probe_as_string
    )


class KiloSortWorker(QtCore.QThread):
    finishedPreprocess = QtCore.Signal(object)
    finishedSpikesort = QtCore.Signal(object)
    finishedAll = QtCore.Signal(object)
    progress_bar = QtCore.Signal(int)
    plotDataReady = QtCore.Signal(str)

    def __init__(self, context, results_directory, steps,
                 device=torch.device('cuda'), file_object=None, *args, **kwargs):
        super(KiloSortWorker, self).__init__(*args, **kwargs)
        self.context = context
        self.data_path = context.data_path
        self.results_directory = results_directory
        assert isinstance(steps, list) or isinstance(steps, str)
        self.steps = steps if isinstance(steps, list) else [steps]
        self.device = device
        self.file_object = file_object

    def run(self):
        if "spikesort" in self.steps:
            settings = self.context.params
            probe = self.context.probe
            settings["data_dir"] = self.data_path.parent
            settings["filename"] = self.data_path
            results_dir = self.results_directory
            if not results_dir.exists():
                results_dir.mkdir(parents=True)
            
            setup_logger(results_dir)

            # NOTE: All but `gui_sorter` are positional args,
            #       don't move these around.
            _ = _sort(
                settings['filename'], results_dir, probe, settings,
                settings['data_dtype'], self.device, settings['do_CAR'],
                settings['clear_cache'], settings['invert_sign'],
                settings['save_preprocessed_copy'], settings['verbose_log'],
                False, self.file_object, self.progress_bar, gui_sorter=self
                )
            # Hard-coded `False` is for "save_extra_vars", which isn't an option
            # in the GUI right now (and isn't likely to be added).

            self.finishedSpikesort.emit(self.context)
