import numpy as np

class KMeans(object):
    def __init__(self, n_clusters, n_iter=100):
        self.n_clusters = n_clusters
        self.n_iter = n_iter

    def fit(self, X):
        n_samples, n_features = X.shape
        cluster_centers = np.random.random((self.n_clusters, n_features))
        
        for i in range(self.n_iter):
            # SCIDB: join/sum
            D = np.sum((X[:, None, :] - cluster_centers) ** 2, -1)

            # SCIDB: argmin
            cluster_labels = np.argmin(D, 1)

            # SCIDB: index join
            cluster_centers = np.array([X[cluster_labels == i].mean(0)
                                        for i in range(self.n_clusters)])

        self.cluster_centers_ = cluster_centers
        return self

    def predict(self, X):
        # SCIDB: join/sum
        D = np.sum((X[:, None, :] - self.cluster_centers_) ** 2, -1)

        # SCIDB: argmin
        return np.argmin(D, -1)


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    N = 500
    D = 2
    data = np.vstack([np.random.normal(center, 1, size=(N, D))
                      for center in [(3.5, 0), (-3, 3), (-3, -3)]])
    clf = KMeans(3).fit(data)
    labels = clf.predict(data)

    plt.scatter(data[:, 0], data[:, 1], c=labels)
    plt.show()
