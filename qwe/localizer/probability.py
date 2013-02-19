from numpy import exp, sqrt, pi

def gaussian(mu, sigma, x):
        
  # calculates the probability of x for 1-dim Gaussian with mean mu and var. sigma
  return exp(- ((mu - x) ** 2) / (sigma ** 2) / 2.0) / sqrt(2.0 * pi * (sigma ** 2))
