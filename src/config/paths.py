"""
Application paths configuration
"""
import os

# Base directories
ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DATA_DIR = os.path.join(ROOT_DIR, 'data')

# Raw data directories
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
RAW_DAA_DIR = os.path.join(RAW_DATA_DIR, 'daa.uit.edu.vn')
RAW_UIT_DIR = os.path.join(RAW_DATA_DIR, 'uit.edu.vn')
RAW_COURSE_DIR = os.path.join(RAW_DATA_DIR, 'course.uit.edu.vn')

# Processed data directories
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
PROCESSED_DAA_DIR = os.path.join(PROCESSED_DATA_DIR, 'daa.uit.edu.vn')
PROCESSED_UIT_DIR = os.path.join(PROCESSED_DATA_DIR, 'uit.edu.vn')
PROCESSED_COURSE_DIR = os.path.join(PROCESSED_DATA_DIR, 'course.uit.edu.vn')

# Other directories
VECTORSTORE_DIR = os.path.join(DATA_DIR, 'vectorstore')

# Ensure directories exist
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(RAW_DAA_DIR, exist_ok=True)
os.makedirs(RAW_UIT_DIR, exist_ok=True)
os.makedirs(RAW_COURSE_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DAA_DIR, exist_ok=True)
os.makedirs(PROCESSED_UIT_DIR, exist_ok=True)
os.makedirs(PROCESSED_COURSE_DIR, exist_ok=True)
os.makedirs(VECTORSTORE_DIR, exist_ok=True)
