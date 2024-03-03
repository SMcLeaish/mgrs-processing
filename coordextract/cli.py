"""this module contains a cli tool for processing gpx files and 
converting coordinates to json format using the coordextract library.

Usage:
    coordextract [INPUT] [OPTIONS]

Input:
    The GPX file(s) or directory to process.
Options:
    --output, -o TEXT   Output file or directory.
    --indent, -n TEXT   Indentation level for the JSON output.
    --concurrency, -c   Use CPU concurrency for batch processing.
    --help              Show this message and exit. 

Note: If the input is a directory or multiple files, the output
will be written to a directory with the name coordextract_output
unless the --output option is specified. If processing multiple
files, the files will be named using the input file name with the
suffix .json.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from pydantic import ValidationError

from coordextract import process_coords as pc

app = typer.Typer()


async def process(
    inputfile: Path,
    outputfile: Optional[Path],
    indentation: Optional[int],
    concurrency: bool = False,
    context: Optional[str] = "cli",
) -> Optional[str]:
    """Processes the input file and writes the JSON output to a file or
    prints it to the console.
    """
    """
    Args:
        inputfile (Path): The input file to process.
        outputfile (Optional[Path]): The output file to.
        indentation (Optional[int]): The JSON indentation level.
        concurrency (Optional[bool]): Flag indicating whether to use
            CPU concurrency for batch processing.

    Returns:
        Optional[str]: The JSON string if outputfile is None, otherwise None.
    """

    json_str = await pc(
        inputfile, outputfile, indentation, concurrency, context
    )
    if json_str is not None:
        print(json_str)
    return None


async def process_batch(
    files: list[Path],
    outputdir: Path,
    indentation: Optional[int],
    concurrency: bool = False,
) -> None:
    """Processes a batch of files concurrently."""
    outputdir.mkdir(parents=True, exist_ok=True)
    tasks = [
        asyncio.create_task(
            pc(file, outputdir / f"{file.stem}.json", indentation, concurrency)
        )
        for file in files
    ]
    await asyncio.gather(*tasks)


async def process_directory(
    inputdir: Path,
    outputdir: Path,
    indentation: Optional[int],
    concurrency: bool = False,
) -> None:
    """Processes all GPX files in a directory."""
    files = [file for file in inputdir.iterdir() if file.suffix == ".gpx"]
    await process_batch(files, outputdir, indentation, concurrency)


@app.command()
def main(
    inputs: list[Path] = typer.Argument(
        ...,
        exists=True,
        dir_okay=True,
        file_okay=True,
        readable=True,
        resolve_path=True,
        help="The GPX file(s) or directory to process.",
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file or directory."
    ),
    indentation: Optional[int] = typer.Option(
        None, "--indent", "-i", help="Indentation level for JSON output."
    ),
    concurrency: bool = typer.Option(
        False,
        "--concurrency",
        "-c",
        help="Use cpu concurrency for batch processessing large datasets.",
    ),
) -> None:
    """This function contains the logic for the  command-line interface
    for processing GPX files and converting coordinates to JSON format
    using the coordextract library.
    """
    try:
        if len(inputs) == 1 and inputs[0].is_dir():
            inputdir = inputs[0]
            outputdir = output or inputdir / "coordextract_output"
            asyncio.run(
                process_directory(
                    inputdir, outputdir, indentation, concurrency
                )
            )
            sys.exit(0)
        else:
            if len(inputs) == 1:
                inputfile = inputs[0]
                asyncio.run(
                    process(inputfile, output, indentation, concurrency)
                )
                sys.exit(0)
            else:
                outputdir = output or Path(".")
                asyncio.run(
                    process_batch(inputs, outputdir, indentation, concurrency)
                )
                sys.exit(0)
    except (
        ValueError,
        OSError,
        RuntimeError,
        NotImplementedError,
        ValidationError,
    ) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    app()  # pragma: no cover
