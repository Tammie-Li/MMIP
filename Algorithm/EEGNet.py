import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class EEGNet(nn.Module):
    def __init__(self, num_classes):
        super(EEGNet, self).__init__()
        self.drop_out = 0.4

        self.block_1 = nn.Sequential(
            nn.ZeroPad2d((15, 16, 0, 0)),
            nn.Conv2d(1, 8, (1, 32), bias=False),
            nn.BatchNorm2d(8)
        )
        
        # block 2 and 3 are implements of Depthwise Conv and Separable Conv
        self.block_2 = nn.Sequential(
            nn.Conv2d(8, 16, (64, 1), groups=8, bias=False),
            nn.BatchNorm2d(16),
            nn.ELU(),
            nn.AvgPool2d((1, 4)),
            nn.Dropout(self.drop_out)
        )
        
        self.block_3 = nn.Sequential(
            nn.ZeroPad2d((7, 8, 0, 0)),
            nn.Conv2d(16, 16, (1, 16), groups=16, bias=False),
            nn.Conv2d(16, 16, (1, 1), bias=False),
            nn.BatchNorm2d(16), 
            nn.ELU(),
            nn.AvgPool2d((1, 8)),
            nn.Dropout(self.drop_out)
        )
        
        self.fc1 = nn.Linear((32 * (256 // 64)), num_classes)
    
    def forward(self, x):
        x = x.reshape(x.shape[0], 1, x.shape[1], x.shape[2])
        x = self.block_1(x)
        # fea = x

        x = self.block_2(x)
        x = self.block_3(x)

        x = x.view(x.size(0), -1)        

        logits = self.fc1(x)
        probas = F.softmax(logits, dim=1)
        return probas