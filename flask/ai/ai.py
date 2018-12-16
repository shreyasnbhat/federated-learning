#!/usr/bin/python3
import tensorflow as tf
import numpy as np
from sklearn.model_selection import train_test_split
import sys
import matplotlib.pyplot as plt
from model import Model
import pickle
from keras.datasets import mnist

MAX_CLIENTS = 2

epochs = 1
batch_size = 64
placeX = [tf.placeholder(tf.float32, shape=[None, 784]) for i in range(MAX_CLIENTS)]
placey = [tf.placeholder(tf.float32, shape=[None, 10]) for i in range(MAX_CLIENTS)]
models = [Model(placeX[i], placey[i]) for i in range(MAX_CLIENTS)]

(X, y), (X_test, y_test) = mnist.load_data()
X = X / 255.
X_test = X_test / 255.
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15)
indices = [(y_train == i).nonzero()[0] for i in range(10)]
X_train = [X_train[indices[i]] for i in range(10)]
y_train = [y_train[indices[i]] for i in range(10)]


def create_batches(X, y, percentage=0.9, n=10):
    X1 = [X[i][:int(percentage * len(X[i]))] for i in range(5)] + [X[i][int(percentage * len(X[i])):] for i in
                                                                   range(5, 10)]
    X2 = [X[i][int(percentage * len(X[i])):] for i in range(5)] + [X[i][:int(percentage * len(X[i]))] for i in
                                                                   range(5, 10)]
    y1 = [y[i][:int(percentage * len(y[i]))] for i in range(5)] + [y[i][int(percentage * len(y[i])):] for i in
                                                                   range(5, 10)]
    y2 = [y[i][int(percentage * len(y[i])):] for i in range(5)] + [y[i][:int(percentage * len(y[i]))] for i in
                                                                   range(5, 10)]
    node1 = [np.concatenate(X1, axis=0), np.concatenate(y1, axis=0)]
    node2 = [np.concatenate(X2, axis=0), np.concatenate(y2, axis=0)]
    perm1 = np.random.RandomState(32).permutation(len(node1[0]))
    perm2 = np.random.RandomState(32).permutation(len(node2[0]))
    node1[0], node1[1] = (node1[0][perm1]).reshape(-1, 784), np.eye(n)[node1[1][perm1]]
    node2[0], node2[1] = (node2[0][perm2]).reshape(-1, 784), np.eye(n)[node2[1][perm2]]
    return node1, node2


X = [[], []]
y = [[], []]

(X[0], y[0]), (X[1], y[1]) = create_batches(X_train, y_train, percentage=0.90)

X_t, y_t = X_test.reshape(-1, 784), np.eye(10)[y_test]

X_val = X_val.reshape(-1, 784)


# train/compare vanilla sgd and ewc
def train_task(model, epochs, batch_size, disp_freq, trainset, testsets, placeX, placey, lams=[0], plot_diffs=False):
    num_iter = (epochs * len(trainset[0])) // batch_size
    for l in range(len(lams)):
        # lams[l] sets weight on old task(s)
        # model.restore(sess) # reassign optimal weights from previous training session
        if (lams[l] == 0):
            model.set_vanilla_loss()
        else:
            model.update_ewc_loss(lams[l])
        # initialize test accuracy array for each task 
        test_accs = []
        for task in range(len(testsets)):
            test_accs.append([])
        # train on current task
        for iter in range(num_iter):
            batch = trainset[0][iter * batch_size:iter * batch_size + batch_size], trainset[1][
                                                                                   iter * batch_size:iter * batch_size + batch_size]
            model.train_step.run(feed_dict={placeX: batch[0], placey: batch[1]})
            if iter % disp_freq == 0:
                if plot_diffs:
                    plt.subplot(1, len(lams), l + 1)
                    plots = []
                    colors = ['r', 'b', 'g']
                for task in range(len(testsets)):
                    feed_dict = {placeX: testsets[task][0], placey: testsets[task][1]}
                    test_accs[task].append(model.accuracy.eval(feed_dict=feed_dict))
                    if plot_diffs:
                        c = chr(ord('A') + task)
                        plot_h, = plt.plot(range(1, iter + 2, disp_freq), test_accs[task][:iter // disp_freq + 1],
                                           colors[task], label="task " + c)
                        plots.append(plot_h)
                if plot_diffs:
                    plot_test_acc(plots)
                    if l == 0:
                        plt.title("vanilla sgd")
                    else:
                        plt.title("ewc")
                    plt.gcf().set_size_inches(len(lams) * 5, 3.5)
        return test_accs


def get_accuracy(model_filename, client_id):

    m = models[client_id]

    m.load_weights(model_filename)

    feed_dict = {placeX: X_t, placey: y_t}
    accuracy = m.accuracy.eval(feed_dict=feed_dict)

    return(accuracy)


def ClientUpdate(model_filename, output_file):
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        accs = []
        for i in range(MAX_CLIENTS):
            m = models[i]
            m.load_weights(model_filename)
            m.compute_fisher(X_val, sess, num_samples=200, plot_diffs=False)
            m.star()
            acc = train_task(m, epochs, batch_size, 50, [X[i], y[i]], [(X[0], y[0]), (X[1], y[1]), (X_t, y_t)], placeX[i],
                       placey[i], lams=[25])
            m.save_weights(output_file)
            print(i)
            accs.append(acc[-1][-1])

        print(accs)
        with open('accuracy.txt', 'w') as f:
                f.write("%s" % " ".join(map(str,accs)))


## Write or import
def get_model_filename(i):
    files = {}
    files[0] = "0x6c156B11819f05Ad79794B008753729466D3Ccd5"
    files[1] = "0xB7D2d5d7824e4ee393c4D83B9014CFb0b66078d5"

    return "../organization/models/" + files[i]


def FederatedAveraging(output_file):
    WEIGHTS = [np.zeros_like(v) for v in models[0].var_list]
    clients = np.random.permutation(MAX_CLIENTS)[:np.random.randint(1, MAX_CLIENTS + 1)]

    for client in clients:
        model_filename = get_model_filename(client)
        # print(model_filename)
        weight = pickle.load(open(model_filename, "rb"))
        for v in range(len(models[0].var_list)):
            WEIGHTS[v] = WEIGHTS[v] + (weight[v] / len(clients))
    with open(output_file, "wb") as f:
        pickle.dump(WEIGHTS, f)


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("Usage python3 client ai.py srcpath destpath")
        exit()


    if sys.argv[1] == 'client':
        ClientUpdate(sys.argv[2], sys.argv[3])

    elif sys.argv[1] == 'org':
        FederatedAveraging(sys.argv[2])
