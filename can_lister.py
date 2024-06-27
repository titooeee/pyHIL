import multiprocessing
import time

class MyClass:
    def __init__(self, name):
        self.name = name

    def greet(self):
        while True:
            print(f"Hello, {self.name}!")
            time.sleep(0.001)



def main():
    obj = MyClass("Alice")
    process = multiprocessing.Process(target=obj.greet, args=())
    process.start()
    process.join()

if __name__ == "__main__":
    main()