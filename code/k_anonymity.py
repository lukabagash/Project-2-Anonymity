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

        # utility_loss = len(columns_to_suppress) * 0.01
        # self.utility_value -= utility_loss

    def generalize_level_1(self):
        """
        Level 1 Generalization: Remove the day from the Departure Date.
        """

        self.anonymized_data['Departure Date'] = pd.to_datetime(self.data['Departure Date']).dt.to_period('M')

        #self.utility_value -= 0.05
    
    def generalize_level_2(self, k, l):
        """
        Level 2 Generalization: Adjust the Departure Date and Age based on k-anonymity requirements.
        """
        # Group by the QIDs and count the number of records in each group.
        main_groups = self.anonymized_data.groupby(['Gender', 'Airport Continent'])

        new_dates = []
        new_ages = []
        #utility_loss = 0

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
                    # # Calculate utility loss based on the difference in months
                    # if total_count >= k:
                    #     start_month = int(str(start_date).split('-')[1])
                    #     end_month = int(str(end_date).split('-')[1])
                    #     age_difference = end_age - start_age
                    #     utility_loss += age_difference/1700 * 0.0001
                    #     month_difference = end_month - start_month
                    #     utility_loss += month_difference/1700 * 0.001
                    #     self.utility_value -= utility_loss
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



    def measure_utility(self):
        data = self.data
        anonymized_data = self.anonymized_data
        total_records = len(data)
        kl_divergences = []

        # Extract month from 'Departure Date' in the original data
        data['Month'] = pd.to_datetime(data['Departure Date']).dt.month

        for index, row in data.iterrows():
            # Calculate p(x) for the original data
            subset_original = data[(data['Gender'] == row['Gender']) & (data['Airport Continent'] == row['Airport Continent'])]
            p_x = len(subset_original[subset_original['Month'] == row['Month']]) / total_records

            # Calculate panon(x) for the anonymized data
            subset_anon = anonymized_data[(anonymized_data['Gender'] == row['Gender']) & (anonymized_data['Airport Continent'] == row['Airport Continent'])]
            for date_range in subset_anon['Departure Date'].unique():
                start_date, end_date = date_range.split('--')
                start_year, start_month = map(int, start_date.split('-'))
                end_year, end_month = map(int, end_date.split('-'))
                if start_month <= row['Month'] <= end_month:
                    month_range_size = end_month - start_month + 1
                    eq_class_size = len(subset_anon[subset_anon['Departure Date'] == date_range])
                    panon_x = (1 / total_records) * (1 / month_range_size) * eq_class_size
                    break
            else:
                panon_x = 0

            # Calculate KL-divergence for the current row
            kl_divergence = p_x * np.log(p_x / panon_x) if p_x != 0 else 0
            kl_divergences.append(kl_divergence)

        return sum(kl_divergences)