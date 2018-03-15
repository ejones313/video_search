import numpy as np
import torch
import torch.nn as nn
import torch.utils.data as data
from torch.autograd import Variable
import pickle
import random
import utils
import math
import data_prep

def validate_L2(word_model, vid_model, things, indices, cuda = False):
    vid_model.eval()
    word_model.eval()

    #Fix get_dataset to return not tuples.

    words, vids = things
    word_indices, vid_indices = indices
    vid_output = vid_model(vids)
    word_output = word_model(words)

    word_output, word_lengths = nn.utils.rnn.pad_packed_sequence(word_output)
    vid_output, vid_lengths = nn.utils.rnn.pad_packed_sequence(vid_output)

    word_order = np.zeros(word_indices.shape)
    vid_order = np.zeros(vid_indices.shape)
    for i in range(word_indices.size()[0]):
        word_order[word_indices[i]] = i
        vid_order[vid_indices[i]] = i
    word_output = word_output[np.array(word_lengths)-1, np.arange(word_output.shape[1]), :]
    vid_output = vid_output[np.array(vid_lengths)-1, np.arange(vid_output.shape[1]), :]
    word_unscrambled = word_output[word_order,:].data.numpy()
    vid_unscrambled = vid_output[vid_order,:].data.numpy()

    dist_matrix = np.zeros((word_unscrambled.shape[0], word_unscrambled.shape[0]))
    
    for i in range(word_unscrambled.shape[0]):
        dist_matrix[i,:] = np.linalg.norm(word_unscrambled[i,:] - vid_unscrambled, axis = 1, keepdims = True).T
        
    avg_prctile_pos = np.sum(dist_matrix.T > np.diag(dist_matrix))/(dist_matrix.shape[0]**2)
    avg_dist_diff = np.mean((np.diag(dist_matrix) - (np.sum(dist_matrix, axis = 1) - np.diag(dist_matrix))/(dist_matrix.shape[0] - 1)))

    return float(avg_prctile_pos), float(avg_dist_diff)


def validate_cosine(word_model, vid_model, things, indices, top_perc = 20, cuda = False):
    vid_model.eval()
    word_model.eval()

    #Fix get_dataset to return not tuples.

    words, vids = things
    word_indices, vid_indices = indices
    vid_output = vid_model(vids)
    word_output = word_model(words)

    word_output, word_lengths = nn.utils.rnn.pad_packed_sequence(word_output)
    vid_output, vid_lengths = nn.utils.rnn.pad_packed_sequence(vid_output)

    word_order = np.zeros(word_indices.shape)
    vid_order = np.zeros(vid_indices.shape)
    for i in range(word_indices.size()[0]):
        word_order[word_indices[i]] = i
        vid_order[vid_indices[i]] = i
    word_output = word_output[np.array(word_lengths)-1, np.arange(word_output.shape[1]), :]
    vid_output = vid_output[np.array(vid_lengths)-1, np.arange(vid_output.shape[1]), :]
    word_unscrambled = word_output[word_order,:].data.numpy()
    vid_unscrambled = vid_output[vid_order,:].data.numpy()

    word_norm_scale = np.linalg.inv(np.diag(np.linalg.norm(word_unscrambled, axis=1)))
    vid_norm_scale = np.linalg.inv(np.diag(np.linalg.norm(vid_unscrambled, axis=1)))
    
    prod_matrix = word_norm_scale@word_unscrambled@vid_unscrambled.T@vid_norm_scale
        
    avg_prctile_pos = np.sum(prod_matrix.T < np.diag(prod_matrix))/(prod_matrix.shape[0]**2)
    avg_dist_diff = -1*np.mean((np.diag(prod_matrix) - (np.sum(prod_matrix, axis = 1) - np.diag(prod_matrix))/(prod_matrix.shape[0] - 1)))

    return float(avg_prctile_pos), float(avg_dist_diff)
