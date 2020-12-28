from datetime import datetime
from dotenv import load_dotenv
import shutil
import os

load_dotenv()
outputDir = os.getenv('OUTPUT_DIR')
print('---------------------------------')
print('Starting housekeeping job: ' + str(datetime.now()) )
shutil.rmtree(outputDir)
print('Finished housekeeping job: ' + str(datetime.now()) )
print('---------------------------------')
