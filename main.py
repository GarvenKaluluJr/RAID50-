import os


class Disk:
    def __init__(self, disk_id):
        self.disk_id = disk_id
        self.file_name = f"{disk_id}.txt"
        self.blocks = []

    def write_block(self, block, block_id):
        while len(self.blocks) <= block_id:
            self.blocks.append(None)

        self.blocks[block_id] = block

        with open(self.file_name, "a") as f:
            f.write(block + "\n")

    def read_block(self, block_id):
        if not os.path.exists(self.file_name):
            return None  # Return None if file doesn't exist

        return self.blocks[block_id] if block_id < len(self.blocks) else None

    def erase_block(self, block_id):
        if block_id < len(self.blocks):
            self.blocks[block_id] = None


class Message:
    def __init__(self, message):
        self.message = message
        self.blocks = self.create_blocks(message)

    def create_blocks(self, message):
        blocks = [message[i:i + 2] for i in range(0, len(message), 2)]

        if len(blocks[-1]) < 2:
            blocks[-1] = blocks[-1].ljust(2, '\0')

        return blocks


class RAID50:
    def __init__(self, num_disks):
        self.num_disks = num_disks
        self.disks = [Disk(f"disk{i}") for i in range(num_disks)]

    def calculate_xor(self, blocks):
        xor_result = int(blocks[0], 16)
        for block in blocks[1:]:
            xor_result ^= int(block, 16)
        return format(xor_result, '02X')

    def write_message(self, message, address):
        message_obj = Message(message)
        blocks = message_obj.blocks
        num_blocks = len(blocks)

        if num_blocks % 2 == 0:
            redundancy = self.calculate_xor(blocks)
            blocks.append(redundancy)
        else:
            blocks.append('01')
            redundancy = self.calculate_xor(blocks)
            blocks[-1] = redundancy

        for disk in self.disks:
            for block_index, block in enumerate(blocks):
                disk.write_block(block, address * (num_blocks + 1) + block_index)

        print(f"Message written successfully to address {address}!")

    def read_message(self, address):
        blocks = []

        for i in range(self.num_disks):
            block = self.disks[i].read_block(address * (len(self.disks[0].blocks)))
            if block is not None:
                blocks.append(block)

        # Check how many valid blocks we have
        valid_blocks = [block for block in blocks if block is not None]

        if len(valid_blocks) >= (self.num_disks - 1):  # At least n-1 disks must be available
            return self.recover_message(valid_blocks)
        else:
            print("Not enough data to recover the message.")
            return None

    def recover_message(self, valid_blocks):
        # The last block is expected to be the redundancy
        redundancy_block = valid_blocks[-1]

        # Calculate the expected redundancy from known blocks
        calculated_redundancy = self.calculate_xor(valid_blocks[:-1])

        # If redundancy matches calculated redundancy, we can reconstruct the message
        if redundancy_block == calculated_redundancy:
            return "".join(valid_blocks[:-1]).rstrip('\0')
        print("Redundancy does not match; recovery may not be complete.")

        # Attempt to recover missing blocks if possible
        recovered_blocks = valid_blocks[:-1]  # Exclude redundancy for recovery
        for i in range(len(valid_blocks) - 1):  # Exclude redundancy
            if valid_blocks[i] is None:
                recovered_block = format(int(redundancy_block, 16) ^ int(calculated_redundancy, 16), '02X')
                recovered_blocks.insert(i, recovered_block)
                print(f"Recovered missing block at index {i}: {recovered_block}")

        return "".join(recovered_blocks).rstrip('\0')

    def erase_data(self, address):
        for disk in self.disks:
            for block_index in range(len(disk.blocks)):
                disk.erase_block(address * (len(disk.blocks)) + block_index)
        print(f"Data erased successfully from address {address}!")


def main():
    raid50 = RAID50(8)  # Using 8 disks as specified
    while True:
        print("Options:")
        print("1. Read ")
        print("2. Write ")
        print("3. Erase data from disks")
        print("4. Recovering data when one disk fail")
        print("5. Exit")
        option = input("Enter your choice: ")
4
        if option == "1":
            while True:
                address = int(input("Enter the address to read from (0-63): "))
                if 0 <= address <= 63:
                    break
                else:
                    print("Invalid address. Please enter a value between 0 and 63.")
            result = raid50.read_message(address)
            if result is not None:
                print(f"Recovered message: {result}")

        elif option == "2":
            while True:
                address = int(input("Enter the address to write to (0-63): "))
                if 0 <= address <= 63:
                    break
                else:
                    print("Invalid address. Please enter a value between 0 and 63.")

            message = input("Enter the message to write (14 bytes): ")
            if len(message) != 14:
                print("Message must be exactly 14 bytes long.")
                continue

            raid50.write_message(message, address)

        elif option == "3":
            while True:
                address = int(input("Enter the address to erase from (0-63): "))
                if 0 <= address <= 63:
                    break
                else:
                    print("Invalid address. Please enter a value between 0 and 63.")
            raid50.erase_data(address)

        elif option == "4":
            break

        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
