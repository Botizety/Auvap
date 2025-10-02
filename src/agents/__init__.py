"""Agents module - Hierarchical Manager and Worker agents"""

from .manager import ManagerAgent
from .worker import WorkerAgent  
# from .hierarchical_env import HierarchicalAUVAPEnv  # TODO: Implement full hierarchical environment

__all__ = ["ManagerAgent", "WorkerAgent"]  # , "HierarchicalAUVAPEnv"]
