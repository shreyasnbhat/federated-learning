## Federated Learning System

#### Prerequisites
- Setup `ganache-cli` and `truffle`.
- Run `setup.sh` to setup libraries.
- Start the IPFS Daemon by running `ipfs daemon`
- Run the client and app using the `run.py` scripts.


#### The Idea
What if we wanted to learn about user behaviour in applications? What if you want to know whether or not the user is interested in the product you suggest him/her? Some of the current machine learning models collect event history logs and send it to a central server, where the model is trained on the data collected. Such an action requires the company to make sure it maintains a certain degree of consumer anonymity amongst dealing with many other privacy issues. Also, data centralization has a high computational cost associated with it.

Instead of doing this, what if we could learn some trends locally on a device and send an updated model to the central server. Say that we have `n` clients and each of these clients has their own local model. We use an algorithm titled `FederatedAveraging` to average out these models and help improve the existing base model, which is then sent back to the users and the whole process repeats. The solution thus allows the base model to learn from user data without it ever residing on a central server thus preserving privacy. The idea proposed has been termed as Federated Learning by Google. 
But, this algorithm has an issue of its own.

When training models again on new data, deep neural networks quickly tend to forget what they have learned before and morph into a network that learns only the new data. This characteristic of Deep networks is called `Catastrophic forgetting` and dealing with this issue is very important for Federated learning algorithms to achieve success. We address this issue using a methodology called `Elastic Weight Consolidation`. This method makes sure the network doesn't morph drastically when its trained on new data.

Considering the above problems, we have spent a great deal of time in writing our `Machine Learning Model Processor`.  Our hack mainly has 3 major components i.e. `Client Side Interface` , `Organization Side Interface` and a `Machine Learning Model Processor`. One could consider that our system proceeds in a round by round fashion. In a round, the organization publishes a `base_model` to `IPFS` which the client uses to learn trends locally. The client then publishes an incremental model update to `IPFS`. The organization then uses the `FederatedAveraging` mechanism to merge all these incremental models into one model and sets it as the new `base_model`. The process repeats and over time the `base_model` learns from trends generated on all devices.

