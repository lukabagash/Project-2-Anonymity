# Project-2: Privacy vs. Utility

# Flight Data Anonymization and Utility Measurement

This repository contains code for anonymizing flight data using k-anonymity and diversifying it using *l*-diversity, while also measuring the utility of the anonymized data. The project aims to balance the need for privacy protection with data utility in a flight dataset. 

## Getting Started

### Installation

1. Clone this repository:

```bash
git clone https://github.com/lukabagash/Project-2-Anonymity.git
cd Project-2-Anonymity
```

2. Install the required Python libraries:

```bash 
pip install pandas
pip install numpy
```
## Usage

### 1. Data Preparation

Before you can start anonymizing the flight data, you need to obtain the dataset. You can download the dataset from [here](https://github.com/lukabagash/Project-1-Anonymity/blob/main/data/Flight_DataSet.csv). Place the dataset in the `data`/ directory. 

### 2. Running the Anonymization Code

To anonymize the flight data for different k-values & *l*-values, follow these steps:

1. Open the `k_anonymity_test.py` script.
2. Set the `data_path` variable to the path of your flight dataset:

```python
data_path = "data/Flight_DataSet.csv"
```

Run the `k_anonymity_test.py` script:
```bash
python k_anonymity_test.py
```

The script will perform k-anonymization for the specified k-values and save the anonymized datasets in the `data`/ directory with filenames like `anonymized_data_k_2.csv`, `anonymized_data_k_5.csv`, etc.

### 3. Measuring Utility

To measure the utility of the anonymized datasets, you can run the following command:
```bash
python k_anonymity.py
```

The utility scores for different k-values will be printed to the console.

## Results

The anonymized datasets can be found in the `data`/ directory. You can use these datasets for further analysis while considering the trade-off between privacy (k-anonymity) and utility.

## Acknowledgments
Luka Bagash

Haris Iqbal
