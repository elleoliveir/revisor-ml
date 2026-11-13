from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

X = [[1], [2]]
y = [0, 1]
X_train, X_test, y_train, y_test = train_test_split(X, y)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
