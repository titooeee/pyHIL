import multiprocessing.process
class channelDef(multiprocessing.Process):
    def __init__(self,path,value):
        self.path = path
        self.value = value
    def updateVal(self,value):
        self.value = value
        print(self.value)
    def getVal(self):
        print('Return is', self.value)
        return self.value

def channelDictTemplate():
    return {
        'path': None,
        'value': 0,
        'index':0
    }



