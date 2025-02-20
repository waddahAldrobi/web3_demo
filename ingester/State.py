import json
import os


class State:
    def __init__(self, file_path):
        self.file_path = file_path
        self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print("State file is corrupted. Resetting state.")
                    return {}
        return {}

    def _save_state(self):
        with open(self.file_path, "w") as f:
            json.dump(self.state, f, indent=4)

    def get_last_processed_block(self, w3):
        return self.state.get("last_processed_block", w3.eth.block_number)

    def update_last_processed_block(self, block_number):
        self.state["last_processed_block"] = block_number
        self._save_state()
