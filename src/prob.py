from scipy.stats import rv_discrete

# probability utility functions

def sample_pmf(vals, probs, size=1):
    rv = rv_discrete(values=(vals, probs))
    return rv.rvs(size=size)
