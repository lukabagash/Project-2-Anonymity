from k_anonymity import Anonymization

def main():
    data_path = "../data/Flight_DataSet.csv"
    anon = Anonymization(data_path)


    k_values = [15, 20, 50]
    l_values = [3, 6, 15]
    for k, l in zip(k_values, l_values):
        anon.anonymize(k, l)
        anon.save_to_csv(f"../data/anonymized_data_k_{k}.csv")
         # Calculate KL-divergence-based utility for Flight Status
        utility = anon.measure_utility()
      
        print(f"Utility for k={k}, and l={l}: {utility}")

if __name__ == "__main__":
    main()
