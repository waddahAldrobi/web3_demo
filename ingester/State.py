import json
import os


class State:
    """
    Manages the state of the last processed block in a JSON file.

    This class provides methods to load, save, and update the state stored in a file.
    The state is used to keep track of the last processed block in a blockchain context.
    """

    def __init__(self, file_path):
        """
        Initializes the State object.

        Args:
            file_path (str): Path to the JSON file that stores the state.
        """
        self.file_path = file_path
        self.state = self._load_state()

    def _load_state(self):
        """
        Loads the state from the JSON file.

        Returns:
            dict: The loaded state dictionary. Returns an empty dictionary if the file does not exist
                  or if it is corrupted.
        """
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print("State file is corrupted. Resetting state.")
                    return {}
        return {}

    def _save_state(self):
        """
        Saves the current state to the JSON file.
        """
        with open(self.file_path, "w") as f:
            json.dump(self.state, f, indent=4)

    def get_last_processed_block(self, block_number: int):
        """
        Retrieves the last processed block number.

        Args:
            block_number (int): The new last processed block number.

        Returns:
            int: The last processed block number. If not found in the state, returns the latest block number.
        """
        return self.state.get("last_processed_block", block_number)

    def update_last_processed_block(self, block_number: int):
        """
        Updates the last processed block number in the state.

        Args:
            block_number (int): The new last processed block number.
        """
        self.state["last_processed_block"] = block_number
        self._save_state()
