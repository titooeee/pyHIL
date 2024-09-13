import can
import cantools

# Load the DBC file
db = cantools.database.load_file('/home/mtitoo/pyHIL/open_actuator.dbc')

def decode_can_message(msg):
    try:
        # Decode the message using cantools
        decoded = db.decode_message(msg.arbitration_id, msg.data)
        return decoded
    except KeyError:
        # If the message ID is not in the DBC file
        return None

def receive_and_decode_can_messages(interface, filters):
    bus = can.interface.Bus(interface, bustype='socketcan')
    print(f"Listening on {bus.channel_info}...")
    
    while True:
        msg = bus.recv()
        if msg:
            # Check if the message matches any of the filters
            if any(f['can_id'] == msg.arbitration_id for f in filters):
                decoded_message = decode_can_message(msg)
                if decoded_message:
                    print(f"Decoded message: {decoded_message}")

if __name__ == "__main__":
    interface = 'vcan0'
    # Define filters (example: filter messages with ID 123 and 456)
    filters = [
        {"can_id": 0xFA, "can_mask": 0x7FF},
        {"can_id": 0xFB, "can_mask": 0x7FF},
        {"can_id": 0xFC, "can_mask": 0x7FF}
    ]
    receive_and_decode_can_messages(interface, filters)
