import os
import numpy
import gym
import random

from gym.spaces.box import Box

from baselines import bench
from baselines.common.atari_wrappers import make_atari, wrap_deepmind

try:
    import pybullet_envs
except ImportError:
    pass

try:
    import gym_aigame
except ImportError:
    pass

try:
    import gym_duckietown
    from gym_duckietown.envs import *
except ImportError:
    pass

def make_env(env_id, seed, rank, log_dir, start_container):
    def _thunk():
        if env_id.startswith('Duckietown'):
            basePort = DuckietownEnv.SERVER_PORT
            if start_container:
                basePort += random.randint(0, 20000)
            env = DuckietownEnv(
                serverPort= basePort + rank,
                startContainer=start_container
            )
            if "Discrete" in env_id:
                env = DiscreteWrapper(env)
        elif "SimpleSim" in env_id:
            env = SimpleSimEnv()
            if "Discrete" in env_id:
                env = DiscreteWrapper(env)
            elif "Heading" in env_id:
                env = HeadingWrapper(env)
        else:
            env = gym.make(env_id)
            env = DiscreteWrapper(env)

        is_atari = hasattr(gym.envs, 'atari') and isinstance(env.unwrapped, gym.envs.atari.atari_env.AtariEnv)
        if is_atari:
            env = make_atari(env_id)
        env.seed(seed + rank)
        if log_dir is not None:
            env = bench.Monitor(env, os.path.join(log_dir, str(rank)))
        if is_atari:
            env = wrap_deepmind(env)

        # If the input has shape (W,H,3), wrap for PyTorch convolutions
        obs_shape = env.observation_space.shape
        if len(obs_shape) == 3 and obs_shape[2] == 3:
            env = WrapPyTorch(env)

        env = ScaleObservations(env)

        return env

    return _thunk

class ScaleObservations(gym.ObservationWrapper):
    def __init__(self, env=None):
        super(ScaleObservations, self).__init__(env)
        self.obs_lo = self.observation_space.low[0,0,0]
        self.obs_hi = self.observation_space.high[0,0,0]
        obs_shape = self.observation_space.shape
        self.observation_space = Box(0.0, 1.0, obs_shape)

    def _observation(self, obs):
        if self.obs_lo == 0.0 and self.obs_hi == 1.0:
            return obs
        else:
            return (obs - self.obs_lo) / (self.obs_hi - self.obs_lo)

class WrapPyTorch(gym.ObservationWrapper):
    def __init__(self, env=None):
        super(WrapPyTorch, self).__init__(env)
        obs_shape = self.observation_space.shape
        self.observation_space = Box(
            self.observation_space.low[0,0,0],
            self.observation_space.high[0,0,0],
            [obs_shape[2], obs_shape[1], obs_shape[0]]
        )

    def _observation(self, observation):
        return observation.transpose(2, 0, 1)
