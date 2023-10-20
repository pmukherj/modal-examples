# ---
# args: ["--just-run"]
# runtimes: ["runc", "gvisor"]
# ---
# # Tensorflow tutorial
#
# This is essentially a version of the
# [image classification example in the Tensorflow documention](https://www.tensorflow.org/tutorials/images/classification)
# running inside Modal on a GPU.
# If you run this script, it will also create an Tensorboard URL you can go to:
#
# ![tensorboard](./tensorboard.png)
#
# ## Setting up the dependencies
#
# Installing Tensorflow in Modal is quite straightforward.
# If you want it to run on a GPU, you need the container image to have CUDA libraries available
# to the Tensorflow package. You can use Conda to install these libraries before `pip` installing `tensorflow`, or you
# can use Tensorflow's official GPU base image which comes with the CUDA libraries and `tensorflow` already installed.

import time

from modal import Image, NetworkFileSystem, Stub, wsgi_app

dockerhub_image = Image.from_registry(
    "tensorflow/tensorflow:latest-gpu",
).pip_install("protobuf==3.20.*")

conda_image = (
    Image.conda()
    .conda_install(
        "cudatoolkit=11.2",
        "cudnn=8.1.0",
        "cuda-nvcc",
        channels=["conda-forge", "nvidia"],
    )
    .pip_install("tensorflow~=2.9.1")
)

stub = Stub(
    "example-tensorflow-tutorial",
    image=conda_image or dockerhub_image,  # pick one and remove the other.
)

# ## Logging data for Tensorboard
#
# We want to run the web server for Tensorboard at the same time as we are training the Tensorflow model.
# The easiest way to do this is to set up a shared filesystem between the training and the web server.

stub.volume = NetworkFileSystem.new()
logdir = "/tensorboard"

# ## Training function
#
# This is basically the same code as the official example.
# A few things are worth pointing out:
#
# * We set up the network file system in the arguments to `stub.function`
# * We also annotate this function with `gpu="any"`
# * We put all the Tensorflow imports inside the function body.
#   This makes it a bit easier to run this example even if you don't have Tensorflow installed on you local computer.


@stub.function(
    network_file_systems={logdir: stub.volume}, gpu="any", timeout=600
)
def train():
    import pathlib

    import tensorflow as tf
    from tensorflow.keras import layers
    from tensorflow.keras.models import Sequential

    dataset_url = "https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz"
    data_dir = tf.keras.utils.get_file(
        "flower_photos", origin=dataset_url, untar=True
    )
    data_dir = pathlib.Path(data_dir)

    batch_size = 32
    img_height = 180
    img_width = 180

    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=(img_height, img_width),
        batch_size=batch_size,
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=(img_height, img_width),
        batch_size=batch_size,
    )

    class_names = train_ds.class_names
    train_ds = (
        train_ds.cache().shuffle(1000).prefetch(buffer_size=tf.data.AUTOTUNE)  # type: ignore
    )
    val_ds = val_ds.cache().prefetch(buffer_size=tf.data.AUTOTUNE)  # type: ignore
    num_classes = len(class_names)

    model = Sequential(
        [
            layers.Rescaling(1.0 / 255, input_shape=(img_height, img_width, 3)),
            layers.Conv2D(16, 3, padding="same", activation="relu"),
            layers.MaxPooling2D(),
            layers.Conv2D(32, 3, padding="same", activation="relu"),
            layers.MaxPooling2D(),
            layers.Conv2D(64, 3, padding="same", activation="relu"),
            layers.MaxPooling2D(),
            layers.Flatten(),
            layers.Dense(128, activation="relu"),
            layers.Dense(num_classes),
        ]
    )

    model.compile(
        optimizer="adam",
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=["accuracy"],
    )

    model.summary()

    tensorboard_callback = tf.keras.callbacks.TensorBoard(
        log_dir=logdir,
        histogram_freq=1,
    )

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=20,
        callbacks=[tensorboard_callback],
    )


# ## Running Tensorboard
#
# Tensorboard is a WSGI-compatible web server, so it's easy to expose it in Modal.
# The app isn't exposed directly through the Tensorboard library, but it gets
# [created in the source code](https://github.com/tensorflow/tensorboard/blob/master/tensorboard/program.py#L467)
# in a way where we can do the same thing quite easily too.
#
# Note that the Tensorboard server runs in a different container.
# This container shares the same log directory containing the logs from the training.
# The server does not need GPU support.
# Note that this server will be exposed to the public internet!


@stub.function(network_file_systems={logdir: stub.volume})
@wsgi_app()
def tensorboard_app():
    import tensorboard

    board = tensorboard.program.TensorBoard()
    board.configure(logdir=logdir)
    (data_provider, deprecated_multiplexer) = board._make_data_provider()
    wsgi_app = tensorboard.backend.application.TensorBoardWSGIApp(
        board.flags,
        board.plugin_loaders,
        data_provider,
        board.assets_zip_provider,
        deprecated_multiplexer,
    )
    return wsgi_app


# ## Local entrypoint code
#
# Let's kick everything off.
# Everything runs in an ephemeral "app" that gets destroyed once it's done.
# In order to keep the Tensorboard web server running, we sleep in an infinite loop
# until the user hits ctrl-c.
#
# The script will take a few minutes to run, although each epoch is quite fast since it runs on a GPU.
# The first time you run it, it might have to build the image, which can take an additional few minutes.


@stub.local_entrypoint()
def main(just_run: bool = False):
    train.remote()
    if not just_run:
        print("Training is done, but app is still running until you hit ctrl-c")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Terminating app")
