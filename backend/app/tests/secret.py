import secrets

def generate_key():
    return secrets.token_hex(32)


if __name__ == "__main__":
    print("32bit hex is :",generate_key())