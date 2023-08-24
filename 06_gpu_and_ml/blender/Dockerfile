#Easy GPU Enabled base to start from
FROM gcr.io/deeplearning-platform-release/pytorch-gpu.1-13
RUN apt-get update && \
    apt-get install -y \
        curl wget nano \
        bzip2 libfreetype6 libgl1-mesa-dev \
        libglu1-mesa \
        libxi6 libxrender1 && \
    apt-get -y autoremove && \
    pip install --upgrade pip && \

# Install blender
RUN mkdir /usr/local/blender && \
    wget https://download.blender.org/release/Blender3.4/blender-3.4.1-linux-x64.tar.xz -O blender.tar.xz && \
    tar -xvf blender.tar.xz -C /usr/local/blender --strip-components=1 && \
    rm blender.tar.xz
    
# Copy Script
COPY render_all_cameras.py ~/render_all_cameras.py