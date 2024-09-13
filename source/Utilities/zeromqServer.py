import zmq
import time

def publisher():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5555")

    while True:
        topic = "topic1"
        message = "Hello, subscribers!"
        socket.send_string(f"{topic} {message}")
        print(f"Sent: {topic} {message}")
        time.sleep(1)

if __name__ == "__main__":
    publisher()
