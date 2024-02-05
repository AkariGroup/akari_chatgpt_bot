from grpc.tools import protoc

protoc.main(
    (
        "",
        "-I.",
        "--python_out=../lib/grpc",
        "--grpc_python_out=../lib/grpc",
        "gpt_server.proto",
    )
)
protoc.main(
    (
        "",
        "-I.",
        "--python_out=../lib/grpc",
        "--grpc_python_out=../lib/grpc",
        "voicevox_server.proto",
    )
)
