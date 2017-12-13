from gym.envs.registration import register

register(
    id='Duckiebot-Env',
    entry_point='gym_duckietown.envs:DuckiebotEnv',
    # This next value would seem useless in the case that we are running on the real robot
    reward_threshold=1000.0,
)

