import pandas as pd

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
    
    def generalize_level_2(self, k):
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
                if subset_groups.iloc[i]['count'] < k:
                    start_date = subset_groups.iloc[i]['Departure Date']
                    start_age = subset_groups.iloc[i]['Age']
                    end_date = start_date
                    end_age = start_age
                    count = subset_groups.iloc[i]['count']

                    # Keep adding records from the next groups until we have at least k records.
                    while count < k and i < len(subset_groups) - 1:
                        i += 1
                        count += subset_groups.iloc[i]['count']
                        end_date = subset_groups.iloc[i]['Departure Date']
                        end_age = subset_groups.iloc[i]['Age']

                    # If we're at the last subset group and it's less than k, merge with the previous group
                    if i == len(subset_groups) - 1 and count < k:
                        if prev_count:
                            new_dates = new_dates[:-prev_count]
                            new_ages = new_ages[:-prev_count]
                            count += prev_count
                        if last_generalized_start_date:
                            start_date = last_generalized_start_date
                        if last_generalized_start_age:
                            start_age = last_generalized_start_age
                        end_date = subset_groups.iloc[i]['Departure Date']
                        end_age = subset_groups.iloc[i]['Age']

                    # Set the new date and age range for the combined group.
                    new_dates.extend([f"{start_date}--{end_date}"] * count)
                    new_ages.extend([f"{start_age}--{end_age}"] * count)
                    last_generalized_start_date = start_date
                    last_generalized_start_age = start_age
                    prev_count = count
                    # Calculate utility loss based on the difference in months
                    if count >= k:
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
        


    def anonymize(self, k):
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
        insufficient_groups = grouped.filter(lambda x: len(x) < k)
        
        # If there are groups that don't meet the k-anonymity requirement, apply Level 2 Generalization
        if not insufficient_groups.empty:
            self.generalize_level_2(k)



    def save_to_csv(self, filename):
        """
        Save the anonymized data to a CSV file.
        """
        if self.anonymized_data is not None:
            self.anonymized_data.to_csv(filename, index=False)
        else:
            print("Data has not been anonymized yet.")


    def measure_utility(self):
        """
        Return the utility of the anonymized data.
        """
        return round(self.utility_value, 2)
