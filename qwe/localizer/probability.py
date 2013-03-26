from numpy import exp, sqrt, pi

# gaussian normalized a unity area
def gaussian(mu, sigma, x):
  var = sigma**2
  # calculates the probability of x for 1-dim Gaussian with mean mu and var. sigma
  return exp(- ((mu - x) ** 2) / ( 2.0 * var)) / sqrt(2.0 * pi * var)

# gaussian normalized a unity peak
def ngaussian(mu, sigma, x):
  var = sigma**2
  # calculates the probability of x for 1-dim Gaussian with mean mu and var. sigma
  return exp(- ((mu - x) ** 2) / ( 2.0 * var))
