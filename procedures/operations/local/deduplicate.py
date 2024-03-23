from nltk.metrics import edit_distance
from operations.local.logging import baton_log


class Deduplicate:
    def __init__(self, existing_participants_df, new_participants_list):
        self.existing_participants_df = existing_participants_df
        self.new_participants_list = new_participants_list

    def _accumulate_duplicates(self, participant, result):
        """Accumulate duplicate result, then cast back to boolean (False==0, True>=1). This way the
        result of cumulative deduplication methods will not overwrite True values (they instead
        "accumulate" to higher values, then get cast back to True AKA 1).
        """
        if "duplicate" in participant:
            participant["duplicate"] = bool(participant["duplicate"] + result)
        else:
            participant["duplicate"] = bool(result)

    # Accessors

    def get_all_new_participants(self):
        return self.new_participants_list

    def get_duplicate_new_participants(self):
        return [
            participant
            for participant in self.new_participants_list
            if participant["duplicate"] == True
        ]

    def get_non_duplicate_new_participants(self):
        return [
            participant
            for participant in self.new_participants_list
            if participant["duplicate"] == False
        ]

    # Deduplication checkers

    def exact_name_match(self):
        """Concatenates first and last name, and checks for exact match."""
        all_names_no_spaces = (
            self.existing_participants_df["First Name"].astype(str)
            + self.existing_participants_df["Last Name"].astype(str)
        ).replace(" ", "")
        count = 0
        for participant in self.new_participants_list:
            name_no_spaces = (
                str(participant["first_name"]) + str(participant["last_name"])
            ).replace(" ", "")
            result = name_no_spaces in all_names_no_spaces.values
            count += (int)(result)
            self._accumulate_duplicates(participant, result)
        baton_log.info(f"Found {count} duplicates with exact_name_match.")

    def levenshtein_name_match(self, cutoff):
        """Concatenates first and last name, and checks the number of characters difference, marking
        a duplicate if the number of characters difference is under the cutoff threshold.
        """
        all_names_no_spaces = (
            self.existing_participants_df["First Name"].astype(str)
            + self.existing_participants_df["Last Name"].astype(str)
        ).replace(" ", "")
        count = 0
        for participant in self.new_participants_list:
            name_no_spaces = (
                str(participant["first_name"]) + str(participant["last_name"])
            ).replace(" ", "")
            for each_name in all_names_no_spaces:
                lev_distance = edit_distance(name_no_spaces, each_name)
                if lev_distance <= cutoff:
                    result = 1
                else:
                    result = 0
                if result == 1:
                    break
            count += result
            self._accumulate_duplicates(participant, result)
        baton_log.info(
            f"Found {count} duplicates with Levenshtein edit distance with inclusive cutoff {cutoff}."
        )
