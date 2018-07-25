# ************************************************************
# Author : Bumsoo Kim, 2018
# Github : https://github.com/meliketoy/graph-cnn.pytorch
#
# Korea University, Data-Mining Lab
# Graph Convolutional Neural Network
#
# Description : train.py
# The main code for training classification networks.
# ***********************************************************

import time
import numpy as np
import torch
import torch.nn.functional as F
import torch.optim as optim

from utils import *
from models import GCN
from opts import TrainOptions

"""
N : number of nodes
D : number of features per node
E : number of classes

@ input :
    - adjacency matrix (N x N)
    - feature matrix (N x D)
    - label matrix (N x E)

@ dataset :
    - citeseer
    - cora
    - pubmed
"""
opt = TrainOptions().parse()

# Data upload
adj, features, labels, idx_train, idx_val, idx_test = load_data(path=opt.dataroot, dataset=opt.dataset)
use_gpu = torch.cuda.is_available()

best_model = None
best_acc = 0

# Define the model and optimizer
model = GCN(
        nfeat = features.shape[1],
        nhid = opt.num_hidden,
        nclass = labels.max().item() + 1,
        dropout = opt.dropout
)

if (opt.optimizer == 'SGD'):
    optimizer = optim.SGD(
            model.parameters(),
            lr = opt.lr,
            weight_decay = opt.weight_decay,
            momentum = 0.9
    )
elif (opt.optimizer == 'Adam'):
    optimizer = optim.Adam(
            model.parameters(),
            lr = opt.lr
    )
else:
    print("Optimizer is not defined")
    sys.exit(1)

def lr_scheduler(epoch, opt):
    return opt.lr * (0.2 ** (epoch / opt.lr_decay_epoch))

# Train
def train(epoch):
    global best_model
    global best_acc

    t = time.time()
    model.train()
    optimizer.lr = lr_scheduler(epoch, opt)
    optimizer.zero_grad()

    output = model(features, adj)
    loss_train = F.nll_loss(output[idx_train], labels[idx_train])
    acc_train = accuracy(output[idx_train], labels[idx_train])

    loss_train.backward()
    optimizer.step()

    # Validation for each epoch
    model.eval()
    output = model(features, adj)
    loss_val = F.nll_loss(output[idx_val], labels[idx_val])
    acc_val = accuracy(output[idx_val], labels[idx_val])

    if acc_val > best_acc:
        print("=> Training Epoch #{} : lr = {}".format(epoch, optimizer.lr))
        print("| Training acc : {}%".format(acc_train.data.cpu().numpy() * 100))
        print("| Best acc : {}%". format(acc_val.data.cpu().numpy() * 100))
        best_acc = acc_val
        best_model = model

# Test
def test():
    print("\n[STEP 4] : Testing")
    best_model.eval()
    output = best_model(features, adj)
    acc_val = accuracy(output[idx_test], labels[idx_test])

    print("| Test acc : {}%\n".format(acc_val.data.cpu().numpy() * 100))

# Main code for training
if __name__ == "__main__":

    print("\n[STEP 2] : Obtain (adjacency, feature, label) matrix")
    print("| Adjacency matrix : {}".format(adj.shape))
    print("| Feature matrix   : {}".format(features.shape))
    print("| Label matrix     : {}".format(labels.shape))

    if use_gpu:
        _, features, adj, labels, idx_train, idx_val, idx_test = \
                list(map(lambda x: x.cuda(), [model, features, adj, labels, idx_train, idx_val, idx_test]))

    # Test forward
    print("\n[STEP 3] : Dummy Forward")
    output = model(features, adj)
    print("| Shape of result : {}".format(output.shape))

    # Training
    print("\n[STEP 4] : Training")
    for epoch in range(1, opt.epoch+1):
        train(epoch)
    print("=> Training finished!")

    # Testing
    test()