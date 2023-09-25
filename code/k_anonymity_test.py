from k_anonymity import Anonymization

def main():
    data_path = "../data/Flight_DataSet.csv"
    anon = Anonymization(data_path)

    k_values = [2, 5, 50]
    for k in k_values:
        anon.anonymize(k)
        anon.save_to_csv(f"../data/anonymized_data_k_{k}.csv")
        utility = anon.measure_utility()
        print(f"Utility for k={k}: {utility}")

if __name__ == "__main__":
    main()