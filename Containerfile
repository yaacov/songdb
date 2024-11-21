# Use the Red Hat Universal Base Image (UBI)
FROM registry.access.redhat.com/ubi9/python-311

# Set the working directory
WORKDIR /app

# Copy all application files to the container
COPY . .

# Install the dependencies
RUN pip install --upgrade pip; pip install --no-cache-dir -r requirements.txt

# Generate SSL certificates if they don't exist
USER 0
RUN make ssl

# Change ownership of working directory and home directory to default user
RUN chown -R 1001:0 /app /home/ && chmod -R ugo+rw /app /home/

# Switch back to the default user
USER 1001

# Expose the port on which the server runs
EXPOSE 8000

# Start the Python server
CMD ["make", "start"]
