import pandas as pd
import numpy as np

class Anonymization:

    def __init__(self, data_path):
        self.data = self.load_data(data_path)
        self.anonymized_data = None
        self.utility_value = 1

    def load_data(self, data_path):
        """
        Load the dataset from the given path.
        """
        return pd.read_csv(data_path, encoding="ISO-8859-1")



    def suppress_attributes(self, columns_to_suppress):
        """
        Suppress the specified columns from the dataset.
        """
        self.anonymized_data = self.data.drop(columns=columns_to_suppress, errors='ignore')

        utility_loss = len(columns_to_suppress) * 0.01
        self.utility_value -= utility_loss

    def generalize_level_1(self):
        """
        Level 1 Generalization: Remove the day from the Departure Date.
        """

        self.anonymized_data['Departure Date'] = pd.to_datetime(self.data['Departure Date']).dt.to_period('M')

        self.utility_value -= 0.05
    
    def generalize_level_2(self, k, l):
        """
        Level 2 Generalization: Adjust the Departure Date and Age based on k-anonymity requirements.
        """
        # Group by the QIDs and count the number of records in each group.
        main_groups = self.anonymized_data.groupby(['Gender', 'Airport Continent'])

        new_dates = []
        new_ages = []
        utility_loss = 0

        for _, group in main_groups:
            # Sort the group by 'Departure Date' and then by 'Age'
            group = group.sort_values(['Departure Date', 'Age'])

            # Create a subset group based on 'Departure Date' and 'Age' and count the records
            subset_groups = group.groupby(['Departure Date', 'Age']).size().reset_index(name='count')

            i = 0
            last_generalized_start_date = None
            last_generalized_start_age = None
            prev_count = None
            while i < len(subset_groups):
                # Get the counts for each Flight Status within the subset group
                flight_status_counts = group[(group['Departure Date'] == subset_groups.iloc[i]['Departure Date']) & 
                                         (group['Age'] == subset_groups.iloc[i]['Age'])].groupby('Flight Status').size().to_dict()
                total_count = subset_groups.iloc[i]['count']

                # Check if the group meets the k-anonymity and l-diversity requirements
                if total_count < k or any(flight_status_counts.get(status, 0) < l for status in ['Delayed', 'On Time', 'Cancelled']):
                    start_date = subset_groups.iloc[i]['Departure Date']
                    start_age = subset_groups.iloc[i]['Age']
                    end_date = start_date
                    end_age = start_age
                    # Keep adding records from the next groups until we have at least k records and l-diversity.
                    while (total_count < k or any(flight_status_counts.get(status, 0) < l for status in ['Delayed', 'On Time', 'Cancelled'])) and i < len(subset_groups) - 1:
                        i += 1
                        total_count += subset_groups.iloc[i]['count']
                        next_flight_status_counts = group[(group['Departure Date'] == subset_groups.iloc[i]['Departure Date']) & 
                                                          (group['Age'] == subset_groups.iloc[i]['Age'])].groupby('Flight Status').size().to_dict()
                        for status in ['Delayed', 'On Time', 'Cancelled']:
                            flight_status_counts[status] = flight_status_counts.get(status, 0) + next_flight_status_counts.get(status, 0)

                        end_date = subset_groups.iloc[i]['Departure Date']
                        end_age = subset_groups.iloc[i]['Age']

                    # If we're at the last subset group and it's less than k, merge with the previous group
                    if i == len(subset_groups) - 1 and (total_count < k or any(flight_status_counts.get(status, 0) < l for status in ['Delayed', 'On Time', 'Cancelled'])):
                        if prev_count:
                            new_dates = new_dates[:-prev_count]
                            new_ages = new_ages[:-prev_count]
                            total_count += prev_count
                        if last_generalized_start_date:
                            start_date = last_generalized_start_date
                        if last_generalized_start_age:
                            start_age = last_generalized_start_age
                        end_date = subset_groups.iloc[i]['Departure Date']
                        end_age = subset_groups.iloc[i]['Age']

                    # Set the new date and age range for the combined group.
                    new_dates.extend([f"{start_date}--{end_date}"] * total_count)
                    new_ages.extend([f"{min(start_age, end_age)}--{max(start_age, end_age)}"] * total_count)
                    last_generalized_start_date = start_date
                    last_generalized_start_age = start_age
                    prev_count = total_count
                    # Calculate utility loss based on the difference in months
                    if total_count >= k:
                        start_month = int(str(start_date).split('-')[1])
                        end_month = int(str(end_date).split('-')[1])
                        age_difference = end_age - start_age
                        utility_loss += age_difference/1700 * 0.0001
                        month_difference = end_month - start_month
                        utility_loss += month_difference/1700 * 0.001
                        self.utility_value -= utility_loss
                else:
                    new_dates.extend([subset_groups.iloc[i]['Departure Date']] * subset_groups.iloc[i]['count'])
                    new_ages.extend([str(subset_groups.iloc[i]['Age'])] * subset_groups.iloc[i]['count'])
                i += 1

        # Sort the self.anonymized_data DataFrame in the same order as the groups DataFrame.
        self.anonymized_data = self.anonymized_data.sort_values(['Gender', 'Airport Continent', 'Departure Date', 'Age'])

        # Directly assign the new_dates and new_ages lists to the respective columns.
        self.anonymized_data['Departure Date'] = new_dates
        self.anonymized_data['Age'] = new_ages
        


    def anonymize(self, k, l):
        """
        Anonymize the data for a given k value.
        This is a placeholder and needs the actual anonymization logic.
        """
        # Suppress the specified columns
        columns_to_suppress = ["Passenger ID", "First Name", "Last Name", "Nationality", "Pilot Name"]

        if columns_to_suppress:
            self.suppress_attributes(columns_to_suppress)

        # Level 1 Generalization
        self.generalize_level_1()

        # Check k-anonymity after Level 1
        grouped = self.anonymized_data.groupby(['Gender', 'Airport Continent', 'Departure Date', 'Age'])
        insufficient_groups_k = grouped.filter(lambda x: len(x) < k)

        # Check l-diversity after Level 1
        insufficient_groups_l = grouped.filter(lambda x: any(x.groupby('Flight Status').size() < l))

        # If there are groups that don't meet the k-anonymity or l-diversity requirement, apply Level 2 Generalization
        if not insufficient_groups_k.empty or not insufficient_groups_l.empty:
            self.generalize_level_2(k,l)
        



    def save_to_csv(self, filename):
        """
        Save the anonymized data to a CSV file.
        """
        if self.anonymized_data is not None:
            self.anonymized_data.to_csv(filename, index=False)
        else:
            print("Data has not been anonymized yet.")


    # def measure_utility(self):
    #     """
    #     Return the utility of the anonymized data.
    #     """
    #     return round(self.utility_value, 2)

    def calculate_probabilities(self, data, sensitive_attribute):
        """
        Calculate the probability distribution of the sensitive attribute.
        """
        # Assuming 'sensitive_attribute' is categorical (discrete)
        probabilities = data[sensitive_attribute].value_counts(normalize=True)
        return probabilities

    def calculate_kl_divergence(self, p, q):
        """
        Calculate KL-divergence between two probability distributions p and q.
        """
        kl_divergence = np.sum(np.where(p != 0, p * np.log(p / q), 0))
        return kl_divergence

    def measure_utility(self, sensitive_attribute):
      """
      Calculate utility based on KL-divergence for the sensitive attribute.
      """
      original_probabilities = self.calculate_probabilities(self.data, sensitive_attribute)
      anonymized_probabilities = self.calculate_probabilities(self.anonymized_data, sensitive_attribute)
      # print("Original Probabilities:")
      # print(original_probabilities)
      # print("Anonymized Probabilities:")
      # print(anonymized_probabilities)
    
      kl_divergence = self.calculate_kl_divergence(original_probabilities, anonymized_probabilities)

      return kl_divergence
