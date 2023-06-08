import gym
import asyncio

from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3 import PPO
from torch.distributions import Categorical
import torch.optim as optim


from gymclient import GameEnvironment, CustomFeaturesExtractor, CustomPolicy


host = "2001:67c:20a1:232:753b:18:538d:6a34"
port = 4000
username = "dino"
password = "cheese"

# Instantiate the game environment

# Train the agent using the environment
# Use any reinforcement learning algorithm available in the Gym library
env = GameEnvironment(host, port, username, password)
env = DummyVecEnv([lambda: env])

# Define the custom policy and the PPO agent
policy_kwargs = dict(
    features_extractor_class=CustomFeaturesExtractor,
    features_extractor_kwargs=dict(features_dim=64),
)
model = PPO(CustomPolicy, env, policy_kwargs=policy_kwargs, verbose=1)

# Train the agent
model.learn(total_timesteps=10000)

# Evaluate the trained agent
mean_reward, _ = evaluate_policy(model, env, n_eval_episodes=10)

print(f"Mean reward: {mean_reward}")
