import zipfile


def read_zip_without_extracting(zip_file_path):
    chunk_size = 65536
    try:
        with zipfile.ZipFile(zip_file_path, "r") as zip_file:
            print(f"Contents of '{zip_file_path}':")
            for name in zip_file.namelist():
                print(f"- {name}")

            for file in zip_file.infolist():
                print(
                    f"\nContent of the file '{file.filename}' (Offset: {file.header_offset}):",
                )
                try:
                    with zip_file.open(file) as fd:
                        while True:
                            content = fd.read(chunk_size)
                            # We know it is a sparse file
                            if b"UMASS" in content:
                                print(content)
                            if b"\x00\x00" in content:
                                break
                except Exception as e:
                    print(f"(Could not read content: {e})")

    except FileNotFoundError:
        print(f"Error: Zip file not found at '{zip_file_path}'")
    except zipfile.BadZipFile:
        print(f"Error: Invalid zip file at '{zip_file_path}'")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


read_zip_without_extracting("archive.zip")
