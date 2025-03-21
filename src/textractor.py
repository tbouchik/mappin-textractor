import sys
import os
from urllib.parse import urlparse
import boto3
import time
from tdp import DocumentProcessor
from og import OutputGenerator
from helper import FileHelper, S3Helper
# import pdb_attach
# pdb_attach.listen(5000)
class Textractor:
    def getInputParameters(self, args):
        event = {}
        i = 0
        if(args):
            while(i < len(args)):
                if(args[i] == '--documents'):
                    event['documents'] = args[i+1]
                    i = i + 1
                if(args[i] == '--region'):
                    event['region'] = args[i+1]
                    i = i + 1
                if(args[i] == '--text'):
                    event['text'] = True
                if(args[i] == '--forms'):
                    event['forms'] = True
                if(args[i] == '--tables'):
                    event['tables'] = True
                if(args[i] == '--insights'):
                    event['insights'] = True
                if(args[i] == '--medical-insights'):
                    event['medical-insights'] = True
                if(args[i] == '--translate'):
                    event['translate'] = args[i+1]
                    i = i + 1
                if(args[i] == '--output'):
                    event['output'] = args[i+1]
                    i = i + 1

                i = i + 1
        return event

    def validateInput(self, args):

        event = self.getInputParameters(args)

        ips = {}

        if(not 'documents' in event):
            raise Exception("Document or path to a foler or S3 bucket containing documents is required.")

        inputDocument = event['documents']
        idl = inputDocument.lower()

        bucketName = None
        documents = []
        awsRegion = 'us-east-1'

        if(idl.startswith("s3://")):
            o = urlparse(inputDocument)
            bucketName = o.netloc
            path = o.path[1:]
            ar = S3Helper.getS3BucketRegion(bucketName)
            if(ar):
                awsRegion = ar

            if(idl.endswith("/")):
                allowedFileTypes = ["jpg", "jpeg", "png", "pdf"]
                documents = S3Helper.getFileNames(awsRegion, bucketName, path, 1, allowedFileTypes)
            else:
                documents.append(path)
        else:
            if(idl.endswith("/")):
                allowedFileTypes = ["jpg", "jpeg", "png"]
                documents = FileHelper.getFileNames(inputDocument, allowedFileTypes)
            else:
                documents.append(inputDocument)

            if('region' in event):
                awsRegion = event['region']

        ips["bucketName"] = bucketName
        ips["documents"] = documents
        ips["awsRegion"] = awsRegion
        ips["text"] = ('text' in event)
        ips["forms"] = ('forms' in event)
        ips["tables"] = ('tables' in event)
        ips["insights"] = ('insights' in event)
        ips["medical-insights"] = ('medical-insights' in event)
        if("translate" in event):
            ips["translate"] = event["translate"]
        else:
            ips["translate"] = ""
        if("output" in event):
            ips["output"] = os.path.join(os.path.dirname( __file__),event["output"])
        else:
            ips["output"] = os.getcwd()

        return ips
    
    def constructIps (self, event):
        ips = {}
        ips["bucketName"] = event["bucketName"]
        ips["documents"] = [event["document"]]
        ips["awsRegion"] = event["region"]
        ips["text"] = True
        ips["tables"] = event["tables"]
        ips["forms"] = False
        ips["insights"] = False
        ips["medical-insights"] = False
        ips["translate"] = ""
        ips["output"] = ""

        return ips

    def processDocument(self, ips, i, document):
        print("\nTextracting Document # {}: {}".format(i, document))
        print('=' * (len(document)+30))

        # Get document textracted
        dp = DocumentProcessor(ips["bucketName"], document, ips["awsRegion"], ips["text"], ips["forms"], ips["tables"])
        response = dp.run()
        print("Recieved Textract response...")

        #FileHelper.writeToFile("temp-response.json", json.dumps(response))

        #Generate output files
        print("Generating output...")
        name, ext = FileHelper.getFileNameAndExtension(document)
        opg = OutputGenerator(response, os.path.join(ips["output"],"{}-{}".format(name, ext, name, ext)),
                    ips["forms"], ips["tables"])
        print("{} textracted successfully.".format(document))
        return opg.run()

    def printFormatException(self, e):
        print("Invalid input: {}".format(e))
        print("Valid format:")
        print('- python3 textractor.py --documents mydoc.jpg --text --forms --tables --region us-east-1')
        print('- python3 textractor.py --documents ./myfolder/ --text --forms --tables')
        print('- python3 textractor.py --documents s3://mybucket/mydoc.pdf --text --forms --tables')
        print('- python3 textractor.py --documents s3://mybucket/ --text --forms --tables')
        print('- python3 textractor.py --documents s3://mybucket/ --output ../results/ --text --forms --tables')

    def run(self, useEvent = False, event = None):

        ips = None
        try:
            if useEvent:
                ips = self.constructIps(event)
            else:
                ips = self.validateInput(sys.argv)
        except Exception as e:
            self.printFormatException(e)

        #try:
        i = 1
        totalDocuments = 1

        print("\n")
        print('*' * 60)
        print("Total input documents: {}".format(totalDocuments))
        print('*' * 60)

        
        result = self.processDocument(ips, i, ips["documents"][0])


        print("\n")
        print('*' * 60)
        print("Successfully textracted documents: {}".format(totalDocuments))
        print('*' * 60)
        print("\n")
        return result
        #except Exception as e:
        #    print("Something went wrong:\n====================================================\n{}".format(e))

def handler(event, context):
    return Textractor().run(True, event)

if __name__ == "__main__":
    event = {
        "bucketName": "bucket413",
        "document": "cih.pdf", #be3b2d51-a238-484e-9358-3bd00328b7c5.pdf
        "region":"us-east-1",
        "tables": True
    }
    a = handler(dict(event), None)
    print(a)