FROM python:3.11

# Install base utils
RUN apt-get update && apt-get install -y git vim make

# Install Jupyter and necessary Python packages
RUN pip install jupyterlab notebook ipykernel

# Set up a Python kernel
RUN python -m ipykernel install --name "python3" --display-name "Python 3"

# Set the working directory
WORKDIR /workspace

# Expose Jupyter Notebook port
EXPOSE 8888
