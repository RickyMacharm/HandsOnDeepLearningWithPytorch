# copied from pytorch ignite source code
from argparse import ArgumentParser
import logging

from torch import nn
from torch.optim import SGD
from torch.utils.data import DataLoader
import torch.nn.functional as F
from torchvision.transforms import Compose, ToTensor, Normalize
from torchvision.datasets import MNIST

from ignite.engine import Events, Engine


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv2_drop = nn.Dropout2d()
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
        x = x.view(-1, 320)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x, dim=-1)


def get_data_loaders(train_batch_size, val_batch_size):
    data_transform = Compose([ToTensor(), Normalize((0.1307,), (0.3081,))])

    train_loader = DataLoader(MNIST(download=True, root=".", transform=data_transform, train=True),
                              batch_size=train_batch_size, shuffle=True)

    val_loader = DataLoader(MNIST(download=False, root=".", transform=data_transform, train=False),
                            batch_size=val_batch_size, shuffle=False)
    return train_loader, val_loader


def custom_loop(trainer, batch):
    optimizer.zero_grad()
    x, y = prepare_batch(batch)
    pred = model(x)
    loss = loss_fn(pred, y)
    loss.backward()
    optimizer.step()
    return loss.item()

train_loader, val_loader = get_data_loaders(train_batch_size, val_batch_size)
model = Net()
device = 'cpu'
optimizer = SGD(model.parameters(), lr=lr, momentum=momentum)
trainer = Engine(custom_loop)

# Setup debug level of engine logger:
trainer._logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s|%(name)s|%(levelname)s| %(message)s")
ch.setFormatter(formatter)
trainer._logger.addHandler(ch)

@trainer.on(Events.ITERATION_COMPLETED)
def log_training_loss(engine):
    iter = (engine.state.iteration - 1) % len(train_loader) + 1
    if iter % log_interval == 0:
        print("Epoch[{}] Iteration[{}/{}] Loss: {:.2f}"
              "".format(engine.state.epoch, iter, len(train_loader), engine.state.output))

    if engine.state.iteration == crash_iteration:
        raise Exception("STOP at {}".format(engine.state.iteration))

@trainer.on(Events.EPOCH_COMPLETED)
def log_training_results(engine):
    evaluator.run(train_loader)
    metrics = evaluator.state.metrics
    avg_accuracy = metrics['accuracy']
    avg_nll = metrics['nll']
    print("Training Results - Epoch: {}  Avg accuracy: {:.2f} Avg loss: {:.2f}"
          .format(engine.state.epoch, avg_accuracy, avg_nll))

@trainer.on(Events.EPOCH_COMPLETED)
def log_validation_results(engine):
    evaluator.run(val_loader)
    metrics = evaluator.state.metrics
    avg_accuracy = metrics['accuracy']
    avg_nll = metrics['nll']
    print("Validation Results - Epoch: {}  Avg accuracy: {:.2f} Avg loss: {:.2f}"
          .format(engine.state.epoch, avg_accuracy, avg_nll))

objects_to_checkpoint = {"model": model, "optimizer": optimizer}
engine_checkpoint = EngineCheckpoint(dirname="engine_checkpoint",
                                     to_save=objects_to_checkpoint,
                                     save_interval=100)
trainer.add_event_handler(Events.ITERATION_COMPLETED, engine_checkpoint)

if restore_from == "":
    trainer.run(train_loader, max_epochs=epochs)
else:
    trainer.resume(train_loader, restore_from, to_load=objects_to_checkpoint)


    EPOCH_STARTED = "epoch_started"
    EPOCH_COMPLETED = "epoch_completed"
    STARTED = "started"
    COMPLETED = "completed"
    ITERATION_STARTED = "iteration_started"
    ITERATION_COMPLETED = "iteration_completed"
    EXCEPTION_RAISED = "exception_raised"