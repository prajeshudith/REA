from datetime import datetime

def generate_uuid():
    """Generate a simple UUID based on the current timestamp."""
    return datetime.now().strftime("%m%d%Y_%H%M%S%f")

# if __name__ == "__main__":
#     print(generate_uuid())