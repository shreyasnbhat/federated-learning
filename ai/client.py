import tensorflow as tf
import numpy as np
from copy import deepcopy
from tensorflow.examples.tutorials.mnist import input_data
from sklearn.model_selection import train_test_split

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from IPython import display

from model import Model

from keras.datasets import mnist

(X, y), (X_test, y_test) = mnist.load_data()
X = X/255.
X_test = X_test/255.
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15)
indices = [(y_train==i).nonzero()[0] for i in range(10)]
X_train = [X_train[indices[i]] for i in range(10)]
y_train = [y_train[indices[i]] for i in range(10)]

def create_batches(X, y, percentage=0.9, n=10):
    X1 = [X[i][:int(percentage*len(X[i]))] for i in range(5)] + [X[i][int(percentage*len(X[i])):] for i in range(5, 10)]
    X2 = [X[i][int(percentage*len(X[i])):] for i in range(5)] + [X[i][:int(percentage*len(X[i]))] for i in range(5, 10)]
    y1 = [y[i][:int(percentage*len(y[i]))] for i in range(5)] + [y[i][int(percentage*len(y[i])):] for i in range(5, 10)]
    y2 = [y[i][int(percentage*len(y[i])):] for i in range(5)] + [y[i][:int(percentage*len(y[i]))] for i in range(5, 10)]
    node1 = [np.concatenate(X1, axis=0), np.concatenate(y1, axis=0)]
    node2 = [np.concatenate(X2, axis=0), np.concatenate(y2, axis=0)]
    perm1 = np.random.RandomState(32).permutation(len(node1[0]))
    perm2 = np.random.RandomState(32).permutation(len(node2[0]))
    node1[0], node1[1] = (node1[0][perm1]).reshape(-1, 784), np.eye(n)[node1[1][perm1]]
    node2[0], node2[1] = (node2[0][perm2]).reshape(-1, 784), np.eye(n)[node2[1][perm2]]
    return node1, node2

(X1, y1), (X2, y2) = create_batches(X_train, y_train, percentage=0.90)

X_t, y_t = X_test.reshape(-1, 784), np.eye(10)[y_test]

X_val = X_val.reshape(-1, 784)


def train_task(model, epochs, batch_size, disp_freq, trainset, testsets, placeX, placey, lams=[0], plot_diffs=False):
    num_iter = (epochs*len(trainset[0]))//batch_size
    for l in range(len(lams)):
        # lams[l] sets weight on old task(s)
        model.restore(sess) # reassign optimal weights from previous training session
        if(lams[l] == 0):
            model.set_vanilla_loss()
        else:
            model.update_ewc_loss(lams[l])
        # initialize test accuracy array for each task 
        test_accs = []
        for task in range(len(testsets)):
            test_accs.append([])
        # train on current task
        for iter in range(num_iter):
            batch = trainset[0][iter*batch_size:iter*batch_size+batch_size], trainset[1][iter*batch_size:iter*batch_size+batch_size] 
            model.train_step.run(feed_dict={placeX: batch[0], placey: batch[1]})
            if iter % disp_freq == 0 and plot_diffs == True:
                plt.subplot(1, len(lams), l+1)
                plots = []
                colors = ['r', 'b', 'g']
                for task in range(len(testsets)):
                    feed_dict={placeX: testsets[task][0], placey: testsets[task][1]}
                    test_accs[task].append(model.accuracy.eval(feed_dict=feed_dict))
                    c = chr(ord('A') + task)
                    plot_h, = plt.plot(range(1,iter+2,disp_freq), test_accs[task][:iter//disp_freq+1], colors[task], label="task " + c)
                    plots.append(plot_h)
                plot_test_acc(plots)
                if l == 0: 
                    plt.title("vanilla sgd")
                else:
                    plt.title("ewc")
                plt.gcf().set_size_inches(len(lams)*5, 3.5)
        return test_accs


placeX = tf.placeholder(tf.float32, shape=[None, 784])
placey = tf.placeholder(tf.float32, shape=[None, 10])
epochs = 1
batch_size = 64


def ClientUpdate(model_filename, output_file):
    for i in range(clients):
        m = Model(placeX, placey)
        m.load_weights(model_filename)
        m.compute_fisher(X_t, sess, num_samples=400, plot_diffs=False)
        train_task(m, epochs, batch_size, 20, [X[i], y[i]], [(X1, y1), (X2, y2), (X_t, y_t)], placeX, placey, lams=[0, 25])
        m.save_weights(output_file)
