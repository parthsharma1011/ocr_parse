# temporary debug file - delete later
# just testing some stuff

import json

def debug_print(msg):
    print(f"DEBUG: {msg}")

# hardcoded test data - should move to config
TEST_DATA = {
    "api_key": "test123",
    "files": ["test.pdf"]
}

# quick and dirty function
def temp_test():
    debug_print("testing something")
    # TODO: implement actual logic
    pass

if __name__ == "__main__":
    temp_test()
    print("done with temp testing")