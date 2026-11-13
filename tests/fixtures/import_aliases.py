import numpy as np
import sklearn.model_selection as msm
from sklearn.model_selection import train_test_split as tts

np.random.seed(0)
msm.train_test_split([[1], [2]], [0, 1])
tts([[1], [2]], [0, 1])
