# Dataset-LLM-Based-Control-Policies-for-Intelligent-Traffic-Intersections-in-SUMO-Veins

This repository contains the dataset used to train and validate the large language model controller presented in the paper “LLM-Based Control Policies for Intelligent Traffic Intersections in SUMO–Veins.”
The data was generated through simulation rollouts collected from a SUMO–OMNeT++/Veins co-simulation environment, where vehicles interact at signalized intersections under varying traffic conditions.

During the simulations, the traffic state of each controlled vehicle and its surrounding context were periodically recorded through the TraCI interface. These observations were then transformed into supervised state–action pairs used to fine-tune the LLM-based decision controller. Each sample therefore represents a structured description of the traffic state together with the corresponding control action applied by the controller.

The dataset contains 108,498 samples, divided into 97,649 training samples and 10,849 validation samples. All data is stored in JSONL format, where each line corresponds to a single state–action example extracted from the simulation rollouts.

The recorded state information includes variables describing the vehicle and its local environment, such as vehicle identifier, lane position, speed, acceleration, waiting time, distance to the leading vehicle, and information about the upcoming traffic light. The associated action describes the maneuver selected by the controller, including longitudinal behavior (e.g., acceleration or braking) and lane-related decisions.

This dataset was generated to support research on LLM-based decision making in traffic control systems, and can be used for tasks such as model fine-tuning, policy learning from simulation data, or evaluation of intelligent traffic controllers.

The simulations used to generate the dataset were executed using the SUMO traffic simulator integrated with OMNeT++ through the Veins framework, enabling synchronized traffic and communication modeling.
