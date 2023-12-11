import logging 
import datetime
import os
import pathlib


"""
this file contains loggers to be used within the notebooks to create persistent documentation of complicated imports / changes. 


streamLogger: logs to the standard output. 
fileLogger: logs to a file given to the logger. The persistent option.
"""
streamLogger = logging.getLogger(name="NotebookStreamLogger")
fileLogger = logging.getLogger(name="NotebookFileLogger")

SH = logging.StreamHandler()
FH = logging.FileHandler(filename="../logs/test/output_test.txt")
fileLogger.addHandler(FH)
fileLogger.setLevel(logging.DEBUG)



def logger_factory(file_name, test=True, stream=True):

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d (%H:%M)")
    logger = logging.getLogger(name="defaultStreamLogger")

    if test:
        path =  "../logs/test/"
    else:
        path =  "../logs/keep/"

    filepath = path + file_name+"_"+timestamp+".txt"
    fileHandler = logging.FileHandler(filepath)
    if stream:
        streamHandler = logging.StreamHandler()
        logger.addHandler(streamHandler)
    
    logger.addHandler(fileHandler)
    logger.setLevel(logging.DEBUG)

    return logger
    