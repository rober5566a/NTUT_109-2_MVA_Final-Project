import os
import math
import random
import pandas as pd
import torch
import torch.utils.data as Data
import torch.nn as nn
from find_file_name import get_filenames
from Dataloader import ImgDataset
from Train_model import train_model
from Model.Model_Perform_Tool import save_history_csv, draw_plot
from Model.CNN import CNN


def get_device():
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    print('GPU State:', device)

    return device


def calc_dataset_size(train_path, test_path):
    train_filenames = get_filenames(train_path, 'jpg')
    test_filenames = get_filenames(test_path, 'jpg')
    random.shuffle(train_filenames)
    random.shuffle(test_filenames)
    dataset_size = len(train_filenames)
    return train_filenames, test_filenames, dataset_size


def train_model_1time_flow(train_filenames, test_filenames, model, EPOCH=30):
    train_datasets = ImgDataset(
        train_filenames, classifier=str(classifier), isTrain=True, rateMagnifyData=3.0)
    test_datasets = ImgDataset(
        test_filenames, classifier=str(classifier), dataAutoBalance=False)

    train_loader = Data.DataLoader(
        dataset=train_datasets,
        batch_size=64,  # <<<setting batch_size>>>
        shuffle=True,
        num_workers=0
    )

    # print(cnn)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_func = nn.CrossEntropyLoss()

    history = train_model(device_0, EPOCH,
                          train_loader, test_datasets, model=model)
    try:
        torch.save(model.state_dict(),
                   'out/class_{}/cnn-model.pkl'.format(classifier))
    except:
        os.mkdir('out/class_{}'.format(classifier))
        torch.save(model.state_dict(),
                   'out/class_{}/cnn-model.pkl'.format(classifier))

    return history


if __name__ == "__main__":
    device_0 = get_device()

    for classifier in range(1, 5):
        train_path = "Data/train_images/select-encode_part"
        test_path = "Data/test_images/select-encode_part"

        # <<<setting train_size>>>
        num_train_size = 1000
        total_train_filenames, total_test_filenames, datasets_size = calc_dataset_size(
            train_path, test_path)

        train_times = math.ceil(datasets_size / num_train_size)

        # recored all the times of model train history
        total_train_loss_ls = []
        total_train_acc_ls = []
        total_test_acc_ls = []
        for train_time in range(train_times):
            torch.cuda.empty_cache()
            model = CNN().to(device_0)
            if train_time != 0:
                model.load_state_dict(torch.load(
                    'out/class_{}/cnn-model.pkl'.format(classifier)))
                model.eval()

            bound_L = num_train_size * train_time
            bound_H = num_train_size * (train_time + 1)
            if bound_H > len(total_train_filenames):
                bound_H = len(total_train_filenames)

            train_filenames = total_train_filenames[bound_L: bound_H]

            history = train_model_1time_flow(
                train_filenames, total_test_filenames[:1000], model, EPOCH=30)
            (train_loss_ls, train_acc_ls, test_acc_ls) = history

            total_train_loss_ls.extend(train_loss_ls)
            total_train_acc_ls.extend(train_acc_ls)
            total_test_acc_ls.extend(test_acc_ls)

        save_history_csv(len(total_train_loss_ls), total_train_loss_ls, total_train_acc_ls,
                         total_test_acc_ls, save_path='out/class_{}'.format(classifier))
        draw_plot(len(total_train_loss_ls), total_train_loss_ls, total_train_acc_ls,
                  total_test_acc_ls, save_path='out/class_{}'.format(classifier))

        torch.save(model,
                   'out/class_{}/cnn-model_compelet.pkl'.format(classifier))