name = "rbl_pipe_usd"

version = "0.14.0"

authors = [
    "Jonathan Cox",
    "Erkan Ozgur Yilmaz",
]

requires = [
    # Technically this should probably have a dependency against USD
    # Or variants that provide it (ie. Houdini etc.)

    "rbl_pipe_sg-0.12+<1",
    "rbl_pipe_core-0.11+<1",
]


def commands():
    env.PATH.prepend("{root}/rbl_pipe_usd/bin")
    env.PYTHONPATH.prepend("{root}/rbl_pipe_usd/lib/python")
