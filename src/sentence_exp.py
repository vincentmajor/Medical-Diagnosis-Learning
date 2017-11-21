exp_name = 'small_5label_adam_lrdecay'

import torch
use_cuda = torch.cuda.is_available()
if use_cuda:
    torch.cuda.set_device(1)


# In[27]:


import sys
from collections import Counter
#sys.path.append('/home/pau/Medical-Diagnosis-Learning/src')
sys.path.append('/home/ag4508/Medical-Diagnosis-Learning/src')
from data_util import *
from util_icu_train import get_labels

# easy_label_map = {"4019":0, "V290":1}
# training_set = load_data_csv('../notes_sample.csv', easy_label_map)

easy_label_map = get_labels('/misc/vlgscratch2/LecunGroup/anant/nlp/labels.txt')
training_set = load_data_csv('/misc/vlgscratch2/LecunGroup/anant/nlp/notes_sample_5class.csv', easy_label_map)
#training_set = training_set[:100]
print("FD of labels:", Counter([_['label'] for _ in training_set]))

PADDING = "<PAD>"
UNKNOWN = "<UNK>"
max_seq_length = 20

word_to_ix, vocab_size, word_counter = build_dictionary([training_set], PADDING, UNKNOWN)
sentences_to_padded_index_sequences(word_to_ix, [training_set], max_seq_length, PADDING, UNKNOWN)


# In[31]:


from models import *
batch_size = 256
num_workers = 4
embed_dim = 50
hidden_dim = 100
lr = 1e-2

val_set = training_set[int(0.8*len(training_set)):]
training_set = training_set[:int(0.8*len(training_set))]

train_loader = torch.utils.data.DataLoader(dataset= TextData(training_set), batch_size=batch_size, shuffle=True, 
                                                           num_workers=num_workers)
val_loader = torch.utils.data.DataLoader(dataset= TextData(val_set), batch_size=batch_size, shuffle=True, 
                                                           num_workers=num_workers)


# In[33]:


model = LSTMModel(vocab_size, embed_dim, hidden_dim, easy_label_map, batch_size, use_cuda)
opti = torch.optim.Adam(model.parameters(), lr=lr, betas=(0.5, 0.999))
crit = nn.CrossEntropyLoss()

if use_cuda:
    model.cuda()
    crit.cuda()

from eval import *    

step = 0
step_log = []
loss_log = []
val_acc_log = []
val_loss_log = []
train_acc_log = []

for nu_ep in range(3):
    for batch in train_loader:
        if batch[0].size(0) != batch_size:
            continue
        model.zero_grad()
        x = Variable(batch[0])
        y = Variable(batch[1].view(-1))
        if use_cuda:
            x, y = x.cuda(), y.cuda()

        hidden = model.init_hidden()
        x = model(x, hidden)
        loss = crit(x, y)
        loss.backward()
        opti.step()

        if step % 100 == 0:
            model.eval()
            _, predicted = torch.max(x.data, 1)    
            train_acc = (predicted == y.data).sum() / batch[1].size(0)

            val_acc, val_loss, pred_vals = evaluate(model, val_loader, batch_size, crit, use_cuda)
            model.train()        
            print("Step: %d, Loss: %.4f, Train Acc: %.2f, Validation Acc: %.2f, Val loss: %.2f"%(step, loss.data[0], train_acc, val_acc, val_loss))
            step_log.append(step)
            loss_log.append(loss.data[0])
            train_acc_log.append(train_acc)
            val_acc_log.append(val_acc)
            val_loss_log.append(val_loss)
        if step % 1000 == 0:
            print(pred_vals) 
        step += 1
    lr *= 0.1
    opti = torch.optim.Adam(model.parameters(), lr=lr, betas=(0.5, 0.999))



import pickle
f = open('results_%s.pkl'%exp_name, 'w')
pickle.dump({'step_log': step_log, 'loss_log': loss_log, 'val_loss_log': val_loss_log, 'val_loss_log': val_loss_log, 'train_acc_log': train_acc_log}, f)
f.close()
#import matplotlib.pyplot as plt
#get_ipython().magic(u'matplotlib inline')

#plt.plot(step_log, loss_log)



