# utils/general.py - 简化版
import os
import logging
import torch

def set_logging(name=None, verbose=True):
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(format="%(message)s", level=logging.INFO if verbose else logging.WARNING)
    return logging.getLogger(name)

LOGGER = set_logging(__name__)

CUDA = True if torch.cuda.is_available() else False
DEVICE = 'cuda' if CUDA else 'cpu'

# 删除 Loggers 类和其他训练相关功能